from time import time, perf_counter
from functools import wraps
from random import Random

from .variables import STATUS_CODES

IMAGE_TYPES = ("jpeg", "png", "svg", "webp")


def timer(func):
    @wraps(func)
    def wrapper(urls, n_trials=1000, *args, **kwargs):
        start = perf_counter()
        results = func(urls, n_trials, *args, **kwargs)
        end = perf_counter()
        print(f"[{func.__name__}]({n_trials}) Execution time: {end - start:.4f}")
        return results
    return wrapper


def atimer(func):
    @wraps(func)
    async def wrapper(urls, n_trials=1000, *args, **kwargs):
        start = perf_counter()
        results = await func(urls, n_trials, *args, **kwargs)
        end = perf_counter()
        print(f"[{func.__name__}]({n_trials}) Execution time: {end - start:.4f}")
        return results
    return wrapper


class Urls:
    RNG = Random()
    STATUS_CODES = tuple(STATUS_CODES.keys())

    def __init__(self, port=80):
        self.port = port
        self.BASE_URL = f"http://localhost:{self.port}"
        self.IP_URL = f"{self.BASE_URL}/ip"
        self.UUID_URL = f"{self.BASE_URL}/uuid"
        self.DELETE_URL = f"{self.BASE_URL}/delete"
        self.GET_URL = f"{self.BASE_URL}/get"
        self.PATCH_URL = f"{self.BASE_URL}/patch"
        self.POST_URL = f"{self.BASE_URL}/post"
        self.PUT_URL = f"{self.BASE_URL}/put"


    def GET_URLS(self, n_trials=1000):
        return (self.GET_URL for _ in range(n_trials))


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
            f"{self.self.BASE_URL}/drip?&duration={duration_}&numbytes={numbytes_}&code={code_}&delay={delay_}"
            for  delay_, duration_, code_, numbytes_ in zip(
                (self.RNG.uniform(0, delay) for _ in range(n_trials)),
                (self.RNG.uniform(0, duration) for _ in range(n_trials)),
                (code for code in self.RNG.choices(STATUS_CODES, k=n_trials)),
                (numbyte for numbyte in self.RNG.choices(range(5, numbyte), k=n_trials))
            )
        )


    def BYTES_URLS(self, n_trials=1000, numbytes=100):
        return (
            f"{self.self.BASE_URL}/bytes/{numbyte}"
            for numbyte in self.RNG.choices(range(numbytes), k=n_trials)
        )



    def STATUS_CODE_URLS(self, n_trials=1000):
        return (
            f"{self.self.BASE_URL}/status/{code}"
            for code in self.RNG.choices(STATUS_CODES, k=n_trials)
        )



    def IMAGE_URLS(self, n_trials=1000):

        return (
            f"{self.self.BASE_URL}/image/{image_type}"
            for image_type in self.RNG.choices(IMAGE_TYPES, k=n_trials)
        )