# Python for the Coding Round — API, async, and integration-flavoured problems

> EY GDS — Cloud Integration Platform Engineer / Integration Senior. L1 / L2 technical.

**What this file buys you:** the 45–60 min live-coding or HackerRank slot, and the "show me how you'd code that" tangent inside an architecture round. EY GDS Senior Consultant data (n=43 AmbitionBox experiences) says three technical *conversations*, no algorithm screen — but two verifiable senior coding rounds do exist (a HackerRank set of 3, and a single Streams string problem). So: 80% of this file is **integration code you will actually be asked to sketch** (idempotency, retry, outbox, consumer shutdown, JWKS), 20% is a DSA safety net. You are already strong at DSA and Python basics — nothing here re-teaches either.

**The single highest-value behaviour in this round:** state your approach in one linear sentence *before* you type, then type. Two 2026 EY GDS candidates were penalised for answers that "evolved with follow-ups" — one interviewer read it as external help. Commit, then refine.

## Table of Contents

| § | Section | What it covers |
|---|---------|----------------|
| 0 | [How this round actually runs](#0-how-this-round-actually-runs) | format, what they score |
| 1 | [Python that reads senior in an API context](#1-python-that-reads-senior-in-an-api-context) | Q1–Q15: asyncio, httpx, GIL, typing, contextvars |
| 2 | [Build-it problems with full solutions](#2-build-it-problems-with-full-solutions) | P1–P15: the actual integration problems |
| 3 | [Testing an integration service](#3-testing-an-integration-service) | pytest-asyncio, respx, testcontainers, schemathesis, Pact |
| 4 | [DSA safety net](#4-dsa-safety-net) | 6 problems, one line each |
| — | [Interviewer traps](#interviewer-traps-consolidated) | 12 wrong-answer/right-answer pairs |
| — | [30-second whiteboard versions](#30-second-whiteboard-versions) | idempotency, retry+breaker, outbox, shutdown |
| — | [Rapid fire](#rapid-fire) | 40 one-liners |

Siblings: [Auth & Security](06-auth-and-security.md) · [../DSA_MASTER.md](../DSA_MASTER.md) · [../virtusa/03-api-frameworks-fastapi-flask-django.md](../virtusa/03-api-frameworks-fastapi-flask-django.md) · [../virtusa/01-python-core-advanced.md](../virtusa/01-python-core-advanced.md)

---

## 0. How this round actually runs

| Format | Probability | What to do |
|---|---|---|
| Screenshare, they type a problem in a shared doc / Teams chat | Highest | Talk the design in 30s, then code. Narrate trade-offs as you go. |
| HackerRank, 3 questions (reported: 1 DP, 1 medium, 1 easy), 60–90 min | Real but less common | Solve easy → medium → DP. Never leave the easy one un-submitted. |
| "Write the code for what you just described" mid-architecture-round | Very likely | This file. They want 15 lines, not a repo. |
| Take-home assignment | Rare (1 report across all EY GDS designations) | — |

**They are scoring four things, in this order:** (1) do you handle failure at all, (2) do you know the difference between at-least-once and exactly-once and say it out loud, (3) is the code idiomatic modern Python (type hints, async, context managers), (4) does it terminate correctly. Correctness of a clever algorithm is a distant fifth for this role.

**Say these words unprompted, they are free marks:** idempotent, at-least-once, bounded concurrency, backpressure, dead-letter, correlation ID, graceful shutdown, deadline.

---

## 1. Python that reads senior in an API context

### Q1. Explain the event loop in one breath, then tell me what breaks it.

**Answer:** The event loop is a single-threaded scheduler running a ready queue of callbacks over an I/O selector (`epoll` on Linux). `await` on a real I/O operation yields control back to the loop, which parks that coroutine against a file descriptor and runs the next ready one. Throughput comes from the fact that a 200 ms HTTP call costs you one socket, not one thread.

What breaks it: **any CPU work or blocking syscall inside a coroutine.** `requests.get()`, `time.sleep()`, `psycopg2`, a 10 MB `json.loads`, `pandas` — none of them yield, so every other in-flight request in that worker stalls for the full duration.

```python
import asyncio, time
import httpx

# BAD: blocks the loop for 2s; concurrent requests in this worker all stall
async def bad() -> None:
    time.sleep(2)

# GOOD: yields
async def good() -> None:
    await asyncio.sleep(2)

# GOOD: blocking third-party SDK pushed to a worker thread (3.9+)
def legacy_sdk_call(payload: dict) -> dict:
    import requests
    return requests.post("https://legacy.internal/score", json=payload, timeout=10).json()

async def bridged(payload: dict) -> dict:
    return await asyncio.to_thread(legacy_sdk_call, payload)
```

**If they push back — "how do you *find* a loop block in prod?"** Turn on debug mode (`asyncio.run(main(), debug=True)` or `PYTHONASYNCIODEBUG=1`); the loop logs any callback that took longer than `loop.slow_callback_duration` (default 0.1 s). In production I export an event-loop-lag metric: a task that sleeps 1 s in a loop and records `actual - expected`.

---

### Q2. `asyncio.gather` vs `asyncio.TaskGroup` — when do you use which?

**Answer:** `TaskGroup` (Python 3.11+) is structured concurrency: the `async with` block cannot exit until every child finishes, and if one child raises, the siblings are **cancelled** and you get an `ExceptionGroup`. `gather` has no scope — if you don't await it the tasks leak, and by default the first exception propagates while the siblings keep running orphaned.

Rule I use: **`TaskGroup` when the operation is all-or-nothing; `gather(return_exceptions=True)` when I need partial results.** A fan-out to five downstream systems where three answering is still a useful response is the classic `gather` case (see [P9](#p9-fan-out-to-n-downstreams-with-a-hard-deadline-and-partial-failure)).

```python
import asyncio

async def fetch(i: int) -> int:
    await asyncio.sleep(0.1 * i)
    if i == 2:
        raise ValueError("boom")
    return i

async def all_or_nothing() -> list[int]:
    results: list[int] = []
    async with asyncio.TaskGroup() as tg:              # 3.11+
        tasks = [tg.create_task(fetch(i)) for i in range(4)]
    return [t.result() for t in tasks]                  # raises ExceptionGroup

async def partial() -> list[int | BaseException]:
    return await asyncio.gather(*(fetch(i) for i in range(4)), return_exceptions=True)

async def main() -> None:
    try:
        await all_or_nothing()
    except* ValueError as eg:                           # 3.11 except* syntax
        print("failed children:", eg.exceptions)
    print(await partial())   # [0, 1, ValueError('boom'), 3]

asyncio.run(main())
```

**If they push back — "what does `except*` buy you?"** It lets me handle one *kind* of failure across a group without swallowing the rest — e.g. `except* httpx.TimeoutException` retries, `except* ValidationError` dead-letters, and anything unmatched still propagates.

---

### Q3. How do you bound concurrency when fanning out to a downstream that rate-limits you?

**Answer:** `asyncio.Semaphore` around the call, sized to whatever the downstream contract allows — not to how many items I have. A thousand tasks with a semaphore of 10 is ten in flight and 990 cheaply parked; a thousand tasks without one is a self-inflicted DDoS and a wall of 429s.

```python
import asyncio
import httpx

async def upsert_all(client: httpx.AsyncClient, rows: list[dict], concurrency: int = 10) -> list[int]:
    sem = asyncio.Semaphore(concurrency)

    async def one(row: dict) -> int:
        async with sem:                                   # acquire/release even on exception
            r = await client.post("/customers", json=row)
            return r.status_code

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(one(r)) for r in rows]
    return [t.result() for t in tasks]
```

**If they push back — "semaphore vs a worker pool?"** Semaphore is right when the work items are already materialised in memory. If the source is a stream I don't want fully resident, I use N worker coroutines pulling from an `asyncio.Queue(maxsize=N*2)` — the bounded queue gives me **backpressure** on the producer, which a semaphore does not (see [P7](#p7-stream-a-paginated-upstream-api-into-blob-storage-without-loading-it)).

---

### Q4. Timeouts and cancellation — show me you actually understand them.

**Answer:** Every outbound call gets a timeout, and every request gets an overall **deadline** that is separate from the per-call timeout. `asyncio.timeout()` (3.11+) is a context manager that cancels whatever is inside it and converts the `CancelledError` into `TimeoutError` at the boundary — that conversion is the reason to prefer it over `wait_for`.

Cancellation in asyncio is cooperative: it raises `CancelledError` *at the next await point*. So cleanup belongs in `finally`, and a bare `except Exception` will not swallow it (`CancelledError` inherits from `BaseException` since 3.8) — but a bare `except:` will, which is a bug.

```python
import asyncio

async def slow() -> str:
    try:
        await asyncio.sleep(10)
        return "done"
    finally:
        # runs on cancellation too — release locks, settle messages, close cursors here
        print("cleanup")

async def main() -> None:
    try:
        async with asyncio.timeout(0.5):        # 3.11+; asyncio.timeout_at() for absolute deadline
            await slow()
    except TimeoutError:
        print("deadline exceeded")

    # shifting a deadline mid-flight (e.g. after a fast cache hit gave us budget back)
    async with asyncio.timeout(5) as cm:
        cm.reschedule(asyncio.get_running_loop().time() + 1.0)
        await asyncio.sleep(0.1)

asyncio.run(main())
```

**If they push back — "how do you protect cleanup that must not be cancelled?"** `asyncio.shield()` for the small critical section, or run the settle/commit inside `finally` with its own fresh `asyncio.timeout` — shielding the whole handler just moves the hang.

---

### Q5. A blocking call in an async handler — quantify the damage and fix it.

**Answer:** One worker, one loop. A 2-second blocking call in an `async def` route caps that worker at **0.5 requests/second** regardless of how many clients are connected. The same call in a plain `def` FastAPI route is fine, because Starlette runs sync routes in AnyIO's threadpool — capacity **40 threads** by default, so 40 concurrent, and the 41st waits for a token.

Three fixes in order of preference: (1) use an async client and `await` it; (2) `asyncio.to_thread` / `anyio.to_thread.run_sync` for a blocking *I/O* library; (3) `ProcessPoolExecutor` for genuine CPU work, because a thread does not escape the GIL.

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio, hashlib

import anyio.to_thread
from fastapi import FastAPI

app = FastAPI()
_pool = ProcessPoolExecutor(max_workers=4)

def cpu_heavy(data: bytes) -> str:                # GIL-bound: threads will NOT help
    return hashlib.pbkdf2_hmac("sha256", data, b"salt", 600_000).hex()

def blocking_io(path: str) -> bytes:              # releases the GIL: threads DO help
    with open(path, "rb") as fh:
        return fh.read()

@app.post("/hash")
async def hash_route(payload: bytes) -> dict:
    loop = asyncio.get_running_loop()
    digest = await loop.run_in_executor(_pool, cpu_heavy, payload)   # separate process
    return {"digest": digest}

@app.get("/file")
async def file_route(path: str) -> dict:
    data = await anyio.to_thread.run_sync(blocking_io, path)         # threadpool
    return {"bytes": len(data)}
```

> **TRAP.** Most candidates say "use `to_thread` for CPU work". Wrong — `to_thread` moves a *blocking* call off the loop, but a CPU-bound call still holds the GIL, so it blocks every other Python thread in the process. Threads for I/O, processes for CPU.

**If they push back — "how do you raise the 40-thread limit?"** In `lifespan`: `anyio.to_thread.current_default_thread_limiter().total_tokens = 80`. But raising it is usually the wrong instinct — it's a symptom that a blocking library should be replaced with an async one.

---

### Q6. Write me a production HTTP client. Connection pooling, timeouts, retries.

**Answer:** One long-lived `httpx.AsyncClient` per process, created in the app lifespan, never per-request — a per-request client throws away the connection pool and the TLS handshake, which is typically the single biggest latency regression I see in integration code. httpx defaults are `max_connections=100`, `max_keepalive_connections=20`, `keepalive_expiry=5.0 s`, and a **5-second** timeout on all four phases (connect/read/write/pool).

Retries: httpx's built-in `transport retries` only covers connection-establishment failures. Anything status-code-driven — 429, 502, 503, 504 — I handle myself with backoff + jitter, and only on idempotent methods or on POSTs carrying an `Idempotency-Key`.

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI

TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=2.0)
LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=30.0)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(
        base_url="https://erp.internal/api/v2",
        timeout=TIMEOUT,
        limits=LIMITS,
        http2=True,                                   # needs the h2 extra installed
        transport=httpx.AsyncHTTPTransport(retries=2),   # connect-level retries only
        headers={"User-Agent": "ey-integration/1.0"},
    ) as client:
        app.state.http = client
        yield
    # client closed here — pool drained on shutdown

app = FastAPI(lifespan=lifespan)
```

**If they push back — "pool exhaustion, what happens?"** The 101st concurrent request waits for a free connection and fails with `httpx.PoolTimeout` after `pool=2.0 s`. That's the signal to either raise `max_connections` or — better — put a semaphore upstream so you shed load deliberately instead of timing out randomly.

---

### Q7. The GIL — when does it actually matter to you?

**Answer:** One mutex; only one thread executes CPython bytecode at a time. It is released around I/O syscalls and inside C extensions, so an I/O-bound integration service is unaffected — this is why asyncio and threads both work fine for HTTP fan-out. It bites exactly when the work is CPU in pure Python: XML canonicalisation of a 50 MB SOAP payload, JSON parse of a large batch, crypto, compression.

For those I use `ProcessPoolExecutor` (or push the work to a separate worker deployment). PEP 703 free-threading shipped experimentally in 3.13 and became officially supported-but-opt-in in 3.14; not something I'd assume in an enterprise delivery estate yet.

**If they push back — "so why is asyncio faster than threads for 1000 HTTP calls?"** Not GIL — memory and scheduler cost. 1000 OS threads is ~8 MB of stack each by default plus kernel context switching; 1000 coroutines is 1000 small heap objects on one thread.

---

### Q8. `dataclass` vs pydantic v2 — where do you draw the line?

**Answer:** Pydantic at the **boundary**, dataclass in the **core**. Anything crossing the process edge — request bodies, response models, config, an incoming Service Bus message, an LLM's JSON — gets a pydantic model, because I want coercion, validation, and a JSON Schema I can publish in OpenAPI. Internal value objects that are already trusted get `@dataclass(frozen=True, slots=True)`, which is far cheaper to construct.

Pydantic v2's core is Rust (`pydantic-core`); the project's own benchmarks put it roughly 4–50× faster than v1 depending on the model.

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

class OrderIn(BaseModel):                                  # boundary
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    order_id: Annotated[str, Field(min_length=1, max_length=64)]
    channel: Literal["web", "partner", "erp"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    placed_at: datetime

    @field_validator("order_id")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()

@dataclass(frozen=True, slots=True)                        # internal
class CanonicalOrder:
    order_id: str
    channel: str
    amount_minor: int
    placed_at: datetime
```

> **TRAP.** `extra="forbid"` vs the default `extra="ignore"`. For an *inbound partner* API, forbid — an unexpected field is almost always a mapping bug and you want the 422 now, not a silently dropped field discovered at month-end reconciliation. For an *outbound* upstream response you are parsing, ignore — otherwise their additive change breaks you, which violates the whole point of tolerant reading.

**If they push back — "how do you validate a list of 100k rows fast?"** `TypeAdapter(list[OrderIn]).validate_python(rows)` — one Rust-side pass instead of 100k Python-level `model_validate` calls.

---

### Q9. Show me `typing.Protocol` and why you'd use it over an ABC.

**Answer:** `Protocol` is structural typing — the class satisfies it by shape, no inheritance, no import coupling. That is exactly what I want for an integration adapter seam: the SAP client, the Service Bus publisher, and the in-memory fake in tests all satisfy `MessagePublisher` without any of them importing my base class.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MessagePublisher(Protocol):
    async def publish(self, topic: str, body: bytes, *, message_id: str) -> None: ...

class ServiceBusPublisher:                       # no inheritance
    def __init__(self, sender) -> None:
        self._sender = sender

    async def publish(self, topic: str, body: bytes, *, message_id: str) -> None:
        from azure.servicebus import ServiceBusMessage
        await self._sender.send_messages(ServiceBusMessage(body, message_id=message_id))

class FakePublisher:                             # test double, same shape
    def __init__(self) -> None:
        self.sent: list[tuple[str, bytes, str]] = []

    async def publish(self, topic: str, body: bytes, *, message_id: str) -> None:
        self.sent.append((topic, body, message_id))

async def handle(pub: MessagePublisher, order_id: str) -> None:
    await pub.publish("orders", b"{}", message_id=order_id)
```

**If they push back — "when ABC then?"** When I want shared implementation, or when I want instantiation to *fail loudly* if a method is missing. `runtime_checkable` Protocols only check method *names* at runtime, not signatures — so they are a static tool, not a guard rail.

---

### Q10. Context managers and `AsyncExitStack`.

**Answer:** Every resource with a lifetime gets a context manager, because `finally` semantics survive cancellation and exceptions. `AsyncExitStack` is the one to name when the *number* of resources is dynamic — opening N tenant connections, or conditionally entering a transaction.

```python
from contextlib import AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator

import httpx

@asynccontextmanager
async def traced(name: str) -> AsyncIterator[None]:
    import time
    t0 = time.perf_counter()
    try:
        yield
    finally:
        print(f"{name} took {(time.perf_counter() - t0) * 1000:.1f}ms")

async def call_all(urls: list[str]) -> list[int]:
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(traced("fan-out"))
        client = await stack.enter_async_context(httpx.AsyncClient(timeout=5.0))
        return [(await client.get(u)).status_code for u in urls]
```

---

### Q11. Stream a huge payload without loading it into memory.

**Answer:** Generators, and never `.json()` / `.read()` on a large response. For outbound, an async generator feeding a `StreamingResponse`; for inbound, `client.stream()` plus `aiter_bytes` / `aiter_lines`. The rule is that peak RSS should be O(chunk), not O(payload).

```python
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def ndjson_from_upstream(client: httpx.AsyncClient, url: str) -> AsyncIterator[bytes]:
    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():        # never resp.json()
            if line:
                yield line.encode() + b"\n"

@app.get("/export")
async def export() -> StreamingResponse:
    client = httpx.AsyncClient(timeout=httpx.Timeout(connect=3, read=None, write=10, pool=2))
    return StreamingResponse(
        ndjson_from_upstream(client, "https://erp.internal/exports/orders"),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},          # stop nginx/APIM buffering the stream
    )
```

> **TRAP.** `read=None` on a streaming download. The read timeout in httpx is per-chunk, not per-response — but a long-poll or SSE endpoint that legitimately sends nothing for 60 s will still trip a 10 s read timeout. Set `read=None` only for genuine streams, and keep `connect` finite.

---

### Q12. `functools.lru_cache` — and where it goes wrong.

**Answer:** Great for pure, hashable-argument, process-local lookups: parsed config, a compiled regex, a JWKS-derived key object, a tenant→routing-table map. `@cache` is `lru_cache(maxsize=None)` — unbounded, so only for a genuinely finite key space.

Three failure modes to call out: it does not work on coroutine functions (you cache the coroutine object, which can only be awaited once); on a method it holds a strong reference to `self` and leaks; and it has no TTL, so it is wrong for anything that rotates.

```python
import asyncio, time
from functools import lru_cache

@lru_cache(maxsize=512)
def routing_key(tenant: str, doc_type: str) -> str:
    return f"{tenant}.{doc_type}".lower()

class TTLCache:
    """Async-safe, TTL'd, single-flight. What lru_cache cannot do."""
    def __init__(self, ttl: float) -> None:
        self._ttl = ttl
        self._value: object | None = None
        self._expires = 0.0
        self._lock = asyncio.Lock()

    async def get(self, loader):
        now = time.monotonic()
        if self._value is not None and now < self._expires:
            return self._value
        async with self._lock:                       # single-flight: one refresh, not N
            if self._value is not None and time.monotonic() < self._expires:
                return self._value
            self._value = await loader()
            self._expires = time.monotonic() + self._ttl
            return self._value
```

---

### Q13. Structured logging with a correlation ID.

**Answer:** JSON lines, one event per log call, and a `correlation_id` on every single line so a failed order can be traced from APIM through the API, the queue, and the downstream. I take the ID from an inbound header if present (`traceparent` per W3C, or the client's `X-Correlation-Id`), otherwise mint a UUID, and I always echo it back on the response so the caller can quote it in a ticket.

```python
import json, logging, sys, uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": correlation_id.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload, separators=(",", ":"))

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(handlers=[handler], level=logging.INFO, force=True)
log = logging.getLogger("api")

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        token = correlation_id.set(cid)
        try:
            response = await call_next(request)
            response.headers["x-correlation-id"] = cid
            return response
        finally:
            correlation_id.reset(token)

app = FastAPI()
app.add_middleware(CorrelationMiddleware)

@app.get("/orders/{oid}")
async def get_order(oid: str) -> dict:
    log.info("order lookup", extra={"extra_fields": {"order_id": oid}})
    return {"order_id": oid}
```

**If they push back — "how does the ID survive the queue hop?"** I copy it onto the message's `application_properties` (Service Bus) / headers (Kafka) on publish, and re-`set()` the contextvar at the top of the consumer handler. Without that, the async leg of a flow is untraceable — which is the most common observability gap I see in integration estates.

---

### Q14. Why `contextvars` and not thread-locals?

**Answer:** A thread-local is wrong under asyncio because thousands of coroutines share one thread — every request would see the same value. `ContextVar` is scoped to the *task*: `asyncio.create_task()` copies the current context, so a child task inherits the correlation ID but its own writes don't leak back to the parent. That copy-on-task-creation is the property to name; it's what makes it safe.

Caveat worth saying: a value set inside a task is not visible to the parent after the task ends, and `run_in_executor` runs in a thread that does *not* automatically carry the context — use `contextvars.copy_context().run(fn)` if you need it there.

---

### Q15. `__slots__`, `weakref`, and memory in a long-running consumer.

**Answer:** For a consumer holding tens of thousands of in-flight message objects, `@dataclass(slots=True)` drops the per-instance `__dict__` — typically a large saving on small objects, and it makes typos raise `AttributeError` instead of silently creating a field. The real leaks in integration services are almost never the allocator: they're unbounded dicts used as caches, an `asyncio.Queue()` with no `maxsize`, and tasks kept in a list that is never pruned.

Diagnose with `tracemalloc.take_snapshot()` diffs, not guesswork:

```python
import tracemalloc

tracemalloc.start(10)
snap1 = tracemalloc.take_snapshot()
# ... run 10k messages ...
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:10]:
    print(stat)
```

---

## 2. Build-it problems with full solutions

Every one of these is a plausible 20-minute pairing exercise for this JD. For each: the problem, the clarifying questions that earn marks *before* you type, the code, complexity, and the follow-up they will add.

---

### P1. Idempotent POST with an Idempotency-Key

**Problem.** `POST /payments` must be safe to retry. The client sends `Idempotency-Key: <uuid>`. Same key + same body = return the original response, don't re-charge. Handle the case where the first request is still in flight.

**Clarifying questions to ask (say these out loud):**
1. How long must the key be honoured? (Stripe uses 24 h; I'll assume 24 h.)
2. Same key, *different* body — error, or serve the cached response? (Correct answer: error, 422 — it means a client bug.)
3. Is the key scoped per-tenant/per-endpoint, or global? (Scope it — otherwise tenant A can collide with tenant B.)
4. Redis available, or must state live in the same SQL DB as the payment? (SQL is stronger: the dedupe row and the side effect commit atomically. Redis is the common answer; say you know the difference.)

**Solution.**

```python
# idempotency.py
from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, FastAPI, Header, HTTPException, Request, Response

IDEMPOTENCY_TTL = 24 * 60 * 60      # advertised retention window
IN_FLIGHT_TTL = 60                  # must exceed p99.9 handler latency, else a slow first
                                    # call expires and the retry double-charges

# Atomic claim-or-read. One round trip, no TOCTOU window.
CLAIM_LUA = """
local state = redis.call('HGET', KEYS[1], 'state')
if state == false then
  redis.call('HSET', KEYS[1], 'state', 'in_flight', 'fp', ARGV[1])
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[2]))
  return {'acquired', '', ''}
end
local fp = redis.call('HGET', KEYS[1], 'fp')
if fp ~= ARGV[1] then
  return {'fingerprint_mismatch', '', ''}
end
if state == 'in_flight' then
  return {'in_flight', '', ''}
end
local body = redis.call('HGET', KEYS[1], 'body')
local status = redis.call('HGET', KEYS[1], 'status')
return {'replay', body, status}
"""

class IdempotencyStore:
    def __init__(self, client: redis.Redis) -> None:
        self._r = client
        self._claim = client.register_script(CLAIM_LUA)   # SCRIPT LOAD + EVALSHA, auto NOSCRIPT retry

    @staticmethod
    def _key(tenant: str, route: str, idem_key: str) -> str:
        return f"idem:{tenant}:{route}:{idem_key}"

    @staticmethod
    def fingerprint(method: str, path: str, body: bytes) -> str:
        return hashlib.sha256(b"|".join([method.encode(), path.encode(), body])).hexdigest()

    async def claim(self, key: str, fp: str) -> tuple[str, str, str]:
        outcome, body, status = await self._claim(keys=[key], args=[fp, IN_FLIGHT_TTL])
        dec = lambda v: v.decode() if isinstance(v, bytes) else v
        return dec(outcome), dec(body), dec(status)

    async def commit(self, key: str, status: int, body: dict[str, Any]) -> None:
        async with self._r.pipeline(transaction=True) as pipe:
            pipe.hset(key, mapping={"state": "done", "status": str(status),
                                    "body": json.dumps(body, separators=(",", ":"))})
            pipe.expire(key, IDEMPOTENCY_TTL)
            await pipe.execute()

    async def release(self, key: str) -> None:
        """Handler blew up. Drop the claim so an immediate retry can proceed."""
        await self._r.delete(key)


router = APIRouter()

async def charge(payload: dict[str, Any]) -> dict[str, Any]:
    return {"payment_id": "pay_123", "status": "captured", "amount": payload["amount"]}


@router.post("/payments")
async def create_payment(
    request: Request,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> dict[str, Any]:
    store: IdempotencyStore = request.app.state.idem
    raw = await request.body()
    key = store._key(x_tenant_id, "POST /payments", idempotency_key)
    fp = store.fingerprint("POST", "/payments", raw)

    outcome, cached_body, cached_status = await store.claim(key, fp)

    if outcome == "fingerprint_mismatch":
        raise HTTPException(422, "Idempotency-Key reused with a different request body")
    if outcome == "in_flight":
        # The original is still running. Do NOT run a second charge.
        raise HTTPException(409, "A request with this Idempotency-Key is in progress",
                            headers={"Retry-After": "1"})
    if outcome == "replay":
        response.status_code = int(cached_status)
        response.headers["Idempotent-Replay"] = "true"
        return json.loads(cached_body)

    try:
        result = await charge(json.loads(raw))
    except Exception:
        await store.release(key)          # transient failure -> allow retry
        raise
    await store.commit(key, 201, result)
    response.status_code = 201
    return result


def build() -> FastAPI:
    app = FastAPI()
    app.state.idem = IdempotencyStore(redis.from_url("redis://localhost:6379/0"))
    app.include_router(router)
    return app
```

**Complexity.** O(1) per request — one Lua `EVALSHA` on the claim path, one pipelined `HSET`+`EXPIRE` on commit. Storage O(keys × 24 h).

**The in-flight race, explicitly.** Without the atomic claim, two concurrent retries both `GET` a miss and both charge. The Lua script makes check-and-set a single atomic server-side operation — Redis guarantees a script executes atomically and blocks all other server activity for its runtime. Returning **409 + `Retry-After`** rather than blocking is deliberate: holding the second request open ties up a connection and can outlive the client's own timeout.

**If they push back:**
- *"Why not just a Redis `SET NX`?"* You can, for the claim — but you then need a second key or a second round trip for the fingerprint and the cached response, which reopens the race. One script, one round trip.
- *"Redis loses the key on failover, then what?"* Redis replication is asynchronous, so a failover can lose the claim and you can double-charge. If double-charging is unacceptable, the dedupe row must live in the **same transaction as the side effect** — `INSERT INTO idempotency(key) ... ON CONFLICT DO NOTHING` in the payment's own DB transaction. Redis is the fast path; SQL is the correct one.
- *"How do you clean up?"* TTL only. Never a cron delete.

---

### P2. Rate limiter — token bucket and sliding window

**Problem.** Protect a downstream that allows 100 requests/second per API key. Build it in-process first, then make it correct across 6 pods.

**Clarifying questions:** Per-key or per-tenant? Do bursts need to be allowed (token bucket) or strictly smoothed (sliding window)? Is a small over-admit acceptable at pod boundaries? What do you return — 429 with `Retry-After`, or queue?

**In-process token bucket.**

```python
import asyncio, time
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    capacity: float                # burst size
    refill_per_sec: float          # sustained rate
    _tokens: float = field(init=False)
    _ts: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._ts = time.monotonic()          # monotonic: immune to NTP steps

    async def take(self, cost: float = 1.0) -> tuple[bool, float]:
        """Returns (allowed, retry_after_seconds)."""
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(self.capacity, self._tokens + (now - self._ts) * self.refill_per_sec)
            self._ts = now
            if self._tokens >= cost:
                self._tokens -= cost
                return True, 0.0
            return False, (cost - self._tokens) / self.refill_per_sec

    async def acquire(self, cost: float = 1.0) -> None:
        """Blocking variant — shape traffic instead of rejecting it."""
        while True:
            ok, wait = await self.take(cost)
            if ok:
                return
            await asyncio.sleep(wait)
```

**Distributed token bucket (Redis + Lua).**

```python
import time
import redis.asyncio as redis

TOKEN_BUCKET_LUA = """
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])   -- tokens per second
local now_ms   = tonumber(ARGV[3])
local cost     = tonumber(ARGV[4])

local st     = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(st[1])
local ts     = tonumber(st[2])
if tokens == nil then
  tokens = capacity
  ts = now_ms
end

local elapsed = math.max(0, now_ms - ts) / 1000.0
tokens = math.min(capacity, tokens + elapsed * rate)

local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end

redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', KEYS[1], math.ceil((capacity / rate) * 1000) + 1000)

local retry_ms = 0
if allowed == 0 then
  retry_ms = math.ceil(((cost - tokens) / rate) * 1000)
end
return {allowed, math.floor(tokens), retry_ms}
"""

SLIDING_WINDOW_LUA = """
local now    = tonumber(ARGV[1])   -- ms
local window = tonumber(ARGV[2])   -- ms
local limit  = tonumber(ARGV[3])
local member = ARGV[4]             -- unique per request, e.g. uuid4

redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - window)
local used = redis.call('ZCARD', KEYS[1])
if used < limit then
  redis.call('ZADD', KEYS[1], now, member)
  redis.call('PEXPIRE', KEYS[1], window)
  return {1, limit - used - 1, 0}
end
local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
redis.call('PEXPIRE', KEYS[1], window)
return {0, 0, math.ceil(tonumber(oldest[2]) + window - now)}
"""

class DistributedLimiter:
    def __init__(self, client: redis.Redis) -> None:
        self._bucket = client.register_script(TOKEN_BUCKET_LUA)
        self._window = client.register_script(SLIDING_WINDOW_LUA)

    async def allow_burst(self, key: str, capacity: int, rate: float) -> tuple[bool, int, int]:
        now_ms = int(time.time() * 1000)
        allowed, remaining, retry_ms = await self._bucket(
            keys=[f"rl:tb:{key}"], args=[capacity, rate, now_ms, 1])
        return bool(allowed), int(remaining), int(retry_ms)

    async def allow_smooth(self, key: str, limit: int, window_ms: int, member: str) -> tuple[bool, int, int]:
        now_ms = int(time.time() * 1000)
        allowed, remaining, retry_ms = await self._window(
            keys=[f"rl:sw:{key}"], args=[now_ms, window_ms, limit, member])
        return bool(allowed), int(remaining), int(retry_ms)
```

FastAPI wiring — always emit the standard headers:

```python
from fastapi import Depends, HTTPException, Request

async def rate_limit(request: Request) -> None:
    key = request.headers.get("Ocp-Apim-Subscription-Key", "anon")
    limiter: DistributedLimiter = request.app.state.limiter
    ok, remaining, retry_ms = await limiter.allow_burst(key, capacity=200, rate=100.0)
    if not ok:
        raise HTTPException(429, "rate limit exceeded", headers={
            "Retry-After": str(max(1, retry_ms // 1000)),
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
        })
```

**Complexity.** Token bucket O(1) time, O(1) memory per key. Sliding-window log is O(log n) per op and O(limit) memory per key — for limit=100 that is fine, for limit=1,000,000 it is not; use a sliding-window *counter* (two fixed buckets, weighted) instead.

**If they push back:**
- *"Why Lua and not `INCR` + `EXPIRE`?"* Because those are two commands: a crash between them leaves a key with no TTL, and the read-modify-write on the token count is not atomic across pods. Lua collapses it into one atomic server-side execution.
- *"Fixed window vs sliding?"* Fixed window allows 2× the limit across a boundary — 100 in the last millisecond of minute 1 and 100 in the first millisecond of minute 2. Sliding window log is exact; sliding window counter is a good approximation at O(1) memory.
- *"APIM already does this."* Correct, and that's where I'd put the *first* layer — `rate-limit-by-key` with `counter-key="@(context.Subscription.Id)"`. But APIM's own docs say throttling "is never completely accurate" because counters are tracked independently per gateway instance and per region — so a hard downstream contract still needs an app-level bucket.

---

### P3. Retry with exponential backoff + full jitter, plus a circuit breaker

**Problem.** Wrap a flaky downstream call. Retry transient failures, don't retry client errors, don't retry forever, and stop hammering a downstream that is genuinely down.

**Clarifying questions:** Which errors are retryable? Is the operation idempotent (may I retry a POST)? Is there an overall request deadline that caps total retry time? Do we honour `Retry-After` when the server sends one?

**Solution.**

```python
from __future__ import annotations

import asyncio
import enum
import functools
import logging
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import ParamSpec, TypeVar

import httpx

log = logging.getLogger(__name__)
P = ParamSpec("P")
T = TypeVar("T")

RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})

class Transient(Exception):
    def __init__(self, msg: str, retry_after: float | None = None) -> None:
        super().__init__(msg)
        self.retry_after = retry_after


def classify(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout,
                        httpx.PoolTimeout, httpx.RemoteProtocolError, Transient)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    return False


def retry_after_of(exc: BaseException) -> float | None:
    if isinstance(exc, Transient):
        return exc.retry_after
    if isinstance(exc, httpx.HTTPStatusError):
        hdr = exc.response.headers.get("Retry-After")
        if hdr and hdr.isdigit():
            return float(hdr)
    return None


class State(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5          # consecutive failures before tripping
    reset_timeout: float = 30.0         # seconds OPEN before a probe is allowed
    half_open_max: int = 1              # concurrent probes in HALF_OPEN
    name: str = "default"

    _state: State = field(default=State.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)
    _probes: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def before(self) -> None:
        async with self._lock:
            if self._state is State.OPEN:
                if time.monotonic() - self._opened_at < self.reset_timeout:
                    raise Transient(f"circuit '{self.name}' is OPEN",
                                    retry_after=self.reset_timeout)
                self._state = State.HALF_OPEN
                self._probes = 0
            if self._state is State.HALF_OPEN:
                if self._probes >= self.half_open_max:
                    raise Transient(f"circuit '{self.name}' HALF_OPEN, probe in flight")
                self._probes += 1

    async def on_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._probes = 0
            if self._state is not State.CLOSED:
                log.info("circuit closing", extra={"extra_fields": {"circuit": self.name}})
            self._state = State.CLOSED

    async def on_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            self._probes = max(0, self._probes - 1)
            if self._state is State.HALF_OPEN or self._failures >= self.failure_threshold:
                self._state = State.OPEN
                self._opened_at = time.monotonic()
                log.warning("circuit opened",
                            extra={"extra_fields": {"circuit": self.name,
                                                    "failures": self._failures}})


def resilient(
    *,
    attempts: int = 4,
    base: float = 0.2,
    cap: float = 20.0,
    breaker: CircuitBreaker | None = None,
    deadline: float | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Exponential backoff with FULL jitter: sleep = uniform(0, min(cap, base * 2**n))."""
    def decorate(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            started = time.monotonic()
            last: BaseException | None = None
            for attempt in range(attempts):
                if breaker is not None:
                    await breaker.before()
                try:
                    result = await fn(*args, **kwargs)
                except asyncio.CancelledError:
                    raise                                   # never swallow cancellation
                except BaseException as exc:                # noqa: BLE001
                    if breaker is not None:
                        await breaker.on_failure()
                    if not classify(exc) or attempt == attempts - 1:
                        raise
                    last = exc
                    hinted = retry_after_of(exc)
                    backoff = min(cap, base * (2 ** attempt))
                    sleep = hinted if hinted is not None else random.uniform(0.0, backoff)
                    if deadline is not None and time.monotonic() - started + sleep > deadline:
                        raise TimeoutError("retry budget exhausted") from exc
                    log.warning("retrying", extra={"extra_fields": {
                        "fn": fn.__name__, "attempt": attempt + 1, "sleep_s": round(sleep, 3),
                        "error": type(exc).__name__}})
                    await asyncio.sleep(sleep)
                else:
                    if breaker is not None:
                        await breaker.on_success()
                    return result
            raise AssertionError("unreachable") from last
        return wrapper
    return decorate


erp_breaker = CircuitBreaker(name="erp", failure_threshold=5, reset_timeout=30.0)

@resilient(attempts=4, base=0.2, cap=10.0, breaker=erp_breaker, deadline=15.0)
async def get_order(client: httpx.AsyncClient, order_id: str) -> dict:
    r = await client.get(f"/orders/{order_id}")
    r.raise_for_status()
    return r.json()
```

**Complexity.** O(attempts) calls; worst-case added latency bounded by `deadline`. Expected total sleep with full jitter over 4 attempts at base 0.2 s, cap 10 s ≈ 0.1 + 0.2 + 0.4 = 0.7 s.

**Why full jitter specifically.** Plain exponential backoff synchronises every client that failed at the same instant — they all retry at t+1 s, t+2 s, t+4 s, and re-storm the recovering service. Full jitter (`uniform(0, backoff)`) decorrelates them completely. "Equal jitter" (`backoff/2 + uniform(0, backoff/2)`) is the compromise if you need a latency floor.

**If they push back:**
- *"Why not just retry everything?"* Retrying a 400 or 422 is a guaranteed waste and, on a non-idempotent POST without an idempotency key, a duplicate side effect. Retry the transient set only.
- *"Where does the circuit breaker live in Azure?"* On the APIM **backend** entity, not as a policy — `circuitBreaker.rules[]` with `failureCondition { count, interval, statusCodeRanges }`, `tripDuration`, and `acceptRetryAfter: true`. Not supported in the Consumption tier, one rule per backend, and it trips approximately because gateway instances don't synchronise.
- *"HALF_OPEN with 50 concurrent requests?"* That's exactly why `half_open_max` exists — one probe decides; the rest get the fast fail.

---

### P4. Webhook receiver — signature, replay window, fast-ack, dedupe

**Problem.** Receive webhooks from a partner. Verify authenticity, reject replays, respond in under 200 ms, process reliably, and tolerate the partner sending the same event twice.

**Clarifying questions:** What signature scheme and which bytes are signed? Is a timestamp in the signed payload? What's their retry policy and timeout? Is ordering guaranteed (almost never)? What's the event ID field for dedupe?

**Solution.**

```python
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time

import redis.asyncio as redis
from fastapi import APIRouter, FastAPI, Header, HTTPException, Request, Response, status

log = logging.getLogger(__name__)
router = APIRouter()

TOLERANCE_SECONDS = 300          # Stripe's default tolerance is 5 minutes; mirror it
DEDUPE_TTL = 7 * 24 * 60 * 60    # > partner's maximum retry horizon


def parse_signature_header(header: str) -> tuple[int, list[str]]:
    """Stripe-style: 't=1690000000,v1=abc...,v1=def...'"""
    ts = 0
    sigs: list[str] = []
    for part in header.split(","):
        k, _, v = part.strip().partition("=")
        if k == "t":
            ts = int(v)
        elif k == "v1":
            sigs.append(v)
    if not ts or not sigs:
        raise HTTPException(400, "malformed signature header")
    return ts, sigs


def verify(secret: str, raw_body: bytes, header: str, now: int | None = None) -> None:
    ts, sigs = parse_signature_header(header)
    now = now if now is not None else int(time.time())
    if abs(now - ts) > TOLERANCE_SECONDS:
        raise HTTPException(400, "timestamp outside tolerance window")   # replay defence
    signed_payload = f"{ts}.".encode() + raw_body
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in sigs):          # constant time
        raise HTTPException(401, "signature mismatch")


@router.post("/webhooks/partner", status_code=status.HTTP_202_ACCEPTED)
async def receive(
    request: Request,
    response: Response,
    signature: str = Header(alias="X-Partner-Signature"),
) -> dict:
    raw = await request.body()                  # RAW BYTES — never re-serialise before verifying
    verify(request.app.state.webhook_secret, raw, signature)

    try:
        event = json.loads(raw)
        event_id = event["id"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise HTTPException(400, "unparseable event") from exc

    r: redis.Redis = request.app.state.redis
    # SET NX EX is atomic: exactly one caller wins the claim.
    first_time = await r.set(f"wh:seen:{event_id}", "1", nx=True, ex=DEDUPE_TTL)
    if not first_time:
        log.info("duplicate webhook", extra={"extra_fields": {"event_id": event_id}})
        return {"status": "duplicate", "event_id": event_id}

    try:
        # Durable handoff BEFORE we ack. If this fails we must NOT return 202.
        await request.app.state.publisher.publish(
            "partner-events", raw, message_id=event_id
        )
    except Exception:
        await r.delete(f"wh:seen:{event_id}")   # release the claim so their retry works
        raise HTTPException(503, "temporarily unable to accept event")

    response.headers["X-Correlation-Id"] = event_id
    return {"status": "accepted", "event_id": event_id}
```

**Complexity.** O(len(body)) for the HMAC, O(1) Redis. Latency budget: HMAC over 100 KB is microseconds; the queue publish dominates at single-digit ms.

**The three things they're checking:**
1. **Raw bytes.** `json.loads(raw)` then `json.dumps(...)` and signing *that* fails on key ordering and whitespace. Verify the exact bytes received. In FastAPI that means `await request.body()`, not a pydantic-parsed model.
2. **`hmac.compare_digest`.** A `==` comparison on a hex digest is a timing oracle. GitHub's own docs call this out explicitly for `X-Hub-Signature-256`.
3. **Fast-ack.** Return 202 immediately and do the work off the request. Partners time out at 5–30 s and retry; a 30-second synchronous handler turns one event into five duplicates.

**If they push back:**
- *"Why is the timestamp inside the signed payload?"* Because if it weren't, an attacker could replay a captured body with a fresh timestamp. Signing `"{ts}.{body}"` binds them.
- *"Dedupe window length?"* Longer than the partner's maximum retry horizon. Event Grid, for comparison, retries on a schedule out to 24 hours with a configurable event TTL of 1–1440 minutes (default 1440). A 7-day window is cheap insurance.
- *"The `SET NX` claim then a crash — event lost?"* Yes, that's the hole, and it's why I release the claim on publish failure. The airtight version writes the dedupe key and the event into the **same database transaction** as an outbox row ([P6](#p6-transactional-outbox)).

---

### P5. Message consumer — bounded concurrency, manual settle, SIGTERM shutdown

**Problem.** Consume from Azure Service Bus (or Kafka) in a Kubernetes pod. Process up to 20 messages concurrently. Settle each message explicitly. On `SIGTERM`, finish in-flight work and exit cleanly without losing or duplicating messages.

**Clarifying questions:** At-least-once acceptable? What's the max processing time per message vs the lock duration? Ordering required (sessions/partition keys)? What's `terminationGracePeriodSeconds` on the deployment?

**Solution — Azure Service Bus.**

```python
from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus import ServiceBusReceiveMode
from azure.servicebus.aio import AutoLockRenewer, ServiceBusClient, ServiceBusReceiver
from azure.servicebus.exceptions import MessageLockLostError

log = logging.getLogger(__name__)

NAMESPACE = "ey-int-prod.servicebus.windows.net"
QUEUE = "orders"
CONCURRENCY = 20
PREFETCH = 40                # ~2x concurrency; higher risks lock expiry on parked messages
MAX_WAIT = 5                 # seconds a receive_messages call blocks with nothing available


class Consumer:
    def __init__(self) -> None:
        self._stopping = asyncio.Event()

    def request_stop(self, signame: str) -> None:
        log.warning("shutdown signal", extra={"extra_fields": {"signal": signame}})
        self._stopping.set()

    async def handle(self, msg) -> None:
        body = b"".join(msg.body)
        cid = (msg.application_properties or {}).get(b"correlation-id", b"-").decode()
        log.info("processing", extra={"extra_fields": {
            "message_id": msg.message_id, "delivery_count": msg.delivery_count,
            "correlation_id": cid}})
        await asyncio.sleep(0.05)          # real work here

    async def _process_one(self, receiver: ServiceBusReceiver, msg, sem: asyncio.Semaphore) -> None:
        async with sem:
            try:
                await self.handle(msg)
                await receiver.complete_message(msg)
            except MessageLockLostError:
                # Lock expired mid-flight. Do NOT settle — the broker already redelivered it.
                # Lock loss does not increment delivery_count.
                log.error("lock lost", extra={"extra_fields": {"message_id": msg.message_id}})
            except ValueError as exc:
                # Poison / unparseable: dead-letter immediately, do not burn 10 deliveries.
                await receiver.dead_letter_message(
                    msg, reason="ValidationError", error_description=str(exc)[:4096])
            except Exception as exc:                                    # noqa: BLE001
                log.exception("transient handler failure")
                await receiver.abandon_message(msg)   # +1 delivery_count; auto-DLQ at 10

    async def run(self) -> None:
        sem = asyncio.Semaphore(CONCURRENCY)
        inflight: set[asyncio.Task] = set()

        async with DefaultAzureCredential() as cred, \
                   ServiceBusClient(NAMESPACE, cred) as client, \
                   AutoLockRenewer(max_lock_renewal_duration=600) as renewer, \
                   client.get_queue_receiver(
                       QUEUE,
                       receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                       prefetch_count=PREFETCH,
                       auto_lock_renewer=renewer,
                   ) as receiver:

            while not self._stopping.is_set():
                msgs = await receiver.receive_messages(
                    max_message_count=CONCURRENCY, max_wait_time=MAX_WAIT)
                for msg in msgs:
                    task = asyncio.create_task(self._process_one(receiver, msg, sem))
                    inflight.add(task)
                    task.add_done_callback(inflight.discard)   # or they leak

            # --- graceful drain ---
            log.info("draining", extra={"extra_fields": {"inflight": len(inflight)}})
            if inflight:
                done, pending = await asyncio.wait(inflight, timeout=25)
                for t in pending:
                    t.cancel()
                with suppress(asyncio.CancelledError):
                    await asyncio.gather(*pending, return_exceptions=True)
            log.info("drained, exiting")


async def main() -> None:
    consumer = Consumer()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, consumer.request_stop, sig.name)
    await consumer.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

**Kafka variant — the key differences are commit semantics.**

```python
import asyncio, signal
from aiokafka import AIOKafkaConsumer

async def run_kafka(stopping: asyncio.Event) -> None:
    consumer = AIOKafkaConsumer(
        "orders",
        bootstrap_servers="kafka:9092",
        group_id="order-processor",
        enable_auto_commit=False,          # manual commit or you lose at-least-once
        auto_offset_reset="earliest",
        max_poll_records=100,              # broker default is 500
        isolation_level="read_committed",  # only see committed transactional writes
    )
    await consumer.start()
    try:
        while not stopping.is_set():
            batches = await consumer.getmany(timeout_ms=1000, max_records=100)
            for tp, records in batches.items():
                for rec in records:
                    await handle(rec)              # process
                await consumer.commit({tp: rec.offset + 1})   # commit AFTER processing
    finally:
        await consumer.stop()                      # leaves the group -> fast rebalance
```

**Complexity.** Throughput = CONCURRENCY / mean-handler-latency. At 20 concurrent and 50 ms, ~400 msg/s per pod.

**The numbers that make this answer senior:**

| Fact | Value |
|---|---|
| Service Bus default PeekLock duration | 1 minute |
| Service Bus **maximum** lock duration | 5 minutes (renew beyond that) |
| Default `MaxDeliveryCount` before auto-DLQ | 10 — cannot be disabled, only raised |
| Service Bus idle connection close | 10 minutes (drops the lock) |
| Kafka `max.poll.interval.ms` default | 300000 ms (5 min) — exceed it and you're evicted |
| Kafka `max.poll.records` default | 500 |
| Kafka `session.timeout.ms` default | 45000 ms (brokers 3.0+) |
| K8s `terminationGracePeriodSeconds` default | 30 seconds |

**If they push back:**
- *"What happens on SIGTERM without this code?"* The runtime kills the process, in-flight locks expire, and Service Bus redelivers — so at-least-once still holds, but you burn delivery counts and can DLQ good messages after 10 restarts. On Kafka it's worse: uncommitted offsets mean the whole batch replays.
- *"Grace period tuning?"* `terminationGracePeriodSeconds` must exceed max handler latency + drain. Default 30 s. For the HTTP side add a `preStop: exec sleep 5` so kube-proxy finishes removing the pod from endpoints *before* the app sees SIGTERM — otherwise you 502 in-flight requests.
- *"Ordering?"* Service Bus sessions give FIFO within a session ID; use `get_queue_receiver(session_id=...)` or `max_wait_time` on a session receiver. Kafka gives ordering per partition only. If they ask for global ordering, push back: it caps you at one consumer.

---

### P6. Transactional outbox

**Problem.** When an order is saved, an `OrderCreated` event must reach Service Bus. Writing to the DB and publishing to the broker are two systems — a crash between them either loses the event or publishes a phantom. Fix it.

**Clarifying questions:** Is the DB Postgres/SQL Server (both support `SKIP LOCKED`)? Is ordering per-aggregate required? Do we need CDC (Debezium) or is polling acceptable? How many relay instances?

**Schema.**

```sql
CREATE TABLE outbox (
    id              BIGSERIAL   PRIMARY KEY,
    aggregate_type  TEXT        NOT NULL,
    aggregate_id    TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    payload         JSONB       NOT NULL,
    message_id      UUID        NOT NULL UNIQUE,   -- becomes Service Bus MessageId
    correlation_id  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at    TIMESTAMPTZ,
    attempts        INT         NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_error      TEXT
);

-- Partial index: the relay only ever scans unpublished rows, so the index stays tiny
-- even when the table has 100M historical rows.
CREATE INDEX outbox_pending_idx
    ON outbox (next_attempt_at, id)
    WHERE published_at IS NULL;
```

**Writer — same transaction as the business change.**

```python
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def create_order(session: AsyncSession, order: dict, correlation_id: str) -> str:
    async with session.begin():                     # one transaction, both writes
        await session.execute(
            text("INSERT INTO orders (order_id, customer_id, amount, placed_at) "
                 "VALUES (:oid, :cid, :amt, :ts)"),
            {"oid": order["order_id"], "cid": order["customer_id"],
             "amt": order["amount"], "ts": datetime.now(timezone.utc)},
        )
        await session.execute(
            text("INSERT INTO outbox (aggregate_type, aggregate_id, event_type, "
                 "payload, message_id, correlation_id) "
                 "VALUES ('order', :aid, 'OrderCreated', CAST(:p AS jsonb), :mid, :corr)"),
            {"aid": order["order_id"], "p": json.dumps(order),
             "mid": str(uuid.uuid4()), "corr": correlation_id},
        )
    return order["order_id"]
```

**Relay — poller with `FOR UPDATE SKIP LOCKED`.**

```python
import asyncio
import json
import logging

from azure.servicebus import ServiceBusMessage
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

log = logging.getLogger(__name__)

CLAIM_SQL = text("""
    SELECT id, event_type, payload, message_id, correlation_id, attempts
    FROM outbox
    WHERE published_at IS NULL
      AND next_attempt_at <= now()
    ORDER BY id
    LIMIT :batch
    FOR UPDATE SKIP LOCKED
""")

MARK_SENT_SQL = text("UPDATE outbox SET published_at = now() WHERE id = ANY(:ids)")

MARK_FAILED_SQL = text("""
    UPDATE outbox
       SET attempts = attempts + 1,
           last_error = :err,
           next_attempt_at = now() + (interval '1 second' * LEAST(300, POWER(2, attempts)))
     WHERE id = :id
""")


async def relay_once(sf: async_sessionmaker[AsyncSession], sender, batch: int = 100) -> int:
    async with sf() as session:
        async with session.begin():                       # locks held for this whole block
            rows = (await session.execute(CLAIM_SQL, {"batch": batch})).mappings().all()
            if not rows:
                return 0

            sent_ids: list[int] = []
            for row in rows:
                msg = ServiceBusMessage(
                    body=json.dumps(row["payload"]).encode(),
                    message_id=str(row["message_id"]),      # enables SB duplicate detection
                    subject=row["event_type"],
                    correlation_id=row["correlation_id"],
                    application_properties={"aggregate_id": str(row["id"])},
                )
                try:
                    await sender.send_messages(msg)
                    sent_ids.append(row["id"])
                except Exception as exc:                    # noqa: BLE001
                    log.warning("outbox publish failed",
                                extra={"extra_fields": {"outbox_id": row["id"],
                                                        "error": str(exc)[:200]}})
                    await session.execute(MARK_FAILED_SQL,
                                          {"id": row["id"], "err": str(exc)[:1000]})
            if sent_ids:
                await session.execute(MARK_SENT_SQL, {"ids": sent_ids})
            return len(sent_ids)


async def relay_loop(sf, sender, stopping: asyncio.Event) -> None:
    idle_backoff = 0.05
    while not stopping.is_set():
        n = await relay_once(sf, sender)
        if n == 0:
            await asyncio.sleep(min(2.0, idle_backoff))
            idle_backoff *= 2
        else:
            idle_backoff = 0.05
```

**Complexity.** One indexed range scan per poll, O(batch) sends. `SKIP LOCKED` means K relay instances scale linearly with zero lock contention — each grabs a disjoint set of rows.

**Why `SKIP LOCKED` and not `NOWAIT` or plain `FOR UPDATE`.** Postgres' own docs: "Skipping locked rows provides an inconsistent view of the data, so this is not suitable for general purpose work, but can be used to avoid lock contention with multiple consumers accessing a queue-like table." That is precisely this. Plain `FOR UPDATE` serialises every relay behind the first; `NOWAIT` errors instead of skipping.

**Delivery guarantee, stated precisely.** This is **at-least-once**. A crash after `send_messages` succeeds but before `UPDATE ... published_at` re-publishes on the next poll. That is why the consumer must be idempotent, and why `message_id` is a stable UUID — Service Bus duplicate detection (a configurable window on the queue/topic) uses `MessageId` to drop the repeat, and the consumer's own dedupe store catches the rest.

**If they push back:**
- *"Why not just publish after commit?"* Because the process can die in the microsecond between commit and publish, and now the order exists with no event — silent data divergence, discovered weeks later in reconciliation. The outbox makes the event durable in the same atomic unit as the data.
- *"CDC instead of polling?"* Yes, for high volume: Debezium on the Postgres WAL, or Cosmos DB change feed driving an Azure Function. Lower latency and no polling load; more infrastructure. Note the outbox pattern is **not** in Microsoft's cloud design patterns catalog — it's microservices.io vocabulary; the Azure-native adjacent entries are Idempotent Consumer and Event Sourcing. Say that and you sound like you've read both.
- *"Ordering?"* `ORDER BY id` plus a single relay gives global order but no scale-out. For per-aggregate order, hash `aggregate_id` to a relay shard and set the Service Bus `session_id` to the aggregate ID.
- *"Table growth?"* Partition by month and drop old partitions, or `DELETE FROM outbox WHERE published_at < now() - interval '7 days'` in batches.

---

### P7. Stream a paginated upstream API into blob storage without loading it

**Problem.** An upstream returns 12 million records over cursor pagination, 1,000 per page. Land them in Azure Blob Storage as NDJSON. The pod has 512 MB of memory.

**Clarifying questions:** Cursor or offset pagination? Is the total known up front? Do we need resumability if the pod dies at record 8 million? One blob or many? Is upstream rate-limited?

**Solution.**

```python
from __future__ import annotations

import asyncio
import base64
import json
import uuid
from collections.abc import AsyncIterator

import httpx
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import BlobBlock
from azure.storage.blob.aio import BlobServiceClient

BLOCK_TARGET = 8 * 1024 * 1024     # 8 MiB blocks: well under the 4,000 MiB block ceiling,
                                   # and 50,000 blocks x 8 MiB = 400 GiB headroom per blob


async def pages(client: httpx.AsyncClient, url: str) -> AsyncIterator[list[dict]]:
    """Cursor pagination. Yields one page at a time — never accumulates."""
    cursor: str | None = None
    while True:
        params = {"limit": 1000}
        if cursor:
            params["cursor"] = cursor
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        body = resp.json()
        items = body.get("items", [])
        if items:
            yield items
        cursor = body.get("next_cursor")
        if not cursor:
            return


async def ndjson_blocks(client: httpx.AsyncClient, url: str) -> AsyncIterator[bytes]:
    """Re-chunk record-sized pages into upload-sized blocks. Peak RSS = one block."""
    buf = bytearray()
    async for page in pages(client, url):
        for record in page:
            buf += json.dumps(record, separators=(",", ":")).encode() + b"\n"
        if len(buf) >= BLOCK_TARGET:
            yield bytes(buf)
            buf.clear()
    if buf:
        yield bytes(buf)


async def export(url: str, account_url: str, container: str, blob_name: str) -> int:
    total = 0
    async with DefaultAzureCredential() as cred, \
               BlobServiceClient(account_url, credential=cred) as bsc, \
               httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=60, write=60, pool=5),
                                 limits=httpx.Limits(max_connections=10)) as http:
        blob = bsc.get_blob_client(container, blob_name)
        block_ids: list[str] = []
        async for chunk in ndjson_blocks(http, url):
            block_id = base64.b64encode(uuid.uuid4().bytes).decode()   # must be equal-length
            await blob.stage_block(block_id=block_id, data=chunk)      # committed later
            block_ids.append(block_id)
            total += chunk.count(b"\n")
        await blob.commit_block_list([BlobBlock(block_id=b) for b in block_ids])
    return total
```

**Backpressure variant** — if the producer is faster than the uploader, put a bounded queue between them so the producer *blocks* rather than buffering to death:

```python
async def with_backpressure(client: httpx.AsyncClient, url: str, blob) -> int:
    q: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=4)   # <= 32 MiB resident
    block_ids: list[str] = []

    async def produce() -> None:
        async for chunk in ndjson_blocks(client, url):
            await q.put(chunk)        # BLOCKS when 4 chunks are queued -> backpressure
        await q.put(None)

    async def consume() -> None:
        while (chunk := await q.get()) is not None:
            bid = base64.b64encode(uuid.uuid4().bytes).decode()
            await blob.stage_block(block_id=bid, data=chunk)
            block_ids.append(bid)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(produce())
        tg.create_task(consume())
    await blob.commit_block_list([BlobBlock(block_id=b) for b in block_ids])
    return len(block_ids)
```

**Complexity.** Time O(n) records. Memory O(BLOCK_TARGET × queue depth) — 8 MiB × 4 = 32 MiB regardless of whether the export is 12 million rows or 12 billion.

**Verified Azure numbers.** Maximum blocks per block blob: **50,000**. Maximum block size: **4,000 MiB** (service version 2019-12-12+). Maximum block blob: ~**190.7 TiB**. Single `Put Blob` write: **5,000 MiB**. Target request rate for a single block blob: up to **3,000 requests/second** — which is why 8 MiB blocks rather than 64 KiB ones.

**If they push back:**
- *"Resumability?"* Staged-but-uncommitted blocks live in the uncommitted block list for 7 days. I persist `(cursor, block_ids)` to a small checkpoint blob after every N blocks; on restart I resume from the cursor and re-stage only the tail. Or simpler: write one blob per page-range (`orders/2026-08-25/part-00042.ndjson`) so a restart just redoes one part.
- *"Offset pagination instead?"* Offset over a mutating dataset silently skips and duplicates rows as records shift. Insist on a cursor or a stable sort key with `WHERE id > :last_id`.
- *"Why not `upload_blob` with the generator?"* You can, and the SDK will chunk it — but staging blocks explicitly gives me the block list for checkpointing and lets me parallelise `stage_block` calls.

---

### P8. SOAP/XML → JSON with namespaces, plus a canonical mapper

**Problem.** A legacy SAP endpoint returns a SOAP envelope. Parse it safely, handle namespaces, and map it into your canonical order model.

**Clarifying questions:** Is there an XSD? Are namespaces stable or does the vendor version them? Repeated elements — always a list, or list-only-when-many? What's the encoding declaration vs actual bytes? Any attachments (MTOM)?

**Solution.**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from lxml import etree

SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
ORD_NS = "urn:acme:orders:v1"
NS = {"soap": SOAP_ENV, "ord": ORD_NS}

# Hardened parser. Defaults are NOT safe for untrusted XML.
SAFE_PARSER = etree.XMLParser(
    resolve_entities=False,   # kills XXE / billion-laughs entity expansion
    no_network=True,          # no external DTD/schema fetches
    huge_tree=False,          # keeps libxml2's depth/size guards on
    remove_comments=True,
    remove_pis=True,
)

SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ord:GetOrderResponse xmlns:ord="urn:acme:orders:v1">
      <ord:Order ord:id="SO-1001">
        <ord:Customer><ord:Id>C-77</ord:Id><ord:Name>Acme Pvt Ltd</ord:Name></ord:Customer>
        <ord:PlacedAt>2026-08-25T10:15:00Z</ord:PlacedAt>
        <ord:Line><ord:Sku>ABC</ord:Sku><ord:Qty>2</ord:Qty><ord:Price>19.99</ord:Price></ord:Line>
        <ord:Line><ord:Sku>XYZ</ord:Sku><ord:Qty>1</ord:Qty><ord:Price>5.00</ord:Price></ord:Line>
      </ord:Order>
    </ord:GetOrderResponse>
  </soap:Body>
</soap:Envelope>"""


class SoapFault(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


@dataclass(frozen=True, slots=True)
class CanonicalLine:
    sku: str
    quantity: int
    unit_price: Decimal

@dataclass(frozen=True, slots=True)
class CanonicalOrder:
    order_id: str
    customer_id: str
    customer_name: str
    placed_at: datetime
    lines: tuple[CanonicalLine, ...]

    @property
    def total(self) -> Decimal:
        return sum((l.unit_price * l.quantity for l in self.lines), Decimal("0"))


def _text(node: etree._Element, path: str) -> str:
    found = node.find(path, NS)
    if found is None or found.text is None:
        raise ValueError(f"missing required element: {path}")
    return found.text.strip()


def parse_order(xml: bytes) -> CanonicalOrder:
    root = etree.fromstring(xml, parser=SAFE_PARSER)

    fault = root.find("soap:Body/soap:Fault", NS)
    if fault is not None:
        # SOAP 1.1 uses unqualified faultcode/faultstring; 1.2 uses soap:Code/soap:Reason.
        code = (fault.findtext("faultcode") or fault.findtext("soap:Code/soap:Value", "", NS))
        reason = (fault.findtext("faultstring") or fault.findtext("soap:Reason/soap:Text", "", NS))
        raise SoapFault(code or "unknown", reason or "")

    order = root.find("soap:Body/ord:GetOrderResponse/ord:Order", NS)
    if order is None:
        raise ValueError("no Order element in response body")

    # Namespaced ATTRIBUTE: must use Clark notation, NS prefixes don't work in .get()
    order_id = order.get(f"{{{ORD_NS}}}id") or _text(order, "ord:Id")

    lines = tuple(
        CanonicalLine(
            sku=_text(ln, "ord:Sku"),
            quantity=int(_text(ln, "ord:Qty")),
            unit_price=Decimal(_text(ln, "ord:Price")),   # Decimal, never float, for money
        )
        for ln in order.findall("ord:Line", NS)           # findall -> always a list, 1 or many
    )

    return CanonicalOrder(
        order_id=order_id,
        customer_id=_text(order, "ord:Customer/ord:Id"),
        customer_name=_text(order, "ord:Customer/ord:Name"),
        placed_at=datetime.fromisoformat(_text(order, "ord:PlacedAt").replace("Z", "+00:00")),
        lines=lines,
    )


# --- Declarative mapper for the 200-field version of this problem ---
MAPPING: dict[str, tuple[str, type | object]] = {
    "order_id":      ("soap:Body/ord:GetOrderResponse/ord:Order/@{urn:acme:orders:v1}id", str),
    "customer_id":   ("soap:Body/ord:GetOrderResponse/ord:Order/ord:Customer/ord:Id", str),
    "customer_name": ("soap:Body/ord:GetOrderResponse/ord:Order/ord:Customer/ord:Name", str),
}

def map_declarative(xml: bytes, mapping: dict) -> dict:
    root = etree.fromstring(xml, parser=SAFE_PARSER)
    out: dict[str, object] = {}
    for field, (path, caster) in mapping.items():
        if "/@" in path:
            elem_path, attr = path.split("/@", 1)
            node = root.find(elem_path, NS)
            raw = node.get(attr) if node is not None else None
        else:
            raw = root.findtext(path, None, NS)
        out[field] = caster(raw) if raw is not None else None
    return out


if __name__ == "__main__":
    o = parse_order(SAMPLE)
    print(o.order_id, o.customer_name, str(o.total))   # SO-1001 Acme Pvt Ltd 44.98
```

**Complexity.** O(n) in document size; `etree.fromstring` builds the whole tree, so for documents over ~100 MB switch to `etree.iterparse(source, events=("end",), tag=f"{{{ORD_NS}}}Order")` and `elem.clear()` after each record to keep memory flat.

**If they push back:**
- *"Why not `xmltodict`?"* Convenient, but it collapses namespaces, makes single-vs-multiple elements type-unstable (`dict` when one, `list` when many — the classic production bug), and it inherits `xml.parsers.expat`'s defaults. For a contract-bound integration I want explicit paths and an explicit canonical model.
- *"Security?"* XXE and billion-laughs. `resolve_entities=False`, `no_network=True`, and don't trust the declared encoding — pass bytes, not a decoded `str`, or lxml raises on the XML declaration.
- *"Where does this run in Azure?"* Logic Apps **Standard** gives you XML and Liquid transform actions without an integration account, which is the reason to pick Standard over Consumption for B2B/EDI work. For anything beyond a map, an Azure Function with lxml.

---

### P9. Fan-out to N downstreams with a hard deadline and partial failure

**Problem.** `GET /customer/{id}/360` aggregates CRM, billing, support-tickets and entitlements. Each has its own SLA. The whole endpoint must answer in 2 seconds. If billing is down, still return the other three.

**Clarifying questions:** Which sources are mandatory vs optional? Do we return 200 with partial data, or 206/207? Is stale cached data acceptable for a failed source? Per-call timeout, or a shared budget?

**Solution.**

```python
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import FastAPI, Response

OVERALL_DEADLINE = 2.0

@dataclass(frozen=True, slots=True)
class Source:
    name: str
    path: str
    timeout: float
    required: bool

SOURCES = (
    Source("crm",          "/crm/customers/{id}",       0.8, required=True),
    Source("billing",      "/billing/accounts/{id}",    1.2, required=False),
    Source("tickets",      "/support/tickets?cust={id}",1.5, required=False),
    Source("entitlements", "/ent/{id}",                 0.5, required=False),
)


async def fetch_one(client: httpx.AsyncClient, src: Source, cid: str,
                    budget: float) -> tuple[str, Any, str | None]:
    """Never raises. Returns (name, data|None, error|None)."""
    effective = min(src.timeout, budget)          # per-call timeout capped by remaining budget
    if effective <= 0:
        return src.name, None, "no budget remaining"
    try:
        async with asyncio.timeout(effective):
            r = await client.get(src.path.format(id=cid))
            r.raise_for_status()
            return src.name, r.json(), None
    except TimeoutError:
        return src.name, None, f"timeout after {effective:.2f}s"
    except httpx.HTTPStatusError as exc:
        return src.name, None, f"http {exc.response.status_code}"
    except Exception as exc:                       # noqa: BLE001
        return src.name, None, type(exc).__name__


app = FastAPI()

@app.get("/customer/{cid}/360")
async def customer_360(cid: str, response: Response) -> dict:
    client: httpx.AsyncClient = app.state.http
    started = time.monotonic()

    async def remaining() -> float:
        return OVERALL_DEADLINE - (time.monotonic() - started)

    budget = await remaining()
    # gather(return_exceptions=True) is the PARTIAL-FAILURE tool. TaskGroup would cancel
    # the healthy siblings the moment billing failed, which is the opposite of what we want.
    results = await asyncio.gather(
        *(fetch_one(client, s, cid, budget) for s in SOURCES),
        return_exceptions=True,
    )

    data: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for item in results:
        if isinstance(item, BaseException):
            errors["_unknown"] = type(item).__name__
            continue
        name, payload, err = item
        if err:
            errors[name] = err
        else:
            data[name] = payload

    required_failed = [s.name for s in SOURCES if s.required and s.name in errors]
    if required_failed:
        response.status_code = 502
        return {"error": "required source unavailable", "sources": errors}

    if errors:
        response.status_code = 206                       # Partial Content
        response.headers["X-Degraded-Sources"] = ",".join(sorted(errors))

    return {"customer_id": cid, "data": data, "degraded": errors,
            "elapsed_ms": round((time.monotonic() - started) * 1000)}
```

**Complexity.** Wall time = max(per-source latency) bounded by the deadline, not the sum. Four sources at 0.8/1.2/1.5/0.5 s take ~1.5 s concurrently vs 4.0 s sequentially.

**If they push back:**
- *"Why 206 and not 200?"* Because a silent partial is how a dashboard shows a customer with zero invoices and someone opens a P1. Make degradation explicit in the status and a header, and make the client's contract say so.
- *"How do you avoid a slow source degrading everything?"* Circuit breaker per source ([P3](#p3-retry-with-exponential-backoff--full-jitter-plus-a-circuit-breaker)) so a dead billing service fails in microseconds instead of consuming its 1.2 s of the budget on every request. This is the **Gateway Aggregation** pattern; the breaker is what makes it safe.
- *"Cache?"* Serve last-known-good from Redis with an `X-Data-Age` header when a source is open-circuit. Stale-but-labelled beats missing.

---

### P10. JWT validation middleware with JWKS caching and key rotation

**Problem.** Validate Entra ID (Azure AD) access tokens on every request. Keys rotate. You must not fetch JWKS per request, and you must not fail every request for 24 hours when the IdP rotates a key.

**Clarifying questions:** Which issuer(s) and audience(s)? v1.0 or v2.0 Entra tokens (the `iss` and `aud` differ)? Are we validating a multi-tenant token? Is APIM already doing `validate-jwt` in front of us (defence in depth or duplication)? Required scopes/roles?

**Solution.**

```python
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request
from jwt import PyJWK
from starlette.middleware.base import BaseHTTPMiddleware

TENANT = "contoso.onmicrosoft.com"
OIDC_CONFIG = f"https://login.microsoftonline.com/{TENANT}/v2.0/.well-known/openid-configuration"
AUDIENCE = "api://ey-integration-api"
ALGORITHMS = ["RS256"]                 # allowlist. NEVER read alg from the token.

JWKS_TTL = 3600.0                      # steady-state refresh
ROTATION_COOLDOWN = 300.0              # min seconds between forced refreshes (anti-DoS)


class JwksCache:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._keys: dict[str, PyJWK] = {}
        self._expires = 0.0
        self._last_forced = 0.0
        self._jwks_uri: str | None = None
        self._issuer: str | None = None
        self._lock = asyncio.Lock()

    async def _discover(self) -> None:
        r = await self._client.get(OIDC_CONFIG, timeout=5.0)
        r.raise_for_status()
        doc = r.json()
        self._jwks_uri = doc["jwks_uri"]
        self._issuer = doc["issuer"]

    async def _refresh(self) -> None:
        if self._jwks_uri is None:
            await self._discover()
        r = await self._client.get(self._jwks_uri, timeout=5.0)   # type: ignore[arg-type]
        r.raise_for_status()
        self._keys = {k["kid"]: PyJWK.from_dict(k) for k in r.json()["keys"] if "kid" in k}
        self._expires = time.monotonic() + JWKS_TTL

    async def key_for(self, kid: str) -> PyJWK:
        now = time.monotonic()
        if now >= self._expires or not self._keys:
            async with self._lock:                    # single-flight: one refresh, not N
                if time.monotonic() >= self._expires or not self._keys:
                    await self._refresh()

        if kid in self._keys:
            return self._keys[kid]

        # Unknown kid => probable rotation. Force ONE refresh, rate-limited so a token
        # with a garbage kid cannot turn into a JWKS-endpoint DoS.
        async with self._lock:
            if kid in self._keys:
                return self._keys[kid]
            if time.monotonic() - self._last_forced < ROTATION_COOLDOWN:
                raise HTTPException(401, "unknown signing key")
            self._last_forced = time.monotonic()
            await self._refresh()
        if kid not in self._keys:
            raise HTTPException(401, "unknown signing key")
        return self._keys[kid]

    @property
    def issuer(self) -> str:
        if self._issuer is None:
            raise RuntimeError("discovery not run")
        return self._issuer


async def validate(token: str, cache: JwksCache) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)     # header ONLY, never the payload
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, "malformed token") from exc

    kid = header.get("kid")
    if not kid:
        raise HTTPException(401, "token has no kid")
    if header.get("alg") not in ALGORITHMS:
        raise HTTPException(401, "unsupported algorithm")   # blocks alg:none and HS/RS confusion

    key = await cache.key_for(kid)
    try:
        return jwt.decode(
            token,
            key=key,
            algorithms=ALGORITHMS,                    # allowlist wins over the header
            audience=AUDIENCE,
            issuer=cache.issuer,
            leeway=60,                                # clock skew tolerance
            options={"require": ["exp", "iat", "nbf", "aud", "iss", "sub"],
                     "verify_signature": True, "verify_exp": True,
                     "verify_aud": True, "verify_iss": True},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(401, "token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, f"invalid token: {exc}") from exc


class JwtMiddleware(BaseHTTPMiddleware):
    PUBLIC = {"/livez", "/readyz", "/openapi.json", "/docs"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "missing bearer token")
        claims = await validate(token, request.app.state.jwks)
        request.state.principal = claims
        return await call_next(request)


def require_scope(scope: str):
    async def dep(request: Request) -> None:
        claims = getattr(request.state, "principal", {})
        scopes = set(claims.get("scp", "").split()) | set(claims.get("roles", []))
        if scope not in scopes:
            raise HTTPException(403, f"scope '{scope}' required")
    return dep


app = FastAPI()
app.add_middleware(JwtMiddleware)
```

**Complexity.** O(1) per request after the first — one RSA verify (tens of microseconds), zero network. JWKS fetches: one per hour steady state, plus at most one per 5 minutes during a rotation.

**PyJWT's built-in alternative** (sync path, or when you don't need the cooldown control): `jwt.PyJWKClient(uri, cache_jwk_set=True, lifespan=300, timeout=30)` — `cache_jwk_set` defaults to `True`, `lifespan` to 300 s, `max_cached_keys` to 16, `cache_keys` to `False`.

**If they push back:**
- *"APIM already validates the JWT, why do it again?"* Defence in depth, and because the container can be reached from inside the VNet. But if APIM is the only ingress and does `validate-jwt` with `<openid-config>` plus required claims, I'd validate at the edge and only re-check *authorisation* (scopes/roles) in the app — say the trade-off out loud rather than picking blindly.
- *"What is the `alg:none` attack?"* An attacker sets `"alg":"none"`, strips the signature, and a naive library that trusts the header accepts it. Second variant: an RS256 verifier that's handed `HS256` will use the RSA *public* key as an HMAC secret — and the public key is public. Both are killed by the algorithm allowlist.
- *"Revocation?"* JWTs are bearer credentials valid until `exp`. For revocation you need short lifetimes (Entra access tokens default to 60–90 minutes with randomisation) plus a deny-list of `jti` in Redis for the emergency case, or introspection against the IdP (which costs you the stateless property).

---

### P11. Saga orchestrator with compensating actions

**Problem.** "Place order" spans three services: reserve inventory, charge payment, create shipment. There is no distributed transaction. If shipment creation fails, the payment must be refunded and the inventory released.

**Clarifying questions:** Orchestration or choreography? Are the compensations truly available (can you refund, or only credit-note)? Are steps idempotent? Where does saga state live, and who resumes it after a crash? Is a semantic lock needed to stop concurrent sagas on the same aggregate?

**Solution.**

```python
from __future__ import annotations

import asyncio
import enum
import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

Ctx = dict[str, Any]
Action = Callable[[Ctx], Awaitable[Ctx]]


class SagaState(enum.StrEnum):
    RUNNING = "running"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"           # forward failed AND compensation failed -> needs a human


@dataclass(frozen=True, slots=True)
class Step:
    name: str
    action: Action
    compensate: Action | None = None
    retries: int = 3


class SagaStore:
    """Swap for a real table. Schema: saga_id PK, state, ctx jsonb, completed jsonb,
    updated_at. Every transition is a single UPDATE so a crash can be resumed."""
    def __init__(self) -> None:
        self._rows: dict[str, dict] = {}

    async def save(self, saga_id: str, state: SagaState, ctx: Ctx, done: list[str]) -> None:
        self._rows[saga_id] = {"state": state, "ctx": json.loads(json.dumps(ctx, default=str)),
                               "completed": list(done)}

    async def load(self, saga_id: str) -> dict | None:
        return self._rows.get(saga_id)


class Saga:
    def __init__(self, steps: list[Step], store: SagaStore) -> None:
        self._steps = steps
        self._store = store

    async def _with_retry(self, fn: Action, ctx: Ctx, attempts: int, label: str) -> Ctx:
        for n in range(attempts):
            try:
                return await fn(ctx)
            except Exception:                                    # noqa: BLE001
                if n == attempts - 1:
                    raise
                log.warning("saga step retry", extra={"extra_fields":
                            {"step": label, "attempt": n + 1}})
                await asyncio.sleep(min(8.0, 0.25 * 2 ** n))
        raise AssertionError("unreachable")

    async def run(self, ctx: Ctx, saga_id: str | None = None) -> tuple[SagaState, Ctx]:
        saga_id = saga_id or str(uuid.uuid4())
        ctx = {**ctx, "saga_id": saga_id}
        completed: list[str] = []
        await self._store.save(saga_id, SagaState.RUNNING, ctx, completed)

        for step in self._steps:
            try:
                ctx = await self._with_retry(step.action, ctx, step.retries, step.name)
                completed.append(step.name)
                await self._store.save(saga_id, SagaState.RUNNING, ctx, completed)
            except Exception as exc:                             # noqa: BLE001
                log.error("saga forward failed", extra={"extra_fields":
                          {"saga_id": saga_id, "step": step.name, "error": str(exc)}})
                ctx["failure"] = {"step": step.name, "error": str(exc)}
                return await self._compensate(saga_id, ctx, completed)

        await self._store.save(saga_id, SagaState.COMPLETED, ctx, completed)
        return SagaState.COMPLETED, ctx

    async def _compensate(self, saga_id: str, ctx: Ctx, completed: list[str]) -> tuple[SagaState, Ctx]:
        await self._store.save(saga_id, SagaState.COMPENSATING, ctx, completed)
        by_name = {s.name: s for s in self._steps}
        unrecovered: list[str] = []

        for name in reversed(completed):                # LIFO — undo in reverse order
            step = by_name[name]
            if step.compensate is None:
                continue
            try:
                ctx = await self._with_retry(step.compensate, ctx, step.retries, f"compensate:{name}")
            except Exception as exc:                    # noqa: BLE001
                # A failed compensation is an operational incident, not a retry loop.
                log.critical("compensation failed", extra={"extra_fields":
                             {"saga_id": saga_id, "step": name, "error": str(exc)}})
                unrecovered.append(name)

        final = SagaState.FAILED if unrecovered else SagaState.COMPLETED
        ctx["unrecovered"] = unrecovered
        await self._store.save(saga_id, final, ctx, completed)
        return final, ctx


# --- concrete steps -------------------------------------------------------
async def reserve_inventory(ctx: Ctx) -> Ctx:
    ctx["reservation_id"] = f"resv-{ctx['order_id']}"     # idempotency key = order_id
    return ctx

async def release_inventory(ctx: Ctx) -> Ctx:
    log.info("released %s", ctx.get("reservation_id"))
    return ctx

async def charge_payment(ctx: Ctx) -> Ctx:
    ctx["payment_id"] = f"pay-{ctx['order_id']}"
    return ctx

async def refund_payment(ctx: Ctx) -> Ctx:
    log.info("refunded %s", ctx.get("payment_id"))
    return ctx

async def create_shipment(ctx: Ctx) -> Ctx:
    raise RuntimeError("carrier API 503")                 # force the compensation path

SAGA = Saga(
    steps=[
        Step("reserve_inventory", reserve_inventory, release_inventory),
        Step("charge_payment", charge_payment, refund_payment),
        Step("create_shipment", create_shipment, None),   # last step needs no compensation
    ],
    store=SagaStore(),
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(SAGA.run({"order_id": "SO-1001"})))
```

**Complexity.** O(steps) forward, O(completed steps) backward. State is persisted after every transition, so recovery cost after a crash is O(1) — reload and resume.

**If they push back:**
- *"Isolation?"* Sagas have none — an intermediate state is externally visible. Mitigations by name: **semantic lock** (mark the order `PENDING` so nothing else acts on it), **commutative updates**, **pessimistic view ordering**, **re-read value** before compensating.
- *"What if compensation itself fails?"* You cannot roll back forever. Mark the saga `FAILED`, emit an alert, and put the payload on a manual-intervention queue. Pretending compensation always succeeds is the naive answer.
- *"Azure-native version?"* Durable Functions orchestrator with explicit compensation activities — the orchestrator's replay-based durability gives you the persistence for free. Logic Apps Standard with a scope + `runAfter: [Failed]` handler is the low-code equivalent. Microsoft's own guidance: "Build Saga on Compensating Transaction."
- *"Choreography instead?"* Fewer moving parts, but the flow only exists as an emergent property of event subscriptions — nobody can answer "where is order SO-1001 stuck?" without a trace tool. Orchestration for anything a business user will ask about.

---

### P12. Bulk CSV → API upsert: chunking, parallelism, error report, resumability

**Problem.** A 2 GB CSV of 5 million customer records must be upserted through a REST API that accepts batches of 100 and rate-limits to 50 requests/second. Produce a per-row error report. The job must resume if the pod restarts.

**Clarifying questions:** Is the API batch-atomic or per-row partial? Is there a natural idempotency key per row? Is the file stable or streamed? Acceptable total runtime? Where does the error report land?

**Solution.**

```python
from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

BATCH = 100
CONCURRENCY = 8          # 8 in flight x ~160ms = ~50 rps, matching the contract
CHECKPOINT_EVERY = 50    # batches


@dataclass
class Checkpoint:
    path: Path
    rows_done: int = 0
    batches_done: int = 0
    errors: int = 0

    @classmethod
    def load(cls, path: Path) -> "Checkpoint":
        if path.exists():
            d = json.loads(path.read_text())
            return cls(path=path, **{k: v for k, v in d.items() if k != "path"})
        return cls(path=path)

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"rows_done": self.rows_done,
                                   "batches_done": self.batches_done,
                                   "errors": self.errors}))
        os.replace(tmp, self.path)      # atomic rename: never a half-written checkpoint


def batched_rows(path: Path, skip: int, size: int) -> Iterator[list[dict[str, str]]]:
    """Streams the file. Never loads 2 GB."""
    with path.open(newline="", encoding="utf-8-sig") as fh:   # utf-8-sig strips the BOM
        reader = csv.DictReader(fh)
        for _ in islice(reader, skip):                        # resume: skip processed rows
            pass
        while chunk := list(islice(reader, size)):
            yield chunk


async def push_batch(client: httpx.AsyncClient, rows: list[dict], offset: int,
                     sem: asyncio.Semaphore) -> list[dict]:
    """Returns per-row failures. Never raises."""
    async with sem:
        idem = f"bulk-{offset}-{len(rows)}"
        try:
            r = await client.post("/customers:batchUpsert",
                                  json={"records": rows},
                                  headers={"Idempotency-Key": idem})
            if r.status_code == 429:
                await asyncio.sleep(float(r.headers.get("Retry-After", "1")))
                return await push_batch(client, rows, offset, sem)
            r.raise_for_status()
            # API returns per-record results: [{"index": 3, "error": "..."}]
            return [{"row": offset + item["index"] + 2, "error": item["error"],
                     "record": rows[item["index"]]}
                    for item in r.json().get("failures", [])]
        except httpx.HTTPStatusError as exc:
            return [{"row": offset + i + 2, "error": f"batch http {exc.response.status_code}",
                     "record": rec} for i, rec in enumerate(rows)]
        except Exception as exc:                              # noqa: BLE001
            return [{"row": offset + i + 2, "error": type(exc).__name__, "record": rec}
                    for i, rec in enumerate(rows)]


async def run(csv_path: Path, base_url: str, state_path: Path, err_path: Path) -> Checkpoint:
    ck = Checkpoint.load(state_path)
    log.info("starting", extra={"extra_fields": {"resume_from_row": ck.rows_done}})
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(base_url=base_url,
                                 timeout=httpx.Timeout(connect=5, read=30, write=30, pool=5),
                                 limits=httpx.Limits(max_connections=CONCURRENCY * 2)) as client, \
               err_path.open("a", newline="", encoding="utf-8") as errfh:
        writer = csv.DictWriter(errfh, fieldnames=["row", "error", "record"])
        if errfh.tell() == 0:
            writer.writeheader()

        pending: list[asyncio.Task] = []
        offset = ck.rows_done
        for chunk in batched_rows(csv_path, skip=ck.rows_done, size=BATCH):
            pending.append(asyncio.create_task(push_batch(client, chunk, offset, sem)))
            offset += len(chunk)

            if len(pending) >= CONCURRENCY:
                done = await asyncio.gather(*pending)
                for failures in done:
                    for f in failures:
                        writer.writerow({**f, "record": json.dumps(f["record"])})
                    ck.errors += len(failures)
                ck.rows_done = offset
                ck.batches_done += len(pending)
                pending.clear()
                if ck.batches_done % CHECKPOINT_EVERY == 0:
                    errfh.flush()
                    ck.save()

        if pending:
            for failures in await asyncio.gather(*pending):
                for f in failures:
                    writer.writerow({**f, "record": json.dumps(f["record"])})
                ck.errors += len(failures)
            ck.rows_done = offset
        errfh.flush()
        ck.save()
    return ck
```

**Complexity.** Time = ceil(5,000,000 / 100) / 50 rps ≈ 1,000 seconds ≈ 17 minutes at the contract rate. Memory O(BATCH × CONCURRENCY) rows ≈ 800 rows resident, independent of file size.

**If they push back:**
- *"Resumability is row-count based — isn't that fragile?"* Yes, if the file can change. Two hardenings: hash the file and store the hash in the checkpoint (refuse to resume against a different file), and make each batch idempotent with a deterministic `Idempotency-Key` derived from the row range so re-running the boundary batch is harmless.
- *"Why not multiprocessing?"* The work is network-bound; processes buy nothing and cost you shared rate-limit state. If CSV *parsing* were the bottleneck I'd split the file by byte range and run N processes, each with its own checkpoint.
- *"Where does this run at EY?"* Azure Container Apps Job or an AKS `Job` with a PVC for the checkpoint, or Azure Data Factory Copy activity if it's a pure data move — ADF's Azure IR gives up to 256 DIUs per copy activity and a self-hosted IR scales out to 4 nodes.

---

### P13. Dedupe / idempotency store with TTL, and the correctness argument

**Problem.** Your consumer is at-least-once. Build the dedupe store and then *argue* it's correct.

**Solution.**

```python
from __future__ import annotations

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class RedisDedupe:
    """Fast path. Not durable across a Redis failover."""
    def __init__(self, client: redis.Redis, ttl: int) -> None:
        self._r, self._ttl = client, ttl

    async def claim(self, key: str) -> bool:
        # SET NX EX is a single atomic command. Returns True only for the first caller.
        return bool(await self._r.set(f"dedupe:{key}", "1", nx=True, ex=self._ttl))

    async def release(self, key: str) -> None:
        await self._r.delete(f"dedupe:{key}")


DEDUPE_DDL = """
CREATE TABLE processed_messages (
    message_id   TEXT        PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX processed_messages_ttl_idx ON processed_messages (processed_at);
"""

async def handle_exactly_once(session: AsyncSession, message_id: str, payload: dict) -> bool:
    """The correct version: the dedupe row and the side effect share one transaction."""
    async with session.begin():
        inserted = await session.execute(
            text("INSERT INTO processed_messages (message_id) VALUES (:mid) "
                 "ON CONFLICT (message_id) DO NOTHING RETURNING message_id"),
            {"mid": message_id},
        )
        if inserted.first() is None:
            return False                      # already processed; commit is a no-op
        await session.execute(
            text("INSERT INTO orders (order_id, amount) VALUES (:oid, :amt) "
                 "ON CONFLICT (order_id) DO UPDATE SET amount = EXCLUDED.amount"),
            {"oid": payload["order_id"], "amt": payload["amount"]},
        )
    return True
```

**The correctness argument — say this verbatim:**

> The broker gives me at-least-once. Exactly-once *delivery* is impossible across a network; exactly-once *effect* is achievable if the dedupe record and the side effect commit atomically. In the SQL version they share one transaction, so there are exactly two outcomes: both committed, or neither — and a redelivery hits the `ON CONFLICT` and no-ops. That is **effectively-once within the retention window of the dedupe table**.
>
> The Redis version is not that. Claim-then-work has a window: if the process dies after the claim and before the side effect, the message is dropped, because the redelivery sees the claim and skips. To use Redis I have to either release the claim on failure (which reopens the double-processing window on a hard crash) or accept the risk. I'd use Redis when the side effect is itself idempotent — an upsert by natural key — and SQL when it isn't.
>
> TTL sizing: the window must exceed the maximum redelivery horizon. Service Bus auto-dead-letters at `MaxDeliveryCount` 10 by default, but a message can also sit scheduled, and a DLQ replay days later must still be caught — so 7 days, not 1 hour. Cleanup is `DELETE ... WHERE processed_at < now() - interval '7 days'` in batches, or a Redis TTL, never an unbounded table.

**If they push back — "Service Bus already has duplicate detection."** It does, keyed on `MessageId` over a configurable window on the entity — but that only catches duplicates from the *producer* re-sending. It does not catch a redelivery caused by the *consumer* crashing after the side effect and before settling. Both layers are needed.

---

### P14. Health and readiness endpoints done correctly

**Problem.** Add `/livez` and `/readyz` to the service. Explain what each must and must not check.

**Solution.**

```python
from __future__ import annotations

import asyncio
import time
from typing import Literal

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

app = FastAPI()
_ready_cache: dict[str, tuple[float, dict]] = {}
READY_CACHE_TTL = 5.0            # probes fire every 10s per pod; don't hammer the DB


@app.get("/livez")
async def livez() -> dict[str, Literal["ok"]]:
    """Liveness: 'is this process wedged?' Process-local ONLY.
    NO database, NO cache, NO downstream. If it can serve this handler, it is alive."""
    return {"status": "ok"}


async def _check(name: str, coro, timeout: float) -> tuple[str, bool, str]:
    try:
        async with asyncio.timeout(timeout):
            await coro
        return name, True, ""
    except Exception as exc:                              # noqa: BLE001
        return name, False, type(exc).__name__


@app.get("/readyz")
async def readyz(response: Response) -> dict:
    """Readiness: 'should traffic be routed here right now?' Checks hard dependencies
    only — the ones without which every request would 500."""
    now = time.monotonic()
    if (cached := _ready_cache.get("r")) and now - cached[0] < READY_CACHE_TTL:
        body = cached[1]
        response.status_code = 200 if body["ready"] else 503
        return body

    engine: AsyncEngine = app.state.engine
    cache: redis.Redis = app.state.redis

    async def db() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    results = await asyncio.gather(
        _check("postgres", db(), 2.0),
        _check("redis", cache.ping(), 1.0),
        return_exceptions=False,
    )
    checks = {name: {"ok": ok, "error": err} for name, ok, err in results}
    body = {"ready": all(c["ok"] for c in checks.values()), "checks": checks}
    _ready_cache["r"] = (now, body)
    response.status_code = 200 if body["ready"] else 503
    return body


@app.get("/startupz")
async def startupz(response: Response) -> dict:
    """Startup: gate liveness until warm-up (JWKS fetch, cache prime) has completed."""
    ok = bool(getattr(app.state, "warm", False))
    response.status_code = 200 if ok else 503
    return {"started": ok}
```

Matching Kubernetes manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: integration-api
spec:
  replicas: 3
  selector:
    matchLabels: {app: integration-api}
  template:
    metadata:
      labels: {app: integration-api}
    spec:
      terminationGracePeriodSeconds: 45     # default is 30; must exceed drain time
      containers:
        - name: api
          image: acr.io/ey/integration-api:1.4.2
          ports: [{containerPort: 8000}]
          lifecycle:
            preStop:
              exec:
                # Let kube-proxy/ingress remove this pod from endpoints BEFORE SIGTERM,
                # otherwise in-flight requests get RST and clients see 502.
                command: ["/bin/sh", "-c", "sleep 5"]
          startupProbe:
            httpGet: {path: /startupz, port: 8000}
            periodSeconds: 5
            failureThreshold: 30            # 150s of grace for a slow cold start
          livenessProbe:
            httpGet: {path: /livez, port: 8000}
            periodSeconds: 10               # default 10
            timeoutSeconds: 2               # default 1
            failureThreshold: 3             # default 3 -> ~30s to restart
          readinessProbe:
            httpGet: {path: /readyz, port: 8000}
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            requests: {cpu: 200m, memory: 256Mi}
            limits: {memory: 512Mi}
```

**Why liveness must NOT check the database — the sentence that wins the point:**

> If liveness checks the DB, then a 60-second database blip fails the liveness probe on **every** pod simultaneously. Kubernetes restarts all of them. They come back cold, all reconnect to the still-struggling database at once, fail again, and you have converted a transient dependency wobble into a self-sustaining CrashLoopBackOff outage. Readiness is the correct lever: it pulls the pods out of the Service endpoints, traffic stops, the DB recovers, and readiness flips back — with zero restarts.

**Verified defaults:** `initialDelaySeconds` 0, `periodSeconds` 10, `timeoutSeconds` 1, `successThreshold` 1, `failureThreshold` 3, `terminationGracePeriodSeconds` 30.

**If they push back — "what about a soft dependency?"** A recommendation engine that is nice-to-have goes in neither probe. Report it in a `/healthz/detail` endpoint for dashboards, and let the request path degrade gracefully. Only put a dependency in readiness if its absence makes *every* request fail.

---

### P15. OpenAPI spec-diff breaking-change detector

**Problem.** In CI, compare the PR's `openapi.json` against `main`'s and fail the build on a breaking change.

**Clarifying questions:** Breaking for the *consumer* or the *producer*? Are we the server (adding a required request field breaks clients) or generating a client? Is there an approved-breaking-change escape hatch? OpenAPI 3.0 or 3.1 (3.1 aligns with JSON Schema 2020-12; the current spec version is 3.2.0, released Sept 2025 and backward compatible with 3.1)?

**Solution.**

```python
#!/usr/bin/env python3
"""openapi_diff.py — fail CI on breaking API changes. Exit 1 if any found."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str      # "breaking" | "warning"
    where: str
    what: str


def _resolve(spec: dict, node: Any, seen: frozenset[str] = frozenset()) -> Any:
    """Follow local $ref one level at a time, guarding against cycles."""
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/") or ref in seen:
            return node
        seen = seen | {ref}
        cur: Any = spec
        for part in ref[2:].split("/"):
            cur = cur.get(part.replace("~1", "/").replace("~0", "~"), {})
        node = cur
    return node


def _schema_fields(spec: dict, schema: Any) -> tuple[dict[str, Any], set[str]]:
    schema = _resolve(spec, schema) or {}
    return schema.get("properties", {}) or {}, set(schema.get("required", []) or [])


def _body_schema(spec: dict, op: dict) -> Any:
    rb = _resolve(spec, op.get("requestBody", {})) or {}
    content = rb.get("content", {}) or {}
    for mt in ("application/json", "application/*+json"):
        if mt in content:
            return content[mt].get("schema", {})
    return next((v.get("schema", {}) for v in content.values()), {})


def _response_schema(spec: dict, op: dict, code: str) -> Any:
    resp = _resolve(spec, (op.get("responses", {}) or {}).get(code, {})) or {}
    content = resp.get("content", {}) or {}
    return (content.get("application/json") or {}).get("schema", {})


def diff(old: dict, new: dict) -> list[Finding]:
    out: list[Finding] = []
    old_paths, new_paths = old.get("paths", {}) or {}, new.get("paths", {}) or {}

    for path, old_item in old_paths.items():
        if path not in new_paths:
            out.append(Finding("breaking", path, "path removed"))
            continue
        new_item = new_paths[path]

        for method in METHODS:
            if method not in old_item:
                continue
            if method not in new_item:
                out.append(Finding("breaking", f"{method.upper()} {path}", "operation removed"))
                continue
            o, n = old_item[method], new_item[method]
            loc = f"{method.upper()} {path}"

            # 1. Params: newly-required, removed-required, or type change
            op_params = {(p.get("name"), p.get("in")): _resolve(old, p)
                         for p in (o.get("parameters") or [])}
            np_params = {(p.get("name"), p.get("in")): _resolve(new, p)
                         for p in (n.get("parameters") or [])}
            for key, p in np_params.items():
                if p.get("required") and key not in op_params:
                    out.append(Finding("breaking", loc, f"new required param {key[1]}:{key[0]}"))
            for key, p in op_params.items():
                if key not in np_params:
                    sev = "breaking" if p.get("required") else "warning"
                    out.append(Finding(sev, loc, f"param removed {key[1]}:{key[0]}"))
                else:
                    ot = (p.get("schema") or {}).get("type")
                    nt = (np_params[key].get("schema") or {}).get("type")
                    if ot and nt and ot != nt:
                        out.append(Finding("breaking", loc,
                                           f"param {key[0]} type {ot} -> {nt}"))

            # 2. Request body: adding a required field breaks existing clients
            ob_props, ob_req = _schema_fields(old, _body_schema(old, o))
            nb_props, nb_req = _schema_fields(new, _body_schema(new, n))
            for field in nb_req - ob_req:
                out.append(Finding("breaking", loc, f"request body: field '{field}' now required"))
            for field in set(ob_props) - set(nb_props):
                out.append(Finding("warning", loc, f"request body: field '{field}' removed"))

            # 3. Responses: removing a 2xx code, or a field consumers may depend on
            o_codes = {c for c in (o.get("responses") or {}) if c.startswith("2")}
            n_codes = {c for c in (n.get("responses") or {}) if c.startswith("2")}
            for code in o_codes - n_codes:
                out.append(Finding("breaking", loc, f"success response {code} removed"))
            for code in o_codes & n_codes:
                or_props, _ = _schema_fields(old, _response_schema(old, o, code))
                nr_props, _ = _schema_fields(new, _response_schema(new, n, code))
                for field in set(or_props) - set(nr_props):
                    out.append(Finding("breaking", loc,
                                       f"response {code}: field '{field}' removed"))
                for field in set(or_props) & set(nr_props):
                    ot = _resolve(old, or_props[field]).get("type")
                    nt = _resolve(new, nr_props[field]).get("type")
                    if ot and nt and ot != nt:
                        out.append(Finding("breaking", loc,
                                           f"response {code}: '{field}' type {ot} -> {nt}"))
                    oe = set(_resolve(old, or_props[field]).get("enum") or [])
                    ne = set(_resolve(new, nr_props[field]).get("enum") or [])
                    # New enum values in a RESPONSE break strict consumers.
                    if oe and ne and (ne - oe):
                        out.append(Finding("warning", loc,
                                           f"response {code}: '{field}' new enum {sorted(ne - oe)}"))
    return out


def main() -> int:
    old = json.loads(open(sys.argv[1]).read())
    new = json.loads(open(sys.argv[2]).read())
    findings = diff(old, new)
    breaking = [f for f in findings if f.severity == "breaking"]
    for f in findings:
        print(f"[{f.severity.upper():8}] {f.where}: {f.what}")
    print(f"\n{len(breaking)} breaking, {len(findings) - len(breaking)} warnings")
    return 1 if breaking else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Wire it into Azure Pipelines:

```yaml
# azure-pipelines.yml (fragment)
- script: |
    git fetch origin main --depth=1
    git show origin/main:openapi.json > /tmp/base.json
    python -m app.export_openapi > /tmp/head.json
    python tools/openapi_diff.py /tmp/base.json /tmp/head.json
  displayName: 'Fail on breaking API change'
```

**Complexity.** O(paths × methods × fields). A 200-operation spec diffs in well under a second.

**The rules table, which is what they actually want to hear:**

| Change | Breaking for whom |
|---|---|
| Remove a path / operation / 2xx response code | Consumers |
| Add a **required** request field or param | Consumers of the *producer* |
| Remove a response field, or narrow its type | Consumers |
| Add a new enum value to a **response** | Strict consumers (warn, don't fail) |
| Add a new enum value to a **request** | Nobody |
| Add an **optional** request field | Nobody |
| Make a required request field optional | Nobody |
| Tighten a validation constraint (`maxLength` down) | Consumers |

**If they push back — "why write it, `oasdiff` exists?"** It does, and in a real pipeline I'd run `oasdiff breaking` or the Spectral ruleset rather than maintain this. The point of writing it is to know *which* rules matter; the tool is only as good as the policy you configure. Also: this is exactly what an APIM revision-vs-version decision hangs on — non-breaking goes out as a **revision**, breaking goes out as a new **version** with the old one deprecated behind a `Deprecation` header for 6+ months.

---

## 3. Testing an integration service

### Q. How do you test this in CI without the real Service Bus / SAP / partner API?

**Answer:** Three layers, and I say which is which. **Unit** — pure functions and mappers, no I/O, milliseconds. **Component** — the FastAPI app with `respx` intercepting httpx and `testcontainers` for real Postgres/Redis/Kafka, so I'm testing my SQL and my Lua, not a mock of them. **Contract** — schemathesis fuzzing my published OpenAPI spec, and Pact for the consumer-provider pair. Only smoke tests hit a real environment.

**pytest + pytest-asyncio setup.**

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"                 # no @pytest.mark.asyncio on every test
addopts = "-q --strict-markers"
markers = ["integration: needs docker", "e2e: needs a deployed environment"]
```

```python
# tests/conftest.py
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.main import create_app


@pytest.fixture(scope="session")
def pg() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine") as c:
        yield c.get_connection_url().replace("psycopg2", "asyncpg")


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with RedisContainer("redis:7-alpine") as c:
        yield f"redis://{c.get_container_host_ip()}:{c.get_exposed_port(6379)}/0"


@pytest_asyncio.fixture
async def client(pg: str, redis_url: str) -> AsyncIterator[AsyncClient]:
    app = create_app(db_url=pg, redis_url=redis_url)
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        # ASGITransport runs lifespan only via LifespanManager; use asgi-lifespan
        # if your app opens pools in lifespan.
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def flush(redis_url: str) -> AsyncIterator[None]:
    r = redis.from_url(redis_url)
    await r.flushdb()
    yield
    await r.aclose()
```

**Mocking the upstream with respx (route-level, not client-level).**

```python
import httpx
import pytest
import respx


@respx.mock
async def test_retries_then_succeeds(client):
    route = respx.get("https://erp.internal/api/v2/orders/SO-1").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json={"order_id": "SO-1", "amount": "10.00"}),
        ]
    )
    r = await client.get("/orders/SO-1")
    assert r.status_code == 200
    assert route.call_count == 3          # proves the retry actually fired


@respx.mock
async def test_does_not_retry_400(client):
    route = respx.get("https://erp.internal/api/v2/orders/BAD").mock(
        return_value=httpx.Response(400, json={"error": "bad id"}))
    r = await client.get("/orders/BAD")
    assert r.status_code == 400
    assert route.call_count == 1          # the important assertion


async def test_idempotent_post_replays(client):
    body = {"amount": "10.00", "currency": "INR"}
    hdrs = {"Idempotency-Key": "k-1", "X-Tenant-Id": "t1"}
    first = await client.post("/payments", json=body, headers=hdrs)
    second = await client.post("/payments", json=body, headers=hdrs)
    assert first.status_code == 201
    assert second.json() == first.json()
    assert second.headers["Idempotent-Replay"] == "true"


async def test_idempotency_key_reuse_with_different_body_is_422(client):
    hdrs = {"Idempotency-Key": "k-2", "X-Tenant-Id": "t1"}
    await client.post("/payments", json={"amount": "10.00"}, headers=hdrs)
    r = await client.post("/payments", json={"amount": "99.00"}, headers=hdrs)
    assert r.status_code == 422
```

**Kafka with testcontainers.**

```python
import json
from collections.abc import Iterator

import pytest
from testcontainers.kafka import KafkaContainer


@pytest.fixture(scope="session")
def kafka() -> Iterator[str]:
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as c:
        yield c.get_bootstrap_server()


@pytest.mark.integration
async def test_consumer_commits_after_processing(kafka):
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    producer = AIOKafkaProducer(bootstrap_servers=kafka)
    await producer.start()
    try:
        await producer.send_and_wait("orders", json.dumps({"id": "1"}).encode())
    finally:
        await producer.stop()

    consumer = AIOKafkaConsumer("orders", bootstrap_servers=kafka,
                                group_id="test", enable_auto_commit=False,
                                auto_offset_reset="earliest")
    await consumer.start()
    try:
        batches = await consumer.getmany(timeout_ms=10_000, max_records=10)
        records = [r for rs in batches.values() for r in rs]
        assert len(records) == 1
        await consumer.commit()
    finally:
        await consumer.stop()
```

**Contract testing — schemathesis against your own OpenAPI spec.** This is property-based fuzzing driven by the schema: it generates inputs that satisfy the spec and asserts the responses conform to it. It reliably finds 500s on boundary values that nobody writes a test for.

```python
import schemathesis
from app.main import create_app

schema = schemathesis.openapi.from_asgi("/openapi.json", create_app())

@schema.parametrize()
def test_api_conforms(case):
    case.call_and_validate()      # checks status codes, content type, response schema
```

```bash
# CI variant against a running service
schemathesis run http://localhost:8000/openapi.json \
  --checks all --hypothesis-max-examples=200 --report
```

**Pact — consumer-driven contracts.** Use it when *another team* consumes you. The consumer writes an expectation, publishes a pact file to a broker, and your CI verifies the provider against every pact before deploy. `can-i-deploy` is the gate. Schemathesis proves you match *your own* spec; Pact proves you match what *consumers actually use*. They are not substitutes.

**How I'd test an end-to-end integration flow in CI:**

```yaml
# azure-pipelines.yml (fragment)
stages:
  - stage: Test
    jobs:
      - job: unit
        steps:
          - script: pytest -m "not integration and not e2e" --cov=app --cov-fail-under=80
      - job: component
        steps:
          - script: pytest -m integration        # testcontainers spins docker itself
      - job: contract
        steps:
          - script: |
              python -m app.export_openapi > openapi.json
              python tools/openapi_diff.py <(git show origin/main:openapi.json) openapi.json
              schemathesis run --dry-run openapi.json --checks all
  - stage: DeployDev
    dependsOn: Test
    jobs:
      - deployment: dev
        environment: dev                          # approvals/gates live on the Environment
        strategy:
          runOnce:
            deploy:
              steps:
                - script: az deployment group create -g rg-int-dev --template-file infra/main.bicep
                - script: pytest -m e2e --base-url=$(DEV_URL)   # smoke only, ~10 tests
```

**If they push back — "how do you test the Service Bus consumer?"** Three levels. The handler is a pure async function with the message body as an argument — unit test it directly. The settle logic gets a fake receiver object satisfying a `Receiver` Protocol, asserting `complete_message` was called exactly once and `dead_letter_message` on a `ValidationError`. Only the wiring needs the emulator (there's an official Service Bus emulator container) or a dedicated dev namespace, and that runs nightly, not per-PR.

---

## 4. DSA safety net

If a HackerRank does appear, EY GDS reports say easy-to-medium plus occasionally one DP. These six are the highest-probability picks for an API/integration role because interviewers reach for problems that sound like caching, batching, and streaming. **One line each — full solutions live in [../DSA_MASTER.md](../DSA_MASTER.md) and [../dsa/](../dsa/).**

| # | Problem | The one thing to remember | Complexity |
|---|---|---|---|
| 1 | **LRU cache** (LC 146) | `OrderedDict` + `move_to_end(k)` on get, `popitem(last=False)` on evict. Say "this is `functools.lru_cache`'s data structure" — instant relevance to API caching. | O(1) get/put |
| 2 | **Sliding window maximum** (LC 239) | Monotonic decreasing `deque` of *indices*; pop from the left when `dq[0] <= i - k`. Say "same shape as a sliding-window rate limiter." | O(n) time, O(k) space |
| 3 | **Merge intervals** (LC 56) | Sort by start, then extend `last[1] = max(last[1], cur[1])` if `cur[0] <= last[1]`. Relevance: merging maintenance windows / SLA outage windows. | O(n log n) |
| 4 | **Top K frequent** (LC 347) | `Counter` + `heapq.nlargest(k, cnt, key=cnt.get)`, or bucket sort for O(n). Frame it as "top K noisiest API consumers." | O(n log k) / O(n) |
| 5 | **Group anagrams** (LC 49) | `defaultdict(list)` keyed on `tuple(sorted(s))` or a 26-length count tuple. Frame it as canonical-key grouping — same idea as an idempotency fingerprint. | O(n·k log k) |
| 6 | **Rotting oranges** (LC 994) | Multi-source BFS: seed the deque with *all* rotten cells, process level by level, count levels. Frame it as event propagation through a dependency graph. | O(m·n) |

**If they hand you a DP problem:** state the recurrence out loud before you code, name the state, then decide table vs memo. Don't optimise space until it works.

---

## Interviewer traps (consolidated)

| # | The trap | Wrong answer most give | What to say instead |
|---|---|---|---|
| 1 | "How do you make this faster with threads?" (CPU-bound XML canonicalisation) | "Use `ThreadPoolExecutor`." | Threads don't escape the GIL for pure-Python CPU work. `ProcessPoolExecutor`, or move it out of the request path entirely. |
| 2 | "Your retry loop retries on any exception." | Silence, or "yeah that's fine." | Retrying a 400/422 is a guaranteed waste; retrying a non-idempotent POST without an idempotency key duplicates the side effect. Classify first. |
| 3 | "Just publish the event after the DB commit." | "Sure, that works." | Two systems, no atomicity. A crash in between loses the event silently. Transactional outbox, then a relay. |
| 4 | "Add a DB check to your liveness probe." | "Good idea, more coverage." | No — a DB blip then restarts every pod at once and turns a wobble into an outage. Dependencies belong in **readiness**. |
| 5 | "Exactly-once, can you do it?" | "Yes, with Kafka transactions." | Exactly-once *delivery* is impossible across a network. Exactly-once *effect* is achievable: at-least-once delivery + an idempotent consumer whose dedupe record commits in the same transaction as the side effect. |
| 6 | "Verify this webhook signature." (candidate parses JSON first) | `hmac(json.dumps(parsed))` | Sign the **raw bytes**. Re-serialising changes key order and whitespace and the signature will never match. And compare with `hmac.compare_digest`, not `==`. |
| 7 | "Your rate limiter uses `INCR` then `EXPIRE`." | "It's atomic, Redis is single-threaded." | Two commands are not one operation — a crash between them leaves a key with no TTL, permanently locked. One Lua script, which Redis executes atomically. |
| 8 | "Use `asyncio.TaskGroup` for the fan-out." | "Yes, it's the modern one." | Only if it's all-or-nothing. `TaskGroup` cancels healthy siblings on the first failure — the opposite of partial-result aggregation. Use `gather(return_exceptions=True)` there. |
| 9 | "`except Exception` in your consumer loop." | Leaves it as-is. | It won't catch `CancelledError` (good), but a bare `except:` will — and that silently defeats graceful shutdown. Also re-raise `CancelledError` explicitly if you catch `BaseException`. |
| 10 | "Create the httpx client inside the handler." | "Cleaner, no globals." | Throws away the connection pool and pays a TLS handshake per request. One client per process, opened in `lifespan`. |
| 11 | "Offset pagination is fine for the export." | "It's simpler." | Over a mutating dataset, offsets skip and duplicate rows as records shift under you. Cursor, or `WHERE id > :last_id`. |
| 12 | "Set `maxDeliveryCount` to 1 so we don't reprocess." | "Avoids duplicates." | Now one transient blip dead-letters a good message. The default is 10 and cannot be disabled — the fix for duplicates is an idempotent consumer, not fewer retries. |

---

## 30-second whiteboard versions

**Idempotent POST.**
> Client sends `Idempotency-Key`. I hash method+path+body into a fingerprint. One atomic Redis Lua call does claim-or-read: no key → claim it as `in_flight` with a 60-second TTL and proceed; key exists with a different fingerprint → 422, that's a client bug; key exists and `in_flight` → 409 with `Retry-After`, because the original is still running; key exists and `done` → replay the stored response with an `Idempotent-Replay` header. On success I store status+body with a 24-hour TTL. If the handler throws, I delete the claim so the retry can proceed. The atomic claim is the whole trick — a `GET` then `SET` has a race that double-charges. If double-charging is unacceptable I move the dedupe row into the same SQL transaction as the payment, because Redis replication is async and a failover can lose the claim.

**Retry + circuit breaker.**
> Classify the error first: connect errors, read timeouts, 408/425/429/5xx are transient; 4xx are not. Backoff is exponential with **full jitter** — `sleep = uniform(0, min(cap, base * 2**n))` — because plain exponential synchronises every failed client into a retry storm at t+1, t+2, t+4. Honour `Retry-After` when the server sends one. Cap total retry time with a deadline so the caller's own timeout is never exceeded. Wrap it in a circuit breaker: five consecutive failures trips it OPEN, requests fail in microseconds for 30 seconds, then one HALF_OPEN probe decides — success closes it, failure re-opens. In Azure I'd also configure the APIM backend `circuitBreaker` rule so the gateway sheds it before it reaches me.

**Transactional outbox.**
> The problem: saving the order and publishing the event are two systems and there's no distributed transaction. So I write the event as a row in an `outbox` table inside the *same* DB transaction as the order — one atomic unit, both or neither. A separate relay polls `SELECT ... WHERE published_at IS NULL AND next_attempt_at <= now() ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED`, publishes to Service Bus with the row's UUID as `MessageId`, and stamps `published_at` in the same transaction as the lock. `SKIP LOCKED` means N relay pods take disjoint row sets with zero contention. This is at-least-once: a crash after send and before the update republishes. That's fine, because `MessageId` drives Service Bus duplicate detection and the consumer is idempotent anyway. A partial index on `WHERE published_at IS NULL` keeps the scan tiny forever. Higher volume, swap polling for CDC — Debezium on the WAL or the Cosmos change feed.

**Graceful shutdown in Kubernetes.**
> Kubernetes sends SIGTERM and gives you `terminationGracePeriodSeconds`, default 30. I register a signal handler that sets an `asyncio.Event`; the receive loop checks it and stops pulling new messages, then I `asyncio.wait` on in-flight tasks with a timeout a few seconds under the grace period, cancel any stragglers, and settle or abandon each message explicitly. For the HTTP side I add a `preStop` hook that sleeps 5 seconds, because endpoint removal and SIGTERM are concurrent — without the sleep, the ingress is still routing to a pod that has already started shutting down, and you 502 in-flight requests. Grace period has to exceed max handler latency plus drain, so I usually raise it to 45.

---

## Rapid fire

- **Coroutine vs task** — A coroutine is inert until awaited; `create_task` schedules it on the loop to run concurrently.
- **`gather` vs `TaskGroup`** — `TaskGroup` is structured: one failure cancels siblings, raises `ExceptionGroup`. `gather(return_exceptions=True)` for partial results.
- **What cancels a coroutine** — `CancelledError` raised at the next `await`. It's `BaseException`, so `except Exception` won't swallow it; a bare `except:` will.
- **`asyncio.timeout` vs `wait_for`** — Same mechanics; `timeout()` is a context manager, composes better, and supports `reschedule()` for a moving deadline. 3.11+.
- **Bound concurrency** — `asyncio.Semaphore(n)` for in-memory work items; N workers on a bounded `asyncio.Queue` when you need backpressure on the producer.
- **Blocking call in `async def`** — Stalls every concurrent request in that worker. `asyncio.to_thread` for blocking I/O, `ProcessPoolExecutor` for CPU.
- **FastAPI `def` vs `async def`** — `def` routes run in AnyIO's threadpool, default capacity 40 tokens, shared process-wide.
- **httpx defaults** — 5 s timeout on all four phases; `max_connections=100`, `max_keepalive_connections=20`, `keepalive_expiry=5.0 s`.
- **httpx `transport retries`** — Connection-establishment failures only. Status-code retries are yours to write.
- **Full jitter formula** — `sleep = random.uniform(0, min(cap, base * 2 ** attempt))`.
- **Circuit breaker states** — CLOSED → (N failures) → OPEN → (reset timeout) → HALF_OPEN → success closes, failure re-opens.
- **APIM circuit breaker** — Configured on the *backend* entity, not a policy. Not in Consumption tier; one rule per backend; approximate because gateways don't sync.
- **Idempotent HTTP methods** — GET, PUT, DELETE, HEAD, OPTIONS, TRACE. POST and PATCH are not — make POST retryable with an `Idempotency-Key`.
- **429 response should carry** — `Retry-After`, plus `X-RateLimit-Limit` / `-Remaining` / `-Reset`.
- **Token bucket vs sliding window** — Bucket allows bursts up to capacity; sliding window smooths strictly. APIM v2 tiers use token bucket, classic uses sliding window.
- **Why Lua for a distributed limiter** — Redis executes a script atomically and blocks all other server activity for its runtime; `INCR`+`EXPIRE` is two operations with a race.
- **`SET NX EX`** — Atomic claim-with-TTL. Returns truthy only for the first caller. The one-liner dedupe primitive.
- **Fixed-window flaw** — Allows 2× the limit across the boundary.
- **Webhook signature** — HMAC-SHA256 over `"{timestamp}.{raw_body}"`, compared with `hmac.compare_digest`. GitHub uses `X-Hub-Signature-256: sha256=<hex>`.
- **Replay window** — Stripe's libraries default to 300 s tolerance. Reject anything outside it.
- **Fast-ack pattern** — Verify, dedupe, durably enqueue, return 202. Never process synchronously inside a webhook.
- **At-least-once vs exactly-once** — Exactly-once delivery is impossible; exactly-once effect = at-least-once + idempotent consumer with the dedupe row in the same transaction.
- **Service Bus lock** — Default 1 minute, maximum 5 minutes; renew with `AutoLockRenewer` beyond that. Idle connections close at 10 minutes.
- **Service Bus `MaxDeliveryCount`** — Default 10; auto-dead-letters at that count and cannot be disabled, only raised.
- **Service Bus max message** — 256 KB Basic/Standard; Premium up to 100 MB over AMQP, but the per-entity default is 1 MB and 100 MB is opt-in.
- **Claim check pattern** — Payload to Blob, blob URI (SAS) in the message. The direct answer to the 256 KB ceiling.
- **Kafka defaults worth knowing** — `max.poll.interval.ms` 300000, `max.poll.records` 500, `session.timeout.ms` 45000 (brokers 3.0+), `enable.idempotence` true since 3.0.
- **Kafka manual commit** — `enable_auto_commit=False`, commit `offset + 1` *after* processing. Auto-commit at-most-once-ish and loses messages on rebalance.
- **Consumer lag** — Latest broker offset minus committed consumer offset. The single metric to alert on.
- **`SKIP LOCKED`** — Postgres locking clause that skips rows another transaction holds. Purpose-built for queue tables; lets N pollers take disjoint sets.
- **Outbox delivery guarantee** — At-least-once. Dedupe on a stable `MessageId` at the consumer.
- **Saga compensation order** — LIFO over completed steps. A failed compensation is an incident, not a retry loop.
- **Sagas have no isolation** — Mitigate with semantic lock, commutative updates, or re-read-value.
- **Liveness vs readiness** — Liveness restarts the container (process-local checks only); readiness gates traffic (dependency checks). Never put the DB in liveness.
- **Probe defaults** — `initialDelaySeconds` 0, `periodSeconds` 10, `timeoutSeconds` 1, `successThreshold` 1, `failureThreshold` 3.
- **`terminationGracePeriodSeconds`** — Default 30. Add a `preStop: sleep 5` so endpoint removal wins the race against SIGTERM.
- **JWT algorithm allowlist** — Always pass `algorithms=["RS256"]`. Never read `alg` from the token — that's the `alg:none` and HS/RS-confusion attack.
- **JWKS caching** — Cache with a TTL, single-flight the refresh, and force one rate-limited refresh on an unknown `kid` (key rotation). PyJWKClient defaults: `lifespan=300`, `cache_jwk_set=True`, `max_cached_keys=16`.
- **Problem details** — RFC 9457 (obsoletes 7807), `application/problem+json`, members `type`/`title`/`status`/`detail`/`instance`.
- **Breaking API change** — Removing a path/operation/2xx code, adding a required request field, removing or retyping a response field. Additive optional request fields are safe.
- **API versioning** — Non-breaking → APIM *revision*; breaking → new *version*, deprecate the old with a `Deprecation` header and 6+ months of overlap.
- **Block blob limits** — 50,000 blocks, 4,000 MiB max block, ~190.7 TiB max blob, 5,000 MiB single `Put Blob`, ~3,000 req/s per blob.
- **Streaming rule** — Peak RSS must be O(chunk), not O(payload). Async generator plus a bounded queue for backpressure.
- **lxml hardening** — `XMLParser(resolve_entities=False, no_network=True, huge_tree=False)`. XXE and billion-laughs are the two attacks to name.
- **`Decimal` for money** — Always. `float` for currency is an instant credibility loss in a payments/ERP conversation.
- **respx vs mocking httpx** — respx intercepts at the transport, so your real client config, timeouts and retry code all execute. Patching `httpx.get` tests nothing.
- **schemathesis vs Pact** — schemathesis proves you match your own spec (property-based fuzzing); Pact proves you match what consumers actually call. Both.
- **Correlation ID** — `contextvars.ContextVar`, set in middleware, echoed in the response, copied onto message `application_properties`, re-set in the consumer. W3C `traceparent` if you're already on OpenTelemetry.
