from .lock import lock

EXCLUDE = {"__new__", "__init__", "__del__", "__enter__", "__exit__", "__class__", "__repr__"}


#----------------------------------------------------------------------------------------------------#
# STRING OPERATORS

def __repr__(self):
    return repr(self.value)

def __str__(self):
    return str(self.value)

@lock
def __hash__(self):
    return hash(self.value)

@lock
def __format__(self, format_spec):
    return self.value.__format__(format_spec)

@lock
def __bytes__(self):
    return bytes(self.value)

@lock
def __bool__(self):
    return bool(self.value)

@lock
def __dir__(self):
    return dir(self.value)

@lock
def __getattr__(self, name):
    return getattr(self.value, name)

@lock
def __setattr__(self, name, value):
    setattr(self.value, name, value)

@lock
def __delattr__(self, name):
    delattr(self.value, name)

@lock
def __call__(self, *args, **kwargs):
    return self.value(*args, **kwargs)

@lock
def __instancecheck__(self, instance):
    return isinstance(instance, self.value)

@lock
def __subclasscheck__(self, subclass):
    return issubclass(subclass, self.value)

@lock
def __init_subclass__(self, *args, **kwargs):
    return self.value.__init_subclass__(*args, **kwargs)

@lock
def __prepare__(self, name, bases, **kwargs):
    return self.value.__prepare__(name, bases, **kwargs)

@lock
def __new__(self, *args, **kwargs):
    return self.value.__new__(*args, **kwargs)

@lock
def __init__(self, *args, **kwargs):
    return self.value.__init__(*args, **kwargs)

@lock
def __del__(self):
    return self.value.__del__()



#----------------------------------------------------------------------------------------------------#
# CONTAINER OPERATORS

@lock
def __len__(self):
    return len(self.value)

@lock
def __length_hint__(self):
    return self.value.__length_hint__()

@lock
def __getitem__(self, item):
    return self.value[item]

@lock
def __setitem__(self, key, value):
    self.value[key] = value

@lock
def __delitem__(self, key):
    del self.value[key]

@lock
def __missing__(self, key):
    return self.value.__missing__(key)

@lock
def __iter__(self):
    return iter(self.value)

@lock
def __reversed__(self):
    return reversed(self.value)

@lock
def __contains__(self, item):
    return item in self.value

@lock
def __sizeof__(self):
    return self.value.__sizeof__()



#----------------------------------------------------------------------------------------------------#
# MATH OPERATORS

@lock
def __int__(self):
    return int(self.value)

@lock
def __float__(self):
    return float(self.value)

@lock
def __complex__(self):
    return complex(self.value)

@lock
def __index__(self):
    return self.value.__index__()

@lock
def __round__(self, n):
    return round(self.value, n)

@lock
def __trunc__(self):
    return self.value.__trunc__()

@lock
def __floor__(self):
    return self.value.__floor__()

@lock
def __ceil__(self):
    return self.value.__ceil__()

@lock
def __add__(self, other):
    return self.value + other

@lock
def __sub__(self, other):
    return self.value - other

@lock
def __mul__(self, other):
    return self.value * other

@lock
def __matmul__(self, other):
    return self.value @ other

@lock
def __truediv__(self, other):
    return self.value / other

@lock
def __floordiv__(self, other):
    return self.value // other

@lock
def __mod__(self, other):
    return self.value % other

@lock
def __divmod__(self, other):
    return divmod(self.value, other)

@lock
def __pow__(self, other):
    return self.value ** other

@lock
def __neg__(self):
    return -self.value

@lock
def __pos__(self):
    return +self.value

@lock
def __abs__(self):
    return abs(self.value)

@lock
def __iadd__(self, other):
    self.value += other
    return self

@lock
def __isub__(self, other):
    self.value -= other
    return self

@lock
def __imul__(self, other):
    self.value *= other
    return self

@lock
def __imatmul__(self, other):
    self.value @= other
    return self

@lock
def __itruediv__(self, other):
    self.value /= other
    return self

@lock
def __ifloordiv__(self, other):
    self.value //= other
    return self

@lock
def __imod__(self, other):
    self.value %= other
    return self

@lock
def __ipow__(self, other):
    self.value **= other
    return self

@lock
def __ilshift__(self, other):
    self.value <<= other
    return self

@lock
def __irshift__(self, other):
    self.value >>= other
    return self

@lock
def __iand__(self, other):
    self.value &= other
    return self

@lock
def __ixor__(self, other):
    self.value ^= other
    return self

@lock
def __ior__(self, other):
    self.value |= other
    return self

@lock
def __radd__(self, other):
    return other + self.value

@lock
def __rsub__(self, other):
    return other - self.value

@lock
def __rmul__(self, other):
    return other * self.value

@lock
def __rtruediv__(self, other):
    return other / self.value

@lock
def __rfloordiv__(self, other):
    return other // self.value

@lock
def __rmod__(self, other):
    return other % self.value

@lock
def __rpow__(self, other):
    return other ** self.value

@lock
def __rlshift__(self, other):
    return other << self.value

@lock
def __rand__(self, other):
    return other & self.value

@lock
def __rxor__(self, other):
    return other ^ self.value

@lock
def __ror__(self, other):
    return other | self.value

#--------
@lock
def __eq__(self, other):
    return self.value == other

@lock
def __ne__(self, other):
    return self.value != other

@lock
def __lt__(self, other):
    return self.value < other

@lock
def __le__(self, other):
    return self.value <= other

@lock
def __gt__(self, other):
    return self.value > other

@lock
def __ge__(self, other):
    return self.value >= other

#--------------------------------------------#



#----------------------------------------------------------------------------------------------------#
# BINARY OPERATORS

@lock
def __lshift__(self, other):
    return self.value << other

@lock
def __rshift__(self, other):
    return self.value >> other

@lock
def __and__(self, other):
    return self.value & other

@lock
def __xor__(self, other):
    return self.value ^ other

@lock
def __or__(self, other):
    return self.value | other

@lock
def __invert__(self):
    return ~self.value

@lock
def __oct__(self):
    return oct(self.value)

@lock
def __hex__(self):
    return hex(self.value)

#--------------------------------------------#
DUNDERS = {
    "__init__": __init__,
    "__new__": __new__,
    "__del__": __del__,
    "__repr__": __repr__,
    "__str__": __str__,
    "__bytes__": __bytes__,
    "__format__": __format__,
    "__lt__": __lt__,
    "__le__": __le__,
    "__eq__": __eq__,
    "__ne__": __ne__,
    "__gt__": __gt__,
    "__ge__": __ge__,
    "__hash__": __hash__,
    "__bool__": __bool__,
    "__getattr__": __getattr__,
    "__setattr__": __setattr__,
    "__delattr__": __delattr__,
    "__dir__": __dir__,
    "__init_subclass__": __init_subclass__,
    "__instancecheck__": __instancecheck__,
    "__subclasscheck__": __subclasscheck__,
    "__call__": __call__,
    "__len__": __len__,
    "__length_hint__": __length_hint__,
    "__getitem__": __getitem__,
    "__setitem__": __setitem__,
    "__delitem__": __delitem__,
    "__missing__": __missing__,
    "__iter__": __iter__,
    "__reversed__": __reversed__,
    "__contains__": __contains__,
    "__add__": __add__,
    "__radd__": __radd__,
    "__iadd__": __iadd__,
    "__sub__": __sub__,
    "__mul__": __mul__,
    "__matmul__": __matmul__,
    "__truediv__": __truediv__,
    "__floordiv__": __floordiv__,
    "__mod__": __mod__,
    "__divmod__": __divmod__,
    "__pow__": __pow__,
    "__lshift__": __lshift__,
    "__rshift__": __rshift__,
    "__and__": __and__,
    "__xor__": __xor__,
    "__or__": __or__,
    "__neg__": __neg__,
    "__pos__": __pos__,
    "__abs__": __abs__,
    "__invert__": __invert__,
    "__complex__": __complex__,
    "__int__": __int__,
    "__float__": __float__,
    "__index__": __index__,
    "__round__": __round__,
    "__trunc__": __trunc__,
    "__floor__": __floor__,
    "__ceil__": __ceil__,
}