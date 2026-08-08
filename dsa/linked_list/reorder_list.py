"""Reorder List  |  tier: blind75, neetcode150  |  Linked List

Reorder L0->L1->...->Ln to L0->Ln->L1->Ln-1->... in place (values not moved,
pointers rewired).

Approach: (1) find the middle with slow/fast pointers; (2) reverse the second
half; (3) merge the two halves alternately.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reorder_list(head: Optional[ListNode]) -> None:
    """Reorder the list in place."""
    if not head or not head.next:
        return
    slow, fast = head, head
    while fast.next and fast.next.next:  # slow -> middle
        slow = slow.next
        fast = fast.next.next

    second: Optional[ListNode] = slow.next  # reverse second half
    slow.next = None
    prev: Optional[ListNode] = None
    while second:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt

    first: Optional[ListNode] = head  # merge alternately
    second = prev
    while second:
        first.next, first = second, first.next
        second.next, second = first, second.next


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
    even_list = _build([1, 2, 3, 4])
    reorder_list(even_list)
    assert _to_list(even_list) == [1, 4, 2, 3]
    odd_list = _build([1, 2, 3, 4, 5])
    reorder_list(odd_list)
    assert _to_list(odd_list) == [1, 5, 2, 4, 3]
    print("ok")
