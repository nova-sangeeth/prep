"""Pow(x, n)  |  tier: neetcode150  |  Math & Geometry

Compute x raised to the integer power n (n may be negative).

Approach: fast exponentiation by squaring. Halve the exponent each step, squaring
the base; multiply in the base on odd exponents. Invert for negative n.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def my_pow(x: float, n: int) -> float:
    """Return x ** n using exponentiation by squaring."""
    if n < 0:
        x = 1 / x
        n = -n
    result = 1.0
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result


if __name__ == "__main__":
    assert abs(my_pow(2.0, 10) - 1024.0) < 1e-9
    assert abs(my_pow(2.1, 3) - 9.261) < 1e-9
    assert abs(my_pow(2.0, -2) - 0.25) < 1e-9
    print("ok")
