__all__ = "RedisPoolManager"

from shutil import rmtree
from pathlib import Path
from contextlib import contextmanager
from atexit import register

import redis
import redislite

from .abstract import ResourcePool
from .options import RedisOptions
from ..validators import TypeOf, Number


class RedisPool(ResourcePool):
    __slots__ = "_pool", "_expiration" "_idle_timeout", "_idle_check_time", "_options"

    options:    RedisOptions                             = TypeOf(RedisOptions)
    pool:       redislite.Redis                          = TypeOf(redislite.Redis, redis.Redis)
    #expiration: Number                                   = Number(minvalue=0)

    def __init__(
        self,
        options: RedisOptions
    ):
        self.options = options
        self.pool = redislite.Redis(**self._options)
        #self.expiration = time.time()
        register(self.close)

    @contextmanager
    def acquire(self):
        yield self._pool

    def release(self, conn, recycle=True):
        pass

    def get_connection(self):
        return self._pool

    def create_connection(self):
        pass

    def keys(self, key):
        key = bytes(key.encode("utf-8")) if self.options.decode_responses else key
        return tuple(key for key in self._pool.keys() if key.endswith(key))

    def values(self, key):
        key = bytes(key.encode("utf-8")) if self.options.decode_responses else key
        values = []
        for key in self.keys(key):
            data_type = self._pool.type(key)
            if data_type == b"string" or data_type == "string":
                value = self._pool.get(key)
                values.append(value)
            elif data_type == b"hash" or data_type == "hash":
                values = self._pool.hvals(key)
                values.extend([v for v in values])
            elif data_type == b"zset" or data_type == "zset":
                values = self._pool.zrange(key, 0, -1)
                values.extend([v for v in values])
        return tuple(values)

    def items(self, key):
        return tuple(zip(self.keys(key), self.values(key)))

    def close(self):
        if hasattr(self._pool, "socket_file"):
            self._pool._cleanup()
            self._pool.shutdown()
            tmp = Path(self._pool.socket_file).parent
            if tmp.exists() and "tmp" in tmp.parts:
                rmtree(tmp)
        else:
            self._pool.close()

class RedisPoolManager:
    __slots__ = "_pools"

    pools: TypeOf                                       = TypeOf(dict)

    def __init__(
        self,
        **kwargs
    ):
        self.pools = {}

    def from_options(
        self,
        options: RedisOptions
    ):
        if (pool := self.pools.get(options)) is not None:
            return pool
        self.pools[options] = RedisPool(options)
        return self.pools[options]