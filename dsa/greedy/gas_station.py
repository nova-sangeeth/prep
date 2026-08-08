"""Gas Station  |  tier: neetcode150  |  Greedy

gas[i] is fuel at station i; cost[i] is fuel to reach the next. Return the
starting index to complete the circuit once, or -1.

Approach: a solution exists iff total gas >= total cost. Greedily, if the running
tank goes negative at station i, no start in [start..i] works -- restart from
i+1.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def can_complete_circuit(gas: list[int], cost: list[int]) -> int:
    """Return a valid starting station index, or -1."""
    if sum(gas) < sum(cost):
        return -1
    start = 0
    tank = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:  # can't reach i+1 from current start
            start = i + 1
            tank = 0
    return start


if __name__ == "__main__":
    assert can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert can_complete_circuit([2, 3, 4], [3, 4, 3]) == -1
    print("ok")
