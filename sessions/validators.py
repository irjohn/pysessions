__all__ = "OneOf", "TypeOf", "DictOf", "Number", "String", "Immutable", "Bool", "ImmutableString", "IsLock", "LoggedAccess"

from abc import ABC, abstractmethod
from datetime import timedelta
from functools import wraps
from threading import Lock
from typing import Any, Union, Type, Tuple, Callable, Optional, Set, List

NONE = None.__class__

def is_valid_port(value):
    value = int(value)
    return value > 0 and value < 65535

def is_valid_ipv4(value):
    if isinstance(value, str):
        octets = value.split(".")
        assert len(octets) == 4, "IPv4 addresses must have 4 octets"
        for octet in octets:
            octet = int(octet)
            assert octet >= 0 and octet <= 255, f"Invalid octet: {octet}"
        return True
    return False

def predicates(func):
    @wraps(func)
    def wrapper(self, *args, predicate=None, **kwargs):
        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicate = tuple(predicate)
        elif predicate is not None:
            if not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = (predicate,)
        else:
            self.predicate = None
        return func(self, *args, **kwargs)
    return wrapper

def validate_predicates(func):
    @wraps(func)
    def wrapper(self, value):
        if hasattr(self, "predicate") and isinstance(self.predicate, tuple):
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )
        return func(self, value)
    return wrapper


# The `Validator` class is an abstract base class that provides a descriptor for validating attribute
# values before setting them.

class Validator(ABC):
    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private_name, value)

    @abstractmethod
    def validate(self, value):
        pass


# The `OneOf` class is a validator that checks if a given value is one of the specified options.
class OneOf(Validator):
    @predicates
    def __init__(self, *options, predicate=None):
        self.options = set(options)

    @validate_predicates
    def validate(self, value):
        if value not in self.options:
            raise ValueError(f'Expected {value!r} to be one of {self.options!r}')


class TypeOf(Validator):
    @predicates
    def __init__(self, *types, subtypes=True):
        self.subtypes = subtypes
        self.types = set(types)

    @validate_predicates
    def validate(self, value):
        if self.subtypes:
            is_subtype = False
            for base in type(value).mro()[:-1]:
                if any(issubclass(base, t) for t in self.types):
                    is_subtype = True
                    break
            if not is_subtype:
                raise ValueError(f'Expected {value!r} to be subtype of {self.types!r}')
        elif type(value) not in self.types:
            raise ValueError(f'Expected {value!r} to be type of {self.types!r}')


class DictOf(Validator):
    @predicates
    def __init__(self, key_type, value_type, predicate=None):
        self.key_type = key_type
        self.value_type = value_type

    @validate_predicates
    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError(f'Expected {value!r} to be a dict')
        for k, v in value.items():
            if not isinstance(k, self.key_type):
                raise ValueError(
                    f'Expected {k!r} to be a {self.key_type!r}'
                )
            if not isinstance(v, self.value_type):
                raise ValueError(
                    f'Expected {v!r} to be a {self.value_type!r}'
                )

# The `Number` class is a validator that checks if a given value is a number within a specified range.
class Number(Validator):
    @predicates
    def __init__(self, minvalue=None, maxvalue=None, timedelta=True):
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.allow_timedelta = timedelta

    @validate_predicates
    def validate(self, value):
        if self.allow_timedelta and isinstance(value, timedelta):
            value = value.total_seconds()
        elif not self.allow_timedelta and isinstance(value, timedelta):
            raise ValueError(
                f'Expected {value!r} to be a number'
            )

        if not isinstance(value, (int, float)):
            raise TypeError(
                f'Expected {value!r} to be an int or float'
            )
        if self.minvalue is not None and value < self.minvalue:
            raise ValueError(
                f'Expected {value!r} to be at least {self.minvalue!r}'
            )
        if self.maxvalue is not None and value > self.maxvalue:
            raise ValueError(
                f'Expected {value!r} to be no more than {self.maxvalue!r}'
            )


# The `String` class is a validator that checks if a given value is a string and satisfies certain
# size and predicate conditions.
class String(Validator):
    @predicates
    def __init__(self, minsize=None, maxsize=None, predicate=None):
        self.minsize = minsize
        self.maxsize = maxsize

    @validate_predicates
    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f'Expected {value!r} to be an str')

        if self.minsize is not None and len(value) < self.minsize:
            raise ValueError(
                f'Expected {value!r} to be no smaller than {self.minsize!r}'
            )
        if self.maxsize is not None and len(value) > self.maxsize:
            raise ValueError(
                f'Expected {value!r} to be no bigger than {self.maxsize!r}'
            )


class Immutable(Validator):
    @predicates
    def __init__(self):
        pass

    def __set__(self, obj, value):
        if hasattr(obj, self.private_name):
            raise AttributeError('Cannot reassign immutable attribute')
        self.validate(value)
        setattr(obj, self.private_name, value)

    @validate_predicates
    def validate(self, value):
        if self.predicate is not None:
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )
        elif self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate.__name__} to be true for {value!r}'
            )


class Bool(Validator):
    @predicates
    def __init__(self):
        pass

    def __set__(self, obj, value):
        value = self.validate(value)
        setattr(obj, self.private_name, value)

    @validate_predicates
    def validate(self, value):
        if value in {False, "False", "false", "no", "No", 0}:
            return False
        elif value in {True, "True", "true", "yes", "Yes", 1}:
            return True
        else:
            raise ValueError(f'Expected {value!r} to be a boolean')


class ImmutableString(Immutable, String):
    @predicates
    def __init__(self):
        Immutable.__init__(self)
        String.__init__(self)

    @validate_predicates
    def validate(self, value):
        Immutable.validate(self, value)
        String.validate(self, value)


class IsLock(Validator):
    def validate(self, value):
        if value.__class__ is not Lock().__class__:
            raise ValueError(
                f'Expected {value!r} to be a Lock'
            )


# The `LoggedAccess` class provides logging functionality for accessing and updating attributes of an
# object.
class LoggedAccess:
    def __set_name__(self, owner, name):
        import logging
        logging.basicConfig(level=logging.INFO)
        self.public_name = name
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        value = getattr(obj, self.private_name)
        logging.info('Accessing %r giving %r', self.public_name, value) # type: ignore
        return value

    def __set__(self, obj, value):
        logging.info('Updating %r to %r', self.public_name, value) # type: ignore
        setattr(obj, self.private_name, value)