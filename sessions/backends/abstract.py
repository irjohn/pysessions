__all__ = "ResourcePool",

from abc import ABC, abstractmethod

from threading import current_thread


class ResourcePool(ABC):
    __slots__ = ("_max_connections", "_lock", "_n_connections", "_options", "_pool")

    def __del__(self):
        self.close()

    @property
    def max_connections(self):
        return self._max_connections

    @property
    def n_connections(self):
        return self._n_connections

    @property
    def options(self):
        return self._options

    @property
    def lock(self):
        return self._lock

    @property
    def current_thread(self):
        return current_thread()

    @property
    def thread_id(self):
        return current_thread().ident

    @abstractmethod
    def acquire(self):
        pass

    @abstractmethod
    def release(self, resource):
        pass

    @abstractmethod
    def create_connection(self):
        pass

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def close(self):
        pass
