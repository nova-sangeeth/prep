"""Cheapest Flights Within K Stops  |  tier: neetcode150  |  Advanced Graphs

Find the cheapest price from src to dst using at most k stops (k+1 edges), or -1.

Approach: Bellman-Ford limited to k+1 relaxation rounds. Each round relaxes all
edges using a SNAPSHOT of the previous round's costs, so no path uses more than
the allowed number of edges.
Time: O(k * E)   Space: O(V)
"""
from __future__ import annotations


def find_cheapest_price(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
    """Return the cheapest price within k stops, or -1."""
    cost = [float("inf")] * n
    cost[src] = 0
    for _ in range(k + 1):
        snapshot = cost[:]  # use last round's values only
        for u, v, price in flights:
            if snapshot[u] + price < cost[v]:
                cost[v] = snapshot[u] + price
    return -1 if cost[dst] == float("inf") else int(cost[dst])


if __name__ == "__main__":
    flights = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]
    assert find_cheapest_price(4, flights, 0, 3, 1) == 700
    flights2 = [[0, 1, 100], [1, 2, 100], [0, 2, 500]]
    assert find_cheapest_price(3, flights2, 0, 2, 1) == 200
    assert find_cheapest_price(3, flights2, 0, 2, 0) == 500
    print("ok")
