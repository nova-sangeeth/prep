"""Balanced Binary Tree  |  tier: neetcode150  |  Trees

Return True if the tree is height-balanced: every node's two subtrees differ in
height by at most 1.

Approach: DFS returning height, but propagate -1 as a sentinel once any subtree
is found unbalanced -- short-circuits the whole tree in one pass.
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


def is_balanced(root: Optional[TreeNode]) -> bool:
    """Return True if the tree is height-balanced."""

    def height(node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        left = height(node.left)
        if left == -1:
            return -1
        right = height(node.right)
        if right == -1 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return height(root) != -1


if __name__ == "__main__":
    balanced = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert is_balanced(balanced) is True
    small = TreeNode(1, TreeNode(2, TreeNode(3)))
    assert is_balanced(small) is False  # root: left height 2, right 0
    leaf_pair = TreeNode(1, TreeNode(2), TreeNode(3))
    assert is_balanced(leaf_pair) is True
    assert is_balanced(None) is True
    print("ok")
