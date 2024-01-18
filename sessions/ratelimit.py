from time import time as _time
from functools import wraps as _wraps

class TokenBucketRatelimiter:
    __slots__ = ("tokens", "window", "bucket", "last_check")

    def __init__(self, tokens=10, window=1, *args, **kwargs):
        self.tokens = tokens
        self.window = window
        self.bucket = tokens
        self.last_check = _time()


    def __call__(self, func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            current = _time()
            time_passed = current - self.last_check
            self.last_check = current

            self.bucket = self.bucket + \
                time_passed * (self.tokens / self.window)

            if (self.bucket > self.tokens):
                self.bucket = self.tokens

            if (self.bucket < 1):
                raise InterruptedError("Ratelimit exceeded")
            else:
                self.bucket = self.bucket - 1
                return func(*args, **kwargs)
        return wrapper


# The `LeakyBucketRateLimiter` class is a decorator that implements a rate limit for a given function
# using the leaky bucket algorithm.
class LeakyBucketRatelimiter:
    __slots__ = ("capacity", "leak_rate", "water", "last_checked")

    def __init__(self, capacity=10, leak_rate=1, *args, **kwargs):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.water = 0
        self.last_checked = _time()

    def __call__(self, func):
        """
        The above function is a decorator that implements a rate limit for a given function.

        :param func: The `func` parameter is a function that will be decorated by the `__call__` method
        :return: The function `wrapper` is being returned.
        """
        @_wraps(func)
        def wrapper(*args, **kwargs):
            current_time = _time()
            elapsed_time = current_time - self.last_checked
            self.water = max(0, self.water - elapsed_time * self.leak_rate)
            self.last_checked = current_time

            if self.water < self.capacity:
                self.water += 1
                return func(*args, **kwargs)
            else:
                raise InterruptedError("Rate limit exceeded")
        return wrapper


class SlidingWindowRatelimiter:
    __slots__ = ("capacity", "window", "cur_time", "pre_count", "cur_count")

    def __init__(self, capacity=10, window=1, *args, **kwargs):
        self.capacity = capacity
        self.window = window
        self.cur_time = _time()
        self.pre_count = capacity
        self.cur_count = 0


    def __call__(self, func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            if ((time := _time()) - self.cur_time) > self.window:
                self.cur_time = time
                self.pre_count = self.cur_count
                self.cur_count = 0

            ec = (self.pre_count * (self.window - (_time() - self.cur_time)) / self.window) + self.cur_count

            if (ec > self.capacity):
                raise InterruptedError("Ratelimit exceeded")

            self.cur_count += 1
            return func(*args, **kwargs)
        return wrapper


class FixedWindowRatelimiter:
    __slots__ = ("capacity", "current_time", "allowance")

    def __init__(self, capacity=10, *args, **kwargs):
        self.current_time = int(_time())
        self.allowance = capacity
        self.capacity = capacity


    def __call__(self, func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            if (int(_time()) != self.current_time):
                self.current_time = int(_time())
                self.allowance = self.capacity

            if (self.allowance < 1):
                raise InterruptedError("Ratelimit surpassed")

            self.allowance -= 1
            return func(*args, **kwargs)
        return wrapper



# The `GCRARatelimiter` class is a decorator that limits the rate at which a function can be called
# based on a specified rate and burst size.
class GCRARatelimiter:
    __slots__ = ("tau", "tat", "burst", "last_time")

    def __init__(self, rate=1, burst=5, *args, **kwargs):
        self.tau = 1 / rate
        self.tat = 0
        self.burst = burst
        self.last_time = _time()


    def __call__(self, func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            current_time = _time()
            increment = (current_time - self.last_time) * self.tau
            self.tat = max(0, self.tat - increment)
            self.last_time = current_time

            if self.tat < self.burst:
                self.tat += self.tau
                return func(*args, **kwargs)
            else:
                raise InterruptedError("Ratelimit exceeded")
        return wrapper


_TYPES = {
    "leakybucket": LeakyBucketRatelimiter,
    "tokenbucket": TokenBucketRatelimiter,
    "slidingwindow": SlidingWindowRatelimiter,
    "fixedwindow": FixedWindowRatelimiter,
    "gcra": GCRARatelimiter,
}


class ratelimit:
    def __new__(cls, type="slidingwindow", *args, **kwargs):
        type = _TYPES[type.lower()]
        instance = type.__new__(type)
        instance.__init__(*args, **kwargs)
        return instance