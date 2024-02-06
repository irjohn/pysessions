from random import Random

from .vars import USER_AGENTS as _USER_AGENTS


class UserAgents:
    """
    A class for generating user agents.

    Attributes:
        RNG: An instance of the Random class for generating random numbers.
        agents: A generator object that yields user agents.
    """

    RNG = Random()
    agents = (ua for ua in RNG.choices(_USER_AGENTS, k=1000))

    def __init__(self, n_requests=None):
        self.set_agents(n_requests)

    def __call__(self):
        return self.user_agent

    @classmethod
    def set_agents(cls, n_requests=None):
        """
        Sets the user agents based on the number of requests.

        Args:
            n_requests: An integer representing the number of requests. If None, defaults to 1000.
        """
        cls.agents = (ua for ua in cls.RNG.choices(_USER_AGENTS, k=n_requests or 1000))

    @classmethod
    @property
    def user_agent(cls):
        """
        Returns the next user agent from the agents generator.

        If all user agents have been exhausted, a new set of agents is generated.

        Returns:
            A string representing the user agent.
        """
        if not hasattr(cls, "agents"):
            cls.set_agents()
        try:
            return next(cls.agents)
        except StopIteration:
            cls.set_agents()
            return next(cls.agents)


useragent = UserAgents()