import time
import asyncio
from functools import wraps
from collections import deque

from sessions import *

URL = "http://localhost/uuid"

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


@timer
def test_session(n_trials=1000):
    with Session() as session:
        return deque(map(session.get, tuple(URL for _ in range(n_trials))), maxlen=0)


@atimer
async def test_asyncsession(n_trials=1000):
    async with AsyncSession() as session:
        return await asyncio.gather(*[
            session.get(URL)
            for _ in range(n_trials)
        ])


@atimer
async def test_asyncclient(n_trials=1000):
    from aiohttp import ClientSession
    async with AsyncClient() as session:
        return await asyncio.gather(*[
            session.get(URL)
            for _ in range(n_trials)
        ])


N_TRIALS = 10_000
loop = asyncio.get_event_loop()

loop.run_until_complete(test_asyncsession(N_TRIALS))
test_session(N_TRIALS)
loop.run_until_complete(test_asyncclient(N_TRIALS))