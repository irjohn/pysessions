import traceback
from functools import wraps
from inspect import iscoroutinefunction
from asyncio import iscoroutinefunction as _iscoroutinefunction

from .objects import Response
from .config import SessionConfig as config


def clear_cache(self):
    if hasattr("self", "_cache"):
        self._cache.clear()
    if hasattr(self, "_ratelimiter"):
        self._ratelimiter.clear()


def _run_callbacks(
        self,
        response:   Response,
        callbacks:  tuple | list | set,
        bar:        callable
    ):
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

def cache(func):
    @wraps(func)
    def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, threaded=False, **kwargs):
        if cache:
            response = self._cache[url]
            if response is not None:
                return self._retrieve_response(response, callbacks, bar)

        response = func(self, url, method, headers=headers, callbacks=callbacks, ratelimit=ratelimit, keys=keys, bar=bar, threaded=threaded, **kwargs)

        if cache and str(response.status_code).startswith("2"):
            self._cache[url] = response

        return response

    return request

def async_cache(func):
    @wraps(func)
    async def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
        if cache:
            async with self._semaphore:
                response = self._cache[url]
                if response is not None:
                    return await self._retrieve_response(response, callbacks, bar)

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
                namespace["clear_cache"] = clear_cache
                namespace["_run_callbacks"] = _run_callbacks
                if hasattr(session, "request"):
                    namespace["request"] = cls.define_request(session, set(parents.keys()))

        namespace["__bases__"] = parents
        return super().__new__(cls, name, bases, namespace)


    @staticmethod
    def define_request(session, parents):
        """Define the request method based on the mixins present in the inheritance hierarchy.

        Args:
            name (str): The name of the session class.
            session (class): The base session class.
            parents (set): Set of parent class names.

        Returns:
            function: The defined request method.
        """
        if iscoroutinefunction(session.request) or _iscoroutinefunction(session.request):
            if "CacheMixin" in parents and "RatelimitMixin" in parents:
                @async_cache
                async def request(self, url, method, *, headers=None, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
                    if ratelimit:
                        if not cache:
                            async with self._semaphore:
                                await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                        else:
                            await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                    return await session.request(self, url=url, method=method, headers=headers, callbacks=callbacks, bar=bar, **kwargs)

            elif "RatelimitMixin" in parents:
                async def request(self, url, method, *, headers=None, callbacks=None, ratelimit=True, keys=None, bar=None, **kwargs):
                    if ratelimit:
                        async with self._semaphore:
                            await self._ratelimiter.increment_async(url=url, method=method, keys=keys)
                    return await session.request(self, method=method, url=url, headers=headers, callbacks=callbacks, bar=bar, **kwargs)

            elif "CacheMixin" in parents:
                @async_cache
                async def request(self, url, method, *, headers=None, callbacks=None, cache=True, bar=None, **kwargs):
                    return await session.request(self, method=method, url=url, headers=headers, callbacks=callbacks, bar=bar, **kwargs)

            else:
                request = session.request

        else:
            if "CacheMixin" in parents and "RatelimitMixin" in parents:
                @cache
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, cache=True, ratelimit=True, keys=None, bar=None, **kwargs):
                    if ratelimit:
                        self._ratelimiter.increment(url=url, method=method, keys=keys)
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)


            elif "RatelimitMixin" in parents:
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, ratelimit=True, keys=None, bar=None, **kwargs):
                    if ratelimit:
                        self._ratelimiter.increment(url=url, method=method, keys=keys)
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)


            elif "CacheMixin" in parents:
                @cache
                def request(self, url, method, *, headers=None, threaded=False, callbacks=None, cache=True, bar=None, **kwargs):
                    return session.request(self, method=method, url=url, headers=headers, threaded=threaded, callbacks=callbacks, bar=bar, **kwargs)

            else:
                request = session.request

        return request