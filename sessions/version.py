import pkg_resources
from sys import version_info


__version__ = "0.1.2"
__python_version__ = (version_info.major, version_info.minor)
__aiohttp_version__ = pkg_resources.get_distribution("aiohttp").version
__httpx_version__ = pkg_resources.get_distribution("httpx").version