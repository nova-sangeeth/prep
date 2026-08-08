"""Reverse Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Reverse the bits of a 32-bit unsigned integer.

Approach: shift the result left and OR in the input's lowest bit, 32 times. Each
step peels one bit off the input and appends it to the (reversed) output.
Time: O(32)   Space: O(1)
"""
from __future__ import annotations


def reverse_bits(n: int) -> int:
    """Return the 32-bit reversal of n."""
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result


if __name__ == "__main__":
    assert reverse_bits(0b00000010100101000001111010011100) == 964176192
    assert reverse_bits(0b11111111111111111111111111111101) == 3221225471
    print("ok")
