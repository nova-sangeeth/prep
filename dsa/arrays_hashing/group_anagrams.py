"""Group Anagrams  |  tier: core50, blind75, neetcode150  |  Arrays & Hashing

Group a list of strings so anagrams land in the same group.

Approach: key each word by its 26-letter count signature (tuple). Anagrams
share a signature. Sorting the word also works but is O(k log k) per word;
the count key is O(k).
Time: O(n * k)   Space: O(n * k)   (n words, k max length)
"""
from __future__ import annotations

from collections import defaultdict


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """Return anagrams grouped together (group order not significant)."""
    groups: defaultdict[tuple[int, ...], list[str]] = defaultdict(list)
    for word in strs:
        count = [0] * 26
        for ch in word:
            count[ord(ch) - ord("a")] += 1
        groups[tuple(count)].append(word)
    return list(groups.values())


if __name__ == "__main__":
    out = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    normalized = sorted(sorted(g) for g in out)
    assert normalized == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    print("ok")
