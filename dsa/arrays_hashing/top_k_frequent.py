"""Top K Frequent Elements  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return the k most frequent elements.

Approach: bucket sort by frequency. Index buckets by count (0..n), then walk
from highest count down collecting k elements. Avoids a full sort / heap.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequent values (any order)."""
    counts = Counter(nums)
    buckets: list[list[int]] = [[] for _ in range(len(nums) + 1)]
    for value, freq in counts.items():
        buckets[freq].append(value)

    result: list[int] = []
    for freq in range(len(buckets) - 1, 0, -1):
        for value in buckets[freq]:
            result.append(value)
            if len(result) == k:
                return result
    return result


if __name__ == "__main__":
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    print("ok")
