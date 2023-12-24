from httpx import (
    Client,
    Headers
)

from .useragents import UserAgents


class Session(Client):
    def __init__(self, headers={}, http2=True, **kwargs):
        super().__init__(headers=headers, http2=http2, **kwargs)
        self._headers = headers


    def __enter__(self):
        return self
    

    def __exit__(self, *args):
        self.close()
        return
    

    @property
    def headers(self):
        return Headers(UserAgents.headers | self._headers)


    @headers.setter
    def headers(self, value):
        self._headers = value


    def request(self, method, url, *, headers=None, **kwargs):
        return super().request(method, url, headers=headers or self.headers, **kwargs)


    def get(self, url, **kwargs):
        return super().request("GET", url, **kwargs)


    def head(self, url, **kwargs):
        return super().request("HEAD", url, **kwargs)


    def options(self, url, **kwargs):
        return super().request("OPTIONS", url, **kwargs)


    def delete(self, url, **kwargs):
        return super().request("DELETE", url, **kwargs)


    def post(self, url, **kwargs):
        return super().request("POST", url, **kwargs)
    

    def put(self, url, **kwargs):
        return super().request("PUT", url, **kwargs)
    

    def patch(self, url, **kwargs):
        return super().request("PATCH", url, **kwargs)