# Bloom Filters

> A tiny probabilistic set that answers "definitely not present" or "probably present" — no false negatives, tunable false positives, huge memory savings.

## What it is & why it matters

A Bloom filter is a space-efficient probabilistic membership test. It can say a
key is **definitely not** in the set (skip the expensive lookup) or **maybe** in
the set (do the real check). It never returns a false negative. The payoff: a few
bits per element instead of storing keys, letting you keep a membership summary
of billions of items in RAM and avoid pointless disk/network lookups for the
common "not found" case.

## How it works

A bit array of `m` bits and `k` independent hash functions. **Insert:** hash the
element with all `k` functions, set those `k` bits. **Query:** hash again — if
**any** of the `k` bits is 0, the element is definitely absent; if **all** are 1,
it's *probably* present (those bits may have been set by other elements →
collision = false positive). No deletes (you'd clear bits shared by others — use
a **counting Bloom filter** for deletion).

```
bits:  index ->  0 1 2 3 4 5 6 7 8 9
insert "x": h1=2,h2=5,h3=8 -> set     [0 0 1 0 0 1 0 0 1 0]
query  "y": h1=2,h2=5,h3=7 -> bit7=0  => DEFINITELY NOT present
query  "z": h1=2,h2=5,h3=8 -> all 1   => MAYBE present (verify)
```

**Sizing:** for `n` items and target false-positive rate `p`:
`m = -n·ln(p) / (ln2)^2` bits, optimal `k = (m/n)·ln2`. Rule of thumb: ~**9.6
bits/element for 1% FP**, ~14.4 bits for 0.1%. FP rate rises as the filter fills;
size for your max `n`.

## Tradeoffs / variants

| Variant | Adds | Cost |
|---|---|---|
| Standard Bloom | Membership, no delete | Fixed size, FP grows with load |
| Counting Bloom | Deletion (counters not bits) | ~4x memory |
| Scalable Bloom | Grows as n grows | More complexity |
| Cuckoo filter | Delete + better FP at high load | Slightly more complex |

| | False positive | False negative |
|---|---|---|
| Possible? | Yes (tunable) | **Never** |
| Meaning | "maybe" → verify | "no" is always true |

## When to use · pitfalls

Classic uses — front a slow lookup with a fast "is it even worth checking?":
- **DB / LSM-tree (Cassandra, HBase, RocksDB):** per-SSTable Bloom filter avoids
  disk reads for keys not in that file — huge read-amplification savings.
- **Caches:** skip a cache/DB lookup for keys known absent; mitigate cache
  penetration for non-existent keys.
- **CDN/web:** "have I seen this URL?" (e.g. malicious-URL checks), dedup.
- **Distributed systems:** set reconciliation, avoiding redundant work/sync.

Pitfalls:
- **You must handle false positives** — always do the real lookup on "maybe";
  the filter only saves the "no" case.
- **No deletion** in the standard form; a long-lived filter degrades — rebuild
  periodically or use counting/scalable variants.
- **Undersizing** spikes the FP rate as it fills; size for peak `n`.
- **Correlated/poor hashes** worsen FP — use independent (e.g. double-hashing).
- It tells you membership, **not the value or count** — it's a gatekeeper, not a
  store.

## Interview soundbites
- "Bloom filters give 'definitely no' or 'probably yes' — no false negatives, ever."
- "It's a memory-for-accuracy trade: ~10 bits per element buys a 1% false-positive rate."
- "Use it as a cheap gate in front of an expensive lookup — only the negatives are free."
- "Cassandra/RocksDB put a Bloom filter per SSTable to skip disk reads for absent keys."
- "Standard Bloom filters can't delete — use a counting Bloom filter if you must."
- "On a 'maybe', you still do the real check; on a 'no', you skip it entirely."
