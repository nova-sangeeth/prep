"""Reverse Integer  |  tier: neetcode150  |  Bit Manipulation

Reverse the digits of a signed 32-bit integer. Return 0 if the result overflows
the signed 32-bit range [-2^31, 2^31 - 1].

Approach: pop digits with divmod and push onto the reversed value, checking the
32-bit bound before it is exceeded. Handle the sign separately.
Time: O(digits)   Space: O(1)
"""
from __future__ import annotations

INT_MIN, INT_MAX = -(2**31), 2**31 - 1


def reverse(x: int) -> int:
    """Return x with its digits reversed, or 0 on 32-bit overflow."""
    sign = -1 if x < 0 else 1
    x = abs(x)
    result = 0
    while x:
        x, digit = divmod(x, 10)
        result = result * 10 + digit
    result *= sign
    return result if INT_MIN <= result <= INT_MAX else 0


if __name__ == "__main__":
    assert reverse(123) == 321
    assert reverse(-123) == -321
    assert reverse(120) == 21
    assert reverse(1534236469) == 0  # overflow
    print("ok")
