"""Valid Parenthesis String  |  tier: neetcode150  |  Greedy

'*' can be '(', ')', or empty. Return True if the string can be a valid sequence
of parentheses.

Approach: track the RANGE of possible open-paren counts [low, high]. '(' bumps
both; ')' drops both; '*' widens (low-1, high+1). Clamp low at 0; if high goes
negative there are too many ')'. Valid iff low can reach 0 at the end.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def check_valid_string(text: str) -> bool:
    """Return True if text can form a valid parenthesis sequence."""
    low = high = 0  # min/max possible unmatched '('
    for ch in text:
        if ch == "(":
            low += 1
            high += 1
        elif ch == ")":
            low -= 1
            high -= 1
        else:  # '*'
            low -= 1
            high += 1
        if high < 0:  # too many ')'
            return False
        low = max(low, 0)
    return low == 0


if __name__ == "__main__":
    assert check_valid_string("()") is True
    assert check_valid_string("(*)") is True
    assert check_valid_string("(*))") is True
    assert check_valid_string(")(") is False
    print("ok")
