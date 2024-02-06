import traceback
import asyncio
from time import perf_counter as _perf_counter
from datetime import timedelta as _timedelta
from itertools import tee

from orjson import dumps as _jsondump
from alive_progress import alive_bar as _alive_bar
from httpx import AsyncClient as _AsyncClient
from aiohttp import (
    ClientSession as _ClientSession,
    ClientTimeout as AIOHTTPTimeout,
    ClientError as _ClientError,
)

from .meta import SessionMeta as _SessionMeta
from .utils import get_valid_kwargs as _get_valid_kwargs, take as _take
from .useragents import useragent
from .objects import Response as _Response, Timeouts
from .config import SessionConfig as config


def _dumps(obj):
    return _jsondump(obj).decode("utf-8")


class AsyncSession(metaclass=_SessionMeta):
    """
    An asynchronous session for making HTTP requests.

    Args:
        headers (dict, optional): Custom headers to be included in each request. Defaults to None.
        json_serialize (callable, optional): Custom JSON serialization function. Defaults to _dumps.
        random_user_agents (bool, optional): Whether to include random user agents in the request headers. Defaults to True.
        **kwargs: Additional keyword arguments to be passed to the underlying _ClientSession.

    Attributes:
        _random_user_agents (bool): Whether random user agents are enabled.
        _session (ClientSession): The underlying client session.
        _semaphore (Semaphore): A semaphore used for limiting the number of concurrent requests.

    Methods:
        __aenter__(): Asynchronous context manager entry point.
        __aexit__(exc_type, exc_value, exc_traceback): Asynchronous context manager exit point.
        retrieve_response(resp): Asynchronously retrieve the response from a request.
        request(url, method, headers=None, *, bar=None, **kwargs): Asynchronously send a request.
        requests(urls, method="GET", *, headers=None, progress=True, **kwargs): Asynchronously send multiple requests.
        get(url, **kwargs): Asynchronously send a GET request.
        head(url, **kwargs): Asynchronously send a HEAD request.
        options(url, **kwargs): Asynchronously send an OPTIONS request.
        delete(url, **kwargs): Asynchronously send a DELETE request.
        post(url, **kwargs): Asynchronously send a POST request.
        put(url, **kwargs): Asynchronously send a PUT request.
        patch(url, **kwargs): Asynchronously send a PATCH request.
    """
    __slots__ = ("_random_user_agents", "_session", "_semaphore", "_limit")

    def __init__(
        self,
        headers: dict | None                                = None,
        json_serialize: callable                            = _dumps,
        random_user_agents: bool                            = True,
        **kwargs
    ):
        if (loop := kwargs.pop("loop", None)) is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

        headers = headers if isinstance(headers, dict) else {}
        kwargs["loop"] = loop
        kwargs["raise_errors"] = kwargs.pop("raise_errors", None) or config.raise_errors
        kwargs = self._parse_kwargs(kwargs)
        kwargs = _get_valid_kwargs(_ClientSession.__init__, kwargs)
        self._session = _ClientSession(headers=headers, json_serialize=json_serialize, **kwargs)
        self._random_user_agents = random_user_agents
        self._limit = max(self._session.connector.limit, 100) if self._session.connector.limit > 0 else 1
        if config.semaphore == "global":
            AsyncSession._semaphore = asyncio.Semaphore(self._limit)
        else:
            self._semaphore = asyncio.Semaphore(self._limit)


    async def __aenter__(self):
        return self


    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if exc_traceback:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        await self._session.close()


    def _parse_kwargs(self, kwargs):
        keys = set(kwargs.keys())
        timeouts = set(_take(lambda x: x in Timeouts.AIOHTTP.value, keys))

        if timeouts:
            args = {"total": kwargs.pop("timeout", None)}
            if  "pool_timeout" in timeouts and (pool := kwargs.pop("pool_timeout", "None")) != "None" or\
                "connect_timeout" in timeouts and (pool := kwargs.pop("connect_timeout", "None")) != "None":
                args["connect"] = connect

            if "connect_timeout" in timeouts and (connect := kwargs.pop("connect_timeout", "None")) != "None" or\
               "sock_connect" in timeouts and (connect := kwargs.pop("sock_connect", "None")) != "None":
                args["connect"] = connect

            if "read_timeout" in timeouts and (read := kwargs.pop("read_timeout", "None")) != "None" or\
               "sock_read" in timeouts and (read := kwargs.pop("sock_read", "None")) != "None":
                args["read"] = read

            kwargs["timeout"] = AIOHTTPTimeout(**args)
        return kwargs


    async def _retrieve_response(self, resp, callbacks, bar):
        response = _Response(**{
            "version": resp.version,
            "status": resp.status,
            "ok": resp.ok,
            "method": resp.method,
            "reason": resp.reason,
            "url": resp.url,
            "real_url": resp.real_url,
            "connection": resp.connection,
            "content": await resp.content.read() if not isinstance(resp.content, bytes) else resp.content,
            "cookies": resp.cookies,
            "headers": resp.headers,
            "raw_headers": resp.raw_headers,
            "links": resp.links,
            "content_type": resp.content_type,
            "charset": resp.charset,
            "content_disposition": resp.content_disposition,
            "history": resp.history,
            "request": resp.request_info,
            "elapsed": resp.elapsed,
        })
        return self._run_callbacks(response, callbacks, bar)


    async def request(self, url, method, headers=None, *, bar=None, callbacks=None, **kwargs):
        if self._random_user_agents:
            headers = headers or {}
            headers["User-Agent"] = useragent()

        kwargs = _get_valid_kwargs(_ClientSession._request, kwargs)
        begin = _perf_counter()

        try:
            async with self._session.request(method=method, url=url, headers=headers, **kwargs) as response:
                end = _perf_counter()
                response.elapsed = _timedelta(seconds=end - begin)
                return await self._retrieve_response(response, callbacks, bar)

        except asyncio.TimeoutError as e:
            if config.raise_errors:
                raise e
            response =_Response(status=408, errors=e, reason="TimeoutError", content=str(e))
            return self._run_callbacks(response, callbacks, bar)


        except _ClientError as e:
            if config.raise_errors:
                raise e
            if hasattr(response, "status") and response.status is not None:
                status = response.status
            else:
                status = 500
            response = _Response(status=status, errors=e, reason="ClientError", content=str(e))
            return self._run_callbacks(response, callbacks, bar)

        except Exception as e:
            if config.raise_errors:
                raise e
            response = _Response(status=500, errors=e, reason="Exception", content=str(e))
            return self._run_callbacks(response, callbacks, bar)





    # NEEDS FIXED
    async def requests(self, urls, method="GET", *, headers=None, progress=True, ratelimit=True, use_cache=True, callbacks=None, **kwargs):
        if not isinstance(method, str) and isinstance(method, (list, tuple)):
            items = zip(urls, method)
        else:
            items = ((url, method) for url in urls)

        if progress:
            items, items_ = tee(items)
            item_length = sum(1 for _ in items_)
            with _alive_bar(item_length) as bar:
                results = await asyncio.gather(*(self.request(url=url, method=method, headers=headers, ratelimit=ratelimit, use_cache=use_cache, bar=bar, callbacks=callbacks, **kwargs) for url, method in items))
        else:
            results = await asyncio.gather(*(self.request(url=url, method=method, headers=headers, ratelimit=ratelimit, use_cache=use_cache, callbacks=callbacks, **kwargs) for url, method in items))
        return results


    async def get(self, url, **kwargs):
        return await self.request(url=url, method="GET", **kwargs)


    async def head(self, url, **kwargs):
        return await self.request(url=url, method="HEAD", **kwargs)


    async def options(self, url, **kwargs):
        return await self.request(url=url, method="OPTIONS", **kwargs)


    async def delete(self, url, **kwargs):
        return await self.request(url=url, method="DELETE", **kwargs)


    async def post(self, url, **kwargs):
        return await super().request(url=url, method="POST", **kwargs)


    async def put(self, url, **kwargs):
        return await super().request(url=url, method="PUT", **kwargs)


    async def patch(self, url, **kwargs):
        return await self.request(url=url, method="PATCH", **kwargs)



class AsyncClient(_AsyncClient):
    def __init__(self, headers=None, http2=True, random_user_agents=True, **kwargs):
        headers = headers if isinstance(headers, dict) else {}
        self._random_user_agents = random_user_agents
        session_kwargs = _get_valid_kwargs(_AsyncClient.__init__, kwargs)
        super().__init__(headers=headers, http2=http2, **session_kwargs)
        self._headers = headers


    async def __aenter__(self):
        return self


    async def __aexit__(self, *args):
        await self.aclose()


    async def request(self, method, url, *, headers=None, **kwargs):
        if self._random_user_agents:
            headers = headers or {}
            headers["User-Agent"] = useragent()
        return await super().request(method, url, headers=headers, **kwargs)