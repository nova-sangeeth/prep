# CAP Theorem (and PACELC)

> During a network partition you must choose consistency or availability; PACELC adds: even without partitions, you trade latency vs consistency.

## What it is & why it matters
CAP states that a distributed data store cannot simultaneously guarantee all three of **Consistency** (every read sees the most recent write — linearizable), **Availability** (every request to a non-failing node gets a non-error response), and **Partition tolerance** (the system keeps working despite dropped/delayed messages between nodes). Because network partitions are a fact of life — you can't opt out of P — the real choice is **C vs A when a partition happens**. It matters because it frames the central design decision for any replicated/sharded store and it's a near-guaranteed interview topic. The common misframing ("pick 2 of 3") is misleading: P is mandatory, so you're picking between CP and AP for partition behavior only.

## How it works
When the network splits the cluster into groups that can't talk:
```
   [Client]──► Node A  ╳╳ partition ╳╳  Node B ◄──[Client]
                 │                          │
   CP: minority/uncertain side REFUSES (or blocks) to avoid stale/divergent data
   AP: BOTH sides keep serving; data diverges, reconcile later (read repair, CRDT)
```
- **CP (consistency over availability)**: on a partition, the side that can't reach a quorum **rejects or blocks** requests rather than risk returning stale data or accepting conflicting writes. The system stays correct but loses availability on the cut-off side. Examples: ZooKeeper/etcd, HBase, Spanner (within constraints), classic RDBMS with sync replication, MongoDB (majority writes).
- **AP (availability over consistency)**: on a partition, **all reachable nodes keep serving** reads and writes; copies diverge and are reconciled afterward (eventual consistency, read repair, version vectors/CRDTs). Examples: Cassandra, DynamoDB (default), Riak.
- Crucially this is a **per-operation / per-partition** decision, not a fixed label. Cassandra with `QUORUM` leans CP-ish; with `ONE` it's strongly AP. Tunable consistency lets one system slide along the axis.

## Tradeoffs / variants
| | CP | AP |
|---|---|---|
| On partition | Reject/block on minority side | Serve everywhere, diverge |
| Guarantees | Linearizable reads | Eventual convergence |
| Risk | Downtime / errors | Stale reads, conflicts |
| Reconciliation | N/A (never diverges) | Read repair, CRDT, LWW |
| Examples | etcd, ZK, Spanner, HBase | Cassandra, Dynamo, Riak |
| Use for | Money, locks, config, leader election | Carts, likes, feeds, telemetry |

## When to use · pitfalls
- **Choose CP** when stale or conflicting data is unacceptable: payments, inventory decrement, distributed locks, config/coordination, leader election. You accept that some requests fail during a partition.
- **Choose AP** when availability and write acceptance trump momentary staleness: social feeds, likes, shopping-cart adds, metrics, presence. You accept reconciliation and "eventually correct."
- **PACELC** completes the picture: **if Partition (P), choose A or C; Else (E), choose Latency (L) or Consistency (C).** It captures the everyday trade — even with a healthy network, synchronous strong consistency costs latency (extra round trips/quorums), while relaxing it buys speed. Classifications: Dynamo/Cassandra = **PA/EL** (available + low-latency), Spanner = **PC/EC** (consistent always, pays latency), MongoDB ≈ **PA/EC**.
- Pitfalls: thinking "pick 2 of 3" (P isn't optional); believing CAP-C and ACID-C are the same (they're not — CAP-C is linearizability, ACID-C is integrity constraints); assuming a system is uniformly CP or AP (it's per-operation and tunable); ignoring the no-partition case where PACELC's latency cost actually dominates day to day; conflating availability (a node answers) with durability or correctness.

## Interview soundbites
- "Partitions are mandatory, so CAP is really: during a partition, do you sacrifice consistency or availability?"
- "CP rejects requests on the cut-off side to stay correct; AP keeps serving and reconciles later."
- "It's per-operation, not a label — Cassandra is AP at ONE and effectively CP at QUORUM."
- "PACELC is the honest version: partition → A or C; else → latency or consistency, which is the cost you pay every single day."
- "Money, locks, and leader election are CP; likes, carts, and feeds are AP."
- "CAP's C is linearizability, not ACID's C — don't conflate them."
