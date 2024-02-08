import os
from random import Random
from urllib.parse import quote, unquote
from pickle import (
    load,
    dump,
    HIGHEST_PROTOCOL as PICKLE_HIGHEST_PROTOCOL
)

from dotenv import dotenv_values
from requests import Session
from requests.auth import HTTPProxyAuth

from .useragents import useragent

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_NORDVPN_SERVER_URL = "https://nordvpn.com/api/server"


def _path(relative):
    return os.path.join(_MODULE_DIR, relative)

try:
    with open(_path("proxies.tuple"), "rb") as f:
        PROXIES = load(f)
except:
    with Session() as session:
        response = session.get(_NORDVPN_SERVER_URL)
    servers = response.json()
    PROXIES = tuple(server["domain"] for server in servers if server["features"]["proxy_ssl"])
    with open(_path("proxies.tuple"), "wb") as f:
        dump(PROXIES, f, protocol=PICKLE_HIGHEST_PROTOCOL)


class ProxySession(Session):
    def __init__(self, username="", password="", headers=None, random_user_agents=True, **kwargs):
        headers = headers if isinstance(headers, dict) else {}
        super().__init__()
        self._rng = Random()
        self._random_user_agents = random_user_agents
        env = dotenv_values()
        self._username = quote(unquote(username)) or env.get("PROXY_USERNAME", env.get("NORDVPN_USERNAME", ""))
        self._password = quote(unquote(password)) or env.get("PROXY_PASSWORD", env.get("NORDVPN_PASSWORD", ""))
        self._auth = HTTPProxyAuth(self._username, self._password)


    @classmethod
    def update_proxies(cls):
        global PROXIES
        with Session() as session:
            response = session.get(_NORDVPN_SERVER_URL)
        servers = response.json()
        PROXIES = tuple(server["domain"] for server in servers if server["features"]["proxy_ssl"])
        with open(_path("proxies.tuple"), "wb") as f:
            dump(PROXIES, f, protocol=PICKLE_HIGHEST_PROTOCOL)


    @property
    def proxies(self):
        #url = f"{self._username}:{self._password}@{self._rng.choice(PROXIES)}"
        url = self._rng.choice(PROXIES)
        return {
            "http": f"http://{url}:89",
            "https": f"https://{url}:89"
        }


    @proxies.setter
    def proxies(self, value):
        pass


    def request(self, method, url, headers=None, **kwargs):
        proxies = self.proxies
        print(proxies)
        if self._random_user_agents:
            headers = headers or {}
            headers["User-Agent"] = useragent()
        try:
            return super().request(method=method, url=url, proxies=proxies, headers=headers, auth=self._auth, **kwargs)
        except Exception as e:
            print(e)
            return self.request(method=method, url=url, **kwargs)


    def get(self, url, **kwargs):
        return self.request(method="GET", url=url, **kwargs)


    def head(self, url, **kwargs):
        return self.request(method="HEAD", url=url, **kwargs)


    def options(self, url, **kwargs):
        return self.request(method="OPTIONS", url=url, **kwargs)


    def delete(self, url, **kwargs):
        return self.request(method="DELETE", url=url, **kwargs)


    def post(self, url, **kwargs):
        return self.request(method="POST", url=url, **kwargs)


    def put(self, url, **kwargs):
        return self.request(method="PUT", url=url, **kwargs)


    def patch(self, url, **kwargs):
        return self.request(method="PATCH", url=url, **kwargs)