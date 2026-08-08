"""Median of Two Sorted Arrays  |  tier: neetcode150  |  Binary Search

Return the median of two sorted arrays in O(log(min(m, n))).

Approach: binary search a partition of the SMALLER array. Choose cuts in both
arrays so the left side holds exactly half the elements and every left value <=
every right value (left_smaller <= right_larger and left_larger <=
right_smaller). The median comes from the boundary values.
Time: O(log(min(m, n)))   Space: O(1)
"""
from __future__ import annotations


def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    """Return the median of the two sorted arrays combined."""
    smaller, larger = nums1, nums2
    if len(smaller) > len(larger):
        smaller, larger = larger, smaller
    total = len(smaller) + len(larger)
    half = total // 2
    left, right = 0, len(smaller)
    while left <= right:
        i = (left + right) // 2  # cut in smaller
        j = half - i  # cut in larger
        left_smaller = smaller[i - 1] if i > 0 else float("-inf")
        right_smaller = smaller[i] if i < len(smaller) else float("inf")
        left_larger = larger[j - 1] if j > 0 else float("-inf")
        right_larger = larger[j] if j < len(larger) else float("inf")
        if left_smaller <= right_larger and left_larger <= right_smaller:
            if total % 2:
                return float(min(right_smaller, right_larger))
            return (max(left_smaller, left_larger) + min(right_smaller, right_larger)) / 2
        if left_smaller > right_larger:
            right = i - 1
        else:
            left = i + 1
    raise ValueError("inputs not sorted")


if __name__ == "__main__":
    assert find_median_sorted_arrays([1, 3], [2]) == 2.0
    assert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5
    assert find_median_sorted_arrays([], [1]) == 1.0
    print("ok")
