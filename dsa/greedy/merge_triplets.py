"""Merge Triplets to Form Target  |  tier: neetcode150  |  Greedy

You may take the element-wise max of any chosen triplets. Return True if the
target triplet can be formed.

Approach: a triplet is usable only if no component exceeds the target (else it
would overshoot). Among usable triplets, collect which positions already equal the
target value; success needs all three positions covered.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def merge_triplets(triplets: list[list[int]], target: list[int]) -> bool:
    """Return True if target can be built from element-wise maxes."""
    matched: set[int] = set()
    for triplet in triplets:
        if any(triplet[i] > target[i] for i in range(3)):
            continue  # would overshoot -> unusable
        for i in range(3):
            if triplet[i] == target[i]:
                matched.add(i)
    return len(matched) == 3


if __name__ == "__main__":
    assert merge_triplets([[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]) is True
    assert merge_triplets([[3, 4, 5], [4, 5, 6]], [3, 2, 5]) is False
    print("ok")
