"""House Robber  |  tier: core50, blind75, neetcode150  |  1-D DP

Maximize loot from houses in a row without robbing two adjacent houses.

Approach: dp[i] = max(dp[i-1], dp[i-2] + nums[i]) -- either skip house i or rob
it plus the best up to i-2. Roll two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def rob(nums: list[int]) -> int:
    """Return the maximum loot without robbing adjacent houses."""
    prev, curr = 0, 0  # best up to i-2 and i-1
    for num in nums:
        prev, curr = curr, max(curr, prev + num)
    return curr


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4  # rob 1 and 3
    assert rob([2, 7, 9, 3, 1]) == 12  # rob 2, 9, 1
    assert rob([]) == 0
    print("ok")
