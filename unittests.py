import asyncio
from collections import deque

from utils import (
    timer,
    Urls
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


@timer
def test_session(urls, n_trials=1000, **kwargs):
    with Session(**kwargs) as session:
        if n_trials >= 10000:
            return deque(map(session.get, urls), maxlen=0)
        return tuple(map(session.get, urls))


@timer
def test_torsession(urls, n_trials=1000, **kwargs):
    with TorSession(**kwargs) as session:
        return tuple(map(session.get, urls))
        #if n_trials >= 10000:
        #    return deque(map(session.get, (urls.GET_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.post, (urls.POST_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.put, (urls.PUT_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.patch, (urls.PATCH_URL,)*n_trials), maxlen=0) +\
        #           deque(map(session.delete, (urls.DELETE_URL,)*n_trials), maxlen=0)

        #return tuple(map(session.get, (urls.GET_URL,)*n_trials)) +\
        #       tuple(map(session.post, (urls.POST_URL,)*n_trials)) +\
        #       tuple(map(session.put, (urls.PUT_URL,)*n_trials)) +\
        #       tuple(map(session.patch, (urls.PATCH_URL,)*n_trials)) +\
        #       tuple(map(session.delete, (urls.DELETE_URL,)*n_trials))
    

@timer
@asynchronize
async def test_asyncsession(urls, n_trials=1000, **kwargs):
    async with AsyncSession(**kwargs) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(url)) for url in urls)
    if n_trials >= 10000:
        return deque(tuple(task.result() for task in tasks), maxlen=0)
    return tuple(task.result() for task in tasks)



@timer
@asynchronize
async def test_asyncclient(urls, n_trials=1000, **kwargs):
    async with AsyncClient(**kwargs) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(url)) for url in urls)
    if n_trials >= 10000:
        return tuple()
    return tuple(task.result() for task in tasks)


@timer
@asynchronize
async def test_ratelimit_async_session(urls, n_trials=100, limit=5, window=1, **kwargs):
    async with RatelimitAsyncSession(limit=limit, window=window, **kwargs) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = tuple(tg.create_task(session.get(url)) for url in urls)
    if n_trials >= 10000:
        return deque(tuple(task.result() for task in tasks), maxlen=0)
    return tuple(task.result() for task in tasks)


@timer
def test_ratelimit_session(urls, n_trials=100, limit=5, window=1, **kwargs):
    with RatelimitSession(limit=limit, window=window, **kwargs) as session:
        if n_trials >= 10000:
            return deque(map(session.get, urls), maxlen=0)
        return tuple(map(session.get, urls))  


@timer
def test_torratelimit_session(urls, n_trials=100, limit=5, window=1, **kwargs):
    with TorRatelimitSession(limit=limit, window=window, **kwargs) as session:
        if n_trials >= 10000:
            return deque(map(session.get, urls), maxlen=0)
        return tuple(map(session.get, urls))


@timer
@asynchronize
async def test_requests(urls, n_trials=1000, method="GET", progress=True, **kwargs):
    async with AsyncSession(**kwargs) as session:
        results = await session.requests(tuple(urls), method, progress=progress)
    return results


if __name__ == "__main__":
    URLS = Urls(8080)
    N_TRIALS = 100_000
    RATELIMIT_TRIALS = 10
    RATELIMIT = 5
    RATELIMIT_WINDOW = 1


    results = test_requests(URLS.IP_URLS(N_TRIALS), N_TRIALS)

    # Test sessions
    #async_session_results = test_asyncsession(N_TRIALS)
    #session_results = test_session(N_TRIALS)
    #tor_session_results = test_torsession(5)
    #async_client_results = r = test_asyncclient(N_TRIALS)
    
    # Test ratelimit sessions
    #ratelimit_session_results = test_ratelimit_async_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)
    #async_ratelimit_session_results = test_ratelimit_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)
    #tor_ratelimit_session_results = test_torratelimit_session(RATELIMIT_TRIALS, limit=RATELIMIT, window=RATELIMIT_WINDOW)