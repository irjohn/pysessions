from random import SystemRandom
from itertools import cycle

from stem import Signal
from stem.control import Controller
from httpx import (
    Client,
    Headers
)

from .useragents import UserAgents
from .variables import IP_APIS

class TorSession(Client):
    RNG = SystemRandom()

    """
    tor_ports = specify Tor socks ports tuple (default is (9150,), as the default in Tor Browser),
    if more than one port is set, the requests will be sent sequentially through the each port;
    tor_cport = specify Tor control port (default is 9151 for Tor Browser, for Tor use 9051);
    password = specify Tor control port password (default is None);
    autochange_id = number of requests via a one Tor socks port (default=5) to change TOR identity,
    specify autochange_id = 0 to turn off autochange Tor identity;
    threads = specify threads to download urls list (default=8).
    """

    def __init__(self, tor_ports=(9000, 9001, 9002, 9003, 9004), tor_cport=9051,
                 password=None, autochange_id=5, headers={}, **kwargs):
        self._headers = headers
        self.check_service()
        super().__init__(**kwargs)
        self.tor_ports = tor_ports
        self.tor_cport = tor_cport
        self.password = password
        self.autochange_id = autochange_id
        self.ports = cycle(tor_ports)
        self.headers = headers
        

    @property
    def headers(self):
        return Headers(UserAgents.headers | self._headers)
    

    @headers.setter
    def headers(self, value):
        self._headers = value
    
    
    def check_service(self):
        from psutil import process_iter
        if not any(process.name() == "tor" for process in process_iter()):
            from psutil import Popen
            from os import devnull
            tor = Popen([
                "/usr/bin/tor",
                "-f", "/etc/tor/torrc",
                "--runasdaemon", "1"
            ], stdout=open(devnull, 'w'), stderr=open(devnull, 'w'))

            if not tor.is_running():
                return self.check_service()
        return
    

    def new_id(func):     
        def wrapper(self, *args, **kwargs):         
            with Controller.from_port(port=self.tor_cport) as controller:
                controller.authenticate(password=self.password)
                controller.signal(Signal.NEWNYM)
            return func(self, *args, **kwargs)
        return wrapper


    def check_ip(self):
        my_ip = self.get(self.RNG.choice(IP_APIS)).text
        return my_ip
    

    @new_id
    def request(self, method, url, headers=None, **kwargs):
        port = next(self.ports)

        # if using requests_tor as drop in replacement for requests remove any user set proxy
        if kwargs.__contains__("proxy"):
            del kwargs["proxy"]

        proxy = {
            "http": f"socks5h://localhost:{port}",
            "https": f"socks5h://localhost:{port}",
        }

        try:
            resp = super().request(method, url, headers=headers or self.headers, **kwargs)
        except Exception as e:
            print(e)
            return self.request(method, url, proxy=proxy, **kwargs)
        return resp


    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)


    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)


    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)


    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)


    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)
