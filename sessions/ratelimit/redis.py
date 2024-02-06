import time

from redislite import Redis

from .abstract import Ratelimit, RatelimitDecoratorMixin


class LeakyBucket(Ratelimit):
    __slots__ = ("_capacity", "_leak_rate")

    def __init__(
        self,
        capacity: int | float   = 10,
        leak_rate: int | float  = 5,
        key: str | None         = None,
        conn: Redis | None     = None,
        **kwargs
    ):
        self._capacity = capacity  # Maximum capacity of the bucket
        self._leak_rate = leak_rate  # Leak rate in requests per second
        super().__init__(key=key, conn=conn, backend="redis", **kwargs)


    def _leak(self, key):
        # Get the key information
        data = self._instance._redis_conn.hgetall(key) # type: ignore
        if not data: # type: ignore
            now = time.time()
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"content": 0, "last_check": now, "last_update": now}) # type: ignore
            return 0

        content = float(data[b"content"]) # type: ignore
        last_check = float(data[b"last_check"]) # type: ignore

        # Calculate the amount of time that has passed
        now = self.now
        elapsed = now - last_check

        # Leak the appropriate amount of requests
        content -= elapsed * self._leak_rate
        content = max(content, 0)  # Ensure content doesn't go negative

        # Store the data
        self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"content": content, "last_check": now, "last_update": now}) # type: ignore
        return content


    def ok(self, key):
        content = self._leak(key)
        if content < self._capacity:
            self._set_redis_key(key, self._instance._redis_conn.hset, "content", content + 1) # type: ignore
            return True
        return False



class TokenBucket(Ratelimit):
    __slots__ = ("_capacity", "_fill_rate")

    def __init__(
        self,
        capacity: float | int       = 20,
        fill_rate: float | int      = 5,
        key: str | int | None       = None,
        conn: Redis | None         = None,
        **kwargs
    ):
        self._capacity = float(capacity)
        self._fill_rate = float(fill_rate)
        super().__init__(key=key, conn=conn, backend="redis", **kwargs)


    def get_tokens(self, key):
        data = self._instance._redis_conn.hgetall(key) # type: ignore
        if not data:
            now = time.time()
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"tokens": self._capacity, "last_fill": now, "last_update": now}) # type: ignore
            return self._capacity

        tokens = float(data[b"tokens"]) # type: ignore
        last_fill = float(data[b"last_fill"]) # type: ignore

        # Calculate the time elapsed since the last fill
        now = time.time()
        elapsed = now - last_fill

        # Calculate the number of tokens to add based on the fill rate
        to_add = elapsed * (self._fill_rate / self._capacity)

        # Set the new number of tokens (up to the capacity)
        tokens = min(self._capacity, tokens + to_add)

        # Store the new number of tokens and the last fill time
        if tokens < 1:
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"tokens": tokens, "last_fill": now, "last_update": now}) # type: ignore
            return False

        tokens -= 1
        self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"tokens": tokens, "last_fill": now, "last_update": now}) # type: ignore
        return True


    def ok(self, key):
        return self.get_tokens(key)



class SlidingWindow(Ratelimit):
    __slots__ = ("_limit", "_window")

    def __init__(
        self,
        limit: int              = 10,
        window: float | int     = 1.0,
        key: str | None         = None,
        conn: Redis | None     = None,
        **kwargs
    ):
        self._limit = limit
        self._window = window * 1000000000
        super().__init__(key=key, conn=conn, backend="redis", **kwargs)


    @property
    def limit(self):
        return self._limit


    @property
    def window(self):
        return self._window


    @property
    def edge(self):
        return self.current_timestampns - self.window


    def ok(self, key):
        self._set_redis_key(key, self._instance._redis_conn.zremrangebyscore, 0, self.edge) # type: ignore
        count = self._instance._redis_conn.zcard(key) # type: ignore
        if count < self.limit: # type: ignore
            ts = self.current_timestampns
            self._set_redis_key(key, self._instance._redis_conn.zadd, mapping={ts:ts})# type: ignore
            return True
        return False


class FixedWindow(Ratelimit):
    __slots__= ("_limit", "_window")

    def __init__(
        self,
        limit: int              = 10,
        window: float | int     = 1.0,
        key: str | None         = None,
        conn: Redis | None     = None,
        **kwargs
    ):
        self._limit = limit
        self._window = window
        super().__init__(key=key, conn=conn, backend="redis", **kwargs)


    def ok(self, key):
        data = self._instance._redis_conn.hgetall(key) # type: ignore
        if not data:
            now = time.time()
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"requests": 1, "window_start": now, "last_update": now}) # type: ignore

            return True

        window_start = float(data[b"window_start"]) # type: ignore
        requests = int(data[b"requests"]) # type: ignore
        current_time = time.time()
        if current_time - window_start > self._window:
            requests = 0
            self._instance._redis_conn.hset(key, mapping={"requests": requests, "window_start": time.time(), "last_update": current_time}) # type: ignore

        if requests < self._limit:
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"requests": requests + 1, "last_update": current_time}) # type: ignore
            return True

        self._set_redis_key(key, self._instance._redis_conn.hset, "last_update", current_time) # type: ignore
        return False


class GCRA(Ratelimit):
    __slots__ = ("_period", "_limit")

    def __init__(
        self,
        period: float | int     = 1,
        limit: int              = 10,
        key: str | None         = None,
        conn: Redis | None     = None,
        **kwargs
    ):
        self._period = period
        self._limit = limit
        super().__init__(key=key, conn=conn, backend="redis", **kwargs)


    def ok(self, key):
        data = self._instance._redis_conn.hgetall(key) # type: ignore
        if not data:
            now = time.time()
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"last_time": now, "last_update": now}) # type: ignore
            return True

        last_time = float(data[b"last_time"]) # type: ignore
        current_time = time.time()
        expected_time = last_time + self._period

        if current_time < expected_time - self._limit:
            self._set_redis_key(key, self._instance._redis_conn.hset, "last_update", current_time) # type: ignore
            return False
        else:
            self._set_redis_key(key, self._instance._redis_conn.hset, mapping={"last_time": max(expected_time, current_time), "last_update": current_time}) # type: ignore
            return True


_CLASS_TYPES = {
    "leakybucket": LeakyBucket,
    "tokenbucket": TokenBucket,
    "slidingwindow": SlidingWindow,
    "fixedwindow": FixedWindow,
    "gcra": GCRA,
}

class RedisRatelimitFactory:
    def __new__(cls, instance, type="slidingwindow", key=None, *args, **kwargs):
        type_name = type
        type = _CLASS_TYPES[type_name]
        self = type.__new__(type)
        self._instance = instance
        self.__init__(*args, key=key, **kwargs)
        self._ratelimit_type = type_name
        return self


class RedisRatelimitDecoratorFactory:
    _type = type

    def __new__(cls, type="slidingwindow", *args, **kwargs):
        type_name = type
        new_type = cls._type(type, (_CLASS_TYPES[type_name], RatelimitDecoratorMixin), {})
        self = new_type.__new__(new_type)
        self.__init__(*args, **kwargs)
        return self