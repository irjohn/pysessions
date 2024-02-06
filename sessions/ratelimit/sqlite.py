import sqlite3
from time import time
from dataclasses import make_dataclass, field, astuple
from functools import partial

from .abstract import Ratelimit


class TokenBucket(Ratelimit):
    """
    A token bucket implementation for rate limiting.

    Args:
        capacity (float | int): The maximum number of tokens the bucket can hold. Defaults to 10.
        fill_rate (float | int): The rate at which tokens are added to the bucket per second. Defaults to 1.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Attributes:
        _capacity (float | int): The maximum number of tokens the bucket can hold.
        _fill_rate (float | int): The rate at which tokens are added to the bucket per second.
    """

    __slots__ = ("_capacity", "_fill_rate")
    __attrs__ = ("key", "tokens", "last_check", "expiration")
    __dc__ = make_dataclass("TokenBucketCache", fields=(("key", str), ("tokens", float), ("last_check", float), ("expiration", float)), slots=True, eq=False)

    def __init__(
        self,
        capacity: float | int           = 10,
        fill_rate: float | int          = 1,
        key: str | None                 = None,
        conn: sqlite3.Connection | None = None,
        **kwargs
    ):
        super().__init__(backend="sqlite", key=key, conn=conn, **kwargs)
        self._capacity = capacity
        self._fill_rate = fill_rate

    def default(self):
        """
        Returns the default token bucket data.

        Returns:
            dict: The default token bucket data, including the initial number of tokens, last check time, and expiration time.
        """
        return dict(
            tokens=self._capacity,
            last_check=self.now,
            expiration=time() + self.options.cache_timeout if self.options.cache_timeout else 0
        )

    def get_tokens(self, key):
        """
        Retrieves the number of tokens from the token bucket for the given key.

        Args:
            key: The key associated with the token bucket.

        Returns:
            TokenBucketCache: The token bucket data, including the number of tokens, last check time, and expiration time.
        """
        # Retrieve data
        data = self[key]

        # Calculate the time elapsed since the last fill
        current = time()
        elapsed = current - data.last_check # type: ignore

        # Calculate the number of tokens to add based on the fill rate
        to_add = elapsed * (self._fill_rate / self._capacity)

        # Set the new number of tokens (up to capacity)
        data.tokens = min(self._capacity, data.tokens + to_add) # type: ignore
        data.last_check = current # type: ignore
        return data


    def ok(self, key):
        """
        Checks if a token can be consumed from the token bucket for the given key.

        Args:
            key: The key associated with the token bucket.

        Returns:
            bool: True if a token can be consumed, False otherwise.
        """
        output = False
        data = self.get_tokens(key)

        if data.tokens >= 1: # type: ignore
            data.tokens -= 1 # type: ignore
            output = True

        self[key] = data
        return output


# The `LeakyBucket` class is a decorator that implements a rate limit for a given function
# using the leaky bucket algorithm.
class LeakyBucket(Ratelimit):
    """
    A class representing a leaky bucket rate limiter.

    The leaky bucket algorithm is a rate limiting algorithm that allows a certain number of requests
    to be processed per unit of time. If the bucket is full, additional requests are either discarded
    or delayed.

    Args:
        capacity (float | int): The maximum capacity of the bucket.
        leak_rate (float | int): The rate at which the bucket leaks requests.

    Attributes:
        _capacity (float | int): The maximum capacity of the bucket.
        _leak_rate (float | int): The rate at which the bucket leaks requests.
    """

    __slots__ = ("_capacity", "_leak_rate")
    __attrs__ = ("key", "content", "last_check", "expiration")
    __dc__ = make_dataclass("LeakyBucketCache", fields=(("key", str), ("content", float), ("last_check", float), ("expiration", float, field(default=0.0))), slots=True, eq=False)

    def __init__(
        self,
        capacity: float | int           = 10,
        leak_rate: float | int          = 5,
        key: str | None                 = None,
        conn: sqlite3.Connection | None = None,
        **kwargs
    ):
        super().__init__(backend="sqlite", key=key, conn=conn, **kwargs)
        self._capacity = capacity
        self._leak_rate = leak_rate

    def default(self):
        return dict(
            content=0,
            last_check=self.now,
            expiration=time() + self.options.cache_timeout if self.options.cache_timeout else 0
        )

    def _leak(self, key):
        """
        Leaks the appropriate amount of requests from the specified key.

        Args:
            key: The key to leak requests from.

        Returns:
            The updated data object after leaking requests.
        """
        data = self[key]

        # Calculate the amount of time that has passed
        current_time = time()
        elapsed = current_time - data.last_check # type: ignore
        data.last_check = current_time # type: ignore

        # Leak the appropriate amount of requests
        data.content -= elapsed * self._leak_rate # type: ignore
        data.content = max(data.content, 0) # type: ignore
        return data


    def ok(self, key):
        """
        Checks if the given key is within the rate limit capacity and updates the count if it is.

        Args:
            key (str): The key to check against the rate limit.

        Returns:
            bool: True if the key is within the rate limit capacity and the count is updated, False otherwise.
        """
        output = False
        data = self._leak(key)

        if data.content < self._capacity: # type: ignore
            data.content += 1 # type: ignore
            output = True

        self[key] = data
        return output


class SlidingWindow(Ratelimit):
    """
    A sliding window rate limiter implementation.

    This class provides rate limiting functionality based on a sliding window algorithm.
    It tracks the number of requests made within a specified time window and enforces a limit on the number of requests allowed.

    Attributes:
        _limit (int): The maximum number of requests allowed within the time window.
        _window (float | int): The time window (in seconds) within which the requests are counted.

    Methods:
        __init__(self, limit: int = 10, window: float | int = 1.0, **kwargs): Initializes the SlidingWindow rate limiter.
        default(self): Returns the default rate limit data for a key.
        ok(self, key): Checks if the given key is allowed to proceed based on the rate limit rules.

    Example usage:
        sliding_window = SlidingWindow(limit=10, window=1.0)
        if sliding_window.ok("user123"):
            # Allow the request to proceed
        else:
            # Rate limit exceeded, reject the request
    """

    __slots__ = ("_limit", "_window")
    __attrs__ = ("key", "cur_time", "cur_count", "pre_count", "expiration")
    __dc__ = make_dataclass("SlidingWindowCache", fields=(("key", str), ("cur_time", float), ("cur_count", int), ("pre_count", int), ("expiration", float, field(default=0.0))), slots=True, eq=False)

    def __init__(
        self,
        limit: int                      = 10,
        window: float | int             = 1.0,
        key: str | None                 = None,
        conn: sqlite3.Connection | None = None,
        **kwargs
    ):
        super().__init__(backend="sqlite", key=key, conn=conn, **kwargs)
        self._limit = limit
        self._window = window

    def default(self):
        return dict(
            cur_time=self.now,
            cur_count=0,
            pre_count=self._limit,
            expiration=time() + self.options.cache_timeout if self.options.cache_timeout else 0
        )

    def ok(self, key):
        """
        Checks if the given key is allowed to proceed based on the rate limit rules.

        Args:
            key: The key to check for rate limiting.

        Returns:
            bool: True if the key is allowed to proceed, False otherwise.
        """
        output = False
        data = self[key]

        if ((time_ := time()) - data.cur_time) > self._window: # type: ignore
            data.cur_time = time_ # type: ignore
            data.pre_count = data.cur_count # type: ignore
            data.cur_count = 0 # type: ignore

        ec = (data.pre_count * (self._window - (time() - data.cur_time)) / self._window) + data.cur_count # type: ignore

        if ec < self._limit:
            data.cur_count += 1 # type: ignore
            output = True

        self[key] = data
        return output


class FixedWindow(Ratelimit):
    """
    Represents a fixed window rate limiter.

    Attributes:
        _limit (int): The maximum number of requests allowed within the window.
        _window (float | int): The duration of the window in seconds.
    """

    __slots__ = ("_limit", "_window")
    __attrs__ = ("key", "window_start", "requests", "expiration")
    __dc__ = make_dataclass("FixedWindowCache", fields=(("key", str), ("window_start", float), ("requests", int), ("expiration", float, field(default=0.0))), slots=True, eq=False)

    def __init__(
        self,
        limit: int                      = 10,
        window: float | int             = 10.0,
        key: str | None                 = None,
        conn: sqlite3.Connection | None = None,
        **kwargs
    ):
        super().__init__(backend="sqlite", key=key, conn=conn, **kwargs)
        self._window = window
        self._limit = limit

    def default(self):
        return dict(
            window_start=self.now,
            requests=0,
            expiration=time() + self.options.cache_timeout if self.options.cache_timeout else 0
        )

    def ok(self, key):
        """
        Checks if the given key is allowed to make a request based on the rate limit rules.

        Args:
            key: The key to check for rate limiting.

        Returns:
            True if the key is allowed to make a request, False otherwise.
        """
        output = False
        data = self[key]
        window_start = data.window_start # type: ignore
        current_time = time()

        if current_time - window_start > self._window:
            data.requests = 0 # type: ignore
            data.window_start = current_time # type: ignore

        if data.requests < self._limit: # type: ignore
            data.requests += 1 # type: ignore
            output = True

        self[key] = data
        return output


# The `GCRA` class is a decorator that limits the rate at which a function can be called
# based on a specified rate and burst size.
class GCRA(Ratelimit):
    """
    GCRA (Generic Cell Rate Algorithm) is a rate limiting algorithm that limits the rate at which requests can be made.
    It is implemented using a SQLite backend.

    Attributes:
        _period (float | int): Time period for each cell/token (in seconds).
        _limit (int): Limit on the burst size (in seconds).

    Args:
        period (float | int, optional): Time period for each cell/token (in seconds). Defaults to 1.0.
        limit (int, optional): Limit on the burst size (in seconds). Defaults to 10.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Methods:
        default(): Returns the default data structure for a new key.
        ok(key): Checks if a request with the given key is allowed based on the rate limit.

    """

    __slots__ = ("_period", "_limit")
    __attrs__ = ("key", "last_check", "expiration")
    __dc__ = make_dataclass("GCRACache", fields=(("key", str), ("last_check", float), ("expiration", float, field(default=0.0))), slots=True, eq=False)

    def __init__(
        self,
        period: float | int             = 1.0,
        limit: int                      = 10,
        key: str | None                 = None,
        conn: sqlite3.Connection | None = None,
        **kwargs
    ):
        super().__init__(backend="sqlite", key=key, conn=conn, **kwargs)
        self._period = period  # Time period for each cell/token (in seconds)
        self._limit = limit  # Limit on the burst size (in seconds)

    def default(self):
        """
        Returns the default data structure for a new key.

        Returns:
            dict: The default data structure containing the last_check and expiration values.
        """
        return dict(
            last_check=self.now,
            expiration=time() + self.options.cache_timeout if self.options.cache_timeout else 0
        )

    def ok(self, key):
        """
        Checks if a request with the given key is allowed based on the rate limit.

        Args:
            key (str): The key associated with the request.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        output = False
        data = self[key]
        current_time = time()
        expected_time = data.last_check + self._period

        if not current_time < expected_time - self._limit:
            # The cell/token conforms; update the last_check.
            data.last_check = max(expected_time, current_time) # type: ignore
            output = True

        self[key] = data
        return output


_CLASS_TYPES = {
    "leakybucket": LeakyBucket,
    "tokenbucket": TokenBucket,
    "slidingwindow": SlidingWindow,
    "fixedwindow": FixedWindow,
    "gcra": GCRA,
}



class SQLiteRatelimitFactory:
    """
    Factory class for creating SQLite ratelimit objects.

    This class provides methods for interacting with a SQLite database to implement ratelimiting functionality.
    """
    _type = type

    def __new__(cls, instance, type="slidingwindow", key=None, *args, **kwargs):
        type_name = type
        type = _CLASS_TYPES[type_name]
        type = cls._type(type.__name__, (type, ), {
            "__slots__": ("_cursor", "_getstatement", "_setstatement", "_create_tables", "__contains__", "__getitem__", "__setitem__", "__delitem__", "clear", "keys", "values", "items", "_cleanup"),
        })

        self = type.__new__(type)
        self._getstatement = f"SELECT {', '.join(attr for attr in self.__attrs__)} FROM ratelimit WHERE key = ?"
        self._setstatement = f"INSERT OR REPLACE INTO ratelimit ({', '.join(attr for attr in self.__attrs__)}) VALUES (?{', ?'.join('' for _ in range(len(self.__attrs__)))})"
        self._instance = instance
        self._ratelimit_type = type_name
        self._create_tables = partial(SQLiteRatelimitFactory._create_tables, self)
        self.__contains__ = partial(SQLiteRatelimitFactory.__contains__, self)
        self.__getitem__ = partial(SQLiteRatelimitFactory.__getitem__, self)
        self.__setitem__ = partial(SQLiteRatelimitFactory.__setitem__, self)
        self.__delitem__ = partial(SQLiteRatelimitFactory.__delitem__, self)
        self.clear = partial(SQLiteRatelimitFactory.clear, self)
        self.keys = partial(SQLiteRatelimitFactory.keys, self)
        self.values = partial(SQLiteRatelimitFactory.values, self)
        self.items = partial(SQLiteRatelimitFactory.items, self)
        self._cleanup = partial(SQLiteRatelimitFactory._cleanup, self)
        self.__init__(*args, key=key, **kwargs)
        return self


    def _create_tables(self):
        with self._instance._sqlite_conn:
            self._instance._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS ratelimit (
                key TEXT PRIMARY KEY,
                requests INT,
                window_start FLOAT,
                cur_time FLOAT,
                cur_count INT,
                pre_count INT,
                tokens FLOAT,
                last_check FLOAT,
                content FLOAT,
                expiration FLOAT
                )
            """)

    def __contains__(self, url):
        key = self._parse_key(url)
        self._cursor.execute("SELECT key FROM ratelimit WHERE key = ?", (key,))
        return bool(self._cursor.fetchone())

    def __getitem__(self, key):
        self._cursor.execute(self._getstatement, (key,))
        data = self._cursor.fetchone()
        if data is not None:
            if self.options.cache_timeout and data[-1] < time():
                del self[key]
                return self.__dc__(key=key, **self.default())
            return self.__dc__(*data)
        return self.__dc__(key=key, **self.default())


    def __setitem__(self, key, value):
        value.expiration = time() + self.options.cache_timeout if self.options.cache_timeout else 0
        with self._instance._sqlite_conn:
            self._instance._sqlite_conn.execute(self._setstatement, astuple(value))

    def __delitem__(self, key):
        with self._instance._sqlite_conn:
            self._instance._sqlite_conn.execute("DELETE FROM ratelimit WHERE key = ?", (key,))

    def clear(self):
        with self._instance._sqlite_conn:
            self._instance._sqlite_conn.execute("DELETE FROM ratelimit")

    def keys(self):
        self._cursor.execute("SELECT key FROM ratelimit")
        return tuple(key[0] for key in self._cursor.fetchall())

    def values(self):
        self._cursor.execute("SELECT value FROM ratelimit")
        return tuple(value[0] for value in self._cursor.fetchall())

    def items(self):
        self._cursor.execute("SELECT key, value FROM ratelimit")
        return tuple((key, value) for key, value in self._cursor.fetchall())

    def _cleanup(self):
        pass