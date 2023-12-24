from setuptools import setup, find_packages

setup(
    name="sessions",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "orjson",
        "requests",
        "httpx[http2]",
        "aiohttp[speedups]",
        "stem",
    ],
    extras_require={

    }
)