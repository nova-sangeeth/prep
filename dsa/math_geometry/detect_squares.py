"""Detect Squares  |  tier: neetcode150  |  Math & Geometry

Design a structure: add(point) and count(point) returning the number of
axis-aligned squares that can be formed using the query point as one corner plus
three previously added points.

Approach: keep a frequency count of points. For a query, iterate candidate
diagonal points (sharing neither x nor y, forming a square's opposite corner);
multiply the counts of the two remaining corners.
Time: add O(1); count O(n) over distinct points   Space: O(n)
"""
from __future__ import annotations

from collections import Counter


class DetectSquares:
    """Counts axis-aligned squares formed with stored points."""

    def __init__(self) -> None:
        self._counts: Counter[tuple[int, int]] = Counter()

    def add(self, point: list[int]) -> None:
        """Add a point (duplicates allowed)."""
        self._counts[(point[0], point[1])] += 1

    def count(self, point: list[int]) -> int:
        """Count squares using point plus three stored points."""
        px, py = point
        total = 0
        for (x, y), freq in list(self._counts.items()):
            if abs(x - px) == abs(y - py) and x != px and y != py:
                total += freq * self._counts[(px, y)] * self._counts[(x, py)]
        return total


if __name__ == "__main__":
    ds = DetectSquares()
    for point in ([3, 10], [11, 2], [3, 2]):
        ds.add(point)
    assert ds.count([11, 10]) == 1
    assert ds.count([14, 8]) == 0
    ds.add([11, 2])  # second copy
    assert ds.count([11, 10]) == 2
    print("ok")
