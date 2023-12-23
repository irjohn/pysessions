import time
import asyncio
from functools import wraps
from collections import deque

from sessions import (
    Session,
    TorSession,
    AsyncSession,
    AsyncClient
)

BASE_URL = "http://localhost:8080"
IP_URL = "http://localhost:8080/ip"
UUID_URL = "http://localhost:8080/uuid"

DELETE_URL = "http://localhost:8080/delete"
GET_URL = "http://localhost:8080/get"
PATCH_URL = "http://localhost:8080/patch"
POST_URL = "http://localhost:8080/post"
PUT_URL = "http://localhost:8080/put"


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
        if n_trials >= 10000:
            return deque(map(session.get, (GET_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.post, (POST_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.put, (PUT_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.patch, (PATCH_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.delete, (DELETE_URL,)*n_trials), maxlen=0)
        
        return tuple(map(session.get, (GET_URL,)*n_trials)) +\
               tuple(map(session.post, (POST_URL,)*n_trials)) +\
               tuple(map(session.put, (PUT_URL,)*n_trials)) +\
               tuple(map(session.patch, (PATCH_URL,)*n_trials)) +\
               tuple(map(session.delete, (DELETE_URL,)*n_trials))


@timer
def test_torsession(n_trials=1000):
    with TorSession() as session:
        if n_trials >= 10000:
            return deque(map(session.get, (GET_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.post, (POST_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.put, (PUT_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.patch, (PATCH_URL,)*n_trials), maxlen=0) +\
                   deque(map(session.delete, (DELETE_URL,)*n_trials), maxlen=0)

        return tuple(map(session.get, (GET_URL,)*n_trials)) +\
               tuple(map(session.post, (POST_URL,)*n_trials)) +\
               tuple(map(session.put, (PUT_URL,)*n_trials)) +\
               tuple(map(session.patch, (PATCH_URL,)*n_trials)) +\
               tuple(map(session.delete, (DELETE_URL,)*n_trials))
    

@atimer
async def test_asyncsession(n_trials=1000):
    async with AsyncSession() as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(GET_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.post(POST_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.put(PUT_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.patch(PATCH_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.delete(DELETE_URL)) for _ in range(n_trials))

    if n_trials >= 10000:
        return tuple()     
    return tuple(task.result() for task in tasks)



@atimer
async def test_asyncclient(n_trials=1000):
    async with AsyncClient(timeout=None) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(GET_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.post(POST_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.put(PUT_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.patch(PATCH_URL)) for _ in range(n_trials)) +\
                    tuple(tg.create_task(session.delete(DELETE_URL)) for _ in range(n_trials))
    if n_trials >= 10000:
        return tuple()
    return tuple(task.result() for task in tasks)


if __name__ == "__main__":
    N_TRIALS = 100
    loop = asyncio.get_event_loop()

    async_session_results = loop.run_until_complete(test_asyncsession(N_TRIALS))
    session_results = test_session(N_TRIALS)
    #tor_session_results = test_torsession(N_TRIALS)
    async_client_results = r = loop.run_until_complete(test_asyncclient(N_TRIALS))