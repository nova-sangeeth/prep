"""Q26. Inheritance and super().

A subclass reuses/extends a parent. super() calls the parent implementation,
which is the correct way to chain __init__ and methods (works with MRO).
"""
from __future__ import annotations


class Animal:
    """Base class."""

    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return f"{self.name} makes a sound"


class Dog(Animal):
    """Subclass that extends the parent."""

    def __init__(self, name: str, breed: str) -> None:
        super().__init__(name)  # chain parent __init__
        self.breed = breed

    def speak(self) -> str:  # override
        base = super().speak()  # reuse parent result
        return f"{base} (woof)"


if __name__ == "__main__":
    d = Dog("Rex", "Lab")
    print(d.speak())
    print(isinstance(d, Animal))  # True
    print(issubclass(Dog, Animal))  # True
