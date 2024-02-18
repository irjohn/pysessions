__all__ = "ProtectedTuple", "ProtectedList", "ProtectedDict", "ProtectedSet", "ProtectedDefaultDict", "ProtectedComplex", "ProtectedFloat", "ProtectedInt", "ProtectedBytes", "ProtectedString"

from threading import Lock
from collections import defaultdict

from ._dunders import DUNDERS
from ._methods import METHODS
from ._examples import example

METHODS = {**DUNDERS, **METHODS}

def __setattr__(self, name, value):
    if name not in self.__attrs__:
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")
    if name == "value":
        if not hasattr(self, "value"):
            self.__dict__["value"] = value
        else:
            raise AttributeError("Cannot reassign immutable attribute")
    else:
        self.__dict__[name] = value


def __enter__(self):
    self.lock.acquire()
    return self

def __exit__(self, exc_type, exc_value, traceback):
    self.lock.release()
    return False if exc_type is not None else True

class ProtectedMeta(type):
    """Metaclass for creating protected classes."""

    def __new__(cls, name, bases, dct):
        dct["__setattr__"] = __setattr__
        dct["__class__"] = bases[0].__class__
        dct["__dir__"] = lambda self: dir(self.value)
        dct["__enter__"] = __enter__
        dct["__exit__"] = __exit__
        dct["lock"] = Lock()
        __attrs__ = set(("lock", "value", "__class__"))

        for attr_name in vars(bases[0]):
            if attr_name in METHODS and attr_name not in {"__new__", "__class__", "__init__"}:
                method = cls._define(attr_name)
                dct[attr_name] = method
            else:
                __attrs__.add(attr_name)

        dct["__attrs__"] = __attrs__
        new_class = super().__new__(cls, name, bases, dct)
        return new_class

    @staticmethod
    def _define(name):
        return METHODS[name]

#----------------------------------------------------------------------------------------------------#
# Sequence

class ProtectedTuple(tuple, metaclass=ProtectedMeta):
    """
    A protected tuple that ensures its value cannot be modified directly.

    Args:
        value (iterable, optional): The initial values for the tuple. Defaults to an empty tuple.
    """

    def __init__(self, value=None):
        self.value = tuple(value) if value is not None else ()

class ProtectedList(list, metaclass=ProtectedMeta):
    """
    A protected list that ensures its contents cannot be modified directly.

    Args:
        value (iterable, optional): Initial values for the protected list.

    Attributes:
        value (list): The underlying list that holds the protected values.

    Example:
        >>> import time
        >>> import random
        >>> from pypools import ProtectedResource
        >>> from concurrent.futures import ThreadPoolExecutor, as_completed
        ...
        >>> def update_protected_list(lst):
        >>>     with lst:
        >>>         length = len(lst)
        >>>         if random.choice([True, False]):
        >>>             time.sleep(random.uniform(0, 1))
        >>>         lst.append(length)
        >>>         return length
        ...
        >>> def update_unprotected_list(lst):
        >>>     length = len(lst)
        >>>     if random.choice([True, False]):
        >>>         time.sleep(random.uniform(0, 1))
        >>>     lst.append(length)
        >>>     return length
        ...
        >>> with ThreadPoolExecutor() as executor:
        >>>     protected_list = ProtectedResource([])
        >>>     unprotected_list = []
        ...
        >>>     futures = [executor.submit(update_protected_list, protected_list) for _ in range(10)]
        >>>     for i, future in enumerate(as_completed(futures)):
        >>>         assert future.result() == i, f"Protected list is not thread safe! {protected_list[i]} is not > {protected_list[i - 1] if i > 0 else 0}"
        ...
        >>>     futures = [executor.submit(update_unprotected_list, unprotected_list) for _ in range(10)]
        >>>     for i, future in enumerate(as_completed(futures)):
        >>>         assert future.result() == i, f"Unprotected list is not thread safe! {unprotected_list[i]} is not > {unprotected_list[i - 1] if i > 0 else 0}"
        ...
        AssertionError: Unprotected list is not thread safe! 1 is not > 0
    """

    def __init__(self, value=None):
        self.value = list(value) if value is not None else []

class ProtectedDict(dict, metaclass=ProtectedMeta):
    """
    A dictionary class that provides protection for its contents.

    This class inherits from the built-in `dict` class and uses the `ProtectedMeta` metaclass
    to enforce protection on the dictionary's contents.

    Attributes:
        value (dict): The underlying dictionary that stores the data.

    Args:
        value (dict, optional): The initial dictionary to populate the `ProtectedDict` with.
                                Defaults to an empty dictionary if not provided.

    Example:
        >>> import time
        >>> import random
        >>> from pypools import ProtectedResource
        >>> from concurrent.futures import ThreadPoolExecutor, as_completed
        ...
        >>> def update_protected_dict(dct):
        >>>     with dct:
        >>>         length = len(dct)
        >>>         if random.choice([True, False]):
        >>>             time.sleep(random.uniform(0, 1))
        >>>         dct.append(length)
        >>>         return length
        ...
        >>> def update_unprotected_dict(dct):
        >>>     length = len(dct)
        >>>     if random.choice([True, False]):
        >>>         time.sleep(random.uniform(0, 1))
        >>>     dct.append(length)
        >>>     return length
        ...
        >>> with ThreadPoolExecutor() as executor:
        >>>     protected_dict = ProtectedResource([])
        >>>     unprotected_dict = []
        ...
        >>>     futures = [executor.submit(update_protected_dict, protected_dict) for _ in range(10)]
        >>>     for i, future in enumerate(as_completed(futures)):
        >>>         assert future.result() == i, f"Protected dict is not thread safe! {protected_dict[i]} is not > {protected_dict[i - 1] if i > 0 else 0}"
        ...
        >>>     futures = [executor.submit(update_unprotected_dict, unprotected_dict) for _ in range(10)]
        >>>     for i, future in enumerate(as_completed(futures)):
        >>>         assert future.result() == i, f"Unprotected dict is not thread safe! {unprotected_dict[i]} is not > {unprotected_dict[i - 1] if i > 0 else 0}"
        ...
        AssertionError: Unprotected dict is not thread safe! 1 is not > 0
    """

    def __init__(self, value=None):
        self.value = dict(value) if value is not None else {}

class ProtectedSet(set, metaclass=ProtectedMeta):
    """
    A protected set that ensures the privacy of its elements.

    This class extends the built-in `set` class and provides additional protection
    for the elements stored in the set. It uses a metaclass `ProtectedMeta` to enforce
    privacy rules.

    Args:
        value (iterable, optional): An iterable of elements to initialize the set with.

    Attributes:
        value (set): The underlying set that stores the elements.

    Example:
        >>> pset = ProtectedSet([1, 2, 3])
        >>> pset.add(4)
        >>> pset
        {1, 2, 3, 4}
    """

    def __init__(self, value=None):
        self.value = set(value) if value is not None else set()

class ProtectedDefaultDict(dict, metaclass=ProtectedMeta):
    """
    A dictionary subclass that provides a default value for missing keys.

    This class extends the built-in `dict` class and adds the ability to specify a default value
    for keys that are not present in the dictionary. It uses the `default_factory` function to
    generate the default value for missing keys.

    Attributes:
        __attr__ (set): A set of attribute names that are protected and cannot be modified.

    Args:
        default_factory (callable, optional): A function that returns the default value for missing keys.
            Defaults to None.
        value (dict, optional): A dictionary to initialize the `ProtectedDefaultDict` with.
            Defaults to an empty dictionary.

    Methods:
        __missing__(key): Returns the default value for missing keys.

    Example:
        >>> d = ProtectedDefaultDict(lambda: 0)
        >>> d['a'] = 1
        >>> d['b']
        0
    """

    __attr__ = {"default_factory", "value", "__lock", "__class__"}

    def __init__(self, default_factory=None, value=None):
        self.value = defaultdict(default_factory, value) if value is not None else defaultdict()

    def __missing__(self, key):
        return self.default_factory(key)

#----------------------------------------------------------------------------------------------------#
# Numeric

class ProtectedComplex(complex, metaclass=ProtectedMeta):
    """
    A protected complex number that is thread-safe.

    Args:
        value (complex, optional): The initial value of the protected complex number. Defaults to 0j.

    Returns:
        ProtectedComplex: A protected complex number object.

    Examples:
        >>> x = ProtectedComplex(3 + 4j)
        >>> print(x)
        (3+4j)
    """

    def __init__(self, value=None):
        self.value = value or 0j

    def __int__(self):
        return ProtectedInt(int(self.value.real))

    def __float__(self):
        return ProtectedFloat(float(self.value.real))

class ProtectedFloat(float, metaclass=ProtectedMeta):
    """
    A protected float class that is thread-safe.

    Args:
        value (float): The initial value of the protected float. Defaults to 0.0.

    Attributes:
        value (float): The current value of the protected float.

    Methods:
        __int__(): Converts the protected float to a protected integer.
        __complex__(): Converts the protected float to a protected complex number.
    """

    def __init__(self, value=None):
        self.value = value or 0.0

    def __int__(self):
        return ProtectedInt(int(self.value))

    def __complex__(self):
        return ProtectedComplex(complex(self.value))

class ProtectedInt(int, metaclass=ProtectedMeta):
    """
    A protected integer that is thread-safe.

    Args:
        value (int): The initial value of the protected integer. Defaults to 0.

    Attributes:
        value (int): The current value of the protected integer.

    Methods:
        __float__(): Converts the protected integer to a protected float.
        __complex__(): Converts the protected integer to a protected complex number.
    """

    def __init__(self, value=None):
        self.value = value or 0

    def __float__(self):
        return ProtectedFloat(float(self.value))

    def __complex__(self):
        return ProtectedComplex(complex(self.value))

#----------------------------------------------------------------------------------------------------#
# Text

class ProtectedBytes(bytes, metaclass=ProtectedMeta):
    """
    Represents a protected byte string that is thread-safe.

    Inherits from the built-in `bytes` class and uses a metaclass `ProtectedMeta`
    for additional protection.

    Args:
        value (bytes): The initial value of the protected byte string.

    Attributes:
        value (bytes): The underlying byte string value.

    Methods:
        __str__: Returns a protected string representation of the byte string.

    Example:
        >>> pb = ProtectedBytes(b"Hello")
        >>> print(pb)
        ProtectedString('Hello')
    """

    def __init__(self, value=None):
        self.value = value or b""

    def __str__(self):
        return ProtectedString(str(self.value.decode("utf-8")))

class ProtectedString(str, metaclass=ProtectedMeta):
    """
    Represents a protected string that is thread-safe.
    """

    def __init__(self, value=None):
        self.value = value or ""

    def __bytes__(self):
        return ProtectedBytes(self.value.encode("utf-8"))
