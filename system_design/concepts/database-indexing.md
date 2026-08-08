# Database Indexing

> Indexes trade write throughput and storage for fast reads — pick the structure (B-tree vs LSM vs hash) by your read/write mix and query shape.

## What it is & why it matters

An index is an auxiliary data structure that lets the DB find rows without a full
scan — turning O(n) into O(log n) (or O(1)). It is the single biggest lever on
query latency. But every index must be **maintained on every write**, costs disk,
and can be ignored by the planner if unselective. The skill is indexing exactly
what your queries need and no more.

## How it works

```
B-tree (read-optimized, in-place):     LSM-tree (write-optimized, append):
        [50]                            writes -> [MemTable] (sorted, in RAM)
       /    \                                        | flush
   [20,40] [70,90]   sorted, balanced            [SSTable L0] [SSTable L1] ...
   /  |  \                                        merged/compacted in background
 leaves -> ordered, range scans            reads check memtable + SSTables (+bloom)
```

- **B-tree / B+-tree:** balanced, sorted, supports point lookups **and range
  scans**; updates in place. Default for Postgres/MySQL (InnoDB). O(log n)
  reads/writes; random I/O on writes.
- **LSM-tree:** buffers writes in memory, flushes sorted **SSTables**, compacts
  later. Sequential writes → very high write throughput (Cassandra, RocksDB,
  LevelDB). Reads may touch multiple SSTables (mitigated by **bloom filters**);
  compaction adds background I/O and write amplification.
- **Hash index:** O(1) equality lookups, **no range queries**, no ordering. Used
  for in-memory engines and some specialized stores.

## Tradeoffs / variants

| Structure | Reads | Writes | Range scan | Used by |
|---|---|---|---|---|
| B+-tree | Fast (log n) | Moderate (in-place, random I/O) | Yes | Postgres, MySQL/InnoDB |
| LSM-tree | Moderate (multi-SSTable) | Very fast (sequential) | Yes (sorted) | Cassandra, RocksDB |
| Hash | O(1) equality | Fast | No | Redis, in-memory engines |

| Index type | What it does |
|---|---|
| Primary / clustered | Table stored in index key order; one per table |
| Secondary | Separate structure pointing to rows; many allowed |
| Composite `(a,b,c)` | Multi-column; obeys **leftmost-prefix** rule |
| Covering | Index includes all queried columns → index-only scan, skips table |
| Partial | Index only rows matching a predicate (e.g. `WHERE active`) |
| Unique | Enforces uniqueness + speeds lookup |

## When to use · pitfalls

Index columns in `WHERE`, `JOIN`, `ORDER BY`, and high-selectivity filters. Order
composite columns by selectivity/equality-first, and to match `ORDER BY`. Use a
**covering index** to serve a hot query entirely from the index.

When indexes hurt:
- **Write-heavy tables:** each index is extra work per `INSERT/UPDATE/DELETE`.
- **Low cardinality** (e.g. boolean): planner skips it; full scan is cheaper.
- **Over-indexing:** bloats storage, slows writes, confuses the planner.
- **Leftmost-prefix:** an index on `(a,b)` won't help a query filtering only on
  `b`.
- **Function/type mismatch:** `WHERE lower(email)=...` or implicit casts can
  bypass the index (need an expression index).
- **Write amplification (LSM):** compaction can dominate I/O; tune accordingly.

## Interview soundbites
- "An index trades write speed and storage for read speed — never free."
- "B-tree for balanced read/write and range scans; LSM for write-heavy ingest."
- "LSM turns random writes into sequential ones and leans on bloom filters for reads."
- "A covering index answers the query from the index alone — no table lookup."
- "Composite indexes follow the leftmost-prefix rule; column order matters."
- "Don't index low-cardinality columns — the planner will scan instead."
