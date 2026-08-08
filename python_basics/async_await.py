"""Q28. async / await (asyncio).

Coroutines defined with `async def` run concurrently on a single thread.
`await` yields control while waiting on I/O. Great for many concurrent I/O
tasks; not for CPU-bound work (still bound by the GIL).
"""
from __future__ import annotations

import asyncio


async def fetch(name: str, delay: float) -> str:
    """Simulate an I/O call that takes `delay` seconds."""
    await asyncio.sleep(delay)  # non-blocking wait
    return f"{name} done"


async def main() -> list[str]:
    """Run three 'fetches' concurrently -> total time ~max, not sum."""
    results = await asyncio.gather(
        fetch("a", 0.10),
        fetch("b", 0.05),
        fetch("c", 0.08),
    )
    return results


if __name__ == "__main__":
    print(asyncio.run(main()))
