import traceback
import asyncio
from concurrent.futures import as_completed
from itertools import tee
from atexit import register as _register
from typing import (
    List,
    Tuple,
    Set,
    Generator,
)

from requests import Session as _Session
from alive_progress import alive_bar as _alive_bar
from httpx._exceptions import TimeoutException as _TimeoutException
from httpx import (
    Client as _HTTPXSession,
    Timeout as _HTTPXTimeout,
    Limits as _HTTPXLimits,
)

from .asyncsession import AsyncSession as _AsyncSession
from .thread import AsyncLoopThread
from .config import SessionConfig as config
from .meta import SessionMeta as _SessionMeta
from .useragents import useragent
from .objects import (
    Response,
    Timeouts as _Timeouts
)
from .utils import (
    take as _take,
    get_valid_kwargs as _get_valid_kwargs,
)



class Session(_HTTPXSession, metaclass=_SessionMeta):
    _ID = 0

    def __init__(
        self,
        headers: dict                           = None,
        http2: bool                             = True,
        random_user_agents: bool                = True,
        threaded: bool                          = True,
        **kwargs
    ):
        """
        Initializes a Session object.

        Args:
            headers (dict, optional): Custom headers to be included in the requests. Defaults to None.
            http2 (bool, optional): Flag indicating whether to use HTTP/2. Defaults to True.
            random_user_agents (bool, optional): Flag indicating whether to use random user agents. Defaults to True.
            **kwargs: Additional keyword arguments to be passed to the _HTTPXSession constructor.
        """
        Session._ID += 1
        self._id = Session._ID

        self._threaded = threaded
        self._raise_errors = kwargs.pop("raise_errors", None) or config.raise_errors
        self._headers = headers if isinstance(headers, dict) else {}
        self._random_user_agents = random_user_agents

        if self._threaded:
            kwargs["timeout"] = kwargs.pop("timeout", None) or config.threaded_timeout
            self._loop = asyncio.new_event_loop()
            self._thread = AsyncLoopThread(target=self.__start_event_loop, name=f"Session {self._id}-EventLoopThread", daemon=True)
            self._thread.start()

        self.__kwargs = kwargs.copy()
        kwargs = self._parse_kwargs(kwargs)

        kwargs = _get_valid_kwargs(_HTTPXSession.__init__, kwargs)
        super().__init__(http2=http2, headers=self._headers, **kwargs)


    def __call__(self):
        self.__kwargs["threaded"] = False
        return self.__class__(**self.__kwargs)

    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_traceback:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        self._cleanup()


    def _cleanup(self):
        if self._threaded and hasattr(self, "_loop"):
            self._thread.stop()
            self._loop.close()
        self.close()


    def _parse_kwargs(self, kwargs):
        keys = set(kwargs.keys())
        timeouts = set(_take(lambda x: x in _Timeouts.HTTPX.value, keys))
        limits = set(_take(lambda x: x in {"max_keepalive", "max_connections", "max_concurrent_requests", "limits"}, keys))

        if timeouts:
            if "timeout" in timeouts and isinstance(kwargs["timeout"], _HTTPXTimeout):
                pass
            else:
                args = {}
                if "connect_timeout" in timeouts and (connect := kwargs.pop("connect_timeout", "None")) != "None":
                    args["connect"] = connect

                if "read_timeout" in timeouts and (read := kwargs.pop("read_timeout", "None")) != "None":
                    args["read"] = read

                if "write_timeout" in timeouts and (write := kwargs.pop("write_timeout", "None")) != "None":
                    args["write"] = write

                if "pool_timeout" in timeouts and (pool := kwargs.pop("pool_timeout", "None")) != "None":
                    args["pool"] = pool

                kwargs["timeout"] = _HTTPXTimeout(
                    timeout=kwargs.pop("timeout", 5),
                    **args
                )

        if limits:
            if "limits" in limits:
                if isinstance(kwargs["limits"], _HTTPXLimits):
                    pass
                else:

                    kwargs["limits"] = _HTTPXLimits(
                        max_keepalive_connections       = kwargs.pop("max_keepalive_connections", None),
                        max_connections                 = kwargs.pop("max_connections", None),
                        keepalive_expiry                = kwargs.pop("keepalive_expiry", 5),
                    )
        return kwargs


    def _retrieve_response(self, resp, callbacks, bar):
        response = Response(**{
            "version":  resp.http_version,
            "status":   resp.status_code,
            "ok":       resp.status_code < 400,
            "method":   resp.request.method,
            "reason":   resp.reason_phrase,
            "url":      resp.url,
            "content":  resp.content,
            "encoding": resp.encoding,
            "cookies":  resp.cookies,
            "headers":  resp.headers,
            "history":  resp.history,
            "request":  resp.request,
            "elapsed":  resp.elapsed,
        })
        return self._run_callbacks(response, callbacks, bar)


    def request(self, method, url, *, headers=None, threaded=False, bar=None, callbacks=None, **kwargs):
        """
        Sends an HTTP request.

        Args:
            method (str): The HTTP method to be used.
            url (str): The URL to send the request to.
            headers (dict, optional): Custom headers to be included in the request. Defaults to None.
            bar (callable, optional): A progress bar function. Defaults to None.
            **kwargs: Additional keyword arguments to be passed to the super().request method.

        Returns:
            The response from the HTTP request.
        """
        if self._random_user_agents:
            headers = headers if isinstance(headers, dict) else {}
            headers["User-Agent"] = useragent()

        kwargs = _get_valid_kwargs(super().request, kwargs)
        try:
            response = super().request(method=method, url=url, headers=headers, **kwargs)
            return self._retrieve_response(response, callbacks, bar)
        except _TimeoutException as e:
            if self._raise_errors:
                raise e
            return Response(status=408, ok=False, reason="Request Timeout", url=url, errors=e)
        except Exception as e:
            if self._raise_errors:
                raise e
            return Response(status=500, ok=False, reason="Internal Server Error", url=url, errors=e)

    def __async_session(self):
        class AsyncSession(*(base for name, base in self.__bases__.items() if name.endswith("Mixin")), _AsyncSession):
            pass
        return AsyncSession(loop=self._loop, **self.__kwargs)

    def __start_event_loop(self):
        asyncio.set_event_loop(self._loop)
        return self._loop

    async def __requests(self, urls, method="GET", headers=None, progress=None, callbacks=None, **kwargs):
        async with self.__async_session() as session:
            return await session.requests(urls=urls, method=method, headers=headers, progress=progress, callbacks=callbacks, **kwargs)

    def requests(
        self,
        urls:   str | List[str] | Tuple[str, ...] | Set[str] | Generator[str, None, None],
        method: str | List[str] | Tuple[str, ...] | Set[str] | Generator[str, None, None]       = "GET",
        headers: dict | None                                                                    = None,
        progress: bool                                                                          = True,
        threaded: bool                                                                          = True,
        callbacks: List[callable] | Tuple[callable, ...] | Set[callable]                        = None,
        **kwargs
    ):
            """
            Sends multiple HTTP requests asynchronously.

            Args:
                urls (list or tuple): List of URLs to send requests to.
                method (str or list or tuple, optional): HTTP method to use for the requests. Defaults to "GET".
                headers (dict, optional): Headers to include in the requests. Defaults to None.
                progress (bool, optional): Whether to display progress bar. Defaults to True.
                threaded (bool, optional): Whether to use threaded execution. Defaults to True.
                callbacks (list or tuple, optional): List of callback functions to execute after each request. Defaults to None.
                **kwargs: Additional keyword arguments to pass to the requests.

            Returns:
                tuple: A tuple of the results from each request.

            """
            if self._threaded and threaded:
                future = asyncio.run_coroutine_threadsafe(self.__requests(urls=urls, method=method, headers=headers, progress=progress, callbacks=callbacks, **kwargs), self._loop)
                return tuple(future.result() for future in as_completed((future,)))[0]

            if isinstance(urls, str):
                urls = (urls,)

            if not isinstance(method, str) and isinstance(method, (list, tuple)):
                items = zip(urls, method)
            else:
                items = ((url, method) for url in urls)

            if progress:
                items, items_ = tee(items)
                item_length = sum(1 for _ in items_)

                with _alive_bar(item_length) as bar:
                        results = tuple(self.request(method=method, url=url, headers=headers, callbacks=callbacks, bar=bar, **kwargs) for url, method in items)
            else:
                results = tuple(self.request(method=method, url=url, headers=headers, callbacks=callbacks, **kwargs) for url, method in items)

            return results


    def get(self, url, **kwargs):
        """
        Sends an HTTP GET request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="GET", url=url, **kwargs)


    def head(self, url, **kwargs):
        """
        Sends an HTTP HEAD request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="HEAD", url=url, **kwargs)


    def options(self, url, **kwargs):
        """
        Sends an HTTP OPTIONS request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="OPTIONS", url=url, **kwargs)


    def delete(self, url, **kwargs):
        """
        Sends an HTTP DELETE request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="DELETE", url=url, **kwargs)


    def post(self, url, **kwargs):
        """
        Sends an HTTP POST request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="POST", url=url, **kwargs)


    def put(self, url, **kwargs):
        """
        Sends an HTTP PUT request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="PUT", url=url, **kwargs)


    def patch(self, url, **kwargs):
        """
        Sends an HTTP PATCH request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="PATCH", url=url, **kwargs)


class RequestsSession(_Session, metaclass=_SessionMeta):
    def __init__(
        self,
        headers=None,
        random_user_agents=True,
        threaded=False,
        **kwargs
    ):
        """
        Initializes a Session object.

        Args:
            headers (dict, optional): Custom headers to be included in the requests. Defaults to None.
            http2 (bool, optional): Flag indicating whether to use HTTP/2. Defaults to True.
            random_user_agents (bool, optional): Flag indicating whether to use random user agents. Defaults to True.
            **kwargs: Additional keyword arguments to be passed to the _HTTPXSession constructor.
        """
        super().__init__()
        self._headers = headers if isinstance(headers, dict) else {}
        self._random_user_agents = random_user_agents
        kwargs = _get_valid_kwargs(_HTTPXSession.__init__, kwargs)

        self._threaded = threaded
        if self._threaded:
            kwargs["timeout"] = config.threaded_timeout
            self._loop = asyncio.new_event_loop()
            self._thread = AsyncLoopThread(target=self.__start_event_loop, name=f"Session {self._id}-EventLoopThread", daemon=True)
            self._thread.start()
            _register(self._cleanup)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_traceback:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        self._cleanup()
        self.close()

    def _cleanup(self):
        if self._threaded and hasattr(self, "_loop"):
            self._thread.stop()
            self._loop.close()


    @staticmethod
    def _retrieve_response(resp):
        return Response(**{
            "status": resp.status_code,
            "ok": resp.ok,
            "method": resp.request.method,
            "reason": resp.reason,
            "url": resp.url,
            "content": resp.content,
            "encoding": resp.encoding,
            "cookies": resp.cookies,
            "headers": resp.headers,
            "links": resp.links,
            "history": resp.history,
            "request": resp.request,
            "elapsed": resp.elapsed,
        })

    def request(self, method, url, *, headers=None, threaded=False, bar=None, **kwargs):
        """
        Sends an HTTP request.

        Args:
            method (str): The HTTP method to be used.
            url (str): The URL to send the request to.
            headers (dict, optional): Custom headers to be included in the request. Defaults to None.
            bar (callable, optional): A progress bar function. Defaults to None.
            **kwargs: Additional keyword arguments to be passed to the super().request method.

        Returns:
            The response from the HTTP request.
        """
        if self._threaded and threaded:
            return self._request(method, url, headers=headers, bar=bar, **kwargs)

        if self._random_user_agents:
            headers = headers if isinstance(headers, dict) else {}
            headers["User-Agent"] = useragent()
        kwargs = _get_valid_kwargs(super().request, kwargs)
        results = super().request(method=method, url=url, headers=headers, **kwargs)
        if bar is not None:
            bar()
        return self._retrieve_response(results)


    def requests(self, urls, method="GET", *, headers=None, threaded=True, progress=True, **kwargs):
        """
        Sends multiple HTTP requests.

        Args:
            urls (iterable): An iterable of URLs to send the requests to.
            method (str, optional): The HTTP method to be used. Defaults to "GET".
            headers (dict, optional): Custom headers to be included in the requests. Defaults to None.
            progress (bool, optional): Flag indicating whether to show a progress bar. Defaults to False.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            A tuple of responses from the HTTP requests.
        """

        if not isinstance(method, str) and isinstance(method, (list, tuple)):
            items = zip(urls, method)
        else:
            items = ((url, method) for url in urls)

        if progress:
            items, items_ = tee(items)
            item_length = sum(1 for _ in items_)
            with _alive_bar(item_length) as bar:
                if self._threaded and threaded:
                    futures = tuple(self._request(method=method, url=url, headers=headers, bar=bar, **kwargs) for url, method in items)
                    results = tuple(future.result() for future in as_completed(futures))
                else:
                    results = tuple(self.request(method=method, url=url, headers=headers, bar=bar, **kwargs) for url, method in items)
        else:
            if self._threaded and threaded:
                futures = tuple(self._request(method=method, url=url, headers=headers, **kwargs) for url, method in items)
                results = tuple(future.result() for future in as_completed(futures))
            else:
                results = tuple(self.request(method=method, url=url, headers=headers, **kwargs) for url, method in items)
        return results


    def get(self, url, **kwargs):
        """
        Sends an HTTP GET request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="GET", url=url, **kwargs)


    def head(self, url, **kwargs):
        """
        Sends an HTTP HEAD request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="HEAD", url=url, **kwargs)


    def options(self, url, **kwargs):
        """
        Sends an HTTP OPTIONS request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="OPTIONS", url=url, **kwargs)


    def delete(self, url, **kwargs):
        """
        Sends an HTTP DELETE request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="DELETE", url=url, **kwargs)


    def post(self, url, **kwargs):
        """
        Sends an HTTP POST request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="POST", url=url, **kwargs)


    def put(self, url, **kwargs):
        """
        Sends an HTTP PUT request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="PUT", url=url, **kwargs)


    def patch(self, url, **kwargs):
        """
        Sends an HTTP PATCH request.

        Args:
            url (str): The URL to send the request to.
            **kwargs: Additional keyword arguments to be passed to the request method.

        Returns:
            The response from the HTTP request.
        """
        return self.request(method="PATCH", url=url, **kwargs)