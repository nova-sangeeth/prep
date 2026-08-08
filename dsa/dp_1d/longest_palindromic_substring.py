"""Longest Palindromic Substring  |  tier: blind75, neetcode150  |  1-D DP

Return the longest substring that is a palindrome.

Approach: expand around centers. Each index (and each gap between indices) is a
potential palindrome center; expand outward while characters match. Track the
longest span found. 2n-1 centers.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def longest_palindrome(text: str) -> str:
    """Return the longest palindromic substring."""
    if not text:
        return ""
    start, end = 0, 0

    def expand(left: int, right: int) -> tuple[int, int]:
        while left >= 0 and right < len(text) and text[left] == text[right]:
            left -= 1
            right += 1
        return left + 1, right - 1  # last valid bounds

    for i in range(len(text)):
        for left, right in (expand(i, i), expand(i, i + 1)):  # odd, even centers
            if right - left > end - start:
                start, end = left, right
    return text[start : end + 1]


if __name__ == "__main__":
    assert longest_palindrome("babad") in {"bab", "aba"}
    assert longest_palindrome("cbbd") == "bb"
    assert longest_palindrome("a") == "a"
    print("ok")
