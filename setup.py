from setuptools import setup, find_packages

setup(
    name="sessions",
    version="0.1.2",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "orjson",
        "requests",
        "httpx[http2]>=0.14.0",
        "aiohttp[speedups]>=3.9",
        "alive_progress",
        "python-dotenv",
        "yarl",
        "redislite",
        "redis",
    ],
    extras_require={
        "all": ["redislite", "stem"],
        "backend": ["redislite"],
        "proxy": ["requests[socks]"],
        "tor": ["stem"],
    }
)