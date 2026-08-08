"""Copy List with Random Pointer  |  tier: neetcode150  |  Linked List

Deep-copy a linked list where each node also has a random pointer to any node or
None.

Approach: hash map from original node -> its clone. First pass creates all
clones; second pass wires next and random using the map.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations

from typing import Optional


class Node:
    """List node with next and random pointers."""

    def __init__(self, val: int) -> None:
        self.val = val
        self.next: Optional[Node] = None
        self.random: Optional[Node] = None


def copy_random_list(head: Optional[Node]) -> Optional[Node]:
    """Return a deep copy of the list including random pointers."""
    clones: dict[Optional[Node], Optional[Node]] = {None: None}
    curr = head
    while curr:  # pass 1: clone nodes
        clones[curr] = Node(curr.val)
        curr = curr.next
    curr = head
    while curr:  # pass 2: wire pointers
        clones[curr].next = clones[curr.next]  # type: ignore[union-attr]
        clones[curr].random = clones[curr.random]  # type: ignore[union-attr]
        curr = curr.next
    return clones[head]


if __name__ == "__main__":
    node1, node2, node3 = Node(7), Node(13), Node(11)
    node1.next, node2.next = node2, node3
    node1.random, node2.random, node3.random = None, node1, node1
    copy = copy_random_list(node1)
    assert copy is not node1 and copy.val == 7  # type: ignore[union-attr]
    assert copy.next.val == 13  # type: ignore[union-attr]
    assert copy.next.random is copy  # type: ignore[union-attr]
    print("ok")
