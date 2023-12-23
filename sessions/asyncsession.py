import orjson as json

from aiohttp.helpers import sentinel
from aiohttp import (
    ClientSession,
    HttpVersion11,
)

from httpx import (
    AsyncClient as _AsyncClient,
    Timeout,
    Limits
)

from .useragents import UserAgents


class AsyncSession(ClientSession):
    async def __aenter__(self):
        return self
    

    async def __aexit__(self, *args):
        await self.close()
        return


    @property
    def headers(self):
        return self._headers or UserAgents.headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    async def request(self, method, url, *, headers=None, **kwargs):
        return await super().request(method, url, headers=headers or self.headers, **kwargs)


    async def get(self, url, **kwargs):
        return await super().request("GET", url, **kwargs)


    async def head(self, url, **kwargs):
        return await super().request("HEAD", url, **kwargs)


    async def options(self, url, **kwargs):
        return await super().request("OPTIONS", url, **kwargs)


    async def delete(self, url, **kwargs):
        return await super().request("DELETE", url, **kwargs)


    async def post(self, url, **kwargs):
        return await super().request("POST", url, **kwargs)
    

    async def put(self, url, **kwargs):
        return await super().request("PUT", url, **kwargs)
    

    async def patch(self, url, **kwargs):
        return await super().request("PATCH", url, **kwargs)


class AsyncClient(_AsyncClient):
    def __init__(self, http2=True, **kwargs):
        super().__init__(http2=http2, **kwargs)


    async def __aenter__(self):
        return self
    

    async def __aexit__(self, *args):
        await self.aclose()
        return


    @property
    def headers(self):
        return self._headers or UserAgents.headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    async def request(self, method, url, *, headers=None, **kwargs):
        return await super().request(method, url, headers=headers or self.headers, **kwargs)


    async def get(self, url, **kwargs):
        return await super().request("GET", url, **kwargs)


    async def head(self, url, **kwargs):
        return await super().request("HEAD", url, **kwargs)


    async def options(self, url, **kwargs):
        return await super().request("OPTIONS", url, **kwargs)


    async def delete(self, url, **kwargs):
        return await super().request("DELETE", url, **kwargs)


    async def post(self, url, **kwargs):
        return await super().request("POST", url, **kwargs)
    

    async def put(self, url, **kwargs):
        return await super().request("PUT", url, **kwargs)
    

    async def patch(self, url, **kwargs):
        return await super().request("PATCH", url, **kwargs)