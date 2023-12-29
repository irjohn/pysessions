import asyncio as  _asyncio

from orjson import (
    dumps as _dumps,
)

from aiohttp import (
    ClientSession as _ClientSession,
)

from httpx import (
    AsyncClient as _AsyncClient,
)

from .ratelimit import (
    ARatelimit as _ARatelimit,
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
    

    async def __aexit__(self, *args):
        await self.close()
        return


    @property
    def headers(self):
        return _UserAgents.headers | self._headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    @staticmethod
    async def retrieve_response(resp):
        try:
            text = await resp.json()
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


    async def request(self, url, method, headers=None, **kwargs):
        async with super().request(method, url, headers=headers or self.headers, **kwargs) as response:                      
            resp = await self.retrieve_response(response)
            return _AsyncResponse(**resp)


    # NEEDS FIXED
    async def requests(self, urls, method="GET"):
        async with _asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(self.request(url, method=method) for url in urls))
        return tuple(task.result() for task in tasks)


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


class RatelimitAsyncSession(AsyncSession, _ARatelimit):
    _ID = 0

    def __init__(self, *args, limit=10, window=1, **kwargs):
        RatelimitAsyncSession._ID += 1
        self._limit = limit
        self._window = window
        AsyncSession.__init__(self, *args, **kwargs)
        _ARatelimit.__init__(self, limit, window)
        self._key = f"RatelimitAsyncSession:{self._ID}"

    
    async def request(self, url, method, headers=None, **kwargs):
        async with super(AsyncSession, self).request(method, url, headers=headers or self.headers, **kwargs) as response:                      
            resp = await self.retrieve_response(response)
            await self.increment()
            return _AsyncResponse(**resp)
    

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
    

class RatelimitAsyncClient(AsyncClient, _ARatelimit):
    _ID = 0

    def __init__(self, *args, limit=10, window=1, **kwargs):
        RatelimitAsyncClient._ID += 1
        self._limit = limit
        self._window = window
        AsyncClient.__init__(self, *args, **kwargs)
        _ARatelimit.__init__(self, limit, window)
        self._key = self._ID


    async def request(self, method, url, *, headers=None, **kwargs):
        results = await super().request(method, url, headers=headers or self.headers, **kwargs)
        await self.increment()
        return results