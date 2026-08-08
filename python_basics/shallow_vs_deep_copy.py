"""Q8. Shallow copy vs deep copy.

= assignment   -> no copy, another name for the same object.
copy.copy()    -> shallow: new outer object, nested objects shared.
copy.deepcopy()-> deep: recursively independent clone (slower, handles cycles).
"""
from __future__ import annotations

import copy


def compare() -> None:
    """Mutating a nested list shows up in the shallow copy but not the deep one."""
    original: list[list[int]] = [[1, 2], [3, 4]]
    shallow = copy.copy(original)
    deep = copy.deepcopy(original)

    original[0][0] = 99

    print("shallow:", shallow)  # [[99, 2], [3, 4]] -> nested shared
    print("deep:   ", deep)  # [[1, 2], [3, 4]]  -> independent


if __name__ == "__main__":
    compare()
