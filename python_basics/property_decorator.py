"""Q32. The @property decorator.

@property exposes a method as an attribute -> computed/validated access
without changing the public API. Add a setter for controlled writes.
Pythonic alternative to Java-style getX()/setX().
"""
from __future__ import annotations


class Temperature:
    """Stores Celsius, exposes a validated property and a computed one."""

    def __init__(self, celsius: float) -> None:
        self._celsius = celsius  # leading _ = internal

    @property
    def celsius(self) -> float:
        """Read access looks like a plain attribute."""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        """Validate on write."""
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Computed, read-only property."""
        return self._celsius * 9 / 5 + 32


if __name__ == "__main__":
    t = Temperature(25)
    print(t.celsius, t.fahrenheit)  # 25 77.0
    t.celsius = 30  # uses setter
    print(t.fahrenheit)  # 86.0
    try:
        t.celsius = -300
    except ValueError as exc:
        print("rejected:", exc)
