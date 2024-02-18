__all__ = "ConnectionPool", "BackendOptions"

from threading import current_thread, Lock

from .redis_pool import RedisPoolManager
from .sqlite_pool import SQLitePoolManager
from .memory_pool import MemoryPoolManager
from .options import BackendOptions

MAIN_THREAD_ID = current_thread().ident


class ConnectionPool:
    REDIS: RedisPoolManager             = RedisPoolManager()
    SQLITE: SQLitePoolManager           = SQLitePoolManager()
    MEMORY: MemoryPoolManager           = MemoryPoolManager()
    lock: Lock                          = Lock()

    @classmethod
    def from_options(cls, backend, options):
        with cls.lock:
            if backend == "sqlite":
                return cls.SQLITE.from_options(options)
            elif backend == "redis":
                return cls.REDIS.from_options(options)
            elif backend == "memory":
                return cls.MEMORY.from_options(options)
            else:
                raise ValueError(f"Invalid backend: {backend}")