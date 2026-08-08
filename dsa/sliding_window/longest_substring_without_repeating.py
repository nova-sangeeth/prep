"""Longest Substring Without Repeating Characters  |  tier: core50, blind75, neetcode150  |  Sliding Window

Return the length of the longest substring with all distinct characters.

Approach: sliding window with a map of char -> last index. When a repeat falls
inside the window, jump the left edge past its previous position. Window always
holds distinct chars.
Time: O(n)   Space: O(min(n, alphabet))
"""
from __future__ import annotations


def length_of_longest_substring(text: str) -> int:
    """Return length of the longest substring without repeating characters."""
    last_seen: dict[str, int] = {}
    left = 0
    best = 0
    for right, ch in enumerate(text):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3  # "abc"
    assert length_of_longest_substring("bbbbb") == 1  # "b"
    assert length_of_longest_substring("pwwkew") == 3  # "wke"
    assert length_of_longest_substring("") == 0
    print("ok")
