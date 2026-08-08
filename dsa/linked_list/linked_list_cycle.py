"""Linked List Cycle  |  tier: core50, blind75, neetcode150  |  Linked List

Return True if the linked list contains a cycle.

Approach: Floyd's tortoise and hare. A slow pointer (1 step) and fast pointer
(2 steps) meet inside any cycle; if fast reaches the end, there is no cycle.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def has_cycle(head: Optional[ListNode]) -> bool:
    """Return True if the list has a cycle (Floyd's algorithm)."""
    slow, fast = head, head
    while fast and fast.next:
        slow = slow.next  # type: ignore[union-attr]
        fast = fast.next.next
        if slow is fast:
            return True
    return False


if __name__ == "__main__":
    node1, node2, node3 = ListNode(3), ListNode(2), ListNode(0)
    node1.next, node2.next, node3.next = node2, node3, node2  # cycle: node3 -> node2
    assert has_cycle(node1) is True
    head, tail = ListNode(1), ListNode(2)
    head.next = tail
    assert has_cycle(head) is False
    print("ok")
