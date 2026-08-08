# Consistent Hashing

> Map keys and nodes onto a hash ring so adding/removing a node moves only ~1/N of keys instead of nearly all of them.

## What it is & why it matters

Naive sharding uses `hash(key) % N`. When `N` changes (scale out, node failure),
**almost every key remaps**, forcing a massive reshuffle and cache stampede.
Consistent hashing makes node count changes cheap: only the keys adjacent to the
changed node move — about **K/N keys**. It's the backbone of distributed caches
(Memcached clients), DHTs, and Dynamo-style databases (DynamoDB, Cassandra,
Riak) for partitioning and locating data.

## How it works

Hash both nodes and keys onto the same circular space (e.g. 0..2^32-1). A key is
owned by the **first node clockwise** from the key's position. Adding a node only
captures the arc between it and its predecessor; removing a node hands its arc to
the next node clockwise. No global remap.

```
        0/2^32
          N_A
      k4 /    \ k1
    N_D |  ring | N_B    key -> walk clockwise -> owning node
      k3 \    / k2
          N_C
  k2 falls between N_B and N_C -> owned by N_C
```

**Virtual nodes (vnodes):** hashing each physical node once gives lumpy,
unbalanced arcs and big variance. Instead, map each physical node to **many**
points on the ring (e.g. 100–256 vnodes). This evens out load, lets you weight
heterogeneous hardware (more vnodes = bigger share), and spreads a failed node's
load across *many* survivors instead of dumping it all on one neighbor.

## Tradeoffs / variants

| Aspect | Without vnodes | With vnodes |
|---|---|---|
| Load balance | Skewed (high variance) | Even (smooths arcs) |
| Node loss impact | Dumped on 1 successor | Spread across many |
| Heterogeneity | Hard | Weight by vnode count |
| Metadata | Tiny | Larger ring map |
| Rebalance on change | ~K/N keys | ~K/N keys |

| Variant | Idea |
|---|---|
| Classic ring (Dynamo/Cassandra) | Clockwise successor owns key; replicate to next R nodes |
| Rendezvous (HRW) hashing | Pick node with max `hash(key,node)`; no ring, simple, even |
| Jump consistent hash | O(1) memory, no vnode map; but only appends buckets at the end |

## When to use · pitfalls

Use whenever you horizontally partition stateful data/cache and want minimal
movement on scaling or failure, or to locate a key's owner without a central
directory. Cassandra/Dynamo also replicate to the **R successor nodes** clockwise
for fault tolerance.

Pitfalls:
- **Hot keys / hot partitions:** consistent hashing balances *key space*, not
  *access frequency*. A single viral key still overloads its owner — add a
  per-key cache, split, or salt the hot key.
- **Too few vnodes → imbalance**; too many → bloated ring metadata and slower
  lookups. ~100–256 is typical.
- **Use a good hash** (MD5/Murmur) for uniform distribution; weak hashes cluster.
- **Ring consistency:** all clients must agree on ring membership — use gossip or
  a coordination service; stale views misroute.
- Movement is minimal but **not zero** — plan for bootstrap/streaming during
  rebalance.

## Interview soundbites
- "`hash % N` remaps everything when N changes; consistent hashing moves only K/N keys."
- "Keys and nodes live on one ring; the first node clockwise owns the key."
- "Virtual nodes smooth out load and spread a failed node's keys across many survivors."
- "It balances the keyspace, not the traffic — hot keys still need special handling."
- "It's how Dynamo and Cassandra partition data and pick replica owners."
- "Rendezvous and jump hashing are vnode-free alternatives with even spread."
