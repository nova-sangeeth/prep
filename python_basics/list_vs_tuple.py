"""Q1. Difference between a list and a tuple.

List  -> mutable, more methods, slower, not hashable.
Tuple -> immutable, fewer methods, faster, hashable (usable as dict key).
"""
from __future__ import annotations


def demo_mutability() -> None:
    """Show that a list can be mutated but a tuple cannot."""
    my_list: list[int] = [1, 2, 3]
    my_list[0] = 99  # OK
    my_list.append(4)  # OK

    my_tuple: tuple[int, ...] = (1, 2, 3)
    try:
        my_tuple[0] = 99  # TypeError
    except TypeError as exc:
        print("tuple is immutable:", exc)


def tuple_as_dict_key() -> dict[tuple[int, int], str]:
    """Tuples are hashable, so they can be dict keys; lists cannot."""
    return {(0, 0): "origin", (1, 2): "point"}


if __name__ == "__main__":
    demo_mutability()
    print(tuple_as_dict_key())
