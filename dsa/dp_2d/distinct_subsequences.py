"""Distinct Subsequences  |  tier: neetcode150  |  2-D DP

Return the number of distinct subsequences of source that equal target.

Approach: dp[j] = ways to form target[:j]. Iterate source; update j from high to
low so each source-char is used once per position. When source[i] == target[j-1],
dp[j] += dp[j-1].
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def num_distinct(source: str, target: str) -> int:
    """Return the count of subsequences of source equal to target."""
    dp = [1] + [0] * len(target)  # dp[0] = 1: empty target matches once
    for ch in source:
        for j in range(len(target), 0, -1):  # reverse -> don't reuse this char
            if ch == target[j - 1]:
                dp[j] += dp[j - 1]
    return dp[len(target)]


if __name__ == "__main__":
    assert num_distinct("rabbbit", "rabbit") == 3
    assert num_distinct("babgbag", "bag") == 5
    assert num_distinct("abc", "") == 1
    print("ok")
