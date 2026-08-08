"""Validate Binary Search Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return True if the tree is a valid BST: every left subtree value < node <
every right subtree value (strictly).

Approach: DFS carrying an open (low, high) bound. Each node must lie strictly
inside; recurse tightening the bound for each child. Bounds (not just the parent)
catch violations several levels apart.
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


def is_valid_bst(root: Optional[TreeNode]) -> bool:
    """Return True if the tree is a valid binary search tree."""

    def valid(node: Optional[TreeNode], low: float, high: float) -> bool:
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)

    return valid(root, float("-inf"), float("inf"))


if __name__ == "__main__":
    assert is_valid_bst(TreeNode(2, TreeNode(1), TreeNode(3))) is True
    # 5 with right child 4 -> invalid even though 4 < 6
    bad = TreeNode(5, TreeNode(1), TreeNode(6, TreeNode(4), TreeNode(7)))
    assert is_valid_bst(bad) is False
    print("ok")
