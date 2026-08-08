# Design a Distributed Rate Limiter

## 1. Requirements
- **Functional:**
  - `allow(key, rule) -> {allowed: bool, remaining, retryAfter}` where `key` is a client identifier (user ID, API key, IP) and `rule` is e.g. "100 req / minute".
  - Support multiple, composable rules per key (per-second burst + per-minute sustained) and per-endpoint limits.
  - Return standard headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.
- **Non-functional:**
  - **Scale:** must handle the full request volume of the services it protects (100k+ checks/s).
  - **Latency:** the limiter is on every request's critical path → p99 added latency < 1-2ms. It must be cheaper than the work it protects.
  - **Availability:** highly available; **fail-open vs fail-closed** is a deliberate policy choice (see tradeoffs).
  - **Consistency:** "approximately correct" globally is acceptable; small over-admission under partition is tolerable, hard exactness is not worth the latency.

## 2. Back-of-envelope estimates
- Protect a fleet doing **100k req/s**. Each request = 1 limiter check → **100k limiter ops/s**.
- Each check is a Redis round trip: a counter read+increment. A single Redis node handles ~100k ops/s comfortably; at higher scale or with multi-rule checks (2-3 ops each → 200-300k ops/s) we shard by key.
- **Memory:** one counter per active key. 10M active keys × ~100 bytes (key + counter + window state) ≈ **1 GB** — trivially fits in RAM. Sliding-window-log is heavier (stores timestamps): a key doing 100 req/window × 8 bytes × 10M keys ≈ 8 GB; prefer counter-based algorithms to keep memory flat.
- **Network:** at 100k ops/s with ~50-byte requests/responses, ~5-10 MB/s to Redis — negligible.

## 3. API
```
// Library/sidecar call
allow(key: string, limit: int, windowSec: int) -> Decision
  Decision { allowed: bool, remaining: int, resetAt: ts, retryAfter: int }

// As a service (gRPC)
rpc ShouldAllow(RateLimitRequest) returns (RateLimitResponse)
  RateLimitRequest  { domain, descriptors[] }   // Envoy ratelimit-style
  RateLimitResponse { overallCode, statuses[] }
```

## 4. High-level design
```
                 +------------------+
  request -----> | API Gateway /    |   (rate-limit at the edge, before
                 | Service + LB     |    expensive downstream work)
                 +---------+--------+
                           | allow(key, rule)
                  +--------v---------+
                  | Rate Limiter     |  (library, sidecar, or service)
                  |  - rule lookup   |
                  |  - algorithm     |
                  +--------+---------+
                           | atomic INCR / Lua script
                  +--------v---------+
                  |  Redis cluster   |  (sharded by key, counters/state)
                  +------------------+
```
- **Placement:** as far upstream as possible — at the **API gateway / edge**, so rejected traffic never reaches application servers or the DB. Embed as a library for lowest latency, or as a sidecar/central service for centralized rules and language-agnostic enforcement.
- **Rate Limiter:** resolves which rule(s) apply, runs the algorithm against shared state.
- **Redis:** holds counters/window state, shared across all gateway instances so the limit is *global*, not per-instance.

## 5. Data model & storage choice
```
Token bucket (per key):
  rl:{key} -> HASH { tokens: float, lastRefill: ts }   TTL = idle expiry

Fixed/sliding window:
  rl:{key}:{windowEpoch} -> INT counter, TTL = 2*window
```
**Choice: Redis (in-memory) as shared state.**
Why: rate limiting is high-frequency read-modify-write on tiny values where **latency and atomicity** dominate — exactly Redis's strength. It offers atomic `INCR`/`EXPIRE`, single-threaded execution (no per-key locks needed), and Lua scripts for multi-step atomic logic. A durable disk-backed DB would add unacceptable latency; we don't need durability because losing a counter just resets a window — a benign, self-healing error. TTLs auto-evict idle keys, keeping memory bounded.

## 6. Deep dives

### Algorithm choice
- **Fixed window counter:** `INCR rl:{key}:{minute}`, reject above limit. Cheap, O(1), tiny memory. **Flaw:** boundary burst — a client can send `limit` at 0:59 and another `limit` at 1:00, i.e. 2× the limit across the window edge.
- **Sliding window log:** store a sorted set of request timestamps, count those within the window. Exact, but **O(N) memory per key** and heavier ops — expensive at scale.
- **Sliding window counter (chosen for most cases):** weighted blend of current + previous fixed window: `count = prevWindow * overlapFraction + currWindow`. Smooths the boundary-burst flaw at O(1) memory. Approximate but good enough.
- **Token bucket (chosen when bursts are desired):** bucket of `B` tokens refilled at `r`/s; each request consumes one. Allows controlled bursts up to `B` while bounding the sustained rate — ideal for APIs that want to permit short spikes. Leaky bucket is the same idea but enforces a strictly smooth output rate (queue-based).
- **Decision:** token bucket for user-facing APIs (burst-friendly, intuitive `limit`+`burst`), sliding-window counter when you want strict smoothing with minimal memory.

### Atomicity & race conditions
- The naive `GET; if < limit then INCR` is a **read-then-write race**: under concurrency, N gateway instances all read `count=99`, all allow, all increment → over-admission. Fixes:
  - **Atomic `INCR`** (then compare result) instead of GET-then-SET — the increment and the new value come back in one atomic op.
  - **Lua script** for multi-step algorithms (token bucket refill math, sliding-window weighting): Redis runs the whole script atomically on one thread, eliminating the race without distributed locks.
  - This is why Redis's single-threaded model is a feature here, not a limitation.

### Distributed sync issues
- **Sharding:** partition counters by `key` so each key's state lives on exactly one shard → no cross-node coordination per check; the limit stays globally consistent for that key.
- **Local-cache optimization at scale:** at extreme volume, doing a Redis round trip per request is costly. Use **local token buckets** that periodically sync/reconcile with the central store (each instance gets a slice of the budget). Trades exactness (brief over/under-admission) for latency and resilience. Envoy/Stripe-style designs do this.
- **Clock skew:** window math depends on time; prefer Redis server time (single clock) over distributed client clocks to avoid skew across instances.

## 7. Bottlenecks & scaling
- **First to break: Redis throughput / hot keys.** A single very active key (one giant tenant) concentrates load on one shard. Fixes: local per-instance buckets that sync periodically; or split a hot key's budget across N sub-keys and sum.
- **Redis as SPOF:** run Redis in cluster mode with replicas; on failover, counters reset — acceptable (brief over-admission). Decide **fail-open** (if Redis is down, allow traffic — protects availability) vs **fail-closed** (reject — protects the backend). Most pick fail-open for the limiter, fail-closed for critical abuse-prevention paths.
- **Latency tail:** co-locate Redis with gateways (same AZ); pipeline multiple rule checks into one round trip.
- **Rule explosion:** many per-endpoint rules → multiple ops per request. Batch them in a single Lua script.

## 8. Tradeoffs / talking points
- Algorithm is a memory-vs-accuracy-vs-burst tradeoff: fixed window (cheap, boundary bug) → sliding counter (cheap, smooth, approximate) → sliding log (exact, expensive) → token bucket (burst-friendly).
- Atomicity is the crux: use `INCR`/Lua, never GET-then-SET, or you over-admit under concurrency.
- Global vs local enforcement: central Redis = accurate but a round trip; local buckets + periodic sync = fast and resilient but approximate.
- Fail-open vs fail-closed is a business decision — availability of the protected service vs. guaranteed protection.
- Put the limiter at the edge so rejected requests cost as little as possible.
- Don't make the limiter durable — counter loss is self-healing; durability would only add latency.
