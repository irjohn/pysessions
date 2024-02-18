from datetime import timedelta
from dataclasses import dataclass, field
from typing import Sequence

from orjson import loads
from yarl import URL
from aiohttp.connector import Connection
from http.cookies import SimpleCookie
from multidict import CIMultiDictProxy, MultiDictProxy, CIMultiDict
from requests import Response as RequestsResponse
from httpx import Response as HTTPXResponse
from aiohttp import (
    RequestInfo,
    ClientResponse,
    HttpVersion,
)

from .vars import STATUS_CODES


@dataclass(slots=True, frozen=True, eq=False)
class Request:
    """
    Represents an HTTP request.

    Attributes:
        url (str): The URL of the request.
        method (str): The HTTP method of the request.
        headers (dict | CIMultiDictProxy | None): The headers of the request.
        real_url (str | URL | None): The real URL of the request.
        cookies (SimpleCookie | None): The cookies of the request.
    """

    url: str | None                             = None
    method: str | None                          = None
    headers: dict | CIMultiDictProxy | None     = None
    real_url: str | URL | None                  = None
    cookies: SimpleCookie | None                = None

    def __post_init__(self):
        if self.url is not None:
            self.__set("url", URL(self.url))
        if self.real_url is not None:
            self.__set("real_url", URL(self.real_url))
        if self.cookies is not None:
            self.__set("cookies", SimpleCookie(self.cookies))
        if self.headers is not None:
            self.__set("headers", CIMultiDictProxy(CIMultiDict(self.headers)))

    def __set(self, name, value):
        object.__setattr__(self, name, value)


@dataclass(slots=True, frozen=True)
class Response:
    """
    Represents an HTTP response.

    Attributes:
        callbacks (tuple | None): Callback functions to be executed after the response is received.
        errors (Exception | None): Any exception that occurred during the request.
        version (HttpVersion | None): HTTP version of the response.
        status (int | None): HTTP status code of the response.
        reason (str | None): Reason phrase associated with the status code.
        ok (bool | None): Indicates if the response was successful.
        method (str | None): HTTP method used for the request.
        url (URL | None): URL of the request.
        real_url (URL | None): The actual URL after any redirects.
        connection (Connection | None): Connection object used for the request.
        content (bytes | None | None): Raw content of the response.
        cookies (SimpleCookie | None): Cookies received in the response.
        headers (CIMultiDictProxy | None): Headers of the response.
        raw_headers (tuple | None): Raw headers of the response.
        links (MultiDictProxy | None): Links extracted from the response.
        content_type (str | None): Content type of the response.
        encoding (str | None): Encoding of the response.
        charset (str | None | None): Character set of the response.
        content_disposition (str | None): Content disposition of the response.
        history (Sequence[ClientResponse|RequestsResponse|HTTPXResponse] | None): History of the response.
        request (RequestInfo | None): Information about the request.
        elapsed (timedelta | None): Time elapsed for the request.
        _json (dict | None): Parsed JSON content of the response.
        _text (str | None): Decoded text content of the response.

    Methods:
        __repr__(): Returns a string representation of the response.
        __bool__(): Returns True if the response is considered successful.
        serialize(): Serializes the response object into a dictionary.
        deserialize(data: dict): Deserializes a dictionary into a response object.
        text: Property that returns the decoded text content of the response.
        json: Property that returns the parsed JSON content of the response.
        request_info: Property that returns information about the request.
        status_code: Property that returns the HTTP status code of the response.
        http_version: Property that returns the HTTP version of the response.
        reason_phrase: Property that returns the reason phrase associated with the status code.
        set_callbacks(results: tuple): Sets the callback functions for the response.
    """
    callbacks: tuple | None                                                                  = None
    errors: Exception | None                                                                 = None
    version: HttpVersion | None                                                              = None
    status: int | None                                                                       = None
    reason: str | None                                                                       = None
    ok: bool | None                                                                          = None
    method: str | None                                                                       = None
    url: URL | None                                                                          = None
    real_url: URL | None                                                                     = None
    connection: Connection | None                                                            = None
    content: bytes | None | None                                                             = None
    cookies: SimpleCookie | None                                                             = None
    headers: CIMultiDictProxy | None                                                         = None
    raw_headers: tuple | None                                                                = None
    links: MultiDictProxy | None                                                             = None
    content_type: str | None                                                                 = None
    encoding: str | None                                                                     = None
    charset: str | None | None                                                               = None
    content_disposition: str | None                                                          = None
    history: Sequence[ClientResponse|RequestsResponse|HTTPXResponse] | None                  = None
    request: RequestInfo | None                                                              = None
    elapsed: timedelta | None                                                                = None
    _is_cached: bool | None                                                                  = False
    _json: dict | None                                                                       = field(default=None, init=False)
    _text: str | None                                                                        = field(default=None, init=False)

    def __repr__(self):
        return f"<Response [{self.status} {STATUS_CODES[self.status]}]>"

    def __bool__(self):
        return self.ok

    def serialize(self):
        if self.headers is not None:
            if not isinstance(self.headers, dict):
                headers = {str(k):v for k,v in self.headers.items()}
            else:
                headers = dict(self.headers)

        if isinstance(self.version, HttpVersion):
            version = f"{self.version.major}/{self.version.minor}"
        else:
            version = self.version

        return {
            "version": version,
            "status": self.status,
            "reason": self.reason,
            "ok": self.ok,
            "elapsed": self.elapsed.total_seconds(),
            "method": self.method,
            "headers": headers,
            "request": {
                "url": str(self.request.url),
                "method": self.request.method,
                "headers": headers,
                "real_url": str(self.request.real_url)                   if hasattr(self.request, "real_url") else None,
                "cookies": dict(self.request.cookies)                    if hasattr(self.request, "cookies") else None,
            }                                                            if self.request is not None else None,
            "content": self.content.decode("utf-8")                      if self.content is not None else None,
            "cookies": dict(self.cookies)                                if self.cookies is not None else None,
            "url": str(self.url)                                         if self.url is not None else None,
            "real_url": str(self.real_url)                               if self.real_url is not None else None,
        }

    @classmethod
    def deserialize(cls, data: dict):
        data["version"] = HttpVersion(*version.split("/"))               if (version := data.get("version")) is not None else None
        data["content"] = bytes(content, "utf-8")                        if (content := data.get("content")) is not None else None
        data["url"] = URL(url)                                           if (url := data.get("url")) is not None else None
        data["real_url"] = URL(real_url)                                 if (real_url := data.get("real_url")) is not None else None
        data["cookies"] = SimpleCookie(cookies)                          if (cookies := data.get("cookies")) is not None else None
        data["headers"] = CIMultiDictProxy(CIMultiDict(headers))         if (headers := data.get("headers")) is not None else None
        data["raw_headers"] = tuple(raw_headers)                         if (raw_headers := data.get("raw_headers")) is not None else None
        data["request"] = Request(**request)                             if (request := data.get("request")) is not None else None
        data["elapsed"] = timedelta(seconds=data["elapsed"])
        data["_is_cached"] = True
        return cls(**data)

    @property
    def text(self):
        if self._text is not None:
            return self._text
        object.__setattr__(self, "_text", self.content.decode(self.charset or "utf-8"))
        return self._text

    @property
    def json(self):
        if self._json is not None:
            return self._json
        try:
            object.__setattr__(self, "_json", loads(self.content))
            return self._json
        except:
            return {}

    @property
    def request_info(self):
        return self.request

    @property
    def status_code(self):
        return self.status

    @property
    def http_version(self):
        return self.version

    @property
    def reason_phrase(self):
        return self.reason

    @property
    def is_cached(self):
        return self._is_cached

    def __set(self, name, value):
        object.__setattr__(self, name, value)

    def set_callbacks(self, results: tuple):
        self.__set("callbacks", results)

    def set_cache(self, value: bool):
        self.__set("_is_cached", value)


@dataclass(slots=True)
class CacheData:
    """
    Represents cached data with response and last update timestamp.
    """
    response: Response = field(repr=False)
    expiration: float | int