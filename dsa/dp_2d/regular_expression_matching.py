"""Regular Expression Matching  |  tier: neetcode150  |  2-D DP

Implement matching with '.' (any single char) and '*' (zero or more of the
preceding element), covering the ENTIRE string.

Approach: dp over (i, j) into text and pattern. '*' either skips the pattern pair
(zero occurrences) or, if the preceding element matches text[i], consumes one
text char and stays on the same pattern position. Memoize.
Time: O(m * n)   Space: O(m * n)
"""
from __future__ import annotations

from functools import lru_cache


def is_match(text: str, pattern: str) -> bool:
    """Return True if the pattern matches the whole text."""

    @lru_cache(maxsize=None)
    def dp(i: int, j: int) -> bool:
        if j == len(pattern):
            return i == len(text)
        first = i < len(text) and pattern[j] in (text[i], ".")
        if j + 1 < len(pattern) and pattern[j + 1] == "*":
            return dp(i, j + 2) or (first and dp(i + 1, j))  # zero, or one more
        return first and dp(i + 1, j + 1)

    return dp(0, 0)


if __name__ == "__main__":
    assert is_match("aa", "a") is False
    assert is_match("aa", "a*") is True
    assert is_match("ab", ".*") is True
    assert is_match("mississippi", "mis*is*p*.") is False
    print("ok")
