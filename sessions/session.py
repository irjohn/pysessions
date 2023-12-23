from httpx import Client, Timeout, Limits

from .useragents import UserAgents


class Session(Client):
    def __init__(self, *, auth=None, params=None, headers=None, cookies=None, verify=True, cert=None, http1=True, http2=True, proxies=None, mounts=None, timeout=Timeout(timeout=5.0), follow_redirects=False, limits=Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=5.0), max_redirects=20, event_hooks=None, base_url='', transport=None, app=None, trust_env=True, default_encoding='utf-8'):
        super().__init__(auth=auth,  params=params,  headers=headers,  cookies=cookies,  verify=verify,  cert=cert,  http1=http1,  http2=http2, proxies=proxies,  mounts=mounts,  timeout=timeout, follow_redirects=follow_redirects, limits=limits, max_redirects=max_redirects, event_hooks=event_hooks, base_url=base_url, transport=transport,  app=app,  trust_env=trust_env,  default_encoding=default_encoding)


    def __enter__(self):
        return self
    

    def __exit__(self, *args):
        self.close()
        return
    

    @property
    def headers(self):
        return self._headers or UserAgents.headers


    @headers.setter
    def headers(self, value):
        self._headers = value


    def request(self, method, url, *, headers=None, **kwargs):
        return super().request(method, url, headers=headers or self.headers, **kwargs)


    def get(self, url, **kwargs):
        return super().request("GET", url, **kwargs)


    def head(self, url, **kwargs):
        return super().request("HEAD", url, **kwargs)


    def options(self, url, **kwargs):
        return super().request("OPTIONS", url, **kwargs)


    def delete(self, url, **kwargs):
        return super().request("DELETE", url, **kwargs)


    def post(self, url, **kwargs):
        return super().request("POST", url, **kwargs)
    

    def put(self, url, **kwargs):
        return super().request("PUT", url, **kwargs)
    

    def patch(self, url, **kwargs):
        return super().request("PATCH", url, **kwargs)