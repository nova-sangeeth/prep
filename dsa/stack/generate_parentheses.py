"""Generate Parentheses  |  tier: neetcode150  |  Stack

Generate all combinations of n well-formed pairs of parentheses.

Approach: backtracking with two counters. Add '(' while opens < n; add ')' only
while closes < opens (keeps every prefix valid). Record when length == 2n.
Time: O(4^n / sqrt(n))  (Catalan number)   Space: O(n) recursion depth
"""
from __future__ import annotations


def generate_parenthesis(n: int) -> list[str]:
    """Return all valid combinations of n pairs of parentheses."""
    result: list[str] = []
    stack: list[str] = []

    def backtrack(opens: int, closes: int) -> None:
        if len(stack) == 2 * n:
            result.append("".join(stack))
            return
        if opens < n:
            stack.append("(")
            backtrack(opens + 1, closes)
            stack.pop()
        if closes < opens:
            stack.append(")")
            backtrack(opens, closes + 1)
            stack.pop()

    backtrack(0, 0)
    return result


if __name__ == "__main__":
    assert sorted(generate_parenthesis(3)) == sorted(["((()))", "(()())", "(())()", "()(())", "()()()"])
    assert generate_parenthesis(1) == ["()"]
    print("ok")
