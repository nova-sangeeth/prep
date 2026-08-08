"""Binary Tree Right Side View  |  tier: neetcode150  |  Trees

Return the values visible from the right side, top to bottom (the last node of
each level).

Approach: BFS level by level; the last node dequeued in each level is the one
visible from the right.
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


def right_side_view(root: Optional[TreeNode]) -> list[int]:
    """Return the rightmost value at each level."""
    if root is None:
        return []
    result: list[int] = []
    queue: deque[TreeNode] = deque([root])
    while queue:
        size = len(queue)
        for i in range(size):
            node = queue.popleft()
            if i == size - 1:  # last node of this level
                result.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    return result


if __name__ == "__main__":
    root = TreeNode(1, TreeNode(2, None, TreeNode(5)), TreeNode(3, None, TreeNode(4)))
    assert right_side_view(root) == [1, 3, 4]
    assert right_side_view(None) == []
    print("ok")
