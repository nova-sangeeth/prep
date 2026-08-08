"""Q19. How does slicing work?

sequence[start:stop:step] -- stop is exclusive, bounds are clamped.
Works on any sequence (list, tuple, str, bytes). Negative indices count
from the end; step -1 reverses.
"""
from __future__ import annotations


def slice_demo() -> None:
    """Common slice patterns on a list."""
    s: list[int] = [0, 1, 2, 3, 4, 5]
    print(s[1:4])  # [1, 2, 3]
    print(s[:3])  # [0, 1, 2]
    print(s[3:])  # [3, 4, 5]
    print(s[::2])  # [0, 2, 4]
    print(s[::-1])  # [5, 4, 3, 2, 1, 0]
    print(s[-2:])  # [4, 5]


def reverse_string(text: str) -> str:
    """Reverse a string via slicing."""
    return text[::-1]


def slice_assignment() -> list[int]:
    """Slice assignment can change length (lists only)."""
    lst = [1, 2, 3, 4]
    lst[1:3] = [9, 9, 9]
    return lst  # [1, 9, 9, 9, 4]


if __name__ == "__main__":
    slice_demo()
    print(reverse_string("python"))
    print(slice_assignment())
