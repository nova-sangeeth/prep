"""Q15. Scope and the LEGB rule.

Name lookup order: Local -> Enclosing -> Global -> Built-in.
`global` rebinds a module-level name; `nonlocal` rebinds an enclosing one.
Assigning without them creates a NEW local name.
"""
from __future__ import annotations

scope_name = "global"


def legb_demo() -> None:
    """Innermost binding wins under LEGB."""
    scope_name = "enclosing"

    def inner() -> None:
        scope_name = "local"
        print(scope_name)  # local

    inner()
    print(scope_name)  # enclosing


def make_counter() -> "callable[[], int]":  # noqa: F821 - illustrative
    """Closure using nonlocal to mutate the enclosing variable."""
    count = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment


if __name__ == "__main__":
    legb_demo()
    print(scope_name)  # global
    counter = make_counter()
    print(counter(), counter(), counter())  # 1 2 3
