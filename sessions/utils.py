import inspect
from dataclasses import dataclass
from time import perf_counter
from functools import wraps
from random import Random
from math import floor as _floor

from .vars import STATUS_CODES


_slidingwindow_target = lambda window, limit, n_tests, **kwargs: ((window / limit) * n_tests, window)
_tokenbucket_target = lambda capacity, fill_rate, n_tests, **kwargs: ((capacity / fill_rate * (n_tests - capacity)), capacity / fill_rate)
_leakybucket_target = lambda capacity, leak_rate, n_tests, **kwargs: ((n_tests - capacity) / leak_rate, leak_rate / capacity)
_fixedwindow_target = lambda window, limit, n_tests, **kwargs: ((n_tests / limit) * window, window)
_gcra_target = lambda period, limit, n_tests, **kwargs: ((n_tests - (capacity := _floor(limit / period))) * period + (limit if n_tests <= capacity else 0), period)
_target = lambda type, **kwargs: globals()[f"_{type}_target"](**kwargs)


@dataclass(slots=True, frozen=True)
class RatelimitResult:
    name: str
    execution_time: float
    target_time: float
    delta: float
    observed_delta: float
    passed: bool
    args: dict


def take(predicate, iterable):
    """
    Returns an iterator that yields elements from the iterable as long as the predicate is True.

    Args:
        predicate (function): A function that takes an element from the iterable and returns a boolean value.
        iterable (iterable): An iterable object.

    Yields:
        The elements from the iterable that satisfy the predicate.

    """
    for x in iterable:
        if predicate(x):
            yield x
        else:
            continue

def timer(func):
    """
    Decorator that measures the execution time of a function and compares it to a target time with a given delta.

    Args:
        func: The function to be timed.

    Returns:
        The wrapped function.

    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(n_tests, urls=None, min=0, max=5, type="slidingwindow", backend="memory", limit=5, window=1, capacity=5, fill_rate=5, leak_rate=5, period=5, **kwargs): # type: ignore
            start = perf_counter()
            args = await func(n_tests, urls=urls, min=min, max=max, type=type, backend=backend, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, **kwargs)
            end = perf_counter()

            target_time, delta = _target(type, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, n_tests=n_tests)
            execution_time = end - start
            observed_delta = execution_time - target_time
            test_passed = abs(observed_delta) <= delta
            print(f"{func.__name__} took {execution_time:.2f}s, Expected {target_time:.2f}s within {delta:.2f}s delta for {type}. Observed Delta ({observed_delta:.2f}s) {'Passed' if test_passed else 'Failed'}")
            return RatelimitResult(func.__name__, execution_time, target_time, delta, observed_delta, test_passed, args)
    else:
        @wraps(func)
        def wrapper(n_tests, urls=None, min=0, max=5, type="slidingwindow", backend="memory", limit=5, window=1, capacity=5, fill_rate=5, leak_rate=5, period=5, **kwargs):
            start = perf_counter()
            args = func(n_tests, urls=urls, min=min, max=max, type=type, backend=backend, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, **kwargs)
            end = perf_counter()

            target_time, delta = _target(type, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, n_tests=n_tests)
            execution_time = end - start
            observed_delta = execution_time - target_time
            test_passed = abs(observed_delta) <= delta
            print(f"{func.__name__} took {execution_time:.2f}s, Expected {target_time:.2f}s within {delta:.2f}s delta for {type}. Observed Delta ({observed_delta:.2f}s) {'Passed' if test_passed else 'Failed'}")
            return RatelimitResult(func.__name__, execution_time, target_time, delta, observed_delta, test_passed, args)
    return wrapper


def extract_args(type, kwargs):
    """
    Extracts and returns the arguments based on the given type.

    Args:
        type (str): The type of the session algorithm.
        kwargs (dict): The keyword arguments.

    Returns:
        dict: The extracted arguments based on the type.
    """
    if type == "slidingwindow":
        return {"window": kwargs.get("window"), "limit": kwargs.get("limit"), "n_tests": kwargs.get("n_tests")}
    elif type == "fixedwindow":
        return {"window": kwargs.get("window"), "limit": kwargs.get("limit"), "n_tests": kwargs.get("n_tests")}
    elif type == "tokenbucket":
        return {"capacity": kwargs.get("capacity"), "fill_rate": kwargs.get("fill_rate"), "n_tests": kwargs.get("n_tests")}
    elif type == "leakybucket":
        return {"capacity": kwargs.get("capacity"), "fill_rate": kwargs.get("leak_rate"), "n_tests": kwargs.get("n_tests")}
    elif type == "gcra":
        return {"period": kwargs.get("period"), "limit": kwargs.get("limit"), "n_tests": kwargs.get("n_tests")}
    return {}


def make_test(typename, dct=False):
    """
    Generate test parameters based on the given typename.

    Parameters:
        typename (str): The type of test to generate parameters for.
        dct (bool, optional): If True, return the parameters as a dictionary.
                              If False (default), return the parameters as individual values.

    Returns:
        tuple or dict: The generated test parameters. If dct is True, returns a dictionary,
                       otherwise returns a tuple.

    Raises:
        None

    """
    RNG = Random()
    if typename == "slidingwindow":
        window = round(RNG.uniform(1, 5), 1)
        limit = RNG.randint(int(window), int(window*3))
        n_tests = max(15, RNG.randint(int(limit*3), int(limit*5)))
        return (window, limit, n_tests) if not dct else dict(window=window, limit=limit, n_tests=n_tests)

    elif typename == "fixedwindow":
        window = round(RNG.uniform(1, 5), 1)
        limit = RNG.randint(int(window), int(window*3))
        n_tests = max(15, RNG.randint(int(limit*3), int(limit*5)))
        return (window, limit, n_tests) if not dct else dict(window=window, limit=limit, n_tests=n_tests)

    elif typename == "tokenbucket":
        capacity = RNG.randint(1, 6)
        fill_rate = RNG.randint(int(capacity*1.5), int(capacity*3))
        n_tests = max(15, RNG.randint(int(fill_rate*3), int(fill_rate*5)))
        return (capacity, fill_rate, n_tests) if not dct else dict(capacity=capacity, fill_rate=fill_rate, n_tests=n_tests)

    elif typename == "leakybucket":
        capacity = RNG.randint(1, 6)
        leak_rate = RNG.randint(int(capacity*1.5), int(capacity*3))
        n_tests = max(15, RNG.randint(int(leak_rate*3), int(leak_rate*5)))
        return (capacity, leak_rate, n_tests) if not dct else dict(capacity=capacity, leak_rate=leak_rate, n_tests=n_tests)

    elif typename == "gcra":
        period = round(RNG.uniform(0.001, 2), 1)
        limit = RNG.randint(1, 10)
        n_tests = max(15, RNG.randint(int(limit*1.5), int(limit*5)))
        return (period, limit, n_tests) if not dct else dict(period=period, limit=limit, n_tests=n_tests)


IMAGE_TYPES = ("jpeg", "png", "svg", "webp")


def get_valid_kwargs(func, kwargs):
    """Get the subset of non-None 'kwargs' that are valid params for 'func'"""
    sig_params = list(inspect.signature(func).parameters)
    return {k: v for k, v in kwargs.items() if k in sig_params and v is not None}


def generate_random_weights(xlen, weights):
    """
    Generate random weights for a given length.

    Args:
        xlen (int or sequence): The length of the desired weights or a sequence of values that length can be obtained from.
        weights (tuple or list): The initial weights.

    Returns:
        tuple: The generated random weights.

    Raises:
        TypeError: If xlen is not an int or a sequence of values.
        AssertionError: If the sum of given weights is not less than 1.
    """
    if not isinstance(xlen, int):
        if isinstance(xlen, (list, tuple, set, range)):
            xlen = len(xlen)
        else:
            raise TypeError("xlen must be an int representing the length of the desired weights or a sequence of values that length can be obtained from")

    if isinstance(weights[0], float):
        weights = tuple((i, x) for i,x in enumerate(weights))
    elif isinstance(weights[0], int):
        weights = tuple((i, x/100) for i,x in enumerate(weights))
    elif isinstance(weights[0][0], int):
        weights = tuple((x[0], x[1]/100) for x in weights)

    mapping = dict(weights)
    indexes = set(x[0] for x in weights)
    weights = tuple(x[1] for x in weights)
    weight_to_split = 1 - sum(weights)
    assert weight_to_split > 0, "sum of given weights must be less than 1"
    len_of_weights = xlen - len(weights)
    constant = weight_to_split / len_of_weights
    return tuple(constant if i not in indexes else mapping[i] for i in range(xlen))


class Urls:
    """
    A class that provides various URL generation methods.

    Attributes:
        RNG (Random): An instance of the Random class for generating random values.
        STATUS_CODES (tuple): A tuple of status codes.
        port (int): The port number for the URLs.
        BASE_URL (str): The base URL.
        IP_URL (str): The URL for retrieving IP information.
        UUID_URL (str): The URL for generating UUIDs.
        DELETE_URL (str): The URL for DELETE requests.
        GET_URL (str): The URL for GET requests.
        PATCH_URL (str): The URL for PATCH requests.
        POST_URL (str): The URL for POST requests.
        PUT_URL (str): The URL for PUT requests.
    """
    RNG = Random()
    STATUS_CODES = tuple(STATUS_CODES.keys())

    def __init__(self, base_url=None, port=80, secure=False):
        """
        Initializes a new instance of the Urls class.

        Args:
            base_url (str, optional): The base URL. Defaults to None.
            port (int, optional): The port number for the URLs. Defaults to 80.
            secure (bool, optional): Indicates whether the URLs should use HTTPS. Defaults to False.
        """
        secure = "s" if secure else ""
        self.port = port
        self.BASE_URL = base_url or f"http{secure}://localhost:{self.port}"
        self.IP_URL = f"{self.BASE_URL}/ip"
        self.UUID_URL = f"{self.BASE_URL}/uuid"
        self.DELETE_URL = f"{self.BASE_URL}/delete"
        self.GET_URL = f"{self.BASE_URL}/get"
        self.PATCH_URL = f"{self.BASE_URL}/patch"
        self.POST_URL = f"{self.BASE_URL}/post"
        self.PUT_URL = f"{self.BASE_URL}/put"


    def random(self):
        return self.RNG.choice((
            self.GET_URL,
            self.POST_URL,
            self.PUT_URL,
            self.PATCH_URL,
            self.DELETE_URL,
            self.UUID_URL,
            self.IP_URL
        ))

    @classmethod
    def google_search(cls, min=0, max=100, weights=None):
        return f"https://www.google.com/search?q={cls.RNG.randint(min, max)}"

    @classmethod
    def GOOGLE_URLS(cls, n_trials=1000, min=0, max=100):
        return (cls.google_search(min, max) for _ in range(n_trials))

    def RANDOM_URLS(self, n_trials=1000, min=0, max=50, weights=None):
        if weights is not None:
            return (self.GET_URL + f"?id={id}" for id in self.RNG.choices(range(min, max), k=n_trials, weights=generate_random_weights(max-min, weights)))
        return (self.GET_URL + f"?id={self.RNG.randint(min, max)}" for _ in range(n_trials))

    def GET_URLS(self, n_trials=1000, suffix=""):
        return (self.GET_URL + suffix for _ in range(n_trials))

    def POST_URLS(self, n_trials=1000):
        return (self.POST_URL for _ in range(n_trials))

    def PUT_URLS(self, n_trials=1000):
        return (self.PUT_URL for _ in range(n_trials))

    def PATCH_URLS(self, n_trials=1000):
        return (self.PATCH_URL for _ in range(n_trials))

    def DELETE_URLS(self, n_trials=1000):
        return (self.DELETE_URL for _ in range(n_trials))

    def UUID_URLS(self, n_trials=1000):
        return (self.UUID_URL for _ in range(n_trials))

    def IP_URLS(self, n_trials=1000):
        return (self.IP_URL for _ in range(n_trials))

    def DRIP_URLS(self, n_trials=1000, delay=0, duration=0.01, numbyte=10):
        return (
            f"{self.BASE_URL}/drip?&duration={duration_}&numbytes={numbytes_}&code={code_}&delay={delay_}"
            for  delay_, duration_, code_, numbytes_ in zip(
                (self.RNG.uniform(0, delay) for _ in range(n_trials)),
                (self.RNG.uniform(0, duration) for _ in range(n_trials)),
                (code for code in self.RNG.choices(STATUS_CODES, k=n_trials)),
                (numbyte for numbyte in self.RNG.choices(range(5, numbyte), k=n_trials))
            )
        )

    def BYTES_URLS(self, n_trials=1000, numbytes=100):
        return (
            f"{self.BASE_URL}/bytes/{numbyte}"
            for numbyte in self.RNG.choices(range(numbytes), k=n_trials)
        )

    def STATUS_CODE_URLS(self, n_trials=1000):
        return (
            f"{self.BASE_URL}/status/{code}"
            for code in self.RNG.choices(STATUS_CODES, k=n_trials)
        )

    def IMAGE_URLS(self, n_trials=1000):
        return (
            f"{self.BASE_URL}/image/{image_type}"
            for image_type in self.RNG.choices(IMAGE_TYPES, k=n_trials)
        )