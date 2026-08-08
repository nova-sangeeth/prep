"""Q2. Mutable vs immutable types.

Mutable   : list, dict, set, bytearray  -> changed in place (same id).
Immutable : int, float, str, tuple, frozenset, bytes, bool -> "change" makes new object.

Practical impact: only immutable objects are hashable, and mutable default
arguments are a classic bug.
"""
from __future__ import annotations


def shows_identity_change() -> None:
    """Immutable str gets a new id on '+='; mutable list keeps its id."""
    text = "hello"
    before = id(text)
    text += " world"  # new object
    print("str id changed:", before != id(text))

    nums: list[int] = [1, 2]
    before = id(nums)
    nums.append(3)  # same object
    print("list id same:", before == id(nums))


def mutable_default_bug(items: list[int] | None = None) -> list[int]:
    """Correct pattern: use None sentinel, never a mutable default literal."""
    if items is None:
        items = []
    items.append(1)
    return items


if __name__ == "__main__":
    shows_identity_change()
    print(mutable_default_bug())
    print(mutable_default_bug())  # independent list each call
