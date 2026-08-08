"""Number of 1 Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Return the number of set bits (Hamming weight) of an unsigned integer.

Approach: Brian Kernighan's trick. n & (n - 1) clears the lowest set bit; count
how many times until n becomes 0 -- loops once per set bit, not per total bit.
Time: O(set bits)   Space: O(1)
"""
from __future__ import annotations


def hamming_weight(n: int) -> int:
    """Return the count of set bits in n."""
    count = 0
    while n:
        n &= n - 1  # drop the lowest set bit
        count += 1
    return count


if __name__ == "__main__":
    assert hamming_weight(0b00000000000000000000000000001011) == 3
    assert hamming_weight(0b10000000000000000000000000000000) == 1
    assert hamming_weight(0) == 0
    print("ok")
