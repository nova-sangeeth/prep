"""Missing Number  |  tier: core50, blind75, neetcode150  |  Bit Manipulation

An array contains n distinct numbers from the range [0, n]. Return the missing one.

Approach: XOR all indices 0..n with all values. Each present value cancels with its
index; the leftover is the missing number. (Gauss sum n(n+1)/2 minus the array sum
also works.)
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def missing_number(nums: list[int]) -> int:
    """Return the missing number in [0, n]."""
    result = len(nums)  # start with n (the index with no value)
    for i, num in enumerate(nums):
        result ^= i ^ num
    return result


if __name__ == "__main__":
    assert missing_number([3, 0, 1]) == 2
    assert missing_number([0, 1]) == 2
    assert missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8
    print("ok")
