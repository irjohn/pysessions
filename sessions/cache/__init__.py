__all__ = "CacheMixin", "cache_factory"

from inspect import signature

from .pycache import InMemoryCache
from .redis import RedisCache
from .sqlite import SQLiteCache
from ..utils import get_valid_kwargs
from ..objects import Alias


def cache_factory(instance, backend="memory", *args, **kwargs):
    if backend in Alias.MEMORY.value:
        self = InMemoryCache(instance, *args, **kwargs)
    elif backend in Alias.REDIS.value:
        self = RedisCache(instance, *args, **kwargs)
    elif backend in Alias.SQLITE.value:
        self = SQLiteCache(instance, *args, **kwargs)
    else:
        raise NotImplementedError(f"Cache backend {backend} is not implemented.")

    return self


class CacheMixin():
    def __init__(
        self,
        backend: str                    = "memory",
        **kwargs
    ):
        self._backend = backend
        self._cache = cache_factory(self, backend=backend, **kwargs)
        kwargs["backend"] = backend

        if "kwargs" in signature(super().__init__).parameters:
            super().__init__(**kwargs)
        else:
            super().__init__(**get_valid_kwargs(super().__init__, kwargs))

    @property
    def cache(self):
        return self._cache

    @property
    def backend(self):
        return self._backend