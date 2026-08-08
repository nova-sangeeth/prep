# Replication

> Keep copies of data on multiple nodes for availability, read scale, and locality; the cost is keeping them in sync.

## What it is & why it matters
Replication maintains copies of the same data on multiple nodes. It buys three things: **availability** (survive node/DC failure), **read throughput** (serve reads from many copies), and **locality** (a replica near the user). It is orthogonal to sharding — you replicate each shard. The core tension is synchronization: how copies agree on writes, and what you expose to readers in the meantime (lag, stale reads, conflicts). Almost every consistency/availability question in an interview reduces to a replication choice.

## How it works
**Topologies**:
- **Leader-follower (single-leader / primary-replica)**: all writes go to one leader, which streams its change log (WAL/binlog/oplog) to followers; reads can hit any replica. Simple, no write conflicts, strong-ish consistency on the leader. The leader is a write SPOF until failover.
- **Multi-leader**: multiple nodes accept writes (e.g., one leader per region) and replicate to each other. Great for multi-region write latency and offline clients, but **write conflicts** are inevitable and need resolution (LWW, version vectors, CRDTs, app merge).
- **Leaderless (Dynamo-style)**: client (or coordinator) writes to several replicas and reads from several; no single leader. Uses **quorums** (W + R > N) and **read repair / anti-entropy** to converge. High availability, tunable consistency, conflict handling pushed to reads.

```
Leader-follower:            Leaderless (N=3, W=2, R=2):
   writes                      write → R1 R2 (ack) R3(lag)
     ▼                         read  ← R1 R3 (pick newest, repair R3)
  ┌Leader┐──log──► F1 (read)   overlap of W and R guarantees a fresh copy
  └──────┘──log──► F2 (read)
```

**Sync vs async propagation**:
- **Synchronous**: leader waits for follower ack before confirming the write. No data loss on leader failure, but slower writes and a stalled follower blocks writes. Often **semi-sync**: wait for one follower, the rest async.
- **Asynchronous**: leader confirms immediately, ships changes after. Fast and available, but a leader crash can lose un-replicated writes (RPO > 0) and readers see **replication lag**.

## Tradeoffs / variants
| Topology | Writes | Conflicts | Availability | Best for |
|---|---|---|---|---|
| Leader-follower | One leader | None | Leader = SPOF (until failover) | Read-heavy, single region |
| Multi-leader | Many leaders | Yes (resolve) | High | Multi-region writes, offline |
| Leaderless | Any replica (quorum) | Yes (at read) | Very high | AP systems, tunable consistency |

| Propagation | Durability on failure | Write latency | Read freshness |
|---|---|---|---|
| Synchronous | No loss (RPO≈0) | Higher | Fresh |
| Async | Can lose recent writes | Low | Lag possible |
| Semi-sync | Bounded loss | Medium | Mostly fresh |

## When to use · pitfalls
- **Read replicas** scale reads but not writes (every replica still applies every write). They shine in read-heavy systems; they don't help write-bound ones — shard for that.
- **Replication lag** breaks **read-your-own-writes** (user posts, then reads a stale replica and sees nothing). Mitigations: read from leader for recently-written keys, pin a session to the leader briefly, track a write timestamp/LSN and only read replicas caught up past it, or accept eventual consistency.
- **Failover** (leader dies): detect (heartbeat/lease timeout), elect/promote a new leader (consensus — Raft/Paxos — or an orchestrator), redirect writes. Hazards: **split-brain** (two leaders accept writes — fence with leases/quorum/STONITH), lost async writes, and clients caching the old leader. Measure **RTO** (time to recover) and **RPO** (data lost).
- **Multi-leader/leaderless conflicts**: concurrent writes to the same key. Resolution: last-write-wins (simple, loses data; needs synced clocks), version vectors (detect causality), CRDTs (auto-merge for some types), or surface both versions to the app.
- Pitfalls: assuming async replicas are consistent; routing read-after-write to a lagging replica; no fencing → split-brain; treating replication as a backup (it faithfully replicates a `DROP TABLE`); ignoring that sync replication couples availability to the slowest replica.

## Interview soundbites
- "Replication is for availability, read scale, and locality; it does not scale writes — that's sharding."
- "Single-leader avoids write conflicts but the leader is a SPOF until failover promotes a replica."
- "Async replication is fast but lossy on failure (RPO>0) and lagging replicas serve stale reads."
- "Read-your-writes breaks under replication lag — read from the leader or wait for the replica to catch up to your LSN."
- "Multi-leader and leaderless trade conflict-freedom for availability; now you need LWW, version vectors, or CRDTs."
- "Failover's enemies are split-brain and lost writes — fence with leases and a quorum."
