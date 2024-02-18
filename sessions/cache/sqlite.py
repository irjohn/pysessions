from time import time
from functools import wraps as wraps

from .abstract import Cache

def cache_expiration_trigger(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.options.cache_timeout:
            self._conn.cursor.execute("DELETE FROM cache WHERE expiration < strftime('%s', 'now');")
        result = func(self, *args, **kwargs)
        return result
    return wrapper

def commit(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._conn.commit()
        return result
    return wrapper

class SQLiteCache(Cache):
    __slots__ = "_conn",

    def __init__(
        self,
        instance,
        **kwargs
    ):
        self._instance = instance
        super().__init__(backend="sqlite", **kwargs)

    @commit
    def _create_tables(self):
        cursor = self._conn.cursor
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value BLOB,
            expiration FLOAT
            )
        """)
        if self.options.cache_timeout:
            cursor.execute("DELETE FROM cache WHERE expiration < strftime('%s', 'now');")

    @commit
    @cache_expiration_trigger
    def __contains__(self, key):
        cursor = self._conn.cursor
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        cursor.execute("SELECT key FROM cache WHERE key = ?", (key,))
        return bool(cursor.fetchone())

    @commit
    @Cache.deserialize
    def __getitem__(self, key):
        cursor = self._conn.cursor
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        cursor.execute("SELECT value,expiration FROM cache WHERE key = ?", (key,))
        value = cursor.fetchone()

        if value is not None:
            data, expiration = value
            if self.options.cache_timeout and expiration < time():
                del self[key]
                return None
            if self.options.compression:
                data = self._decompress(data)
            return data
        return None

    @commit
    @Cache.serialize
    def __setitem__(self, key, value):
        cursor = self._conn.cursor
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        if self.options.compression:
            value = self._compress(value)

        expiration = time() + self.options.cache_timeout if self.options.cache_timeout else 0
        cursor.execute("INSERT OR REPLACE INTO cache (key, value, expiration) VALUES (?, ?, ?)", (key, value, expiration))

    @commit
    @cache_expiration_trigger
    def __delitem__(self, key):
        cursor = self._conn.cursor
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))

    @commit
    def clear(self):
        cursor = self._conn.cursor
        return cursor.execute("DELETE FROM cache")

    @commit
    @cache_expiration_trigger
    def keys(self):
        cursor = self._conn.cursor
        cursor.execute("SELECT key FROM cache")
        return tuple(key[0] for key in cursor.fetchall())

    @commit
    @cache_expiration_trigger
    def values(self):
        cursor = self._conn.cursor
        cursor.execute("SELECT value FROM cache")
        return tuple(self._decompress(value[0]) if self.options.compression else value[0] for value in cursor.fetchall())

    @commit
    @cache_expiration_trigger
    def items(self):
        cursor = self._conn.cursor
        cursor.execute("SELECT key, value FROM cache")
        #return tuple((key, self._decompress(value)) if self.options.compression else (key, value) for key, value in cursor.fetchall())
        return tuple((key, value) for key, value in zip(self.keys(), self.values()))

    def _cleanup(self):
        self._pool.release(self._conn, recycle=False)
        self._pool.close_current_pool()