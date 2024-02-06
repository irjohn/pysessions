__all__ = "RatelimitMixin", "ratelimit"

from inspect import signature

from .pyratelimit import PyRatelimitFactory, PyRatelimitDecoratorFactory
from .redis import RedisRatelimitFactory, RedisRatelimitDecoratorFactory
from .sqlite import SQLiteRatelimitFactory
from ..utils import get_valid_kwargs
from ..objects import Alias


def ratelimit_factory(instance, backend="memory", *args, **kwargs):
    keys = set(kwargs.keys())
    if any((alias := a) in keys for a in Alias.RATELIMIT_TYPE.value):
        type = kwargs.pop(alias)
    else:
        type = "slidingwindow"

    type = type.lower()
    type = Alias.validate_ratelimit_type(type)

    if backend in Alias.MEMORY.value:
        self = PyRatelimitFactory(instance, type=type, *args, **kwargs)
    elif backend in Alias.REDIS.value:
        self = RedisRatelimitFactory(instance, type=type, *args, **kwargs)
    elif backend in Alias.SQLITE.value:
        self =  SQLiteRatelimitFactory(instance, type=type, *args, **kwargs)
    else:
        raise NotImplementedError(f"Ratelimit backend {backend} is not implemented.")

    return self


class ratelimit:
    def __new__(cls, backend="memory", *args, **kwargs):
        keys = set(kwargs.keys())
        if any((alias := a) in keys for a in Alias.RATELIMIT_TYPE.value):
            type = kwargs.pop(alias)
        else:
            type = "slidingwindow"

        type = type.lower()
        type = Alias.validate_ratelimit_type(type)

        if backend in Alias.MEMORY.value:
            self = PyRatelimitDecoratorFactory(type=type, *args, **kwargs)
        elif backend in Alias.REDIS.value:
            self = RedisRatelimitDecoratorFactory(type=type, *args, **kwargs)
        else:
            raise NotImplementedError(f"Ratelimit backend {backend} is not implemented.")
        return self


class RatelimitMixin:
    def __init__(
        self,
        backend: str | None     = "memory",
        **kwargs
    ):
        self._backend = backend
        self._ratelimiter = ratelimit_factory(self, backend, **kwargs)
        kwargs["backend"] = backend

        if "kwargs" in signature(super().__init__).parameters:
            super().__init__(**kwargs)
        else:
            super().__init__(**get_valid_kwargs(super().__init__, kwargs))


    @property
    def ratelimiter(self):
        return self._ratelimiter

    @property
    def ratelimit(self):
        return self._ratelimiter

    @property
    def backend(self):
        return self._backend

    @property
    def ratelimit_type(self):
        return self._ratelimiter._ratelimit_type
