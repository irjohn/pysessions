import unittest
import asyncio
from time import perf_counter
from unittest import mock
from unittest.mock import DEFAULT, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from sessions.utils import Urls, make_test
from random import Random
from math import floor
from sessions import Session, AsyncSession, CacheMixin, RatelimitMixin


RNG = Random()
URLS = Urls("http://httpbin.org")

sliding_window_target = lambda window, limit, n_tests: (window / limit) * n_tests
fixed_window_target = lambda window, limit, n_tests: (n_tests / limit) * window
token_bucket_target = lambda capacity, fill_rate, n_tests: (capacity / fill_rate * (n_tests - capacity))
leaky_bucket_target = lambda capacity, fill_rate, n_tests: (n_tests - capacity) / fill_rate
target_tolerance = 0.1
gcra_target = lambda period, limit, n_tests: (n_tests - (capacity := floor(limit / period))) * period + (limit if n_tests <= capacity else 0)


class RatelimitAsyncSession(RatelimitMixin, AsyncSession):
    pass

class RatelimitSession(RatelimitMixin, Session):
    pass

class TestAsyncSession(AioHTTPTestCase):
    DEFAULT_USER_AGENT = "Python/3.12 aiohttp/3.9.1"
    URL = URLS.BASE_URL + "/ip"

    async def get_application(self):
        return web.Application()

    @unittest_run_loop
    @patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent')
    async def test_random_user_agents_enabled(self):
        async with AsyncSession(random_user_agents=True) as session:
            response = await session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), 'TestUserAgent')
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    @unittest_run_loop
    async def test_random_user_agents_disabled(self):
        async with AsyncSession(random_user_agents=False) as session:
            response = await session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), self.DEFAULT_USER_AGENT)


    @unittest_run_loop
    async def test_custom_user_agent(self):
        async with AsyncSession(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = await session.get(url=self.URL)
            response2 = await session.get(url=self.URL, headers={"user-agent": "someotheragent"})
        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")


    @unittest_run_loop
    async def test_requests_with_progress_bar(self):
        urls = [self.URL for _ in range(5)]
        with patch('sessions.asyncsession._alive_bar') as mock_alive_bar:
            async with AsyncSession() as session:
                await session.requests(urls, progress=True)
                mock_alive_bar.assert_called_once_with(len(urls))


    @unittest_run_loop
    async def test_requests_without_progress_bar(self):
        urls = [self.URL for _ in range(5)]
        with patch('sessions.asyncsession._alive_bar') as mock_alive_bar:
            async with AsyncSession() as session:
                await session.requests(urls, progress=False)
                mock_alive_bar.assert_not_called()



#from sessions.backends import RatelimitAsyncSession
class TestRatelimitAsyncSession(AioHTTPTestCase):
    URL = URLS.BASE_URL + "/ip"
    DEFAULT_USER_AGENT = "Python/3.12 aiohttp/3.9.1"

    async def get_application(self):
        return web.Application()


    @unittest_run_loop
    async def test_redis_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        async with RatelimitAsyncSession(backend="redis", type="slidingwindow", key="redis-slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_redis_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = fixed_window_target(window, limit, n_tests)
        delta = window

        async with RatelimitAsyncSession(backend="redis", type="fixedwindow", key="redis-fixedwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_redis_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period

        async with RatelimitAsyncSession(backend="redis", type="gcra", key="redis-gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: GCRA\nLimit: {limit}\nPeriod: {period}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_redis_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        async with RatelimitAsyncSession(backend="redis", type="tokenbucket", key="redis-tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_redis_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        async with RatelimitAsyncSession(backend="redis", type="leakybucket", key="redis-leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_python_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        async with RatelimitAsyncSession(backend="py", type="slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_python_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = fixed_window_target(window, limit, n_tests)
        delta = window

        async with RatelimitAsyncSession(backend="py", type="fixedwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_python_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period

        async with RatelimitAsyncSession(backend="py", type="gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: GCRA\nLimit: {limit}\nPeriod: {period}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_python_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        async with RatelimitAsyncSession(backend="py", type="tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_python_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        async with RatelimitAsyncSession(backend="py", type="leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_sqlite_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        async with RatelimitAsyncSession(backend="sqlite", db="test.db", key="sqlite-slidingwindow", type="slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_sqlite_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = fixed_window_target(window, limit, n_tests)
        delta = window

        async with RatelimitAsyncSession(backend="sqlite", db="test.db", type="fixedwindow", key="sqlite-fixedwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_sqlite_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period

        async with RatelimitAsyncSession(backend="sqlite", db="test.db", type="gcra", key="sqlite-gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: GCRA\nLimit: {limit}\nPeriod: {period}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_sqlite_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        async with RatelimitAsyncSession(backend="sqlite", db="test.db", type="tokenbucket", key="sqlite-tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @unittest_run_loop
    async def test_sqlite_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        async with RatelimitAsyncSession(backend="sqlite", db="test.db", type="leakybucket", key="sqlite-leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = await asyncio.gather(*(session.get(url) for url in urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)

    @unittest_run_loop
    @patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent')
    async def test_random_user_agents_enabled(self):
        async with RatelimitAsyncSession(random_user_agents=True) as session:
            response = await session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), 'TestUserAgent')
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    @unittest_run_loop
    async def test_random_user_agents_disabled(self):
        async with RatelimitAsyncSession(random_user_agents=False) as session:
            response = await session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), self.DEFAULT_USER_AGENT)


    @unittest_run_loop
    async def test_custom_user_agent(self):
        async with RatelimitAsyncSession(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = await session.get(url=self.URL)
            response2 = await session.get(url=self.URL, headers={"user-agent": "someotheragent"})
        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")


    async def test_redis_server_closed(self):
        # Initialize RatelimitAsyncSession
        async with RatelimitAsyncSession(backend="redis", limit=2, window=1) as session:
            session._ratelimiter._cleanup()

        # Check that the Redis server is closed after exiting the context manager
        self.assertFalse(session._conn._is_redis_running()) # type: ignore


class TestRatelimitSession(unittest.TestCase):
    URL = URLS.BASE_URL + "/ip"
    DEFAULT_USER_AGENT = "python-httpx/0.26.0"


    def test_redis_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        with RatelimitSession(backend="redis", type="fixedwindow", key="redis-slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_redis_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        with RatelimitSession(backend="redis", type="slidingwindow", key="redis-slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_redis_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        with RatelimitSession(backend="redis", type="tokenbucket", key="redis-tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_redis_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        with RatelimitSession(backend="redis", type="leakybucket", key="redis-leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_redis_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period


        with RatelimitSession(backend="redis", type="gcra", key="redis-gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Redis\nType: GCRA\nPerdiod: {period}\nLimit: {limit}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)



    def test_sqlite_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        with RatelimitSession(backend="sqlite", db="test.db", key="sqlite-slidingwindow", type="slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)



    def test_sqlite_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = fixed_window_target(window, limit, n_tests)
        delta = window

        with RatelimitSession(backend="sqlite", db="test.db", type="fixedwindow", key="sqlite-fixedwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)



    def test_sqlite_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period

        with RatelimitSession(backend="sqlite", db="test.db", type="gcra", key="sqlite-gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: GCRA\nLimit: {limit}\nPeriod: {period}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_sqlite_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        with RatelimitSession(backend="sqlite", db="test.db", type="tokenbucket", key="sqlite-tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_sqlite_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        with RatelimitSession(backend="sqlite", db="test.db", type="leakybucket", key="sqlite-leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Sqlite\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_python_fixed_window(self):
        window, limit, n_tests = make_test("fixedwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        with RatelimitSession(backend="py", type="fixedwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: FixedWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_python_sliding_window(self):
        window, limit, n_tests = make_test("slidingwindow")

        urls = (self.URL for _ in range(n_tests))
        target_time = (window / limit) * n_tests
        delta = window

        with RatelimitSession(backend="py", type="slidingwindow", limit=limit, window=window) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: SlidingWindow\nLimit: {limit}\nWindow: {window}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_python_gcra(self):
        period, limit, n_tests = make_test("gcra")

        urls = (self.URL for _ in range(n_tests))
        target_time = gcra_target(period, limit, n_tests)
        delta = period


        with RatelimitSession(backend="memory", type="gcra", period=period, limit=limit) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: GCRA\nPerdiod: {period}\nLimit: {limit}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_python_token_bucket(self):
        capacity, fill_rate, n_tests = make_test("tokenbucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = token_bucket_target(capacity, fill_rate, n_tests)
        delta = capacity / fill_rate

        with RatelimitSession(backend="memory", type="tokenbucket", capacity=capacity, fill_rate=fill_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: TokenBucket\nCapacity: {capacity}\nFill_rate: {fill_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    def test_python_leaky_bucket(self):
        capacity, leak_rate, n_tests = make_test("leakybucket")

        urls = (self.URL for _ in range(n_tests))
        target_time = leaky_bucket_target(capacity, leak_rate, n_tests)
        delta = leak_rate / capacity

        with RatelimitSession(backend="memory", type="leakybucket", capacity=capacity, leak_rate=leak_rate) as session:
            begin = perf_counter()
            results = tuple(map(session.get, urls))
            end = perf_counter()

        execution_time = end - begin
        print(f"\nBackend: Python\nType: LeakyBucket\nCapacity: {capacity}\nLeak_rate: {leak_rate}\nN_tests: {n_tests}\nTarget_time: {target_time}\nDelta: {delta}\nExecution_time: {execution_time}\n")
        self.assertAlmostEqual(execution_time, target_time, delta=delta)


    @patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent')
    def test_random_user_agents_enabled(self):
        with mock.patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent'):
            with RatelimitSession(random_user_agents=True) as session:
                response = session.get(self.URL)
                self.assertEqual(response.request.headers.get('User-Agent'), 'TestUserAgent')
                self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    def test_random_user_agents_disabled(self):
        with RatelimitSession(random_user_agents=False) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), self.DEFAULT_USER_AGENT)


    def test_custom_user_agent(self):
        with RatelimitSession(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = session.get(url=self.URL)
            response2 = session.get(url=self.URL, headers={"user-agent": "someotheragent"})
        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")


    def test_redis_server_closed(self):
        # Initialize RatelimitSession
        with RatelimitSession(backend="redis", limit=2, window=1) as session:
            session._ratelimiter._cleanup()

        # Check that the Redis server is closed after exiting the context manager
        self.assertFalse(session._conn._is_redis_running()) # type: ignore


class TestSession(unittest.TestCase):
    DEFAULT_USER_AGENT = "python-httpx/0.26.0"
    URL = URLS.BASE_URL + "/ip"


    @patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent')
    def test_random_user_agents_enabled(self):
        with Session(random_user_agents=True) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get("User-Agent"), 'TestUserAgent')
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    def test_random_user_agents_disabled(self):
        with Session(random_user_agents=False) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    def test_custom_user_agent(self):
        with Session(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = session.get(url=self.URL)
            response2 = session.get(url=self.URL, headers={"user-agent": "someotheragent"})

        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")



    @patch('sessions.session._alive_bar')
    def test_requests_with_progress_bar(self, mock_alive_bar):
        urls = [self.URL for i in range(5)]
        with Session() as session:
            session.requests(urls, progress=True)
            mock_alive_bar.assert_called_once_with(len(urls))


    def test_requests_without_progress_bar(self):
        urls = [self.URL for i in range(5)]
        with Session() as session:
            with patch('sessions.session._alive_bar') as mock_alive_bar:
                session.requests(urls, progress=False)
                mock_alive_bar.assert_not_called()



"""
from sessions.proxysession import ProxySession
ProxySession.update_proxies()

class TestProxySession(unittest.TestCase):
    DEFAULT_USER_AGENT = "python-requests/2.31.0"
    URL = "https://httpbin.org/ip"

    def test_proxy_ip(self):
        with ProxySession(random_user_agents=False) as session:
            response = session.get(self.URL)
            ip = response.json().get("origin")
            self.assertNotEqual(ip, "172.17.0.1")
            print(response.request.headers)


    @patch('sessions.useragents.UserAgents.user_agent', 'TestUserAgent')
    def test_random_user_agents_enabled(self):
        with ProxySession(random_user_agents=True) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get("User-Agent"), 'TestUserAgent')
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    def test_random_user_agents_disabled(self):
        with ProxySession(random_user_agents=False) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    def test_custom_user_agent(self):
        with ProxySession(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = session.get(url=self.URL)
            response2 = session.get(url=self.URL, headers={"user-agent": "someotheragent"})

        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")
"""

if __name__ == '__main__':
    unittest.main()
