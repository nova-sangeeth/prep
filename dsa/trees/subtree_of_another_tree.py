"""Subtree of Another Tree  |  tier: blind75, neetcode150  |  Trees

Return True if subRoot is a subtree of root (a node in root whose subtree is
identical to subRoot).

Approach: at every node of root, test same-tree against subRoot. An empty
subRoot is always a subtree.
Time: O(n * m)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def _same(tree1: Optional[TreeNode], tree2: Optional[TreeNode]) -> bool:
    if tree1 is None and tree2 is None:
        return True
    if tree1 is None or tree2 is None or tree1.val != tree2.val:
        return False
    return _same(tree1.left, tree2.left) and _same(tree1.right, tree2.right)


def is_subtree(root: Optional[TreeNode], sub_root: Optional[TreeNode]) -> bool:
    """Return True if sub_root is a subtree of root."""
    if sub_root is None:
        return True
    if root is None:
        return False
    if _same(root, sub_root):
        return True
    return is_subtree(root.left, sub_root) or is_subtree(root.right, sub_root)


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(4, TreeNode(1), TreeNode(2)), TreeNode(5))
    sub = TreeNode(4, TreeNode(1), TreeNode(2))
    assert is_subtree(root, sub) is True
    assert is_subtree(root, TreeNode(4, TreeNode(1), TreeNode(2, TreeNode(0)))) is False
    print("ok")
