import unittest
from sessions import Session, AsyncSession
from sessions.config import SessionConfig as config
from sessions.objects import Response

config.raise_errors = False
config.return_callbacks = True
config.run_callbacks_on_error = True

def callback1(response: Response):
    return response.ok

def callback2(response: Response):
    return response.elapsed

def callback3(response: Response):
    raise ValueError("This is a test")

fail_url = "http://httpbin.org/status/404"
success_url = "http://httpbin.org/status/200"
callbacks = (callback1, callback2)


class TestSessionCallbacks(unittest.TestCase):
    def test_callbacks_with_exception(self):
        with Session(timeout=0.00001) as session:
            response = session.get(success_url, callbacks=callbacks)
            self.assertFalse(response.ok)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))

    def test_callbacks_success(self):
        with Session() as session:
            response = session.get(success_url, callbacks=callbacks)
            self.assertTrue(response.ok)
            self.assertTrue(response.elapsed.total_seconds() > 0)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))

    def test_callbacks_fail(self):
        with Session() as session:
            response = session.get(fail_url, callbacks=callbacks)
            self.assertFalse(response.ok)
            self.assertTrue(response.elapsed.total_seconds() > 0)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))

class TestAsyncSessionCallbacks(unittest.IsolatedAsyncioTestCase):
    async def test_callbacks_with_exception(self):
        async with AsyncSession(timeout=0.00001) as session:
            response = await session.get(success_url, callbacks=callbacks)
            self.assertFalse(response.ok)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))

    async def test_callbacks_success(self):
        async with AsyncSession() as session:
            response = await session.get(success_url, callbacks=callbacks)
            self.assertTrue(response.ok)
            self.assertTrue(response.elapsed.total_seconds() > 0)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))

    async def test_callbacks_fail(self):
        async with AsyncSession() as session:
            response = await session.get(fail_url, callbacks=callbacks)
            self.assertFalse(response.ok)
            self.assertTrue(response.elapsed.total_seconds() > 0)
            self.assertTupleEqual(response.callbacks, (response.ok, response.elapsed))


if __name__ == "__main__":
    unittest.main()