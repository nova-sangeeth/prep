"""Q30. Method Resolution Order (MRO) and the diamond problem.

MRO is the order Python searches base classes for an attribute/method.
CPython uses the C3 linearization algorithm. super() follows the MRO,
so the diamond inheritance pattern calls each ancestor exactly once.
"""
from __future__ import annotations


class A:
    def whoami(self) -> str:
        return "A"


class B(A):
    def whoami(self) -> str:
        return "B -> " + super().whoami()


class C(A):
    def whoami(self) -> str:
        return "C -> " + super().whoami()


class D(B, C):  # diamond: D -> B -> C -> A
    def whoami(self) -> str:
        return "D -> " + super().whoami()


if __name__ == "__main__":
    print([cls.__name__ for cls in D.__mro__])  # ['D', 'B', 'C', 'A', 'object']
    print(D().whoami())  # D -> B -> C -> A
