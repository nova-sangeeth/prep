"""Reverse Nodes in K-Group  |  tier: neetcode150  |  Linked List

Reverse the list in groups of k nodes. A trailing group smaller than k is left
as-is.

Approach: for each group, first check that k nodes remain; if so, reverse those
k nodes and connect the reversed segment to the previous and next groups via a
dummy/group-prev pointer.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def reverse_k_group(head: Optional[ListNode], k: int) -> Optional[ListNode]:
    """Reverse every consecutive group of k nodes."""
    dummy = ListNode(0, head)
    group_prev = dummy

    while True:
        kth = group_prev  # find the k-th node from group_prev
        for _ in range(k):
            kth = kth.next  # type: ignore[assignment]
            if not kth:
                return dummy.next
        group_next = kth.next

        prev, curr = group_next, group_prev.next  # reverse the group
        while curr is not group_next:
            nxt = curr.next  # type: ignore[union-attr]
            curr.next = prev  # type: ignore[union-attr]
            prev = curr
            curr = nxt

        new_group_prev = group_prev.next
        group_prev.next = kth
        group_prev = new_group_prev  # type: ignore[assignment]


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
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
    assert _to_list(reverse_k_group(_build([1, 2, 3, 4, 5]), 1)) == [1, 2, 3, 4, 5]
    print("ok")
