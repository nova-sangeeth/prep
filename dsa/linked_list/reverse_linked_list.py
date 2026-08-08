"""Reverse Linked List  |  tier: core50, blind75, neetcode150  |  Linked List

Reverse a singly linked list and return the new head.

Approach: iterate, re-pointing each node's next to the previous node. Three
variables: prev, curr, and the saved next.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    """Return the head of the reversed list."""
    prev: Optional[ListNode] = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev


def _build(values: list[int]) -> Optional[ListNode]:
    head: Optional[ListNode] = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _to_list(head: Optional[ListNode]) -> list[int]:
    out: list[int] = []
    while head:
        out.append(head.val)
        head = head.next
    return out


if __name__ == "__main__":
    assert _to_list(reverse_list(_build([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert _to_list(reverse_list(_build([]))) == []
    print("ok")
