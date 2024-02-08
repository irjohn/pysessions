import unittest
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from sessions.utils import Urls
from sessions import Session, AsyncSession
from sessions.config import SessionConfig as config
from sessions.vars import AIOHTTP_DEFAULT_AGENT, HTTPX_DEFAULT_AGENT
from sessions.useragents import useragent

config.raise_errors = False

URLS = Urls("http://httpbin.org")



class TestSession(unittest.TestCase):
    DEFAULT_USER_AGENT = HTTPX_DEFAULT_AGENT
    URL = URLS.BASE_URL + "/ip"

    def test_random_user_agents_enabled(self):
        with Session(random_user_agents=True) as session:
            response = session.get(self.URL)
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)

    def test_random_user_agents_disabled(self):
        with Session(random_user_agents=False) as session:
            response = session.get(self.URL)
            self.assertEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)

    def test_custom_user_agent_with_random_with_session_headers(self):
        with Session(headers={"user-agent": "custom-user-agent"}) as session:
            response1 = session.get(url=self.URL)
            response2 = session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
            response3 = session.get(url=self.URL)
        self.assertEqual(response1.request.headers.get("User-Agent"), "custom-user-agent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "some-other-agent")
        self.assertEqual(response3.request.headers.get("User-Agent"), "custom-user-agent")


    def test_custom_user_agent_with_random_with_session_headers_request_override(self):
        with Session(headers={"user-agent": "custom-user-agent"}) as session:
            response1 = session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
            response2 = session.get(url=self.URL)
        self.assertEqual(response1.request.headers.get("User-Agent"), "some-other-agent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "custom-user-agent")

    def test_custom_user_agent_with_random_with_no_session_headers_request_override(self):
        with Session() as session:
            response = session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
        self.assertEqual(response.request.headers.get("User-Agent"), "some-other-agent")

    def test_custom_user_agent_with_no_random_with_session_headers_request_override(self):
        with Session(random_user_agents=False, headers={"User-Agent": "some-user-agent"}) as session:
            response2 = session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
        self.assertEqual(response2.request.headers.get("User-Agent"), "some-other-agent")

    def test_custom_user_agent_with_no_random_with_session_headers(self):
        with Session(random_user_agents=False, headers={"User-Agent": "some-user-agent"}) as session:
            response = session.get(url=self.URL)
        self.assertEqual(response.request.headers.get("User-Agent"), "some-user-agent")


    @unittest.skip
    def test_requests_with_progress_bar(self):
        urls = [self.URL for i in range(5)]
        with Session() as session:
            with patch("sessions.session.alive_bar") as mock_alive_bar:
                session.requests(urls, progress=True)
                mock_alive_bar.assert_called_once_with(len(urls))

    @unittest.skip
    def test_requests_without_progress_bar(self):
        urls = [self.URL for i in range(5)]
        with Session() as session:
            with patch("sessions.session.alive_bar") as mock_alive_bar:
                session.requests(urls, progress=False)
                mock_alive_bar.assert_not_called()


class TestAsyncSession(AioHTTPTestCase):
    DEFAULT_USER_AGENT = AIOHTTP_DEFAULT_AGENT
    URL = URLS.BASE_URL + "/ip"

    async def get_application(self):
        return web.Application()

    #@unittest_run_loop
    async def test_random_user_agents_enabled(self):
        async with AsyncSession(random_user_agents=True) as session:
            response = await session.get(self.URL)
            self.assertNotEqual(response.request.headers.get("User-Agent"), self.DEFAULT_USER_AGENT)


    #@unittest_run_loop
    async def test_random_user_agents_disabled(self):
        async with AsyncSession(random_user_agents=False) as session:
            response = await session.get(self.URL)
            self.assertEqual(response.request.headers.get('User-Agent'), self.DEFAULT_USER_AGENT)


    #@unittest_run_loop
    async def test_custom_user_agent(self):
        async with AsyncSession(random_user_agents=False, headers={"User-Agent": "someuseragent"}) as session:
            response1 = await session.get(url=self.URL)
            response2 = await session.get(url=self.URL, headers={"user-agent": "someotheragent"})
        self.assertEqual(response1.request.headers.get("User-Agent"), "someuseragent")
        self.assertEqual(response2.request.headers.get("User-Agent"), "someotheragent")

    async def test_custom_user_agent_with_random_with_session_headers_request(self):
        async with AsyncSession(headers={"user-agent": "custom-user-agent"}) as session:
            response = await session.get(url=self.URL)
        self.assertEqual(response.request.headers.get("User-Agent"), "custom-user-agent")
        self.assertEqual(response.request.headers.get("user-agent"), "custom-user-agent")

    async def test_custom_user_agent_with_random_with_session_headers_request_override(self):
        async with AsyncSession(headers={"user-agent": "custom-user-agent"}) as session:
            response = await session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
        self.assertEqual(response.request.headers.get("User-Agent"), "some-other-agent")

    async def test_custom_user_agent_with_random_with_no_session_headers_request_override(self):
        async with AsyncSession() as session:
            response = await session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
        self.assertEqual(response.request.headers.get("User-Agent"), "some-other-agent")

    async def test_custom_user_agent_with_no_random_with_session_headers_request_override(self):
        async with AsyncSession(random_user_agents=False, headers={"User-Agent": "some-user-agent"}) as session:
            response2 = await session.get(url=self.URL, headers={"user-agent": "some-other-agent"})
        self.assertEqual(response2.request.headers.get("User-Agent"), "some-other-agent")

    async def test_custom_user_agent_with_no_random_with_session_headers(self):
        async with AsyncSession(random_user_agents=False, headers={"User-Agent": "some-user-agent"}) as session:
            response = await session.get(url=self.URL)
        self.assertEqual(response.request.headers.get("User-Agent"), "some-user-agent")

    @unittest_run_loop
    async def test_requests_with_progress_bar(self):
        urls = [self.URL for _ in range(5)]
        with patch('sessions.asyncsession.alive_bar') as mock_alive_bar:
            async with AsyncSession() as session:
                await session.requests(urls, progress=True)
                mock_alive_bar.assert_called_once_with(len(urls))


    @unittest_run_loop
    async def test_requests_without_progress_bar(self):
        urls = [self.URL for _ in range(5)]
        with patch('sessions.asyncsession.alive_bar') as mock_alive_bar:
            async with AsyncSession() as session:
                await session.requests(urls, progress=False)
                mock_alive_bar.assert_not_called()



if __name__ == '__main__':
    unittest.main()
