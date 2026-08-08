"""Min Cost Climbing Stairs  |  tier: neetcode150  |  1-D DP

Each step has a cost; from a step you climb 1 or 2 steps. You may start at index
0 or 1. Return the minimum cost to reach the top (past the last step).

Approach: dp[i] = min cost to STAND on step i = cost[i] + min(dp[i-1], dp[i-2]).
The answer is min(dp[last], dp[second-last]). Roll two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def min_cost_climbing_stairs(cost: list[int]) -> int:
    """Return the minimum cost to reach the top of the stairs."""
    n = len(cost)
    prev2, prev1 = 0, 0  # dp[i-2], dp[i-1]: cost to ARRIVE at step
    for i in range(2, n + 1):  # step n is the top (past last index)
        cur = min(prev1 + cost[i - 1], prev2 + cost[i - 2])
        prev2, prev1 = prev1, cur
    return prev1


if __name__ == "__main__":
    assert min_cost_climbing_stairs([10, 15, 20]) == 15
    assert min_cost_climbing_stairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]) == 6
    print("ok")
