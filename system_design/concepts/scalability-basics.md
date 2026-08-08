# Scalability Basics

> Scale out, not up; keep services stateless; know your latency numbers cold.

## What it is & why it matters
Scalability is the ability to handle growing load by adding resources, ideally with cost growing no faster than load. Two axes matter and are often confused:
- **Latency**: time for one operation (e.g., p99 = 120 ms). A property of a single request.
- **Throughput**: operations per unit time (e.g., 50k QPS). A property of the system.
They are not the same and can trade off: batching raises throughput but adds latency; aggressive parallelism can cut latency while hurting throughput via overhead. Interviews care because every scale number you estimate maps to one of these, and they drive whether you replicate, shard, cache, or queue.

## How it works
**Vertical scaling (scale up)**: bigger box — more CPU/RAM/IO. Simple, no app changes, keeps strong consistency easy. But there's a hard ceiling, cost grows superlinearly, and the box is a single point of failure.

**Horizontal scaling (scale out)**: more boxes behind a load balancer. Near-linear capacity, fault tolerance, commodity hardware. Cost: you must handle distribution — coordination, data partitioning, and especially **state**.

The enabler for scale-out is **statelessness**. A stateless service holds no per-client data between requests; any node can serve any request, so you can add/remove nodes freely and a node death loses nothing. Push state outward:

```
        ┌──────────────┐
client → │ Load Balancer│
        └──────┬───────┘
   ┌──────┬────┼────┬──────┐   stateless app tier
  app1   app2 app3 app4 ...    (add/remove freely)
   └──────┴────┼────┴──────┘
        ┌──────┴───────┐
        │ shared state │  ← Redis (sessions), DB, blob store
        └──────────────┘
```
Session data → Redis/token; uploads → object store; locks → distributed lock service. Now the app tier is a pure function of (request, shared state).

## Tradeoffs / variants
| | Vertical (up) | Horizontal (out) |
|---|---|---|
| Ceiling | Hard, single-machine limit | Effectively unbounded |
| Fault tolerance | None (SPOF) | Built-in via redundancy |
| Complexity | Low | High (distribution, consistency) |
| Cost curve | Superlinear | ~Linear (commodity HW) |
| Consistency | Trivial | Requires coordination |
| Best for | DBs, quick wins, low scale | Web/app tiers, big scale |

## When to use · pitfalls
- **Use vertical first** when scale is modest or to buy time; it's the cheapest engineering effort. Scale out once you hit the ceiling or need HA.
- **Stateful tiers** (databases) scale out hardest — that's why sharding/replication get their own treatment.
- Pitfalls: hidden state (in-memory caches, sticky local files) that breaks scale-out; sticky sessions that pin load and defeat the LB; assuming linear scaling — coordination, lock contention, and the DB become the real ceiling (Amdahl / Universal Scalability Law).
- Watch **tail latency**: p99 dominates user-visible behavior in fan-out systems (one slow shard slows the whole request). Optimize p99, not the mean.

## Latency numbers every engineer should know
Order-of-magnitude (the relative scale is the point):
| Operation | Time |
|---|---|
| L1 cache reference | ~1 ns |
| Branch mispredict | ~3 ns |
| L2 cache reference | ~4 ns |
| Mutex lock/unlock | ~17 ns |
| Main memory (RAM) reference | ~100 ns |
| Compress 1 KB (cheap) | ~2 µs |
| Read 1 MB sequentially from RAM | ~3 µs |
| SSD random read | ~16 µs |
| Read 1 MB from SSD | ~50 µs |
| Round trip within same datacenter | ~500 µs |
| Read 1 MB from disk (HDD) | ~1-2 ms |
| Disk seek (HDD) | ~2-10 ms |
| Round trip CA ↔ Netherlands | ~150 ms |

Derived rules of thumb: **RAM is ~100,000× faster than disk seek; SSD ~10-100× faster than HDD; cross-region RTT (~150 ms) dwarfs everything in-DC.** Sequential >> random for both disk and SSD. These justify caching in RAM, keeping data local to a region, and batching to amortize round trips.

## Interview soundbites
- "Scale up to buy time, scale out to survive; the app tier should be stateless so any node serves any request."
- "Latency is per-request, throughput is system-wide — batching trades one for the other."
- "RAM is ~100,000× faster than a disk seek, which is the whole reason caches exist."
- "Optimize p99, not the mean — in fan-out systems the slowest shard sets the response time."
- "Cross-region RTT is ~150 ms; keep the hot path inside one datacenter."
- "Statelessness is the precondition for horizontal scaling — push sessions to Redis, files to blob store."
