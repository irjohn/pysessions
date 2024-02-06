import sqlite3
from abc import ABC, abstractmethod
from atexit import register
from functools import wraps
from zlib import compress, decompress

import orjson as json
from redislite import Redis

from ..objects import Response, CacheOptions, CacheInMemoryCache


class Cache(ABC):
    """
    Abstract base class for cache implementations.

    Attributes:
        options (CacheOptions): The cache options.
        _backend (str): The backend used for caching.
        _conn (InMemoryCacheObject | Redis | sqlite3.Connection): The cache object.
        _key (str): The cache key.
    """

    __slots__ = ("options", "_instance", "_backend", "_key")

    def __init__(
        self,
        backend: str | None             = None,
        key: str | None                 = None,
        conn: Redis | None             = None,
        cache_timeout: float | int      = 3600,
        check_frequency: float | int    = 30,
        **kwargs,
    ):
        self._backend = backend
        self._key = key if isinstance(key, str) else "Session"

        kwargs = {
            "cache_timeout": cache_timeout,
            "check_frequency": check_frequency,
            **kwargs
        }

        if kwargs.get("cache_options") is not None:
            kwargs = {**kwargs, **kwargs["cache_options"]}
        elif kwargs.get("cache") is not None:
            kwargs = {**kwargs, **kwargs["cache"]}

        self.options = CacheOptions.from_backend(backend, **kwargs)

        if self._backend == "memory":
            if not hasattr(self._instance, "_memory_conn"):
                self._instance.__class__._cache_memory_conn = CacheInMemoryCache(options=self.options) # type: ignore

        elif self._backend == "redis":
            if not hasattr(self._instance, "_redis_conn") or not isinstance(self._instance._redis_conn, Redis):
                self._instance.__class__._redis_conn = conn or Redis(**self.options.redis_server_config())

        elif self._backend == "sqlite":
            assert self.options.db is not None, "Database file must be provided for SQLite cache."
            if not hasattr(self._instance, "_sqlite_conn") or not isinstance(self._instance._sqlite_conn, sqlite3.Connection):
                self._instance.__class__._sqlite_conn = conn or sqlite3.connect(self.options.db)
            if not hasattr(self, "_cursor"):
                self._cursor = self._instance._sqlite_conn.cursor()
            self._create_tables()

        register(self._cleanup)


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} cached={len(self.keys())}>"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} cached={len(self.keys())}>"


    @property
    def cache(self):
        """
        Get the cache object based on the backend.

        Returns:
            CacheInMemoryCache | Redis | sqlite3.Connection: The cache object.
        """
        if self._backend == "memory":
            return self._instance._cache_memory_conn
        elif self._backend == "redis":
            return self._instance._redis_conn
        elif self._backend == "sqlite":
            return self._instance._sqlite_conn

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

    def _compress(self, value):
        return compress(value)

    def _decompress(self, value):
        return decompress(value)

    def clear_cache(self):
        """
        Clear the cache.
        """
        self.cache.clear()

    def _parse_key(self, url):
        """
        Parse the cache key.

        Args:
            url (str): The URL to parse.

        Returns:
            str: The parsed cache key.
        """
        return ":".join((self._key, url, "cache"))