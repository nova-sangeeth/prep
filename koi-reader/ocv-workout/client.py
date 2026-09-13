"""
client.py — hammer the API to see the concurrency win.

Sends N images concurrently and reports throughput. Use it to FEEL the
difference between blocking and process-pool offloading.

Usage:
    python client.py path/to/image.jpg            # single request
    python client.py path/to/image.jpg 50         # 50 concurrent requests
"""

import sys
import time

import requests

URL = "http://localhost:8000/detect"


def one(path: str) -> dict:
    with open(path, "rb") as f:
        r = requests.post(URL, files={"file": f})
    r.raise_for_status()
    return r.json()


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python client.py <image> [n]")
        sys.exit(1)

    path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    if n == 1:
        print(one(path))
        return

    # Fire n requests, time the batch. Threads here are fine: the work is
    # I/O (waiting on HTTP), so the GIL is released during the wait.
    from concurrent.futures import ThreadPoolExecutor

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as ex:
        results = list(ex.map(lambda _: one(path), range(n)))
    elapsed = time.perf_counter() - start

    print(f"{n} requests in {elapsed:.2f}s "
          f"=> {n / elapsed:.1f} req/s")
    print("sample:", results[0])


if __name__ == "__main__":
    main()
