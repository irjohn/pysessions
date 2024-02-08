import traceback
from functools import wraps
from inspect import iscoroutinefunction as inspect_iscoroutinefunction
from asyncio import iscoroutinefunction as asyncio_iscoroutinefunction

from .objects import Response
from .config import SessionConfig as config


def clear_cache(self):
    """
    Clears the cache and ratelimiter attributes of the object.
    """
    if hasattr("self", "_cache"):
        self._cache.clear()
    if hasattr(self, "_ratelimiter"):
        self._ratelimiter.clear()


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

    if is_cache:
        response.set_cache(True)

    return response

def cache(func):
    """
    Decorator that caches the response of a request.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """
    @wraps(func)
    def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, threaded=False, **kwargs):
        if cache:
            response = self._cache[url]
            if response is not None:
                return self._retrieve_response(response, callbacks, bar, is_cache=True)

        response = func(self, url, method, headers=headers, callbacks=callbacks, ratelimit=ratelimit, keys=keys, bar=bar, threaded=threaded, **kwargs)

        if cache and str(response.status_code).startswith("2"):
            self._cache[url] = response
        return response
    return request

def async_cache(func):
    """
    A decorator that provides caching functionality for asynchronous requests.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """
    @wraps(func)
    async def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
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


class SessionMeta(type):
    """Metaclass for session classes.

    This metaclass is responsible for dynamically modifying the session class based on its parents.
    It adds additional functionality to the session class based on the mixins present in its inheritance hierarchy.
    """

    def __new__(cls, name, bases, namespace):
        parents = {base.__name__: base for base in bases}
        namespace["_run_callbacks"] = _run_callbacks
        namespace["clear_cache"] = clear_cache

        if namespace.get("request") is None:
            session = None
            for name, base in parents.items():
                name = name.lower()
                if "session" in name or "client" in name:
                    session = base
                    base_index = bases.index(session)
                    if base_index != len(bases) - 1:
                        bases = list(bases)
                        bases.remove(session)
                        bases.append(session)
                        bases = tuple(bases)
                        parents = {base.__name__: base for base in bases}
                    break

            if session is not None:

                if hasattr(session, "request"):
                    namespace["request"] = cls.define_request(session, set(parents.keys()))

        namespace["__bases__"] = parents
        return super().__new__(cls, name, bases, namespace)


    @staticmethod
    def define_request(session, parents):
        """Define the request method based on the mixins present in the inheritance hierarchy.

        Args:
            session (class): The base session class.
            parents (set): Set of parent class names.

        Returns:
            function: The defined request method.
        """
        if inspect_iscoroutinefunction(session.request) or asyncio_iscoroutinefunction(session.request):
            if "CacheMixin" in parents and "RatelimitMixin" in parents:
                @async_cache
                async def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
                    """
                    Send an HTTP request asynchronously.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): The headers to include in the request. Defaults to None.
                        callbacks (list, optional): List of callback functions to be called after the request is completed. Defaults to None.
                        cache (bool, optional): Whether to cache the response. Defaults to True.
                        ratelimit (bool, optional): Whether to apply rate limiting. Defaults to True.
                        keys (list, optional): List of keys to use for rate limiting. Defaults to None.
                        bar (ProgressBar, optional): Progress bar to display the request progress. Defaults to None.
                        **kwargs: Additional keyword arguments to be passed to the underlying session.request method.

                    Returns:
                        The response of the HTTP request.
                    """
                    if ratelimit:
                        if not cache:
                            async with self._semaphore:
                                await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                        else:
                            await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                    return await session.request(self, url=url, method=method, headers=headers, callbacks=callbacks, bar=bar, **kwargs)

            elif "RatelimitMixin" in parents:
                async def request(self, url, method, *, headers=None, callbacks=None, ratelimit=True, keys=None, bar=None, **kwargs):
                    """
                    Send an HTTP request.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): Additional headers to include in the request. Defaults to None.
                        callbacks (list, optional): List of callback functions to be called after the request is complete. Defaults to None.
                        ratelimit (bool, optional): Whether to apply rate limiting. Defaults to True.
                        keys (list, optional): List of keys to use for rate limiting. Defaults to None.
                        bar (ProgressBar, optional): Progress bar to display during the request. Defaults to None.
                        **kwargs: Additional keyword arguments to pass to the underlying session.request() method.

                    Returns:
                        The response from the HTTP request.

                    """
                    if ratelimit:
                        async with self._semaphore:
                            await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                    return await session.request(self, method=method, url=url, headers=headers, callbacks=callbacks, bar=bar, **kwargs)

            elif "CacheMixin" in parents:
                @async_cache
                async def request(self, url, method, *, headers=None, callbacks=None, cache=True, bar=None, **kwargs):
                    """
                    Send an HTTP request.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): Additional headers to include in the request. Defaults to None.
                        callbacks (list, optional): List of callback functions to apply to the response. Defaults to None.
                        cache (bool, optional): Whether to cache the response. Defaults to True.
                        bar (ProgressBar, optional): Progress bar to display during the request. Defaults to None.
                        **kwargs: Additional keyword arguments to pass to the underlying session.request() method.

                    Returns:
                        The response from the HTTP request.
                    """
                    return await session.request(self, method=method, url=url, headers=headers, callbacks=callbacks, bar=bar, **kwargs)
            else:
                request = session.request

        else:
            if "CacheMixin" in parents and "RatelimitMixin" in parents:
                @cache
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
                    """
                    Send a request to the specified URL using the specified HTTP method.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): Additional headers to include in the request. Defaults to None.
                        threaded (bool, optional): Whether to execute the request in a separate thread. Defaults to False.
                        callbacks (list, optional): List of callback functions to execute after the request completes. Defaults to None.
                        cache (bool, optional): Whether to cache the response. Defaults to True.
                        ratelimit (bool, optional): Whether to apply rate limiting. Defaults to True.
                        keys (list, optional): List of keys to use for rate limiting. Defaults to None.
                        bar (ProgressBar, optional): Progress bar to display during the request. Defaults to None.
                        **kwargs: Additional keyword arguments to pass to the underlying session.request method.

                    Returns:
                        The response object returned by the underlying session.request method.
                    """
                    if ratelimit:
                        self._ratelimiter.increment(url=url, method=method, keys=keys)
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)

            elif "RatelimitMixin" in parents:
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, ratelimit=True, keys=None, bar=None, **kwargs):
                    """
                    Send a request to the specified URL using the specified HTTP method.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): Additional headers to include in the request. Defaults to None.
                        threaded (bool, optional): Whether to execute the request in a separate thread. Defaults to False.
                        callbacks (list, optional): List of callback functions to execute after the request completes. Defaults to None.
                        ratelimit (bool, optional): Whether to apply rate limiting. Defaults to True.
                        keys (list, optional): List of keys to use for rate limiting. Defaults to None.
                        bar (ProgressBar, optional): Progress bar to display during the request. Defaults to None.
                        **kwargs: Additional keyword arguments to pass to the underlying session's request method.

                    Returns:
                        The response object returned by the underlying session's request method.
                    """
                    if ratelimit:
                        self._ratelimiter.increment(url=url, method=method, keys=keys)
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)

            elif "CacheMixin" in parents:
                @cache
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, cache=True, bar=None, **kwargs):
                    """
                    Send a request to the specified URL using the specified method.

                    Args:
                        url (str): The URL to send the request to.
                        method (str): The HTTP method to use for the request.
                        headers (dict, optional): Additional headers to include in the request. Defaults to None.
                        threaded (bool, optional): Whether to execute the request in a separate thread. Defaults to False.
                        callbacks (list, optional): List of callback functions to execute after the request completes. Defaults to None.
                        cache (bool, optional): Whether to cache the response. Defaults to True.
                        bar (ProgressBar, optional): Progress bar to display during the request. Defaults to None.
                        **kwargs: Additional keyword arguments to pass to the underlying session.request() method.

                    Returns:
                        The response object.

                    """
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)
            else:
                request = session.request

        return request