# Sessions Repository

This repository contains a collection of HTTP session clients. It provides optional rate limiting and caching mixins to manage your HTTP requests efficiently.

## Installation

To install the sessions repository, you can use pip to install with:

```bash
pip install pysessions
```

Or alternatively, clone the repository to your local machine:

```bash
git clone https://github.com/irjohn/pysessions.git
```

Then, navigate into the cloned repository and install the necessary dependencies:

```bash
cd pysessions
pip install .
```

## Usage

### Here's a basic example of how to use the sessions repository:

```python
from sessions import Session

# Create a new Session
client = Session()

# Make a GET request
response = client.get('https://httpbin.org/ip')

# Print the response
print(response.json)

Output
{'origin': '45.27.245.68'}
```

### Multiple requests and callbacks are supported

```python
from sessions import Session

def callback(response):
    print(f"Response status: {response.ok}")

urls = (f"https://httpbin.org/get?id={x}" for x in range(100))
s = Session()

s.requests(urls, method="GET", callbacks=[callback])

Output
on 0: Response status: True
on 1: Response status: True
on 2: Response status: True
on 3: Response status: True
on 4: Response status: True
on 5: Response status: True
on 6: Response status: True
on 7: Response status: True
on 8: Response status: True
on 9: Response status: True
|████████████████████████████████████████| 10/10 [100%] in 0.6s (18.03/s)
```
### Callbacks can be configured to return results
```python
import random
from sessions import Session
from sessions.config import SessionConfig

SessionConfig.return_callbacks = True

def callback1(response):
    if response.ok:
        # Some work here
        return {"callback": "callback1", "status": "success"}
    return {"callback": "callback1", "status": "fail"}

def callback2(response):
    if response.ok:
        # Some work here
        return {"callback": "callback2", "status": "success"}
    return {"callback": "callback2", "status": "fail"}


urls = [
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/404",
]

choices = random.choices(urls, k=5, weights=[0.9, 0.1])
s = Session()

responses = s.requests(choices, callbacks=[callback1, callback2])
for response in responses:
    print(response.callbacks)

Output
|████████████████████████████████████████| 5/5 [100%] in 0.2s (24.77/s)
({'callback': 'callback1', 'status': 'success'}, {'callback': 'callback2', 'status': 'success'})
({'callback': 'callback1', 'status': 'success'}, {'callback': 'callback2', 'status': 'success'})
({'callback': 'callback1', 'status': 'success'}, {'callback': 'callback2', 'status': 'success'})
({'callback': 'callback1', 'status': 'success'}, {'callback': 'callback2', 'status': 'success'})
({'callback': 'callback1', 'status': 'fail'}, {'callback': 'callback2', 'status': 'fail'})
```

### To utilize ratelimiting and caching features, there are 2 mixin classes provided, CacheMixin and RatelimitMixin. There are 5 implementations of ratelimiting: LeakyBucket, TokenBucket, SlidingWindow, FixedWindow, GCRA with 3 backends to choose from: InMemory, Redis, or SQLite. You can create a new Session with the mixins like this:

```python
from sessions import Session, CacheMixin

class Session(CacheMixin, Session):
    pass

client = Session()

url = 'https://httpbin.org/get?id=5013'

response = client.get(url)
print(response.json)

print(client.cache[url])
print(client.cache[url].json)
Output
{'args': {'id': '5013'}, 'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Host': 'httpbin.org', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/116.', 'X-Amzn-Trace-Id': 'Root=1-65c64ac9-4136de573290794f5aeddc2f'}, 'origin': '45.27.245.68', 'url': 'https://httpbin.org/get?id=5013'}
<Response [200 OK]>
{'args': {'id': '5013'}, 'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Host': 'httpbin.org', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/116.', 'X-Amzn-Trace-Id': 'Root=1-65c64ac9-4136de573290794f5aeddc2f'}, 'origin': '45.27.245.68', 'url': 'https://httpbin.org/get?id=5013'}
```

# Backends

Choose from: memory, redis, sql

## Memory

Manage cache in memory with pure python.

### Parameters

- cache_timeout   
    - How long a key remains active before being evicted
    - float | int | timedelta  
    - default 3600    
                 
- check_frequency   
    - How often to check for expired keys for eviction
    - float | int | timedelta
    - default 15      

## Redis

Spawns a temporary redis server that is closed upon program exit

### Parameters

### Existing Redis Server   
                 
- conn               
    - A redis connection object
    - default None    
                 
- host   
    - A redis server to connect to. If set, a temporary server will not be started
    - str          
    - default None    
                 
- port       
    - The port to connect to redis server, host must be set
    - int | str
    - default None    
                 
- username         
    - User to authenticate with
    - str
    - default None    
                 
- password         
    - Password to authenticate with
    - str
    - default None    
                 
### Temporary Server Usage  
                 
- cache_timeout     
    - How long a key remains active before being evicted
    - float | int | timedelta 
    - CacheMixin     
        - default 3600
    - RatelimitMixin 
        - default 300
                 
- dbfilename          
    - A filename to save the dump to
    - If None the database will not be saved on exit
    - str | Path
    - default None    
                 
- db        
    - Alias for dbfilename
    - str | Path
    - default None    
                 
- maxmemory           
    - Maximum memory for the temporary redis server
    - str | int
    - default 0       
                 
- maxmemory_policy          
    - Policy for redis memory management.
    - Must be one of: volatile-lru, allkeys-lru, volatile-lfu, allkeys-lfu, volatile-random, allkeys-random, volatile-ttl, noeviction
    - str
    - default "noeviction"                                                           
                 
- decode_responses    
    - Whether redis server should decode bytes to string objects
    - bool      
    - default False   
                 
- protocol         
    - Redis RESP protocol version.
    - int
    - default 3       


## SQLite

Use an SQLite database as cache

### Parameters

- conn    
    - An SQLite connection object
    - sqlite3.Connection
    - default None    
                   
- cache_timeout   
    - How long a key remains active before being evicted
    - float | int | timedelta
    - default 3600    
                   
- db 
    - An SQLite database filepath
    - str | Path    
    - default None    


# Mixins

Parameters are shared between mixins. To specify parameters for only one include a dictionary as a keyword argument

- ratelimit_options: (dict)
    - Specify parameters for RatelimitMixin as a dictionary of parameters
- cache | cache_options: (dict)
    - Specify parameters for CacheMixin as a dictionary of parameters

# RatelimitMixin

## Parameters

- backend   
Which backend to use: memory, redis, sqlite
    - str
    - default "memory"
                 
- key   
Key prefix per cache item e.g. Session:METHOD:URL:ratelimit 
    - string    
    - default "Session"

- cache_timeout   
How long a key remains active before being evicted
    - int | float
    - default 300     
                 
- conn   
Existing connection object to use
    - Redis | sqlite3.Connection
    - default: None    

- per_host   
Whether to ratelimit requests to the host 
    - bool   
    - default False   
                 
- per_endpoint   
Whether to ratelimit requests to the endpoint
    - bool
    - default True    
                 
- sleep_duration   
Amount of time program should sleep between ratelimit checks 
    - int | float
    - default(0.05)    
                 
- raise_errors   
Whether to raise an error instead of delaying until request can go through 
    - bool
    - default False  

## Ratelimit Algorithms

- slidingwindow
    - Implements a sliding window algorithm where`limit` requests can be made in any `window` seconds
    - Parameters:
        - `limit`: (int) | Requests allowed within `window` seconds
        - `window`: (float, int) | Time period in seconds of how many requests are allowed through in any `window` seconds


- fixedwindow
    - Implements a fixed window algorithm where `limit` requests can be made every `window` seconds
    - Parameters:
        - `limit`: (int) | Requests allowed every `window` seconds
        - `window`: (float, int) | Time period in seconds where only `limit` requests are allowed every `window` seconds


- leakybucket
    - The leaky bucket algorithm is a rate limiting algorithm that allows a `capacity` of requests to be processed per unit of time.  
    - The `leak_rate` defines how many requests per second leak through
    - Parameters
        - `capacity`: (float, int)  | Requests allowed before bucket is full
        - `leak_rate`: (float, int) | The rate at which the bucket leaks requests per unit of time.


- tokenbucket
    - The bucket can hold at the most `capacity` tokens. If a token arrives when the bucket is full, it is discarded.   
    - A token is added to the bucket every 1 / `fill_rate` seconds
    - Parameters:
        - `capacity`: (float, int) |      Requests allowed before bucket is empty
        - `fill_rate`: (float, int) |      The rate at which tokens are added to the bucket per second.


- gcra
    - GCRA (Generic Cell Rate Algorithm) is a rate limiting algorithm that allows a burst of requests up to a certain `limit` within a specified time `period`
    - Parameters:
        - `period`: (float, int) |     Time period for each cell/token (in seconds)
        - `limit`: (int) |     Limit on the burst size (in seconds)

## Usage

### Basic

```python
from sessions import Session, AsyncSession, RatelimitMixin

class Session(RatelimitMixin, Session):
    pass

# algorithm type can be specified by a variety of keyword args, most commonly: type, ratelimiter, ratelimit, rate_limit, limiter, limitertype
session = Session(backend="memory", type="slidingwindow", window=1, limit=10, per_host=True)
urls = ["https://httpbin.org/uuid"] * 100

session.requests(urls)
```

![alt text](/assets/gif/ratelimit-basic.gif)

## CacheMixin

### Parameters

- backend: str     
One of: memory, redis, sqlite   
Backend to use for caching.    
    - default "memory"
                 
- key: string        
Key prefix per cache item e.g. Session:METHOD:URL:ratelimit
    - default "Session"
                 
- cache_timeout   
How long a key remains active before being evicted 
    - int | float
    - default 3600    
                 
- conn   
Existing connection object to use
    - Redis | sqlite3.Connection | pymysql.Connection
    - default None

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