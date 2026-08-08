"""Time Based Key-Value Store  |  tier: neetcode150  |  Binary Search

Design a store: set(key, value, timestamp), and get(key, timestamp) returning the
value with the largest stored timestamp <= the query (or "" if none). Timestamps
for a key are strictly increasing.

Approach: per key, append (timestamp, value) -> the list is sorted by timestamp.
get binary-searches for the rightmost timestamp <= query.
Time: set O(1), get O(log n)   Space: O(n)
"""
from __future__ import annotations

from collections import defaultdict


class TimeMap:
    """Key -> time-ordered (timestamp, value) history."""

    def __init__(self) -> None:
        self._store: defaultdict[str, list[tuple[int, str]]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        """Append a value with its timestamp (timestamps increase per key)."""
        self._store[key].append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        """Return the value at the greatest timestamp <= the query."""
        history = self._store[key]
        left, right = 0, len(history) - 1
        result = ""
        while left <= right:
            mid = left + (right - left) // 2
            if history[mid][0] <= timestamp:
                result = history[mid][1]
                left = mid + 1  # search for a later valid time
            else:
                right = mid - 1
        return result


if __name__ == "__main__":
    tm = TimeMap()
    tm.set("foo", "bar", 1)
    assert tm.get("foo", 1) == "bar"
    assert tm.get("foo", 3) == "bar"
    tm.set("foo", "bar2", 4)
    assert tm.get("foo", 4) == "bar2"
    assert tm.get("foo", 5) == "bar2"
    assert tm.get("foo", 0) == ""
    print("ok")
