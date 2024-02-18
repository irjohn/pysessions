__all__ = "RedisOptions", "SQLiteOptions", "MemoryOptions"

from datetime import timedelta
from dataclasses import dataclass, field
from typing import Callable
from pathlib import Path

from redis import ConnectionPool as _RedisConnectionPool
from redis.retry import Retry as RedisRetry

from ..utils import get_valid_kwargs

@dataclass(slots=True)
class BaseOptions:
    _attrs: set[str]                                    = None

    def __post_init__(self):
        self._attrs = set(key for key in self.__slots__ if not key.startswith("_"))

    def __iter__(self):
        for key in self._attrs:
            yield key, getattr(self, key)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def keys(self):
        return self._attrs

    def add(self, key, value):
        setattr(self, key, value)
        self._attrs.add(key)

    def update(self, iterable):
        for key, value in iterable:
            setattr(self, key, value)
        self._attrs.update(iterable)

    def discard(self, *keys):
        for key in keys:
            self._attrs.discard(key)


@dataclass(slots=True)
class RedisServerOptions(BaseOptions):
    ALLOWED_MEMORY_POLICIES = {"volatile-lru", "allkeys-lru", "volatile-lfu", "allkeys-lfu", "volatile-random", "allkeys-random", "volatile-ttl", "noeviction"}
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

    save:             list[str] | str                       = field(default_factory=lambda: ["900 1", "300 100", "60 200", "15 1000"])
    maxmemory:        str | int                             = "0"
    maxmemory_policy: str                                   = "noeviction"

    def __post_init__(self):
        BaseOptions.__post_init__(self)

        if isinstance(self.save, list):
            for i, value in enumerate(self.save):
                if isinstance(value, int):
                    self.save[i] = str(value)
                else:
                    assert isinstance(value, str), "Save must be a list of strings or string"
        else:
            assert isinstance(self.save, str), "Save must be a list of strings or string"

        assert isinstance(self.maxmemory, (int, str)), "Max memory must be an int or string in the format 'xxx Kb|Mb|Gb'"
        assert isinstance(self.maxmemory_policy, str) and self.maxmemory_policy in self.ALLOWED_MEMORY_POLICIES, f"maxmemory-policy must be one of: {self.ALLOWED_MEMORY_POLICIES}"


@dataclass(slots=True)
class RedisOptions(RedisServerOptions):
    host:                      str | None                        = None
    port:                      int | str | None                  = None
    unix_socket_path:          Path | str | None                 = None
    db:                        int                               = 0
    password:                  str | None                        = None
    socket_timeout:            int | float | None                = None
    socket_connect_timeout:    int | float | None                = None
    socket_keepalive:          int | float | None                = None
    socket_keepalive_options:  dict | None                       = None
    connection_pool:          _RedisConnectionPool | None        = None
    encoding:                  str                               = "utf-8"
    encoding_errors:           str                               = "strict"
    charset:                   str | None                        = None
    errors:                    str | None                        = None
    decode_responses:          bool                              = False
    retry_on_timeout:          bool                              = False
    retry_on_error:            list[Exception] | None            = None
    ssl:                       bool                              = False
    ssl_keyfile:               Path | str | None                 = None
    ssl_certfile:              Path | str | None                 = None
    ssl_cert_reqs:             str                               = "required"
    ssl_ca_certs:              Path | str | None                 = None
    ssl_ca_path:               Path | str | None                 = None
    ssl_ca_data:               Path | str | None                 = None
    ssl_check_hostname:        bool                              = False
    ssl_password:              str | None                        = None
    ssl_validate_ocsp:         bool                              = False
    ssl_validate_ocsp_stapled: bool                              = False
    ssl_ocsp_context:          object | None                     = None
    ssl_ocsp_expected_cert:    object | None                     = None
    max_connections:           int | None                        = None
    single_connection_client:  bool                              = False
    health_check_interval:     int | float                       = 0
    client_name:               str | None                        = None
    lib_name:                  str                               = "redis-py"
    lib_version:               str                               = "99.99.99"
    username:                  str | None                        = None
    retry:                     RedisRetry | None                 = None
    redis_connect_func:        Callable | None                   = None
    credential_provider:       Callable | object | None          = None
    protocol:                  int                               = 3
    serverconfig:              dict | RedisServerOptions         = None
    dbfilename:                Path | str | None                 = None

    def __hash__(self):
        return hash(
            (self.host, self.port, self.unix_socket_path, self.db, self.password, self.username, self.dbfilename, self.maxmemory, self.maxmemory_policy)
        )

    def __post_init__(self):
        RedisServerOptions.__post_init__(self)
        self._make_serverconfig()


        if self.dbfilename is None:
            # Discard unused redislite options
            self.discard("dbfilename")

        if all((
            self.host is None,
            self.port is None,
            self.unix_socket_path is None,
        )):
            # Creating a new redislite server
            self.discard("host")
            self.discard("port")
            return

        if self.host or self.port:
            # Connecting to an existing redis server
            self.discard("unix_socket_path")
            self.discard("serverconfig")
            self.discard("dbfilename")
            self.port = int(self.port) if self.port else 6379
            return

        if self.unix_socket_path:
            path = Path(self.unix_socket_path)
            if path.exists():
                # Connecting to an existing redis server
                self.discard("dbfilename")
                self.discard("serverconfig")
                self.add("host", None)
                self.add("port", None)
            else:
                # Creating a new redislite server
                self.discard("host")
                self.discard("port")


    def _make_serverconfig(self):
        self.serverconfig = {
            "save": self.save,
            "maxmemory": self.maxmemory,
            "maxmemory-policy": self.maxmemory_policy,
        }
        self.discard("save", "maxmemory", "maxmemory_policy")


@dataclass(slots=True)
class SQLiteOptions(BaseOptions):
    db_name:         str | Path                        = "http_cache.db"
    max_connections: int | None                        = None
    idle_timeout:    int | float | None                = None

    def __hash__(self):
        return hash(self.db_name)

    def __post_init__(self):
        BaseOptions.__post_init__(self)

        if self.max_connections is None:
            self.add("max_connections", 5)

        if self.idle_timeout is None:
            self.add("idle_timeout", 0.5)


@dataclass(slots=True, kw_only=True)
class MemoryOptions:
    """
    Represents the memory options for a session.

    Attributes:
        check_frequency (float | int | timedelta): The frequency at which memory checks are performed.
            If a timedelta object is provided, it will be converted to seconds.
            If an integer or float is provided, it will be used directly as the check frequency.
            Default value is 15.
    """
    key: str | None
    default: Callable
    cache_timeout: float | int | timedelta                 = 300
    check_frequency: float | int | timedelta               = 15

    def __post_init__(self):
        if isinstance(self.check_frequency, timedelta):
            self.check_frequency = self.check_frequency.total_seconds()
        assert self.check_frequency >= 0, "Check frequency must be greater than or equal to 0"

        if isinstance(self.cache_timeout, timedelta):
            self.cache_timeout = self.cache_timeout.total_seconds()
        assert self.cache_timeout >= 0, "Cache timeout must be greater than or equal to 0"

class BackendOptions:
    @classmethod
    def from_backend(
        cls,
        backend,
        **options
    ) -> SQLiteOptions | RedisOptions | MemoryOptions:
        if backend == "sqlite":
            optclass = SQLiteOptions
        elif backend == "redis":
            optclass = RedisOptions
        elif backend == "memory":
            optclass = MemoryOptions
        else:
            raise ValueError(f"Invalid backend: {backend}")

        options = get_valid_kwargs(optclass.__init__, options)
        return optclass(**options)