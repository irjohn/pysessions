import asyncio
from collections import deque

from utils import (
    timer,
    BYTES_URLS,
    DRIP_URLS,
    IMAGE_URLS,
    STATUS_CODE_URLS,
)

from sessions import (
    Session,
    TorSession,
    TorRatelimitSession,
    AsyncSession,
    AsyncClient,
    RatelimitSession,
    RatelimitAsyncSession,
)

from asynchronizer import asynchronize

BASE_URL = "http://localhost:8080"
IP_URL = "http://localhost:8080/ip"
UUID_URL = "http://localhost:8080/uuid"


DELETE_URL = "http://localhost:8080/delete"
GET_URL = "http://localhost:8080/get"
PATCH_URL = "http://localhost:8080/patch"
POST_URL = "http://localhost:8080/post"
PUT_URL = "http://localhost:8080/put"



@timer
def test_session(n_trials=1000):
    with Session(headers={"User-Agent": "something"}) as session:
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
        return tuple(session.get("https://httpbin.org/ip") for _ in range(n_trials))
        #if n_trials >= 10000:
        #    return deque(map(session.get, (GET_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.post, (POST_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.put, (PUT_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.patch, (PATCH_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.delete, (DELETE_URL,)*n_trials), maxlen=0)

        #return tuple(map(session.get, (GET_URL,)*n_trials)) +\
        #       tuple(map(session.post, (POST_URL,)*n_trials)) +\
        #       tuple(map(session.put, (PUT_URL,)*n_trials)) +\
        #       tuple(map(session.patch, (PATCH_URL,)*n_trials)) +\
        #       tuple(map(session.delete, (DELETE_URL,)*n_trials))
    

@timer
@asynchronize
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



@timer
@asynchronize
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


@timer
@asynchronize
async def test_ratelimit_async_session(n_trials=100, limit=5, window=1):
    async with RatelimitAsyncSession(limit=limit, window=window) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(url)) for url in BYTES_URLS(n_trials))
    return tuple(task.result() for task in tasks)


@timer
def test_ratelimit_session(n_trials=100, limit=5, window=1):
    with RatelimitSession(limit=limit, window=window) as session:
        return tuple(session.get(url) for url in BYTES_URLS(n_trials))    


@timer
def test_torratelimit_session(n_trials=100, limit=5, window=1):
    with TorRatelimitSession(limit=limit, window=window) as session:
        return tuple(session.get(url) for url in BYTES_URLS(n_trials))   


if __name__ == "__main__":
    N_TRIALS = 100
    RATELIMIT_TRIALS = 10
    RATELIMIT = 5
    RATELIMIT_WINDOW = 1

    # Test sessions
    async_session_results = test_asyncsession(N_TRIALS)
    session_results = test_session(N_TRIALS)
    tor_session_results = test_torsession(5)
    #async_client_results = r = test_asyncclient(N_TRIALS)
    
    # Test ratelimit sessions
    ratelimit_session_results = test_ratelimit_async_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)
    async_ratelimit_session_results = test_ratelimit_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)
    #tor_ratelimit_session_results = test_torratelimit_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)