"""Valid Anagram  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Given strings word and candidate, return True if candidate is an anagram of word
(same letters, same counts).

Approach: compare character frequency maps. Equal length is a prerequisite;
then equal Counters means anagram.
Time: O(n)   Space: O(1)  (bounded alphabet)
"""
from __future__ import annotations

from collections import Counter


def is_anagram(word: str, candidate: str) -> bool:
    """Return True if candidate is an anagram of word."""
    if len(word) != len(candidate):
        return False
    return Counter(word) == Counter(candidate)


if __name__ == "__main__":
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("", "") is True
    print("ok")
