# Sharding & Partitioning

> Split data across nodes so no single one is the bottleneck; the shard key decides whether you win or create a hotspot.

## What it is & why it matters
Partitioning splits a dataset into pieces so each can live and scale independently; **sharding** is partitioning across separate database servers/nodes. It's how stateful tiers scale horizontally past one machine's CPU, RAM, disk, and IO. The entire success of a sharded system rides on the **shard (partition) key**: a good key spreads load and keeps related data together; a bad one creates hot shards or forces expensive cross-shard operations. This is the #1 deep-dive trap in interviews, so be ready to defend your key.

## How it works
**Two orthogonal directions**:
- **Vertical partitioning**: split by columns/feature — put rarely-read blobs or a feature's tables on their own store (e.g., user_auth vs user_profile vs user_media). Reduces row width, isolates workloads. Limited by single-feature growth.
- **Horizontal partitioning (sharding)**: split by rows — each shard holds a subset of rows by some key. This is what scales unbounded.

**Mapping rows → shards**:
```
Range:   key in [a–h]→S1  [i–p]→S2  [q–z]→S3   (ordered; range scans easy; skew-prone)
Hash:    shard = hash(key) mod N                (even spread; kills range scans)
Consistent hash: keys+nodes on a ring          (adding node moves ~1/N keys)
Directory: lookup table key→shard              (flexible; the table is a SPOF/bottleneck)
```
- **Range**: contiguous key ranges per shard. Great for range/time queries; risks hotspots (recent timestamps, sequential IDs all hit one shard).
- **Hash**: `hash(key) mod N` spreads evenly but destroys locality (range scans must hit all shards). Naive mod-N reshuffles everything when N changes.
- **Consistent hashing**: place shards and keys on a ring; adding/removing a node remaps only ~1/N keys. Virtual nodes smooth out imbalance. Backbone of Dynamo/Cassandra.
- **Directory-based**: a lookup service maps key→shard; maximally flexible (rebalance freely) but the directory must be HA and fast.

## Tradeoffs / variants
| Scheme | Spread | Range queries | Resharding cost | Notes |
|---|---|---|---|---|
| Range | Can skew | Excellent | Move ranges | Hotspots on sequential keys |
| Hash mod-N | Even | Poor (scatter) | High (reshuffle all) | Simple but rigid |
| Consistent hash | Even (w/ vnodes) | Poor | Low (~1/N moves) | Industry default |
| Directory | Tunable | Depends | Low (update map) | Extra hop; map is SPOF |

## When to use · pitfalls
- **Choosing a shard key**: pick high-cardinality, evenly-accessed, and aligned with your dominant query so most queries hit one shard. `user_id` is common (co-locates a user's data). Avoid low-cardinality keys (status, country), monotonic keys (timestamp, auto-increment → all writes on last shard), and keys that don't match read patterns.
- **Hotspots / hot shards**: caused by skewed keys or a celebrity. Mitigate with a better key, **key salting** (append a bucket suffix to spread a hot key), consistent hashing + vnodes, or splitting the hot partition.
- **Resharding / rebalancing**: avoid by over-provisioning logical shards up front (e.g., 1024 logical shards mapped to few physical nodes — split by moving logical shards, no rehash). Otherwise use consistent hashing to bound data movement. Resharding live traffic is one of the hardest ops problems — needs dual-writes/backfill/cutover.
- **Cross-shard joins/queries**: not possible in one DB call. Options: denormalize so the join isn't needed, scatter-gather (query all shards, merge — slow, tail-latency bound), maintain a secondary index/derived table, or keep related data co-located by choosing the join key as the shard key. Cross-shard **transactions** need 2PC/sagas — avoid if you can.
- **Secondary indexes**: local (per-shard, scatter-gather reads) vs global (separate index, partitioned independently — consistent reads, harder writes).
- Pitfalls: sharding too early (a single tuned DB + replicas goes far); a shard key you can't change later; rebalancing under load with no plan; forgetting that each shard still needs replication for HA (sharding ≠ redundancy).

## Interview soundbites
- "Sharding scales writes and storage; the shard key makes or breaks it — high cardinality, even access, matches the query."
- "Range partitioning gives you range scans but invites hotspots; hashing spreads load but kills locality."
- "Consistent hashing exists so adding a node moves ~1/N of keys instead of reshuffling everything."
- "Avoid resharding by pre-splitting into many logical shards and mapping them to few physical nodes."
- "Cross-shard joins are a design smell — denormalize, co-locate by shard key, or scatter-gather and pay the tail latency."
- "Salt a hot key to spread it; sharding alone doesn't give HA — each shard still needs replicas."
