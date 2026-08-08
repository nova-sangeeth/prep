"""Q24. Is Python pass-by-value or pass-by-reference?

Neither -- it is "pass-by-object-reference" (call by sharing).
- Mutating a mutable arg in place is visible to the caller.
- Reassigning the parameter, or passing an immutable, is not.
"""
from __future__ import annotations


def mutate(lst: list[int]) -> None:
    """Mutates the same list object -> caller sees the change."""
    lst.append(4)


def reassign(lst: list[int]) -> None:
    """Rebinds the local name only -> caller unaffected."""
    lst = [9, 9]


def change_int(x: int) -> None:
    """int is immutable -> creates a new object, caller unaffected."""
    x += 1


if __name__ == "__main__":
    nums = [1, 2, 3]
    mutate(nums)
    print(nums)  # [1, 2, 3, 4]
    reassign(nums)
    print(nums)  # still [1, 2, 3, 4]

    n = 5
    change_int(n)
    print(n)  # still 5
