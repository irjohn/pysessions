from os import (
    getpid as _getpid,
)

from httpx import (
    Client as _Client,
)


from alive_progress import (
    alive_bar as _alive_bar,
)

from .ratelimit import (
    Ratelimit as _Ratelimit
)

from .useragents import (
    UserAgents as _UserAgents
)


class Session(_Client):
    def __init__(self, headers={}, http2=True, **kwargs):
        super().__init__(http2=http2, **kwargs)
        self._headers = {k.title(): v for k, v in headers.items()}


    def __enter__(self):
        return self
    

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_traceback:
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        self.close()
    

    @property
    def headers(self):
        return _UserAgents.headers | self._headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    def request(self, method, url, *, headers=None, bar=None, **kwargs):
        results = super().request(method, url, headers=headers or self.headers, **kwargs)
        if bar is not None:
            bar()
        return results
    

    def requests(self, urls, method="GET", headers=None, progress=False, **kwargs):
        if progress:
            with _alive_bar(len(urls)) as bar:
                results = tuple(self.request(method, url, headers=headers, bar=bar, **kwargs) for url in urls)
        else:
            results = tuple(self.request(method, url, headers=headers, **kwargs) for url in urls)
        return results


    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)


    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)


    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)


    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)


    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)
    

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)
    

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)
    


class RatelimitSession(Session, _Ratelimit):
    _ID = 0

    def __init__(self, *args, limit=10, window=1, **kwargs):
        RatelimitSession._ID += 1
        self._limit = limit
        self._window = window
        Session.__init__(self, *args, **kwargs)
        _Ratelimit.__init__(self, limit, window)
        self._key = f"RatelimitSession:{self._ID}:{_getpid()}"

    
    def request(self, method, url, *, headers=None, **kwargs):
        result =  super().request(method, url, headers=headers or self.headers, **kwargs)
        self.increment()
        return result