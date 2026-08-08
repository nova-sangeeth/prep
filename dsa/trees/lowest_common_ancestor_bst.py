"""Lowest Common Ancestor of a BST  |  tier: core50, blind75, neetcode150  |  Trees

Return the lowest common ancestor of two nodes node_p and node_q in a binary SEARCH tree.

Approach: exploit BST ordering. If both values are less than the node, go left;
if both greater, go right; otherwise the paths split here -> this node is the LCA.
Time: O(h)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary search tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def lowest_common_ancestor(root: TreeNode, node_p: TreeNode, node_q: TreeNode) -> TreeNode:
    """Return the LCA node of node_p and node_q in the BST."""
    node: Optional[TreeNode] = root
    while node:
        if node_p.val < node.val and node_q.val < node.val:
            node = node.left
        elif node_p.val > node.val and node_q.val > node.val:
            node = node.right
        else:
            return node
    raise ValueError("nodes not found")


if __name__ == "__main__":
    #        6
    #     2     8
    #   0  4  7   9
    n0, n4, n7, n9 = TreeNode(0), TreeNode(4), TreeNode(7), TreeNode(9)
    n2 = TreeNode(2, n0, n4)
    n8 = TreeNode(8, n7, n9)
    root = TreeNode(6, n2, n8)
    assert lowest_common_ancestor(root, n2, n8).val == 6
    assert lowest_common_ancestor(root, n2, n4).val == 2
    print("ok")
