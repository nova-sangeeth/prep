"""Target Sum  |  tier: neetcode150  |  2-D DP

Assign '+' or '-' to each number so the signed sum equals target. Return the
number of ways.

Approach: DP over running sums. Map each reachable sum to its number of ways;
each number branches every current sum into +num and -num.
Time: O(n * range)   Space: O(range)
"""
from __future__ import annotations

from collections import defaultdict


def find_target_sum_ways(nums: list[int], target: int) -> int:
    """Return the number of sign assignments yielding target."""
    ways: dict[int, int] = {0: 1}
    for num in nums:
        nxt: defaultdict[int, int] = defaultdict(int)
        for total, count in ways.items():
            nxt[total + num] += count
            nxt[total - num] += count
        ways = nxt
    return ways.get(target, 0)


if __name__ == "__main__":
    assert find_target_sum_ways([1, 1, 1, 1, 1], 3) == 5
    assert find_target_sum_ways([1], 1) == 1
    assert find_target_sum_ways([1], 2) == 0
    print("ok")
