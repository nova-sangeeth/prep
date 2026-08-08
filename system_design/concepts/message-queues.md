# Message Queues & Streaming

> Decouple producers from consumers with async, durable, buffered delivery — trade latency and consistency for throughput, resilience, and elasticity.

## What it is & why it matters

A message broker sits between producers and consumers so neither blocks the
other. Benefits: **decoupling** (services don't know each other), **buffering**
(absorb load spikes), **async work** (return to user fast, process later),
**fan-out** (one event, many consumers), and **resilience** (broker persists
messages if a consumer is down). The cost is added latency, operational
complexity, and weaker end-to-end consistency (eventual, not synchronous).

Two core abstractions:
- **Queue (point-to-point):** each message consumed by exactly one worker in a
  consumer group. Used for task/work distribution (SQS, RabbitMQ).
- **Pub/Sub (topic):** each message delivered to every subscriber. Used for
  event broadcast (Kafka topics, SNS, RabbitMQ fanout exchange).

## How it works

Kafka-style log: an append-only, partitioned, replicated commit log. Consumers
track an **offset**; the broker doesn't delete on read (retention by time/size),
enabling replay and multiple independent consumer groups.

```
producers --> [ Topic: partition 0 | m0 m1 m2 m3 ...] <-- consumer group A (offset 2)
          \-> [ Topic: partition 1 | m0 m1 m2 ...    ] <-- consumer group B (offset 0)
                  ^ key-hash routes msg to a partition; order kept per-partition
```

RabbitMQ/SQS-style queue: broker pushes (or consumer pulls) a message, consumer
**ACKs** on success; unacked messages redeliver after a visibility timeout. The
message is deleted after ack — no replay.

## Tradeoffs / variants

| Dimension | Kafka (log) | RabbitMQ (broker) | SQS (managed) |
|---|---|---|---|
| Model | Partitioned log, pull | Exchanges+queues, push | Queue, poll |
| Throughput | Very high (M/s) | Moderate–high | High (auto-scale) |
| Ordering | Per-partition | Per-queue (best effort) | FIFO queue only |
| Replay | Yes (retention) | No (deleted on ack) | No |
| Routing | Consumer-side, by partition | Rich (topic/headers/fanout) | Minimal |
| Ops | Heavy (ZK/KRaft, partitions) | Medium | Zero (fully managed) |
| Best for | Event streaming, log, analytics | Complex routing, RPC, tasks | Simple decoupling on AWS |

**Delivery semantics:**
- *At-most-once:* ack before processing; fast, may drop on crash.
- *At-least-once:* ack after processing; never lose, may duplicate → **consumers must be idempotent.** This is the practical default.
- *Exactly-once:* only within a closed system (Kafka transactions: idempotent
  producer + transactional read-process-write). Across heterogeneous systems it
  is effectively impossible — emulate via at-least-once + idempotency/dedup.

## When to use · pitfalls

Use for async tasks (email, image resize), spike buffering, event-driven fan-out,
log/CDC pipelines, and cross-service decoupling. Avoid when you need a synchronous
answer (use RPC) or strong transactional consistency across the boundary.

Pitfalls:
- **Ordering needs a partition/queue key** (e.g. partition by `userId`). Global
  order kills parallelism — order is only free within one partition.
- **Backpressure:** unbounded queues hide the problem until they OOM or balloon
  lag. Bound queues, monitor **consumer lag**, scale consumers (≤ partition count
  in Kafka), or shed/throttle producers.
- **Poison messages:** a message that always fails blocks/retries forever. Send
  to a **dead-letter queue (DLQ)** after N attempts; alert and inspect.
- **Idempotency:** dedup by a business/message key in a store (or use natural
  idempotent ops like `SET`) so redelivery is safe.
- **Duplicate fan-out side effects:** don't trigger non-idempotent external calls
  without a dedup guard.

## Interview soundbites
- "Queue = one consumer wins; pub/sub = everyone gets a copy."
- "Default to at-least-once and make consumers idempotent — exactly-once across systems is a myth."
- "Kafka keeps the log so you get replay and many consumer groups; RabbitMQ deletes on ack and gives you rich routing."
- "Ordering is per-partition only; pick a partition key, accept no global order."
- "Watch consumer lag — that's your backpressure signal; cap retries with a DLQ for poison messages."
- "Parallelism is bounded by partition count in Kafka."
