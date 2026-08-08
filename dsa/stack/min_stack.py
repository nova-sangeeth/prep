"""Min Stack  |  tier: blind75, neetcode150  |  Stack

Design a stack supporting push, pop, top, and getMin all in O(1).

Approach: alongside the main stack, keep a 'min stack' whose top is always the
minimum of the current contents. On push, store min(new, current_min).
Time: O(1) per op   Space: O(n)
"""
from __future__ import annotations


class MinStack:
    """Stack with O(1) minimum retrieval."""

    def __init__(self) -> None:
        self._stack: list[int] = []
        self._mins: list[int] = []

    def push(self, val: int) -> None:
        """Push val and update the running minimum."""
        self._stack.append(val)
        self._mins.append(val if not self._mins else min(val, self._mins[-1]))

    def pop(self) -> None:
        """Remove the top element."""
        self._stack.pop()
        self._mins.pop()

    def top(self) -> int:
        """Return the top element."""
        return self._stack[-1]

    def get_min(self) -> int:
        """Return the current minimum in O(1)."""
        return self._mins[-1]


if __name__ == "__main__":
    st = MinStack()
    st.push(-2)
    st.push(0)
    st.push(-3)
    assert st.get_min() == -3
    st.pop()
    assert st.top() == 0
    assert st.get_min() == -2
    print("ok")
