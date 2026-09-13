# REST APIs — FastAPI / Flask / Django

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

**How to use this file:** FastAPI is ~75% of it because that is what GenAI shops ship. If you only have 40 minutes, read §1, §3, §4 (SSE code — memorise it), §7, and the Rapid-Fire.

## Table of Contents

| § | Section | Qs |
|---|---------|----|
| 1 | [ASGI, Starlette & the Server Layer](#1-asgi-starlette--the-server-layer) | Q1–Q7 |
| 2 | [Routing, Params & Validation (pydantic v2)](#2-routing-params--validation-pydantic-v2) | Q8–Q13 |
| 3 | [Dependency Injection](#3-dependency-injection) | Q14–Q19 |
| 4 | [Responses, Streaming & Real-Time](#4-responses-streaming--real-time) | Q20–Q26 |
| 5 | [Background Work & Long-Running LLM Jobs](#5-background-work--long-running-llm-jobs) | Q27–Q30 |
| 6 | [Databases & SQLAlchemy 2.0 Async](#6-databases--sqlalchemy-20-async) | Q31–Q34 |
| 7 | [Auth & Security](#7-auth--security) | Q35–Q40 |
| 8 | [Production Hardening](#8-production-hardening) | Q41–Q47 |
| 9 | [Testing, Config & Observability](#9-testing-config--observability) | Q48–Q51 |
| 10 | [Flask](#10-flask) | Q52–Q56 |
| 11 | [Django & DRF](#11-django--drf) | Q57–Q62 |
| — | [FastAPI vs Flask vs Django for an AI Service](#fastapi-vs-flask-vs-django-for-an-ai-service) | table |
| — | [Production Checklist](#production-checklist-for-a-genai-api) | checklist |
| — | [Red Flags / Do NOT Say](#red-flags--do-not-say) | — |
| — | [Rapid-Fire (last 10 min before you walk in)](#rapid-fire-last-10-min-before-you-walk-in) | 25 |

---

## 1. ASGI, Starlette & the Server Layer

### Q1. What is FastAPI actually made of?
`[EASY]`

**Answer:** FastAPI is a thin layer over **Starlette** (routing, middleware, requests/responses, WebSockets, test client) plus **pydantic v2** (validation, serialisation, JSON Schema). FastAPI itself contributes the dependency-injection system, automatic OpenAPI generation, and the parameter-declaration DSL (`Query`, `Path`, `Body`, `Depends`, `Header`).

Mental model: `Starlette = the ASGI web toolkit`, `pydantic = the type layer`, `FastAPI = DI + docs glue`.

**Follow-up they will ask:** *"So could you use Starlette directly?"* — Yes, and you'd get more raw throughput, but you lose validation, DI and OpenAPI. Not worth it for a business API; it is worth it for a pure proxy/streaming gateway with zero body validation.

---

### Q2. ASGI vs WSGI — explain like you'd explain to a Django dev.
`[MEDIUM]`

**Answer:** WSGI is a **synchronous, one-request-per-thread** callable: `app(environ, start_response) -> iterable[bytes]`. ASGI is an **async, event-driven** callable: `async app(scope, receive, send)` where `scope` is the connection metadata, and `receive`/`send` are awaitables that stream messages.

| | WSGI | ASGI |
|---|---|---|
| Signature | `app(environ, start_response)` | `async app(scope, receive, send)` |
| Concurrency unit | OS thread / process | coroutine on one event loop |
| Long I/O (LLM call, 30 s) | blocks a worker thread | blocks nothing |
| WebSockets | no (needs a bolt-on) | yes, first-class |
| SSE / streaming | possible but pins a worker | natural |
| Lifespan (startup/shutdown) | no standard | yes, `lifespan` scope |
| Servers | gunicorn, uWSGI | uvicorn, hypercorn, granian |

**Why this matters for GenAI:** an LLM call is 1–30 s of *pure network wait*. On WSGI with 8 workers you serve 8 concurrent chats. On ASGI one worker can hold hundreds of in-flight LLM calls because the event loop only needs the socket, not a thread.

**Gotcha:** ASGI only helps if you are `await`-ing. A `requests.post()` inside an `async def` blocks the entire event loop and makes ASGI *worse* than WSGI.

---

### Q3. `async def` vs `def` endpoints in FastAPI — what actually happens?
`[HARD]`

**Answer:**
- `async def` → coroutine is scheduled **directly on the event loop**. If you block inside it, you block *every* concurrent request in that worker process.
- `def` (plain sync) → FastAPI/Starlette runs it in an **anyio worker threadpool** via `run_in_threadpool`, so blocking is contained to one thread. The capacity is anyio's default thread limiter — **40 tokens**; the 41st call waits for a token.
- That limiter is **process-wide and shared**: sync `def` *dependencies*, sync `BackgroundTasks` functions, and `UploadFile` disk reads all take tokens from the same 40. One slow sync dependency starves your sync endpoints.

Decision table:

| Your endpoint does | Use |
|---|---|
| `await` on httpx / AsyncOpenAI / asyncpg | `async def` |
| Blocking SDK (`requests`, `psycopg2`, boto3, pandas, `time.sleep`) | `def` |
| Mixed — mostly async but one blocking call | `async def` + `await anyio.to_thread.run_sync(blocking_fn, arg)` |
| CPU-heavy (tokenising 10 MB, PDF parse, local embedding) | offload to a process pool / Celery, not the threadpool |

**Code:**
```python
import anyio
from fastapi import FastAPI
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI()

@app.post("/good-async")
async def good_async(q: str) -> dict:
    r = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": q}],
    )
    return {"answer": r.choices[0].message.content}

@app.post("/good-sync")            # legacy blocking SDK -> plain def
def good_sync(q: str) -> dict:
    import requests
    return requests.post("https://legacy.internal/score", json={"q": q}, timeout=10).json()

def _parse_pdf_blocking(path: str) -> str:   # CPU/IO-blocking third-party call
    ...

@app.post("/mixed")
async def mixed(pdf_path: str) -> dict:
    text = await anyio.to_thread.run_sync(_parse_pdf_blocking, pdf_path)  # frees the loop
    return {"chars": len(text)}
```

**Gotcha (the classic interview trap):** `async def` + `time.sleep(5)` → throughput collapses to 1 req/5 s per worker. `def` + `time.sleep(5)` → 40 concurrent. Counter-intuitive but true: the *sync* version is faster here.

**Follow-up they will ask:** *"How do you raise the threadpool limit?"* — set the anyio capacity limiter during startup (inside `lifespan`, **not** the deprecated `@app.on_event("startup")`):
```python
from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # must run inside the running loop -> lifespan, not import time
    anyio.to_thread.current_default_thread_limiter().total_tokens = 100
    yield

app = FastAPI(lifespan=lifespan)
```
Raising it is a band-aid; fixing the blocking call is the real answer.

---

### Q4. uvicorn vs gunicorn vs "gunicorn with uvicorn workers" — what do you run in prod?
`[MEDIUM]`

**Answer:** In containers/Kubernetes: **run uvicorn directly with `--workers N`** and let the orchestrator handle restarts and scaling. On a bare VM where you want a battle-tested process supervisor: **gunicorn as the master with uvicorn worker class**.

```bash
# Container / K8s (preferred): 1 process per container, replicas via HPA
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 \
    --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 30

# VM: gunicorn master + uvicorn workers
gunicorn app.main:app -k uvicorn_worker.UvicornWorker \
    -w 4 -b 0.0.0.0:8000 --timeout 120 --graceful-timeout 30
```

Key facts:
- `pip install "uvicorn[standard]"` pulls **uvloop** (C event loop, ~2–4× loop throughput) and **httptools** (fast HTTP parser). Without `[standard]` you get pure-Python asyncio + h11.
- The worker class moved out of uvicorn core: uvicorn ≥0.30 deprecated `uvicorn.workers.UvicornWorker` in favour of the separate **`uvicorn-worker`** package (`uvicorn_worker.UvicornWorker`). Say both names — they will accept either.
- Worker sizing for an **I/O-bound LLM API**: `workers ≈ CPU cores` is *over*-provisioning. Start at 2 and scale on p95 latency; each worker can hold hundreds of in-flight awaits. For CPU-bound work use `2 × cores + 1`.
- `--reload` is dev-only and incompatible with `--workers`.

**Gotcha:** every worker is a separate process → separate memory. If you load a 500 MB embedding model at import time, 4 workers = 2 GB RSS. Load heavy models once in a sidecar/inference service, not per worker.

---

### Q5. What is uvloop and when does it not help?
`[EASY]`

**Answer:** uvloop is a drop-in `asyncio` event-loop implementation built on libuv (the Node.js loop), typically 2–4× faster at socket/event handling. Enabled automatically by `uvicorn[standard]`, or `uvicorn --loop uvloop`.

It does **not** help when your latency is dominated by an upstream LLM (1–20 s). Saving 200 µs of loop overhead on a 3 s OpenAI call is noise. It matters at 10k+ req/s of small payloads. Not available on Windows.

---

### Q6. How do you do startup/shutdown work now that `@app.on_event` is deprecated?
`[MEDIUM]`

**Answer:** Use the **`lifespan` async context manager** (`@app.on_event("startup"/"shutdown")` is deprecated since FastAPI 0.93). Everything before `yield` is startup; after `yield` is shutdown. Share objects via `app.state` or a module-level container.

**Code:**
```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # --- startup: create long-lived, pooled clients ONCE ---
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    app.state.openai = AsyncOpenAI(timeout=60.0, max_retries=2)
    app.state.redis = aioredis.from_url("redis://cache:6379", decode_responses=True)
    engine = create_async_engine("postgresql+asyncpg://u:p@db/app", pool_size=10, max_overflow=20)
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    yield
    # --- shutdown: drain in reverse order ---
    await app.state.http.aclose()
    await app.state.openai.close()
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(lifespan=lifespan, title="genai-api", version="1.0.0")
```

**Gotcha:** creating an `httpx.AsyncClient()` (or `AsyncOpenAI()`) *inside* a handler is the #1 perf bug in GenAI services — you get a new DNS lookup + TCP + TLS handshake and zero connection reuse on every request. Cost is round-trip-dependent — **order of tens to a couple of hundred milliseconds** in a typical cloud region, more cross-region. Create once in lifespan.

**Follow-up they will ask:** *"Does lifespan run per worker?"* — Yes, once per worker process. So a "run migrations on startup" hook in lifespan runs N times; use an init container / release command instead.

---

### Q7. Explain FastAPI middleware, and the trap with streaming responses.
`[HARD]`

**Answer:** Middleware wraps every request/response. Two flavours:

1. **Starlette `BaseHTTPMiddleware`** — the ergonomic one (`@app.middleware("http")`). Gives you `Request`/`Response` objects.
2. **Pure ASGI middleware** — a callable `async (scope, receive, send)`. Lower-level and more verbose (you inspect/patch raw `http.response.start` messages yourself), but it adds no extra task/queue per request and does not interfere with streaming.

**Code (request-id + timing, the one to write on a whiteboard):**
```python
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request

app = FastAPI()
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    response.headers["x-request-id"] = rid
    response.headers["x-process-time-ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
    return response
```

**Gotcha (say this, it scores points):** `BaseHTTPMiddleware` runs the downstream app in a *separate task* and pipes the body back through a memory stream. It can therefore **buffer or delay SSE/streaming responses**, and it breaks `await request.is_disconnected()` detection, so your LLM stream keeps burning tokens after the user closed the tab. For token-streaming endpoints either use **pure ASGI middleware** or exclude those routes. Note also that a `ContextVar` set *inside* the endpoint is not visible back in the middleware (the child task gets a copy of the context) — set it in the middleware **before** `call_next`, as above.

**Order matters:** middleware added last runs **first** (outermost). So add `CORSMiddleware` last if you want CORS headers even on responses produced by an inner middleware that errored.

---

## 2. Routing, Params & Validation (pydantic v2)

### Q8. How does FastAPI decide if a parameter is path / query / body / header?
`[EASY]`

**Answer:** Rules, in order:
1. Name appears in the route path → **path param**.
2. Type is a pydantic `BaseModel` → **body**.
3. Declared with an explicit marker (`Query`, `Header`, `Cookie`, `Form`, `File`, `Body`, `Depends`) → that.
4. Otherwise, scalar type (`int`, `str`, `bool`, `float`, `UUID`, `datetime`, `Enum`) → **query param**.

**Code (modern `Annotated` style — use this, not the old default-value style):**
```python
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Header, Path, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1", tags=["chat"])

class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)

@router.post("/threads/{thread_id}/chat")
async def chat(
    thread_id: Annotated[UUID, Path(description="Conversation id")],
    body: ChatRequest,
    stream: Annotated[bool, Query()] = False,
    mode: Annotated[Literal["fast", "quality"], Query()] = "fast",
    x_tenant_id: Annotated[str, Header()] = "default",   # maps to X-Tenant-Id
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    return {"thread_id": str(thread_id), "mode": mode, "tenant": x_tenant_id}
```

**Gotcha:** header names are converted `x_tenant_id` → `X-Tenant-Id` automatically (underscores → hyphens, case-insensitive). Use `Header(alias=...)` when you need an exact non-standard name, and `convert_underscores=False` to disable the conversion.

---

### Q9. What changed in pydantic v2 that matters for a FastAPI service?
`[MEDIUM]`

**Answer:** Core rewritten in Rust (`pydantic-core`) → validation typically **5–50× faster**; that alone cuts p50 on validation-heavy endpoints. FastAPI ≥0.100 supports v2.

Rename map (they *will* test this):

| v1 | v2 |
|---|---|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `parse_raw()` | `model_validate_json()` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator(mode="before"/"after")` |
| `schema()` | `model_json_schema()` |
| `allow_population_by_field_name` | `populate_by_name` |
| `Optional[str]` implicitly optional | must write `str | None = None` |

**Code:**
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class DocumentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def lowercase_unique(cls, v: list[str]) -> list[str]:
        return sorted({t.lower() for t in v})

    @model_validator(mode="after")
    def not_empty(self):
        if not self.content.strip():
            raise ValueError("content must not be blank")
        return self

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # was orm_mode
    id: int
    title: str
```

**Gotcha:** `extra="forbid"` turns unknown fields into a 422. Great for internal APIs, dangerous for public ones (clients that send extra keys break on your next release). Default is `extra="ignore"`.

---

### Q10. `response_model` — what does it buy you, and how do you trim the payload?
`[MEDIUM]`

**Answer:** `response_model` does four things: (1) validates your output, (2) **filters out fields not in the model** — the security win, (3) serialises correctly (datetime/UUID/Decimal), (4) documents the response in OpenAPI.

**Code:**
```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr   # EmailStr needs `pip install "pydantic[email]"`

app = FastAPI()

class UserDB(BaseModel):
    id: int
    email: EmailStr
    hashed_password: str      # must never leak
    internal_score: float | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    internal_score: float | None = None

@app.get("/users/{uid}", response_model=UserOut, response_model_exclude={"internal_score"})
async def get_user(uid: int) -> UserDB:            # returns MORE than UserOut
    return UserDB(id=uid, email="a@b.com", hashed_password="$2b$12$...", internal_score=0.9)

@app.get("/users/{uid}/sparse", response_model=UserOut, response_model_exclude_unset=True)
async def sparse(uid: int): ...
```

Flags:

| Flag | Effect |
|---|---|
| `response_model_exclude={"a","b"}` | always drop these fields |
| `response_model_include={...}` | whitelist |
| `response_model_exclude_unset=True` | omit fields the handler never set (not just defaults) |
| `response_model_exclude_defaults=True` | omit fields equal to their default |
| `response_model_exclude_none=True` | omit `None` values |

**Gotcha:** Modern FastAPI can infer the response model from the **return type annotation**. If you annotate `-> UserDB` and *don't* pass `response_model`, the hashed password leaks. When they differ, always set `response_model` explicitly — it wins over the annotation.

---

### Q11. What is a 422 in FastAPI, and how do you customise it?
`[MEDIUM]`

**Answer:** 422 Unprocessable Entity is FastAPI's response when pydantic validation of the request fails. It raises `RequestValidationError` and returns `{"detail": [{"type", "loc", "msg", "input"}, ...]}`. Override with an exception handler when you have a house error envelope.

**Code:**
```python
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "request_id": request.headers.get("x-request-id", "-"),
                "fields": [
                    {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
                    for e in exc.errors()
                ],
            }
        },
    )
```

**Gotcha:** `exc.errors()` in pydantic v2 may contain non-JSON-serialisable values in `input`/`ctx` (e.g. a `ValueError` instance). Never `json.dumps(exc.errors())` blindly — pick out `loc`/`msg` as above, or pass the whole thing through `fastapi.encoders.jsonable_encoder(exc.errors())`. Note that FastAPI's `RequestValidationError.errors()` takes **no arguments** — the `include_url=False` / `include_input=False` kwargs exist on pydantic's own `ValidationError.errors()`, not on FastAPI's wrapper, so calling `exc.errors(include_url=False)` in a handler raises `TypeError`.

**Naming note:** Starlette renamed the constant to `status.HTTP_422_UNPROCESSABLE_CONTENT` (matching the current IANA name) and kept `HTTP_422_UNPROCESSABLE_ENTITY` as a deprecated alias. Both resolve to `422`; use whichever your pinned Starlette version exposes.

**Follow-up:** *"Why 422 and not 400?"* — 400 means malformed syntax; 422 means syntactically valid JSON that fails semantic validation. Many enterprises mandate 400; you change it in exactly this handler.

---

### Q12. `HTTPException` vs a custom exception — what do you use in a layered app?
`[MEDIUM]`

**Answer:** Raise **domain exceptions** in the service layer (no HTTP knowledge), and translate them to HTTP in one place with `@app.exception_handler`. `HTTPException` is fine directly inside a router/dependency, but leaking it into `services/` couples business logic to the web framework.

**Code:**
```python
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()

class AppError(Exception):
    status_code = 500
    code = "internal_error"
    def __init__(self, message: str): self.message = message

class NotFound(AppError):      status_code, code = 404, "not_found"
class QuotaExceeded(AppError): status_code, code = 429, "quota_exceeded"
class UpstreamLLMError(AppError): status_code, code = 502, "llm_upstream_error"

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers={"Retry-After": "30"} if isinstance(exc, QuotaExceeded) else None,
    )

# direct use is still fine at the edge:
@app.get("/docs/{doc_id}")
async def read_doc(doc_id: int):
    if doc_id < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="doc_id must be positive")
```

**Gotcha:** a bare `@app.exception_handler(Exception)` catches everything *including* things you want to bubble to your APM. Always `logger.exception(...)` inside it and never return the raw `str(exc)` to the client (leaks stack/SQL/prompt content).

---

### Q13. How do you version an API, and how do you structure routers?
`[EASY]`

**Answer:** URL-path versioning (`/v1/...`) is the pragmatic default: visible in logs, cacheable, trivial to route at the gateway. Header versioning (`Accept: application/vnd.acme.v2+json`) is purer but harder to debug and breaks browser testing.

**Code:**
```python
# app/api/v1/chat.py
from fastapi import APIRouter, Depends

from app.api.deps import verify_api_key

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])

# app/api/v1/__init__.py
from fastapi import APIRouter
from . import chat, documents, agents
v1 = APIRouter(prefix="/v1")
v1.include_router(chat.router)
v1.include_router(documents.router)
v1.include_router(agents.router)

# app/main.py
from app.api.v1 import v1
from app.api.v2 import v2

app.include_router(v2)
app.include_router(v1, deprecated=True)   # renders a strikethrough in Swagger during sunset
```

Rules: additive changes (new optional field) → no version bump. Removing/renaming a field or changing types → new version. Keep N-1 alive for a deprecation window and emit a `Deprecation` / `Sunset` response header.

---

## 3. Dependency Injection

### Q14. How does `Depends` work and why is it better than a decorator?
`[MEDIUM]`

**Answer:** `Depends(callable)` tells FastAPI to *call that callable first*, resolve **its** parameters the same way (recursively), and inject the result. Because the dependency's own signature is inspected, it can itself declare query params, headers and sub-dependencies — and all of it shows up in OpenAPI. A decorator can't do that.

**Code (nested dependencies):**
```python
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

async def get_settings() -> Settings:                # leaf
    return get_cached_settings()

async def get_db(settings: Annotated[Settings, Depends(get_settings)]) -> AsyncIterator[AsyncSession]:
    async with app.state.sessionmaker() as s:
        yield s

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await verify_token_and_load(token, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]   # reusable alias

@app.get("/me")
async def me(user: CurrentUser) -> dict:
    return {"id": user.id}
```

**Gotcha:** `Depends()` with no argument uses the **type annotation** as the dependency: `commons: Annotated[CommonParams, Depends()]`. Neat for class-based deps.

**Follow-up they will ask:** *"Dependency that returns nothing?"* — Put it in the decorator or router for pure side-effects/guards: `@app.get("/x", dependencies=[Depends(verify_api_key)])`, or `APIRouter(dependencies=[...])` to apply to every route.

---

### Q15. Explain sub-dependency caching in FastAPI.
`[HARD]`

**Answer:** Within a **single request**, FastAPI caches each dependency's result keyed by `(callable, security_scopes)`. So if `get_db` is required by three different dependencies in one request, it is executed **once** and the same session is shared. Disable with `Depends(fn, use_cache=False)`.

```python
# get_settings runs ONCE for this request even though 3 deps need it
async def a(s: Annotated[Settings, Depends(get_settings)]): ...
async def b(s: Annotated[Settings, Depends(get_settings)]): ...
async def c(s: Annotated[Settings, Depends(get_settings)]): ...

# force a fresh value every time (e.g. a per-call correlation token)
async def handler(t: Annotated[str, Depends(new_trace_id, use_cache=False)]): ...
```

**Gotcha:** the cache is **per request**, not global. For process-wide caching of expensive, immutable objects (settings, a tokenizer, a compiled regex) use `functools.lru_cache` on the dependency function itself:
```python
from functools import lru_cache
@lru_cache
def get_settings() -> Settings: return Settings()   # sync + lru_cache = created once per process
```

---

### Q16. What is a dependency with `yield` and what are its rules?
`[HARD]`

**Answer:** A generator dependency: code before `yield` = setup, code after = teardown. FastAPI wraps them in an `AsyncExitStack`, so teardown runs in reverse order — the standard way to manage DB sessions, file handles, tracing spans.

**Code:**
```python
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncIterator[AsyncSession]:
    async with app.state.sessionmaker() as session:
        try:
            yield session
            await session.commit()          # commit only on clean exit
        except Exception:
            await session.rollback()
            raise
        # `async with` closes/returns the connection to the pool
```

Rules to state out loud:
1. **When does teardown run?** Since **FastAPI 0.106.0** the exit code runs as soon as the path operation returns — **before the response body is sent** and **before** `BackgroundTasks`. (Before 0.106 it was the opposite: teardown ran after the response and after background tasks; that is the old behaviour people still quote.) The change exists so you don't hold a DB connection while bytes travel the network.
2. **Consequence A — background tasks:** a `yield`-dep resource (DB session, request-scoped httpx client) is already closed when a `BackgroundTask` runs. Open a fresh session inside the task.
3. **Consequence B — streaming (the one seniors probe):** a `StreamingResponse` body generator is iterated *after* the route returns, i.e. after teardown. So a `Depends(get_db)` session used inside an SSE/CSV generator is **already closed** → create the session inside the generator instead (see Q22).
4. Raising in the exit code *is* possible on modern FastAPI (the exception propagates and your handlers run) — but only while the response hasn't started, so it is useless for streaming routes. Prefer validating **before** `yield`.
5. Exceptions from the route propagate *through* the `yield`, so `try/except/finally` around it works — always re-raise. (FastAPI ≥0.110 re-raises a swallowed exception for you rather than leaving the request in an undefined state; don't rely on it.)
6. Sub-dependencies with `yield` nest correctly; teardown is LIFO.

---

### Q17. How do you override dependencies in tests?
`[EASY]`

**Answer:** `app.dependency_overrides` — a plain dict mapping the original callable to a replacement. This is FastAPI's killer testing feature.

**Code:**
```python
from fastapi.testclient import TestClient

async def fake_user() -> User:
    return User(id=1, email="test@x.com", role="admin")

app.dependency_overrides[get_current_user] = fake_user
app.dependency_overrides[get_openai_client] = lambda: FakeLLM(canned="hello")

client = TestClient(app)
assert client.get("/me").json()["id"] == 1

app.dependency_overrides.clear()      # always clean up (use a pytest fixture)
```

**Gotcha:** the key must be the **exact same function object** used in `Depends(...)`. Re-importing under a different module path (`app.deps.get_db` vs `deps.get_db`) silently fails to override.

---

### Q18. Write an RBAC / scope dependency.
`[MEDIUM]`

**Answer:** A parameterised **class-based dependency** — `__init__` takes config, `__call__` is the actual dependency.

**Code:**
```python
from typing import Annotated
from fastapi import Depends, HTTPException, status

class RequireRole:
    def __init__(self, *allowed: str) -> None:
        self.allowed = set(allowed)

    async def __call__(self, user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in self.allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"requires one of {sorted(self.allowed)}",
            )
        return user

admin_only = RequireRole("admin")
staff = RequireRole("admin", "analyst")

@app.delete("/v1/documents/{doc_id}", status_code=204)
async def delete_doc(doc_id: int, user: Annotated[User, Depends(admin_only)]): ...

@app.get("/v1/reports", dependencies=[Depends(staff)])
async def reports(): ...
```

**Follow-up they will ask:** *"OAuth2 scopes?"* — FastAPI has `Security(get_user, scopes=["docs:write"])` + `SecurityScopes`, which also renders the required scopes in the Swagger UI. Use it when scopes come from the token; use `RequireRole` when roles come from your DB.

---

### Q19. How do you inject an LLM client / RAG retriever cleanly?
`[MEDIUM]`

**Answer:** Build it **once in lifespan**, expose it via a trivial dependency that reads from `app.state`. This keeps handlers pure and lets tests swap in a fake with `dependency_overrides`.

**Code:**
```python
from typing import Annotated, Protocol
from fastapi import Depends, Request
from openai import AsyncOpenAI

class Retriever(Protocol):
    async def search(self, query: str, k: int = 5) -> list[str]: ...

def get_llm(request: Request) -> AsyncOpenAI:
    return request.app.state.openai

def get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever

LLM = Annotated[AsyncOpenAI, Depends(get_llm)]
Ret = Annotated[Retriever, Depends(get_retriever)]

@app.post("/v1/rag/answer")
async def answer(q: str, llm: LLM, retriever: Ret) -> dict:
    ctx = await retriever.search(q, k=5)
    resp = await llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer only from CONTEXT. If absent, say you don't know."},
            {"role": "user", "content": f"CONTEXT:\n{chr(10).join(ctx)}\n\nQ: {q}"},
        ],
        temperature=0.0,
    )
    return {"answer": resp.choices[0].message.content, "sources": ctx}
```

---

## 4. Responses, Streaming & Real-Time

### Q20. **Stream LLM tokens from OpenAI to a browser with SSE. Write the endpoint.**
`[HARD]`

**Answer:** Use `StreamingResponse` with `media_type="text/event-stream"` and an async generator that iterates the OpenAI stream, emitting `data: <json>\n\n` frames. Critical production details: **disconnect detection** (stop burning tokens when the tab closes), **`X-Accel-Buffering: no`** (nginx buffers SSE by default and you'll see zero output until completion), **error frames instead of a 500** (headers are already sent, you cannot change the status code mid-stream), and a **heartbeat** so proxies don't kill an idle connection.

**Code (server — this is the one to memorise):**
```python
import asyncio
import json
import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1")
client = AsyncOpenAI(timeout=httpx.Timeout(60.0, connect=5.0), max_retries=2)


class ChatIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    model: str = "gpt-4o-mini"


def sse(data: str, event: str | None = None) -> str:
    """Format one SSE frame. Blank line terminates the frame."""
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {data}\n\n"


async def token_stream(body: ChatIn, request: Request) -> AsyncIterator[str]:
    stream = None
    try:
        stream = await client.chat.completions.create(
            model=body.model,
            messages=[{"role": "user", "content": body.prompt}],
            stream=True,
            stream_options={"include_usage": True},   # final chunk carries token usage
        )
        async for chunk in stream:
            if await request.is_disconnected():       # client closed the tab -> stop paying
                log.info("client disconnected, aborting stream")
                break
            if not chunk.choices:                     # usage-only final chunk
                if chunk.usage:
                    yield sse(json.dumps({"usage": chunk.usage.model_dump()}), event="usage")
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield sse(json.dumps({"token": delta}), event="token")
        yield sse("[DONE]", event="done")
    except asyncio.CancelledError:                    # server shutdown / client abort
        raise
    except Exception as exc:                          # status already 200 -> send an error EVENT
        log.exception("llm stream failed")
        yield sse(json.dumps({"code": type(exc).__name__}), event="error")
    finally:
        if stream is not None:
            await stream.close()                      # release the upstream HTTP connection


@router.post("/chat/stream")
async def chat_stream(body: ChatIn, request: Request) -> StreamingResponse:
    return StreamingResponse(
        token_stream(body, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # nginx: do not buffer
        },
    )
```

**Code (browser client — note the trap):**
```javascript
// EventSource only does GET and cannot send headers/body -> for POST use fetch + reader
const res = await fetch("/v1/chat/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ prompt: "explain RAG in 3 lines" }),
});
const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
let buf = "";
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buf += value;
  const frames = buf.split("\n\n");
  buf = frames.pop();                       // keep the incomplete tail
  for (const f of frames) {
    const line = f.split("\n").find((l) => l.startsWith("data: "));
    if (!line) continue;
    const payload = line.slice(6);
    if (payload === "[DONE]") return;
    document.getElementById("out").textContent += JSON.parse(payload).token;
  }
}
```

**Gotcha:** the `sse_starlette` package (`from sse_starlette.sse import EventSourceResponse`) gives you heartbeats/ping and clean disconnect handling for free — mention it as the production choice, but be able to hand-roll the frames as above.

**Precision point on disconnects:** Starlette's `StreamingResponse` already races your generator against a `listen_for_disconnect` task and **cancels the generator** when `http.disconnect` arrives — that is why the `except asyncio.CancelledError: raise` + `finally: await stream.close()` pair matters. The explicit `await request.is_disconnected()` poll is belt-and-braces (it is a non-blocking peek at the receive channel), and it is exactly what `BaseHTTPMiddleware` breaks. Say both mechanisms.

**API-surface note:** OpenAI's newer **Responses API** (`client.responses.create(..., stream=True)`, deltas arrive as typed `response.output_text.delta` events) is the recommended surface for new integrations; `chat.completions` is still fully supported and is what most production code you'll be handed uses. Either is a safe answer — just don't mix the two shapes.

**Follow-up they will ask:** *"SSE vs WebSocket for a chatbot?"* — SSE: unidirectional server→client, plain HTTP, auto-reconnect built into `EventSource`, works through corporate proxies, trivially load-balanced. WebSocket: bidirectional, needed for voice/interrupts/collaborative editing, but needs sticky sessions and its own auth handshake. **For token streaming, SSE. For a live agent that takes mid-flight user interrupts, WebSocket.**

---

### Q21. Show the same streaming endpoint against **Azure OpenAI**.
`[MEDIUM]`

**Answer:** Same code, different client. Azure uses `AsyncAzureOpenAI` with `azure_endpoint`, `api_version`, and — critically — `model=` is the **deployment name**, not the model name.

**Code:**
```python
import os
from openai import AsyncAzureOpenAI

client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],   # https://<res>.openai.azure.com/
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-10-21",                              # GA version; pin it
    timeout=60.0,
    max_retries=2,
)

async def stream_azure(prompt: str):
    stream = await client.chat.completions.create(
        model="gpt-4o-mini-prod",        # <-- DEPLOYMENT name in Azure
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**Gotcha:** Azure returns **429 with a `Retry-After` header** when you exceed TPM/RPM quota. The SDK's `max_retries` handles some of it, but honour `Retry-After` explicitly and surface 429 (not 500) to your caller.

**Entra ID (keyless) auth** — the preferred production pattern, no secret to rotate. Pass `azure_ad_token_provider=` instead of `api_key=`:
```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",   # the AOAI scope
)
client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)
```
The identity needs the **Cognitive Services OpenAI User** role on the resource. Note `DefaultAzureCredential`/`get_bearer_token_provider` are the *sync* azure-identity primitives; the OpenAI SDK calls the provider in a threadpool, so this is safe from async code, but `azure.identity.aio` + `azure_ad_token_provider` (async callable) is the cleaner fit for a fully-async service.

---

### Q22. `StreamingResponse` vs `FileResponse` vs returning a generator — and how do you stream a large file?
`[MEDIUM]`

**Answer:**

| Class | Use for |
|---|---|
| `JSONResponse` | normal payloads (default) |
| `StreamingResponse` | SSE, chunked generation, on-the-fly CSV/ZIP, proxying an upstream stream |
| `FileResponse` | a file on disk; sets `Content-Length`, streams in chunks, handles `Range` requests (Starlette ≥0.45) |
| `RedirectResponse` | 3xx |
| `Response` | raw bytes + custom `media_type` |
| `ORJSONResponse` | large JSON, ~2–3× faster serialisation (`pip install orjson`) |

```python
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, StreamingResponse
from sqlalchemy import select

app = FastAPI(default_response_class=ORJSONResponse)

@app.get("/v1/export.csv")
async def export_csv() -> StreamingResponse:
    # NOTE: do NOT take `db: DB` (a `yield` dependency) here. Since FastAPI 0.106 the
    # dependency teardown runs when this function RETURNS -- i.e. before the generator
    # below is ever iterated -- so that session would already be closed. Own the session
    # inside the generator instead.
    async def rows() -> AsyncIterator[str]:
        yield "id,title,created_at\n"
        async with SessionLocal() as db:
            # AsyncSession.stream_scalars() is a COROUTINE returning an AsyncScalarResult --
            # you must await it before iterating. `async for r in db.stream_scalars(...)`
            # without the await is a TypeError.
            result = await db.stream_scalars(select(Doc).execution_options(yield_per=1000))
            async for r in result:                      # server-side cursor, constant memory
                yield f"{r.id},{r.title},{r.created_at.isoformat()}\n"
    return StreamingResponse(
        rows(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="docs.csv"'},
    )
```

**Gotcha:** with `StreamingResponse` you have **no `Content-Length`**, so no progress bar, and the status code is committed on the first byte. Validate everything *before* returning the response object.

**Gotcha 2 (the one above, stated for the interviewer):** anything a streaming generator needs must outlive the request handler. `yield`-dependencies do not — they tear down when the handler returns, before the body is produced. Long-lived objects on `app.state` (engine, httpx client, OpenAI client) are fine; per-request `yield` resources are not.

---

### Q23. Handle file upload (PDF for a RAG ingest endpoint).
`[MEDIUM]`

**Answer:** `UploadFile` is a spooled temp file (in memory up to ~1 MB, then on disk), so a 200 MB PDF doesn't blow up RAM. Read it in chunks, enforce a size cap yourself — FastAPI does not.

**Code:**
```python
import os
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, File, Form, HTTPException, UploadFile, status

MAX_BYTES = 25 * 1024 * 1024        # 25 MB
ALLOWED = {"application/pdf", "text/plain", "text/markdown"}

@app.post("/v1/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload(
    file: Annotated[UploadFile, File()],
    tasks: BackgroundTasks,                             # no default -> must precede defaulted params
    collection: Annotated[str, Form()] = "default",
) -> dict:
    if file.content_type not in ALLOWED:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"got {file.content_type}")

    size, dest = 0, f"/data/uploads/{uuid.uuid4().hex}"
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):      # 1 MB chunks
            size += len(chunk)
            if size > MAX_BYTES:
                out.close(); os.remove(dest)
                # newer Starlette also exposes HTTP_413_CONTENT_TOO_LARGE (same value, 413)
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "max 25 MB")
            out.write(chunk)
    tasks.add_task(enqueue_ingest, dest, collection)
    return {"status": "accepted", "bytes": size}
```

**Gotcha:** `content_type` comes from the client and is trivially spoofed — sniff magic bytes (`python-magic`) for anything security-relevant. Also needs `pip install python-multipart` or FastAPI raises at import time. Enforce the real limit at nginx/ingress (`client_max_body_size`) too, so you reject before buffering.

---

### Q24. WebSocket endpoint in FastAPI — write one with auth and a connection manager.
`[MEDIUM]`

**Answer:**
```python
from typing import Annotated

from fastapi import Query, WebSocket, WebSocketDisconnect, WebSocketException, status

class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, set[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.active.setdefault(room, set()).add(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        self.active.get(room, set()).discard(ws)

    async def broadcast(self, room: str, msg: str) -> None:
        for ws in list(self.active.get(room, ())):
            try:
                await ws.send_text(msg)
            except Exception:
                self.disconnect(room, ws)

manager = ConnectionManager()

@app.websocket("/ws/agent/{room}")
async def agent_ws(ws: WebSocket, room: str, token: Annotated[str, Query()]):
    user = await verify_token(token)             # browsers can't set WS headers -> token in query
    if user is None:
        # raised BEFORE accept() -> Starlette rejects the handshake (HTTP 403)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="bad token")
    await manager.connect(room, ws)
    try:
        while True:
            prompt = await ws.receive_text()
            async for tok in run_agent_streaming(prompt, user):
                await ws.send_json({"type": "token", "value": tok})
            await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass                                     # normal client close
    finally:
        manager.disconnect(room, ws)             # finally, not except -- a crash must also deregister
```

**Gotcha:** the manager dict is **per worker process**. With 4 workers, a broadcast reaches only the clients attached to that one worker (~25% if connections are evenly spread). Fan out through **Redis pub/sub** in real deployments. Also: WebSockets need sticky sessions / `proxy_read_timeout` tuning at the LB.

**Security gotcha:** a token in the query string lands in access logs and proxy logs. The cleaner options are (a) accept the connection, then require an auth message as the **first frame** and close with 1008 if it doesn't arrive within a few seconds, or (b) smuggle the token in the `Sec-WebSocket-Protocol` header — the browser's only settable handshake header, via the second argument of `new WebSocket(url, ["bearer", token])`. With (b) the server **must** echo one of the offered subprotocols back: `await ws.accept(subprotocol="bearer")`, otherwise the browser aborts the connection.

---

### Q25. How do you set status codes correctly?
`[EASY]`

**Answer:** Declare `status_code=` on the decorator; use the `status` module for readability. Change it dynamically with the `Response` object.

| Code | When |
|---|---|
| 200 | GET / successful PUT with body |
| 201 | resource created (return `Location` header) |
| 202 | accepted, work happens async (long LLM jobs) |
| 204 | delete/no content — **must return `None`, no body** |
| 400 | malformed request |
| 401 | not authenticated (+ `WWW-Authenticate`) |
| 403 | authenticated but not allowed |
| 404 | not found |
| 409 | conflict / duplicate idempotency key |
| 413 | payload too large |
| 422 | validation failed (FastAPI default) |
| 429 | rate limited (+ `Retry-After`) |
| 499 | client closed (nginx-only, appears in logs on aborted streams) |
| 502/503 | upstream LLM failed / circuit open |
| 504 | upstream timeout |

```python
from fastapi import Response, status

@app.post("/v1/items", status_code=status.HTTP_201_CREATED)
async def create(item: ItemIn, response: Response) -> ItemOut:
    obj = await svc.create(item)
    response.headers["Location"] = f"/v1/items/{obj.id}"
    return obj
```

---

### Q26. Configure CORS properly for a browser chat UI.
`[MEDIUM]`

**Answer:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.acme.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
    expose_headers=["X-Request-Id", "X-RateLimit-Remaining", "Retry-After"],
    max_age=600,                # cache preflight for 10 min
)
```

**Gotcha (they love this one):** `allow_origins=["*"]` **with** `allow_credentials=True` is invalid per spec — browsers reject it. You must enumerate origins (or use `allow_origin_regex`) once cookies/`Authorization` are in play. Also, custom response headers are invisible to JS unless listed in `expose_headers`.

---

## 5. Background Work & Long-Running LLM Jobs

### Q27. `BackgroundTasks` vs Celery vs ARQ — when do you use which?
`[MEDIUM]`

**Answer:**

| | FastAPI `BackgroundTasks` | ARQ / Dramatiq | Celery |
|---|---|---|---|
| Runs where | **same process**, after response | separate worker, Redis queue | separate worker, Redis/RabbitMQ |
| Async native | yes | yes (ARQ is asyncio-first) | no (sync workers; async support limited) |
| Survives a deploy/crash | **no — task is lost** | yes (queue persists) | yes |
| Retries / scheduling | none | yes | yes (+ beat, chords, chains) |
| Setup cost | zero | low | high |
| Good for | send an email, write an audit row, fire a webhook (<1 s) | async LLM/RAG jobs, embeddings backfill | mature stacks, complex workflows, Django shops |

**Code:**
```python
from fastapi import BackgroundTasks

@app.post("/v1/chat", status_code=201)
async def chat(body: ChatIn, tasks: BackgroundTasks) -> ChatOut:
    answer = await llm_answer(body)
    tasks.add_task(log_interaction, body.prompt, answer)  # fire-and-forget, in-process
    return ChatOut(answer=answer)
```

**Gotcha:** `BackgroundTasks` runs **inside the same worker** — a 60 s ingest task there occupies the process (and blocks the event loop entirely if it's sync-blocking). Rule of thumb: `BackgroundTasks` only for <1 s, best-effort, loss-tolerant work. Everything else goes to a real queue.

**Follow-up they will ask:** *"Why not `asyncio.create_task`?"* — Because you must hold a strong reference (the loop only keeps weak refs, so the task can be garbage-collected mid-flight) and exceptions vanish silently. `BackgroundTasks` at least ties the task to the request lifecycle.

---

### Q28. How do you expose a 3-minute agentic workflow over HTTP?
`[HARD]`

**Answer:** Never hold an HTTP request open for 3 minutes — LBs, nginx (`proxy_read_timeout` 60 s default) and browsers will cut it. Three valid patterns:

| Pattern | Shape | Use when |
|---|---|---|
| **202 + polling** | `POST /jobs` → `202` + `{job_id}` + `Location: /jobs/{id}`; client polls `GET /jobs/{id}` → `pending/running/succeeded/failed` | default; simplest; survives client reconnects |
| **Webhook / callback** | client supplies `callback_url`; you POST the result (signed HMAC, retries w/ backoff) | server-to-server, batch jobs |
| **SSE / WebSocket** | stream partial progress + tokens live | user is watching a UI; best UX |

Best-in-class GenAI answer: **202 + job row in Postgres + Redis-backed worker, plus an SSE `GET /jobs/{id}/events` channel for live progress.** Client gets both durability and live updates.

**Code:**
```python
@app.post("/v1/agent/runs", status_code=status.HTTP_202_ACCEPTED)
async def start_run(body: RunIn, db: DB, response: Response) -> RunAccepted:
    run_id = uuid.uuid4()
    await db.execute(insert(Run).values(id=run_id, status="queued", input=body.model_dump()))
    await db.commit()
    await arq_pool.enqueue_job("execute_agent_run", str(run_id))
    response.headers["Location"] = f"/v1/agent/runs/{run_id}"
    return RunAccepted(run_id=run_id, status="queued", poll_after_ms=2000)

# RunStatus is a pydantic model with model_config = ConfigDict(from_attributes=True),
# so the ORM Run instance is validated/filtered into it on the way out.
@app.get("/v1/agent/runs/{run_id}", response_model=RunStatus)
async def get_run(run_id: UUID, db: DB) -> Run:
    run = await db.get(Run, run_id)
    if run is None:
        raise NotFound(f"run {run_id}")
    return run
```

**Gotcha:** always return a `poll_after`/`Retry-After` hint, otherwise clients hammer you at 10 req/s. And make the job row the source of truth — Redis alone loses state on eviction.

---

### Q29. How do you set timeouts and retries against the LLM upstream?
`[HARD]`

**Answer:** Three layers, each with a budget smaller than the one outside it: **client → your API (gateway timeout) → LLM SDK timeout → per-attempt connect timeout**.

**Code:**
```python
import httpx
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError

client = AsyncOpenAI(
    timeout=httpx.Timeout(60.0, connect=5.0, read=60.0, write=10.0),
    max_retries=2,          # SDK retries 408/409/429/5xx with exponential backoff + jitter
)

async def answer(prompt: str) -> str:
    try:
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0,                    # per-request override
        )
        return r.choices[0].message.content
    except RateLimitError as e:
        raise QuotaExceeded("LLM quota exceeded, retry shortly") from e
    except (APITimeoutError, APIConnectionError) as e:
        raise UpstreamLLMError("LLM unavailable") from e
```

Rules to say out loud:
- **Never retry a non-idempotent streaming call** that already emitted tokens.
- Retry only on 408/429/5xx/connection errors; never on 400/401/403/422.
- Use **exponential backoff with full jitter**; honour `Retry-After` on 429.
- Add a **circuit breaker** (e.g. `purgatory` / hand-rolled: open after 5 consecutive failures, half-open after 30 s) so you fail fast instead of queueing 10k requests behind a dead upstream.
- Set an overall **request budget** — if 25 s of a 30 s budget is spent, don't start another retry; degrade (return cached/RAG-only answer).

---

### Q30. Implement idempotency keys.
`[HARD]`

**Answer:** Client sends `Idempotency-Key: <uuid>`. Server atomically claims the key in Redis (`SET key ... NX EX 86400`). First caller executes and stores the response; concurrent duplicates get 409 (in-progress); later duplicates get the **stored response replayed**.

**Code:**
```python
import hashlib
import json
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

IDEM_TTL = 24 * 3600


@dataclass
class Idem:
    key: str | None = None        # Redis key we claimed; None -> no idempotency requested
    fingerprint: str | None = None
    replay: dict | None = None    # a previously stored response, to return verbatim


async def idempotent(
    request: Request,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Idem:
    if idempotency_key is None:
        return Idem()
    body = await request.body()   # Starlette caches the body, so the route can still parse it
    fingerprint = hashlib.sha256(body).hexdigest()
    r = request.app.state.redis
    key = f"idem:{idempotency_key}"
    claimed = await r.set(key, json.dumps({"state": "in_progress", "fp": fingerprint}),
                          nx=True, ex=IDEM_TTL)
    if claimed:
        return Idem(key=key, fingerprint=fingerprint)

    raw = await r.get(key)
    if raw is None:               # expired between SET NX and GET -> treat as a fresh request
        return Idem(key=key, fingerprint=fingerprint)
    stored = json.loads(raw)
    if stored["fp"] != fingerprint:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Idempotency-Key reused with a different body")
    if stored["state"] == "in_progress":
        raise HTTPException(status.HTTP_409_CONFLICT, "request already in progress",
                            headers={"Retry-After": "2"})
    return Idem(key=key, fingerprint=fingerprint, replay=stored["response"])


@app.post("/v1/agent/runs")
async def create_run(body: RunIn, request: Request,
                     idem: Annotated[Idem, Depends(idempotent)]) -> dict:
    if idem.replay is not None:
        return idem.replay                       # <- the actual replay path
    result = await svc.create_run(body)
    if idem.key:
        await request.app.state.redis.set(
            idem.key,
            json.dumps({"state": "done", "fp": idem.fingerprint, "response": result}),
            ex=IDEM_TTL,
        )
    return result
```

**Two details a senior interviewer probes for:** (1) if the handler **fails**, you must delete the `in_progress` claim (or store the error), otherwise a genuine retry is locked out for 24 h — do it in a `try/except` around `svc.create_run`; (2) the stored response must be JSON-serialisable, so store the already-serialised body, not an ORM object.

**Why it matters for GenAI:** a retried `POST /chat` without idempotency = paying twice for the same completion and double-writing to your vector store.

---

## 6. Databases & SQLAlchemy 2.0 Async

### Q31. Set up SQLAlchemy 2.0 async with FastAPI. Session per request — why?
`[MEDIUM]`

**Answer:** One `AsyncEngine` per process (holds the connection pool), one `AsyncSession` **per request** (holds the unit of work / identity map). Sharing a session across requests corrupts the identity map and breaks transaction isolation; `AsyncSession` is not concurrency-safe.

**Code:**
```python
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pw@db:5432/app",
    pool_size=10,          # persistent connections per worker
    max_overflow=20,       # burst
    pool_timeout=30,       # wait before raising TimeoutError
    pool_recycle=1800,     # recycle before the DB/proxy kills idle conns
    pool_pre_ping=True,    # cheap SELECT 1 to avoid stale-connection errors
    echo=False,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

DB = Annotated[AsyncSession, Depends(get_db)]
```

**Pool sizing math:** `workers × (pool_size + max_overflow)` must stay under Postgres `max_connections` (default 100). 4 workers × (10+20) = 120 → **you will exhaust the DB**. Either drop to `pool_size=5, max_overflow=5` (4 × 10 = 40 connections, comfortable), or put **PgBouncer** in transaction mode in front (then set `poolclass=NullPool` on the app side **and** disable asyncpg's prepared-statement cache — `create_async_engine(url, poolclass=NullPool, connect_args={"statement_cache_size": 0})` — otherwise you get `DuplicatePreparedStatementError` as PgBouncer reuses backends).

**Gotcha:** `expire_on_commit=False` is near-mandatory in async — otherwise attribute access after commit triggers a lazy refresh, which in async raises `MissingGreenlet`.

---

### Q32. What is the N+1 problem and how do you fix it in SQLAlchemy 2.0?
`[MEDIUM]`

**Answer:** Fetching N parents then lazily loading each parent's children = 1 + N queries. In **async** SQLAlchemy, lazy loading doesn't just get slow, it **raises `MissingGreenlet`** — async forces you to be explicit.

**Code:**
```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

# BAD: 1 + N (and blows up in async)
docs = (await db.scalars(select(Document))).all()
for d in docs:
    print(d.chunks)        # lazy load per doc

# GOOD: one-to-many -> selectinload => 2 queries (SELECT ... WHERE id IN (...))
stmt = select(Document).options(selectinload(Document.chunks)).limit(50)

# GOOD: many-to-one / one-to-one -> joinedload => 1 query with a LEFT JOIN
stmt = select(Chunk).options(joinedload(Chunk.document)).where(Chunk.id.in_(ids))

docs = (await db.scalars(stmt)).unique().all()
```

| Strategy | SQL | Best for |
|---|---|---|
| `selectinload` | 2 queries, `IN (...)` | collections (one-to-many, many-to-many) — no row explosion |
| `joinedload` | 1 query, LEFT JOIN | many-to-one / one-to-one |
| `subqueryload` | 2 queries w/ subquery | legacy; prefer `selectinload` |
| `raiseload("*")` | raises on any lazy access | **use in tests** to catch N+1 before prod |

**Gotcha:** `joinedload` on a collection multiplies rows (10 docs × 100 chunks = 1000 rows) and breaks `LIMIT` — that is exactly when you need `selectinload`. Also remember `.unique()` is required on scalars results when `joinedload` targets a collection.

---

### Q33. Where do transactions belong, and how do you avoid holding one across an LLM call?
`[HARD]`

**Answer:** Transaction boundary = the **use case**, not the request. The killer anti-pattern in GenAI services is:

```python
# ANTI-PATTERN: DB transaction held open for 8 seconds
async with db.begin():
    doc = await db.get(Document, doc_id)
    summary = await llm.summarize(doc.text)   # 8 s of network wait, row locks held
    doc.summary = summary
```
This pins a pooled connection and holds row locks for the whole LLM round trip → pool exhaustion under load and lock contention.

**Fix — read, commit, call, then write:**
```python
async with SessionLocal() as s:                  # tx 1: read
    text = (await s.get(Document, doc_id)).text

summary = await llm.summarize(text)              # no DB connection held

async with SessionLocal() as s:                  # tx 2: write (optimistic concurrency)
    await s.execute(
        update(Document)
        .where(Document.id == doc_id, Document.version == version)
        .values(summary=summary, version=Document.version + 1)
    )
    await s.commit()
```

**Follow-up:** *"What if you must be atomic?"* — Use the **outbox pattern**: commit the domain change + an outbox row in one transaction, and let a worker do the LLM call and follow-up write.

---

### Q34. How do you paginate, and why is offset pagination bad at scale?
`[MEDIUM]`

**Answer:** `OFFSET 100000` makes Postgres scan and discard 100k rows — latency grows linearly, and rows inserted mid-scroll cause duplicates/skips. Use **keyset (cursor) pagination** on a stable, indexed, unique sort key.

**Code:**
```python
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import select, tuple_

class Page(BaseModel):
    items: list[DocumentOut]
    next_cursor: str | None = None

@app.get("/v1/documents", response_model=Page)
async def list_docs(
    db: DB,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> Page:
    stmt = select(Document).order_by(Document.created_at.desc(), Document.id.desc()).limit(limit + 1)
    if cursor:
        ts, last_id = urlsafe_b64decode(cursor).decode().split("|")
        stmt = stmt.where(
            tuple_(Document.created_at, Document.id) < (datetime.fromisoformat(ts), int(last_id))
        )
    rows = (await db.scalars(stmt)).all()
    has_more, rows = len(rows) > limit, rows[:limit]
    nxt = (urlsafe_b64encode(f"{rows[-1].created_at.isoformat()}|{rows[-1].id}".encode()).decode()
           if has_more and rows else None)
    return Page(items=rows, next_cursor=nxt)
```

Index needed: `CREATE INDEX ON documents (created_at DESC, id DESC);`
Use offset pagination only when the UI genuinely needs "page 7 of 40" and the table is small.

---

## 7. Auth & Security

### Q35. Implement OAuth2 password flow + JWT in FastAPI.
`[HARD]`

**Answer:** `OAuth2PasswordBearer` extracts the `Authorization: Bearer <token>` header and wires the "Authorize" button into Swagger. `OAuth2PasswordRequestForm` parses the `username`/`password` form body at the token endpoint.

**Code (PyJWT — the maintained choice; `python-jose` is the older one you'll see in FastAPI docs):**
```python
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

import jwt                              # PyJWT
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

SECRET = settings.jwt_secret.get_secret_value()
ALGO = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")


def make_token(sub: str, ttl: timedelta, typ: str, scopes: list[str] | None = None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": sub, "iat": now, "exp": now + ttl, "typ": typ,
         "jti": uuid4().hex, "scopes": scopes or []},
        SECRET, algorithm=ALGO,
    )


@app.post("/v1/auth/token")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> dict:
    user = await db.scalar(select(User).where(User.email == form.username))
    if user is None or not pwd.verify(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return {
        "access_token": make_token(str(user.id), ACCESS_TTL, "access", user.scopes),
        "refresh_token": make_token(str(user.id), REFRESH_TTL, "refresh"),
        "token_type": "bearer",
        "expires_in": int(ACCESS_TTL.total_seconds()),
    }


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    creds_exc = HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials",
                              headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(
            token, SECRET, algorithms=[ALGO],          # ALWAYS pin the algorithm list
            options={"require": ["exp", "sub", "typ", "jti"]},   # incl. jti: read below
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired",
                            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})
    except jwt.InvalidTokenError:
        raise creds_exc
    if payload["typ"] != "access":                     # refresh token must not access resources
        raise creds_exc
    if await db.scalar(select(RevokedJTI).where(RevokedJTI.jti == payload["jti"])):
        raise creds_exc
    user = await db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise creds_exc
    return user
```

**Gotcha (say this — it's a classic security question):** never call `jwt.decode(token, options={"verify_signature": False})` in the auth path, and never let the token's own `alg` header pick the algorithm — that is the **`alg: none` / HS256-vs-RS256 confusion attack**. Always pass an explicit `algorithms=[...]` allowlist.

**Note:** `passlib` 1.7.4 emits a spurious `AttributeError: module 'bcrypt' has no attribute '__about__'` warning with `bcrypt>=4.1`; pin `bcrypt<4.1`, or use `pwdlib[argon2]`/the `bcrypt` package directly. passlib is effectively unmaintained — **`pwdlib` with Argon2id is the modern recommendation** for new services. Also know that **bcrypt silently truncates the password at 72 bytes** (pre-hash with SHA-256 if you allow long passphrases); Argon2id has no such limit.

**Note:** `from datetime import UTC` requires **Python 3.11+**; on 3.10 use `from datetime import timezone` and `datetime.now(timezone.utc)`. PyJWT converts `datetime` values for the `exp`/`iat`/`nbf` claims to numeric timestamps for you — other claims must already be JSON types.

**Scaling note they may push on:** HS256 means every service that validates the token holds the signing secret, so any one of them can *mint* tokens. Once more than one service verifies, move to **RS256/EdDSA** — the issuer holds the private key, verifiers fetch public keys from a JWKS endpoint and select by the token's `kid`. That also makes key rotation possible without a synchronised deploy.

---

### Q36. Refresh tokens — how do you do them safely?
`[MEDIUM]`

**Answer:** Short-lived access token (5–15 min, stateless JWT) + long-lived refresh token (7–30 days, **stored server-side** so it can be revoked). On refresh: verify → **rotate** (issue a new refresh token, invalidate the old one) → detect reuse.

**Reuse detection:** if a refresh token that was already rotated is presented again, it means it was stolen → **revoke the whole token family** for that user and force re-login.

Storage: refresh token in an `HttpOnly; Secure; SameSite=Strict` cookie (browser); access token in memory only. Never put either in `localStorage` — XSS reads it instantly.

```python
import hashlib
from datetime import UTC, datetime

@app.post("/v1/auth/refresh")
async def refresh(payload: RefreshIn, db: DB) -> dict:
    digest = hashlib.sha256(payload.token.encode()).hexdigest()   # store hashes, never raw tokens
    row = await db.scalar(select(RefreshToken).where(RefreshToken.hash == digest))
    if row is None:
        raise HTTPException(401, "invalid refresh token")
    if row.used_at is not None:                       # replay -> compromised
        await db.execute(update(RefreshToken)
                         .where(RefreshToken.family_id == row.family_id)
                         .values(revoked=True))
        await db.commit()
        raise HTTPException(401, "token reuse detected; please log in again")
    row.used_at = datetime.now(UTC)
    ...
```

---

### Q37. API-key auth for service-to-service — how, and what are the pitfalls?
`[MEDIUM]`

**Answer:**
```python
import hashlib, hmac, secrets
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def issue_key() -> tuple[str, str]:
    raw = "sk_live_" + secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()      # store the HASH only

async def verify_api_key(
    key: Annotated[str | None, Depends(api_key_header)], db: DB
) -> ApiClient:
    if not key:
        raise HTTPException(401, "missing X-API-Key")
    digest = hashlib.sha256(key.encode()).hexdigest()
    client = await db.scalar(select(ApiClient).where(ApiClient.key_hash == digest))
    if client is None or client.revoked:
        raise HTTPException(401, "invalid api key")
    return client
```

Pitfalls: store **hashes, not keys**; use `secrets`, never `random`; use `hmac.compare_digest` for any in-code comparison (timing attacks); prefix keys (`sk_live_`) so scanners can detect leaks; support **two active keys** per client so rotation is zero-downtime; never accept the key in a query string (it lands in access logs).

---

### Q38. Rate limiting a GenAI endpoint — design it.
`[HARD]`

**Answer:** Two dimensions: **requests/min** (abuse control) and **tokens/min or cost/day** (the one that actually protects your budget). Limits must be enforced in **Redis** — in-memory limits are per worker and therefore wrong by a factor of N.

**Code (slowapi for the simple case):**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://cache:6379")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/chat")
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatIn):   # `request: Request` is REQUIRED by slowapi
    ...
```

**Code (token-budget limiter — the GenAI-specific answer):**
```python
import time
from fastapi import HTTPException

# Atomic check-and-increment: the whole script runs as one Redis command,
# so two workers cannot both pass the budget check.
LUA = """
local used = tonumber(redis.call('GET', KEYS[1]) or '0')
if used + tonumber(ARGV[1]) > tonumber(ARGV[2]) then return -1 end
redis.call('INCRBY', KEYS[1], ARGV[1])
redis.call('EXPIRE', KEYS[1], ARGV[3], 'NX')
return used + tonumber(ARGV[1])
"""

async def reserve_tokens(redis, tenant: str, est_tokens: int, budget: int = 200_000) -> None:
    key = f"tpm:{tenant}:{int(time.time() // 60)}"     # fixed 1-minute window
    used = await redis.eval(LUA, 1, key, est_tokens, budget, 120)
    if used == -1:
        raise HTTPException(429, "token budget exceeded",
                            headers={"Retry-After": "60"})
```
**Version gotcha:** the `NX` flag on `EXPIRE` requires **Redis ≥ 7.0**. On 6.x drop it and use `redis.call('EXPIRE', KEYS[1], ARGV[3])` unconditionally (harmless — it just re-arms the TTL on a key that is rewritten every minute anyway), or `SET`+`TTL`-check.

Reserve on the estimate before the call, then **reconcile** with the real `response.usage.total_tokens` afterwards (`INCRBY` the delta, which may be negative). Estimate input tokens with `tiktoken` (`tiktoken.encoding_for_model(...)`, falling back to `tiktoken.get_encoding("o200k_base")` for models it doesn't know) and assume worst-case `max_tokens` for the output.

Always return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` and `Retry-After`. Algorithms: fixed window (simple, boundary-burst bug), **sliding window** (good default), **token bucket** (allows bursts — best for chat UX).

---

### Q39. What are the top security controls for a production FastAPI GenAI service?
`[MEDIUM]`

**Answer:**
1. **TLS terminated at the LB**; app behind it with `--proxy-headers` and trusted-proxy IPs set (otherwise `request.client.host` is your LB, and IP rate limiting is useless).
2. `TrustedHostMiddleware(allowed_hosts=[...])` — blocks Host-header injection.
3. **Secrets from env / Key Vault**, never in code; `SecretStr` in settings so they never print in logs or tracebacks.
4. Disable `/docs`, `/redoc`, `/openapi.json` in prod, or gate them behind auth: `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`.
5. **Body size limits** at ingress (`client_max_body_size 25m`) — FastAPI has no built-in cap.
6. Security headers: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy`.
7. **Never echo `str(exc)`** to the client — a stack trace can leak prompts, connection strings, and customer data.
8. **GenAI-specific:** prompt-injection defence on retrieved content, PII redaction before sending to the LLM, output filtering, per-tenant data isolation in the vector store (filter by `tenant_id`, never rely on the prompt), and **log prompts with redaction + a retention policy** — raw prompt logs are a GDPR/DPDP liability.

---

### Q40. How do you prevent a slow/abusive client from exhausting your server?
`[MEDIUM]`

**Answer:**
- **Concurrency cap per tenant** with an `asyncio.Semaphore` (or Redis counter across workers) so one tenant can't hold every in-flight LLM slot.
- **Global timeout middleware**: wrap the handler in `asyncio.timeout(...)` and return 504.
- Cap `max_tokens` server-side; never let the client pass an unbounded value.
- Cap input length in the pydantic model (`Field(max_length=8000)`) — cheap rejection before the model call.
- Reject on `Content-Length` at the edge; slowloris protection at the LB (uvicorn is not a hardened edge server — always put nginx/ALB in front).

```python
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def timeout_mw(request: Request, call_next):
    try:
        async with asyncio.timeout(30):        # Python 3.11+
            return await call_next(request)
    except TimeoutError:
        return JSONResponse({"error": {"code": "timeout"}}, status_code=504)
```
**Gotcha:** exclude streaming routes from this middleware — a legitimate SSE stream lasts minutes. And be precise about what this actually bounds: because this is a `BaseHTTPMiddleware`, `call_next` returns as soon as the **response headers** are ready, so for a `StreamingResponse` the timeout covers only the time to first byte, not the body. To bound a whole stream, put the budget inside the generator (`asyncio.timeout` around the token loop) or at the LB.

---

## 8. Production Hardening

### Q41. Liveness vs readiness probes — what goes in each?
`[EASY]`

**Answer:** **Liveness** = "is the process wedged? restart me." Must check **nothing external** — otherwise a Redis blip restarts every pod and turns a degradation into an outage. **Readiness** = "can I serve traffic right now?" Checks dependencies; failing it pulls the pod out of the LB without killing it.

```python
import asyncio
from collections.abc import Callable, Coroutine

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

@app.get("/healthz", include_in_schema=False)
async def liveness() -> dict:
    return {"status": "ok"}                  # no I/O, no DB

async def _db_ping(app) -> None:
    # `async with` is essential: awaiting engine.connect() alone checks a connection
    # OUT of the pool and never returns it -> the probe itself exhausts the pool.
    async with app.state.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

@app.get("/readyz", include_in_schema=False)
async def readiness(request: Request) -> JSONResponse:
    checks: dict[str, str] = {}

    # take FACTORIES, not pre-created coroutines, so nothing is left un-awaited on timeout
    async def probe(name: str, make: Callable[[], Coroutine]) -> None:
        try:
            async with asyncio.timeout(2):
                await make()
            checks[name] = "ok"
        except Exception as e:
            checks[name] = f"fail: {type(e).__name__}"

    app_ = request.app
    await asyncio.gather(
        probe("db", lambda: _db_ping(app_)),
        probe("redis", lambda: app_.state.redis.ping()),
        probe("vectordb", lambda: app_.state.retriever.ping()),
    )
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse({"ready": ok, "checks": checks}, status_code=200 if ok else 503)
```
Add a **startup probe** in K8s for slow-loading models so liveness doesn't kill the pod during warm-up.

---

### Q42. How does graceful shutdown work, and what breaks streaming during a deploy?
`[MEDIUM]`

**Answer:** On `SIGTERM`, uvicorn stops accepting new connections, waits for in-flight requests up to `--timeout-graceful-shutdown`, runs the lifespan shutdown, then exits. In K8s, add `terminationGracePeriodSeconds` **greater** than that, plus a `preStop` sleep (~5 s) so the endpoints controller removes the pod from the Service before it stops accepting.

Budget for a GenAI service: a streaming response can run 60–120 s → `--timeout-graceful-shutdown 90`, `terminationGracePeriodSeconds: 120`.

**Gotcha:** long SSE connections will still be cut on deploy. Mitigations: emit a `event: reconnect` frame and have the client resume with `Last-Event-ID`; or persist the run server-side (202 + polling pattern) so the client can re-attach.

---

### Q43. Structured logging with request correlation — show the setup.
`[MEDIUM]`

**Answer:** JSON logs + a `contextvar` request id injected by middleware, so every log line inside a request (including deep in your RAG service) carries the same `request_id`, `tenant_id`, and `trace_id`.

**Code:**
```python
import json, logging, sys
from contextvars import ContextVar

log = logging.getLogger(__name__)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        payload |= getattr(record, "extra_fields", {})
        return json.dumps(payload, default=str)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(handlers=[handler], level=logging.INFO, force=True)

log.info("llm_call", extra={"extra_fields": {
    "model": "gpt-4o-mini", "prompt_tokens": 812,
    "completion_tokens": 190, "latency_ms": 1430, "cost_usd": 0.00023,
}})
```

For GenAI specifically, log per call: `model`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `cost_usd`, `retrieved_doc_ids`, `cache_hit`, `finish_reason`. **Do not** log raw prompts/completions unredacted. Use `structlog` in real projects; OpenTelemetry (`opentelemetry-instrumentation-fastapi`) for traces.

---

### Q44. Which metrics do you expose for a GenAI API?
`[MEDIUM]`

**Answer:** RED metrics plus LLM-specific ones. `prometheus-fastapi-instrumentator` gives you the HTTP layer in three lines.

| Metric | Type | Why |
|---|---|---|
| `http_requests_total{route,status}` | counter | Rate + Errors |
| `http_request_duration_seconds` | histogram | p50/p95/p99 — **never average latency** |
| `llm_time_to_first_token_seconds` | histogram | the number users actually feel in chat |
| `llm_tokens_total{direction,model}` | counter | cost attribution |
| `llm_cost_usd_total{tenant}` | counter | budget alerts |
| `llm_errors_total{type}` | counter | 429 vs timeout vs 5xx |
| `retrieval_latency_seconds` / `retrieval_hits` | histogram/counter | RAG health |
| `inflight_requests` | gauge | saturation |
| `db_pool_checked_out` | gauge | pool exhaustion early warning |

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```

---

### Q45. How do you customise the OpenAPI schema?
`[EASY]`

**Answer:**
```python
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="GenAI Platform API",
    version="1.4.0",
    description="RAG + agent orchestration",
    docs_url=None if settings.env == "prod" else "/docs",
    openapi_url=None if settings.env == "prod" else "/openapi.json",
    servers=[{"url": "https://api.acme.com", "description": "prod"}],
)

def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    # `components` is absent when no route declares a model/security scheme -> setdefault,
    # never `schema["components"][...] = ...` (that is a KeyError waiting to happen).
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
```
Per-route: `@app.get(..., summary=..., description=..., response_description=..., tags=["chat"], deprecated=True, responses={429: {"model": ErrorOut}}, operation_id="chat_create")`. Set stable `operation_id`s if clients are generated from the spec.

---

### Q46. What breaks when you scale from 1 to N replicas?
`[HARD]`

**Answer:** Anything held in process memory becomes wrong:

| In-memory thing | Breaks how | Fix |
|---|---|---|
| Rate-limit counters | limit becomes N× the intended value | Redis |
| WebSocket connection registry | broadcast reaches 1/N clients | Redis pub/sub |
| Conversation / agent memory dict | user hits a different pod, context is gone | Redis / Postgres checkpointer |
| Response / embedding cache | low hit rate, N× cost | shared Redis cache |
| Background `asyncio.create_task` | lost on any pod restart | durable queue (ARQ/Celery) |
| `lru_cache` on user permissions | stale after a revoke | short TTL + explicit invalidation |
| Scheduled/cron code in the app | runs N times | leader election, K8s CronJob, or a lock |
| Local file uploads | next request lands elsewhere | S3/Blob storage |

**LangGraph note:** the memory-saver checkpointer is per process. Use a Postgres/Redis checkpointer so an agent run can resume on any replica.

---

### Q47. Caching for a RAG/LLM API — what do you cache and where?
`[MEDIUM]`

**Answer:** Three layers with very different hit rates. The numbers below are **rough orders of magnitude from typical assistant traffic, not benchmarks** — quote them as "in my experience, roughly", never as measured fact:

| Layer | Key | TTL | Rough hit rate |
|---|---|---|---|
| **Exact response cache** | `sha256(normalised_prompt + model + params)` | 1–24 h | 5–20% |
| **Semantic cache** | embedding of query, cosine ≥ 0.95 vs cached queries | hours | 15–40% on FAQ traffic |
| **Embedding cache** | `sha256(chunk_text + embed_model)` | permanent | very high on re-ingest |
| **Provider prompt cache** | long stable system prefix | provider-managed | big cost cut on long system prompts |
| **Retrieval cache** | `sha256(query + filters + k)` | minutes | medium |

Rules: never cache across tenants (key must include `tenant_id`); never cache when `temperature > 0` unless the product tolerates repeats; always emit `X-Cache: HIT|MISS` for debuggability; invalidate the retrieval cache on re-ingest.

---

## 9. Testing, Config & Observability

### Q48. How do you test a FastAPI app — sync and async?
`[MEDIUM]`

**Answer:** `TestClient` (sync, wraps httpx, runs the ASGI app in a portal) for most tests. `httpx.AsyncClient` + `ASGITransport` when the test itself must await things (async fixtures, async DB assertions).

**Code:**
```python
# --- sync ---
from fastapi.testclient import TestClient

def test_health():
    with TestClient(app) as client:            # `with` triggers lifespan startup/shutdown
        assert client.get("/healthz").json() == {"status": "ok"}

# --- async ---
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager      # ASGITransport does NOT run lifespan
from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture                        # NOT @pytest.fixture, unless asyncio_mode=auto
async def client():
    app.dependency_overrides[get_current_user] = lambda: User(id=1, role="admin")
    app.dependency_overrides[get_llm] = lambda: FakeLLM(tokens=["Hel", "lo"])
    async with LifespanManager(app):           # populates app.state.*
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_chat_stream(client):
    async with client.stream("POST", "/v1/chat/stream", json={"prompt": "hi"}) as r:
        assert r.status_code == 200
        chunks = [c async for c in r.aiter_text()]
    assert "Hello" in "".join(chunks)
```

**Why `dependency_overrides` and not `monkeypatch.setattr("app.deps.get_llm", ...)`:** FastAPI resolves the dependency graph at **route-registration time** and stores a reference to the original function object. Rebinding the module attribute afterwards changes nothing — the route still calls the object it captured. `dependency_overrides` is keyed on that exact object, which is why it is the only reliable hook.

Points to make: use `dependency_overrides` for the LLM and DB (never hit OpenAI in CI — it's slow, flaky and costs money); use **testcontainers** or a transactional-rollback fixture for the DB; **record/replay** (VCR-style) for a small set of golden LLM interactions; assert on structure, not exact model wording — LLM outputs are non-deterministic even at `temperature=0`.

**Gotcha:** plain `TestClient(app)` without the `with` block **does not run lifespan**, so `app.state.redis` is missing and you get confusing `AttributeError`s. The same is true of `httpx.AsyncClient(transport=ASGITransport(app=app))` — `ASGITransport` only speaks the `http` scope and never sends `lifespan`, so wrap it in `asgi_lifespan.LifespanManager` (or set `app.state.*` by hand in the fixture).

---

### Q49. Configuration with pydantic-settings.
`[EASY]`

**Answer:**
```python
from functools import lru_cache
from typing import Annotated, Literal
from fastapi import Depends
from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        env_prefix="APP_", extra="ignore", case_sensitive=False,
    )
    env: Literal["local", "dev", "staging", "prod"] = "local"
    database_url: PostgresDsn
    redis_url: RedisDsn
    openai_api_key: SecretStr
    azure_openai_endpoint: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_s: float = Field(default=60.0, gt=0)
    max_output_tokens: int = Field(default=1024, ge=1, le=8192)


@lru_cache
def get_settings() -> Settings:
    return Settings()          # fails fast at startup if a required env var is missing

SettingsDep = Annotated[Settings, Depends(get_settings)]
```
Env var `APP_OPENAI_API_KEY` maps to `openai_api_key`. `SecretStr` prints as `**********` in logs and reprs — call `.get_secret_value()` only at the point of use. Nested config uses `env_nested_delimiter="__"`.

**Gotcha:** in pydantic v2, `PostgresDsn`/`RedisDsn` validate to URL objects, not `str`. `create_async_engine(settings.database_url)` fails — pass `str(settings.database_url)`. (`pydantic-settings` is a **separate package** from pydantic v2; `from pydantic import BaseSettings` is v1 and now raises a helpful error telling you to install `pydantic-settings`.)

---

### Q50. What does "12-factor" mean for this service, concretely?
`[EASY]`

**Answer:** Config in env (not files baked into the image); logs to stdout (the platform ships them, you don't write files); stateless processes (state in Postgres/Redis/S3); explicit dependencies (`uv`/`poetry` lockfile pinned in the image); dev/prod parity (same image, different env); disposability (fast startup, graceful SIGTERM); admin tasks as one-off processes (migrations as a K8s Job, not in lifespan); port binding (the app *is* the server, no external web server required in the container).

---

### Q51. Sketch the project layout you'd use.
`[EASY]`

**Answer:**
```
app/
  main.py                 # FastAPI(), lifespan, middleware, include_router
  core/
    config.py             # pydantic-settings
    logging.py            # JSON formatter + request-id contextvar
    security.py           # jwt encode/verify, password hashing
    errors.py             # AppError hierarchy + handlers
  api/
    deps.py               # DB, CurrentUser, LLM, Retriever Annotated aliases
    v1/
      __init__.py         # v1 APIRouter aggregation
      chat.py  documents.py  agents.py  health.py
  schemas/                # pydantic request/response models (the API contract)
  models/                 # SQLAlchemy ORM models
  services/               # business logic — NO fastapi imports here
    rag.py  agent.py  llm_client.py
  workers/                # ARQ/Celery tasks
  db/
    session.py  migrations/   # alembic
tests/
  conftest.py  test_chat.py  test_rag.py
Dockerfile  pyproject.toml
```
**The rule to state:** `services/` must not import `fastapi`. That keeps business logic testable without HTTP and reusable from a CLI, a worker, or an MCP server.

---

## 10. Flask

### Q52. What is the app factory pattern and why does it matter?
`[MEDIUM]`

**Answer:** A `create_app(config)` function that builds and returns the app instead of a module-level global. It lets you instantiate multiple configured apps (test vs prod), avoids circular imports, and defers extension binding via `ext.init_app(app)`.

**Code:**
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()           # created unbound at import time

def create_app(config_object: str = "config.Production") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    db.init_app(app)                              # bound here
    from .api.chat import bp as chat_bp
    from .api.docs import bp as docs_bp
    app.register_blueprint(chat_bp, url_prefix="/v1/chat")
    app.register_blueprint(docs_bp, url_prefix="/v1/docs")

    @app.errorhandler(404)
    def not_found(e): return {"error": "not_found"}, 404
    return app
```
Run with `gunicorn "app:create_app()"`.

---

### Q53. Explain Flask's `g`, `current_app`, `request` and context locals.
`[HARD]`

**Answer:** They are `LocalProxy` objects backed by Werkzeug's context-local storage (built on `contextvars` since Flask 2.0). Flask pushes an **application context** and a **request context** per request; the proxies resolve to whatever is on top of the current stack.

| Object | Context | Lifetime | Use for |
|---|---|---|---|
| `request` | request ctx | one request | incoming data |
| `session` | request ctx | one request (cookie-backed) | user session |
| `g` | **app ctx** | one request in practice | per-request scratch: DB conn, current user, request id |
| `current_app` | app ctx | as long as the ctx is pushed | config, logger, extensions |

**Code:**
```python
from flask import Flask, current_app, g

def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_URL"])
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

**Gotcha:** `g` is **not** a global cache across requests — it is wiped every request. And "Working outside of application context" in a background thread/Celery task is fixed with `with app.app_context():`, which is why the factory returning `app` matters.

---

### Q54. Does Flask support async? What actually happens?
`[HARD]`

**Answer:** Yes since Flask 2.0 (`pip install "flask[async]"`), and it is **mostly a convenience, not a concurrency win**. Flask wraps the coroutine with `asgiref.sync.async_to_sync`, spins up an event loop, runs the coroutine to completion, and returns — all while **still occupying the WSGI worker thread**.

```python
@app.get("/ask")
async def ask():
    async with httpx.AsyncClient() as c:            # a new loop per request
        r = await c.post(LLM_URL, json={...})
    return r.json()
```

Consequences: no gain in requests-per-worker; you cannot keep background tasks alive after the response (the loop is torn down); no WebSockets. If your workload is LLM-heavy async I/O, **use FastAPI/Quart, or run Flask behind an ASGI adapter (`asgiref.wsgi.WsgiToAsgi`) knowing it doesn't make the views async.**

---

### Q55. How do you tune gunicorn for a Flask API that calls an LLM?
`[MEDIUM]`

**Answer:** Because each request blocks a thread for seconds, you need many concurrent slots per core.

```bash
# threaded workers: concurrency = workers x threads = 4 x 16 = 64 in-flight
gunicorn "app:create_app()" -w 4 -k gthread --threads 16 \
  --timeout 120 --graceful-timeout 30 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 100 --access-logfile -

# or gevent (monkey-patches sockets -> thousands of green threads)
gunicorn "app:create_app()" -w 4 -k gevent --worker-connections 500
```

| Worker class | Concurrency | Notes |
|---|---|---|
| `sync` (default) | 1 req/worker | never for LLM calls — one slow call = one dead worker |
| `gthread` | threads/worker | safe default for blocking I/O |
| `gevent`/`eventlet` | thousands | must monkey-patch early; breaks C libs that block outside sockets |
| `uvicorn` worker | async | only for ASGI apps (FastAPI/Quart), not Flask |

`--timeout` must exceed your slowest LLM call or gunicorn SIGKILLs the worker mid-response. `--max-requests` recycles workers to bound memory leaks.

---

### Q56. When would you still pick Flask in 2026?
`[EASY]`

**Answer:** Existing Flask codebase/team; a tiny internal service or webhook receiver; heavy reliance on a Flask-only extension; server-rendered Jinja pages where async buys nothing; or an ML team that already has Flask + gunicorn in their deployment templates and the service is one blocking `predict()` call. For anything with streaming, WebSockets, high-concurrency LLM calls, or an OpenAPI contract, **FastAPI is strictly better** — say that plainly.

---

## 11. Django & DRF

### Q57. DRF serializers vs pydantic models — compare honestly.
`[MEDIUM]`

**Answer:**

| | DRF `Serializer` | pydantic v2 |
|---|---|---|
| Primary job | validate **and** map to/from ORM instances | validate/parse arbitrary Python data |
| Speed | pure Python | Rust core, ~5–50× faster |
| ORM integration | `ModelSerializer` auto-generates fields from the model | none (you write `from_attributes=True`) |
| Nested writes | supported (fiddly) | you write it explicitly |
| Type hints / IDE | weak (fields are class attrs) | strong — real types, `mypy` works |
| OpenAPI | via `drf-spectacular` | native in FastAPI |
| Async | sync-first | agnostic |

```python
# DRF
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "content", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_title(self, value):
        if len(value) < 3: raise serializers.ValidationError("too short")
        return value

# pydantic v2 equivalent
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    created_at: datetime
```
One-liner for the interview: *"DRF serializers are an ORM-coupled validation + persistence layer; pydantic is a pure, much faster data-validation layer. DRF does more; pydantic does less, faster, with real types."*

---

### Q58. `select_related` vs `prefetch_related` in Django ORM.
`[MEDIUM]`

**Answer:**

| | `select_related` | `prefetch_related` |
|---|---|---|
| Relations | FK, OneToOne (forward) | M2M, reverse FK, GenericFK |
| SQL | **one query** with SQL `JOIN` | **two queries**, joined in Python |
| Row cost | duplicates parent columns | no duplication |

```python
# N+1: 1 + N queries
for chunk in Chunk.objects.all()[:100]:
    print(chunk.document.title)

# 1 query
Chunk.objects.select_related("document").all()[:100]

# 2 queries, no row explosion
Document.objects.prefetch_related("chunks").all()[:50]

# controlled prefetch
from django.db.models import Prefetch
Document.objects.prefetch_related(
    Prefetch("chunks", queryset=Chunk.objects.filter(active=True).order_by("idx"))
)

# further trimming
Document.objects.only("id", "title")            # SELECT only these columns
Document.objects.defer("content")               # everything except this
Document.objects.values("id", "title")          # dicts, no model instantiation
```
Also mention: querysets are **lazy** and evaluate on iteration/`len()`/`bool()`/slicing-with-step; `.iterator(chunk_size=1000)` for large exports; `annotate`/`aggregate` push work into SQL; `select_for_update()` for row locks; `django-debug-toolbar` or `assertNumQueries` to catch N+1 in tests.

---

### Q59. How does Django middleware work?
`[EASY]`

**Answer:** An ordered list of callables in `settings.MIDDLEWARE`, each wrapping the next — request phase runs **top-down**, response phase **bottom-up**.

```python
class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response          # one-time config at startup

    def __call__(self, request):
        request.id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        response = self.get_response(request)     # everything below runs here
        response["X-Request-Id"] = request.id
        return response
```
Optional hooks: `process_view`, `process_exception`, `process_template_response`. Order matters: `SecurityMiddleware` first; `AuthenticationMiddleware` must come after `SessionMiddleware`; `CommonMiddleware` handles APPEND_SLASH.

---

### Q60. Can Django be async? Where are the sharp edges?
`[HARD]`

**Answer:** Yes — `asgi.py` + uvicorn/daphne, async views since Django 3.1, async ORM methods (`aget`, `acreate`, `asave`, `adelete`, `abulk_create`, `async for`) since 4.1, async signal dispatch (`Signal.asend`) and async auth helpers (`alogin`/`aauthenticate`, 5.0). But:

1. **The ORM is sync underneath.** The `a*` methods wrap sync calls in a threadpool; you're not getting asyncpg-level async.
2. **DRF is sync-first.** Async ViewSet support is partial/recent — don't claim full async DRF.
3. Calling sync ORM code from an async view raises `SynchronousOnlyOperation` → wrap in `sync_to_async(fn, thread_sensitive=True)`.
4. Much of the middleware stack is sync; a sync middleware in an async stack forces a thread hop per request (Django adapts, but you pay for it).
5. **Transactions are the sharp edge.** `transaction.atomic()` is not usable directly from async context — wrap the whole transactional unit in `sync_to_async(...)`. If you're unsure of the exact version state, say *"transactions were still sync-only last I checked"* rather than asserting async `atomic`.

```python
from asgiref.sync import sync_to_async

async def summarize(request, doc_id: int):
    doc = await Document.objects.aget(pk=doc_id)         # 4.1+
    summary = await llm.summarize(doc.content)           # true async
    await sync_to_async(_legacy_audit)(request.user.id)  # sync-only helper
    return JsonResponse({"summary": summary})
```
**Verdict for the interview:** for a *new* streaming GenAI service, FastAPI. To bolt GenAI onto an existing Django product, keep Django for CRUD/admin/auth and add a **separate FastAPI service** for the LLM endpoints, sharing the DB or talking over HTTP.

---

### Q61. How does Celery fit into a Django GenAI stack?
`[MEDIUM]`

**Answer:** Celery runs the long, unreliable, expensive work off the request path: document ingestion, embedding backfills, scheduled re-indexing, batch evaluations.

```python
# proj/celery.py
import os
from celery import Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")
app = Celery("proj")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# rag/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=5, acks_late=True,
             autoretry_for=(TimeoutError, ConnectionError),
             retry_backoff=True, retry_jitter=True, retry_backoff_max=600)
def ingest_document(self, doc_id: int) -> dict:
    doc = Document.objects.get(pk=doc_id)
    chunks = chunk_text(doc.content, size=800, overlap=100)
    vectors = embed(chunks)                       # OpenAI embeddings
    upsert_to_vector_db(doc_id, chunks, vectors)
    Document.objects.filter(pk=doc_id).update(status="indexed")
    return {"chunks": len(chunks)}
```
Things to say: **tasks must be idempotent** (`acks_late=True` means a task can be re-delivered after a crash); pass **IDs, not ORM objects** (payloads are serialised, objects go stale); use separate queues for fast vs slow work; `task_time_limit`/`soft_time_limit` to kill runaway LLM loops; Celery Beat for cron; Flower/Prometheus for visibility. **ARQ** is the lighter asyncio-native alternative when you're not on Django.

---

### Q62. When does Django genuinely win over FastAPI?
`[MEDIUM]`

**Answer:** When the product is bigger than the API. Django wins on: the **admin** (weeks of internal CRUD for free), batteries-included auth/permissions/sessions, **migrations** (Django's are still the best-in-class DX), forms + server-rendered pages, a huge mature ecosystem (allauth, guardian, django-tenants), and enterprise familiarity — many Virtusa-style client estates are already Django + DRF + Celery.

FastAPI wins on: async throughput, streaming/SSE/WebSockets, typed contracts + auto OpenAPI, and microservice-sized footprints.

**The mature answer:** *"Django for the product surface, FastAPI for the AI surface."* One Django app for users/billing/admin; one FastAPI service for chat, RAG and agents; shared Postgres or an internal HTTP contract.

---

## FastAPI vs Flask vs Django for an AI Service

| Dimension | FastAPI | Flask | Django + DRF |
|---|---|---|---|
| Protocol | ASGI (async native) | WSGI (async views ≠ async concurrency) | WSGI + ASGI (ORM still sync-ish) |
| Concurrent LLM calls / worker | hundreds | = threads (16–64) | tens (thread/async hybrid) |
| Token streaming (SSE) | first-class `StreamingResponse` | possible, pins a worker | possible via ASGI, awkward |
| WebSockets | built-in | needs flask-sock/socketio | Channels (extra infra) |
| Validation | pydantic v2 (Rust, fast) | manual / marshmallow | DRF serializers |
| Auto OpenAPI | native | flasgger/apispec (manual) | drf-spectacular |
| DI | built-in `Depends` | none (globals/extensions) | none (viewset mixins) |
| ORM | bring your own (SQLAlchemy 2.0) | bring your own | best-in-class built-in |
| Admin UI | none | none | **killer feature** |
| Auth batteries | primitives only | extensions | complete |
| Background jobs | BackgroundTasks / ARQ / Celery | Celery/RQ | Celery (canonical) |
| Boilerplate for a 5-endpoint service | lowest | low | highest |
| Time to a CRUD product | medium | medium | fastest |
| Best fit | **chat/RAG/agent APIs, streaming, microservices** | tiny internal services, legacy | full products, admin-heavy, enterprise CRUD |

**Verdict for this JD:** FastAPI for the GenAI service. Be able to defend that in one sentence: *"LLM calls are long I/O waits, so ASGI gives an order-of-magnitude better concurrency per pod; plus streaming and typed contracts come free."*

---

## Production Checklist (for a GenAI API)

**API layer**
- [ ] `/v1` prefix; routers per domain; `services/` free of `fastapi` imports
- [ ] `response_model` on every route that returns internal objects
- [ ] Custom exception hierarchy + one handler; no `str(exc)` in responses
- [ ] Request size caps at ingress + `Field(max_length=...)` on prompts
- [ ] `docs_url`/`openapi_url` disabled or auth-gated in prod

**Async correctness**
- [ ] Zero blocking calls inside `async def` (audit `requests`, `time.sleep`, `psycopg2`, boto3)
- [ ] Clients (`httpx`, `AsyncOpenAI`, redis, engine) created once in `lifespan`
- [ ] No DB transaction held open across an LLM call

**LLM upstream**
- [ ] Explicit connect/read timeouts + bounded retries + jitter; honour `Retry-After`
- [ ] Circuit breaker; graceful degradation path
- [ ] Server-side `max_tokens` cap; per-tenant token budget in Redis
- [ ] Streaming: disconnect detection, `X-Accel-Buffering: no`, error frames, heartbeat

**Data**
- [ ] Pool sized so `workers × (pool_size + max_overflow) < max_connections`
- [ ] `pool_pre_ping`, `pool_recycle`; `expire_on_commit=False`
- [ ] Eager loading (`selectinload`) — N+1 asserted against in tests
- [ ] Alembic migrations run as a job, not in lifespan

**Security**
- [ ] JWT with pinned `algorithms=[...]`, short TTL, rotation + reuse detection
- [ ] API keys stored hashed; `hmac.compare_digest`; two-key rotation
- [ ] Secrets via `SecretStr` from env/Key Vault
- [ ] CORS allowlist (no `*` with credentials); TrustedHost; security headers
- [ ] Per-tenant isolation enforced in the vector-DB filter, not the prompt
- [ ] Prompt/PII redaction before logging; retention policy set

**Ops**
- [ ] `/healthz` (no deps) + `/readyz` (deps, 503 on failure) + startup probe
- [ ] Graceful shutdown ≥ longest stream; preStop sleep; `terminationGracePeriodSeconds` larger
- [ ] JSON logs with `request_id` contextvar; OpenTelemetry traces
- [ ] Metrics: RED + TTFT + tokens + cost per tenant; alert on p95 and 429 rate
- [ ] Idempotency keys on all POSTs that cost money
- [ ] Rate limits in Redis, not memory; `X-RateLimit-*` + `Retry-After` headers
- [ ] Nothing stateful in process memory (see Q46 table)

---

## Red Flags / Do NOT Say

- ❌ *"FastAPI is faster than Flask because it's async."* → Say: *"ASGI gives far better concurrency for I/O-bound work; raw single-request CPU cost is similar."*
- ❌ Using `requests` inside `async def`. If you write this on the whiteboard, you lose the round.
- ❌ `@app.on_event("startup")` — deprecated. Use `lifespan`.
- ❌ `openai.ChatCompletion.create(...)` — removed in openai ≥1.0. Use `client.chat.completions.create(...)`.
- ❌ `from langchain.llms import OpenAI` — legacy. Use `from langchain_openai import ChatOpenAI`.
- ❌ pydantic v1 methods (`.dict()`, `.json()`, `class Config`) without flagging them as v1.
- ❌ `jwt.decode(..., options={"verify_signature": False})` in an auth path, or omitting `algorithms=[...]`.
- ❌ *"I'd use `BackgroundTasks` for the 5-minute ingestion job."* → It dies with the pod.
- ❌ *"The `yield`-dependency session is still open in my `StreamingResponse` generator / background task."* → Since FastAPI 0.106 teardown runs when the handler returns, i.e. **before** either of those. Open a fresh session.
- ❌ Overriding a dependency in tests with `monkeypatch.setattr` on the module attribute — the route captured the original function object. Use `app.dependency_overrides`.
- ❌ *"We rate limit with a dict in memory."* → Wrong by a factor of N replicas.
- ❌ `allow_origins=["*"]` together with `allow_credentials=True`.
- ❌ Creating `AsyncOpenAI()` / `httpx.AsyncClient()` inside the request handler.
- ❌ Claiming DRF is fully async, or that Django's ORM is truly async.
- ❌ Holding an HTTP request open for a 3-minute agent run.
- ⚠️ If you don't know an internal: say *"I haven't read that part of Starlette's source; here's the behaviour I've relied on in production and how I'd verify it."* Confident wrong answers are worse than a scoped admission.

---

## Rapid-Fire (last 10 min before you walk in)

1. **FastAPI = ?** → Starlette (web) + pydantic v2 (types) + DI/OpenAPI glue.
2. **ASGI vs WSGI?** → `async app(scope, receive, send)` vs sync `app(environ, start_response)`; ASGI gets websockets, lifespan, non-blocking long I/O.
3. **`def` endpoint in FastAPI runs where?** → anyio threadpool, default **40** threads.
4. **`async def` + `time.sleep(5)`?** → blocks the whole event loop; entire worker stalls.
5. **Replacement for `@app.on_event`?** → `lifespan` asynccontextmanager passed to `FastAPI(lifespan=...)`.
6. **uvicorn `[standard]` gives?** → uvloop + httptools + websockets.
7. **Prod command?** → `uvicorn app.main:app --workers N --proxy-headers` or gunicorn `-k uvicorn_worker.UvicornWorker`.
8. **Dependency cached where?** → per request, keyed on the callable; disable with `use_cache=False`.
9. **`yield` dep teardown runs when?** → since FastAPI 0.106, when the route returns — **before the response is sent and before `BackgroundTasks`** → the session is already closed inside a `StreamingResponse` generator.
10. **Override deps in tests?** → `app.dependency_overrides[dep] = fake`.
11. **Validation failure status?** → **422** via `RequestValidationError`.
12. **Stop leaking a password field?** → `response_model=` (+ `response_model_exclude`); don't rely on the return annotation.
13. **SSE media type + the nginx fix?** → `text/event-stream` + header `X-Accel-Buffering: no`.
14. **SSE frame format?** → `data: <payload>\n\n` (blank line ends the frame).
15. **Client closed the tab mid-stream?** → `await request.is_disconnected()` → break → `await stream.close()`.
16. **SSE vs WebSocket?** → SSE = one-way, plain HTTP, auto-reconnect (token streaming). WS = two-way (interrupts/voice).
17. **3-minute agent run over HTTP?** → `202 Accepted` + job id + `Location`, poll `GET /runs/{id}`, or SSE progress channel.
18. **`BackgroundTasks` limit?** → same process, lost on restart, no retries — <1 s best-effort only.
19. **N+1 fix in SQLAlchemy 2.0?** → `selectinload` (collections) / `joinedload` (many-to-one); `raiseload("*")` in tests.
20. **Async session gotcha?** → `expire_on_commit=False`, else lazy refresh → `MissingGreenlet`.
21. **Pool math?** → `workers × (pool_size + max_overflow) < Postgres max_connections` (default 100).
22. **JWT must-do?** → pin `algorithms=["HS256"]`, verify `exp`, separate `typ` for access vs refresh, rotate refresh tokens + detect reuse.
23. **Rate limit across 4 pods?** → Redis (slowapi with `storage_uri`), never in-memory.
24. **Liveness vs readiness?** → liveness checks nothing external; readiness checks DB/Redis/vector store and returns 503.
25. **`select_related` vs `prefetch_related`?** → JOIN in one query (FK/O2O) vs two queries joined in Python (M2M/reverse).
