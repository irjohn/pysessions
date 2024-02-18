from enum import Enum

class RatelimitParams(Enum):
    SLIDINGWINDOW = {"window", "limit"}
    FIXEDWINDOW = {"window", "limit"}
    TOKENBUCKET = {"capacity", "fill_rate"}
    LEAKYBUCKET = {"capacity", "leak_rate"}
    GCRA = {"period", "limit"}
    ALL = {"limit", "window", "capacity", "fill_rate", "leak_rate", "period"}


class Timeouts(Enum):
    HTTPX = {"timeout", "read_timeout", "write_timeout", "connect_timeout", "pool_timeout"}
    AIOHTTP = {"timeout", "read_timeout", "write_timeout", "connect_timeout", "pool_timeout", "sock_connect", "sock_read"}


class Alias(Enum):
    SLIDINGWINDOW = {"slidingwindow", "SlidingWindow", "sliding_window", "sliding-window", "slidingwindowratelimit", "sliding-windowratelimit", "sliding_windowratelimit", "slidingwindowratelimiter", "sliding-windowratelimiter", "sliding_windowratelimiter", "slidingwindowratelimiting", "sliding-windowratelimiting", "sliding_windowratelimiting", "slidingwindowratelimitter", "sliding-windowratelimitter", "sliding_windowratelimitter", "slidingwindowratelimiters", "sliding-windowratelimiters", "sliding_windowratelimiters", "slidingwindowratelimitting", "sliding-windowratelimitting", "sliding_windowratelimitting"}

    FIXEDWINDOW = {"fixedwindow", "FixedWindow", "fixed_window", "fixed-window", "fixedwindowratelimit", "fixed-windowratelimit", "fixed_windowratelimit", "fixedwindowratelimiter", "fixed-windowratelimiter", "fixed_windowratelimiter", "fixedwindowratelimiting", "fixed-windowratelimiting", "fixed_windowratelimiting", "fixedwindowratelimitter", "fixed-windowratelimitter", "fixed_windowratelimitter", "fixedwindowratelimiters", "fixed-windowratelimiters", "fixed_windowratelimiters", "fixedwindowratelimitting", "fixed-windowratelimitting", "fixed_windowratelimitting"}

    TOKENBUCKET = {"tokenbucket", "TokenBucket", "token_bucket", "token-bucket", "tokenbucketratelimit", "token-bucketratelimit", "token_bucketratelimit", "tokenbucketratelimiter", "token-bucketratelimiter", "token_bucketratelimiter", "tokenbucketratelimiting", "token-bucketratelimiting", "token_bucketratelimiting", "tokenbucketratelimitter", "token-bucketratelimitter", "token_bucketratelimitter", "tokenbucketratelimiters", "token-bucketratelimiters", "token_bucketratelimiters", "tokenbucketratelimitting", "token-bucketratelimitting", "token_bucketratelimitting"}

    LEAKYBUCKET = {"leakybucket", "LeakyBucket", "leaky_bucket", "leaky-bucket", "leakybucketratelimit", "leaky-bucketratelimit", "leaky_bucketratelimit", "leakybucketratelimiter", "leaky-bucketratelimiter", "leaky_bucketratelimiter", "leakybucketratelimiting", "leaky-bucketratelimiting", "leaky_bucketratelimiting", "leakybucketratelimitter", "leaky-bucketratelimitter", "leaky_bucketratelimitter", "leakybucketratelimiters", "leaky-bucketratelimiters", "leaky_bucketratelimiters", "leakybucketratelimitting", "leaky-bucketratelimitting", "leaky_bucketratelimitting"}

    GCRA = {"gcra", "GCRA", "gcra", "Gcra", "gcraratelimit", "gcra-ratelimit", "gcra_ratelimit", "gcraratelimiter", "gcra-ratelimiter", "gcra_ratelimiter", "gcraratelimiting", "gcra-ratelimiting", "gcra_ratelimiting", "gcraratelimitter", "gcra-ratelimitter", "gcra_ratelimitter", "gcraratelimiters", "gcra-ratelimiters", "gcra_ratelimiters", "gcraratelimitting", "gcra-ratelimitting", "gcra_ratelimitting"}

    RATELIMIT_TYPE = {"type", "ratelimit", "ratelimiter", "ratelimit_type", "ratelimittype", "limiter", "limitertype", "limiter_type", "ratelimiter_type", "rate_limit", "rate-limit", "rate_limiter", "rate-limiter", "ratelimiting", "rate_limiting", "rate-limiting", "ratelimitter", "rate_limitter", "rate-limitter", "ratelimiters", "rate_limiters", "rate-limiters", "ratelimitting", "rate_limitting", "rate-limitting", "ratelimitter", "rate_limitter", "rate-limitter", "ratelimiters", "rate_limiters", "rate-limiters", "ratelimitting", "rate_limitting", "rate-limitting"}

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