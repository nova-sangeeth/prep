"""Burst Balloons  |  tier: neetcode150  |  2-D DP

Bursting balloon i yields nums[i-1] * nums[i] * nums[i+1] coins (out-of-range = 1).
Return the maximum coins from bursting all balloons.

Approach: interval DP. Pad with 1s at both ends. dp[l][r] = best coins for the
open interval (l, r), choosing balloon k as the LAST to burst there, so its
neighbors are the fixed boundaries l and r. Build over increasing interval width.
Time: O(n^3)   Space: O(n^2)
"""
from __future__ import annotations


def max_coins(nums: list[int]) -> int:
    """Return the maximum coins obtainable by bursting all balloons."""
    balloons = [1] + nums + [1]
    n = len(balloons)
    dp = [[0] * n for _ in range(n)]
    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            for k in range(left + 1, right):  # k = last balloon burst in (left,right)
                coins = balloons[left] * balloons[k] * balloons[right]
                dp[left][right] = max(dp[left][right], dp[left][k] + coins + dp[k][right])
    return dp[0][n - 1]


if __name__ == "__main__":
    assert max_coins([3, 1, 5, 8]) == 167
    assert max_coins([1, 5]) == 10
    print("ok")
