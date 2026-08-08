"""Jump Game II  |  tier: neetcode150  |  Greedy

Each value is the max jump length. Return the minimum number of jumps to reach the
last index (always reachable).

Approach: greedy BFS by "levels". Track the end of the current jump's reach; when
the scan passes it, take another jump and extend the reach to the farthest seen.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def jump(nums: list[int]) -> int:
    """Return the minimum number of jumps to reach the last index."""
    jumps = 0
    current_end = 0  # boundary of the current jump
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:  # must jump now
            jumps += 1
            current_end = farthest
    return jumps


if __name__ == "__main__":
    assert jump([2, 3, 1, 1, 4]) == 2
    assert jump([2, 3, 0, 1, 4]) == 2
    assert jump([0]) == 0
    print("ok")
