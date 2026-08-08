"""Minimum Window Substring  |  tier: blind75, neetcode150  |  Sliding Window

Return the smallest substring of text containing every character of pattern (with
multiplicity). Empty string if none.

Approach: grow the right edge until the window covers pattern (track how many required
chars are satisfied via a 'have/need' counter). Then shrink from the left while
still valid, recording the smallest window.
Time: O(n)   Space: O(unique chars in t)
"""
from __future__ import annotations

from collections import Counter


def min_window(text: str, pattern: str) -> str:
    """Return the minimum window in text covering all chars of pattern."""
    if not pattern or not text:
        return ""
    need = Counter(pattern)
    required = len(need)
    have = 0
    window: dict[str, int] = {}
    best_len = float("inf")
    best = (0, 0)
    left = 0
    for right, ch in enumerate(text):
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            have += 1
        while have == required:
            if right - left + 1 < best_len:
                best_len = right - left + 1
                best = (left, right)
            window[text[left]] -= 1
            if text[left] in need and window[text[left]] < need[text[left]]:
                have -= 1
            left += 1
    start, end = best
    return text[start : end + 1] if best_len != float("inf") else ""


if __name__ == "__main__":
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""
    print("ok")
