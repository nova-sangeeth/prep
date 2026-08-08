"""Serialize and Deserialize Binary Tree  |  tier: blind75, neetcode150  |  Trees

Encode a binary tree to a string and decode it back to the same structure.

Approach: preorder DFS. Emit each value, using a sentinel ('#') for None.
Deserialize consumes the tokens in the same preorder, rebuilding recursively.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from collections import deque
from typing import Optional


class TreeNode:
    """Binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def serialize(root: Optional[TreeNode]) -> str:
    """Encode the tree to a comma-separated preorder string."""
    parts: list[str] = []

    def dfs(node: Optional[TreeNode]) -> None:
        if node is None:
            parts.append("#")
            return
        parts.append(str(node.val))
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return ",".join(parts)


def deserialize(data: str) -> Optional[TreeNode]:
    """Decode the preorder string back into a tree."""
    tokens = deque(data.split(","))

    def build() -> Optional[TreeNode]:
        tok = tokens.popleft()
        if tok == "#":
            return None
        node = TreeNode(int(tok))
        node.left = build()
        node.right = build()
        return node

    return build()


def _inorder(node: Optional[TreeNode]) -> list[int]:
    if node is None:
        return []
    return _inorder(node.left) + [node.val] + _inorder(node.right)


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    restored = deserialize(serialize(root))
    assert _inorder(restored) == _inorder(root)
    assert serialize(None) == "#"
    assert deserialize(serialize(None)) is None
    print("ok")
