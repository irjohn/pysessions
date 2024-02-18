__all__ = "SQLitePoolManager",

import atexit
import time
from functools import wraps
from datetime import timedelta
from queue import Queue
from pathlib import Path
from threading import Lock, current_thread
from contextlib import contextmanager
from collections import defaultdict

from .abstract import ResourcePool
from .resources import SQLiteConnection
from .options import SQLiteOptions
from ..validators import NONE, Number, TypeOf, IsLock

MAIN_THREAD_ID = current_thread().ident

def check_idle(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        results = func(self, *args, **kwargs)
        self.close_idle_pools()
        return results
    return wrapper

class SQLitePool:
    __slots__ = "_pool", "_lock", "_max_connections", "_n_connections", "_expiration"
    pool: Queue                                       = TypeOf(Queue)
    lock: Lock                                        = IsLock()
    max_connections: Number                           = Number(minvalue=-1)
    n_connections: Number                             = Number(minvalue=0)
    expiration: Number                                = Number(minvalue=0)

    def __init__(self, max_connections):
        self.max_connections = max_connections
        self.pool = Queue(max_connections)
        self.lock = Lock()
        self.n_connections = 0
        self.expiration = time.time()

    def empty(self):
        return self.pool.empty()

    def get(self):
        return self.pool.get()

    def put(self, item):
        self.pool.put(item)


class SQLiteConnectionPool(ResourcePool):
    __slots__ = "_db_name", "_pools", "_locks", "_idle_timeout", "_idle_check_time"

    db_name: TypeOf                                 = TypeOf(str, Path)
    idle_timeout: TypeOf                            = TypeOf(float, int, NONE)
    idle_check_time: TypeOf                         = TypeOf(float, int, NONE)
    pools: TypeOf                                   = TypeOf(dict)
    locks: TypeOf                                   = TypeOf(dict)
    max_connections: TypeOf                         = TypeOf(dict)
    n_connections: TypeOf                           = TypeOf(dict)

    def __init__(
        self,
        db_name: str | Path,
        max_connections                             = 5,
        idle_timeout                                = 0.5,
    ):
        self.db_name                                = str(db_name)
        self.idle_timeout                           = idle_timeout or 0
        self.idle_check_time                        = time.time()

        self.max_connections                        = defaultdict(lambda: max_connections or 5)
        self.pools                                  = defaultdict(lambda: SQLitePool(max_connections))
        self.locks                                  = defaultdict(Lock)
        self.n_connections                          = defaultdict(int)

        atexit.register(self.close)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_pool(thread_id=self.thread_id)
        return True if exc_type is None else False

    @property
    def pool(self):
        return self.pools[self.thread_id]

    def set_max_connections(self, max_connections, thread_id=None):
        if thread_id:
            self.max_connections[thread_id] = max_connections
            pool = self.pool
            new_pool = Queue(max_connections)

            with pool.lock:
                while not pool.empty():
                    new_pool.put(pool.get())
                self.pools[thread_id] = new_pool
        else:
            for thread_id in self.pools.keys():
                self.set_max_connections(max_connections, thread_id)

    def set_idle_timeout(self, idle_timeout):
        self.idle_timeout = idle_timeout
        for thread_id in self.pools.keys():
            self.set_idle_timeout(idle_timeout, thread_id)

    def get_connection(self, timeout=30):
        if isinstance(timeout, (float, int, timedelta)):
            if isinstance(timeout, timedelta):
                timeout = timeout.total_seconds()
            start = time.time()

        pool = self.pool

        with pool.lock:
            # If pool is empty
            if pool.empty():
                if pool.n_connections < pool.max_connections:
                    conn = self.create_connection()
                else:
                    pool.lock.release()
                    while pool.empty():
                        time.sleep(0.1)
                        #print(f"Waiting for a connection: {self.thread_id}: {pool.qsize()}/{self.max_connections}")
                        if timeout and time.time() - start >= timeout:
                            raise TimeoutError("Timed out waiting for a connection")
                    pool.lock.acquire()
            else:
                conn = pool.get()
        return conn

    def get_pool(self, thread_id):
        return self.pools[thread_id]

    @contextmanager
    def acquire(self, timeout=30):
        conn = self.get_connection(timeout=timeout)
        try:
            yield conn
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.release(conn)

    def create_connection(self, thread_id=None):
        thread_id = thread_id or self.thread_id
        self.n_connections[thread_id] += 1
        return SQLiteConnection(self.db_name)

    @check_idle
    def release(self, conn, recycle=True):
        pool = self.pool

        if recycle:
            with pool.lock:
                pool.put(conn)
                pool.expiration = time.time() + self._idle_timeout
        else:
            conn.close()
            del conn
            self.n_connections[self.thread_id] -= 1

    def close(self):
        thread_ids = tuple(self.pools.keys())
        for thread_id in thread_ids:
            self.close_pool(thread_id)

    def close_pool(self, thread_id):
        pool = self.pools[thread_id]

        while not pool.empty():
            conn = pool.get()
            conn.close()
            del conn
            self.n_connections[thread_id] -= 1
        return thread_id

    def close_current_pool(self):
        return self.close_pool(self.thread_id)

    def close_idle_pools(self, idle_timeout=None):
        idle_timeout = idle_timeout or self.idle_timeout
        current_time = time.time()
        if idle_timeout:
            to_remove = tuple(self.close_pool(thread_id) for thread_id, pool in self.pools.items() if current_time > pool.expiration)
            for thread_id in to_remove:
                self.close_pool(thread_id)
                self.pools.pop(thread_id, None)
                self.locks.pop(thread_id, None)
                self.n_connections.pop(thread_id, None)


class SQLitePoolManager:
    pools: dict                         = TypeOf(dict)

    def __init__(self):
        self.pools = {}

    def from_options(
        self,
        options: SQLiteOptions
    ):
        pool = self.pools.setdefault(options, SQLiteConnectionPool(**options))
        return pool
