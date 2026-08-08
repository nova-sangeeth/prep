"""Longest Repeating Character Replacement  |  tier: core50, blind75, neetcode150  |  Sliding Window

You may replace at most k characters. Return the length of the longest substring
of a single repeated letter achievable after replacements.

Approach: sliding window tracking counts. A window is valid when
(window_len - count_of_most_frequent_char) <= k -- the non-majority chars are
the ones to replace. Grow right; shrink left when invalid.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations

from collections import defaultdict


def character_replacement(text: str, k: int) -> int:
    """Return longest single-char run achievable with <=k replacements."""
    counts: defaultdict[str, int] = defaultdict(int)
    left = 0
    max_freq = 0
    best = 0
    for right, ch in enumerate(text):
        counts[ch] += 1
        max_freq = max(max_freq, counts[ch])
        while (right - left + 1) - max_freq > k:
            counts[text[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    assert character_replacement("ABAB", 2) == 4
    assert character_replacement("AABABBA", 1) == 4
    assert character_replacement("", 0) == 0
    print("ok")
