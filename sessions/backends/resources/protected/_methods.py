from .lock import lock

#---------------------------------------------------------------
# LIST

@lock
def append(self, value):
    self.value.append(value)

@lock
def clear(self):
    self.value.clear()

@lock
def copy(self):
    return self.value.copy()

@lock
def count(self, value):
    return self.value.count(value)

@lock
def extend(self, iterable):
    self.value.extend(iterable)

@lock
def index(self, value, start=0, stop=None):
    return self.value.index(value, start, stop)

@lock
def insert(self, index, value):
    self.value.insert(index, value)

@lock
def pop(self, index=-1):
    return self.value.pop(index)

@lock
def remove(self, value):
    self.value.remove(value)

@lock
def reverse(self):
    self.value.reverse()

@lock
def sort(self, key=None, reverse=False):
    self.value.sort(key, reverse)

LIST = {
    "append": append,
    "clear": clear,
    "copy": copy,
    "count": count,
    "extend": extend,
    "index": index,
    "insert": insert,
    "pop": pop,
    "remove": remove,
    "reverse": reverse,
    "sort": sort,
}

#---------------------------------------------------------------
# DICT

@lock
def clear(self):
    self.value.clear()

@lock
def copy(self):
    return self.value.copy()

@lock
def fromkeys(self, seq, value=None):
    return self.value.fromkeys(seq, value)

@lock
def get(self, key, default=None):
    return self.value.get(key, default)

@lock
def items(self):
    return self.value.items()

@lock
def keys(self):
    return self.value.keys()

@lock
def pop(self, key, default=None):
    return self.value.pop(key, default)

@lock
def popitem(self):
    return self.value.popitem()

@lock
def setdefault(self, key, default=None):
    return self.value.setdefault(key, default)

@lock
def update(self, other=None, **kwargs):
    return self.value.update(other, **kwargs)

@lock
def values(self):
    return self.value.values()

DICT = {
    "clear": clear,
    "copy": copy,
    "fromkeys": fromkeys,
    "get": get,
    "items": items,
    "keys": keys,
    "pop": pop,
    "popitem": popitem,
    "setdefault": setdefault,
    "update": update,
    "values": values,
}

#---------------------------------------------------------------
# SET

@lock
def add(self, elem):
    self.value.add(elem)

@lock
def clear(self):
    self.value.clear()

@lock
def difference(self, other):
    return self.value.difference(other)

@lock
def difference_update(self, other):
    self.value.difference_update(other)

@lock
def discard(self, elem):
    self.value.discard(elem)

@lock
def intersection(self, other):
    return self.value.intersection(other)

@lock
def intersection_update(self, other):
    self.value.intersection_update(other)

@lock
def isdisjoint(self, other):
    return self.value.isdisjoint(other)

@lock
def issubset(self, other):
    return self.value.issubset(other)

@lock
def issuperset(self, other):
    return self.value.issuperset(other)

@lock
def pop(self):
    return self.value.pop()

@lock
def remove(self, elem):
    self.value.remove(elem)

@lock
def symmetric_difference(self, other):
    return self.value.symmetric_difference(other)

@lock
def symmetric_difference_update(self, other):
    self.value.symmetric_difference_update(other)

@lock
def union(self, other):
    return self.value.union(other)

@lock
def update(self, other):
    self.value.update(other)

SET = {
    "add": add,
    "clear": clear,
    "difference": difference,
    "difference_update": difference_update,
    "discard": discard,
    "intersection": intersection,
    "intersection_update": intersection_update,
    "isdisjoint": isdisjoint,
    "issubset": issubset,
    "issuperset": issuperset,
    "pop": pop,
    "remove": remove,
    "symmetric_difference": symmetric_difference,
    "symmetric_difference_update": symmetric_difference_update,
    "union": union,
    "update": update,
}

METHODS = {**LIST, **SET, **DICT}