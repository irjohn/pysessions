from setuptools import setup, find_packages

setup(
    name="sessions",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "orjson",
        "requests",
        "httpx[http2]",
        "aiohttp[speedups]",
        "stem",
        "alive_progress",
        "aiomisc",
        "retry",
    ],
    extras_require={
        "all": ["redis[hiredis]", "psutil", "stem"],
        "backend": ["redis[hiredis]", "psutil"],
        "tor": ["stem"],
    }
)