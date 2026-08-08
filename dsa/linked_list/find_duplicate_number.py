"""Find the Duplicate Number  |  tier: neetcode150  |  Linked List

An array of n+1 integers in [1, n] has exactly one repeated value. Find it
without modifying the array and in O(1) space.

Approach: treat indices as a linked list where i -> nums[i]. A duplicate creates
a cycle; Floyd's algorithm finds the cycle entrance, which is the duplicate.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def find_duplicate(nums: list[int]) -> int:
    """Return the single duplicated value using cycle detection."""
    slow, fast = nums[0], nums[0]
    while True:  # phase 1: find a meeting point
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]  # phase 2: find cycle entrance
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


if __name__ == "__main__":
    assert find_duplicate([1, 3, 4, 2, 2]) == 2
    assert find_duplicate([3, 1, 3, 4, 2]) == 3
    assert find_duplicate([2, 2, 2, 2, 2]) == 2
    print("ok")
