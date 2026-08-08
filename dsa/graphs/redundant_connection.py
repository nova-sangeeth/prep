"""Redundant Connection  |  tier: neetcode150  |  Graphs

A tree had one extra edge added, forming exactly one cycle. Return the edge that
can be removed (the last one in input order that closes a cycle).

Approach: union-find. Process edges; for each, if both endpoints already share a
root, that edge closes the cycle -> return it. Otherwise union them.
Time: O(n * alpha(n))   Space: O(n)
"""
from __future__ import annotations


def find_redundant_connection(edges: list[list[int]]) -> list[int]:
    """Return the redundant edge forming a cycle."""
    parent = list(range(len(edges) + 1))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]  # path compression
            node = parent[node]
        return node

    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a == root_b:
            return [node_a, node_b]  # already connected -> cycle edge
        parent[root_a] = root_b
    return []


if __name__ == "__main__":
    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4]
    print("ok")
