"""Jump Game  |  tier: core50, blind75, neetcode150  |  Greedy

Each value is the max jump length from that index. Return True if you can reach
the last index from index 0.

Approach: greedy. Track the farthest reachable index while scanning. If the
current index ever exceeds it, you are stuck.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def can_jump(nums: list[int]) -> bool:
    """Return True if the last index is reachable."""
    farthest = 0
    for i, jump in enumerate(nums):
        if i > farthest:
            return False  # cannot even reach index i
        farthest = max(farthest, i + jump)
    return True


if __name__ == "__main__":
    assert can_jump([2, 3, 1, 1, 4]) is True
    assert can_jump([3, 2, 1, 0, 4]) is False
    assert can_jump([0]) is True
    print("ok")
