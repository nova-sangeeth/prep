"""Word Break  |  tier: core50, blind75, neetcode150  |  1-D DP

Return True if text can be segmented into a space-separated sequence of dictionary
words (words reusable).

Approach: dp[i] = True if text[:i] is segmentable. For each end i, check every
split j: if dp[j] and text[j:i] is a word, then dp[i] is True.
Time: O(n^2 * wordlen)   Space: O(n)
"""
from __future__ import annotations


def word_break(text: str, word_dict: list[str]) -> bool:
    """Return True if text can be segmented into dictionary words."""
    words = set(word_dict)
    dp = [False] * (len(text) + 1)
    dp[0] = True  # empty prefix is segmentable
    for i in range(1, len(text) + 1):
        for j in range(i):
            if dp[j] and text[j:i] in words:
                dp[i] = True
                break
    return dp[len(text)]


if __name__ == "__main__":
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("applepenapple", ["apple", "pen"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    print("ok")
