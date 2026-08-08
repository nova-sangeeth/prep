"""Invert Binary Tree  |  tier: core50, blind75, neetcode150  |  Trees

Mirror a binary tree: swap every node's left and right subtrees.

Approach: recurse, swapping children at each node. (A BFS/DFS with a queue/stack
works identically.)
Time: O(n)   Space: O(h)  recursion depth
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def invert_tree(root: Optional[TreeNode]) -> Optional[TreeNode]:
    """Return the root of the mirrored tree."""
    if root is None:
        return None
    root.left, root.right = invert_tree(root.right), invert_tree(root.left)
    return root


def _inorder(root: Optional[TreeNode]) -> list[int]:
    if root is None:
        return []
    return _inorder(root.left) + [root.val] + _inorder(root.right)


if __name__ == "__main__":
    #        4
    #      2   7
    #     1 3 6 9
    root = TreeNode(4, TreeNode(2, TreeNode(1), TreeNode(3)), TreeNode(7, TreeNode(6), TreeNode(9)))
    assert _inorder(invert_tree(root)) == [9, 7, 6, 4, 3, 2, 1]
    assert invert_tree(None) is None
    print("ok")
