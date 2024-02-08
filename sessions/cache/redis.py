from .abstract import Cache
from ..config import SessionConfig as config

class RedisCache(Cache):
    __slots__ = ("_cache_conn")

    def __init__(
        self,
        instance: object,
        **kwargs
    ):
        self._instance = instance
        super().__init__(backend="redis", **kwargs)

    def __contains__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        return self._cache_conn.exists(key)

    @Cache.deserialize
    def __getitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        if config.renew_cache_on_get:
            value = self._cache_conn.getex(key, int(self.options.cache_timeout))
        else:
            value = self._cache_conn.get(key)

        if value is None:
            return value

        if self.options.compression:
            return self._decompress(value)

        return value

    @Cache.serialize
    def __setitem__(self, key, value):
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        if self.options.compression:
            value = self._compress(value)

        self._cache_conn.setex(key, int(self.options.cache_timeout), value)

    def __delitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        return self._cache_conn.delete(key)

    def clear(self):
        return self._cache_conn.flushdb()

    def keys(self):
        if self.options.decode_responses:
            return tuple(key for key in self._cache_conn.keys() if key.endswith("cache"))
        else:
            return tuple(key for key in self._cache_conn.keys() if key.endswith(b"cache"))

    def values(self):
        if self.options.decode_responses:
            return tuple(self._cache_conn.get(key) for key in self.keys() if key.endswith("cache"))
        else:
            return tuple(self._cache_conn.get(key) for key in self.keys() if key.endswith(b"cache"))

    def items(self):
        return tuple(zip(self.keys(), self.values()))

    def _cleanup(self):
        pass