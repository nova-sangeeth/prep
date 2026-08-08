# Rate Limiting

> Cap request rate per client to protect capacity, ensure fairness, and contain abuse — choose an algorithm by burst tolerance and accuracy needs.

## What it is & why it matters

Rate limiting bounds how many requests a caller (user/API key/IP/tenant) may make
per unit time. It protects backends from overload, enforces quotas/SLA tiers,
ensures fairness across tenants, and blunts abuse (credential stuffing, scraping,
DDoS-lite). Enforce **as early as possible** — at the API gateway / edge — so bad
traffic is rejected before consuming downstream resources. Return **HTTP 429**
with a `Retry-After` header.

## How it works

Common algorithms, in order of sophistication:

```
Token bucket: tokens refill at rate r, cap B.
  [ • • • • ]  request takes 1 token; empty bucket -> reject.
  Allows bursts up to B, steady rate r.

Leaky bucket: requests queue, drain at fixed rate.
  in -> [ | | | ] -> out @ r   (smooths bursts, adds queueing delay)
```

- **Fixed window:** count per calendar window (e.g. 100/min). Simple, but allows
  a **2x burst at the boundary** (100 at 0:59 + 100 at 1:00).
- **Sliding window log:** store timestamp of each request; count those in the
  trailing window. Exact, but memory-heavy (one entry per request).
- **Sliding window counter:** weighted blend of current + previous fixed-window
  counts. Approximates the log with O(1) memory — the common production choice.

## Tradeoffs / variants

| Algorithm | Burst handling | Memory | Accuracy | Notes |
|---|---|---|---|---|
| Token bucket | Allows bursts ≤ B | O(1) per key | Good | Most popular; tune r & B |
| Leaky bucket | Smooths to constant r | O(queue) | Good | Adds latency; shapes traffic |
| Fixed window | Boundary 2x spike | O(1) | Low | Simplest; cheap |
| Sliding log | Exact | O(N requests) | Exact | Costly at scale |
| Sliding counter | Near-exact | O(1) | High | Best memory/accuracy tradeoff |

## When to use · pitfalls

Gateway-level limiting for all public APIs; per-tenant quotas for SaaS tiers;
tighter limits on expensive/auth endpoints (login, search, writes). Use token
bucket when bursts are acceptable, leaky bucket when you must protect a fragile
fixed-capacity downstream.

**Distributed limiting:** with many gateway nodes, a local counter lets a client
exceed the limit N-fold. Centralize state in **Redis**: `INCR key` + `EXPIRE`
(fixed window), or atomic token-bucket logic in a **Lua script** to avoid
read-modify-write races. Trade strict global accuracy for latency — some designs
allow small local buckets synced periodically (slightly leaky but fast).

Pitfalls:
- **Race conditions** under concurrency → use atomic ops (Lua/`INCR`) not GET+SET.
- **Hot keys** (one giant tenant) can hotspot a Redis shard.
- **Identity:** keying on IP punishes users behind NAT/CGNAT and is spoofable;
  prefer API key / user ID where possible.
- **Redis as a dependency:** add a fail-open vs fail-closed decision for outages.
- **Clock skew** across nodes corrupts window math.
- Always return **429 + `Retry-After`** and document limits in response headers
  (`X-RateLimit-Remaining`).

## Interview soundbites
- "Token bucket allows controlled bursts; leaky bucket enforces a constant drain."
- "Fixed window is cheap but lets through a 2x burst at the boundary."
- "Sliding window counter is the sweet spot: O(1) memory, near-exact."
- "Enforce at the gateway so junk traffic dies before it costs you anything."
- "Distributed limiting = centralized counter in Redis with an atomic Lua script."
- "Return 429 with Retry-After; decide fail-open vs fail-closed when Redis is down."
