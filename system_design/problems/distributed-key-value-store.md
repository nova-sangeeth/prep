# Design a Distributed Key-Value Store (Dynamo-style)

## 1. Requirements
- **Functional:** `get(key)` / `put(key, value)` over an opaque blob value. Highly available, horizontally scalable, no single point of failure. Tunable consistency. Handle node failures and network partitions gracefully.
- **Non-functional:**
  - **Scale:** millions of ops/s, petabytes across thousands of commodity nodes; data spread evenly.
  - **Latency:** p99 read/write < 10-20ms (Dynamo's SLA was 99.9th percentile, not average — design to the tail).
  - **Availability:** "always writeable" — prioritize availability over consistency (AP in CAP). Accept conflicts, resolve later.
  - **Consistency:** **eventual**, tunable per-operation via quorum (R/W/N).
  - **Durability:** replicate N ways; survive node and even datacenter loss.

## 2. Back-of-envelope estimates
- **Throughput:** target 1M ops/s. With N=3 replication, a write touches 3 nodes → ~3M internal write ops/s. Spread over, say, 300 nodes → ~10k ops/s/node — comfortable.
- **Storage:** 100 TB logical × 3 replicas = 300 TB physical. At ~4 TB usable/node → ~75 nodes minimum for capacity; more for throughput/headroom.
- **Key distribution:** with virtual nodes (~128-256 vnodes/physical node), load imbalance stays within a few percent even as nodes join/leave.
- **Gossip:** O(nodes) membership entries; gossip converges in O(log N) rounds — trivial bandwidth (KBs/s) even at thousands of nodes.
- **Merkle tree sync:** comparing two replicas of a key range transfers O(differences), not O(keys) — anti-entropy stays cheap when replicas are mostly in sync.

## 3. API
```
get(key)              -> {value(s), context}     // context = version metadata (vector clock)
put(key, value, context) -> ack                  // context from a prior get for causality
delete(key, context)  -> ack                     // tombstone

// coordinator-level knobs (per request or per key space)
N = replication factor, W = write quorum, R = read quorum
```
- `get` may return **multiple sibling values** when there are concurrent conflicting writes; client (or app logic) reconciles and writes back with the merged context.

## 4. High-level design
```
        Client
          │ (any node can coordinate)
          ▼
   ┌─────────────────────────────────────────┐
   │            Consistent Hash Ring           │
   │   ┌────┐   ┌────┐   ┌────┐   ┌────┐       │
   │   │ N1 │   │ N2 │   │ N3 │   │ N4 │  ...  │
   │   └────┘   └────┘   └────┘   └────┘       │
   │   each node: storage engine + vnodes      │
   └─────────────────────────────────────────┘
   Cross-cutting (decentralized, no master):
     • Gossip protocol  → membership + failure detection
     • Replication      → N successor nodes on the ring
     • Hinted handoff   → temp store writes for down nodes
     • Merkle trees     → anti-entropy / replica repair
     • Vector clocks    → causal versioning / conflict detection
```
- **Every node is identical** (no master) — any node can act as **coordinator** for a request, routing to the replica set.
- **Consistent hash ring** maps keys → nodes; each key replicated to its N successors.
- **Gossip** spreads membership and liveness so each node knows the ring without a central registry.
- **Storage engine** per node: local LSM-tree (e.g. log-structured) for high write throughput.

## 5. Data model & storage choice
- **Logical model:** flat key → value (bytes) + version metadata. No queries, no joins — deliberately minimal so it scales and stays available.
- **Per-node storage:** **LSM-tree / log-structured store** (write-optimized: sequential appends + compaction) over B-tree, because the workload is write-heavy and we want fast, durable appends with a commit log for crash recovery. Pluggable engine (BerkeleyDB/MySQL/LSM in original Dynamo).
- **Partitioning metadata:** the ring (token → node) replicated everywhere via gossip; no central config store.
- **Why a KV (not SQL):** the entire premise is availability + linear scale via a simple key-addressed model; relational guarantees would force coordination that kills availability under partitions.

## 6. Deep dives

### 6.1 Consistent hashing + virtual nodes
- Hash key and nodes onto a ring; a key is owned by the first node clockwise, and replicated to the next N-1 distinct physical nodes (the **preference list**, skipping vnodes on the same physical host / same rack for fault isolation).
- **Plain consistent hashing problems:** non-uniform load and a node's whole range dumped on its neighbor when it leaves. **Fix: virtual nodes** — each physical node owns many small ring tokens. Joins/leaves redistribute small slices across *many* nodes (smooth rebalancing) and heterogeneous hardware gets proportionally more vnodes. This is the key to even load and cheap membership changes.

### 6.2 Replication & quorum (N/R/W)
- Coordinator writes to the N replicas; the operation succeeds when **W** ack a write or **R** respond to a read.
- **R + W > N ⇒ read-your-writes / strong-ish consistency** (read and write quorums overlap). Common configs:
  - `N=3, W=2, R=2` — balanced, overlapping quorums.
  - `W=1` — fastest, most available writes; weaker consistency. `R=1` — fast reads.
  - `W=N` — durable but blocks if any replica down (bad for "always writeable").
- The point: **tunable** per workload. Dynamo favored `W` small (always-writeable) and pushed conflict resolution to reads.

### 6.3 Conflict resolution — vector clocks vs LWW
- Concurrent writes to different replicas create divergent versions. Two strategies:
  - **Vector clocks:** each value carries `[(node, counter), ...]`. On write, the coordinator increments its entry. On read, clocks that are causally ordered (one descends from the other) → keep the newer; **concurrent** (neither dominates) → return **both siblings** for the client/app to merge (semantic reconciliation, e.g. merging a shopping cart so no add is lost). Cost: metadata growth (truncate old entries), and the app must handle siblings.
  - **Last-Write-Wins (LWW):** attach a timestamp; highest wins, silently dropping the other. Simple, no siblings, but **loses data** under concurrency and is hostage to **clock skew**. Cassandra defaults to LWW; Dynamo used vector clocks.
- **Choice:** vector clocks when no write may be silently lost (carts, counters → or use CRDTs); LWW when last-writer-wins is semantically acceptable and simplicity matters.

### 6.4 Handling failures — hinted handoff
- **Temporary failure:** if a preference-list replica is down, the coordinator writes to the next healthy node with a **hint** (metadata saying "this belongs to node X"). When X recovers, the hint is replayed to it and deleted. This is **sloppy quorum** — keeps writes available during transient outages without sacrificing durability.

### 6.5 Anti-entropy — Merkle trees
- Replicas drift (missed hints, longer outages). Each node builds a **Merkle tree** over each key range it owns (leaves = hashes of keys/values, parents = hashes of children). To compare two replicas, exchange root hashes; if equal, ranges are in sync (one comparison!). If not, walk down only the differing branches → transfer just the divergent keys. **O(differences)** instead of O(keys) — efficient background repair (read repair handles the rest at read time).

### 6.6 Membership & failure detection — gossip
- Decentralized **gossip:** each node periodically exchanges its view of (membership, token map, liveness) with a random peer; state converges in O(log N) rounds. Failure detection via heartbeats/timeouts (often φ-accrual). No central coordinator = no SPOF, but membership is **eventually** consistent (briefly divergent views are tolerated).
- **Temporary vs permanent failure distinction:** failure detection only suspends a node (triggers hinted handoff / read repair). Permanent removal and rebalancing of token ranges is an explicit admin action (or a longer timeout), avoiding expensive data reshuffles every time a node blips. This separation keeps a flapping node from triggering repeated TB-scale rebalances.

### 6.7 Reads, write path, and the request flow
- **Write:** client → any node (coordinator) → coordinator generates/advances the vector clock, writes locally, and forwards to the other N-1 preference-list replicas in parallel → returns success once **W** ack (the coordinator usually counts as one). Each replica appends to its commit log then its LSM memtable.
- **Read:** coordinator requests from all N (or enough), waits for **R** responses, and if versions diverge returns all causally-concurrent siblings. **Read repair:** if some replicas returned stale versions, the coordinator pushes the merged/newest version back to them asynchronously — the cheap, traffic-driven half of anti-entropy (Merkle trees cover keys that are rarely read).

## 7. Bottlenecks & scaling
- **Hot keys** (one key, massive traffic) — consistent hashing distributes keys, not load within a key. Fix: client-side caching, key-splitting, or replica read fan-out.
- **Tail latency (p99.9):** slowest replica drags reads. Fix: send to all N, return after R fastest; speculative/hedged requests.
- **Sibling explosion:** pathological concurrent writes grow vector clocks and siblings. Fix: clock truncation, app-side merge, CRDTs.
- **Rebalancing storms** on node join/leave: virtual nodes spread the movement; throttle streaming.
- **Anti-entropy cost** if replicas diverge widely after a long outage: Merkle trees keep it proportional to divergence; rate-limit repair.

## 8. Tradeoffs / talking points
- **AP over CP:** always-writeable, eventual consistency — the foundational call; everything (quorums, siblings, hinted handoff) follows from it.
- **R+W>N** gives quorum overlap (consistency) at the cost of latency/availability; tune per use case.
- **Vector clocks** preserve all concurrent writes (no data loss) but push reconciliation to the app; **LWW** is simple but loses writes and trusts clocks.
- **Virtual nodes** are the unlock for even load + smooth, incremental rebalancing + heterogeneous hardware.
- **Decentralized (gossip, no master)** removes the SPOF but accepts eventually-consistent membership.
- **Sloppy quorum + hinted handoff** keeps writes flowing through transient failures; **Merkle anti-entropy + read repair** clean up afterward.
- LSM storage trades read amplification for write throughput — right for a write-heavy, always-available store.
