from pathlib import Path
from datetime import timedelta as timedelta
from dataclasses import dataclass, field, make_dataclass, fields, MISSING
from typing import  List
from datetime import timedelta

from .utils import get_valid_kwargs


def _validate_port(port):
    if port is None:
        return
    try:
        port = int(port)
        assert 0 <= port <= 65535, "Port must be an integer or string between 0 and 65535."
    except:
        raise ValueError("Port must be an integer or string between 0 and 65535.")


@dataclass(frozen=True, eq=False)
class BackendOptions:
    """
    Represents the options for a backend connection.

    Attributes:
        username (str | None): The username for the backend connection.
        password (str | None): The password for the backend connection.
        host (str | None): The host address for the backend connection.
        port (str | int | None): The port number for the backend connection.
        db (str | Path | None): The database name or path for the backend connection.
    """

    username: str | None                                    = None
    password: str | None                                    = None
    host: str | None                                        = None
    port: str | int | None                                  = None
    db: str | Path | None                                  = None

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
    dbfilename: str | Path | None                          = None
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
    db: str | Path | None                                  = "http_cache.db"

    def __post_init__(self):
        super().__post_init__()


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
    check_frequency: float | int | timedelta               = 15

    def __post_init__(self):
        if isinstance(self.check_frequency, timedelta):
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

    cache_timeout: float | int | timedelta                 = 3600

    def __post_init__(self):
        """
        Post-initialization method that handles cache_timeout value.
        If cache_timeout is a timedelta object, it is converted to seconds.
        If cache_timeout is a negative number, it is overridden to 0.
        """
        if isinstance(self.cache_timeout, timedelta):
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


@dataclass(frozen=True, kw_only=True, eq=False)
class RatelimitOptions(MixinOptions):
    """
    Represents the options for rate limiting.

    Args:
        per_host (bool): Whether to apply rate limiting per host. Defaults to False.
        per_endpoint (bool): Whether to apply rate limiting per endpoint. Defaults to True.
        sleep_duration (float | int): The duration to sleep when rate limiting is triggered. Defaults to 0.25.
        raise_errors (bool): Whether to raise errors when rate limiting is triggered. Defaults to False.
    """
    backend: str                                          = "memory"
    key: str                                              = "Session"
    per_host: bool                                        = False
    per_endpoint: bool                                    = True
    sleep_duration: float | int                           = 0.25
    raise_errors: bool                                    = False

    def __post_init__(self):
        super().__post_init__()

    @classmethod
    def from_backend(
        cls,
        backend: str,
        **kwargs
    ):
        """
        Creates a RatelimitOptions instance based on the specified backend.

        Args:
            backend (str | None): The backend to use for rate limiting. Can be "memory", "sqlite", or "redis".
            **kwargs: Additional keyword arguments to pass to the RatelimitOptions constructor.

        Returns:
            RatelimitOptions: The created RatelimitOptions instance.
        """

        kwargs["backend"] = backend

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
                eq=False,
                kw_only=True,
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
                eq=False,
                kw_only=True,
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
                eq=False,
                kw_only=True,
            )

        kwargs = get_valid_kwargs(dc.__init__, kwargs)
        return dc(**kwargs)


@dataclass(frozen=True, kw_only=True, eq=False)
class CacheOptions(MixinOptions):
    """
    Represents options for caching.

    Attributes:
        compression (bool): Flag indicating whether compression is enabled.
    """

    backend: str                                        = "memory"
    key: str                                            = "Session"
    compression: bool                                   = True

    def __post_init__(self):
        super().__post_init__()

    @classmethod
    def from_backend(
        cls,
        backend: str,
        **kwargs
    ):
        """
        Creates a CacheOptions instance based on the specified backend.

        Args:
            backend (str | None): The backend to use for caching.
            **kwargs: Additional keyword arguments.

        Returns:
            CacheOptions: The created CacheOptions instance.
        """

        kwargs["backend"] = backend

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
                eq=False,
                kw_only=True,
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
                eq=False,
                kw_only=True,
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
                eq=False,
                kw_only=True,
            )

        kwargs = get_valid_kwargs(dc.__init__, kwargs)
        return dc(**kwargs)