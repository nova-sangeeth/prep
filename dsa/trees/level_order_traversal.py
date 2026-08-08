"""Binary Tree Level Order Traversal  |  tier: core50, blind75, neetcode150  |  Trees

Return node values level by level, top to bottom, left to right.

Approach: BFS with a queue. Process the queue one full level at a time using its
current length, collecting each level's values into its own list.
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


def level_order(root: Optional[TreeNode]) -> list[list[int]]:
    """Return values grouped by level (BFS)."""
    if root is None:
        return []
    result: list[list[int]] = []
    queue: deque[TreeNode] = deque([root])
    while queue:
        level: list[int] = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result


if __name__ == "__main__":
    root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    assert level_order(root) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    print("ok")
