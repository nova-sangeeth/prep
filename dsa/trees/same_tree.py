"""Same Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return True if two binary trees are structurally identical with equal values.

Approach: recurse in lockstep. Both None -> equal; one None or values differ ->
not equal; else compare left and right subtrees.
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


def is_same_tree(tree1: Optional[TreeNode], tree2: Optional[TreeNode]) -> bool:
    """Return True if both trees are identical."""
    if tree1 is None and tree2 is None:
        return True
    if tree1 is None or tree2 is None or tree1.val != tree2.val:
        return False
    return is_same_tree(tree1.left, tree2.left) and is_same_tree(tree1.right, tree2.right)


if __name__ == "__main__":
    tree1 = TreeNode(1, TreeNode(2), TreeNode(3))
    tree2 = TreeNode(1, TreeNode(2), TreeNode(3))
    tree3 = TreeNode(1, TreeNode(2), TreeNode(4))
    assert is_same_tree(tree1, tree2) is True
    assert is_same_tree(tree1, tree3) is False
    assert is_same_tree(None, None) is True
    print("ok")
