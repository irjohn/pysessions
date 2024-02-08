from time import time
from sqlite3 import connect
from functools import wraps as wraps

from .abstract import Cache

def cache_expiration_trigger(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.options.cache_timeout:
            self._cursor.execute("DELETE FROM cache WHERE expiration < strftime('%s', 'now');")
        result = func(self, *args, **kwargs)
        self._cache_conn.commit()
        return result
    return wrapper

def commit(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._cache_conn.commit()
        return result
    return wrapper

class SQLiteCache(Cache):
    __slots__ = ("_cache_conn")
    def __init__(
        self,
        instance,
        **kwargs
    ):
        self._instance = instance
        super().__init__(backend="sqlite", **kwargs)

    @property
    def newconn(self):
        return connect(self.options.db)

    @commit
    def _create_tables(self):
        self._cursor("""
            CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value BLOB,
            expiration FLOAT
            )
        """)
        if self.options.cache_timeout:
            self._cursor("DELETE FROM cache WHERE expiration < strftime('%s', 'now');")

    @commit
    @cache_expiration_trigger
    def __contains__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        self._cursor.execute("SELECT key FROM cache WHERE key = ?", (key,))
        return bool(self._cursor.fetchone())

    @commit
    @Cache.deserialize
    def __getitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        self._cursor.execute("SELECT value,expiration FROM cache WHERE key = ?", (key,))
        value = self._cursor.fetchone()

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
        if not key.endswith(":cache"):
            key = self._parse_key(key)

        if self.options.compression:
            value = self._compress(value)

        expiration = time() + self.options.cache_timeout if self.options.cache_timeout else 0
        self._cursor("INSERT OR REPLACE INTO cache (key, value, expiration) VALUES (?, ?, ?)", (key, value, expiration))

    @commit
    @cache_expiration_trigger
    def __delitem__(self, key):
        if not key.endswith(":cache"):
            key = self._parse_key(key)
        self._cursor("DELETE FROM cache WHERE key = ?", (key,))

    @commit
    def clear(self):
        return self._cursor("DELETE FROM cache")

    @commit
    @cache_expiration_trigger
    def keys(self):
        self._cursor.execute("SELECT key FROM cache")
        return tuple(key[0] for key in self._cursor.fetchall())

    @commit
    @cache_expiration_trigger
    def values(self):
        self._cursor.execute("SELECT value FROM cache")
        return tuple(self._decompress(value[0]) if self.options.compression else value[0] for value in self._cursor.fetchall())

    @commit
    @cache_expiration_trigger
    def items(self):
        self._cursor.execute("SELECT key, value FROM cache")
        return tuple((key, self._decompress(value)) if self.options.compression else (key, value) for key, value in self._cursor.fetchall())

    def _cleanup(self):
        pass