import os as _os

from signal import (
    SIGKILL as _SIGKILL
)
from atexit import (
    register as _register
)

from psutil import (
    Process as _Process,
    process_iter as _process_iter,
)

from subprocess import (
    Popen as _Popen, 
    DEVNULL as _DEVNULL
)

from time import (
    sleep as _ssleep
)

from asyncio import (
    Semaphore,
    sleep as _asleep
)

from databases import BaseAIORedis, BaseRedis

_NEED_TO_START = True
for process in _process_iter():
    if "redis-server unixsocket:/tmp/ratelimit.sock" in process.cmdline():
        _pid = process.id
        _NEED_TO_START = False
        _REDIS = _Process(_pid)


if _NEED_TO_START:
    _REDIS = _Process(
        _Popen([
            "redis-server", 
            "--port", "0", 
            "--unixsocket", "/tmp/ratelimit.sock", 
            "--unixsocketperm", "777", 
            "--save", "''"
        ], 
        stdout=_DEVNULL
        ).pid
    )


class ratelimit(BaseRedis):
    _REDIS = _REDIS

    def __init__(self, limit, window):
        self._limit = limit
        self._window = window * 1000000000
        super().__init__(unix_socket_path="/tmp/ratelimit.sock", db=0, decode_responses=False)


    def __call__(self, func):
        self._key = func.__name__
        def wrapped_func(*args, **kwargs):
            result = func(*args, **kwargs)
            self.increment()
            return result
        return wrapped_func


    @property
    def key(self):
        return self._key


    @property
    def limit(self):
        return self._limit
    

    @property
    def window(self):
        return self._window


    @property
    def edge(self):
        return self.current_timestampns - self.window


    @property
    def ok(self):
        self.zremrangebyscore(self._key, 0, self.edge)
        count = self.zcard(self._key)
        return count < self.limit


    @classmethod
    def _ratelimit_signal_handler(cls, signum=None, frame=None):
        cls._REDIS.send_signal(_SIGKILL)
        if _os.path.exists("/tmp/ratelimit.sock"):
            _os.remove("/tmp/ratelimit.sock")


    @classmethod    
    def _register_handlers(cls): 
        _register(cls._ratelimit_signal_handler)


    def increment(self):
        while not self.ok:
            _ssleep(1)

        ts = self.current_timestampns
        self.zadd(self._key, mapping={ts: ts})



class aratelimit(BaseAIORedis):
    _REDIS = _REDIS

    def __init__(self, limit,  window):
        self._limit = limit
        self._window = window * 1000000000
        self.semaphore = Semaphore(limit)
        super().__init__(unix_socket_path="/tmp/ratelimit.sock", db=0, decode_responses=False)


    def __call__(self, func):
        self._key = func.__name__
        async def wrapped_func(*args, **kwargs):
            result = await func(*args, **kwargs)
            await self.increment()
            return result
        return wrapped_func


    @property
    def key(self):
        return self._key
    

    @property
    def limit(self):
        return self._limit
    

    @property
    def window(self):
        return self._window


    @property
    def edge(self):
        return self.current_timestampns - self.window


    @classmethod
    def _aratelimit_signal_handler(cls, signum=None, frame=None):
        cls._REDIS.send_signal(_SIGKILL)
        if _os.path.exists("/tmp/ratelimit.sock"):
            _os.remove("/tmp/ratelimit.sock")


    @classmethod
    def _register_handlers(cls):
        _register(cls._aratelimit_signal_handler)


    async def ok(self):
        await self.zremrangebyscore(self._key, 0, self.edge)
        count = await self.zcard(self._key)
        return count < self.limit


    async def increment(self):
        async with self.semaphore:
            while not await self.ok():
                await _asleep(0)

            ts = self.current_timestampns
            await self.zadd(self._key, mapping={ts: ts})


class Ratelimit(ratelimit):
    def __call__(self):
        raise TypeError("'Ratelimit' object is not callable")


class ARatelimit(aratelimit):
    def __call__(self):
        raise TypeError("'Aratelimit' object is not callable")


ratelimit._register_handlers()
aratelimit._register_handlers()