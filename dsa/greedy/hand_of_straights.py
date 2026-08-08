"""Hand of Straights  |  tier: neetcode150  |  Greedy

Can the hand be rearranged into groups of size groupSize, each group being
consecutive integers? Return True/False.

Approach: count cards. Repeatedly start a group at the smallest remaining card and
remove the next groupSize-1 consecutive values; if any is missing, fail. A min-heap
(or sorted counts) finds the smallest efficiently.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


def is_n_straight_hand(hand: list[int], group_size: int) -> bool:
    """Return True if the hand splits into consecutive groups of group_size."""
    if len(hand) % group_size != 0:
        return False
    counts = Counter(hand)
    for start in sorted(counts):
        need = counts[start]
        if need <= 0:
            continue
        for card in range(start, start + group_size):
            if counts[card] < need:
                return False
            counts[card] -= need
    return True


if __name__ == "__main__":
    assert is_n_straight_hand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3) is True
    assert is_n_straight_hand([1, 2, 3, 4, 5], 4) is False
    print("ok")
