"""Q13. map, filter, reduce.

map(f, it)    -> apply f to each item (lazy iterator).
filter(f, it) -> keep items where f is truthy (lazy iterator).
reduce(f, it) -> fold to a single value (functools.reduce).
Comprehensions / sum() are often the more Pythonic choice.
"""
from __future__ import annotations

from functools import reduce


def demo() -> None:
    """Show each of the three plus the comprehension alternatives."""
    nums = [1, 2, 3, 4]

    print(list(map(lambda x: x * x, nums)))  # [1, 4, 9, 16]
    print(list(filter(lambda x: x % 2 == 0, nums)))  # [2, 4]
    print(reduce(lambda a, b: a + b, nums))  # 10

    # Pythonic equivalents
    print([x * x for x in nums])
    print([x for x in nums if x % 2 == 0])
    print(sum(nums))


if __name__ == "__main__":
    demo()
