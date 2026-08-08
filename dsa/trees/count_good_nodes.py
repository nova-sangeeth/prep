"""Count Good Nodes in Binary Tree  |  tier: neetcode150  |  Trees

A node is "good" if no node on the path from the root to it has a greater value.
Count the good nodes.

Approach: DFS carrying the maximum value seen on the path so far. A node is good
when its value >= that running max; recurse with the updated max.
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


def good_nodes(root: TreeNode) -> int:
    """Return the count of good nodes."""

    def dfs(node: Optional[TreeNode], path_max: int) -> int:
        if node is None:
            return 0
        good = 1 if node.val >= path_max else 0
        new_max = max(path_max, node.val)
        return good + dfs(node.left, new_max) + dfs(node.right, new_max)

    return dfs(root, root.val)


if __name__ == "__main__":
    #        3
    #      1   4
    #     3   1 5
    root = TreeNode(3, TreeNode(1, TreeNode(3)), TreeNode(4, TreeNode(1), TreeNode(5)))
    assert good_nodes(root) == 4
    assert good_nodes(TreeNode(1)) == 1
    print("ok")
