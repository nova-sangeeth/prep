"""Q23. Context managers and the `with` statement.

`with` runs setup/cleanup automatically, even on exception. Implemented via
__enter__/__exit__, or more simply with contextlib.contextmanager.
Common uses: files, locks, DB connections/transactions.
"""
from __future__ import annotations

from contextlib import contextmanager
from types import TracebackType
from typing import Iterator


class Resource:
    """Class-based context manager that acquires and releases a resource."""

    def __enter__(self) -> "Resource":
        print("acquire")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        print("release")  # always runs, even on error
        return False  # don't suppress exceptions


@contextmanager
def managed() -> Iterator[str]:
    """Generator-based context manager: code before/after yield is setup/teardown."""
    print("setup")
    try:
        yield "resource"
    finally:
        print("teardown")


if __name__ == "__main__":
    with Resource():
        print("use resource")
    with managed() as r:
        print("got:", r)
