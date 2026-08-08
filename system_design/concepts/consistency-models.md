# Consistency Models

> A spectrum from strong (acts like one copy) to eventual (converges later); quorums (R+W>N) let you dial where you sit.

## What it is & why it matters
A consistency model is the contract a data store gives about *when and in what order* writes become visible to readers across replicas. It defines what stale, out-of-order, or conflicting reads are *possible*, so you can reason about correctness. It matters because replication makes "the latest value" ambiguous, and choosing too strong wastes latency/availability while too weak ships subtle bugs (lost updates, a user not seeing their own post). Models form a hierarchy: stronger ones forbid more anomalies but cost more coordination.

## How it works
From strongest to weakest (each is implied by the ones above it):
- **Strong / linearizable**: the system behaves as if there's a single copy; once a write commits, *every* subsequent read (real-time order) sees it. Requires consensus/coordination → higher latency, lower availability under partition. Use for money, locks, unique constraints.
- **Sequential**: all clients see operations in *some* single global order, consistent per-client, but not tied to real-time wall clock.
- **Causal**: operations that are causally related (A happened-before B) are seen in that order by everyone; concurrent (unrelated) ops may be seen in different orders. Preserves "reply appears after the comment it answers." Achievable without global coordination (version vectors) → a sweet spot.
- **Eventual**: if writes stop, all replicas *eventually* converge to the same value; no ordering guarantee meanwhile. Cheapest, most available; readers may see stale or out-of-order data.

**Client-centric session guarantees** (often what users actually need; layered on eventual):
- **Read-your-writes (read-after-write)**: you always see your own prior writes (even if others don't yet). Fixes "I posted but my feed is empty."
- **Monotonic reads**: once you've seen a value, you never see an older one (no going back in time across replicas).
- **Monotonic writes**: your writes are applied in the order you issued them.
- **Writes-follow-reads (causal-ish)**: a write that depends on a read you did is ordered after the value you read.

```
Strong ─────────────► weaker ─────────────► Eventual
linearizable  sequential  causal  | session guarantees |  eventual
  (consensus)            (version vectors)   (read-your-writes,
   high coord                                 monotonic reads)   low coord
```

## Tradeoffs / variants
| Model | Guarantee | Coordination cost | Use for |
|---|---|---|---|
| Linearizable | Real-time single-copy order | High (consensus) | Balances, locks, leader election |
| Sequential | Some global order | High | Replicated state machines |
| Causal | Cause-before-effect | Medium (version vectors) | Comments, messaging, collab |
| Read-your-writes | See own writes | Low (route/sticky) | Profiles, post-then-view |
| Monotonic reads | Never go backwards | Low (pin replica) | Timelines, paging |
| Eventual | Converges if writes stop | Lowest | Likes, counters, telemetry |

## When to use · pitfalls
- **Quorums (R + W > N)**: in leaderless/replicated systems with N replicas, require W replicas to ack a write and R to be read. If **R + W > N**, the read set and write set overlap, so a read is guaranteed to touch at least one replica with the latest write → strong-ish consistency. Tune the knobs:
  - `W=N, R=1`: fast reads, slow/fragile writes (any replica down blocks writes).
  - `W=1, R=N`: fast writes, slow reads.
  - `W=R=⌈(N+1)/2⌉` (e.g., N=3 → W=R=2): balanced quorum, tolerates one failure. This is the common default.
  - `R+W ≤ N`: explicitly eventual (e.g., `W=R=1`) — fast, available, stale reads possible.
  - Caveat: quorum overlap guarantees a *fresh copy is read*, not that you pick it correctly without read-repair/versioning, and concurrent writes still need conflict resolution (version vectors, LWW).
- **Pick the weakest model that's still correct** — coordination is latency and availability. Most "needs strong consistency" turns out to need only read-your-writes + monotonic reads, which are cheap (sticky routing / leader reads).
- Pitfalls: assuming eventual consistency is fine without session guarantees (users notice their own missing writes); LWW silently dropping concurrent updates (lost update); clock skew making timestamp-based ordering wrong; conflating consistency (replica agreement) with isolation (concurrency control in transactions — different axis); believing quorum reads are linearizable (need extra care — read repair, no concurrent in-flight writes).

## Interview soundbites
- "Consistency models are a spectrum from linearizable (acts like one copy) to eventual (converges later); each step down trades a guarantee for latency and availability."
- "Most apps don't need strong consistency — they need read-your-writes and monotonic reads, which are cheap to provide."
- "Causal consistency keeps cause-before-effect without global coordination — great for comments and chat."
- "R + W > N forces the read and write sets to overlap, so you read at least one up-to-date replica."
- "N=3, W=2, R=2 is the workhorse quorum: balanced and survives one node down."
- "Last-write-wins is simple but silently loses concurrent updates — use version vectors when that matters."
