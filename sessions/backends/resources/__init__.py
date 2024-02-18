__all__ = "Resource", "SQLiteConnection", "RedisConnection", "sqlite_connection_factory", "redis_connection_factory", "ProtectedResource", "ProtectedTuple", "ProtectedList", "ProtectedSet", "ProtectedDict", "ProtectedDefaultDict", "ProtectedComplex", "ProtectedFloat", "ProtectedInt", "ProtectedString", "ProtectedBytes"

from pathlib import Path
from threading import current_thread

from .abstract import Resource
from .sqlite import SQLiteConnection
from .redis import RedisConnection
from .protected import *

MAIN_THREAD_ID = current_thread().ident

def sqlite_connection_factory(
    conn: SQLiteConnection | None = None,
    db_name: str | Path = ":memory:",
) -> SQLiteConnection:
    if conn is not None and isinstance(conn, SQLiteConnection) and conn._thread_id == MAIN_THREAD_ID:
        return conn
    return SQLiteConnection(db_name)


def redis_connection_factory(
    conn: RedisConnection | None = None,
    **kwargs
) -> RedisConnection:
    if conn is not None and isinstance(conn, RedisConnection):
        return conn
    return RedisConnection(**kwargs)