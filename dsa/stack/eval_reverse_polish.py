"""Evaluate Reverse Polish Notation  |  tier: core50, neetcode150  |  Stack

Evaluate an arithmetic expression in postfix (RPN) form. Operators: + - * /.
Division truncates toward zero.

Approach: scan tokens; push numbers; on an operator pop the two operands, apply,
push the result. Final stack value is the answer.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def eval_rpn(tokens: list[str]) -> int:
    """Evaluate a reverse Polish notation expression."""
    ops = {"+", "-", "*", "/"}
    stack: list[int] = []
    for tok in tokens:
        if tok in ops:
            right = stack.pop()
            left = stack.pop()
            if tok == "+":
                stack.append(left + right)
            elif tok == "-":
                stack.append(left - right)
            elif tok == "*":
                stack.append(left * right)
            else:
                stack.append(int(left / right))  # truncate toward zero
        else:
            stack.append(int(tok))
    return stack[0]


if __name__ == "__main__":
    assert eval_rpn(["2", "1", "+", "3", "*"]) == 9  # (2+1)*3
    assert eval_rpn(["4", "13", "5", "/", "+"]) == 6  # 4 + 13//5
    assert eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
    print("ok")
