"""Reconstruct Itinerary  |  tier: neetcode150  |  Advanced Graphs

Given airline tickets [from, to], reconstruct the itinerary starting at "JFK",
using every ticket exactly once. If multiple are valid, return the
lexicographically smallest.

Approach: Hierholzer's algorithm for an Eulerian path. Sort each node's
destinations (visit smallest first). DFS, and append a node to the route only
after its edges are exhausted; reverse the route at the end.
Time: O(E log E)   Space: O(E)
"""
from __future__ import annotations

from collections import defaultdict


def find_itinerary(tickets: list[list[str]]) -> list[str]:
    """Return the lexicographically smallest valid itinerary from JFK."""
    graph: defaultdict[str, list[str]] = defaultdict(list)
    for src, dst in sorted(tickets, reverse=True):
        graph[src].append(dst)  # reverse-sorted -> pop() gives smallest

    route: list[str] = []
    stack = ["JFK"]
    while stack:
        while graph[stack[-1]]:
            stack.append(graph[stack[-1]].pop())
        route.append(stack.pop())
    return route[::-1]


if __name__ == "__main__":
    assert find_itinerary([["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]) == [
        "JFK",
        "MUC",
        "LHR",
        "SFO",
        "SJC",
    ]
    assert find_itinerary([["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]) == [
        "JFK",
        "ATL",
        "JFK",
        "SFO",
        "ATL",
        "SFO",
    ]
    print("ok")
