"""House Robber II  |  tier: blind75, neetcode150  |  1-D DP

Houses are arranged in a CIRCLE, so the first and last are adjacent. Maximize
loot without robbing two adjacent houses.

Approach: the circular constraint means house 0 and house n-1 can't both be
robbed. Run the linear House Robber twice -- on houses [0..n-2] and [1..n-1] --
and take the better. Handle the single-house case directly.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def _rob_linear(nums: list[int]) -> int:
    prev, curr = 0, 0
    for num in nums:
        prev, curr = curr, max(curr, prev + num)
    return curr


def rob(nums: list[int]) -> int:
    """Return max loot for houses in a circle."""
    if len(nums) == 1:
        return nums[0]
    return max(_rob_linear(nums[:-1]), _rob_linear(nums[1:]))


if __name__ == "__main__":
    assert rob([2, 3, 2]) == 3  # can't rob both ends
    assert rob([1, 2, 3, 1]) == 4
    assert rob([1, 2, 3]) == 3
    assert rob([5]) == 5
    print("ok")
