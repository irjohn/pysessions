import time as _time
from enum import Enum
from pathlib import Path as _Path
from datetime import timedelta as _timedelta
from dataclasses import dataclass, field, make_dataclass, fields, MISSING
from typing import Sequence, List
from collections import defaultdict as _defaultdict
from datetime import timedelta as _timedelta

from orjson import loads as _jsonload
from yarl import URL
from aiohttp.connector import Connection
from http.cookies import SimpleCookie
from multidict import CIMultiDictProxy, MultiDictProxy, CIMultiDict
from requests import Response as _RequestsResponse
from httpx import Response as _HttpxResponse
from aiohttp import (
    RequestInfo,
    ClientResponse,
    HttpVersion,
)

from .vars import STATUS_CODES
from .utils import get_valid_kwargs


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

    url: str
    method: str
    headers: dict | CIMultiDictProxy | None = None
    real_url: str | URL | None = None
    cookies: SimpleCookie | None = None

    def __post_init__(self):
        self.__set("url", URL(self.url))
        self.__set("real_url", URL(self.real_url) if self.real_url is not None else None)
        self.__set("cookies", SimpleCookie(self.cookies) if self.cookies is not None else None)
        self.__set("headers", CIMultiDictProxy(CIMultiDict(self.headers))) if self.headers is not None else None

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
        history (Sequence[ClientResponse|_RequestsResponse|_HttpxResponse] | None): History of the response.
        request (RequestInfo | None): Information about the request.
        elapsed (_timedelta | None): Time elapsed for the request.
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
    history: Sequence[ClientResponse|_RequestsResponse|_HttpxResponse] | None                = None
    request: RequestInfo | None                                                              = None
    elapsed: _timedelta | None                                                               = None
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
        data["elapsed"] = _timedelta(seconds=data["elapsed"])
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
            object.__setattr__(self, "_json", _jsonload(self.content))
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

    def __set(self, name, value):
        object.__setattr__(self, name, value)

    def set_callbacks(self, results: tuple):
        self.__set("callbacks", results)


def _validate_port(port):
    if port is None:
        return
    try:
        port = int(port)
        assert 0 <= port <= 65535, "Port must be an integer or string between 0 and 65535."
    except:
        raise ValueError("Port must be an integer or string between 0 and 65535.")


@dataclass(slots=True)
class CacheData:
    """
    Represents cached data with response and last update timestamp.
    """
    response: object
    last_update: float | int


@dataclass(frozen=True, eq=False)
class BackendOptions:
    """
    Represents the options for a backend connection.

    Attributes:
        username (str | None): The username for the backend connection.
        password (str | None): The password for the backend connection.
        host (str | None): The host address for the backend connection.
        port (str | int | None): The port number for the backend connection.
        db (str | _Path | None): The database name or path for the backend connection.
    """

    username: str | None                                    = None
    password: str | None                                    = None
    host: str | None                                        = None
    port: str | int | None                                  = None
    db: str | _Path | None                                  = None

    def __post_init__(self):
        _validate_port(self.port)


@dataclass(frozen=True, eq=False)
class RedisServerOptions(BackendOptions):
    """
    Represents the options for a Redis server.

    Attributes:
        save (List[str] | str): The save options for the Redis server.
        dbfilename (str | Path | None): The filename of the Redis database.
        maxmemory (str | int): The maximum memory limit for the Redis server.
        maxmemory_policy (str): The eviction policy for the Redis server.
        decode_responses (bool): Whether to decode responses from Redis as strings.
        protocol (int): The protocol version to use for Redis communication.
    """

    save: List[str] | str                                   = field(default_factory=lambda: ["900 1", "300 100", "60 200", "15 1000"])
    dbfilename: str | _Path | None                          = None
    maxmemory: str | int                                    = "0"
    maxmemory_policy: str                                   = "noeviction"
    decode_responses: bool                                  = False
    protocol: int                                           = 3

    def __post_init__(self):
        super().__post_init__()

    @staticmethod
    def _redis_bool(value):
        if value in {"true" "True", True, "yes", "Yes"}:
            return "yes"
        elif value in {"false", "False", False, "no", "No"}:
            return "no"

    def redis_server_config(self):
        """
        Returns the Redis server configuration options.

        Returns:
            dict: The Redis server configuration options.
        """
        options = {}
        if self.host is not None:
            options["host"] = self.host
            options["port"] = self.port or 6379
            if self.username is not None:
                options["username"] = self.username
            if self.password is not None:
                options["password"] = self.password
            return options

        options["serverconfig"] = {}
        if self.dbfilename is not None:
            options["dbfilename"] = str(self.dbfilename)
        elif self.db is not None:
            options["dbfilename"] = str(self.db)

        if (isinstance(self.maxmemory, int) and self.maxmemory > 0) or (isinstance(self.maxmemory, str) and self.maxmemory[0] != "0"):
            options["serverconfig"]["maxmemory"] = str(self.maxmemory).replace(" ", "")

        maxmemory_policy = self.maxmemory_policy.lower()
        if maxmemory_policy != "noeviction":
            assert options.get("maxmemory") is not None, "maxmemory must be set if maxmemory-policy is not noeviction"

        assert self.maxmemory_policy in {"volatile-lru", "allkeys-lru", "volatile-lfu", "allkeys-lfu", "volatile-random", "allkeys-random", "volatile-ttl", "noeviction"}, "maxmemory-policy must be one of: volatile-lru, allkeys-lru, volatile-lfu, allkeys-lfu, volatile-random, allkeys-random, volatile-ttl, noeviction"

        options["serverconfig"]["maxmemory-policy"] = maxmemory_policy
        options["serverconfig"]["save"] = self.save
        options["decode_responses"] = self.decode_responses
        options["protocol"] = self.protocol
        return options

@dataclass(frozen=True, eq=False)
class SQLiteOptions(BackendOptions):
    """
    Represents the options for SQLite backend.

    Attributes:
        database (str | None): The path to the SQLite database file.
        db (str | Path | None): The default database name if `database` is not provided.
    """

    database: str | None                                    = None
    db: str | _Path | None                                  = "http_cache.db"

    def __post_init__(self):
        super().__post_init__()

    def mysql_server_config(self):
        db = self.database or self.db
        return {
            "user": self.username or "",
            "password": self.password or "",
            "host": self.host,
            "port": self.port or 3306,
            "database": db,
        }

@dataclass(frozen=True, eq=False)
class MemoryOptions:
    """
    Represents the memory options for a session.

    Attributes:
        check_frequency (float | int | timedelta): The frequency at which memory checks are performed.
            If a timedelta object is provided, it will be converted to seconds.
            If an integer or float is provided, it will be used directly as the check frequency.
            Default value is 15.
    """
    check_frequency: float | int | _timedelta               = 15

    def __post_init__(self):
        if isinstance(self.check_frequency, _timedelta):
            self.override("check_frequency", self.check_frequency.total_seconds())
        elif isinstance(self.check_frequency, (int, float)):
            if self.check_frequency < 0:
                self.override("check_frequency", 0)
        super().__post_init__()

@dataclass(frozen=True, eq=False)
class MixinOptions:
    """
    MixinOptions class represents options for a mixin.
    """

    cache_timeout: float | int | _timedelta                 = 3600

    def __post_init__(self):
        """
        Post-initialization method that handles cache_timeout value.
        If cache_timeout is a timedelta object, it is converted to seconds.
        If cache_timeout is a negative number, it is overridden to 0.
        """
        if isinstance(self.cache_timeout, _timedelta):
            self.override("cache_timeout", self.cache_timeout.total_seconds())
        elif isinstance(self.cache_timeout, (int, float)):
            if self.cache_timeout < 0:
                self.override("cache_timeout", 0)

    def override(self, key, value):
        """
        Overrides the value of a given key in the object.
        """
        object.__setattr__(self, key, value)

    def _delete(self, key):
        """
        Deletes the attribute with the given key from the object.
        """
        object.__delattr__(self, key)

@dataclass(frozen=True, eq=False)
class RatelimitOptions(MixinOptions):
    """
    Represents the options for rate limiting.

    Args:
        per_host (bool): Whether to apply rate limiting per host. Defaults to False.
        per_endpoint (bool): Whether to apply rate limiting per endpoint. Defaults to True.
        sleep_duration (float | int): The duration to sleep when rate limiting is triggered. Defaults to 0.25.
        raise_errors (bool): Whether to raise errors when rate limiting is triggered. Defaults to False.
    """

    per_host: bool                                        = False
    per_endpoint: bool                                    = True
    sleep_duration: float | int                           = 0.25
    raise_errors: bool                                    = False

    def __post_init__(self):
        super().__post_init__()

    @classmethod
    def from_backend(cls, backend: str | None, **kwargs):
        """
        Creates a RatelimitOptions instance based on the specified backend.

        Args:
            backend (str | None): The backend to use for rate limiting. Can be "memory", "sqlite", or "redis".
            **kwargs: Additional keyword arguments to pass to the RatelimitOptions constructor.

        Returns:
            RatelimitOptions: The created RatelimitOptions instance.
        """

        if backend == "memory":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(RatelimitOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(MemoryOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="RatelimitOptions",
                fields=fields_,
                bases=(RatelimitOptions, MemoryOptions),
                frozen=True,
                eq=False
            )

        elif backend == "sqlite":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(RatelimitOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(SQLiteOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="RatelimitOptions",
                fields=fields_,
                bases=(RatelimitOptions, SQLiteOptions),
                frozen=True,
                eq=False
            )

        elif backend == "redis":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(RedisServerOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(RatelimitOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="RatelimitOptions",
                fields=fields_,
                bases=(RatelimitOptions, RedisServerOptions),
                frozen=True,
                eq=False
            )

        kwargs = get_valid_kwargs(dc.__init__, kwargs)
        return dc(**kwargs)


@dataclass(frozen=True, eq=False)
class CacheOptions(MixinOptions):
    """
    Represents options for caching.

    Attributes:
        compression (bool): Flag indicating whether compression is enabled.
    """

    compression: bool                                   = True

    def __post_init__(self):
        super().__post_init__()

    @classmethod
    def from_backend(cls, backend: str | None, **kwargs):
        """
        Creates a CacheOptions instance based on the specified backend.

        Args:
            backend (str | None): The backend to use for caching.
            **kwargs: Additional keyword arguments.

        Returns:
            CacheOptions: The created CacheOptions instance.
        """
        if backend == "memory":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(CacheOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(MemoryOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="CacheOptions",
                fields=fields_,
                bases=(CacheOptions, MemoryOptions),
                frozen=True,
                eq=False
            )

        elif backend == "sqlite":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(CacheOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(SQLiteOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="CacheOptions",
                fields=fields_,
                bases=(CacheOptions, SQLiteOptions),
                frozen=True,
                eq=False
            )
        elif backend == "redis":
            fields_ = (
                *((field_.name, field_.type, field_) for field_ in fields(RedisServerOptions)),
                *((field_.name, field_.type, field_) for field_ in fields(CacheOptions)),
            )
            fields_ = sorted(set(fields_), key=lambda x: x[2].default is not MISSING)
            dc = make_dataclass(
                cls_name="CacheOptions",
                fields=fields_,
                bases=(CacheOptions, RedisServerOptions),
                frozen=True,
                eq=False
            )

        kwargs = get_valid_kwargs(dc.__init__, kwargs)
        return dc(**kwargs)


class InMemoryCacheMixin:
    """
    A mixin class that provides in-memory caching functionality.

    This mixin class implements common caching operations such as clearing the cache,
    deleting items from the cache, checking if an item is in the cache, retrieving items
    from the cache, and providing a string representation of the cache.

    Attributes:
        _cache (dict): The underlying dictionary used for storing the cached items.
    """

    def clear(self):
        """Clears the cache by removing all items."""
        self._cache.clear()

    def __delitem__(self, key):
        """Deletes an item from the cache using the specified key."""
        del self._cache[key]

    def __contains__(self, key):
        """Checks if an item with the specified key is in the cache."""
        return key in self._cache

    def pop(self, key, default=None):
        """
        Removes and returns the item with the specified key from the cache.

        If the key is not found in the cache, the default value is returned.

        Args:
            key: The key of the item to be removed.
            default: The value to be returned if the key is not found (default: None).

        Returns:
            The value of the removed item, or the default value if the key is not found.
        """
        return self._cache.pop(key, default)

    def items(self):
        """
        Returns a tuple of (key, value) pairs representing all items in the cache.

        Returns:
            A tuple of (key, value) pairs.
        """
        return tuple((key, data.response) for key, data in self._cache.items())

    def keys(self):
        """
        Returns a tuple of all keys in the cache.

        Returns:
            A tuple of keys.
        """
        return self._cache.keys()

    def values(self):
        """
        Returns a tuple of all values in the cache.

        Returns:
            A tuple of values.
        """
        return tuple(value.response for value in self._cache.values())

    def __repr__(self):
        """Returns a string representation of the cache."""
        return repr(dict(self._cache))

class CacheInMemoryCache(InMemoryCacheMixin):
    def __init__(
        self,
        options: CacheOptions,
    ):
        """
        Initializes an instance of CacheInMemoryCache.

        Args:
            options (CacheOptions): The cache options.

        """
        self._cache_timeout = options.cache_timeout
        self._cache = _defaultdict(lambda: CacheData(None, _time.time()))
        self._check_frequency = options.check_frequency
        self._last_check = _time.time()


    def __getitem__(self, key):
        """
        Retrieves the value associated with the given key from the cache.

        Args:
            key: The key to retrieve the value for.

        Returns:
            The value associated with the key.

        """
        now = _time.time()
        self._cache[key].last_update = now

        if self._cache_timeout > 0 and now - self._last_check > self._check_frequency:
            self._cache = {key: data for key, data in self._cache.items() if now - data.last_update <= self._cache_timeout}
            self._last_check = now

        return self._cache[key].response


    def __setitem__(self, key, value):
        """
        Sets the value associated with the given key in the cache.

        Args:
            key: The key to set the value for.
            value: The value to be set.

        """
        self._cache[key].last_update = _time.time()
        self._cache[key].response = value



class RatelimitInMemoryCache(InMemoryCacheMixin):
    """
    A class representing an in-memory cache with rate-limiting capabilities.

    Args:
        options (RatelimitOptions): The rate-limiting options.
        default (Any, optional): The default value for cache entries. Defaults to None.
    """

    def __init__(
        self,
        options: RatelimitOptions,
        default=None,
    ):
        self._cache = _defaultdict(default)
        self._cache_timeout = options.cache_timeout
        self._check_frequency = options.check_frequency
        self._last_check = _time.time()


    def __getitem__(self, key):
        now = _time.time()

        if self._cache_timeout > 0 and now - self._last_check > self._check_frequency:
            self._cache = {key: data for key, data in self._cache.items() if now - data.last_update <= self._cache_timeout}
            self._last_check = now

        return self._cache[key]

    def __setitem__(self, key, value):
        self._cache[key] = value

class Timeouts(Enum):
    HTTPX = {"timeout", "read_timeout", "write_timeout", "connect_timeout", "pool_timeout"}
    AIOHTTP = {"timeout", "read_timeout", "write_timeout", "connect_timeout", "pool_timeout", "sock_connect", "sock_read"}


class Alias(Enum):
    SLIDINGWINDOW = {"slidingwindow", "SlidingWindow", "sliding_window", "sliding-window", "slidingwindowratelimit", "sliding-windowratelimit", "sliding_windowratelimit", "slidingwindowratelimiter", "sliding-windowratelimiter", "sliding_windowratelimiter", "slidingwindowratelimiting", "sliding-windowratelimiting", "sliding_windowratelimiting", "slidingwindowratelimitter", "sliding-windowratelimitter", "sliding_windowratelimitter", "slidingwindowratelimiters", "sliding-windowratelimiters", "sliding_windowratelimiters", "slidingwindowratelimitting", "sliding-windowratelimitting", "sliding_windowratelimitting"}

    FIXEDWINDOW = {"fixedwindow", "FixedWindow", "fixed_window", "fixed-window", "fixedwindowratelimit", "fixed-windowratelimit", "fixed_windowratelimit", "fixedwindowratelimiter", "fixed-windowratelimiter", "fixed_windowratelimiter", "fixedwindowratelimiting", "fixed-windowratelimiting", "fixed_windowratelimiting", "fixedwindowratelimitter", "fixed-windowratelimitter", "fixed_windowratelimitter", "fixedwindowratelimiters", "fixed-windowratelimiters", "fixed_windowratelimiters", "fixedwindowratelimitting", "fixed-windowratelimitting", "fixed_windowratelimitting"}

    TOKENBUCKET = {"tokenbucket", "TokenBucket", "token_bucket", "token-bucket", "tokenbucketratelimit", "token-bucketratelimit", "token_bucketratelimit", "tokenbucketratelimiter", "token-bucketratelimiter", "token_bucketratelimiter", "tokenbucketratelimiting", "token-bucketratelimiting", "token_bucketratelimiting", "tokenbucketratelimitter", "token-bucketratelimitter", "token_bucketratelimitter", "tokenbucketratelimiters", "token-bucketratelimiters", "token_bucketratelimiters", "tokenbucketratelimitting", "token-bucketratelimitting", "token_bucketratelimitting"}

    LEAKYBUCKET = {"leakybucket", "LeakyBucket", "leaky_bucket", "leaky-bucket", "leakybucketratelimit", "leaky-bucketratelimit", "leaky_bucketratelimit", "leakybucketratelimiter", "leaky-bucketratelimiter", "leaky_bucketratelimiter", "leakybucketratelimiting", "leaky-bucketratelimiting", "leaky_bucketratelimiting", "leakybucketratelimitter", "leaky-bucketratelimitter", "leaky_bucketratelimitter", "leakybucketratelimiters", "leaky-bucketratelimiters", "leaky_bucketratelimiters", "leakybucketratelimitting", "leaky-bucketratelimitting", "leaky_bucketratelimitting"}

    GCRA = {"gcra", "GCRA", "gcra", "Gcra", "gcraratelimit", "gcra-ratelimit", "gcra_ratelimit", "gcraratelimiter", "gcra-ratelimiter", "gcra_ratelimiter", "gcraratelimiting", "gcra-ratelimiting", "gcra_ratelimiting", "gcraratelimitter", "gcra-ratelimitter", "gcra_ratelimitter", "gcraratelimiters", "gcra-ratelimiters", "gcra_ratelimiters", "gcraratelimitting", "gcra-ratelimitting", "gcra_ratelimitting"}

    RATELIMIT_TYPE = {"type", "ratelimit", "ratelimiter", "ratelimit_type", "limiter", "limitertype", "limiter_type", "ratelimiter_type", "rate_limit", "rate-limit", "rate_limiter", "rate-limiter", "ratelimiting", "rate_limiting", "rate-limiting", "ratelimitter", "rate_limitter", "rate-limitter", "ratelimiters", "rate_limiters", "rate-limiters", "ratelimitting", "rate_limitting", "rate-limitting", "ratelimitter", "rate_limitter", "rate-limitter", "ratelimiters", "rate_limiters", "rate-limiters", "ratelimitting", "rate_limitting", "rate-limitting"}

    MEMORY = {"memory", "mem", "py", "python", "pure", "inmemory", "in-memory", "in_memory", ":memory:", "inmemorycache", "in-memorycache", "in_memorycache", "inmemory_cache", "in-memory_cache", "in_memory_cache", "inmemorycacheobject", "in-memorycacheobject", "in_memorycacheobject", "inmemory_cacheobject", "in-memory_cacheobject", "in_memory_cacheobject"}

    REDIS = {"redis", "redis", "red", "redis_cache", "redis-cache", "rediscache", "redis_cacheobject", "redis-cacheobject", "rediscacheobject", "redis_cache_object", "redis-cache_object", "rediscache_object"}

    SQLITE = {"sqlite", "sqlite3", "sql", "sql3", "sqlite_cache", "sqlite-cache", "sqlitecache", "sqlite_cacheobject", "sqlite-cacheobject", "sqlitecacheobject", "sqlite_cache_object", "sqlite-cache_object", "sqlitecache_object"}


    @classmethod
    def validate_ratelimit_type(cls, value):
        if value in cls.SLIDINGWINDOW.value:
            return "slidingwindow"
        elif value in cls.FIXEDWINDOW.value:
            return "fixedwindow"
        elif value in cls.TOKENBUCKET.value:
            return "tokenbucket"
        elif value in cls.LEAKYBUCKET.value:
            return "leakybucket"
        elif value in cls.GCRA.value:
            return "gcra"
        else:
            raise ValueError(f"Ratelimit type {value} is not implemented.")