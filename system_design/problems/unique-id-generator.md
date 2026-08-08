# Design a Distributed Unique ID Generator

## 1. Requirements
- **Functional:** Generate globally **unique** IDs across a distributed system. IDs should be **roughly time-sortable** (k-sorted) so they're useful as primary keys / for range scans by creation time. Fit in 64 bits (so they're cheap as DB keys and fit a `BIGINT`).
- **Non-functional:**
  - **Scale:** generate ~**10,000+ IDs/sec** per node, millions/sec aggregate; must scale horizontally with no central bottleneck.
  - **Latency:** sub-millisecond, ideally local (no network hop per ID).
  - **Availability:** ID generation can't be a SPOF — an outage here halts all writes.
  - **Uniqueness:** absolute, even under concurrency, restarts, and clock issues.
  - **Sortability:** monotonic-ish by time (newer ID > older ID) — important for index locality and pagination.

## 2. Back-of-envelope estimates
- **Throughput needed:** suppose 1M new entities/s peak across the fleet. With a 12-bit per-ms sequence (Snowflake), one node yields **4,096 IDs/ms = ~4.1M IDs/s** — a single node already exceeds typical need; the machine-ID space lets us add nodes for more.
- **ID space lifetime:** 41-bit ms timestamp ≈ 2^41 ms ≈ **69.7 years** from a custom epoch before rollover.
- **Node space:** 10 bits = **1,024 nodes**. Sequence 12 bits = 4,096/ms/node. Total theoretical: 1,024 × 4.1M ≈ **4.2B IDs/s** — far beyond requirements.
- **Storage impact:** 64-bit (8-byte) keys vs 128-bit UUIDs (16 bytes) halves index size and improves cache locality on every table that references them — a real cost at billions of rows.

## 3. API
```
nextId() -> int64        // local call, no network round trip (Snowflake)

// alternatives' interfaces:
DB ticket server:  SELECT/UPDATE on an auto_increment row -> int64  (network hop)
DB range-batch:    fetchRange(1000) -> [start, start+999]           (amortized hop)
UUID:              uuid4()/uuid7() -> 128-bit                       (local, no coordination)
```

### Approach comparison (the decision at a glance)
| Approach        | Bits | Sortable      | Coordination        | Throughput      | SPOF |
|-----------------|------|---------------|---------------------|-----------------|------|
| UUIDv4          | 128  | No            | None                | Unlimited local | No   |
| UUIDv7          | 128  | Yes (k-sort)  | None                | Unlimited local | No   |
| DB ticket       | 64   | Yes (strict)  | Every ID (or batch) | DB-bound        | Yes  |
| Snowflake       | 64   | Yes (k-sort)  | Once at startup     | ~4M/s/node      | No   |

## 4. High-level design (Snowflake — chosen)
```
 64-bit ID layout (sign bit unused = always 0 to keep IDs positive):
 ┌─┬───────────────────────────┬────────────┬───────────────┐
 │0│   timestamp (41 bits)     │ machine ID │ sequence (12) │
 │ │   ms since custom epoch   │  (10 bits) │  per-ms ctr   │
 └─┴───────────────────────────┴────────────┴───────────────┘
   1            41                   10             12   = 64

 Each app/ID node generates locally:
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Node A   │   │ Node B   │   │ Node C   │     (machine IDs 1,2,3...)
   │ nextId() │   │ nextId() │   │ nextId() │
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        └──────────────┴──────────────┘
                  assigned by
            ┌───────────────────────┐
            │ Coordinator (ZooKeeper │  hands out unique machine IDs
            │ / etcd) at startup     │  (or static config)
            └───────────────────────┘
```
- **Per-node generator:** composes `(timestamp << 22) | (machineId << 12) | sequence`. Fully local, no network per ID → sub-µs, no SPOF.
- **Coordinator (ZK/etcd):** only at startup, to assign a unique machine ID. Not in the hot path.
- High bits = time ⇒ IDs sort by creation time across the fleet (k-sorted, since clocks differ slightly).

## 5. Data model & storage choice
- **No primary datastore for IDs** in the Snowflake approach — that's the point: generation is stateless and local. The only persistent state is the **machine-ID assignment** (in ZK/etcd or static config) and, optionally, the last-seen timestamp per node to detect clock regressions.
- IDs are consumed as `BIGINT` primary keys in the application's own databases; storing 8-byte integers keeps indexes small and B-tree inserts near-sequential (good for write locality precisely because IDs are time-ordered).

## 6. Deep dives — the three approaches & why Snowflake

### 6.1 UUID (v4 / v7)
- **UUIDv4:** 128-bit random. Generated locally, zero coordination, trivially unique (collision probability negligible). **Cons:** 128 bits (2x storage), **not sortable** → random inserts fragment B-tree indexes and hurt write throughput; not human-friendly.
- **UUIDv7:** newer — time-ordered (Unix ms in high bits + random low bits). Fixes sortability and keeps no-coordination locality, but still **128 bits**. Good modern default when 64-bit isn't required.
- **Verdict:** great for availability/simplicity; rejected here because we want 64-bit, sortable keys.

### 6.2 DB ticket / auto-increment server
- A single DB row (`auto_increment`) hands out monotonically increasing IDs. Simple, perfectly sortable, 64-bit.
- **Cons:** the DB is a **SPOF and a bottleneck** — every ID is a network round trip + write. **Scaling pattern:** run multiple ticket servers with **stepped offsets** (server A: 1,3,5…; server B: 2,4,6… i.e. `start = k`, `increment = N`) so they don't collide — but this breaks global monotonic sortability and complicates adding servers. **Batching:** each app fetches a *range* (e.g. 1,000 IDs) per round trip and serves locally → amortizes the network cost, but a crash wastes the unused range (gaps — usually fine).
- **Verdict:** fine at small/medium scale or when strict monotonicity matters; the coordination cost and SPOF push us off it at high scale.

### 6.3 Snowflake (chosen) — and its failure modes
- **Why chosen:** local generation (no per-ID network hop, no SPOF in the hot path), 64-bit, time-sortable, ~4M IDs/s/node. Bit-budget is tunable (e.g. shift bits from sequence to machine ID for more nodes).
- **Clock skew / NTP jumps** are the central risk because the timestamp is the high bits:
  - **Within a millisecond:** the 12-bit sequence counter disambiguates; if it overflows (>4,096 in 1ms), **busy-wait to the next millisecond**.
  - **Clock moves backward** (NTP correction, leap second, VM pause): generating with a smaller timestamp could reissue past IDs → **non-unique**. Mitigations: track `lastTimestamp`; if `now < lastTimestamp`, **refuse / wait** until the clock catches up, or fail fast and alarm. Run **NTP in slew mode (no step-backwards)**; disable leap-second smearing surprises.
  - **Machine-ID reuse** after a crash/redeploy: two nodes with the same machine ID can collide within the same ms. Fix: lease machine IDs from ZK/etcd with a TTL, or persist last-used timestamp so a restarted node won't generate "behind" its previous run.

### 6.4 Sortability nuance
- Snowflake IDs are **k-sorted**, not strictly totally ordered, because each node's clock differs by a few ms and the sequence is per-node. Within a node they're monotonic; across nodes, ordering is approximate to clock skew. For "sort by created time" and index locality this is sufficient; for a strict global sequence, only a single ticket server (or a consensus log) delivers it — at the cost of throughput.
- **Don't leak IDs as security tokens:** sequential/time-ordered IDs are guessable and reveal volume (the German-tank-problem: competitors estimate your daily signups from two IDs). Use them as internal keys; expose opaque/encrypted handles externally if enumeration is a concern.

### 6.5 Wall clock vs monotonic clock
- `nextId()` reads the **wall clock** because the timestamp must be comparable across restarts and machines — a monotonic clock isn't shareable. The danger is that wall clocks jump (NTP step, leap second, VM live-migration pause). Guard rail: persist `lastTimestamp` and never emit an ID whose timestamp is less than it; on a detected regression, block until the wall clock advances past `lastTimestamp` (bounded waits) and alarm if the gap is large. This converts a correctness bug (duplicate IDs) into a brief availability dip — the right trade.
- Practical config: NTP in **slew mode** (gradually corrects, never steps backward), leap-second smearing handled by the NTP layer, and a hard cap on how long a node will block before failing over to a spare machine ID.

## 7. Bottlenecks & scaling
- **Sequence overflow** within a hot millisecond → busy-wait to next ms (bounded by 1ms); or widen the sequence bits if a node legitimately needs >4,096/ms.
- **Machine-ID exhaustion** (only 1,024 with 10 bits) → rebalance the bit budget (e.g. 5 datacenter + 5 worker bits, or trade sequence bits) per expected fleet size.
- **Clock skew** is the real scaling hazard, not throughput → strict NTP, monotonic-clock guards, refuse-on-regression.
- **Epoch rollover** (~69 yrs) → set a recent custom epoch; document the rollover date.
- **DB ticket alternative** bottleneck → batch ranges + multiple stepped servers, but accept lost sortability/gaps.

## 8. Tradeoffs / talking points
- **Snowflake vs UUIDv4:** 64-bit + sortable + local vs 128-bit + unsortable + local-but-bigger; pick Snowflake when key size and index locality matter.
- **Snowflake vs DB ticket:** local & no-SPOF & high-throughput vs strictly-monotonic but a coordination bottleneck/SPOF.
- **UUIDv7** is the modern middle ground — sortable + zero coordination — if 128 bits is acceptable; reach for it before building Snowflake unless you truly need 64-bit.
- The **bit budget is a design dial:** more machine bits = bigger fleet; more sequence bits = higher per-node burst; fewer timestamp bits = shorter lifespan.
- We trade **strict total ordering for k-sorted + decentralization** — almost always the right call; only use a single sequencer when exact global order is a hard requirement.
- The hard part isn't throughput, it's **time:** clock skew, backward jumps, leap seconds, and machine-ID reuse are where uniqueness actually breaks — design the guards explicitly.
