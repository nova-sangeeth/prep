"""Interleaving String  |  tier: neetcode150  |  2-D DP

Return True if s3 is formed by interleaving s1 and s2 (preserving each one's
character order).

Approach: dp[i][j] = can s3[:i+j] be formed from s1[:i] and s2[:j]. Each step
takes the next char from s1 (if it matches) or from s2. Roll one row.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def is_interleave(s1: str, s2: str, s3: str) -> bool:
    """Return True if s3 is an interleaving of s1 and s2."""
    m, n = len(s1), len(s2)
    if m + n != len(s3):
        return False
    dp = [False] * (n + 1)
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                dp[j] = True
            elif i == 0:
                dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
            elif j == 0:
                dp[j] = dp[j] and s1[i - 1] == s3[i - 1]
            else:
                dp[j] = (dp[j] and s1[i - 1] == s3[i + j - 1]) or (dp[j - 1] and s2[j - 1] == s3[i + j - 1])
    return dp[n]


if __name__ == "__main__":
    assert is_interleave("aabcc", "dbbca", "aadbbcbcac") is True
    assert is_interleave("aabcc", "dbbca", "aadbbbaccc") is False
    assert is_interleave("", "", "") is True
    print("ok")
