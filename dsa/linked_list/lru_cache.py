"""LRU Cache  |  tier: core50, blind75, neetcode150  |  Linked List

Design a cache with O(1) get and put that evicts the least-recently-used key
when capacity is exceeded.

Approach: an OrderedDict keeps insertion/use order. On access, move the key to
the most-recent end; on overflow, pop the least-recent (front). (A manual
hashmap + doubly linked list achieves the same; OrderedDict encapsulates it.)
Time: O(1) per op   Space: O(capacity)
"""
from __future__ import annotations

from collections import OrderedDict


class LRUCache:
    """Fixed-capacity least-recently-used cache."""

    def __init__(self, capacity: int) -> None:
        self._cap = capacity
        self._data: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        """Return the value and mark key most-recently-used, or -1 if absent."""
        if key not in self._data:
            return -1
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: int, value: int) -> None:
        """Insert/update, evicting the LRU entry if over capacity."""
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self._cap:
            self._data.popitem(last=False)  # evict least recent


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1  # 1 now most recent
    cache.put(3, 3)  # evicts 2
    assert cache.get(2) == -1
    cache.put(4, 4)  # evicts 1
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4
    print("ok")
