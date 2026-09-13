# Rapid-Fire Cheatsheet — Final Hour Cram

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

**Scope:** 254 one-liners across sections 1–7, plus cheat tables and a final-10-minutes drill.

**How to use:** read top-to-bottom once (~35 min). Then re-read only the **bold Q** text and try to say the answer out loud before your eyes hit the dash. Answers are ≤25 words on purpose — that is roughly how long a good verbal answer is before you pause and let them ask a follow-up.

## Table of Contents

1. [Python One-Liners (40)](#1-python-one-liners-40)
2. [FastAPI / API One-Liners (30)](#2-fastapi--api-one-liners-30)
3. [LLM Fundamentals One-Liners (40)](#3-llm-fundamentals-one-liners-40)
4. [RAG One-Liners (40)](#4-rag-one-liners-40)
5. [Vector DB One-Liners (30)](#5-vector-db-one-liners-30)
6. [Agentic One-Liners (42)](#6-agentic-one-liners-42)
7. [Cloud / Azure / Deploy One-Liners (32)](#7-cloud--azure--deploy-one-liners-32)
8. [Cheat Tables](#8-cheat-tables)
9. [Buzzwords To Drop Naturally](#9-buzzwords-to-drop-naturally)
10. [10 Questions To Ask Them](#10-10-questions-to-ask-them)
11. [Red Flags / Do NOT Say](#11-red-flags--do-not-say)
12. [Rapid-Fire (last 10 min before you walk in)](#12-rapid-fire-last-10-min-before-you-walk-in)

---

## 1. Python One-Liners (40)

**Core / runtime / GIL**

- **What is the GIL** — One mutex; only one thread executes CPython bytecode at a time. Protects refcounts, not your data structures.
- **Does the GIL make threads useless** — No. It is released during I/O (sockets, disk) and inside C extensions like NumPy, so I/O threads scale fine.
- **Threads vs processes vs asyncio** — Threads = blocking I/O; processes = CPU-bound (`ProcessPoolExecutor`); asyncio = thousands of concurrent I/O waits, one thread.
- **Is the GIL gone** — Optional build, not the default. PEP 703 free-threading shipped *experimentally* in 3.13 and moved to officially supported (still opt-in) in 3.14; single-thread overhead was large on 3.13 and roughly single-digit percent by 3.14.
- **How does CPython manage memory** — Reference counting for immediate free, plus a generational cycle collector (3 generations) for reference cycles.
- **When do you call `gc.freeze()`** — Before forking workers: moves current objects out of GC scanning so copy-on-write pages stay shared, cutting worker RSS.
- **What is a memory leak in Python** — Usually unbounded caches, module-level dicts, or lingering references — not the allocator. Find with `tracemalloc` snapshots diff.
- **`is` vs `==`** — `is` compares identity (`id()`), `==` calls `__eq__`. Small-int and interned-string caching makes `is` look right by accident.
- **Shallow vs deep copy** — `copy.copy` copies the container only; `copy.deepcopy` recursively copies nested objects and tracks already-seen ids.
- **Mutable default argument bug** — `def f(x=[])` evaluates the list once at def time. Use `None` sentinel and create inside.

**Objects / data model / OOP**

- **What is the MRO** — Method Resolution Order via C3 linearization; check with `Cls.__mro__`. `super()` walks the MRO, not the parent class.
- **What does `super()` really do** — Proxies the next class in the *instance's* MRO — which in multiple inheritance may be a sibling, not the base.
- **What is `__slots__`** — Declares fixed attributes, drops per-instance `__dict__`; typically a large memory saving on small objects (often ~30–50%, measure it) and slightly faster attribute access. Blocks arbitrary attrs.
- **`@dataclass(slots=True)`** — 3.10+; gives dataclass ergonomics with `__slots__` memory. Use `frozen=True` for hashable value objects.
- **`__getattr__` vs `__getattribute__`** — `__getattribute__` runs on every access; `__getattr__` only on failure. Override `__getattr__` for proxies/lazy loading.
- **What is a descriptor** — Object defining `__get__`/`__set__`; the machinery behind `property`, `classmethod`, and ORM/pydantic fields.
- **`@classmethod` vs `@staticmethod`** — `classmethod` receives `cls` (alternate constructors, subclass-aware); `staticmethod` receives nothing, just namespacing.
- **Metaclass in one line** — A class whose instances are classes; `__new__` runs at class creation. Used by ABCs, ORMs. Rarely needed — prefer `__init_subclass__`.
- **Abstract base class** — `from abc import ABC, abstractmethod`; instantiation fails until all abstract methods are implemented. Use for plugin/tool interfaces.
- **How do you make an object hashable** — Define `__hash__` and `__eq__` consistently; immutable fields only, or you corrupt dict/set buckets.

**Iterators, generators, decorators, functional**

- **Iterator vs iterable** — Iterable has `__iter__`; iterator has `__iter__` and `__next__` and is consumed once. Generators are iterators.
- **Why generators** — Lazy, O(1) memory streaming over large files/DB cursors/LLM token streams; state is suspended at `yield`.
- **`yield from`** — Delegates iteration to a sub-generator and forwards `send`/`throw`; flattens nested pipelines without a manual loop.
- **Generator as coroutine (`.send`)** — Push values in; legacy pattern. Modern async uses `async def` + `await`, not `yield`-based coroutines.
- **What does a decorator do** — Takes a function, returns a replacement. Always wrap with `functools.wraps` to keep `__name__`, docstring, and signature metadata.
- **Decorator with arguments** — Three levels: factory → decorator → wrapper. Return the wrapper; the outer call configures it.
- **`functools.lru_cache` vs `cache`** — `cache` is `lru_cache(maxsize=None)`. Keys must be hashable; never use on methods holding big `self` (leaks).
- **Context manager two ways** — Class with `__enter__`/`__exit__`, or `@contextlib.contextmanager` on a single-`yield` generator. `AsyncExitStack` for dynamic async cleanup.
- **Closure and `nonlocal`** — Inner function captures the enclosing variable by reference; `nonlocal` lets you rebind it. Late binding bites in loops.
- **`*args` / `**kwargs` and `/`, `*`** — `/` marks positional-only, bare `*` marks keyword-only; use them to keep public APIs refactor-safe.

**Asyncio**

- **Coroutine vs task** — A coroutine does nothing until awaited; `asyncio.create_task()` schedules it concurrently on the loop.
- **`asyncio.gather` vs `TaskGroup`** — `TaskGroup` (3.11+) is structured concurrency: one child failure cancels siblings and raises an `ExceptionGroup`. Prefer it.
- **Biggest asyncio mistake** — Calling blocking code (`requests`, `time.sleep`, heavy CPU) in a coroutine; it stalls the whole loop. Use `asyncio.to_thread`.
- **How to bound concurrency** — `asyncio.Semaphore(n)` around each call, plus `asyncio.timeout()`; essential for LLM API fan-out to avoid 429s.
- **`contextvars`** — Async-safe "thread-local": carries request_id / trace_id / tenant across awaits. Used by FastAPI and OpenTelemetry.

**Modern Python, typing, pydantic v2**

- **What's new in 3.11 you use** — Faster CPython (~25% average, 10–60% depending on workload), `asyncio.TaskGroup`, `asyncio.timeout()`, `except*`/`ExceptionGroup`, `typing.Self`, `tomllib`, zero-cost exceptions.
- **What's new in 3.12** — PEP 695 `type X = ...` and `def f[T]()` generics, flexible f-strings, `itertools.batched`, per-interpreter GIL groundwork.
- **Pydantic v2 vs v1** — Core rewritten in Rust (`pydantic-core`), roughly 4–50x faster on the project's own benchmarks; `model_validate`/`model_dump`, `field_validator`, `ConfigDict` replace v1's `parse_obj`/`dict`/`validator`/`class Config`.
- **Pydantic v2 API you must name-drop** — `@field_validator("field_name", mode="before")` (field names are required args), `@model_validator(mode="after")`, `TypeAdapter(list[User])`, `computed_field`, `model_dump_json()`, strict vs lax mode.
- **Why pydantic matters for GenAI** — It is the schema layer: tool/function JSON Schema, structured outputs, and validating LLM JSON before it hits your DB.

---

## 2. FastAPI / API One-Liners (30)

**Framework & ASGI**

- **What is ASGI** — Async successor to WSGI; supports long-lived connections (WebSocket, SSE) and concurrent I/O. FastAPI is Starlette (ASGI) + pydantic.
- **Why FastAPI over Flask** — Native async, pydantic validation, auto OpenAPI/Swagger, DI via `Depends`, typed signatures — all critical for streaming LLM endpoints.
- **When Flask or Django instead** — Flask for tiny sync services; Django when you need ORM + admin + auth batteries and the team already lives there.
- **`def` vs `async def` endpoint** — A plain `def` route runs in Starlette's threadpool (safe for blocking libs); `async def` runs on the loop — never block it.
- **How does FastAPI generate docs** — Type hints + pydantic models → JSON Schema → OpenAPI 3.1 at `/openapi.json`, rendered at `/docs` and `/redoc`.
- **Lifespan vs `@app.on_event`** — `on_event` is deprecated; use the `lifespan` async context manager to open/close HTTP clients, DB pools, and vector store handles.
- **Middleware** — `@app.middleware("http")` or ASGI middleware; use for request-id, timing, auth pre-checks, and structured logging.
- **Background tasks** — `BackgroundTasks` runs after the response in the same process; use Celery/ARQ/queue for anything retryable or long.
- **How do you version an API** — URL prefix `/v1` via `APIRouter(prefix="/v1")`; additive changes only inside a version, deprecate with headers and a sunset date.
- **How do you stream LLM tokens** — `StreamingResponse(gen(), media_type="text/event-stream")` with SSE frames; set `X-Accel-Buffering: no` so proxies don't buffer.

**Dependencies, validation, contracts**

- **What is `Depends`** — FastAPI's DI: resolves and caches per request, supports nesting, and yields teardown. Ideal for DB sessions and auth principals.
- **Modern DI idiom** — `def route(svc: Annotated[Service, Depends(get_service)])`; `Annotated` keeps the type checker and FastAPI in agreement.
- **Dependency with cleanup** — Use `yield`: code before yield sets up, after yield tears down — even on exception. Perfect for sessions and tracing spans.
- **Router-level / app-level deps** — `APIRouter(dependencies=[Depends(verify_key)])` applies auth to every route without repeating it.
- **`response_model`** — Declares the outbound schema; filters extra fields (prevents leaking internals) and documents the contract. Pair with `response_model_exclude_none`.
- **Path vs Query vs Body** — Inferred from the signature; scalars default to query, pydantic models to body. Force with `Query()`, `Path()`, `Body()`.
- **Custom validation error format** — Override `RequestValidationError` with `@app.exception_handler`; return your standard error envelope, not raw 422 detail.
- **How do you upload big files** — `UploadFile` streams to a spooled temp file instead of loading into memory; cap size at the proxy layer too.
- **Where do you validate LLM output** — Pydantic model + `model_validate_json`; on failure, one repair retry with the validation error injected into the prompt.
- **What is a request/correlation id** — UUID from header or generated in middleware, stored in a `contextvar`, logged everywhere and passed to LLM trace metadata.

**Production, security, scale**

- **How many workers** — Start with `2 × cores + 1` for sync workloads; for async I/O-bound LLM proxies, 1–2 per core and scale pods instead.
- **Gunicorn + uvicorn command** — `gunicorn app:app -k uvicorn.workers.UvicornWorker -w 4 --timeout 120`; raise timeout for slow LLM calls.
- **JWT in one line** — Signed base64 header.payload.signature; validate `exp`, `aud`, `iss`, and the algorithm. Never accept `alg: none`.
- **HS256 vs RS256** — HS256 shared secret (single service); RS256 asymmetric — services verify with the public key, only the issuer can mint.
- **Access vs refresh token** — Access short-lived (5–15 min) and stateless; refresh long-lived, stored server-side, rotated and revocable.
- **How do you do RBAC** — Claims/scopes in the token → a `Depends(require_scope("agent:write"))` dependency → 403 on mismatch. Enforce server-side, always.
- **Offset vs cursor pagination** — Offset is simple but drifts and slows on deep pages; cursor/keyset (`WHERE id > last`) is stable and O(log n).
- **What is idempotency** — Client sends `Idempotency-Key`; you store key → response for 24h and replay it. Mandatory for payments and agent write-actions.
- **Rate limiting approach** — Token bucket in Redis keyed by API key/tenant; return 429 with `Retry-After` and a `X-RateLimit-Remaining` header.
- **Health endpoints** — `/healthz` liveness (process up, no deps) and `/readyz` readiness (DB, vector store, LLM reachable). Never fail liveness on a downstream blip.

---

## 3. LLM Fundamentals One-Liners (40)

**Architecture**

- **What is a transformer** — Stacked self-attention + feed-forward blocks with residuals and normalization; processes all tokens in parallel, unlike RNNs.
- **Attention formula** — `softmax(QK^T / √d_k) · V`. Q asks, K advertises, V carries content; the softmax is a soft lookup.
- **Why divide by √d_k** — Dot products grow with dimension; scaling keeps the softmax out of saturation so gradients don't vanish.
- **Multi-head attention** — Split `d_model` into h heads so different heads learn different relations (syntax, coreference), then concatenate and project.
- **Decoder-only vs encoder-decoder** — GPT-style decoder-only uses a causal mask for next-token prediction; encoder-decoder (T5) suits translation-style seq2seq.
- **Attention complexity** — O(n²·d) in sequence length — the reason long context is expensive. FlashAttention cuts memory/IO, not asymptotics.
- **GQA / MQA** — Grouped/Multi-Query Attention share K/V heads across query heads, shrinking the KV cache with near-equal quality.
- **RoPE** — Rotary positional embeddings rotate Q/K by position, encoding relative distance; enables context extension via scaling.
- **Mixture of Experts** — Sparse FFN layers; a router picks top-k experts per token, so parameter count is huge but active compute stays small.
- **What are logits** — Raw pre-softmax scores over the vocabulary; sampling parameters reshape this distribution before a token is drawn.

**Tokens & context**

- **What is a token** — Sub-word unit from BPE. English ≈ 4 characters or ~0.75 words per token; code and non-Latin scripts are denser.
- **Which tokenizer** — `tiktoken`: `o200k_base` for GPT-4o and later OpenAI models, `cl100k_base` for GPT-4/3.5-turbo. Count with `tiktoken.encoding_for_model("gpt-4o")` (falls back to `get_encoding("o200k_base")` for unknown names).
- **What is the context window** — Max tokens for prompt **plus** completion. GPT-4o family: 128K context, 16,384 max output tokens; newer frontier models go far higher (hundreds of thousands to ~1M) — quote 4o's numbers and say limits are per-model.
- **Cost of a long prompt** — Linear in input tokens per call, and it repeats on every turn — chat history is the silent budget killer.
- **What is the KV cache** — Cached keys/values per layer so each new token attends without recomputing the prefix; each decode step drops from O(n²) to O(n), so generating n tokens is O(n²) instead of O(n³).
- **KV cache memory** — `2 × layers × kv_heads × head_dim × seq_len × batch × bytes`; it, not weights, is what OOMs long-context serving.
- **What is prompt caching** — Provider caches the static prefix; OpenAI applies it automatically once the prompt is ≥1024 tokens, with a cached-input discount that is model-dependent (roughly 50–90% off input, varies by model/provider). Put static content first.
- **Lost in the middle** — Models attend best to the start and end of context; bury nothing important in the middle of 40 retrieved chunks.
- **Context window vs needle-in-haystack** — A model can hold 128K but reason poorly across it; measure with your own long-context eval, don't trust the spec.
- **How do you trim chat history** — Keep system + last N turns verbatim, roll older turns into a running summary, and always keep tool results that are still referenced.

**Decoding parameters**

- **temperature** — Divides logits before softmax. 0 = greedy/deterministic-ish, 1 = raw distribution, >1 = flatter and more random.
- **top_p (nucleus)** — Sample only from the smallest token set whose cumulative probability ≥ p. Truncates the tail without flattening.
- **top_p vs temperature** — Tune one, not both. Default: temperature for creativity, top_p left at 1.0.
- **Is temperature=0 deterministic** — Practically, not exactly: batching, GPU non-determinism, and MoE routing cause drift. Use `seed` and check `system_fingerprint`.
- **frequency_penalty / presence_penalty** — Range −2…2; frequency scales with repeat count, presence is a flat penalty once a token has appeared.
- **logit_bias** — Per-token score nudge (−100 bans, +100 forces). Useful to hard-forbid a token in constrained classification.
- **max_tokens** — Caps the completion; newer reasoning models use `max_completion_tokens`. Always set it — it is your runaway-cost fuse.
- **stop sequences** — Strings that halt generation; used to end a structured block. Prefer structured outputs over hand-rolled stops.
- **What are structured outputs** — `response_format={"type": "json_schema", "json_schema": {"name": ..., "schema": {...}, "strict": True}}` — note `strict` sits *inside* `json_schema`. Decoding is constrained to the schema, so parsing cannot fail; the SDK's `.parse()` helper takes a pydantic model directly.
- **JSON mode vs structured outputs** — JSON mode guarantees valid JSON only; strict json_schema guarantees *your* schema. Prefer the latter.

**Training, tuning, serving**

- **Pretraining vs SFT vs RLHF** — Pretrain = next-token on web scale; SFT = instruction imitation; RLHF/DPO = align to human preference rankings.
- **What is LoRA** — Freeze base weights, train low-rank adapters `W + (B·A)·α/r`; ~0.1–1% trainable params, adapters are megabytes and swappable.
- **What is QLoRA** — LoRA on a 4-bit NF4 quantized base; fine-tunes a 7–13B model on a single consumer GPU with near-FP16 quality.
- **Fine-tune vs RAG, one line** — RAG for *knowledge* (changing, citable facts); fine-tune for *behaviour* (format, tone, domain jargon, shorter prompts).
- **What is quantization** — Storing weights at lower precision: FP16 → INT8 (~2x smaller), INT4 (~4x). Quality loss is small at 8-bit, noticeable at 4-bit on reasoning.
- **GPTQ vs AWQ vs GGUF** — GPTQ/AWQ are GPU post-training quantizers (AWQ protects salient weights); GGUF is the llama.cpp CPU/edge format.
- **What is distillation** — Train a small student on a large teacher's outputs; a standard production move that can cut cost roughly an order of magnitude on a narrow task (measure it, don't quote a fixed multiple).
- **TTFT / TPOT / throughput** — Time To First Token (prefill, UX-critical), Time Per Output Token (decode speed), tokens/sec across all users (cost-critical).
- **How do you cut perceived latency** — Stream tokens, cache prompts, shorten output, run retrieval in parallel, and use a smaller model for routing/classification.
- **What causes hallucination** — The model optimizes plausibility, not truth; it has no grounding, no uncertainty signal, and is trained to always answer.

---

## 4. RAG One-Liners (40)

**Why & ingest**

- **What is RAG in one sentence** — Retrieve relevant passages at query time and put them in the prompt so the model answers from evidence instead of memory.
- **RAG pipeline stages** — Load → clean → chunk → embed → index → (query rewrite → hybrid retrieve → rerank → pack) → generate → cite → evaluate.
- **Why RAG over fine-tuning** — Fresh data, cheap updates, per-document access control, and citations. Fine-tuning cannot do any of those four.
- **Biggest ingestion mistake** — Bad parsing. Garbage PDF extraction (broken tables, lost headers) caps your ceiling before embeddings even run.
- **How do you handle PDFs with tables** — Layout-aware parsing (e.g. Azure Document Intelligence / Unstructured), keep tables as markdown, repeat headers into each row-group chunk.
- **What metadata do you store per chunk** — doc_id, chunk_index, source URI, page/section, title, timestamp, version, tenant/ACL, and content hash.
- **Why store a content hash** — Deterministic chunk IDs make upserts idempotent and let you re-index only changed documents.
- **How do you handle document updates** — Version documents, upsert changed chunks by deterministic ID, and hard-delete orphaned chunks — stale vectors are a correctness bug.
- **How do you enforce access control in RAG** — Filter at query time on ACL metadata inside the vector search, never after generation. Never let the LLM be the access checker.
- **Multi-tenant isolation** — Separate namespaces/collections per tenant when volume allows; otherwise a mandatory tenant filter injected server-side, not by the caller.

**Chunking**

- **Why chunk at all** — Embeddings dilute over long text and context is finite; chunks are the unit of both retrieval precision and citation.
- **Default chunk size** — 400–800 tokens for prose with 10–15% overlap; then tune against your eval set, never by vibes.
- **Why overlap** — Prevents an answer that straddles a boundary from being cut in half; 10–20%, more costs storage and duplicates hits.
- **Recursive character splitting** — Split on the largest natural separator that fits (`\n\n` → `\n` → sentence → word) so structure survives.
- **Semantic chunking** — Split where consecutive-sentence embedding similarity drops below a percentile threshold; better boundaries, higher ingest cost.
- **Structural chunking** — Split by markdown headers / HTML / legal clause / code function. Best default for technical and legal corpora.
- **Small-to-big (parent document)** — Embed small precise chunks, but return the parent section to the LLM: precision of small, context of large.
- **Contextual retrieval** — Prepend an LLM-written 1–2 sentence "where this sits in the doc" blurb to each chunk before embedding; large recall gains.
- **How do you chunk code** — By function/class using an AST or language-aware splitter, keeping imports and signature in the chunk.
- **How do you chunk chat transcripts** — Sliding windows of 5–10 turns with 1–2 turns overlap, tagged with speakers and timestamp range.

**Retrieval**

- **Dense vs sparse retrieval** — Dense (embeddings) captures meaning and paraphrase; sparse (BM25) nails exact IDs, error codes, and rare product names.
- **What is hybrid search** — Run BM25 and vector search together and fuse the ranked lists; consistently beats either alone on enterprise corpora.
- **What is RRF** — Reciprocal Rank Fusion: `score = Σ 1/(k + rank_i)`, k≈60. Rank-based, so it needs no score normalization across engines.
- **Alternative to RRF** — Weighted score fusion after min-max normalization; more tunable, more fragile when one engine's score scale shifts.
- **What is HyDE** — Ask the LLM to write a hypothetical answer, embed that, and search with it — closes the vocabulary gap between short questions and prose.
- **Multi-query retrieval** — Generate 3–5 paraphrases of the query, retrieve for each, dedupe and fuse. Cheap recall boost for vague questions.
- **Query decomposition** — Split a multi-part question into sub-questions, retrieve per sub-question, then synthesize. Needed for comparative queries.
- **Step-back prompting** — Ask a broader conceptual question first to retrieve background, then answer the specific one with both contexts.
- **What is MMR** — Maximal Marginal Relevance: `λ·relevance − (1−λ)·max_similarity_to_selected`; trades a little relevance for diversity and kills near-duplicate chunks.
- **What top_k do you retrieve** — Retrieve wide (k=20–50) then rerank down to 3–8 for the prompt. Retrieval recall first, precision second.

**Rerank, pack, generate**

- **What is a reranker** — A cross-encoder that scores (query, chunk) jointly with full attention; far more accurate than bi-encoder cosine, ~10–50x slower.
- **Why can't you just use the reranker for everything** — It cannot be indexed; scoring is O(candidates), so it only runs on the top-k the vector search returns.
- **How do you order chunks in the prompt** — Best chunks first and last (lost-in-the-middle), each with a chunk id header so the model can cite.
- **How do you force citations** — Number the chunks, require `[id]` markers in the answer, and post-validate that every cited id exists in the context.
- **How do you make it say "I don't know"** — Explicit instruction plus a relevance threshold: if the top rerank score is below the cutoff, short-circuit before generating.
- **How do you cut RAG cost** — Rerank instead of stuffing, cache embeddings and prompt prefixes, use a small model for extraction and a big one only for synthesis.

**Evaluation & failure triage**

- **How do you evaluate retrieval** — Recall@k, MRR, nDCG@k against a golden set of ~100–200 question→chunk pairs built from real user questions.
- **RAGAS metrics** — `faithfulness` (answer grounded in context), `answer_relevancy`, `context_precision` (are the *top-ranked* chunks the relevant ones), `context_recall` (did we fetch everything the ground-truth answer needed). First two grade generation, last two grade retrieval.
- **Failure triage rule** — Bad answer + correct context = generation/prompt problem. Bad answer + missing context = chunking, embedding, or query problem. Diagnose in that order.
- **Top three real RAG failure causes** — Parsing loss, chunk boundaries splitting the answer, and query/document vocabulary mismatch. Hybrid + rerank fixes most of the third.

---

## 5. Vector DB One-Liners (30)

**Indexes**

- **What is an ANN index** — A structure trading exactness for speed: sub-linear search with ~95–99% recall instead of O(n) exact scan.
- **What is HNSW** — Hierarchical Navigable Small World: a multi-layer proximity graph; greedy descent from a sparse top layer to a dense base layer.
- **HNSW `M`** — Max outgoing edges per node per layer (16–64), with `2M` at the base layer. Higher = better recall and more RAM; roughly `M×2×4` bytes of graph per vector.
- **HNSW `ef_construction`** — Candidate list size at build (100–400). Higher = better graph, slower ingest. Build-time only.
- **HNSW `ef_search`** — Candidate list at query (40–400). The one runtime recall/latency dial — raise it when recall is low, no rebuild needed.
- **What is IVF** — Cluster vectors into `nlist` Voronoi cells; search only the `nprobe` nearest cells. Cheap to build, needs training data.
- **IVF tuning rule** — `nlist ≈ 4–16·√n` (FAISS guideline), `nprobe` at 1–10% of nlist. More probes = more recall and more latency.
- **HNSW vs IVF** — HNSW: better recall/latency, high RAM, no training, slow deletes. IVF: lower memory, needs training, better for huge/batch workloads.
- **What is PQ** — Product Quantization: split the vector into sub-vectors and replace each with a centroid id; 8–32x compression with recall loss.
- **What is DiskANN** — SSD-resident graph index for billion-scale corpora where RAM-only HNSW is uneconomic; higher latency, far lower cost.
- **Flat index** — Brute force, exact, O(n·d). Perfectly fine — and the right answer — below ~50–100K vectors.

**Similarity & operations**

- **Cosine vs dot vs L2** — Cosine = angle (magnitude-free), dot rewards magnitude too, L2 is straight distance. Pick the metric the embedding model was trained with.
- **When is cosine equal to dot** — On L2-normalized vectors they induce identical rankings, so normalize once and use the faster dot product.
- **Which metric for OpenAI embeddings** — Cosine; `text-embedding-3-*` vectors are already normalized, so dot product gives the same order.
- **Embedding dimensions to quote** — `text-embedding-3-small` = 1536, `text-embedding-3-large` = 3072, legacy `ada-002` = 1536.
- **What is the `dimensions` parameter** — Matryoshka truncation: request e.g. 512 dims from `text-embedding-3-large` and keep most quality at a fraction of storage. Re-normalize after truncating if you rely on dot product.
- **Can you mix embedding models in one index** — No. Different model or different dimension = different vector space; re-embed the whole corpus on any model change.
- **pgvector operators** — `<->` L2, `<=>` cosine distance, `<#>` negative inner product, `<+>` L1. `ORDER BY emb <=> $1 LIMIT 10`.
- **pgvector index types** — `ivfflat` (needs data before building, set `lists`) and `hnsw` (0.5+, no training, better recall). Set `hnsw.ef_search` per session.
- **Why pgvector at all** — One database for rows, ACLs, and vectors: transactional consistency, existing backups, no extra vendor. Ceiling is a few million vectors.
- **Pre-filter vs post-filter** — Pre-filter restricts the candidate set before search (correct k, can break graph connectivity); post-filter searches then drops (fast, may return fewer than k).
- **Why do filtered vector searches return too few results** — Post-filtering removed most of the top-k; fix by over-fetching, or use an engine with native filtered ANN.
- **How do you delete in HNSW** — Usually a soft-delete tombstone plus periodic compaction; graph edges cannot be cheaply removed in place.

**Sizing, ops, selection**

- **Memory math you should say out loud** — 1M vectors × 1536 dims × 4 bytes ≈ 6.1 GB raw. The HNSW graph at M=16 adds only ~128 B/vector (`M×2×4`) ≈ 0.13 GB, ~2% here; budget ~1.3–1.5x raw overall once ids, payloads, and replicas are counted.
- **How do you shrink that 6 GB** — int8 scalar quantization (4x), Matryoshka dims 1536→512 (3x), or binary quantization (32x) with a float rescoring pass.
- **Binary quantization** — 1 bit per dimension with Hamming distance; ~32x smaller, ~95% recall when you rescore the top-100 with full vectors.
- **How do you pick a vector DB** — Scale, filtering needs, ops appetite: pgvector (<few M, already on Postgres), Qdrant/Milvus/Weaviate (self-host scale), Pinecone (managed), Azure AI Search (Azure-native hybrid + semantic ranker).
- **Which one on Azure** — Azure AI Search: vector + BM25 + semantic reranker + security trimming in one service, integrates with Azure OpenAI On Your Data.
- **How do you re-index without downtime** — Build the new index under a new alias/collection, dual-write, evaluate on the golden set, then flip the alias atomically.
- **How do you benchmark a vector store** — Fix a query set, sweep `ef_search`/`nprobe`, and plot recall@10 against p95 latency; pick the knee, not the max.

---

## 6. Agentic One-Liners (42)

**Definitions & patterns**

- **What is an AI agent** — An LLM in a loop that decides which tools to call, observes results, and iterates until a goal is met or a limit trips.
- **Agent vs workflow** — Workflow: you fix the control flow. Agent: the model chooses the path. Prefer workflows; use agents only when paths are unpredictable.
- **What is ReAct** — Reason + Act: interleave Thought → Action → Observation so the model plans, uses a tool, and re-plans on evidence.
- **What is Reflexion / self-critique** — The agent grades its own output against criteria and retries with the critique in context; costs an extra call, buys accuracy.
- **Plan-and-Execute** — Plan all steps up front with a strong model, execute each with a cheap one, replan only on failure. Cheaper and more auditable than pure ReAct.
- **Chain-of-Thought vs ReAct** — CoT reasons in text only; ReAct grounds reasoning in real tool observations. CoT alone still hallucinates facts.
- **Self-consistency** — Sample N reasoning paths at temperature >0 and majority-vote the answer; accuracy up, cost ×N.
- **Tree of Thoughts** — Branch and evaluate multiple partial solutions, backtracking on dead ends. High cost — reserve for puzzles/planning, not enterprise Q&A.
- **Routing pattern** — A cheap classifier model picks the specialist chain/model; the biggest single cost lever in production agents.
- **Reflection vs guardrail** — Reflection improves quality probabilistically; a guardrail is a deterministic check that must pass. Ship both, trust only the guardrail.

**Tools & function calling**

- **How does function calling work** — You send JSON Schema tool definitions; the model returns `tool_calls`; you execute and append a `tool` message with `tool_call_id`; call again.
- **Who executes the tool** — Your code, always. The model only emits a name and arguments — it never touches your systems directly.
- **Tool schema essentials** — Precise name, a description that says *when* to use it, typed params with enums and examples, and `required` set correctly.
- **How many tools is too many** — Beyond ~15–20 selection accuracy degrades; group into namespaced sub-agents or retrieve the relevant tool subset per query.
- **Parallel tool calls** — Models can return several `tool_calls` in one turn; run them with `asyncio.gather` and append all results before re-invoking.
- **Strict tool arguments** — Enable strict function schemas so arguments are constrained to your JSON Schema — kills the "missing required field" retry loop.
- **What makes a tool agent-friendly** — Idempotent, fast, returns compact JSON (not a 50KB blob), and returns *actionable* errors the model can recover from.
- **How do you handle tool errors** — Return a structured error string with a hint, let the agent retry twice, then escalate — never crash the loop on the first failure.
- **How do you protect destructive tools** — Split read and write tools, require explicit confirmation (human-in-the-loop) before writes, scope credentials per tool, and log every invocation.
- **Integrating enterprise systems (SAP/Salesforce/ServiceNow)** — Wrap the REST API in a thin typed tool with auth, retries, timeout, pagination, and field whitelisting — never hand the agent a raw HTTP tool.

**Memory & state**

- **Agent memory types** — Short-term (message buffer/scratchpad), long-term semantic (facts in a vector store), episodic (past interactions), procedural (learned instructions).
- **Working memory strategy** — Keep the system prompt + last N turns verbatim, summarize the rest, and re-inject only tool results still in play.
- **How do you persist agent state** — A checkpointer keyed by `thread_id` (LangGraph `MemorySaver` in tests, `PostgresSaver`/`SqliteSaver` in prod) that snapshots state per step.
- **Why a checkpointer matters** — It gives you resume-after-crash, time-travel debugging, and human-in-the-loop pause/resume for free.
- **Semantic memory retrieval** — Embed and store user facts/preferences; retrieve top-k by the current query and inject — it is RAG pointed at the user, not the corpus.
- **How do you stop memory from growing forever** — Token-budget the buffer, summarize on overflow, TTL episodic memory, and dedupe semantic facts on write.
- **What is context engineering** — Deciding what occupies the window each step: instructions, tools, retrieved facts, memory, history — the real skill behind agent quality.
- **How do you handle multi-turn state in an API** — Server-side thread id; the client sends only the new message. Never trust the client to send back the full history.

**Multi-agent & orchestration**

- **When do you use multi-agent** — When roles need different tools, prompts, or models, or work parallelizes. Otherwise one agent with good tools wins.
- **Supervisor pattern** — A router agent owns the plan and delegates to specialists, who report back; the supervisor holds the shared state.
- **Hierarchical / swarm / network** — Hierarchical = supervisors of supervisors; swarm = peers hand off directly; network = anyone-to-anyone (hardest to debug — avoid).
- **What is LangGraph** — A stateful graph runtime: `StateGraph` of nodes and conditional edges over a typed state dict, with checkpointing, streaming, and interrupts.
- **LangGraph state reducers** — `Annotated[list[AnyMessage], add_messages]` appends instead of overwriting; without a reducer, concurrent nodes clobber each other.
- **How do you do human-in-the-loop** — `interrupt()` inside the node pauses and persists state; resume with `Command(resume=decision)` after the human approves.
- **How do you stop infinite loops** — `recursion_limit`/max iterations, a wall-clock deadline, a token/cost budget, and repeated-identical-tool-call detection.
- **Framework choice in one line** — LangGraph for stateful control flow, LlamaIndex for RAG-heavy, CrewAI for quick role-based crews, plain SDK when the flow is simple.
- **What is MCP** — Model Context Protocol: a JSON-RPC 2.0 standard where servers expose tools, resources, and prompts to any client over stdio or streamable HTTP.
- **Why MCP matters** — Write the connector once and every MCP-capable client uses it — it decouples tool integrations from your agent framework.
- **How do you evaluate an agent** — Task success rate, tool-call accuracy, trajectory/step efficiency, cost and latency per task, plus LLM-as-judge on final output.
- **What do you trace in production** — Every step: prompt, tool calls, latency, tokens, cost, retries, and outcome — via LangSmith/Langfuse or OpenTelemetry GenAI semantic conventions.
- **Biggest agent risk** — Excessive agency: an over-permissioned agent taking irreversible actions on injected instructions. Least privilege + HITL on writes.
- **Prompt injection through tools** — Treat all retrieved/tool content as untrusted data, never instructions; delimit it, and never let it change tool permissions.

---

## 7. Cloud / Azure / Deploy One-Liners (32)

**Azure OpenAI**

- **Azure OpenAI vs OpenAI API** — Same models, different plane: Entra ID auth, private networking, regional residency, quota per deployment, enterprise SLAs and compliance.
- **What is a deployment name** — Your alias for a model in a resource; in the SDK you pass the *deployment name* as `model`, not `gpt-4o`.
- **Which client class** — `AzureOpenAI` / `AsyncAzureOpenAI` with `azure_endpoint` and `api_version` (a dated string such as the `2024-10-21` GA — quote it as "a dated api_version, check current GA"); the rest of the API surface matches OpenAI. Azure's newer `/openai/v1/` surface lets you use the plain client and drop the dated `api_version`.
- **How do you auth without keys** — Managed identity: `DefaultAzureCredential` + `get_bearer_token_provider` for scope `https://cognitiveservices.azure.com/.default`.
- **Which RBAC role** — `Cognitive Services OpenAI User` to call the model; `...OpenAI Contributor` to manage deployments. Never hand out keys.
- **What is TPM** — Tokens Per Minute quota per deployment; the RPM ceiling is derived from TPM at a **model-specific ratio** (commonly quoted as ~6 RPM per 1K TPM for GPT-3.5-class and ~1 RPM per 1K TPM for GPT-4-class) — quote it as "a fixed ratio, check the model's quota page" rather than a hard number.
- **What is PTU** — Provisioned Throughput Units: reserved capacity with predictable latency and no noisy-neighbour throttling; billed hourly, worth it above steady high volume.
- **How do you handle 429** — Exponential backoff with jitter, honour `Retry-After`, queue non-interactive work, and fail over to a second region's deployment.
- **How do you scale beyond one deployment** — Multiple deployments/regions behind a router (or Azure API Management) with weighted round-robin and health-aware failover.
- **What is the content filter** — Azure's built-in safety on prompt and completion across four categories (hate, sexual, violence, self-harm) at four severity levels, plus optional jailbreak and protected-material detections; violations return HTTP 400 with a `content_filter` code and per-category detail.
- **How do you keep data private** — Data is not used to train; add private endpoints, disable public network access, customer-managed keys, and opt out of abuse-monitoring logging if approved.
- **Azure RAG stack in one line** — Azure AI Search (hybrid + semantic ranker) + Azure OpenAI embeddings/chat + Blob Storage + Document Intelligence for parsing.

**Containers & Kubernetes**

- **Dockerfile for a Python API** — Multi-stage build, `python:3.11-slim`, install into a venv, copy only the venv and app, run as a non-root `USER`.
- **Why multi-stage** — Build tools and caches stay out of the final image: smaller surface, faster pulls, fewer CVEs.
- **Container start command** — `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --timeout 120`.
- **Which Azure compute** — Azure Container Apps for serverless/scale-to-zero APIs, AKS when you need full K8s control, App Service for simple lift-and-shift.
- **Liveness vs readiness probe** — Liveness restarts a wedged process; readiness pulls the pod out of the load balancer while dependencies are down. Different endpoints.
- **What is HPA** — Horizontal Pod Autoscaler scales replicas on a metric; for LLM apps scale on in-flight requests or queue depth, because CPU stays low while waiting on the API.
- **What is KEDA** — Event-driven autoscaling on queue length (Service Bus, Kafka, Redis) including scale-to-zero — the right fit for batch ingestion workers.
- **Graceful shutdown** — Handle SIGTERM, stop accepting traffic, drain in-flight LLM calls, then exit; set `terminationGracePeriodSeconds` above your longest request.
- **Deployment strategy** — Blue/green or canary with automatic rollback on error-rate and latency SLOs; for prompts, ship behind a flag and A/B on quality metrics.
- **Where do secrets live** — Azure Key Vault surfaced via managed identity or the CSI driver; never in the image, env files, or git.
- **Stateless requirement** — Keep pods stateless: sessions in Redis, agent checkpoints in Postgres, files in Blob — so any replica can serve any request.

**Security, cost, observability**

- **OWASP LLM Top 10 (2025), in order** — LLM01 prompt injection, LLM02 sensitive information disclosure, LLM03 supply chain, LLM04 data and model poisoning, LLM05 improper output handling, LLM06 excessive agency, LLM07 system prompt leakage, LLM08 vector and embedding weaknesses, LLM09 misinformation, LLM10 unbounded consumption.
- **What is improper output handling** — Piping model output into SQL, shell, or HTML unescaped — classic RCE/XSS. Treat LLM output as untrusted user input.
- **What is unbounded consumption** — Denial-of-wallet: unlimited tokens, loops, or retries. Fix with `max_tokens`, iteration caps, per-tenant budgets, and rate limits.
- **How do you defend prompt injection** — Separate instruction and data channels, least-privilege tools, allowlists, output validation, and HITL for any irreversible action. No prompt alone is a defence.
- **How do you handle PII** — Redact before sending to the model (Presidio or similar), tokenize identifiers, keep raw data in your own store, and log redacted prompts only.
- **What do you monitor for a GenAI service** — p50/p95 latency and TTFT, tokens in/out, cost per request and per tenant, error and 429 rates, retrieval recall, and answer-quality samples.
- **How do you control cost** — Route to the cheapest capable model, cache prompts and embeddings, rerank instead of stuffing context, cap output tokens, and batch offline work.
- **How do you roll out a prompt change** — Version prompts in git, evaluate on a golden set in CI, canary to a traffic slice, and watch quality metrics before full rollout.
- **What is LLMOps** — Versioning prompts/models/indexes, offline eval gates in CI, online tracing and feedback capture, drift monitoring, and safe rollback.

---

## 8. Cheat Tables

### 8.1 Temperature / top_p by task

| Task | temperature | top_p | Note |
|---|---|---|---|
| Extraction, classification, routing | 0.0 | 1.0 | Also enable strict JSON schema |
| Tool/function calling in an agent | 0.0 | 1.0 | Non-determinism here breaks trajectories |
| SQL / code generation | 0.0–0.2 | 1.0 | Validate by parsing, not by reading |
| Grounded RAG answer | 0.0–0.3 | 1.0 | Faithfulness over fluency |
| Summarization | 0.2–0.4 | 1.0 | Higher drifts into invention |
| General chat assistant | 0.5–0.7 | 1.0 | Default product setting |
| Marketing / creative copy | 0.8–1.0 | 0.9 | Raise temperature first; clamp top_p only if the tail goes incoherent |
| Brainstorm N distinct ideas | 1.0 | 0.95 | Or sample n>1 at temp 0.8 |

### 8.2 Chunk size by document type

| Doc type | Chunk size | Overlap | Splitter |
|---|---|---|---|
| FAQ / Q&A pairs | 1 pair (100–200 tok) | 0 | Per-item, no splitting |
| Policy / HR / manual prose | 400–800 tok | 10–15% | Recursive or semantic |
| Legal contracts | 1 clause (500–1000 tok) | ~10% | Structural, by clause number |
| Technical docs / markdown | By H2/H3 section | 10% | Header-aware structural |
| Research papers | By section, 600–1000 tok | 10% | Structural + parent-document |
| Source code | 1 function/class (200–500 tok) | 0 | AST / language-aware |
| Slides | 1 slide | 0 | Keep slide title as metadata |
| Tables / CSV | Row groups, header repeated | 0 | Serialize to markdown rows |
| Chat / call transcripts | 5–10 turns | 1–2 turns | Sliding window, speaker-tagged |
| Emails / tickets | 1 thread, split if >1000 tok | 10% | Keep subject + participants |

### 8.3 HNSW parameters vs recall / latency / RAM

| Knob | Typical | ↑ effect on recall | ↑ effect on latency | ↑ effect on RAM | When set |
|---|---|---|---|---|---|
| `M` | 16 (default), 32–64 for high-dim | ↑↑ | ↑ | ↑↑ (`≈ M×2×4` B/vector) | Build |
| `ef_construction` | 100–400 | ↑ (better graph) | build time only | none at query | Build |
| `ef_search` | 40–400 (≥ k) | ↑↑ | ↑↑ | none | Query — tune this first |
| `k` | 20–50 before rerank | n/a | ↑ | none | Query |

Rule: recall too low → raise `ef_search` (free, instant). Still low → rebuild with higher `M`.

### 8.4 Framework selection

| Need | Pick | Why |
|---|---|---|
| Simple single call / streaming endpoint | Plain `openai` SDK | No abstraction tax, easiest to debug |
| Stateful agent, branching, HITL, resume | LangGraph | Typed state, checkpointers, `interrupt()`, streaming |
| RAG-heavy ingestion + retrieval | LlamaIndex | Best loaders, node/parent abstractions, query engines |
| Prompt/chain composition, model swapping | LangChain (LCEL runnables), 1.x current, 0.3 still everywhere | Runnables, wide integrations; v1 adds `create_agent` on top of LangGraph |
| Quick role-based team demo | CrewAI | Roles/tasks in a few lines; less control |
| Conversational multi-agent research | AutoGen | Group chat patterns |
| .NET/Azure enterprise shop | Semantic Kernel | First-class Azure and C# parity |
| Reusable tool servers across clients | MCP servers | Write the connector once, any client uses it |

### 8.5 Prompt vs RAG vs fine-tune

| Dimension | Prompt engineering | RAG | Fine-tuning |
|---|---|---|---|
| Solves | Format, reasoning style | Missing/fresh knowledge | Behaviour, tone, domain format |
| Setup time | Minutes | Days | Weeks (data is the work) |
| Cost | Free | Infra + per-query retrieval | Training + hosting adapters |
| Data freshness | n/a | Instant (re-index) | Stale until retrained |
| Citations | No | Yes | No |
| Per-user access control | No | Yes (metadata filters) | No |
| Prompt length | Grows | Grows (context) | Shrinks |
| Try order | 1st | 2nd | 3rd — and usually with RAG, not instead |

### 8.6 LLM API error code → action

| Code | Meaning | Action |
|---|---|---|
| 400 | Bad request / content filter / too many tokens | Fix payload; on Azure inspect `content_filter` result; trim context |
| 401 | Bad or missing key/token | Rotate key or refresh the Entra token; do not retry blindly |
| 403 | No permission / region or model not enabled | Fix RBAC role or model access approval |
| 404 | Model or deployment name wrong | On Azure, `model` must be the **deployment** name |
| 408 / timeout | Request too slow | Lower `max_tokens`, stream, raise client timeout |
| 409 | Conflict (e.g. duplicate job) | Treat as already-done if idempotent |
| 413 | Payload too large | Chunk the input; check embedding batch size |
| 422 | Schema/validation failure | Fix your JSON schema or tool definition |
| 429 | Rate limit / quota (TPM) exhausted | Backoff with jitter, honour `Retry-After`, spill to a second region, request quota |
| 500 | Provider error | Retry up to 3x with backoff |
| 503 | Overloaded / model busy | Backoff, failover deployment, degrade to a smaller model |

Retry only 408/429/5xx (409 is not a retry — re-check state and treat as done if idempotent). Never retry 400/401/403/404/422 — you will just burn quota. Note 422 is typically *your* FastAPI validation layer, not the provider.

### 8.7 DSA complexity table (whiteboard-ready)

| Pattern | Time | Space | Signal in the question |
|---|---|---|---|
| Hash map / set lookup | O(n) | O(n) | "seen before", "two sum", "duplicates" |
| Two pointers | O(n) | O(1) | Sorted array, pair sum, in-place removal |
| Sliding window | O(n) | O(k) | "longest/shortest substring/subarray with…" |
| Prefix sum | O(n) | O(n) | Range sums, subarray sums equal to k |
| Binary search | O(log n) | O(1) | Sorted input, or "minimum feasible value" |
| Sorting | O(n log n) | O(n) | Grouping, intervals, top-k by order |
| Heap top-k | O(n log k) | O(k) | "k largest / k most frequent" |
| BFS / DFS on graph | O(V+E) | O(V) | Grid, islands, shortest unweighted path |
| Dijkstra | O(E log V) | O(V) | Weighted shortest path |
| Topological sort | O(V+E) | O(V) | Dependencies, course schedule |
| 1-D DP | O(n) | O(n)→O(1) | Fibonacci-shaped, house robber, climb stairs |
| 2-D DP | O(n·m) | O(n·m) | Edit distance, LCS, knapsack |
| Backtracking | O(2ⁿ)/O(n!) | O(n) | Permutations, subsets, N-queens |
| Trie | O(L) per op | O(alphabet·N) | Prefix search, autocomplete |
| Union-Find | ~O(α(n)) | O(n) | Connected components, cycle detection |

State complexity **before** you code — interviewers score that explicitly.

---

## 9. Buzzwords To Drop Naturally

Use these in sentences, not as a list. Two or three per answer is right; ten is a red flag.

- **RAG:** hybrid retrieval, reciprocal rank fusion, cross-encoder reranking, parent-document retrieval, contextual retrieval, chunk-boundary loss, grounding and citation enforcement, golden eval set, faithfulness vs answer relevancy.
- **Agents:** ReAct loop, tool schema design, trajectory evaluation, supervisor topology, checkpointer and thread id, human-in-the-loop interrupt, least-privilege tooling, loop guards, context engineering.
- **LLM:** KV cache, prompt caching, TTFT, structured outputs with strict schema, token budget, self-consistency, distillation to a smaller model.
- **Platform:** ASGI, dependency injection, idempotency key, backpressure, exponential backoff with jitter, p95 latency, blue/green rollout, scale-to-zero with KEDA, managed identity, PTU vs TPM.
- **Quality:** offline eval gate in CI, LLM-as-judge with a rubric, canary on a traffic slice, cost per resolved request, drift monitoring, OWASP LLM Top 10.

---

## 10. 10 Questions To Ask Them

1. Is this team building a customer-facing GenAI product or internal enterprise copilots — and who are the users?
2. What's live in production today versus still at POC stage?
3. Azure OpenAI, OpenAI direct, or open-weight models — and what drove that choice?
4. Which vector store are you on, and roughly what corpus size and query volume?
5. How do you currently evaluate answer quality — golden sets, LLM-as-judge, human review?
6. Which agent framework is standard here, or is it hand-rolled orchestration?
7. What does the deployment path look like — AKS, Container Apps, or something else — and how often do you release?
8. What's the biggest technical pain right now: retrieval quality, latency, cost, or hallucination?
9. How is the team structured — do engineers own the full stack from ingestion to API, or is it split?
10. What would you want the person in this role to have delivered in the first 90 days?

---

## 11. Red Flags / Do NOT Say

- **"I use `openai.ChatCompletion.create`"** — that is pre-1.0 and removed. Say `client.chat.completions.create(...)`.
- **"`from langchain.llms import OpenAI`"** — legacy (and a completion, not chat, model). Say `from langchain_openai import ChatOpenAI` — the partner-package layout since langchain 0.2 and still correct in 1.x.
- **"RAG eliminates hallucination"** — it reduces it. Say grounding + citations + relevance thresholds + eval reduce it measurably.
- **"I'd fine-tune to add the company's documents"** — wrong instinct, and the classic filter question. Knowledge → RAG.
- **"I'd just increase the context window and put everything in"** — costly, slower, and lost-in-the-middle degrades accuracy.
- **"Prompt engineering stops prompt injection"** — it does not. Say least privilege, output validation, and HITL on writes.
- **"I'd use a multi-agent system"** for a simple linear task — signals cargo-culting. Start with one agent or a plain workflow.
- **"LangChain does it for me"** — never let a framework be your explanation. Explain the mechanism, then name the tool.
- **Bluffing a number or an API signature** — say "I'd check the exact parameter, but the shape is…". Interviewers forgive uncertainty, not invention.
- **Silence at the whiteboard** — narrate. Brute force → complexity → optimization → edge cases → code. Thinking out loud is the graded artifact.
- **Trashing a previous employer or a technology** — always frame as trade-offs.
- **"I don't do DSA, I only do AI"** — Virtusa L1 will still ask a coding question. Say "let me talk through the approach first".

---

## 12. Rapid-Fire (last 10 min before you walk in)

- **RAG or fine-tune for company docs?** — RAG. Fine-tune only for tone/format.
- **Chunk size default?** — 400–800 tokens, 10–15% overlap, then tune on an eval set.
- **Retrieval quality fix, in order?** — Hybrid search → rerank → better chunking → query rewriting.
- **RRF constant?** — k = 60; score = Σ 1/(60 + rank).
- **Embedding dims?** — 1536 small / 3072 large; cosine similarity.
- **Which HNSW knob at query time?** — `ef_search`. Raise it for recall, no rebuild.
- **1M vectors × 1536 dims RAM?** — ~6 GB raw plus graph overhead.
- **temperature for tool calling?** — 0.
- **GPT-4o context / max output?** — 128K context, 16,384 output tokens (per-model; newer families are larger).
- **Tokens per word?** — ~1.3 tokens per English word, ~4 characters per token.
- **What is the KV cache for?** — Avoid recomputing attention over the prefix each generated token.
- **Azure `model` parameter?** — The deployment name, not the model name.
- **Azure auth without keys?** — Managed identity via `DefaultAzureCredential` + bearer token provider.
- **429 response?** — Backoff with jitter, honour `Retry-After`, fail over region.
- **Agent infinite loop guard?** — Max iterations + wall-clock deadline + token budget + repeat detection.
- **How does function calling execute?** — Your code runs the tool; the model only emits name plus JSON arguments.
- **LangGraph state append trick?** — `Annotated[list, add_messages]` reducer.
- **How do you pause for a human?** — `interrupt()` in a node, resume with `Command(resume=...)`, state held by the checkpointer.
- **What is MCP?** — JSON-RPC standard exposing tools/resources/prompts to any client; stdio or streamable HTTP.
- **GIL in one line?** — One thread runs bytecode at a time; released on I/O, so async and threads still help.
- **Pydantic v2 method names?** — `model_validate`, `model_dump`, `field_validator`, `ConfigDict`.
- **`async def` vs `def` route?** — `def` goes to a threadpool; never block inside `async def`.
- **Biggest LLM security risk in agents?** — Excessive agency plus prompt injection through tool output.
- **First thing you say to any coding question?** — Restate the problem, state the brute force and its complexity, then optimize.

### If you only remember 20 things

1. **RAG for knowledge, fine-tune for behaviour, prompt first.** This single answer appears in almost every round.
2. **Hybrid (BM25 + dense) + cross-encoder rerank** is the default production retrieval stack, fused with RRF at k=60.
3. **Retrieve wide (k=20–50), rerank narrow (3–8)** into the prompt, best chunks at the edges.
4. **Chunk 400–800 tokens, 10–15% overlap**, structural splitting where documents have structure.
5. **Bad answer + right context = prompt problem. Bad answer + missing context = retrieval problem.** Triage in that order.
6. **Evaluate with a golden set** of 100–200 real questions; recall@k and nDCG for retrieval, faithfulness and answer relevancy for generation.
7. **Embeddings: 1536 dims, cosine, never mix models** in one index. Re-embed everything on a model change.
8. **`ef_search` is the runtime recall dial**; `M` and `ef_construction` are build-time.
9. **temperature 0 for anything structured** — extraction, routing, tool calls, SQL.
10. **Structured outputs with strict JSON Schema** beat "please return JSON" every time.
11. **Your code executes tools, not the model.** Tool design (few, typed, idempotent, compact returns) is most of agent quality.
12. **Prefer a workflow over an agent; prefer one agent over many.** Justify autonomy, don't assume it.
13. **Agent loop guards:** max iterations, deadline, token budget, repeated-call detection — say all four.
14. **Checkpointer + thread_id** gives you persistence, resume, time-travel debugging, and human-in-the-loop.
15. **Prompt injection is defended by architecture** — least privilege, output validation, HITL on writes — not by prompt wording.
16. **Azure: deployment name goes in `model`, managed identity for auth, TPM quota, 429 → backoff + failover, PTU for reserved capacity.**
17. **FastAPI = ASGI + pydantic + `Depends`;** never block the event loop; stream tokens over SSE.
18. **Pydantic v2 names:** `model_validate`, `model_dump`, `field_validator`, `ConfigDict` — and it validates every LLM JSON you accept.
19. **Cost levers:** route to a small model, cache prompts, rerank instead of stuffing, cap output tokens.
20. **Narrate everything at the whiteboard**: restate → brute force + complexity → optimize → edge cases → code → test. The reasoning is what they score.

**Walk-in reminders:** answer first then elaborate, quantify with real numbers, say "I don't know, here's how I'd find out" when true, and bring every abstract answer back to something you have actually built.
