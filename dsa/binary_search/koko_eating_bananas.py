"""Koko Eating Bananas  |  tier: core50, neetcode150  |  Binary Search

Koko eats at speed k bananas/hour, one pile per hour (rounding up). Return the
minimum k that finishes all piles within h hours.

Approach: binary search on the ANSWER (speed) in [1, max(piles)]. hours(k) is
monotonic decreasing in k, so search for the smallest feasible k.
Time: O(n log(max_pile))   Space: O(1)
"""
from __future__ import annotations

import math


def min_eating_speed(piles: list[int], h: int) -> int:
    """Return the minimum eating speed to finish within h hours."""

    def hours_needed(speed: int) -> int:
        return sum(math.ceil(pile / speed) for pile in piles)

    left, right = 1, max(piles)
    while left < right:
        mid = left + (right - left) // 2
        if hours_needed(mid) <= h:
            right = mid  # feasible -> try slower
        else:
            left = mid + 1
    return left


if __name__ == "__main__":
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23
    print("ok")
