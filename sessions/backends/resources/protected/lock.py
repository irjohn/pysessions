from functools import wraps

def lock(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.lock.locked():
            with self.lock:
                print("Using lock!")
                return method(self, *args, **kwargs)
        return method(self, *args, **kwargs)
    return wrapper