"""Partition Labels  |  tier: neetcode150  |  Greedy

Partition the string into as many parts as possible so each letter appears in at
most one part. Return the sizes of the parts in order.

Approach: record each letter's last index. Scan, extending the current part's end
to the farthest last-index of any letter seen. When the scan reaches that end, cut
a partition.
Time: O(n)   Space: O(1)  (26 letters)
"""
from __future__ import annotations


def partition_labels(text: str) -> list[int]:
    """Return the sizes of the maximal non-overlapping letter partitions."""
    last = {ch: i for i, ch in enumerate(text)}
    sizes: list[int] = []
    start = end = 0
    for i, ch in enumerate(text):
        end = max(end, last[ch])
        if i == end:  # every letter so far ends by here
            sizes.append(end - start + 1)
            start = i + 1
    return sizes


if __name__ == "__main__":
    assert partition_labels("ababcbacadefegdehijhklij") == [9, 7, 8]
    assert partition_labels("eccbbbbdec") == [10]
    print("ok")
