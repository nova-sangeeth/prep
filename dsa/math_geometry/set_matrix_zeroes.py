"""Set Matrix Zeroes  |  tier: blind75, neetcode150  |  Math & Geometry

If an element is 0, set its entire row and column to 0, in place, using O(1) extra
space.

Approach: use the first row and first column as marker storage. A separate flag
tracks whether the first column itself must be zeroed. Mark, then apply from the
inside out so markers are read before being overwritten.
Time: O(m * n)   Space: O(1)
"""
from __future__ import annotations


def set_zeroes(matrix: list[list[int]]) -> None:
    """Zero out rows/columns containing a 0, in place."""
    rows, cols = len(matrix), len(matrix[0])
    first_col_zero = False

    for r in range(rows):
        if matrix[r][0] == 0:
            first_col_zero = True
        for c in range(1, cols):
            if matrix[r][c] == 0:
                matrix[r][0] = 0  # mark row
                matrix[0][c] = 0  # mark column

    for r in range(1, rows):  # apply inner cells
        for c in range(1, cols):
            if matrix[r][0] == 0 or matrix[0][c] == 0:
                matrix[r][c] = 0
    if matrix[0][0] == 0:  # first row
        for c in range(cols):
            matrix[0][c] = 0
    if first_col_zero:  # first column
        for r in range(rows):
            matrix[r][0] = 0


if __name__ == "__main__":
    matrix = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    set_zeroes(matrix)
    assert matrix == [[1, 0, 1], [0, 0, 0], [1, 0, 1]]
    matrix2 = [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]
    set_zeroes(matrix2)
    assert matrix2 == [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]
    print("ok")
