"""Longest Common Subsequence  |  tier: blind75, neetcode150  |  2-D DP

Return the length of the longest subsequence common to both strings (characters
in order, not necessarily contiguous).

Approach: dp[i][j] = LCS of text1[i:] and text2[j:]. If chars match, 1 + diagonal;
else max of skipping one char from either string. Use two rolling rows.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def longest_common_subsequence(text1: str, text2: str) -> int:
    """Return the length of the longest common subsequence."""
    prev = [0] * (len(text2) + 1)
    for i in range(len(text1) - 1, -1, -1):
        curr = [0] * (len(text2) + 1)
        for j in range(len(text2) - 1, -1, -1):
            if text1[i] == text2[j]:
                curr[j] = 1 + prev[j + 1]
            else:
                curr[j] = max(prev[j], curr[j + 1])
        prev = curr
    return prev[0]


if __name__ == "__main__":
    assert longest_common_subsequence("abcde", "ace") == 3  # "ace"
    assert longest_common_subsequence("abc", "abc") == 3
    assert longest_common_subsequence("abc", "def") == 0
    print("ok")
