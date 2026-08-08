"""Maximum Depth of Binary Tree  |  tier: core50, blind75, neetcode150  |  Trees

Return the number of nodes along the longest root-to-leaf path.

Approach: depth(node) = 1 + max(depth(left), depth(right)); empty subtree is 0.
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


def max_depth(root: Optional[TreeNode]) -> int:
    """Return the maximum depth of the tree."""
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert max_depth(root) == 3
    assert max_depth(None) == 0
    assert max_depth(TreeNode(1)) == 1
    print("ok")
