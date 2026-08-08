"""Two Sum II (Input Sorted)  |  tier: neetcode150  |  Two Pointers

Given a 1-indexed sorted array, return the 1-based indices of the two numbers
adding to target. O(1) extra space required.

Approach: two pointers from both ends. Sum too small -> move left up; too big ->
move right down. Sortedness guarantees this converges.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    """Return 1-based indices of the pair summing to target."""
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []


if __name__ == "__main__":
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3]
    assert two_sum_sorted([-1, 0], -1) == [1, 2]
    print("ok")
