"""Contains Duplicate  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given an integer array, return True if any value appears at least twice.

Approach: track seen values in a set; first repeat -> True. A set membership
test is O(1) average, so one pass suffices.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def contains_duplicate(nums: list[int]) -> bool:
    """Return True if any element repeats."""
    seen: set[int] = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False


if __name__ == "__main__":
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3, 4]) is False
    assert contains_duplicate([]) is False
    print("ok")
