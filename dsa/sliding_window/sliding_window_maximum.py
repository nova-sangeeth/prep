"""Sliding Window Maximum  |  tier: neetcode150  |  Sliding Window

Return the maximum of each contiguous window of size k as it slides across nums.

Approach: monotonic decreasing deque of indices. Front always holds the current
window's max. Pop smaller values from the back before appending (they can never
be a future max), and drop the front when it slides out of the window.
Time: O(n)   Space: O(k)
"""
from __future__ import annotations

from collections import deque


def max_sliding_window(nums: list[int], k: int) -> list[int]:
    """Return the max of every size-k window."""
    dq: deque[int] = deque()  # indices, values decreasing
    result: list[int] = []
    for i, num in enumerate(nums):
        while dq and nums[dq[-1]] < num:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:  # front slid out of window
            dq.popleft()
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result


if __name__ == "__main__":
    assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert max_sliding_window([1], 1) == [1]
    print("ok")
