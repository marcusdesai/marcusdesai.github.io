Title: Generic Parameters in Python 3.12
Date: 2023-08-06
Slug: py312-generics
Category: code
Status: published
Tags: python, types, features

Just something quick about one of my favourite upcoming Python 3.12 features, generic type parameter syntax!

Generics have been part of Python for almost 8 years. They were added when type hints themselves were introduced by [PEP 484][pep-484] in Python 3.5. Geez, it feels like it's been way less time than that 😅

### Python 3.11

Since then we've been able to write functions and classes with type parameters:
```python
from typing import Generic, TypeVar

T = TypeVar("T")

# although we've only been able to use parameterised 
# `list` since Python 3.11
def first(elems: list[T]) -> T: ...

K = TypeVar("K")
V = TypeVar("V")

class Map(Generic[K, V]):
    def insert(self, key: K, value: V) -> None: ...

    def get(self, key: K) -> V | None: ...
```

Very nice, but I want to highlight two drawbacks to this in maintaining code clarity.

Function signatures are not self contained:
```python
# imagine T, U and V are defined somewhere else
def some_func(param1: T, param2: U) -> V: ...
```
Any of _T_, _U_ or _V_ could be type parameters, but it is not immediately clear which, if any, are. Secondly, type variables can be reused:
```python
T = TypeVar("T")

def func_one(t: T) -> T: ...

def func_two(t: T) -> T: ...
```
Which itself can be confusing, and is made worse by adding variance or constrains to type parameters, making them hazardous to reuse without careful inspection.

### Python 3.12

Starting from the next Python release which includes [PEP 695][pep-695], we'll have a better way:
```python
def first[T](elems: list[T]) -> T: ...

class Map[K, V]:
    def insert(self, key: K, value: V) -> None: ...

    def get(self, key: K) -> V | None: ...
```
<span style="font-size: 4rem;">🤗</span>

Ah, so wonderful. First off, we no longer need to define type variables. But I think the function definition syntax change is the big win here, we keep the type parameters local (which we already had with class generics), reducing mental overhead when reading code.

### Bonus

PEP 695 also includes a good improvement to defining type aliases.

```python
from typing import TypeAlias

# Python 3.11
MyAlias: TypeAlias = int

# Python 3.12
type MyAlias = int
```

A useful property of the new type alias implementation is that it utilises lazy evaluation to allow aliases to refer to names that haven't been defined yet, including themselves.

```python
# this recursive type alias works in 3.12
type RecrAlias = int | list[RecrAlias]
```

There's a lot more going on in PEP 695, so I'd definitely recommend giving it a read if you're interested in more type system goodies (like how constraints, bounds and variance inference work).

[pep-484]: https://peps.python.org/pep-0484/
[pep-695]: https://peps.python.org/pep-0695/
