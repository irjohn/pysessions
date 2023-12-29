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

from databases import (
    BaseAIORedis as _BaseAIORedis, 
    BaseRedis as _BaseRedis,
)

_SOCKET_PATH = f"/tmp/ratelimit-{_os.getpid()}.sock"

_NEED_TO_START = True
for process in _process_iter():
    if f"redis-server unixsocket:{_SOCKET_PATH}" in process.cmdline():
        _pid = process.pid
        _NEED_TO_START = False
        _REDIS = _Process(_pid)


if _NEED_TO_START:
    _REDIS = _Process(
        _Popen([
            "redis-server", 
            "--port", "0", 
            "--unixsocket", _SOCKET_PATH, 
            "--unixsocketperm", "777", 
            "--save", "''"
        ], 
        stdout=_DEVNULL
        ).pid
    )

def _server_handler():
    _REDIS.send_signal(_SIGKILL)
    if _os.path.exists(_SOCKET_PATH):
        _os.remove(_SOCKET_PATH)


_register(_server_handler)

class ratelimit(_BaseRedis):
    _REDIS = _REDIS

    def __init__(self, limit, window):
        self._limit = limit
        self._window = window * 1000000000
        super().__init__(unix_socket_path=_SOCKET_PATH, db=0, decode_responses=False)


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


    def increment(self):
        while not self.ok:
            _ssleep(1)

        ts = self.current_timestampns
        self.zadd(self._key, mapping={ts: ts})



class aratelimit(_BaseAIORedis):
    _REDIS = _REDIS

    def __init__(self, limit,  window):
        self._limit = limit
        self._window = window * 1000000000
        self.semaphore = Semaphore(limit)
        super().__init__(unix_socket_path=_SOCKET_PATH, db=0, decode_responses=False)


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
        raise TypeError("'ARatelimit' object is not callable")