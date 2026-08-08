"""Diameter of Binary Tree  |  tier: neetcode150  |  Trees

Return the length (in edges) of the longest path between any two nodes. The path
need not pass through the root.

Approach: DFS returning subtree height. At each node the longest path THROUGH it
is left_height + right_height; track the global max while computing heights.
Time: O(n)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def diameter_of_binary_tree(root: Optional[TreeNode]) -> int:
    """Return the diameter (longest path in edges)."""
    best = 0

    def height(node: Optional[TreeNode]) -> int:
        nonlocal best
        if node is None:
            return 0
        left = height(node.left)
        right = height(node.right)
        best = max(best, left + right)  # path through this node
        return 1 + max(left, right)

    height(root)
    return best


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3))
    assert diameter_of_binary_tree(root) == 3  # 4-2-5 ... 4-2-1-3 = 3
    assert diameter_of_binary_tree(TreeNode(1)) == 0
    print("ok")
