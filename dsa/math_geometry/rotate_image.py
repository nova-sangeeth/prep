"""Rotate Image  |  tier: blind75, neetcode150  |  Math & Geometry

Rotate an n x n matrix 90 degrees clockwise, in place.

Approach: transpose the matrix (swap across the main diagonal), then reverse each
row. The two operations together produce a clockwise rotation.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def rotate(matrix: list[list[int]]) -> None:
    """Rotate the matrix 90 degrees clockwise in place."""
    n = len(matrix)
    for r in range(n):  # transpose
        for c in range(r + 1, n):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    for row in matrix:  # reverse each row
        row.reverse()


if __name__ == "__main__":
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    rotate(matrix)
    assert matrix == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    single = [[1]]
    rotate(single)
    assert single == [[1]]
    print("ok")
