"""Q34. The collections module.

Counter       -> count hashables, .most_common().
defaultdict   -> dict with auto default for missing keys.
namedtuple    -> lightweight immutable record with named fields.
deque         -> fast O(1) appends/pops at both ends.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque, namedtuple


def counter_demo() -> list[tuple[str, int]]:
    """Tally items and return the two most common."""
    return Counter("mississippi").most_common(2)


def defaultdict_demo() -> dict[str, list[int]]:
    """Group values without checking key existence first."""
    groups: defaultdict[str, list[int]] = defaultdict(list)
    for n in range(6):
        groups["even" if n % 2 == 0 else "odd"].append(n)
    return dict(groups)


def namedtuple_demo() -> int:
    """Access fields by name instead of index."""
    Point = namedtuple("Point", ["x", "y"])
    p = Point(3, 4)
    return p.x + p.y


def deque_demo() -> deque[int]:
    """Append/pop efficiently at both ends."""
    dq: deque[int] = deque([2, 3])
    dq.appendleft(1)
    dq.append(4)
    return dq


if __name__ == "__main__":
    print(counter_demo())  # [('i', 4), ('s', 4)]
    print(defaultdict_demo())  # {'even': [0,2,4], 'odd': [1,3,5]}
    print(namedtuple_demo())  # 7
    print(deque_demo())  # deque([1, 2, 3, 4])
