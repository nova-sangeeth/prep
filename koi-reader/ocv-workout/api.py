"""
api.py — high-throughput detection API.

This is the part that maps directly to the KoiReader job description:

  * FastAPI            -> async, low-latency HTTP layer
  * ProcessPoolExecutor-> bypass the GIL for CPU-bound OpenCV work
  * Redis queue        -> mimic the Edge -> Cloud data flow (Pub/Sub style)

THE KEY CONCURRENCY LESSON
--------------------------
FastAPI handlers are async and run on ONE event loop thread. OpenCV
detection is CPU-bound. If we ran it directly in the handler, that one
request would BLOCK the event loop and kill throughput for everyone.

The GIL means threads won't help for CPU work either — only one thread
runs Python bytecode at a time. So we offload to a PROCESS pool: each
worker is a separate OS process with its own GIL, giving true parallel
CPU use across cores.

Pattern:  await loop.run_in_executor(process_pool, detect_bytes, data)

Run:
    pip install -r requirements.txt
    uvicorn api:app --workers 1 --port 8000
    # (keep uvicorn workers=1 here; OUR process pool does the parallelism)

Endpoints:
    GET  /health
    POST /detect   (multipart file=<image>)  -> JSON result
"""

from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from detector import detect_bytes

# Optional Redis. App still works if Redis isn't installed/running.
try:
    import redis  # type: ignore
except ImportError:
    redis = None

POOL_WORKERS = os.cpu_count() or 4
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_QUEUE = "detections"

# Module-level handles, set up in lifespan below.
state: dict = {"pool": None, "redis": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: build the process pool once (forking per-request is slow).
    state["pool"] = ProcessPoolExecutor(max_workers=POOL_WORKERS)

    # Connect to Redis if available; degrade gracefully if not.
    if redis is not None:
        try:
            client = redis.from_url(REDIS_URL, decode_responses=True)
            client.ping()
            state["redis"] = client
        except Exception:
            state["redis"] = None  # Redis down -> just skip queueing

    yield  # ---- app runs here ----

    # Shutdown: free workers.
    state["pool"].shutdown(wait=False)


app = FastAPI(title="OCV Workout - Detection API", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "pool_workers": POOL_WORKERS,
        "redis": state["redis"] is not None,
    }


@app.post("/detect")
async def detect_endpoint(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    loop = asyncio.get_running_loop()
    try:
        # Offload CPU work to a separate process -> event loop stays free,
        # and we use multiple cores in true parallel (no GIL contention).
        result = await loop.run_in_executor(
            state["pool"], detect_bytes, data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Push result onto the queue (Edge -> Cloud handoff). LPUSH = enqueue.
    client = state["redis"]
    if client is not None:
        payload = {"filename": file.filename, **result}
        client.lpush(RESULT_QUEUE, json.dumps(payload))

    return result
