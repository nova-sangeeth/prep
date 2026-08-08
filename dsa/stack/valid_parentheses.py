"""Valid Parentheses  |  tier: core50, blind75, neetcode150  |  Stack

Given a string of (), [], {}, return True if every bracket is closed by the
matching type in the correct order.

Approach: push opens onto a stack; on a close, the stack top must be the
matching open. Valid iff every close matches and the stack ends empty.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def is_valid(brackets: str) -> bool:
    """Return True if brackets are balanced and correctly nested."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in brackets:
        if ch in pairs:  # closing bracket
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:  # opening bracket
            stack.append(ch)
    return not stack


if __name__ == "__main__":
    assert is_valid("()[]{}") is True
    assert is_valid("(]") is False
    assert is_valid("([{}])") is True
    assert is_valid("(") is False
    print("ok")
