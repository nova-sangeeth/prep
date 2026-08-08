"""Maximum Subarray  |  tier: core50, blind75, neetcode150  |  Greedy

Return the largest sum of any contiguous subarray.

Approach: Kadane's algorithm. Track the best sum ending here: extend the previous
run or restart at the current element (whichever is larger). Keep the global max.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_sub_array(nums: list[int]) -> int:
    """Return the maximum contiguous subarray sum."""
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)  # restart vs extend
        best = max(best, current)
    return best


if __name__ == "__main__":
    assert max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6  # [4,-1,2,1]
    assert max_sub_array([1]) == 1
    assert max_sub_array([-3, -2, -1]) == -1
    print("ok")
