from concurrent.futures import ThreadPoolExecutor, as_completed
from pprint import pprint

from sessions.session import Session
from sessions.utils import timer, Urls
from sessions.backends import ConnectionPool

from utils import statistics

urls = Urls(base_url="http://httpbin")

@timer
def test_threaded_sqlite_get():
    def _test_thread():
        with Session(backend="sqlite", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
            #pprint(session.ratelimiter.items())
            print(session.cache, len(session.cache.keys()))
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.SQLITE._pools.keys()))

@timer
def test_threaded_sqlite_requests():
    def _test_thread():
        with Session(backend="sqlite", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            print(session.cache, len(session.cache.keys()))
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = session.requests((urls.BASE_URL + f"/get?id={n}" for n in range(30)), progress=False)
            #pprint(session.ratelimiter.items())
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.SQLITE._pools.keys()))
    return sessions[-1]

@timer
def test_sqlite_get():
    with Session(backend="sqlite", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="sqlite", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="sqlite", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    pprint(len(ConnectionPool.SQLITE._pools.keys()))


@timer
def test_threaded_memory_get():
    def _test_thread():
        with Session(backend="memory", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
            #pprint(session.ratelimiter.items())
            print(session.cache, len(session.cache.keys()))
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.MEMORY._pools.keys()))

@timer
def test_threaded_memory_requests():
    def _test_thread():
        with Session(backend="memory", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            print(session.cache, len(session.cache.keys()))
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = session.requests((urls.BASE_URL + f"/get?id={n}" for n in range(30)), progress=False)
            #pprint(session.ratelimiter.items())
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.MEMORY._pools.keys()))
    return sessions[-1]

@timer
def test_memory_get():
    with Session(backend="memory", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="memory", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="memory", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    pprint(len(ConnectionPool.MEMORY._pools.keys()))


    def _test_thread():
        with Session(backend="memory", type="fixedwindow", cache=False, ratelimit=True, limit=10, window=1, cache_timeout=11, check_frequency=1) as session:
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + "/get?id={n}" for n in range(30)))
            #pprint(session.ratelimiter.items())
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]

@timer
def test_threaded_redis_get():
    def _test_thread():
        with Session(backend="redis", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
            #pprint(session.ratelimiter.items())
            print(session.cache, len(session.cache.keys()))
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.REDIS._pools.keys()))

@timer
def test_threaded_redis_requests():
    def _test_thread():
        with Session(backend="redis", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
            print(session.cache, len(session.cache.keys()))
            #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
            results = session.requests((urls.BASE_URL + f"/get?id={n}" for n in range(30)), progress=False)
            #pprint(session.ratelimiter.items())
        return session

    with ThreadPoolExecutor(20) as executor:
        futures = [executor.submit(_test_thread) for x in range(3)]
        sessions = [future.result() for future in as_completed(futures)]
    pprint(len(ConnectionPool.REDIS._pools.keys()))
    return sessions[-1]

@timer
def test_redis_get():
    with Session(backend="redis", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="redis", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    with Session(backend="redis", type="fixedwindow", cache=True, ratelimit=True, limit=10, window=1) as session:
        #results = [session.get(url, ratelimit=True) for url in urls.RANDOM_URLS(100)]
        results = tuple(session.get(url, ratelimit=True) for url in (urls.BASE_URL + f"/get?id={n}" for n in range(30)))
        #pprint(session.ratelimiter.items())
    pprint(len(ConnectionPool.REDIS._pools.keys()))



# test_threaded_memory_get()
# test_threaded_memory_requests()
# test_memory_get()

test_sqlite_get()
test_threaded_sqlite_get()
test_threaded_sqlite_requests()

# test_threaded_redis_get()
# s = test_threaded_redis_requests()
# test_redis_get()
