try:
    from stem import Signal as _Signal
    from stem.control import Controller as _Controller
    _has_stem = True
except ImportError:
    _has_stem = False


if _has_stem:
    from os import getpid as _getpid
    from random import Random as _Random
    from itertools import cycle as _cycle
    from atexit import register as _register
    from time import sleep as _sleep
    from functools import wraps as _wraps
    from requests import Session as _Session

    from .useragents import UserAgents as _UserAgents
    from .vars import  IP_APIS as _IP_APIS


    def _check_tor_service():
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
            _sleep(3)
            if not tor.is_running():
                return _check_tor_service()
        return

    _check_tor_service()


    def _new_id(func):
        @_wraps(func)
        def wrapper(self, *args, **kwargs):
            self._controller.authenticate(password=self.password)
            self._controller.signal(_Signal.NEWNYM)
            return func(self, *args, **kwargs)
        return wrapper



    class TorSession(_Session):
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
                    password=None, autochange_id=5, headers=None, random_user_agents=True, **kwargs):
            self.headers = headers if isinstance(headers, dict) else {}
            self._random_user_agents = random_user_agents
            self._tor_ports = tor_ports
            self._tor_cport = tor_cport
            self._password = password
            self.autochange_id = autochange_id
            self.ports = _cycle(tor_ports)
            super().__init__()

            self._start_controller()
            _register(lambda: self._controller.close())


        @property
        def tor_ports(self):
            return self._tor_ports


        @property
        def tor_cport(self):
            return self._tor_cport


        @property
        def password(self):
            return self._password


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
                with _Controller.from_port(port=self.tor_cport) as controller:
                    controller.authenticate(password=self.password)
                    controller.signal(_Signal.NEWNYM)
                return func(self, *args, **kwargs)
            return wrapper


        def check_ip(self):
            my_ip = self.get(self.RNG.choice(_IP_APIS)).text
            return my_ip


        def _start_controller(self):
            self._controller = _Controller.from_port(port=self.tor_cport)


        @_new_id
        def request(self, method, url, headers=None, **kwargs):
            port = next(self.ports)

            # if using requests_tor as drop in replacement for requests remove any user set proxy
            if kwargs.__contains__("proxy"):
                del kwargs["proxy"]


            if kwargs.__contains__("proxies"):
                del kwargs["proxies"]


            proxy = {
                "http": f"socks5h://localhost:{port}",
                "https": f"socks5h://localhost:{port}",
            }
            if self._random_user_agents:
                headers = headers or {}
                headers["User-Agent"] = _UserAgents.user_agent
            try:
                resp = super().request(method, url, headers=headers, proxies=proxy, **kwargs)
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