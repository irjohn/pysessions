from random import SystemRandom

from httpx import Headers

from .variables import USER_AGENTS

class UserAgents:
    ALL = [*USER_AGENTS["desktop"], *USER_AGENTS["mobile"]]
    DESKTOP = USER_AGENTS["desktop"]
    MOBILE = USER_AGENTS["mobile"]
    TYPE = "ALL"
    RNG = SystemRandom()

    def __init__(self, type="all", n_requests=None):
        self.set_agents(type.upper(), n_requests)

    @classmethod
    def set_agents(cls, type=None, n_requests=None):
        type = type or cls.TYPE
        cls.agents = (
            ua
            for ua in cls.RNG.choices(
                getattr(cls, type),
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
        return Headers({
            'User-Agent': cls.ua,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })