"""Product of Array Except Self  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return an array where output[i] is the product of all elements except nums[i].
No division allowed; must run in O(n).

Approach: two passes. First fills each slot with the prefix product (product of
everything to the left). Second multiplies in the suffix product (everything to
the right) using a running variable.
Time: O(n)   Space: O(1)  (output array not counted)
"""
from __future__ import annotations


def product_except_self(nums: list[int]) -> list[int]:
    """Return products of all other elements, without division."""
    length = len(nums)
    result = [1] * length

    prefix = 1
    for i in range(length):
        result[i] = prefix
        prefix *= nums[i]

    suffix = 1
    for i in range(length - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]

    return result


if __name__ == "__main__":
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    print("ok")
