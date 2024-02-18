from importlib.metadata import version
from sys import version_info


__version__ = "0.1.2"
__python_version__ = (version_info.major, version_info.minor)
__aiohttp_version__ = version("aiohttp")
__httpx_version__ = version("httpx")

required_dependencies = [
    "orjson",
    "requests",
    "httpx[http2]>=0.14.0",
    "aiohttp[speedups]>=3.9",
    "alive_progress",
    "python-dotenv",
    "yarl",
    "redislite",
    "redis",
    "termcolor",
]