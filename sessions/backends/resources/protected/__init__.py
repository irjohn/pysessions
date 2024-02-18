__all__ = "ProtectedResource", "ProtectedTuple", "ProtectedList", "ProtectedSet", "ProtectedDict", "ProtectedDefaultDict", "ProtectedComplex", "ProtectedFloat", "ProtectedInt", "ProtectedString", "ProtectedBytes"

from .types import *

class ProtectedResource:
    def __new__(cls, resource):
        if isinstance(resource, list):
            self = ProtectedList(resource)
        elif isinstance(resource, dict):
            self = ProtectedDict(resource)
        elif isinstance(resource, set):
            self = ProtectedSet(resource)
        elif isinstance(resource, int):
            self = ProtectedInt(resource)
        elif isinstance(resource, float):
            self = ProtectedFloat(resource)
        elif isinstance(resource, complex):
            self = ProtectedComplex(resource)
        elif isinstance(resource, str):
            self = ProtectedString(resource)
        elif isinstance(resource, bytes):
            self = ProtectedBytes(resource)
        else:
            raise TypeError(f"Resource type {type(resource)} is not supported.")
        self.__class__ = ProtectedResource
        return self
