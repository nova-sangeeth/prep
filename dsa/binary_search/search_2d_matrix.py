"""Search a 2D Matrix  |  tier: neetcode150  |  Binary Search

Each row is sorted, and the first value of each row exceeds the last value of
the previous row. Return True if target is present.

Approach: treat the m x n matrix as one sorted array of length m*n and binary
search it, mapping a flat index to (index // n, index % n).
Time: O(log(m*n))   Space: O(1)
"""
from __future__ import annotations


def search_matrix(matrix: list[list[int]], target: int) -> bool:
    """Return True if target is in the row/col-sorted matrix."""
    if not matrix or not matrix[0]:
        return False
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = left + (right - left) // 2
        val = matrix[mid // cols][mid % cols]
        if val == target:
            return True
        if val < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


if __name__ == "__main__":
    mat = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(mat, 3) is True
    assert search_matrix(mat, 13) is False
    print("ok")
