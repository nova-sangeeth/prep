# SQL vs NoSQL

> Pick storage by access pattern and consistency need, not by hype; SQL for relational/transactional, NoSQL for scale/flexibility along one axis.

## What it is & why it matters
"SQL vs NoSQL" is shorthand for relational databases vs a family of non-relational stores, each optimized for a different data shape and access pattern. The choice cascades through your whole design — schema, sharding, consistency, query flexibility, and how you join. Interviewers want to see you justify storage from the *access pattern*, not reflexively reach for Postgres or Cassandra. Modern reality: it's a spectrum (NewSQL like Spanner/CockroachDB gives SQL + horizontal scale; many SQL DBs have JSON columns), so reason from requirements.

## How it works
**Relational (SQL)**: data in tables with a fixed schema, related by foreign keys, queried with SQL and joins. Strong on **ACID** transactions, ad-hoc queries, and integrity constraints. Normalized to remove redundancy. Scales up easily, out with effort (sharding, read replicas). Examples: Postgres, MySQL.

**NoSQL** is four distinct shapes:
```
 Key-Value      Document        Wide-Column           Graph
 ┌──────┐      ┌──────────┐    rowkey→{cf:cols}       (A)──likes──►(B)
 k → v          {json doc,       big sparse tables      │           │
 (Redis,         nested}         (Cassandra,           follows   authored
  DynamoDB)     (MongoDB)         HBase, Bigtable)       ▼           ▼
                                                        (C)         (D)
```
- **Key-Value**: hash map at scale; O(1) get/put by key. Sessions, caches, feature flags. (Redis, DynamoDB, Memcached.)
- **Document**: KV where the value is a queryable JSON/BSON doc; flexible/evolving schema, aggregate-per-document. Catalogs, user profiles, CMS. (MongoDB, Couchbase.)
- **Wide-column**: rows keyed by partition+clustering key, sparse columns, tuned for massive writes and range scans within a partition. Time-series, feeds, event logs. (Cassandra, HBase, Bigtable.)
- **Graph**: nodes + edges as first-class; cheap multi-hop traversals. Social graphs, fraud, recommendations. (Neo4j, Neptune.)

## Tradeoffs / variants
| | Relational | Key-Value | Document | Wide-Column | Graph |
|---|---|---|---|---|---|
| Schema | Fixed, normalized | None | Flexible | Flexible, wide | Nodes/edges |
| Query | SQL + joins | Get/put by key | Rich on doc fields | Key + range scan | Traversals |
| Scale-out | Hard (shard) | Easy | Easy | Easy (built-in) | Hard |
| Consistency | Strong (ACID) | Tunable | Tunable | Tunable (AP-leaning) | Varies |
| Joins | Native | None | Limited/embed | None | Native (edges) |
| Sweet spot | Transactions, integrity | Caches, sessions | Evolving aggregates | Write-heavy, time-series | Relationships |

## When to use · pitfalls
- **Use SQL when**: relationships and multi-entity transactions matter (payments, orders, inventory), you need ad-hoc queries, or correctness/integrity dominates. Default for most OLTP until proven otherwise.
- **Use KV when**: access is purely by key and you need extreme throughput/low latency (sessions, rate-limit counters, hot lookups).
- **Use Document when**: data is a self-contained aggregate read/written together and the schema evolves fast.
- **Use Wide-column when**: write volume is huge, queries are key+range, and you can pre-design tables around access patterns (query-first modeling, denormalized).
- **Use Graph when**: the *relationships* are the product and you do many-hop traversals that would be join-explosions in SQL.
- **ACID** (Atomicity, Consistency, Isolation, Durability) vs **BASE** (Basically Available, Soft state, Eventually consistent): NoSQL often relaxes isolation/consistency for availability and scale. Know isolation levels (read-committed, repeatable-read, serializable) for SQL.
- **Normalization** removes redundancy and update anomalies (good for writes/integrity) but needs joins on read; **denormalization** duplicates data for read speed at the cost of write complexity and consistency — the standard NoSQL trade.
- Pitfalls: choosing NoSQL then bolting on joins/transactions in the app; ignoring that "schemaless" just moves schema enforcement into application code; picking wide-column without designing tables per query; assuming NoSQL = web-scale automatically (a single Postgres handles tens of thousands of TPS).

## Interview soundbites
- "SQL is relational + ACID for transactions and ad-hoc queries; NoSQL trades joins/flexibility for one specific scaling axis."
- "There are four NoSQL shapes — KV, document, wide-column, graph — and they're not interchangeable; pick by access pattern."
- "Wide-column is query-first: you design tables around the reads, denormalized, no joins."
- "Normalize for write integrity, denormalize for read speed — that's the core SQL/NoSQL tension."
- "Reach for graph only when the traversals are the workload; otherwise relationships live fine in SQL."
- "Default to Postgres until a requirement — scale, write volume, or schema flux — forces something else."
