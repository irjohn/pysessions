import sqlite3
from abc import ABC, abstractmethod
from atexit import register
from functools import wraps
from time import time
from zlib import compress, decompress

import orjson as json
from redislite import Redis

from ..objects import Response, CacheData
from ..options import CacheOptions
from ..backends import ConnectionPool, BackendOptions


class Cache(ABC):
    """
    Abstract base class for cache implementations.

    Attributes:
        options (CacheOptions): The cache options.
        _backend (str): The backend used for caching.
        _conn (InMemoryCacheObject | Redis | sqlite3.Connection): The cache object.
        _key (str): The cache key.
    """

    __slots__ = "options", "_instance", "_pool", "_conn", "backend_options"
    ID = 0

    def __init__(
        self,
        backend:         str | None                                   = None,
        key:             str | None                                   = None,
        conn:            dict | Redis | sqlite3.Connection | None     = None,
        cache_timeout:   float | int                                  = 3600,
        check_frequency: float | int                                  = 30,
        **kwargs,
    ):
        kwargs = {
            "key": key or "cache",
            "default": self.default,
            "cache_timeout": cache_timeout,
            "check_frequency": check_frequency,
            **kwargs
        }

        if kwargs.get("cache_options") is not None:
            kwargs = {**kwargs, **kwargs["cache_options"]}
        elif kwargs.get("cache") is not None:
            kwargs = {**kwargs, **kwargs["cache"]}
        self.options = CacheOptions.from_backend(backend=backend, **kwargs)
        self.backend_options = BackendOptions.from_backend(backend=backend, **kwargs)

        self.connect(conn)


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} cached={self.num_cached}>"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} cached={self.num_cached}>"

    def connect(self, conn):
        self._pool = ConnectionPool.from_options(self.backend, self.backend_options)
        self._conn = conn or self._pool.get_connection()
        if self.backend == "sqlite":
            self._create_tables()

    @property
    def conn(self):
        """
        Get the cache object based on the backend.

        Returns:
            CacheInMemoryCache | Redis | sqlite3.Connection: The cache object.
        """
        return self._cache_conn

    @property
    def backend(self) -> str:
        """
        Get the cache backend.

        Returns:
            str: The cache backend.
        """
        return self.options.backend

    @property
    def key(self) -> str:
        """
        Get the cache key.

        Returns:
            str: The cache key.
        """
        return self.options.key

    @property
    def num_cached(self) -> int:
        """
        Get the number of items cached.

        Returns:
            int: The number of items cached.
        """
        return len(self.keys())

    def set_option(self, key, value):
        try:
            setattr(self, f"_{key}", value)
        except AttributeError:
            if key in self.options.__dict__:
                return self.options.override(key, value)
            raise AttributeError(f"Attribute {key} not found.")

    def clear_cache(self):
        """
        Clear the cache.
        """
        self.cache.clear("cache")

    @staticmethod
    def serialize(func):
        @wraps(func)
        def wrapper(self, key, response):
            response = json.dumps(response.serialize())
            value = func(self, key, response)
            return value
        return wrapper

    @staticmethod
    def deserialize(func):
        @wraps(func)
        def wrapper(self, key):
            response = func(self, key)
            return Response.deserialize(json.loads(response)) if response is not None else response
        return wrapper

    def default(self, value=None):
        return CacheData(value, time() + self.options.cache_timeout)

    def _compress(self, value):
        return compress(value)

    def _decompress(self, value):
        return decompress(value)

    def _parse_key(self, url):
        """
        Parse the cache key.

        Args:
            url (str): The URL to parse.

        Returns:
            str: The parsed cache key.
        """
        return ":".join((self.options.key, url, "cache"))

    def _cleanup(self):
        """
        Clean up the cache.
        """
        if self.backend == "sqlite":
            self._pool.close_current_pool()

    @abstractmethod
    def __contains__(self, key):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __delitem__(self, key):
        pass

    @abstractmethod
    def _cleanup(self):
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def items(self):
        pass
