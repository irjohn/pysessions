from random import SystemRandom

from httpx import Headers

from .variables import USER_AGENTS

class UserAgents:
    RNG = SystemRandom()

    def __init__(self, n_requests=None):
        self.set_agents(n_requests)


    @classmethod
    def set_agents(cls, n_requests=None):
        cls.agents = (
            ua
            for ua in cls.RNG.choices(
                USER_AGENTS,
                k=n_requests or 250
            )
        )


    @classmethod
    @property
    def ua(cls):
        if not hasattr(cls, "agents"):
            cls.set_agents()
        try:
            return next(cls.agents)
        except StopIteration:
            cls.set_agents()
            return next(cls.agents)


    @classmethod
    @property
    def headers(cls):
        return {
            "User-Agent": cls.ua,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
        }