"""Merge K Sorted Lists  |  tier: blind75, neetcode150  |  Linked List

Merge k sorted linked lists into one sorted list.

Approach: iteratively merge lists in pairs (divide and conquer). Each round
halves the number of lists, so each node is touched O(log k) times.
Time: O(n log k)   Space: O(1)  (in-place merges)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def _merge_two(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
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


def merge_k_lists(lists: list[Optional[ListNode]]) -> Optional[ListNode]:
    """Merge k sorted lists via pairwise divide-and-conquer."""
    if not lists:
        return None
    while len(lists) > 1:
        merged: list[Optional[ListNode]] = []
        for i in range(0, len(lists), 2):
            list1 = lists[i]
            list2 = lists[i + 1] if i + 1 < len(lists) else None
            merged.append(_merge_two(list1, list2))
        lists = merged
    return lists[0]


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
    out = merge_k_lists([_build([1, 4, 5]), _build([1, 3, 4]), _build([2, 6])])
    assert _to_list(out) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_lists([]) is None
    assert _to_list(merge_k_lists([None, _build([1])])) == [1]
    print("ok")
