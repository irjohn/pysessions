import os
import asyncio
import inspect
from time import perf_counter
from functools import wraps
from dataclasses import dataclass
from atexit import register
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import floor
from random import Random
from termcolor import colored

from .utils import Urls
from .config import SessionConfig as config
from . import Session, AsyncSession, RatelimitMixin

@register
def cleanup_dbs():
    if os.path.exists("test.db"):
        os.remove("test.db")
    if os.path.exists("test.db.settings"):
        os.remove("test.db.settings")
    if os.path.exists("http_cache.db"):
        os.remove("http_cache.db")


urls = Urls("http://httpbin.org")
color_time = lambda time: colored(f"{time:.2f}", "light_blue")
color_type = lambda type: colored(type.upper(), "light_yellow")

class Session(RatelimitMixin, Session):
    pass

class AsyncSession(RatelimitMixin, AsyncSession):
    pass



#--------------------------------------------------------------------------------------------------------------------------------------------------#
# RATELIMIT TESTING FUNCTIONS
#--------------------------------------------------------------------------------------------------------------------------------------------------#
PASSED = colored("PASSED", "light_green")
FAILED = colored("FAILED", "light_red")

RATELIMIT_TARGET_FUNCTIONS = {
    "slidingwindow": lambda window, limit, n_tests, **kwargs: ((window / limit) * n_tests, window),
    "tokenbucket": lambda capacity, fill_rate, n_tests, **kwargs: ((capacity / fill_rate * (n_tests - capacity)), capacity / fill_rate),
    "leakybucket": lambda capacity, leak_rate, n_tests, **kwargs: ((n_tests - capacity) / leak_rate, leak_rate / capacity),
    "fixedwindow": lambda window, limit, n_tests, **kwargs: ((n_tests / limit) * window, window),
    "gcra": lambda period, limit, n_tests, **kwargs: ((n_tests - (capacity := floor(limit / period))) * period + (limit if n_tests <= capacity else 0), period)
}


def get_target_time(type, **kwargs):
    """
    Returns the target time and delta for the given type.

    Args:
        type (str): The type of the session algorithm.
        kwargs (dict): The keyword arguments.

    Returns:
        tuple: The target time and delta for the given type.

    """
    return RATELIMIT_TARGET_FUNCTIONS[type](**kwargs)

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


def make_test(
    typename: str,
    dct: bool                 = False,
    target_time: float        = 0.0,
    debug: bool               = False,
    **kwargs
):
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
        kwargs = dict(window=window, limit=limit, n_tests=n_tests)

    elif typename == "fixedwindow":
        window = round(RNG.uniform(1, 5), 1)
        limit = RNG.randint(int(window), int(window*3))
        n_tests = max(15, RNG.randint(int(limit*3), int(limit*5)))
        kwargs = dict(window=window, limit=limit, n_tests=n_tests)

    elif typename == "tokenbucket":
        capacity = RNG.randint(1, 6)
        fill_rate = RNG.randint(int(capacity*1.5), int(capacity*3))
        n_tests = max(15, RNG.randint(int(fill_rate*3), int(fill_rate*5)))
        kwargs = dict(capacity=capacity, fill_rate=fill_rate, n_tests=n_tests)

    elif typename == "leakybucket":
        capacity = RNG.randint(1, 6)
        leak_rate = RNG.randint(int(capacity*1.5), int(capacity*3))
        n_tests = max(15, RNG.randint(int(leak_rate*3), int(leak_rate*5)))
        kwargs = dict(capacity=capacity, leak_rate=leak_rate, n_tests=n_tests)

    elif typename == "gcra":
        period = round(RNG.uniform(0.01, 2), 2)
        limit = RNG.randint(1, 10)
        n_tests = max(15, RNG.randint(int(limit*1.5), int(limit*5)))
        kwargs = dict(period=period, n_tests=n_tests, limit=limit)

    if target_time:
        current_time = get_target_time(typename, **kwargs)
        previous_times = [current_time]

        while True:
            current_time, delta = get_target_time(typename, **kwargs)
            if previous_times.count(current_time) > 10:
                if current_time < target_time:
                    kwargs["n_tests"] += 1
                break
            if config.debug or debug:
                print({
                    "current_time": current_time,
                    "previous_time": previous_times[-1],
                    "kwargs": kwargs,
                })
            if current_time < target_time:
                kwargs["n_tests"] += 1
            elif current_time > target_time:
                kwargs["n_tests"] -= 1
            else:
                break
            previous_times.append(current_time)
    return tuple(kwargs.values()) if not dct else kwargs

def print_test_headers(type, target_time, delta, kwargs):
    print(f"\nStarting tests for {color_type(type)} with target time {color_time(target_time)}s and delta {color_time(delta)}s")
    header = "Test parameters:\n"
    lines = [f"{k}: {v}" for k, v in kwargs.items()]
    print(header + "\n".join(lines))

@dataclass
class RatelimitResult:
    name: str
    message: str
    backend: str
    ratelimit_type: str
    execution_time: float
    target_time: float
    delta: float
    observed_delta: float
    passed: bool
    n_tests: int
    limit: int | None = None
    window: float| int | None = None
    capacity: int | None = None
    fill_rate: int | None = None
    leak_rate: int | None = None
    period: float | None = None

    def __post_init__(self):
        for k, v in self.args.items():
            setattr(self, k, v)

    def __bool__(self):
        return self.passed

    @property
    def args(self):
        return extract_args(self.ratelimit_type, self.__dict__)

def ratelimit_timer(func):
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
            args, avg_execution = await func(n_tests, urls=urls, min=min, max=max, type=type, backend=backend, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, **kwargs)
            end = perf_counter()

            target_time, delta = get_target_time(type, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, n_tests=n_tests)
            delta += avg_execution
            execution_time = end - start
            observed_delta = execution_time - target_time
            test_passed = abs(observed_delta) <= delta
            message = f"{func.__name__} took {color_time(execution_time)}, Expected {color_time(target_time)}s within {color_time(delta)}s delta for {type}. Observed Delta ({color_time(observed_delta)}s) {PASSED if test_passed else FAILED}"
            print(message)
            return RatelimitResult(func.__name__, message, backend, type, execution_time, target_time, delta, observed_delta, test_passed, **args)
    else:
        @wraps(func)
        def wrapper(n_tests, urls=None, min=0, max=5, type="slidingwindow", backend="memory", limit=5, window=1, capacity=5, fill_rate=5, leak_rate=5, period=5, **kwargs):
            start = perf_counter()
            args, avg_execution = func(n_tests, urls=urls, min=min, max=max, type=type, backend=backend, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, **kwargs)
            end = perf_counter()

            target_time, delta = get_target_time(type, limit=limit, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate, period=period, n_tests=n_tests)
            delta += avg_execution
            execution_time = end - start
            observed_delta = execution_time - target_time
            test_passed = abs(observed_delta) <= delta
            message = f"{func.__name__} took {color_time(execution_time)}, Expected {color_time(target_time)}s within {color_time(delta)}s delta for {type}. Observed Delta ({color_time(observed_delta)}s) {PASSED if test_passed else FAILED}"
            print(message)
            return RatelimitResult(func.__name__, message, backend, type, execution_time, target_time, delta, observed_delta, test_passed, **args)
    return wrapper


#--------------------------------------------------------------------------------------------------------------------------------------------------#
# RATELIMIT TESTS
#--------------------------------------------------------------------------------------------------------------------------------------------------#

@ratelimit_timer
def test_memory(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    with Session(backend="memory", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs), avg_exc

@ratelimit_timer
def test_sqlite(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    kwargs.pop("db", None)
    with Session(backend="sqlite", db="test.db", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    return extract_args(kwargs["type"], kwargs), avg_exc

@ratelimit_timer
def test_redis(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    with Session(backend="redis", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs), avg_exc


@ratelimit_timer
async def atest_memory(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    async with AsyncSession(backend="memory", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs), avg_exc

@ratelimit_timer
async def atest_sqlite(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    kwargs.pop("db", None)
    async with AsyncSession(backend="sqlite", db="test.db", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    return extract_args(kwargs["type"], kwargs), avg_exc

@ratelimit_timer
async def atest_redis(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    async with AsyncSession(backend="redis", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    avg_exc =  sum((i.elapsed.total_seconds() for i in results))/len(results)
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs), avg_exc


def run_sync_tests(n_tests=25, *, min=0, max=5, type=None, randomize=True, executor=None, target_time=None):
    """
    Run synchronous tests for different types of algorithms.

    Args:
        n_tests (int): Number of tests to run for each algorithm (default: 25).
        min (int): Minimum value for the test inputs (default: 0).
        max (int): Maximum value for the test inputs (default: 5).
        randomize (bool): Flag indicating whether to randomize test parameters (default: False).
        **kwargs: Additional keyword arguments for the test functions.

    Returns:
        dict: A dictionary containing the test results for each algorithm.
              The keys are the algorithm types and the values are tuples of test results.
    """
    funcs = (test_memory, test_redis, test_sqlite)
    with executor or ThreadPoolExecutor(max_workers=5) as executor:
        if type is None:
            results = {}

            for type in ("slidingwindow", "fixedwindow", "tokenbucket", "leakybucket", "gcra"):
                cleanup_dbs()
                if randomize:
                    kwargs = make_test(type, dct=True, target_time=target_time)

                current_target, current_delta = get_target_time(type, **kwargs)
                print_test_headers(type, current_target, current_delta, kwargs)
                test_results = tuple(executor.submit(func, min=min, max=max, type=type, key=f"{func.__name__}-{type}", **kwargs) for func in funcs)
                results[type] = tuple(result.result() for result in as_completed(test_results))
            return results
        else:
            cleanup_dbs()
            if randomize:
                kwargs = make_test(type, dct=True, target_time=target_time)
            current_target, current_delta = get_target_time(type, **kwargs)
            print_test_headers(type, current_target, current_delta, kwargs)
            test_results =  tuple(executor.submit(func, min=min, max=max, type=type, key=f"{func.__name__}-{type}", **kwargs) for func in funcs)
        return {type: tuple(result.result() for result in as_completed(test_results))}


async def run_async_tests(n_tests=25, *, type=None, min=0, max=5, randomize=True, target_time=None):
    """
    Run synchronous tests for different types of algorithms.

    Args:
        n_tests (int): Number of tests to run for each algorithm (default: 25).
        min (int): Minimum value for the test inputs (default: 0).
        max (int): Maximum value for the test inputs (default: 5).
        randomize (bool): Flag indicating whether to randomize test parameters (default: False).
        **kwargs: Additional keyword arguments for the test functions.

    Returns:
        dict: A dictionary containing the test results for each algorithm.
              The keys are the algorithm types and the values are tuples of test results.
    """
    funcs = (atest_memory, atest_redis, atest_sqlite)
    if type is None:
        results = {}
        for type in ("slidingwindow", "fixedwindow", "tokenbucket", "leakybucket", "gcra"):
            cleanup_dbs()
            if randomize:
                kwargs = make_test(type, dct=True, target_time=target_time)
            current_target, current_delta = get_target_time(type, **kwargs)
            print_test_headers(type, current_target, current_delta, kwargs)
            results[type] = await asyncio.gather(*[func(min=min, max=max, type=type, key=f"{func.__name__}-{type}", **kwargs) for func in funcs])
        return results
    else:
        cleanup_dbs()
        if randomize:
            kwargs = make_test(type, dct=True, target_time=target_time)
        current_target, current_delta = get_target_time(type, **kwargs)
        print_test_headers(type, current_target, current_delta, kwargs)
        test_results =  await asyncio.gather(*[func(min=min, max=max, type=type, key=f"{func.__name__}-{type}", **kwargs) for func in funcs])
    return {type: test_results}


#--------------------------------------------------------------------------------------------------------------------------------------------------#
# CACHE TESTING FUNCTIONS
#--------------------------------------------------------------------------------------------------------------------------------------------------#

#--------------------------------------------------------------------------------------------------------------------------------------------------#
# CACHE TESTS
#--------------------------------------------------------------------------------------------------------------------------------------------------#