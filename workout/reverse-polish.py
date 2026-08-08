# -*- coding: utf-8 -*-
"""
Reverse Polish
=====================================
"""

__author__ = "nova@gitaa.in"


def reverse_polish(expression: list[str]) -> str:
    """
    Eval Polish expression
    """
    store = []
    operation_map = {
        "+": lambda a, b: int(b) + int(a),
        "-": lambda a, b: int(b) - int(a),
        "/": lambda a, b: int(b) / int(a),
        "*": lambda a, b: int(b) * int(a),
    }
    for item in expression:

        if item in operation_map:
            a = store.pop()
            b = store.pop()
            res = operation_map[item](a, b)
            store.append(res)
        else:
            store.append(int(item))

    return store[0]


def main():
    polish_eval = ["2", "4", "*", "2", "1", "*"]
    result = reverse_polish(expression=polish_eval)
    print(result)


if __name__ == "__main__":
    main()
