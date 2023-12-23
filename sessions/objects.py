from dataclasses import dataclass

from yarl import URL
from aiohttp.connector import Connection
from http.cookies import SimpleCookie
from multidict import CIMultiDictProxy, MultiDictProxy
from typing import Sequence
from aiohttp import (
    RequestInfo,
    ClientResponse,
    StreamReader,
    HttpVersion,
)

@dataclass(slots=True)
class AsyncResponse:
    version: HttpVersion
    status: int
    reason: str
    ok: bool
    method: str
    url: URL
    real_url: URL
    connection: Connection
    content: StreamReader
    cookies: SimpleCookie
    headers: CIMultiDictProxy
    raw_headers: tuple
    links: MultiDictProxy
    content_type: str
    charset: str | None
    content_disposition: str
    history: Sequence[ClientResponse]
    text: str
    json: dict | None
    request_info: RequestInfo