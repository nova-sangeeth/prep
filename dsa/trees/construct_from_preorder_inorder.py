"""Construct Binary Tree from Preorder and Inorder  |  tier: blind75, neetcode150  |  Trees

Rebuild a binary tree from its preorder and inorder traversals (unique values).

Approach: preorder[0] is the root. Its position in inorder splits left/right
subtrees by size. Recurse, consuming preorder left to right via an index. An
index map of value -> inorder position avoids repeated scans.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def build_tree(preorder: list[int], inorder: list[int]) -> Optional[TreeNode]:
    """Reconstruct the tree from preorder + inorder traversals."""
    index = {val: i for i, val in enumerate(inorder)}
    pre_idx = 0

    def build(left: int, right: int) -> Optional[TreeNode]:
        nonlocal pre_idx
        if left > right:
            return None
        root_val = preorder[pre_idx]
        pre_idx += 1
        node = TreeNode(root_val)
        mid = index[root_val]
        node.left = build(left, mid - 1)
        node.right = build(mid + 1, right)
        return node

    return build(0, len(inorder) - 1)


def _preorder(node: Optional[TreeNode]) -> list[int]:
    if node is None:
        return []
    return [node.val] + _preorder(node.left) + _preorder(node.right)


if __name__ == "__main__":
    pre = [3, 9, 20, 15, 7]
    ino = [9, 3, 15, 20, 7]
    tree = build_tree(pre, ino)
    assert _preorder(tree) == pre
    print("ok")
