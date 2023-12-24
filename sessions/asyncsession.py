from os import (
    getpid as _getpid,
)

from asyncio import (
    gather as _gather,
)

from orjson import (
    dumps as _dumps,
)

from alive_progress import (
    alive_bar as _alive_bar,
)

from aiohttp import (
    ClientSession as _ClientSession,
)

from httpx import (
    AsyncClient as _AsyncClient,
)

from .useragents import (
    UserAgents as _UserAgents,
)

from .objects import (
    AsyncResponse as _AsyncResponse,
)


class AsyncSession(_ClientSession):
    def __init__(self, *args, headers={}, skip_auto_headers="User-Agent", **kwargs):
        self._headers = headers
        super().__init__(*args, headers=headers, json_serialize=_dumps, skip_auto_headers=skip_auto_headers, **kwargs)


    async def __aenter__(self):
        return self


    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if exc_traceback:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        await self.close()


    @property
    def headers(self):
        return _UserAgents.headers | self._headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    @staticmethod
    async def retrieve_response(resp):
        try:
            text = await resp.text()
        except:
            text = None
        try:
            json = await resp.json()
        except:
            json = None

        data = {
            "version": resp.version,
            "status": resp.status,
            "ok": resp.ok,
            "method": resp.method,
            "reason": resp.reason,
            "url": resp.url,
            "real_url": resp.real_url,
            "connection": resp.connection,
            "content": resp.content,
            "cookies": resp.cookies,
            "headers": resp.headers,
            "raw_headers": resp.raw_headers,
            "links": resp.links,
            "content_type": resp.content_type,
            "charset": resp.charset,
            "content_disposition": resp.content_disposition,
            "history": resp.history,
            "text": text,
            "json": json,
            "request_info": resp.request_info,
        }
        return data


    async def request(self, url, method, headers=None, *, bar=None, **kwargs):
        async with super().request(method, url, headers=headers or self.headers, **kwargs) as response:
            resp = await self.retrieve_response(response)
            if bar is not None:
                bar()
            return _AsyncResponse(**resp)


    # NEEDS FIXED
    async def requests(self, urls, method="GET", *, headers=None, progress=False, **kwargs):
        if progress:
            with _alive_bar(len(urls)) as bar:
                results = await _gather(*tuple(self.request(url, method, headers=headers, bar=bar, **kwargs) for url in urls))
        else:
            results = await _gather(*tuple(self.request(url, method, headers=headers, **kwargs) for url in urls))
        return results


    async def get(self, url, **kwargs):
        return await self.request(url, "GET", **kwargs)


    async def head(self, url, **kwargs):
        return await self.request(url, "HEAD", **kwargs)


    async def options(self, url, **kwargs):
        return await self.request(url, "OPTIONS", **kwargs)


    async def delete(self, url, **kwargs):
        return await self.request(url, "DELETE", **kwargs)


    async def post(self, url, **kwargs):
        return await self.request(url, "POST", **kwargs)


    async def put(self, url, **kwargs):
        return await self.request(url, "PUT", **kwargs)


    async def patch(self, url, **kwargs):
        return await self.request(url, "PATCH", **kwargs)



class AsyncClient(_AsyncClient):
    def __init__(self, headers={}, http2=True, **kwargs):
        super().__init__(headers=headers, http2=http2, **kwargs)
        self._headers = headers


    async def __aenter__(self):
        return self


    async def __aexit__(self, *args):
        await self.aclose()
        return


    @property
    def headers(self):
        return _UserAgents.headers | self._headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    async def request(self, method, url, *, headers=None, **kwargs):
        return await super().request(method, url, headers=headers or self.headers, **kwargs)


    async def get(self, url, **kwargs):
        return await self.request("GET", url, **kwargs)


    async def head(self, url, **kwargs):
        return await self.request("HEAD", url, **kwargs)


    async def options(self, url, **kwargs):
        return await self.request("OPTIONS", url, **kwargs)


    async def delete(self, url, **kwargs):
        return await self.request("DELETE", url, **kwargs)


    async def post(self, url, **kwargs):
        return await self.request("POST", url, **kwargs)


    async def put(self, url, **kwargs):
        return await self.request("PUT", url, **kwargs)


    async def patch(self, url, **kwargs):
        return await self.request("PATCH", url, **kwargs)