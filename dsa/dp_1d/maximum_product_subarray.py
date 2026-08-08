"""Maximum Product Subarray  |  tier: blind75, neetcode150  |  1-D DP

Return the largest product of any contiguous subarray.

Approach: track BOTH the running max and min products ending here -- a negative
number flips them, so today's min can become tomorrow's max. Reset on the current
element to allow starting fresh.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_product(nums: list[int]) -> int:
    """Return the maximum product of a contiguous subarray."""
    best = cur_max = cur_min = nums[0]
    for num in nums[1:]:
        candidates = (num, cur_max * num, cur_min * num)
        cur_max = max(candidates)
        cur_min = min(candidates)
        best = max(best, cur_max)
    return best


if __name__ == "__main__":
    assert max_product([2, 3, -2, 4]) == 6  # [2, 3]
    assert max_product([-2, 0, -1]) == 0
    assert max_product([-2, 3, -4]) == 24  # all three
    print("ok")
