import unittest
import pkg_resources
from sys import version_info as __version__
from dataclasses import asdict
from random import Random

from rich import print
from sessions.utils import Urls
from sessions.config import SessionConfig as config
from sessions.testing import run_sync_tests, cleanup_dbs

config.raise_errors = True

RNG = Random()
urls = Urls("http://httpbin.org")


assert_message = lambda result: f"{result.execution_time} not within {result.delta} ({result.observed_delta} observed) |\nBackend: {result.backend.upper()}\nRatelimit: {result.ratelimit_type.upper()}\n{asdict(result)}"
target_time = 10


class TestSlidingWindow(unittest.TestCase):
    def test_sliding_window(self):
        results = run_sync_tests(type="slidingwindow", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestFixedWindow(unittest.TestCase):
    def test_fixed_window(self):
        results = run_sync_tests(type="fixedwindow", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestTokenBucket(unittest.TestCase):
    def test_token_bucket(self):
        results = run_sync_tests(type="tokenbucket", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestLeakyBucket(unittest.TestCase):
    def test_leaky_bucket(self):
        results = run_sync_tests(type="leakybucket", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))


class TestGCRA(unittest.TestCase):
    def test_gcra(self):
        results = run_sync_tests(type="gcra", target_time=target_time)
        for typename, results in results.items():
            for result in results:
                self.assertTrue(result.passed, assert_message(result))

if __name__ == "__main__":
    unittest.main()