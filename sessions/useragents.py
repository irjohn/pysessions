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
    CONSTANT = 1000
    MAX = 25000


    def __init__(self, multiplier=3):
        self.n = 2
        self.multiplier = multiplier
        self.set_agents(self.n)

    def __call__(self):
        try:
            return next(self.agents)
        except StopIteration:
            self.n *= self.multiplier
            self.set_agents(min(self.n, self.MAX))
            return next(self.agents)

    def set_agents(self, n_requests=None):
        """
        Sets the user agents based on the number of requests.

        Args:
            n_requests: An integer representing the number of requests. If None, defaults to 1000.
        """
        self.agents = (ua for ua in self.RNG.choices(_USER_AGENTS, k=n_requests or self.CONSTANT))

    @property
    def user_agent(self):
        """
        Returns the next user agent from the agents generator.

        If all user agents have been exhausted, a new set of agents is generated.

        Returns:
            A string representing the user agent.
        """
        try:
            return next(self.agents)
        except StopIteration:
            self.n *= self.multiplier
            self.set_agents(min(self.n, self.MAX))
            return next(self.agents)


useragent = UserAgents()