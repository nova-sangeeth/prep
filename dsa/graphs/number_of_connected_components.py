"""Number of Connected Components  |  tier: blind75, neetcode150  |  Graphs

Given num_nodes nodes (0..num_nodes-1) and an undirected edge list, return the
number of connected components.

Approach: union-find. Start with num_nodes components; each edge that joins two
distinct sets reduces the count by one.
Time: O(n + e * alpha(n))   Space: O(n)
"""
from __future__ import annotations


def count_components(num_nodes: int, edges: list[list[int]]) -> int:
    """Return the number of connected components."""
    parent = list(range(num_nodes))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    components = num_nodes
    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a != root_b:
            parent[root_a] = root_b
            components -= 1
    return components


if __name__ == "__main__":
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1
    assert count_components(4, []) == 4
    print("ok")
