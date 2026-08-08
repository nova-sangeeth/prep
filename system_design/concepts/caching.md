# Caching

> Store hot data close to the reader; the hard parts are invalidation, stampedes, and hot keys.

## What it is & why it matters
A cache is a fast, usually in-memory store of a subset of data, placed to cut latency and offload the source of truth. It exploits locality: a small hot set serves most reads. Caching is the single biggest lever in read-heavy systems — it turns a ~10 ms DB hit into a ~0.5 ms memory hit and can absorb 90%+ of reads. The cost is a second copy of data that can go stale, so the whole discipline is really about consistency and failure behavior, not the happy-path hit.

## How it works
**Where to cache** (each layer cuts more load but is harder to invalidate):
```
client/browser → CDN/edge → reverse-proxy → app (local + distributed) → DB buffer pool → disk
   (private)     (static/   (full-page,     (Redis/Memcached;   (page cache)
                  geo)        ESI)           hot objects)
```
- **Client**: HTTP cache headers (`Cache-Control`, `ETag`), avoids the trip entirely.
- **CDN/edge**: static assets and cacheable API responses near the user.
- **App tier**: local in-process (fastest, per-node, risks inconsistency) and a shared distributed cache (Redis/Memcached) for cross-node hits.
- **DB**: buffer pool / query cache — present but least controllable.

**Read patterns**:
- **Cache-aside (lazy)**: app checks cache; on miss, reads DB, populates cache, returns. Most common, resilient (cache down ≠ data loss), but first read is a miss and stale risk exists.
- **Read-through**: cache library fetches from DB on miss transparently. Cleaner app code; cache is in the critical path.

**Write patterns**:
- **Write-through**: write cache + DB synchronously. Cache always fresh, higher write latency, wasted writes for cold data.
- **Write-back (write-behind)**: write cache, flush to DB async/batched. Fast writes, absorbs bursts; risk of data loss on cache crash and complex consistency.
- **Write-around**: write straight to DB, skip cache; cache fills on read. Good for write-once-read-rarely; recent writes miss.

## Tradeoffs / variants
| Strategy | Freshness | Write latency | Failure risk | Fits |
|---|---|---|---|---|
| Cache-aside | Can be stale | Low | Low (graceful) | General read-heavy |
| Read-through | Can be stale | Low | Cache in path | Clean abstraction |
| Write-through | Fresh | Higher | Low | Read-after-write needs |
| Write-back | Eventual to DB | Lowest | Data loss on crash | Write-heavy, burst |
| Write-around | Fresh-on-read | Low | Cold reads miss | Write-once-read-rare |

**Eviction** (cache is bounded): **LRU** (evict least-recently-used; cheap, default), **LFU** (least-frequently-used; better for skewed popularity, needs frequency counts/decay), **FIFO** (simple, ignores reuse), **TTL** (expire by age; bounds staleness regardless of access). Often combined: TTL for staleness + LRU/LFU for capacity.

## When to use · pitfalls
- **Cache invalidation** ("one of two hard things"): TTL (simple, bounded staleness), explicit delete/update on write (fresh but needs every writer to remember), or versioned keys (`user:42:v7` — write bumps version, old entries age out). Pick based on tolerance for staleness vs write complexity.
- **Thundering herd / cache stampede**: a hot key expires and thousands of concurrent misses hammer the DB at once. Fixes: **request coalescing / single-flight** (one fetch per key, others wait), **probabilistic early expiration** (refresh slightly before TTL), **stale-while-revalidate** (serve stale, refresh in background), randomized TTL jitter, and a mutex/lock on repopulation.
- **Hot keys**: one key (celebrity, viral post) overwhelms a single cache node. Fixes: replicate the key across nodes, add a local in-process cache in front, or shard the key (`post:99:shard{0..n}`).
- **Cache penetration**: lookups for keys that don't exist bypass the cache to the DB every time — cache negative results (with short TTL) or use a Bloom filter.
- **Consistency**: a cache is a second source of truth; under writes, define whether reads can be stale and for how long. Dual-write (cache + DB) races — prefer invalidate-then-write or write-through.
- Pitfalls: caching low-hit-rate data (pure overhead), unbounded local caches (OOM), no metrics (track hit ratio, evictions, latency), and treating the cache as durable storage.

## Interview soundbites
- "Cache-aside is the default — app owns the logic, and a cache outage degrades, not breaks."
- "Write-through trades write latency for read-after-write freshness; write-back trades durability for write speed."
- "TTL bounds staleness; LRU/LFU bound size — most caches use both."
- "Stampede control = single-flight plus stale-while-revalidate plus TTL jitter."
- "A hot key is a single-node problem — fix it with replication or a local front cache, not a bigger cluster."
- "Cache the misses too, or non-existent keys penetrate straight to your database."
