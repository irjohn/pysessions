from .abstract import Cache


class InMemoryCache(Cache):
    __slots__ = ("_cache_conn")

    def __init__(
        self,
        instance: object,
        **kwargs
    ):
        self._instance = instance
        super().__init__(backend="memory", **kwargs)

    def __contains__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        return self._conn.__contains__(key)

    @Cache.deserialize
    def __getitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        value = self._conn[key].response
        if value is None:
            return value

        if self.options.compression:
            value = self._decompress(value)

        return value

    @Cache.serialize
    def __setitem__(self, key, value):
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        if self.options.compression:
            value = self._compress(value)

        self._conn[key] = value

    def __delitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        del self._conn[key]

    def keys(self):
        return self._conn.keys()

    def values(self):
        return tuple(self._conn.values())

    def items(self):
        return tuple(self._conn.items())

    def clear(self):
        return self._conn.clear()

    def _cleanup(self):
        pass