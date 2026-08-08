"""Network Delay Time  |  tier: neetcode150  |  Advanced Graphs

Signals travel along directed weighted edges from node k. Return the time for all
n nodes to receive the signal, or -1 if some node is unreachable.

Approach: Dijkstra's shortest path from k. The answer is the maximum shortest
distance among all nodes (the last to be reached).
Time: O(E log V)   Space: O(V + E)
"""
from __future__ import annotations

import heapq
from collections import defaultdict


def network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    """Return the time for all nodes to receive the signal, or -1."""
    graph: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
    for src, dst, weight in times:
        graph[src].append((dst, weight))

    dist: dict[int, int] = {}
    heap: list[tuple[int, int]] = [(0, k)]
    while heap:
        delay, node = heapq.heappop(heap)
        if node in dist:
            continue
        dist[node] = delay
        for neighbor, weight in graph[node]:
            if neighbor not in dist:
                heapq.heappush(heap, (delay + weight, neighbor))

    return max(dist.values()) if len(dist) == n else -1


if __name__ == "__main__":
    assert network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2
    assert network_delay_time([[1, 2, 1]], 2, 1) == 1
    assert network_delay_time([[1, 2, 1]], 2, 2) == -1
    print("ok")
