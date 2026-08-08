"""Partition Equal Subset Sum  |  tier: neetcode150  |  1-D DP

Return True if the array can be split into two subsets with equal sum.

Approach: this is a 0/1 subset-sum for target = total / 2. Use a boolean set of
reachable sums; for each number, add it to every previously reachable sum. An odd
total is immediately impossible.
Time: O(n * sum)   Space: O(sum)
"""
from __future__ import annotations


def can_partition(nums: list[int]) -> bool:
    """Return True if nums splits into two equal-sum subsets."""
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    reachable: set[int] = {0}
    for num in nums:
        reachable |= {partial_sum + num for partial_sum in reachable if partial_sum + num <= target}
        if target in reachable:
            return True
    return target in reachable


if __name__ == "__main__":
    assert can_partition([1, 5, 11, 5]) is True  # [1,5,5] and [11]
    assert can_partition([1, 2, 3, 5]) is False
    assert can_partition([1, 1]) is True
    print("ok")
