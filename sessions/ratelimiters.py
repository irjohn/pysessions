from aiomisc import asyncretry
from retry.api import retry

from .utils import ratelimit
from .asyncsession import AsyncSession
from .session import Session
from .proxysession import ProxySession
try:
    from .tor import TorSession
    _has_tor = True
except ImportError:
    _has_tor = False


def _retry(method):
    def outer(self, *args, **kwargs):
        @retry(self.exceptions, delay=self.pause)
        def inner():
            return method(self, *args, **kwargs)
        return inner()
    return outer


class RatelimitSession(Session):
    def __new__(cls, *args, **kwargs):
        instance = Session.__new__(cls)
        RatelimitSession.__init__(instance, *args, **kwargs)
        return instance


    def __init__(self, type="slidingwindow", capacity=10, window=1, exceptions=(InterruptedError,), pause=0, *args, **kwargs):
        self.exceptions = exceptions
        self.pause = pause
        self.ratelimiter = ratelimit(type, capacity, window)
        super().__init__(*args, **kwargs)


    @_retry
    def request(self, method, url, **kwargs):
        return self.ratelimiter(super().request)(method, url, **kwargs)


class RatelimitProxySession(ProxySession):
    def __init__(self, type="slidingwindow", capacity=10, window=1, exceptions=(InterruptedError,), pause=0, *args, **kwargs):
        self.exceptions = exceptions
        self.pause = pause
        self.ratelimiter = ratelimit(type, capacity, window)
        super().__init__(*args, **kwargs)


    @_retry
    def request(self, method, url, **kwargs):
        return self.ratelimiter(super().request)(method, url, **kwargs)


class RatelimitAsyncSession(AsyncSession):
    def __init__(self, type="slidingwindow", capacity=10, window=1, exceptions=(InterruptedError,), pause=0, *args, **kwargs):
        self.exceptions = exceptions
        self.pause = pause
        self.ratelimiter = ratelimit(type, capacity, window)
        self.retry = asyncretry(max_tries=None, exceptions=self.exceptions, pause=self.pause)
        super().__init__(*args, **kwargs)


    def request(self, method, url, **kwargs):
        return self.retry(self.ratelimiter(super().request))(method, url, **kwargs)


if _has_tor:
    class RatelimitTorSession(TorSession):
        def __init__(self, type="slidingwindow", capacity=10, window=1, exceptions=(InterruptedError,), pause=0, *args, **kwargs):
            self.exceptions = exceptions
            self.pause = pause
            self.ratelimiter = ratelimit(type, capacity, window)
            super().__init__(*args, **kwargs)


        @_retry
        def request(self, method, url, **kwargs):
            return self.ratelimiter(super().request)(method, url, **kwargs)