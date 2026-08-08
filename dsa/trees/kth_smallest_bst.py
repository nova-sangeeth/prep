"""Kth Smallest Element in a BST  |  tier: blind75, neetcode150  |  Trees

Return the k-th smallest value (1-indexed) in a BST.

Approach: an in-order traversal of a BST yields values in sorted order. Walk
iteratively with a stack and stop at the k-th visited node.
Time: O(h + k)   Space: O(h)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary search tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    """Return the k-th smallest value via in-order traversal."""
    stack: list[TreeNode] = []
    node = root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right
    raise ValueError("k larger than tree size")


if __name__ == "__main__":
    #      3
    #    1   4
    #     2
    root = TreeNode(3, TreeNode(1, None, TreeNode(2)), TreeNode(4))
    assert kth_smallest(root, 1) == 1
    assert kth_smallest(root, 2) == 2
    assert kth_smallest(root, 4) == 4
    print("ok")
