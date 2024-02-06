from abc import ABC, abstractmethod


def is_valid_port(port):
    if port is None:
        return
    try:
        port = int(port)
        assert 0 <= port <= 65535, "Port must be an integer or string between 0 and 65535."
    except:
        raise ValueError("Port must be an integer or string between 0 and 65535.")

def is_valid_ipv4(value):
    if isinstance(value, str):
        octets = value.split(".")
        assert len(octets) == 4, "IPv4 addresses must have 4 octets"
        for octet in octets:
            octet = int(octet)
            assert octet >= 0 and octet <= 255, f"Invalid octet: {octet}"
        return True
    return False


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
    def __init__(self, *options, predicate=None):
        self.options = set(options)
        self.predicates = None
        self.predicate = None

        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate

    def validate(self, value):
        if value not in self.options:
            raise ValueError(f'Expected {value!r} to be one of {self.options!r}')

        if self.predicates is not None:
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )
        elif self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate.__name__} to be true for {value!r}'
            )

class TypeOf(Validator):
    def __init__(self, *types, subtypes=False, predicate=None):
        self.subtypes = subtypes
        self.types = set(types)
        self.predicates = None
        self.predicate = None

        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate

    def validate(self, value):
        if self.subtypes:
            is_subtype = False
            for t in self.types:
                if isinstance(value, t):
                    is_subtype = True
                    break
            if not is_subtype:
                raise ValueError(f'Expected {value!r} to be subtype of {self.types!r}')
        elif type(value) not in self.types:
            raise ValueError(f'Expected {value!r} to be type of {self.types!r}')

        if self.predicates is not None:
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )
        elif self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate.__name__} to be true for {value!r}'
            )


# The `Number` class is a validator that checks if a given value is a number within a specified range.
class Number(Validator):
    def __init__(self, minvalue=None, maxvalue=None, predicate=None):
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.predicates = None
        self.predicate = None

        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate


    def validate(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f'Expected {value!r} to be an int or float')
        if self.minvalue is not None and value < self.minvalue:
            raise ValueError(
                f'Expected {value!r} to be at least {self.minvalue!r}'
            )
        if self.maxvalue is not None and value > self.maxvalue:
            raise ValueError(
                f'Expected {value!r} to be no more than {self.maxvalue!r}'
            )
        if self.predicates is not None:
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )
        elif self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate.__name__} to be true for {value!r}'
            )

# The `String` class is a validator that checks if a given value is a string and satisfies certain
# size and predicate conditions.
class String(Validator):
    def __init__(self, minsize=None, maxsize=None, predicate=None):
        self.minsize = minsize
        self.maxsize = maxsize
        self.predicates = None
        self.predicate = None

        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate

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
        if self.predicates is not None:
            for fn in self.predicate:
                if not fn(value):
                    raise ValueError(
                        f'Expected {fn.__name__} to be true for {value!r}'
                    )

        elif self.predicate is not None and not self.predicate(value):
            raise ValueError(
                f'Expected {self.predicate.__name__} to be true for {value!r}'
            )



class Immutable(Validator):
    def __init__(self, predicate=None):
        self.predicates = None
        self.predicate = None
        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate


    def __set__(self, obj, value):
        if hasattr(obj, self.private_name):
            raise AttributeError('Cannot reassign immutable attribute')
        self.validate(value)
        setattr(obj, self.private_name, value)


    def validate(self, value):
        if self.predicates is not None:
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
    def __init__(self, predicate=None):
        self.predicates = None
        self.predicate = None

        if isinstance(predicate, (list, tuple, set)):
            for fn in predicate:
                if not callable(fn):
                    raise ValueError("Predicates must be callable")
            self.predicates = predicate
        else:
            if predicate is not None and not callable(predicate):
                raise ValueError("Predicates must be callable")
            self.predicate = predicate

    def __set__(self, obj, value):
        value = self.validate(value)
        setattr(obj, self.private_name, value)


    def validate(self, value):
        if value in {False, "False", "false", "no", "No", 0}:
            return False
        elif value in {True, "True", "true", "yes", "Yes", 1}:
            return True
        else:
            raise ValueError(f'Expected {value!r} to be a boolean')


class ImmutableString(Immutable, String):
    def __init__(self):
        Immutable.__init__(self)
        String.__init__(self)

    def validate(self, value):
        Immutable.validate(self, value)
        String.validate(self, value)


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