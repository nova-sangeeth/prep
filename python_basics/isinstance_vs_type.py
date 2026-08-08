"""Q37. isinstance() vs type().

isinstance(obj, Cls) -> True for the class AND its subclasses (respects
inheritance). Preferred for type checks.
type(obj) is Cls     -> exact type only, ignores subclasses.
"""
from __future__ import annotations


class Animal:
    pass


class Dog(Animal):
    pass


def check(obj: object) -> tuple[bool, bool]:
    """Compare isinstance (subclass-aware) vs exact type match."""
    return isinstance(obj, Animal), type(obj) is Animal


def isinstance_tuple(value: object) -> bool:
    """isinstance accepts a tuple of types -> match any of them."""
    return isinstance(value, (int, float))


if __name__ == "__main__":
    d = Dog()
    print(check(d))  # (True, False) -> Dog is an Animal, not exactly Animal
    print(check(Animal()))  # (True, True)
    print(isinstance_tuple(3.5))  # True
    print(isinstance(True, int))  # True -> bool subclasses int
