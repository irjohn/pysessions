import time
from functools import wraps
from random import SystemRandom

from sessions.variables import (
    STATUS_CODES
)

RNG = SystemRandom()
STATUS_CODES = tuple(STATUS_CODES.keys())
BASE_URL = "http://localhost:8080"


def timer(func):
    @wraps(func)
    def wrapper(n_trials=1000, *args, **kwargs):
        start = time.perf_counter()
        results = func(n_trials, *args, **kwargs)
        end = time.perf_counter()
        print(f"[{func.__name__}]({n_trials}) Execution time: {end - start:.4f}")
        return results
    return wrapper


def atimer(func):
    @wraps(func)
    async def wrapper(n_trials=1000, *args, **kwargs):
        start = time.perf_counter()
        results = await func(n_trials, *args, **kwargs)
        end = time.perf_counter()
        print(f"[{func.__name__}]({n_trials}) Execution time: {end - start:.4f}")
        return results
    return wrapper


def DRIP_URLS(n_trials=1000, delay=0, duration=0.01, numbyte=10):
    delays = (RNG.uniform(0, delay) for _ in range(n_trials))
    durations = (RNG.uniform(0, duration) for _ in range(n_trials))
    codes = (code for code in RNG.choices(STATUS_CODES, k=n_trials))
    numbytes = (numbyte for numbyte in RNG.choices(range(5, numbyte), k=n_trials))
    for delay_, duration_, code_, numbytes_ in zip(delays, durations, codes, numbytes):
        print(code_, delay_, duration_, numbytes_)
        yield f"{BASE_URL}/drip?&duration={duration_}&numbytes={numbytes_}&code={code_}&delay={delay_}"


def BYTES_URLS(n_trials=1000, numbytes=100):
    return (f"{BASE_URL}/bytes/{numbyte}" for numbyte in RNG.choices(range(numbytes), k=n_trials))


def STATUS_CODE_URLS(n_trials=1000):
    return (f"{BASE_URL}/status/{code}" for code in RNG.choices(STATUS_CODES, k=n_trials))


def IMAGE_URLS(n_trials=1000):
    image_types = ("jpeg", "png", "svg", "webp")
    return (f"{BASE_URL}/image/{image_type}" for image_type in RNG.choices(image_types, k=n_trials))


