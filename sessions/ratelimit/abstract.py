import time
from abc import ABC, abstractmethod
from inspect import iscoroutinefunction
from functools import wraps
from atexit import register as _register
from asyncio import sleep

import sqlite3
from redislite import Redis

from yarl import URL

from ..backends import *
from ..options import RatelimitOptions
from ..enums import RatelimitParams


class Ratelimit(ABC):
    """
    Abstract base class for implementing rate limiting functionality.

    Args:
        backend (str | None): The backend to use for rate limiting. Defaults to None.
        key (str | None): The key to use for rate limiting. Defaults to None.
        conn (_Redis | None): The connection object for the backend. Defaults to None.
        per_host (bool): Whether to apply rate limiting per host. Defaults to False.
        per_endpoint (bool): Whether to apply rate limiting per endpoint. Defaults to True.
        cache_timeout (float | int): The cache timeout in seconds. Defaults to 300.
        check_frequency (float | int): The frequency at which to check the rate limit. Defaults to 15.
        sleep_duration (float | int): The duration to sleep between rate limit checks. Defaults to 0.01.
        **kwargs: Additional keyword arguments to configure the rate limit options.

    Attributes:
        options (RatelimitOptions): The rate limit options object.
    """
    __slots__ = "_count", "_start_time", "_options", "_instance", "_ratelimit_type", "_backend", "_backend_options", "_cache", "_threadpool", "_pool", "_conn"
    ID = 0

    def __init__(
        self,
        backend:         str | None        = None,
        key:             str | None        = None,
        conn:            Redis | None      = None,
        per_host:        bool              = False,
        per_endpoint:    bool              = True,
        cache_timeout:   float | int       = 300,
        check_frequency: float | int       = 15,
        sleep_duration:  float | int       = 0.01,
        raise_errors:    bool              = False,
        **kwargs,
    ):
        Ratelimit.ID += 1
        kwargs = {
            "key":              key or f"{self.__class__.__name__}-{Ratelimit.ID}",
            "default":          self.default,
            "per_host":         per_host,
            "per_endpoint":     per_endpoint,
            "cache_timeout":    cache_timeout,
            "check_frequency":  check_frequency,
            "sleep_duration":   sleep_duration,
            "raise_errors":     raise_errors,
            **kwargs
        }
        if kwargs.get("ratelimit_options") is not None:
            kwargs = {**kwargs, **kwargs["ratelimit_options"]}

        self._count = 0
        self._start_time = time.time()

        self._options = RatelimitOptions.from_backend(backend, **kwargs)
        self._backend_options = BackendOptions.from_backend(backend, **kwargs)

        self.connect(conn=conn)

    def __repr__(self) -> str:
        fields = getattr(RatelimitParams, self._ratelimit_type.upper()).value
        values = (getattr(self, f"_{field}") for field in fields)
        items = ", ".join(f"{str(field)}: {str(value)}" for field, value in zip(fields, values))
        return f"<{self.options.backend.title()}{self.__class__.__name__} current_rate: {self.rate}, {items}>"

    def __str__(self) -> str:
        fields = getattr(RatelimitParams, self._ratelimit_type.upper()).value
        values = (getattr(self, f"_{field}") for field in fields)
        items = ", ".join(f"{str(field)}: {str(value)}" for field, value in zip(fields, values))
        return f"<{self.options.backend.title()}{self.__class__.__name__} current_rate: {self.rate}, {items}>"

    def connect(self, conn=None) -> None:
        self._pool = ConnectionPool.from_options(self.backend, self._backend_options)
        self._conn = self._pool.get_connection()
        if self.options.backend == "sqlite":
            self._create_tables()

    def _cleanup(self):
        self._pool.release(self._conn)

    def set_option(self, key, value) -> None:
        try:
            setattr(self, f"_{key}", value)
        except AttributeError:
            if key in self.options.__dict__:
                return self.options.override(key, value)
            raise AttributeError(f"Attribute {key} not found.")

    @property
    def default(self):
        return None

    @property
    def backend(self) -> str:
        return self.options.backend

    @property
    def cache(self):
        return self._conn

    @property
    def count(self):
        return self._count

    @property
    def params(self):
        return {param: getattr(self, f"_{param}") for param in getattr(RatelimitParams, self._ratelimit_type.upper()).value}

    @property
    def start_time(self):
        return self._start_time

    @property
    def rate(self):
        return self._count / (time.time() - self._start_time)

    @property
    def options(self):
        return self._options

    @property
    def key(self):
        return self.options.key

    @property
    def current_timestampns(self):
        return time.time_ns()

    @property
    def now(self):
        return time.time()

    def keys(self):
        if self.options.backend == "memory":
            return self._conn.keys("ratelimit")
        return self._pool.keys("ratelimit")

    def values(self):
        if self.options.backend == "memory":
            return self._conn.values("ratelimit")
        return self._pool.values("ratelimit")

    def items(self):
        if self.options.backend == "memory":
            return self._conn.items("ratelimit")
        return self._pool.items("ratelimit")

    # TODO : Fix this method to correctly clear the cache of the ratelimit
    def clear(self):
        if self.options.backend == "memory":
            return self.cache.clear()
        elif self.options.backend == "redis":
            return self.cache.flushdb()
        elif self.options.backend == "sqlite":
            return self.cache.clear()

    def _parse_url(self, url):
        try:
            url = URL(str(url))
        except:
            return None
        if self.options.per_host:
            url = f"{url.scheme}://{url.host}"
        elif self.options.per_endpoint:
            url = f"{url.scheme}://{url.host}{url.path}"
        return url

    def _parse_key(self, url=None, method=None, keys=None, **kwargs):
        url = self._parse_url(url)
        keys = keys if isinstance(keys, (list, tuple, set)) else []
        key = ":".join(str(value) for value in (self.options.key, method, *keys, url, "ratelimit") if value is not None)
        return key

    def _set_redis_key(self, key, func, *args, **kwargs):
        ret = func(key, *args, **kwargs)
        self.cache.expire(key, int(self.options.cache_timeout)) # type: ignore
        return ret

    def increment(self, url=None, method=None, keys=None, **kwargs):
        key = self._parse_key(url=url, method=method, keys=keys)
        while not self.ok(key):
            if self.options.raise_errors:
                raise InterruptedError("Rate limit exceeded.")
            time.sleep(self.options.sleep_duration)
            self._count += 1

    async def increment_async(self, url=None, method=None, keys=None, **kwargs):
        key = self._parse_key(url=url, method=method, keys=keys)
        while not self.ok(key):
            if self.options.raise_errors:
                raise InterruptedError("Rate limit exceeded.")
            await sleep(self.options.sleep_duration)
        self._count += 1

    @abstractmethod
    def ok(self):
        pass


class RatelimitDecoratorMixin:
    def __call__(self, func):
        if iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(**kwargs): # type: ignore
                await self.increment_async(**kwargs) # type: ignore
                return await func(**kwargs)
        else:
            @wraps(func)
            def wrapper(**kwargs):
                self.increment(**kwargs) # type: ignore
                return func(**kwargs)
        return wrapper