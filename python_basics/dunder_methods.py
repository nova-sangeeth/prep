"""Q31. Dunder (magic) methods.

Double-underscore methods let your objects work with built-in syntax/operators.
__repr__  -> unambiguous dev string (aim: eval-able).
__str__   -> readable user string (falls back to __repr__).
__eq__    -> ==        __len__ -> len()        __add__ -> +
"""
from __future__ import annotations


class Money:
    """Amount in cents, demonstrating common dunders."""

    def __init__(self, cents: int) -> None:
        self.cents = cents

    def __repr__(self) -> str:
        return f"Money({self.cents})"

    def __str__(self) -> str:
        return f"${self.cents / 100:.2f}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Money) and other.cents == self.cents

    def __add__(self, other: "Money") -> "Money":
        return Money(self.cents + other.cents)


if __name__ == "__main__":
    a, b = Money(150), Money(250)
    print(repr(a))  # Money(150)
    print(str(a))  # $1.50
    print(a + b)  # $4.00  -> __add__ then __str__
    print(a == Money(150))  # True
