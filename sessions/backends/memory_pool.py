__all__ = "InMemoryCache"

import time
from contextlib import contextmanager
from typing import Callable
from threading import Lock

from .abstract import ResourcePool
from .options import MemoryOptions
from ..validators import String, TypeOf, OneOf, Number
from ..objects import CacheData


class MemoryPool(ResourcePool):
    __slots__ = "_key", "_default", "_cache_timeout", "_check_frequency", "_time_to_check", "_options"
    ACCEPTED_KEYS = {"all", "cache", "ratelimit"}

    _lock = Lock()
    _cache = {}
    options: OneOf = TypeOf(MemoryOptions)
    key: String = String(minsize=1)
    default: TypeOf = TypeOf(Callable)
    check_frequency = Number(minvalue=0)
    cache_timeout = Number(minvalue=0)
    time_to_check = Number(minvalue=0)

    def __init__(
        self,
        options: MemoryOptions,
    ):
        self.options = options
        self.key = options.key
        self.default = options.default
        self.check_frequency = options.check_frequency
        self.cache_timeout = options.cache_timeout
        self.time_to_check = time.time() + self._check_frequency

    @property
    def lock(self):
        return self._lock

    def __repr__(self):
        """Returns a string representation of the cache."""
        return repr(dict(self._cache))

    def __getitem__(self, key):
        now = time.time()

        if self._cache_timeout > 0 and now >= self._time_to_check:
            with self._lock:
                self._clear_my_expired_cache(now)
            self._time_to_check = now + self._check_frequency

        if (value := self._cache.get(key)) is None:
            return self.__missing__(key)
        return value

    def __missing__(self, key):
        value = self._default(key)
        with self._lock:
            self._cache[key] = value
        return value

    def __setitem__(self, key, value):
        with self._lock:
            self._cache[key] = self._default(value)

    def __delitem__(self, key):
        """Deletes an item from the cache using the specified key."""
        with self._lock:
            del self._cache[key]

    def __contains__(self, key):
        """Checks if an item with the specified key is in the cache."""
        return key in self._cache

    @contextmanager
    def acquire(self):
        try:
            yield self
        finally:
            pass

    def release(self, conn, recycle=True):
        pass

    def create_connection(self):
        pass

    def get_connection(self):
        return self

    def close(self):
        pass

    @classmethod
    def clear(cls, key="cls"):
        """Clears the cache by removing all items."""
        assert key in cls.ACCEPTED_KEYS, f"Key '{key} is invalid. Must be one of {cls.ACCEPTED_KEYS}."

        if key == "all":
            cls._cache.clear()
        elif key == "cache":
            cls._cache = {key: data for key, data in cls._cache.items() if not isinstance(data, CacheData)}
        elif key == "ratelimit":
            cls._cache = {key: data for key, data in cls._cache.items() if isinstance(data, CacheData)}

    @classmethod
    def items(cls, key="all"):
        """
        Returns a tuple of (key, value) pairs representing all items in the cache.

        Returns:
            A tuple of (key, value) pairs.
        """
        assert key in cls.ACCEPTED_KEYS, f"Key '{key} is invalid. Must be one of {cls.ACCEPTED_KEYS}."

        if key == "all":
            return tuple((key, data.response) if isinstance(data, CacheData) else (key, data) for key, data in cls._cache.items())
        elif key == "cache":
            return tuple((key, data.response) for key, data in cls._cache.items() if isinstance(data, CacheData))
        else:
            return tuple((key, data) for key, data in cls._cache.items() if not isinstance(data, CacheData))

    @classmethod
    def keys(cls, key="all"):
        """
        Returns a tuple of all keys in the cache.

        Returns:
            A tuple of keys.
        """
        assert key in cls.ACCEPTED_KEYS, f"Key '{key} is invalid. Must be one of {cls.ACCEPTED_KEYS}."

        if key == "all":
            return cls._cache.keys()
        elif key == "cache":
            return tuple(key for key in cls._cache.keys() if isinstance(cls._cache[key], CacheData))
        else:
            return tuple(key for key in cls._cache.keys() if not isinstance(cls._cache[key], CacheData))

    @classmethod
    def values(cls, key="all"):
        """
        Returns a tuple of all values in the cache.

        Returns:
            A tuple of values.
        """
        assert key in cls.ACCEPTED_KEYS, f"Key '{key} is invalid. Must be one of {cls.ACCEPTED_KEYS}."

        if key == "all":
            return tuple(value.response if isinstance(value, CacheData) else value for value in cls._cache.values())
        elif key == "cache":
            return tuple(value for value in cls._cache.values() if isinstance(value, CacheData))
        else:
            return tuple(value for value in cls._cache.values() if not isinstance(value, CacheData))

    @classmethod
    def pop(cls, key, default=None):
        """
        Removes and returns the item with the specified key from the cache.

        If the key is not found in the cache, the default value is returned.

        Args:
            key: The key of the item to be removed.
            default: The value to be returned if the key is not found (default: None).

        Returns:
            The value of the removed item, or the default value if the key is not found.
        """
        return cls._cache.pop(key, default)

    def _clear_my_expired_cache(self, now: float):
        MemoryPool._cache = {key: data for key, data in self._cache.items() if data.expiration > now or key != self._key}

    @classmethod
    def _clear_expired_cache(cls, now: float):
        cls._cache = {key: data for key, data in cls._cache.items() if data.expiration > now}


class MemoryPoolManager:
    @classmethod
    def from_options(
        cls,
        options: MemoryOptions
    ):
        return MemoryPool(options)
