from dataclasses import make_dataclass
from time import time

from .abstract import Ratelimit, RatelimitDecoratorMixin


class TokenBucket(Ratelimit):
    """
    A token bucket implementation for rate limiting.

    Args:
        capacity (float | int): The maximum number of tokens the bucket can hold.
        fill_rate (float | int): The rate at which tokens are added to the bucket per second.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Attributes:
        _capacity (float | int): The maximum number of tokens the bucket can hold.
        _fill_rate (float | int): The rate at which tokens are added to the bucket per second.
    """

    __slots__ = ("_capacity", "_fill_rate")
    __dc__ = make_dataclass("TokenBucketCache", (("tokens", float), ("last_check", float), ("last_update", float)), slots=True, eq=False)

    def __init__(
        self,
        capacity: float | int           = 10,
        fill_rate: float | int          = 1,
        key: str | None                 = None,
        **kwargs
    ):
        super().__init__(backend="memory", key=key, **kwargs)
        self._capacity = capacity
        self._fill_rate = fill_rate


    def default(self):
        """
        Returns the default token bucket cache.

        Returns:
            TokenBucketCache: The default token bucket cache with tokens set to the capacity and last_check and last_update set to the current time.
        """
        now = self.now
        return self.__dc__(tokens=self._capacity, last_check=now, last_update=now)


    def get_tokens(self, key):
        """
        Retrieves the token bucket cache for the given key and updates the number of tokens based on the elapsed time and fill rate.

        Args:
            key: The key associated with the token bucket cache.

        Returns:
            TokenBucketCache: The updated token bucket cache.
        """
        # Retrieve data
        data = self._instance._ratelimit_memory_conn[key]

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
        Checks if there are enough tokens in the bucket for the given key and updates the token bucket cache accordingly.

        Args:
            key: The key associated with the token bucket cache.

        Returns:
            bool: True if there are enough tokens and False otherwise.
        """
        data = self.get_tokens(key)
        if data.tokens >= 1: # type: ignore
            data.tokens -= 1 # type: ignore
            data.last_update = time() # type: ignore
            return True
        data.last_update = time() # type: ignore
        return False


# The `LeakyBucket` class is a decorator that implements a rate limit for a given function
# using the leaky bucket algorithm.
class LeakyBucket(Ratelimit):
    """
    LeakyBucket class represents a rate limiter based on the leaky bucket algorithm.

    Args:
        capacity (float | int): The maximum number of requests allowed within a certain time period.
        leak_rate (float | int): The rate at which the bucket leaks requests per second.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Attributes:
        _capacity (float | int): The maximum number of requests allowed within a certain time period.
        _leak_rate (float | int): The rate at which the bucket leaks requests per second.
    """

    __slots__ = ("_capacity", "_leak_rate")
    __dc__ = make_dataclass("LeakyBucketCache", (("content", float), ("last_checked", float), ("last_update", float)), slots=True, eq=False)

    def __init__(
        self,
        capacity: float | int           = 10,
        leak_rate: float | int          = 5,
        key: str | None                 = None,
        **kwargs
    ):
        super().__init__(backend="memory", key=key, **kwargs)
        self._capacity = capacity
        self._leak_rate = leak_rate


    def default(self):
        """
        Returns the default cache data for a key.

        Returns:
            LeakyBucketCache: The default cache data for a key.
        """
        now = self.now
        return self.__dc__(content=0, last_checked=now, last_update=now)


    def _leak(self, key):
        """
        Leaks requests from the bucket based on the elapsed time.

        Args:
            key: The key associated with the cache data.

        Returns:
            LeakyBucketCache: The updated cache data after leaking requests.
        """
        data = self._instance._ratelimit_memory_conn[key]
        content = data.content # type: ignore

        # Calculate the amount of time that has passed
        current_time = time()
        elapsed = current_time - data.last_checked # type: ignore
        data.last_checked = current_time # type: ignore

        # Leak the appropriate amount of requests
        data.content -= elapsed * self._leak_rate # type: ignore
        data.content = max(data.content, 0) # type: ignore
        return data


    def ok(self, key):
        """
        Checks if a request is allowed based on the leaky bucket algorithm.

        Args:
            key: The key associated with the cache data.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        data = self._leak(key)
        if data.content < self._capacity: # type: ignore
            data.content += 1 # type: ignore
            data.last_update = time() # type: ignore
            return True
        data.last_update = time() # type: ignore
        return False


class SlidingWindow(Ratelimit):
    __slots__ = ("_limit", "_window")
    __dc__ = make_dataclass("SlidingWindowCache", (("pre_count", float), ("cur_count", float), ("cur_time", float), ("last_update", float)), slots=True, eq=False)

    def __init__(
        self,
        limit: int                      = 10,
        window: float | int             = 1.0,
        key: str | None                 = None,
        **kwargs
    ):
        super().__init__(backend="memory", key=key, **kwargs)
        self._limit = limit
        self._window = window


    def default(self):
        now = self.now
        return self.__dc__(pre_count=self._limit, cur_count=0, cur_time=now, last_update=now)


    def ok(self, key):
        data = self._instance._ratelimit_memory_conn[key]
        if ((time_ := time()) - data.cur_time) > self._window: # type: ignore
            data.cur_time = time_ # type: ignore
            data.pre_count = data.cur_count # type: ignore
            data.cur_count = 0 # type: ignore

        ec = (data.pre_count * (self._window - (time() - data.cur_time)) / self._window) + data.cur_count # type: ignore
        if ec < self._limit:
            data.cur_count += 1 # type: ignore
            data.last_update = time() # type: ignore
            return True
        data.last_update = time() # type: ignore
        return False


class FixedWindow(Ratelimit):
    __slots__ = ("_limit", "_window")
    __dc__ = make_dataclass("FixedWindowCache", (("window_start", float), ("requests", float), ("last_update", float)), slots=True, eq=False)

    def __init__(
        self,
        limit: int                      = 10,
        window: float | int             = 10.0,
        key: str | None                 = None,
        **kwargs
    ):
        super().__init__(backend="memory", key=key, **kwargs)
        self._window = window
        self._limit = limit


    def default(self):
        now = self.now
        return self.__dc__(window_start=now, requests=0, last_update=now)


    def ok(self, key):
        data = self._instance._ratelimit_memory_conn[key]
        window_start = data.window_start # type: ignore
        current_time = time()
        if current_time - window_start > self._window:
            data.requests = 0 # type: ignore
            data.window_start = current_time # type: ignore

        if data.requests < self._limit: # type: ignore
            data.requests += 1 # type: ignore
            data.last_update = time() # type: ignore
            return True
        data.last_update = time() # type: ignore
        return False


# The `GCRA` class is a decorator that limits the rate at which a function can be called
# based on a specified rate and burst size.
class GCRA(Ratelimit):
    """
    GCRA (Generic Cell Rate Algorithm) is a rate limiting algorithm that allows a burst of requests
    up to a certain limit within a specified time period.

    Args:
        period (float | int): Time period for each cell/token (in seconds). Default is 1.0.
        limit (int): Limit on the burst size (in seconds). Default is 10.
        **kwargs: Additional keyword arguments to be passed to the parent class.

    Attributes:
        _period (float | int): Time period for each cell/token (in seconds).
        _limit (int): Limit on the burst size (in seconds).
    """

    __slots__ = ("_period", "_limit")
    __dc__ = make_dataclass("GCRACache", (("last_time", float), ("last_update", float)), slots=True, eq=False)

    def __init__(
        self,
        period: float | int     = 1.0,
        limit: int              = 10,
        key: str | None         = None,
        **kwargs
    ):
        super().__init__(backend="memory", key=key, **kwargs)
        self._period = period  # Time period for each cell/token (in seconds)
        self._limit = limit  # Limit on the burst size (in seconds)


    def default(self):
        """
        Returns the default cache data object.

        Returns:
            GCRACache: The default cache data object with last_time and last_update set to the current time.
        """
        now = self.now
        return self.__dc__(last_time=now, last_update=now)


    def ok(self, key):
        """
        Checks if a request with the given key is allowed based on the rate limit.

        Args:
            key: The key associated with the request.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        data = self._instance._ratelimit_memory_conn[key]
        current_time = time()
        expected_time = data.last_time + self._period

        if current_time < expected_time - self._limit:
            # The cell/token arrives too early and does not conform.
            data.last_update = current_time # type: ignore
            return False
        else:
            # The cell/token conforms; update the last_time.
            data.last_time = max(expected_time, current_time) # type: ignore
            data.last_update = current_time # type: ignore
            return True


_CLASS_TYPES = {
    "leakybucket": LeakyBucket,
    "tokenbucket": TokenBucket,
    "slidingwindow": SlidingWindow,
    "fixedwindow": FixedWindow,
    "gcra": GCRA,
}

class PyRatelimitDecoratorFactory:
    _type = type

    def __new__(cls, type="slidingwindow", *args, **kwargs):
        type_name = type
        new_type = cls._type(type, (_CLASS_TYPES[type_name], RatelimitDecoratorMixin), {})
        self = new_type.__new__(new_type)
        self.__init__(*args, **kwargs)
        return self


class PyRatelimitFactory:
    def __new__(cls, instance, type="slidingwindow", *args, **kwargs):
        type_name = type
        type = _CLASS_TYPES[type_name]
        self = type.__new__(type)
        self._instance = instance
        self.__init__(*args, **kwargs)
        self._ratelimit_type = type_name
        return self