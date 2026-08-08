"""Two Sum  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given an array and a target, return indices of the two numbers that add to
target. Exactly one solution; cannot reuse an element.

Approach: one pass with a hash map of value -> index. For each number, check
if its complement (target - num) was already seen.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def two_sum(nums: list[int], target: int) -> list[int]:
    """Return the two indices whose values sum to target."""
    seen: dict[int, int] = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []  # problem guarantees a solution


if __name__ == "__main__":
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum([3, 2, 4], 6) == [1, 2]
    assert two_sum([3, 3], 6) == [0, 1]
    print("ok")
