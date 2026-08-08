"""Q14. Exception handling: try / except / else / finally.

try     : code that might raise.
except  : runs on a matching exception (catch specific types).
else    : runs only if try succeeded.
finally : always runs -> cleanup.
"""
from __future__ import annotations


class WithdrawError(Exception):
    """Custom domain exception."""


def safe_divide(a: float, b: float) -> float | None:
    """Divide a by b, handling the zero case and always logging completion."""
    try:
        result = a / b
    except ZeroDivisionError as exc:
        print("cannot divide by zero:", exc)
        return None
    else:
        return result  # only when no exception
    finally:
        print("division attempt finished")  # always runs


def withdraw(balance: float, amount: float) -> float:
    """Raise a custom exception when funds are insufficient."""
    if amount > balance:
        raise WithdrawError(f"need {amount}, have {balance}")
    return balance - amount


if __name__ == "__main__":
    print(safe_divide(10, 2))
    print(safe_divide(10, 0))
    try:
        withdraw(50, 80)
    except WithdrawError as exc:
        print("blocked:", exc)
