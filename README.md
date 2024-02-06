# Sessions Repository

This repository contains a collection of HTTP session clients. It provides optional rate limiting and caching mixins to manage your HTTP requests efficiently.

## Installation

To install the sessions repository, clone the repository to your local machine:

```bash
git clone https://github.com/irjohn/pysessions.git
```

Then, navigate into the cloned repository and install the necessary dependencies:

```bash
cd pysessions
pip install .
```

## Usage

Here's a basic example of how to use the sessions repository:

```python
from sessions import Session

# Create a new Session
client = Session()

# Make a GET request
response = client.get('https://api.example.com/data')

# Print the response
print(response.json())
```

To utilize ratelimiting and caching features, there are 2 mixin classes provided, CacheMixin and RatelimitMixin. There are 5 implementations of ratelimiting: LeakyBucket, TokenBucket, SlidingWindow, FixedWindow, GCRA with 3 backends to choose from: InMemory, Redis, or SQLite. You can create a new Session with the mixins like this:

```python
from sessions import Session, CacheMixin, RatelimitMixin

class Session(CacheMixin, RatelimitMixin, Session):
    pass

client = Session()

url = 'https://api.example.com/data'

response = client.get(url)

print(client.cache[url])
```
# Backends
Choose from: memory, redis, sql
## Memory
Manage cache in memory with pure python.
### Parameters
```
cache_timeout: float | int | timedelta                |  How long a key remains active before being evicted
default(3600)                                         |
                                                      |
check_frequency: float | int | timedelta              |  How often to check for expired keys for eviction
default(15)                                           |
```

## Redis
Spawns a temporary redis server that is closed upon program exit
### Parameters
```
# Existing Redis server                               |
                                                      |
conn:                                                 |  A redis connection object
default(None)                                         |
                                                      |
host: str                                             |  A redis server to connect to. If set, a temporary server will not be started
default(None)                                         |
                                                      |
port: int | str                                       |  The port to connect to redis server, host must be set
default(None)                                         |
                                                      |
username: str                                         |  User to authenticate with
default(None)                                         |
                                                      |
password: str                                         |  Password to authenticate with
default(None)                                         |
                                                      |
# Temporary server Usage                              |
                                                      |
cache_timeout: float | int | timedelta                |  How long a key remains active before being evicted
CacheMixin     default(3600)                          |
RatelimitMixin default(300)                           |
                                                      |
dbfilename: str | Path                                |  A filename to save the dump to, if None the database will not be saved
default(None)                                         |
                                                      |
db: str | Path                                        |  Alias for dbfilename
default(None)                                         |
                                                      |
maxmemory: str | int                                  |  Maximum memory for the temporary redis server
default(0)                                            |
                                                      |
maxmemory_policy: str                                 |  Policy for redis memory management. Must be one of: volatile-lru, allkeys-lru, volatile-lfu, allkeys-lfu,
default("noeviction")                                 |                                                      volatile-random, allkeys-random, volatile-ttl, noeviction
                                                      |
decode_responses: bool                                |  Whether redis server should decode bytes to string objects
default(False)                                        |
                                                      |
protocol: int                                         |  Redis RESP protocol version.
default(3)                                            |
```
## SQL
Use an SQL or SQLite database as cache
### Parameters
    conn: sqlite3.Connection                              |  An SQLite connection object
    default(None)                                         |
                                                          |
    cache_timeout: float | int | timedelta                |  How long a key remains active before being evicted
    default(3600)                                         |
                                                          |
    db:  str | Path                                       |  An SQLite database filepath or SQL database
    default(None)                                         |


# Mixins
```
Parameters are shared between mixins. To specify parameters for only one include a dictionary as a keyword argument

ratelimit | ratelimit_options: dict                   |  Specify parameters for RatelimitMixin as a dictionary of parameters
cache | cache_options: dict                           |  Specify parameters for CacheMixin as a dictionary of parameters
```
## RatelimitMixin
    slidingwindow                                         |  Implements a sliding window algorithm
        limit: int                                        |      Requests allowed within `window` seconds
        window: int | float                               |      Time period in seconds of how many requests are allowed through in any `window` seconds
                                                          |
    fixedwindow                                           |  Implements a fixed window algorithm where
        limit: int                                        |      Requests allowed every `window` seconds
        window: int | float                               |      Time period in seconds where only `limit` requests are allowed every `window` seconds
                                                          |
    leakybucket                                           |  The leaky bucket algorithm is a rate limiting algorithm that allows a `capacity` of requests to be processed
                                                          |  per unit of time. The `leak_rate` defines how many requests per second leak through
        capacity: int | float                             |      Requests allowed before bucket is full
        leak_rate: int | float                            |      The rate at which the bucket leaks requests per unit of time.
                                                          |
    tokenbucket                                           |  The bucket can hold at the most `capacity` tokens. If a token arrives when the bucket is full, it is discarded.
                                                          |  A token is added to the bucket every 1/fill_rate seconds
        capacity: int | float                             |      Requests allowed before bucket is empty
        fill_rate: int | float                            |      The rate at which tokens are added to the bucket per second.
                                                          |
    gcra                                                  |  GCRA (Generic Cell Rate Algorithm) is a rate limiting algorithm that allows a burst of requests up to a certain `limit`
                                                          |  within a specified time `period`
        period: int | float                               |     Time period for each cell/token (in seconds)
        limit: int                                        |     Limit on the burst size (in seconds)
                                                          |
### Usage
```python
from sessions import Session, AsyncSession, RatelimitMixin

class AsyncSession(RatelimitMixin, AsyncSession):
    pass

class Session(RatelimitMixin, Session):
    pass


```

### Parameters
```
backend: str                                          |
default("memory")                                     |
                                                      |
key: string                                           |  Key prefix per cache item e.g. Session:METHOD:URL:ratelimit
default("Session")                                    |
                                                      |
cache_timeout: int | float                            |  How long a key remains active before being evicted
default(300)                                          |
                                                      |
conn: Redis | sqlite3.Connection | pymysql.Connection |  Existing connection object to use
default(None)                                         |
                                                      |
per_host: bool                                        |  Whether to ratelimit requests to the host
default(False)                                        |
                                                      |
per_endpoint: bool                                    |  Whether to ratelimit requests to the endpoint
default(True)                                         |
                                                      |
sleep_duration: int | float                           |  Amount of time program should sleep between ratelimit checks
default(0.05)                                         |
                                                      |
raise_errors: bool                                    |  Whether to raise an error instead of delaying until request can go through
default(False)                                        |
```

## CacheMixin
### Usage
```python
from sessions import Session, CacheMixin, RatelimitMixin

class Session(CacheMixin, RatelimitMixin, Session):
    pass

client = Session()

url = 'https://api.example.com/data'

response = client.get(url)

print(client.cache[url])
```
### Parameter
```
backend: str                                          |
default("memory")                                     |
                                                      |
key: string                                           |  Key prefix per cache item e.g. Session:METHOD:URL:ratelimit
default("Session")                                    |
                                                      |
cache_timeout: int | float                            |  How long a key remains active before being evicted
default(3600)                                         |
                                                      |
conn: Redis | sqlite3.Connection | pymysql.Connection |  Existing connection object to use
default(None)                                         |
```

# Testing
As a testing convenience there is a provided Urls class that generates httpbin urls, I have tested using a local docker image but you can enter the base url as a keyword parameter
```python
import asyncio
import os
from atexit import register
from random import Random

from sessions import Session, AsyncSession, RatelimitMixin
from sessions.utils import Urls, timer, make_test, extract_args

class Session(RatelimitMixin, Session):
    pass

class AsyncSession(RatelimitMixin, AsyncSession):
    pass


rng = Random()
urls = Urls(port=8080)


# Windows
window = 1
limit = 3

# GCRA
period = 2

# Buckets
capacity = 5
fill_rate = 10
leak_rate = 5

n_tests = 25
type_name = "slidingwindow"


@timer
def test(n_tests, urls, **kwargs):
    def _test(session, url, **kwargs):
        result = session.get(url)
        return result

    if isinstance(urls, str):
        urls = (urls,) * n_tests

    with Session(**kwargs) as session:
        return tuple(_test(session, url, **kwargs) for url in urls)


@timer
async def atest(n_tests, urls, **kwargs):
    async def _atest(session, url, **kwargs):
        result = session.get(url)
        return result

    if isinstance(urls, str):
        urls = (urls,) * n_tests

    async with AsyncSession(**kwargs) as session:
        return await asyncio.gather(*[_atest(session, url, **kwargs) for url in urls])


@timer
def test_memory(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    with Session(backend="memory", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)

@timer
def test_sqlite(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    kwargs.pop("db", None)
    with Session(backend="sqlite", db="test.db", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)

@timer
def test_redis(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    with Session(backend="redis", **kwargs) as session:
        results = tuple(map(session.get, urls.RANDOM_URLS(n_tests, min, max)))
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)


@timer
async def atest_memory(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    async with AsyncSession(backend="memory", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)

@timer
async def atest_sqlite(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    kwargs.pop("db", None)
    async with AsyncSession(backend="sqlite", db="test.db", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)

@timer
async def atest_redis(n_tests=25, min=0, max=5, **kwargs):
    kwargs.pop("backend", None)
    async with AsyncSession(backend="redis", **kwargs) as session:
        results = await asyncio.gather(*[session.get(url) for url in urls.RANDOM_URLS(n_tests, min=min, max=max)])
        session.clear_cache()
    kwargs["n_tests"] = n_tests
    return extract_args(kwargs["type"], kwargs)


def run_sync_tests(n_tests=25, min=0, max=5, randomize=False, **kwargs):
    """
    Run synchronous tests for different types of algorithms.

    Args:
        n_tests (int): Number of tests to run for each algorithm (default: 25).
        min (int): Minimum value for the test inputs (default: 0).
        max (int): Maximum value for the test inputs (default: 5).
        randomize (bool): Flag indicating whether to randomize test parameters (default: False).
        **kwargs: Additional keyword arguments for the test functions.

    Returns:
        dict: A dictionary containing the test results for each algorithm.
              The keys are the algorithm types and the values are tuples of test results.
    """
    funcs = (test_memory, test_redis, test_sqlite)
    if os.path.exists("test.db"):
        os.remove("test.db")

    if "type" not in kwargs or randomize:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        executor = ThreadPoolExecutor(max_workers=5)
        results = {}

        for type in ("slidingwindow", "fixedwindow", "tokenbucket", "leakybucket", "gcra"):
            print(f"\nRunning tests for {type}...")
            if randomize:
                kwargs = make_test(type, dct=True)
                print(f"Test parameters:\n{"\n".join(f"{k}: {v}" for k, v in kwargs.items())}")
                test_results = tuple(executor.submit(func, min=min, max=max, type=type, **kwargs) for func in funcs)
            else:
                test_results = tuple(executor.submit(func, n_tests=n_tests, min=min, max=max, type=type, **kwargs) for func in funcs)
            test_results = tuple(result.result() for result in as_completed(test_results))
            results[type] = test_results
        return results
    else:
        return {kwargs["type"]: tuple(func(n_tests=n_tests, min=min, max=max, **kwargs) for func in funcs)}


async def run_async_tests(n_tests=25, min=0, max=5, randomize=False, **kwargs):
    """
    Run asynchronous tests for different types of algorithms.

    Args:
        n_tests (int): Number of tests to run (default: 25).
        min (int): Minimum value for the tests (default: 0).
        max (int): Maximum value for the tests (default: 5).
        randomize (bool): Flag to indicate whether to randomize test parameters (default: False).
        **kwargs: Additional keyword arguments for the tests.

    Returns:
        dict: A dictionary containing the test results for each algorithm type.
    """
    funcs = (atest_memory, atest_redis, atest_sqlite)
    if os.path.exists("test.db"):
        os.remove("test.db")
    if "type" not in kwargs or randomize:
        results = {}
        for type in ("slidingwindow", "fixedwindow", "tokenbucket", "leakybucket", "gcra"):
            print(f"\nRunning tests for {type}...")
            if randomize:
                kwargs = make_test(type, dct=True)
                print(f"Test parameters:\n{"\n".join(f"{k}: {v}" for k, v in kwargs.items())}")
                test_results = await asyncio.gather(*[func(min=min, max=max, **kwargs) for func in funcs])
            else:
                test_results = await asyncio.gather(*[func(n_tests=n_tests, min=min, max=max, **kwargs) for func in funcs])
            results[type] = test_results
        return results
    else:
        return {kwargs["type"]: await asyncio.gather(*[
            func(n_tests=n_tests, min=min, max=max, **kwargs) for func in funcs
        ])}

@register
def _cleanup():
    if os.path.exists("test.db"):
        os.remove("test.db")

# Example usage of the test functions
#s = run_sync_tests(n_tests, type="slidingwindow", min=0, max=100, limit=limit, period=period, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate)
#s = run_sync_tests(randomize=True)

# coro = run_async_tests(n_tests, type="slidingwindow", min=0, max=100, limit=limit, period=period, window=window, capacity=capacity, fill_rate=fill_rate, leak_rate=leak_rate)
#coro = run_async_tests(randomize=True)
#a = asyncio.run(coro)
```

## Contributing

We welcome contributions! Please see our [contributing guide](CONTRIBUTING.md) for more details.

## License

The sessions repository is released under the [MIT License](LICENSE).