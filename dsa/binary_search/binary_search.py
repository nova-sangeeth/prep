"""Binary Search  |  tier: core50, neetcode150  |  Binary Search

Return the index of target in a sorted array, or -1 if absent.

Approach: maintain [left, right]; compare the midpoint to target and discard
half each step. Use left + (right - left) // 2 to avoid overflow in other
languages.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def search(nums: list[int], target: int) -> int:
    """Return index of target, or -1."""
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


if __name__ == "__main__":
    assert search([-1, 0, 3, 5, 9, 12], 9) == 4
    assert search([-1, 0, 3, 5, 9, 12], 2) == -1
    assert search([], 1) == -1
    print("ok")
