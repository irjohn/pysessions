import os as _os
from random import Random as _Random
from pickle import (
    load as _load,
    dump as _dump,
    HIGHEST_PROTOCOL as _PICKLE_HIGHEST_PROTOCOL
)

from dotenv import dotenv_values as _dotenv_values
from requests import Session
from urllib.parse import (
    quote as _quote,
    unquote as _unquote,
)

from .useragents import UserAgents as _UserAgents

_MODULE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_NORDVPN_SERVER_URL = "https://nordvpn.com/api/server"


def _path(relative):
    return _os.path.join(_MODULE_DIR, relative)

try:
    with open(_path("proxies.tuple"), "rb") as f:
        _PROXIES = _load(f)
except:
    with Session() as session:
        response = session.get(_NORDVPN_SERVER_URL)
    servers = response.json()
    _PROXIES = tuple(server["domain"] for server in servers if server["features"]["proxy_ssl"])
    with open(_path("proxies.tuple"), "wb") as f:
        _dump(_PROXIES, f, protocol=_PICKLE_HIGHEST_PROTOCOL)


class ProxySession(Session):
    def __init__(self, username="", password="", headers=None, random_user_agents=True, **kwargs):
        super(ProxySession, self).__init__(**kwargs)
        env = _dotenv_values()
        self._username = _quote(_unquote(username)) or env.get("PROXY_USERNAME", env.get("NORDVPN_USERNAME", ""))
        self._password = _quote(_unquote(password)) or env.get("PROXY_PASSWORD", env.get("NORDVPN_PASSWORD", ""))
        self._random_user_agents = random_user_agents
        self._rng = _Random()
        self.headers = headers or self.headers


    @classmethod
    def update_proxies(cls):
        global _PROXIES
        with Session() as session:
            response = session.get(_NORDVPN_SERVER_URL)
        servers = response.json()
        _PROXIES = tuple(server["domain"] for server in servers if server["features"]["proxy_ssl"])
        with open(_path("proxies.tuple"), "wb") as f:
            _dump(_PROXIES, f, protocol=_PICKLE_HIGHEST_PROTOCOL)


    @property
    def proxies(self):
        url = f"{self._username}:{self._password}@{self._rng.choice(_PROXIES)}"
        return {
            "http": f"http://{url}:89",
            "https": f"https://{url}:89"
        }


    @proxies.setter
    def proxies(self, value):
        pass


    def request(self, method, url, headers=None, **kwargs):
        try:
            headers = headers or _UserAgents.headers if self._random_user_agents else self.headers
            return super(ProxySession, self).request(method, url, proxies=self.proxies, headers=headers, **kwargs)
        except:
            return self.request(method, url, **kwargs)


    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)


    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)


    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)


    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)


    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)


    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)