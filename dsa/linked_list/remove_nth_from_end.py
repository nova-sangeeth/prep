"""Remove Nth Node From End of List  |  tier: core50, blind75, neetcode150  |  Linked List

Remove the n-th node from the end in one pass and return the head.

Approach: two pointers off a dummy node. Advance 'fast' n+1 steps ahead, then
move both until fast falls off the end -- 'slow' now sits just before the target.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next


def remove_nth_from_end(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    """Remove the n-th node from the end and return the new head."""
    dummy = ListNode(0, head)
    fast: Optional[ListNode] = dummy
    slow: Optional[ListNode] = dummy
    for _ in range(n + 1):
        fast = fast.next  # type: ignore[union-attr]
    while fast:
        fast = fast.next
        slow = slow.next  # type: ignore[union-attr]
    slow.next = slow.next.next  # type: ignore[union-attr]
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
    assert _to_list(remove_nth_from_end(_build([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]
    assert _to_list(remove_nth_from_end(_build([1]), 1)) == []
    assert _to_list(remove_nth_from_end(_build([1, 2]), 1)) == [1]
    print("ok")
