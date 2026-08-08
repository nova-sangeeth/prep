"""Daily Temperatures  |  tier: core50, neetcode150  |  Stack

For each day, how many days until a warmer temperature? 0 if none.

Approach: monotonic decreasing stack of indices waiting for a warmer day. When a
warmer temp arrives, pop every colder index and record the day gap.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def daily_temperatures(temperatures: list[int]) -> list[int]:
    """Return days-until-warmer for each day."""
    result = [0] * len(temperatures)
    stack: list[int] = []  # indices of unresolved days
    for i, temp in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temp:
            prev = stack.pop()
            result[prev] = i - prev
        stack.append(i)
    return result


if __name__ == "__main__":
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([30, 20, 10]) == [0, 0, 0]
    print("ok")
