"""Merge Two Sorted Lists  |  tier: core50, blind75, neetcode150  |  Linked List

Merge two sorted linked lists into one sorted list and return its head.

Approach: dummy head + tail pointer. Repeatedly attach the smaller of the two
front nodes, advancing that list. Append the remaining tail at the end.
Time: O(n + m)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def merge_two_lists(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
    """Merge two sorted lists into one sorted list."""
    dummy = ListNode()
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next, list1 = list1, list1.next
        else:
            tail.next, list2 = list2, list2.next
        tail = tail.next
    tail.next = list1 or list2
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
    merged = merge_two_lists(_build([1, 2, 4]), _build([1, 3, 4]))
    assert _to_list(merged) == [1, 1, 2, 3, 4, 4]
    assert _to_list(merge_two_lists(None, _build([0]))) == [0]
    print("ok")
