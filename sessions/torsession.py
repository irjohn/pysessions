from random import (
    Random as _Random
)
from itertools import (
    cycle as _cycle
)

from stem import (
    Signal as _Signal
)
from stem.control import (
    Controller as _Controller
)

from httpx import (
    Client as _Client,
)

from .useragents import (
    UserAgents as _UserAgents
)

from .variables import (
    IP_APIS as _IP_APIS
)

from .ratelimit import (
    Ratelimit as _Ratelimit,
)

class TorSession(_Client):
    RNG = _Random()

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
        self.ports = _cycle(tor_ports)
        self.headers = headers
        

    @property
    def headers(self):
        return _UserAgents.headers | self._headers
    

    @headers.setter
    def headers(self, value):
        self._headers = value
    
    
    def check_service(self):
        from psutil import process_iter as _process_iter
        if not any(process.name() == "tor" for process in _process_iter()):
            from psutil import (
                Popen as _Popen
            )
            from subprocess import (
                DEVNULL as _DEVNULL,
            )
            tor = _Popen([
                "/usr/bin/tor",
                "-f", "/etc/tor/torrc",
                "--runasdaemon", "1"
            ], stdout=_DEVNULL, stderr=_DEVNULL)

            if not tor.is_running():
                return self.check_service()
        return
    
    @staticmethod
    def new_id(func):     
        def wrapper(self, *args, **kwargs):         
            with _Controller.from_port(port=self.tor_cport) as controller:
                controller.authenticate(password=self.password)
                controller.signal(_Signal.NEWNYM)
            return func(self, *args, **kwargs)
        return wrapper


    def check_ip(self):
        my_ip = self.get(self.RNG.choice(_IP_APIS)).text
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


class TorRatelimitSession(TorSession, _Ratelimit):
    _ID = 0

    def __init__(self, *args, limit=10, window=1, **kwargs):
        TorRatelimitSession._ID += 1
        self._limit = limit
        self._window = window
        TorSession.__init__(self, *args, **kwargs)
        _Ratelimit.__init__(self, limit, window)
        self._key = f"TorRatelimitSession:{self._ID}"

    
    def request(self, method, url, *, headers=None, **kwargs):
        result =  super(TorSession, self).request(method, url, headers=headers, **kwargs)
        self.increment()
        return result