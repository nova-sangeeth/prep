"""Plus One  |  tier: neetcode150  |  Math & Geometry

Given a number as a digit array (most significant first), add one and return the
resulting digits.

Approach: walk from the least significant digit. A digit < 9 increments and we are
done; a 9 becomes 0 and carries. If every digit was 9, prepend a leading 1.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def plus_one(digits: list[int]) -> list[int]:
    """Increment the big-endian digit array by one."""
    for i in range(len(digits) - 1, -1, -1):
        if digits[i] < 9:
            digits[i] += 1
            return digits
        digits[i] = 0  # carry
    return [1] + digits  # all nines -> e.g. 999 -> 1000


if __name__ == "__main__":
    assert plus_one([1, 2, 3]) == [1, 2, 4]
    assert plus_one([4, 3, 9]) == [4, 4, 0]
    assert plus_one([9, 9, 9]) == [1, 0, 0, 0]
    print("ok")
