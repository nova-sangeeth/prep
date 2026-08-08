"""Permutation in String  |  tier: neetcode150  |  Sliding Window

Return True if text contains any permutation of pattern as a substring.

Approach: fixed-size sliding window of len(pattern) over text, comparing character
counts. Slide by adding the entering char and removing the leaving char; match
when the window's counts equal pattern's counts.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations

from collections import Counter


def check_inclusion(pattern: str, text: str) -> bool:
    """Return True if some permutation of pattern is a substring of text."""
    if len(pattern) > len(text):
        return False
    need = Counter(pattern)
    window = Counter(text[: len(pattern)])
    if window == need:
        return True
    for i in range(len(pattern), len(text)):
        window[text[i]] += 1  # add entering char
        left = text[i - len(pattern)]
        window[left] -= 1  # remove leaving char
        if window[left] == 0:
            del window[left]
        if window == need:
            return True
    return False


if __name__ == "__main__":
    assert check_inclusion("ab", "eidbaooo") is True  # "ba"
    assert check_inclusion("ab", "eidboaoo") is False
    assert check_inclusion("a", "a") is True
    print("ok")
