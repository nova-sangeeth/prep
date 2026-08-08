"""Search in Rotated Sorted Array  |  tier: core50, blind75, neetcode150  |  Binary Search

A sorted array of distinct values was rotated. Return the index of target, or -1,
in O(log n).

Approach: binary search. At each step one half [left, mid] or [mid, right] is
sorted. Decide which half is sorted, then check whether target lies within that
sorted range to pick the side to keep.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def search(nums: list[int], target: int) -> int:
    """Return index of target in the rotated array, or -1."""
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        if nums[left] <= nums[mid]:  # left half sorted
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # right half sorted
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1


if __name__ == "__main__":
    assert search([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search([1], 1) == 0
    print("ok")
