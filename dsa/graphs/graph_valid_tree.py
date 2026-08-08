"""Graph Valid Tree  |  tier: blind75, neetcode150  |  Graphs

Given num_nodes nodes and an undirected edge list, return True if they form a
valid tree: fully connected and acyclic.

Approach: a tree on num_nodes nodes has exactly num_nodes - 1 edges and is
connected. Check the edge count, then union-find: if any edge joins two
already-connected nodes, there is a cycle.
Time: O(n + e)   Space: O(n)
"""
from __future__ import annotations


def valid_tree(num_nodes: int, edges: list[list[int]]) -> bool:
    """Return True if the graph is a valid tree."""
    if len(edges) != num_nodes - 1:  # tree must have exactly num_nodes - 1 edges
        return False
    parent = list(range(num_nodes))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for node_a, node_b in edges:
        root_a, root_b = find(node_a), find(node_b)
        if root_a == root_b:
            return False  # cycle
        parent[root_a] = root_b
    return True  # num_nodes - 1 edges + no cycle => connected


if __name__ == "__main__":
    assert valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]) is True
    assert valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]) is False
    assert valid_tree(1, []) is True
    print("ok")
