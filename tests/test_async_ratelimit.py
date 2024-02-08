import unittest
from dataclasses import asdict
from random import Random

from sessions.utils import Urls
from sessions.config import SessionConfig as config
from sessions.testing import run_async_tests, cleanup_dbs

config.raise_errors = True

RNG = Random()
urls = Urls("http://httpbin.org")

assert_message = lambda result: f"{result.execution_time} not within {result.delta} ({result.observed_delta} observed) |\nBackend: {result.backend.upper()}\nRatelimit: {result.ratelimit_type.upper()}\n{asdict(result)}"
target_time = 10

class TestAsyncSlidingWindow(unittest.IsolatedAsyncioTestCase):
    async def test_sliding_window(self):
        results = await run_async_tests(type="slidingwindow", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestAsyncFixedWindow(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_window(self):
        results = await run_async_tests(type="fixedwindow", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestAsyncTokenBucket(unittest.IsolatedAsyncioTestCase):
    async def test_token_bucket(self):
        results = await run_async_tests(type="tokenbucket", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestAsyncLeakyBucket(unittest.IsolatedAsyncioTestCase):
    async def test_leaky_bucket(self):
        results = await run_async_tests(type="leakybucket", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestAsyncGCRA(unittest.IsolatedAsyncioTestCase):
    async def test_gcra(self):
        results = await run_async_tests(type="gcra", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))