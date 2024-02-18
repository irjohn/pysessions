import traceback
from abc import ABC, abstractmethod
from functools import wraps
from inspect import iscoroutinefunction
from typing import List, Tuple, Set, Callable

from httpx import (
    Headers as HTTPXHeaders,
    URL as HTTPXURL,
)
from multidict import CIMultiDict
from yarl import URL as AIOHTTPURL

from sessions.cache import abstract


from .config import SessionConfig as config
from .objects import Response

class BaseSession(ABC):
    @property
    def backend(self):
        return self._backend

    @property
    def cache_key(self):
        return self.cache.key

    @property
    def ratelimit_key(self):
        return self._ratelimiter.key

    @property
    def cache(self):
        return self._cache

    @property
    def conn(self):
        return self._cache._cache_conn

    @property
    def cache_conn(self):
        return self._cache._cache_conn

    @property
    def ratelimit_conn(self):
        return self._ratelimiter._ratelimit_conn

    @property
    def ratelimiter(self):
        return self._ratelimiter

    @property
    def use_cache(self):
        return self._use_cache

    @property
    def use_ratelimit(self):
        return self._use_ratelimit

    def clear_cache(self):
        """
        Clears the cache and ratelimiter attributes of the object.
        """
        if hasattr("self", "_cache"):
            self._cache.clear()
        if hasattr(self, "_ratelimiter"):
            self._ratelimiter.clear()

    @staticmethod
    def _cache_decorator(func):
        """
        Decorator that caches the response of a request.

        Args:
            func: The function to be decorated.

        Returns:
            The decorated function.
        """
        if iscoroutinefunction(func):
            @wraps(func)
            async def request(self, url, method, *, headers=None, callbacks=None, cache=None, ratelimit=None, keys=None, bar=None, **kwargs):
                cache = cache if cache is not None else self._use_cache
                if cache:
                    async with self._semaphore:
                        response = self._cache[url]
                        if response is not None:
                            return await self._retrieve_response(response, callbacks, bar, is_cache=True)

                        response = await func(self, url=url, method=method, headers=headers, callbacks=callbacks, cache=cache, ratelimit=ratelimit, keys=keys, bar=bar, **kwargs)

                        if str(response.status_code).startswith("2"):
                            self._cache[url] = response

                        return response
                return await func(self, url=url, method=method, headers=headers, callbacks=callbacks, cache=cache, ratelimit=ratelimit, keys=keys, bar=bar, **kwargs)
            return request
        else:
            @wraps(func)
            def request(self, url, method, *, headers=None, callbacks=None, cache=None, ratelimit=None, keys=None, bar=None, threaded=False, **kwargs):
                cache = cache if cache is not None else self._use_cache
                if cache:
                    response = self._cache[url]
                    if response is not None:
                        return self._retrieve_response(response, callbacks, bar, is_cache=True)

                response = func(self, url=url, method=method, headers=headers, callbacks=callbacks, ratelimit=ratelimit, keys=keys, bar=bar, threaded=threaded, **kwargs)

                if cache and str(response.status_code).startswith("2"):
                    self._cache[url] = response
                return response
            return request

    @staticmethod
    def _ratelimit_decorator(func):
        """
        Decorator that ratelimits the request.

        Args:
            func: The function to be decorated.

        Returns:
            The decorated function.
        """
        if iscoroutinefunction(func):
            @wraps(func)
            async def request(self, url, method, *, headers=None, callbacks=None, cache=None, ratelimit=None, keys=None, bar=None, **kwargs):
                ratelimit = ratelimit if ratelimit is not None else self._use_ratelimit
                if ratelimit:
                    await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                response = await func(self, url=url, method=method, headers=headers, callbacks=callbacks, cache=cache, bar=bar, **kwargs)
                return response
            return request
        else:
            @wraps(func)
            def request(self, url, method, *, headers=None, callbacks=None, cache=None, ratelimit=None, keys=None, bar=None, threaded=False, **kwargs):
                ratelimit = ratelimit if ratelimit is not None else self._use_ratelimit
                if ratelimit:
                    self._ratelimiter.increment(url=url, method=method, keys=keys)
                return func(self, url=url, method=method, headers=headers, callbacks=callbacks, cache=cache, ratelimit=ratelimit, bar=bar, threaded=threaded, **kwargs)
            return request

    def _run_callbacks(
            self,
            response:   Response,
            callbacks:  tuple | list | set,
            bar:        callable,
            is_cache:   bool                    = False
        ):
        """
        Run the specified callbacks on the response object.

        Args:
            response (Response): The response object to run the callbacks on.
            callbacks (tuple | list | set): The callbacks to be executed.
            bar (callable): The progress bar function.
            is_cache (bool, optional): Indicates whether the response is from cache. Defaults to False.

        Returns:
            Response: The response object after running the callbacks.
        """
        response.set_cache(is_cache)
        if callbacks is None or response.errors is not None and not config.run_callbacks_on_error:
            if bar is not None:
                bar()
            return response

        rets = tuple()
        for callback in callbacks:
            try:
                if callable(callback):
                    ret = callback(response)
                    rets = (*rets, ret)
                else:
                    if config.print_callback_exceptions:
                        print(f"Callback {callback} is not callable.")
            except Exception as e:
                rets = (*rets, e)
                if config.print_callback_exceptions:
                    print(f"Callback {callback} raised exception: {e}")
                if config.print_callback_tracebacks:
                    traceback.print_exception(e)

        if config.return_callbacks:
            response.set_callbacks(rets)

        if bar is not None:
            bar()

        return response

    @abstractmethod
    def request(
        self,
        url: str | AIOHTTPURL | HTTPXURL,
        method: str,
        *,
        headers: dict | HTTPXHeaders | CIMultiDict | None  = None,
        callbacks: Tuple[Callable, ...] | None             = None,
        cache: bool                                        = None,
        ratelimit: bool                                    = None,
        keys: str | Tuple[str, ...] | List[str] | Set[str] = None,
        bar: Callable | None                               = None,
        **kwargs
    ):
        pass

    @abstractmethod
    def delete(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass

    @abstractmethod
    def get(
        self,
        url,
        **kwargs
    ):
        pass

    @abstractmethod
    def head(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass


    @abstractmethod
    def options(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass

    @abstractmethod
    def post(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass

    @abstractmethod
    def put(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass

    @abstractmethod
    def patch(
        self,
        url: str | HTTPXURL | AIOHTTPURL,
        **kwargs
    ):
        pass