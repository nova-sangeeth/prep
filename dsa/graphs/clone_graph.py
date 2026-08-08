"""Clone Graph  |  tier: blind75, neetcode150  |  Graphs

Deep-copy a connected undirected graph given a node reference.

Approach: DFS (or BFS) with a map from original node -> its clone. Create a
clone on first visit, then recurse to clone and link neighbors. The map prevents
infinite loops on cycles.
Time: O(V + E)   Space: O(V)
"""
from __future__ import annotations

from typing import Optional


class Node:
    """Undirected graph node with a neighbor list."""

    def __init__(self, val: int = 0, neighbors: "Optional[list[Node]]" = None) -> None:
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def clone_graph(node: Optional[Node]) -> Optional[Node]:
    """Return a deep copy of the graph."""
    if node is None:
        return None
    clones: dict[Node, Node] = {}

    def dfs(original: Node) -> Node:
        if original in clones:
            return clones[original]
        copy = Node(original.val)
        clones[original] = copy
        for neighbor in original.neighbors:
            copy.neighbors.append(dfs(neighbor))
        return copy

    return dfs(node)


if __name__ == "__main__":
    node1, node2, node3, node4 = Node(1), Node(2), Node(3), Node(4)
    node1.neighbors = [node2, node4]
    node2.neighbors = [node1, node3]
    node3.neighbors = [node2, node4]
    node4.neighbors = [node1, node3]
    copy = clone_graph(node1)
    assert copy is not node1 and copy.val == 1  # type: ignore[union-attr]
    assert sorted(neighbor.val for neighbor in copy.neighbors) == [2, 4]  # type: ignore[union-attr]
    assert copy.neighbors[0] is not node2  # type: ignore[union-attr]
    print("ok")
