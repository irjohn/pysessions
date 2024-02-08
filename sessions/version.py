import pkg_resources
from sys import version_info as __version__

__python_version__ = (__version__.major, __version__.minor)
__aiohttp_version__ = pkg_resources.get_distribution("aiohttp").version
__httpx_version__ = pkg_resources.get_distribution("httpx").version