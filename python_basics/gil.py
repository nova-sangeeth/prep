"""Q9. What is the GIL (Global Interpreter Lock)?

CPython mutex: only one thread runs Python bytecode at a time.
- CPU-bound work: threads do NOT run in parallel -> use multiprocessing.
- I/O-bound work: GIL released during I/O -> threads DO help.

This file demonstrates the practical takeaway, not the lock internals.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor


def heavy(n: int) -> int:
    """CPU-bound work: sum of squares up to n."""
    return sum(i * i for i in range(n))


def parallel_cpu(workloads: list[int]) -> list[int]:
    """Use processes (each with its own GIL) for true parallel CPU work."""
    with ProcessPoolExecutor() as pool:
        return list(pool.map(heavy, workloads))


if __name__ == "__main__":
    print(parallel_cpu([100_000, 200_000, 300_000]))
