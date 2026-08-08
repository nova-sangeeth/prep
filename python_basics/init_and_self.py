"""Q11. What do `__init__` and `self` do?

__init__ : initializer, runs automatically on instance creation; sets attributes.
           (It does not create the object -- __new__ does -- it only initializes.)
self     : reference to the current instance; first param of instance methods,
           passed automatically by Python.
"""
from __future__ import annotations


class Dog:
    """A dog with a name and breed."""

    def __init__(self, name: str, breed: str) -> None:
        """Store instance attributes on self."""
        self.name = name
        self.breed = breed

    def bark(self) -> str:
        """Use self to access this instance's state."""
        return f"{self.name} says woof!"


if __name__ == "__main__":
    rex = Dog("Rex", "Lab")  # __init__ runs, self = rex
    print(rex.bark())  # self passed automatically
