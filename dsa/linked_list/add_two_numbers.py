"""Add Two Numbers  |  tier: neetcode150  |  Linked List

Two numbers stored as linked lists of digits in reverse order. Return their sum
as a linked list, also reverse order.

Approach: walk both lists in lockstep adding digit + carry, emitting digit % 10
and carrying digit // 10. Continue while either list or the carry remains.
Time: O(max(n, m))   Space: O(max(n, m))
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def add_two_numbers(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
    """Sum two reverse-order digit lists, returning a reverse-order list."""
    dummy = ListNode()
    tail = dummy
    carry = 0
    while list1 or list2 or carry:
        total = carry
        if list1:
            total += list1.val
            list1 = list1.next
        if list2:
            total += list2.val
            list2 = list2.next
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    return dummy.next


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
    # 342 + 465 = 807
    assert _to_list(add_two_numbers(_build([2, 4, 3]), _build([5, 6, 4]))) == [7, 0, 8]
    assert _to_list(add_two_numbers(_build([9, 9]), _build([1]))) == [0, 0, 1]
    print("ok")
