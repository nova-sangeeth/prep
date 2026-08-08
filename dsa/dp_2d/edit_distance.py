"""Edit Distance  |  tier: blind75, neetcode150  |  2-D DP

Return the minimum number of insert/delete/replace operations to convert word1
into word2 (Levenshtein distance).

Approach: dp[i][j] = edits to turn word1[:i] into word2[:j]. If chars match, carry
the diagonal; else 1 + min(delete, insert, replace). Roll one row.
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def min_distance(word1: str, word2: str) -> int:
    """Return the edit distance between word1 and word2."""
    prev = list(range(len(word2) + 1))  # transform "" -> word2[:j] = j inserts
    for i in range(1, len(word1) + 1):
        curr = [i] + [0] * len(word2)  # transform word1[:i] -> "" = i deletes
        for j in range(1, len(word2) + 1):
            if word1[i - 1] == word2[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[len(word2)]


if __name__ == "__main__":
    assert min_distance("horse", "ros") == 3
    assert min_distance("intention", "execution") == 5
    assert min_distance("", "abc") == 3
    print("ok")
