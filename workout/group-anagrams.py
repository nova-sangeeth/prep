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
    result = {}
    for item in strs:
        word = "".join(sorted(item))
        if item not in result:
            result[item] = []

        result[item].append(word)
    print(result)
    return list(result.values())


def group_anagrams_optimized(strs: list[str]) -> list[list[str]]:
    """Reture anagrams grouped together ()"""
    result = {}
    
    for item in strs:
        counts = [0] * 26
        for ch in item:
            start = ord("a")
            end = ord(ch)
            idx = end - start + 1

            counts[idx] += 1
        key = tuple(counts)

        if key not in result:
            result[key] = []

        result[key].append(item)
        print(result)
    
    return list(result.values())


if __name__ == "__main__":
    # out = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    out = group_anagrams_optimized(["eat", "tea", "tan", "ate", "nat", "bat"])
    print(out)
