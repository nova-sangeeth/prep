"""Binary Tree Maximum Path Sum  |  tier: blind75, neetcode150  |  Trees

Return the maximum sum of any path. A path is a sequence of connected nodes; it
need not pass through the root and cannot reuse a node.

Approach: DFS returning the best DOWNWARD gain from a node (value + max(0, best
child)). At each node the best path THROUGH it is value + left_gain + right_gain;
track the global max. Negative gains are clamped to 0.
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


def max_path_sum(root: Optional[TreeNode]) -> int:
    """Return the maximum path sum in the tree."""
    best = float("-inf")

    def gain(node: Optional[TreeNode]) -> int:
        nonlocal best
        if node is None:
            return 0
        left = max(gain(node.left), 0)
        right = max(gain(node.right), 0)
        best = max(best, node.val + left + right)  # path through node
        return node.val + max(left, right)  # best single branch

    gain(root)
    return int(best)


if __name__ == "__main__":
    assert max_path_sum(TreeNode(1, TreeNode(2), TreeNode(3))) == 6
    # -10 with children 9 and (15,7): best path 15-20-7 = 42
    root = TreeNode(-10, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert max_path_sum(root) == 42
    assert max_path_sum(TreeNode(-3)) == -3
    print("ok")
