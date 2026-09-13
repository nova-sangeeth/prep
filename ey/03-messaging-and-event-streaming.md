# Messaging & Event Streaming — Service Bus, Event Grid, Event Hub, Kafka, RabbitMQ

> EY GDS — DE Cloud Integration Platform Engineer (Senior, Rank 42)

**What this file buys you in the interview:** JD responsibility 4 is verbatim *"Implement Batch Jobs using event streaming and asynchronous messaging using Kafka, Service Bus, Event Grid, or RabbitMQ"* and responsibility 1 names event-driven architectures. **"Service Bus vs Event Grid vs Event Hubs"** is the single most-asked Azure integration question in existence — §2 gives you a 40-second rehearsable script for it. §8 covers the batch-meets-stream bridge that almost every candidate fumbles. Everything numbered here was verified against Microsoft Learn / kafka.apache.org / rabbitmq.com on 25 Aug 2026.

**How to use it:** 75 minutes available? Read §2 (the discriminators — *memorise the four one-liners*), Q12–Q14 (peek-lock, sessions, DLQ), Q51/Q53 (Kafka acks-ISR and rebalancing), §9 Q78 (the 2M-record worked design), §10 Q86–Q87 (idempotency + outbox), §13 (whiteboard), §14 (traps), §15 (rapid-fire). Skip §5 and §8 on a first pass only if you're out of time.

**Bridge from your stack:** a Service Bus queue is *Celery + Redis with the broker doing peek-lock instead of your worker holding the task*. `max_delivery_count` is Celery's `max_retries`; the DLQ is the `celery.failed` sink you always had to hand-roll. Kafka is *the append-only write-ahead log you already reason about in a vector DB's ingestion pipeline* — a consumer group offset is a cursor, not a delete. Event Grid is *a webhook fan-out service with a retry engine*. RabbitMQ's exchange/binding model is *a URL router: the routing key is the path, the binding is the route decorator*. Say those out loud — panels reward the mapping, and it is the fastest way to sound like you have used these rather than read about them.

**Platform-engineer framing (say this at least twice):** the deliverable is not "an app that reads a queue". It is **a golden consumer template** — a Python base class + Helm chart + KEDA scaler + Bicep module + dashboard — that any EY delivery team drops in and gets idempotency, DLQ handling, backoff-with-jitter, trace propagation and an alert pack for free. That is the paved road. Nobody gets to hand-roll a consumer.

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [Mental model: queue vs topic vs stream vs event bus](#1-mental-model-queue-vs-topic-vs-stream-vs-event-bus) | Q1–Q4 |
| 2 | [The Four Azure Services — the decision table and the script](#2-the-four-azure-services--the-decision-table-and-the-script) | Q5–Q9 |
| 3 | [Azure Service Bus](#3-azure-service-bus) | Q10–Q26 |
| 4 | [Service Bus in Python — sender, sessions, DLQ replay](#4-service-bus-in-python--sender-sessions-dlq-replay) | Q27–Q29 |
| 5 | [Azure Event Grid](#5-azure-event-grid) | Q30–Q38 |
| 6 | [Azure Event Hubs](#6-azure-event-hubs) | Q39–Q48 |
| 7 | [Apache Kafka](#7-apache-kafka) | Q49–Q68 |
| 8 | [RabbitMQ](#8-rabbitmq) | Q69–Q76 |
| 9 | [Batch meets stream — JD responsibility 4](#9-batch-meets-stream--jd-responsibility-4) | Q77–Q85 |
| 10 | [The patterns senior interviewers grill on](#10-the-patterns-senior-interviewers-grill-on) | Q86–Q100 |
| 11 | [Observability — JD responsibility 8](#11-observability--jd-responsibility-8) | Q101–Q105 |
| 12 | [The AWS mirror table](#12-the-aws-mirror-table) | — |
| 13 | [30-second whiteboard versions](#13-30-second-whiteboard-versions) | 3 |
| 14 | [Interviewer traps](#14-interviewer-traps) | 13 |
| 15 | [Rapid fire](#15-rapid-fire) | 60 |

Sibling files: [Azure Integration Services](02-azure-integration-services.md) · [API Design](01-api-design-rest-soap-graphql-openapi.md) · [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md) · [CI/CD & IaC](05-cicd-iac-and-gitops.md) · [Auth & Security](06-auth-and-security.md) · [Python for Integration](07-python-for-integration-and-coding-round.md) · [System Design](08-system-design-integration.md) · [Behavioural & HR](09-behavioral-ey-and-hr.md) · [GenAI → Integration Bridge](10-genai-to-integration-bridge.md) · [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md)

---

## 1. Mental model: queue vs topic vs stream vs event bus

### Q1. Before naming any product — what are the four shapes of asynchronous messaging?
`[MEDIUM]` `[THE FOUNDATION — every other answer in this file hangs off it]`

**Answer:** Four shapes, and the discriminator is *who owns the read cursor and what happens after a read*. A **queue** is competing consumers over a shared work list — the broker owns the cursor, one consumer wins each message, and reading destroys it. A **topic/subscription** is the same thing fanned out — the broker copies each message into N independent subscription queues, each with its own competing consumers. A **stream/log** is an append-only partitioned file — *the consumer* owns the offset, reading does not delete, and multiple independent readers replay the same bytes. An **event-notification bus** is a routing engine that pushes small facts at HTTP endpoints and forgets them once acknowledged.

The second discriminator is the **payload's meaning**. Microsoft's own vocabulary, which is worth using verbatim in an Azure interview: a **command** requests an action and must be processed exactly once in effect ("ChargeCard") — that is a queue. An **event** announces a fact and the publisher expects nothing back. Events split into **discrete events** ("BlobCreated" — individually meaningful, route it) and **event streams** ("temperature=41.2" — meaningful only in aggregate, window it).

```text
                     who owns the cursor?     read is destructive?   fan-out?
QUEUE ............... broker                  yes                    no (competing)
TOPIC+SUBSCRIPTION .. broker, per subscription yes, per subscription  yes (copy per sub)
STREAM / LOG ........ consumer (offset)       no (retention deletes) yes (N readers, same bytes)
EVENT BUS (push) .... broker, fire-and-forget yes (after 2xx)        yes (N subscriptions)

  command  -> queue          "do this"            ChargeCard, ReserveStock
  discrete event -> bus/topic "this happened"     BlobCreated, OrderApproved
  stream event -> log         "this is the value" tick data, telemetry, CDC rows
```

**If they push back — "Isn't a Kafka topic the same as a Service Bus topic?"** — No, and this is the single most common confusion. A Service Bus topic *copies* the message into each subscription and each copy is deleted when its subscriber completes it; there are as many physical messages as subscriptions. A Kafka topic stores **one** copy on disk and every consumer group tracks its own integer offset into it; adding a 20th consumer group costs zero storage and lets you replay from the beginning. Same word, opposite storage model. Service Bus topics do server-side content filtering; Kafka does not — Kafka consumers filter client-side or you use ksqlDB/Streams to materialise a filtered topic.

---

### Q2. What actually forces you to pick a stream over a queue?
`[MEDIUM]` `[senior discriminator]`

**Answer:** Three things, any one of which is decisive. **Replay** — if a downstream bug means you need to reprocess last Tuesday, only a log can do it; a queue's messages are gone. **Multiple independent consumers of the same data at different speeds** — a log lets fraud scoring, the data lake loader and the real-time dashboard read the same partition independently. **Volume above roughly a few thousand messages/second sustained**, where per-message broker bookkeeping (locks, delivery counts, DLQ state) becomes the bottleneck.

Conversely, three things force a queue: **per-message lifecycle** (I need to know *this* message failed, retry *this* one, and sideline *this* one to a DLQ), **competing consumers with server-managed at-least-once settlement**, and **server-side routing/filtering** so a subscriber only sees the subset it cares about.

Microsoft states this bluntly in its own comparison doc: Kafka "doesn't implement the competing-consumer queue pattern… has no facilities to track the lifecycle of a job initiated by a message or sidelining faulty messages into a dead-letter queue." Quoting that in an Azure interview lands well.

**If they push back — "Can't you build a DLQ on Kafka?"** — Yes, and everyone does: on failure the consumer produces the record to `<topic>.dlq` with the exception in a header, then commits the original offset. But *you* own retry counting, the poison-pill detection, the replay tool and the operator UI. That is three sprints of platform work Service Bus gives you as a checkbox. On a financial-services engagement where an auditor will ask "show me every payment message that failed and what you did about it", that matters.

---

### Q3. At-most-once, at-least-once, exactly-once — which do you actually get?
`[MEDIUM]` `[NEAR-CERTAIN]`

**Answer:** In practice you get **at-least-once**, and you make it *look* exactly-once by making the consumer idempotent. At-most-once is what you get with `ReceiveAndDelete` mode or `enable.auto.commit=true` committing before processing — fast, and you lose messages on a crash. At-least-once is peek-lock / commit-after-process — the default and the right default. True end-to-end exactly-once across a network boundary is impossible in the general case (two-generals); what Kafka calls exactly-once semantics is a *transaction spanning consume→process→produce inside Kafka only* — the moment your consumer writes to Postgres or calls a partner REST API, that guarantee stops at the broker boundary.

The senior phrasing: **"effectively-once = at-least-once delivery + an idempotent consumer."** Say that sentence; it is the answer.

| Guarantee | How you get it | Cost |
|---|---|---|
| At-most-once | `ServiceBusReceiveMode.RECEIVE_AND_DELETE`; Kafka auto-commit before processing | Message loss on crash |
| At-least-once | Peek-lock + complete after processing; Kafka manual commit after processing | Duplicates; you must dedupe |
| Effectively-once | At-least-once + idempotency key / natural key / dedupe table | One extra DB round-trip per message |
| Kafka EOS | `enable.idempotence=true` + transactional producer + `isolation.level=read_committed` | Only within Kafka; throughput cost; no help for external side effects |

**If they push back — "Azure Service Bus advertises duplicate detection, isn't that exactly-once?"** — Duplicate detection is a *send-side* feature: it deduplicates on `MessageId` within a configurable window (default 10 minutes, min 20 seconds, max 7 days) so a producer that retries after an ambiguous ack doesn't create two messages. It does nothing about the receive side — a consumer that crashes after processing but before `complete_message` will see that message again regardless. You need both: dup-detection on send, an idempotency table on receive.

---

### Q4. Ordering vs throughput — explain the tradeoff.
`[MEDIUM]` `[HIGH-FREQUENCY, and most candidates give a mush answer]`

**Answer:** Ordering and parallelism are in direct opposition, and every broker resolves it the same way: **order is guaranteed only within a partition/session key, never globally.** Kafka orders within a partition, chosen by hashing the message key. Service Bus orders within a session, chosen by `SessionId`. Event Hubs orders within a partition, chosen by `PartitionKey`. In all three, one key's messages go to exactly one consumer at a time, so your maximum parallelism equals your number of distinct active keys — and your throughput ceiling for a single hot key is one consumer.

So the design question is never "do I need ordering?" — it is **"what is the smallest scope over which I need ordering?"** Per-account, per-customer, per-order, per-instrument. Pick that as your key. If the honest answer is "globally", you have a single-threaded system and you should say so out loud and negotiate.

```text
Bad key choice:  session_id = "orders"          -> 1 session -> 1 consumer -> 200 msg/s ceiling
Good key choice: session_id = str(customer_id)  -> 400k sessions -> N consumers -> scales
Danger:          session_id = str(exchange_id)  -> 3 sessions, one is 95% of volume -> hot partition
```

**If they push back — "The client says every message must be processed in strict global order."** — Then push back with a question: is that a *processing* requirement or a *reporting* requirement? Usually it's the latter, and the fix is to process in parallel by key and use the broker's `SequenceNumber` (Service Bus stamps a gap-free increasing 64-bit sequence number per entity) or a Kafka offset to reconstruct global order at read time. If it genuinely is a processing requirement — a ledger with cross-account invariants — then you have a single-writer design, and the right answer is one consumer, one partition, and horizontal scale via sharding the *ledger*, not the queue.

---

## 2. The Four Azure Services — the decision table and the script

### Q5. Service Bus vs Event Grid vs Event Hubs vs Storage Queues. Go.
`[MEDIUM]` `[THE QUESTION. Expect it. This exact wording appears in Azure interviews constantly.]`

**Answer — the four one-line discriminators. Memorise these verbatim:**

> **Service Bus** — enterprise message broker. Use it when the message is a *command* that must not be lost, must be retried, may need ordering, and may need to be sidelined for a human to look at.
> **Event Grid** — reactive event router. Use it when something *happened* and you want to push a small notification at N subscribers over HTTP without either side knowing about the other.
> **Event Hubs** — big-data ingestion pipeline. Use it when the data is a *high-volume telemetry stream* that many consumers replay independently.
> **Storage Queue** — the cheap one. Use it when you need a simple, huge, dirt-cheap queue and you need none of Service Bus's features.

**Then the decision table:**

| | **Service Bus** | **Event Grid** | **Event Hubs** | **Storage Queue** |
|---|---|---|---|---|
| Shape | Queue + topic/sub | Push router | Partitioned log | Queue |
| Payload meaning | Command / high-value message | Discrete event (notification) | Stream event (telemetry) | Command |
| Delivery | Pull (long-poll AMQP) | **Push** (HTTP webhook) + pull option on Namespaces | Pull (consumer owns offset) | Pull (HTTP poll) |
| Ordering | **Yes, via sessions** | **No guarantee** | Yes, per partition | No |
| Replay | No | No | **Yes, up to retention** | No |
| Dead-lettering | **Built-in DLQ subqueue** | To a blob container | No (you build it) | No |
| Dup detection | **Yes** (MessageId, 20s–7d window) | No | No | No |
| Transactions | **Yes** (100 msgs/txn) | No | No | No |
| Max payload | 256 KB Std / **100 MB Premium** (AMQP) | **1 MB** | 1 MB Std, 256 KB Basic, 20 MB Dedicated | **64 KB** |
| Scale unit | Messaging Units (1/2/4/8/16) | Throughput Units (Namespaces) | TU / PU / CU | Storage account |
| Retention | Until consumed (TTL) | 1 day (topics), 7 days (namespace topics) | 1d Basic / 7d Std / **90d Premium+** | **7 days default, or never (`-1`)** |
| Protocol | AMQP 1.0, JMS 2.0 (Premium) | HTTP, **MQTT 3.1.1/5.0** (Namespaces) | AMQP, HTTP, **Kafka** | HTTP/REST |
| Cost shape | Per operation (Std) / per MU (Prem) | Per million operations | Per TU-hour + ingress | Cheapest by a mile |

**The 40-second spoken script (rehearse this out loud three times):**

> "I pick on what the message *is*. If it's a command that must not be lost — a payment instruction, an order — Service Bus, because I get peek-lock, a dead-letter queue, sessions for per-account ordering and duplicate detection. If it's a discrete notification — 'a blob landed', 'a resource changed' — Event Grid, because it pushes to subscribers over HTTP with a built-in retry policy and I don't want a consumer polling an idle queue. If it's a telemetry firehose that several teams want to read independently and replay — Event Hubs, because it's a partitioned log with consumer-group offsets and a Kafka endpoint. Storage Queue only when I need a very cheap, very large queue and none of Service Bus's features. And in real architectures I combine them: Event Grid notices the blob, drops a message on a Service Bus queue, and a scaled consumer does the work — that gives me the reactivity of Grid and the reliability of Service Bus."

That last sentence is the senior signal. Microsoft calls it a **crossover scenario** and documents it.

**If they push back — "Give me the one-sentence version."** — *"Grid for notifications, Bus for commands, Hubs for streams, Storage Queue for cheap."*

---

### Q6. "Notify me when a blob lands." Event Grid or Service Bus?
`[MEDIUM]` `[the classic follow-up to Q5]`

**Answer:** **Event Grid**, and specifically a **system topic** on the storage account — Blob Storage is a first-party event source, so `Microsoft.Storage.BlobCreated` is emitted for free with no polling and no code. Service Bus can't do it at all on its own, because Blob Storage doesn't write to a queue; you'd have to poll the container, which is exactly what Event Grid exists to eliminate.

But the *good* answer is: Event Grid to **notice**, Service Bus to **do the work**, if the work matters.

```text
Blob lands
  -> Storage account system topic emits Microsoft.Storage.BlobCreated
     -> Event Grid subscription, filtered:  subjectBeginsWith = "/blobServices/default/containers/inbound/"
                                            subjectEndsWith   = ".csv"
        -> delivers to a Service Bus QUEUE (a supported EG destination)
           -> KEDA-scaled Python consumer: claim-check the blob, process, complete
              -> failures land in the queue's $deadletterqueue with a delivery count
```

Why not deliver Event Grid straight to a Function? You can, and for cheap idempotent work you should. You add the Service Bus hop when you need any of: back-pressure/load-levelling against a fragile downstream, a DLQ with a replay story, ordering by session, more than Event Grid's retry budget, or a message bigger than 1 MB.

**If they push back — "Event Grid has retries and dead-lettering, why add Service Bus at all?"** — Event Grid's dead-letter target is a **blob container**, not a queue. That means replay is a batch job you write, not a receiver you point at `$deadletterqueue`. Also Event Grid explicitly gives **no ordering guarantee** and enters "probation" on an unhealthy endpoint — it will *skip* retries and delay delivery by up to several hours for a consistently failing subscriber. For a payments flow that's unacceptable; for a thumbnail generator it's fine. Match the guarantee to the value of the message.

---

### Q7. When is a Storage Queue actually the right answer?
`[EASY]` `[people forget it exists, which is itself a signal]`

**Answer:** Three cases. **Cost at volume** — Storage Queues are roughly an order of magnitude cheaper than Service Bus Standard for high-volume simple work. **Queue size beyond Service Bus entity limits** — a Service Bus queue caps at 80 GB; a Storage Queue is bounded only by the storage account (5 PiB default). **Auditability of the raw transaction log** — you can turn on storage analytics logging of every queue operation, which some regulated clients ask for.

Its limits, exactly: **64 KB** per message, max **32 messages** per `Get Messages` call, default visibility timeout **30 seconds** and a maximum of **7 days**, default TTL **7 days** (or `-1` for never-expire on REST API version 2017-07-29+), and a `DequeueCount` you must check yourself because there is no DLQ.

```python
# Poison-message handling on a Storage Queue is YOUR job — there is no DLQ.
# This is the guardrail that goes in the platform template.
MAX_DEQUEUE = 5
if msg.dequeue_count > MAX_DEQUEUE:
    poison_client.send_message(msg.content)   # your own "-poison" queue
    queue_client.delete_message(msg)
    continue
```

**If they push back — "Azure Functions creates a `-poison` queue automatically, doesn't it?"** — Correct, and that's the honest nuance: the Azure Functions Storage Queue trigger moves a message to `<queuename>-poison` after 5 dequeues by default. But that's a *Functions host* feature, not a Storage Queue feature. If you're consuming from a container on AKS — which is what this JD's responsibility 7 describes — you implement it yourself, which is exactly why it belongs in the shared consumer template.

---

### Q8. What is Azure Event Grid Namespaces and why does it change the picture?
`[HARD]` `[good-to-have depth; shows you're current]`

**Answer:** Event Grid now has two tiers with genuinely different shapes. The **Basic tier** is classic Event Grid: push delivery from custom topics, system topics, domains and partner topics. The **Standard tier** is the **Namespace** resource, which adds two things Event Grid never had: an **MQTT broker** (3.1.1 and 5.0, for IoT/device pub-sub) and **HTTP pull delivery** with queue-like semantics — receive, acknowledge, release, reject, renew-lock.

Pull delivery matters for this JD because it removes the "my consumer must expose a public HTTPS endpoint" problem. In a financial-services network where nothing is internet-reachable and Private Link is mandated, a pull consumer behind a private endpoint is often the only shape that passes review.

Namespace numbers worth knowing: max **40 throughput units** per namespace, **1,000 events/sec or 1 MB/sec ingress per TU**, up to **2,000 events/sec or 2 MB/sec egress per TU**, **100 namespace topics per TU**, **500 subscriptions per topic**, **7 days** max event retention (vs 1 day on classic topics), max event size **1 MB**, MQTT max message size **512 KB**, MQTT session expiry default **8 hours**.

**If they push back — "So why not use Namespaces for everything?"** — Because Microsoft's own guidance is explicit: if you need strictly ordered processing via sessions, transactions, or duplicate detection, use Service Bus. Event Grid pull delivery is optimised for high-throughput distribution of discrete events, not for enterprise message semantics. Namespaces solve the *connectivity* problem, not the *guarantee* problem.

---

### Q9. How do you stop 40 EY delivery teams each inventing their own messaging topology?
`[MEDIUM]` `[PLATFORM-ENGINEER FRAMING — this is the question the title implies]`

**Answer:** Governance in three layers: a **decision record**, **IaC modules that only permit the sanctioned shapes**, and **Azure Policy** that blocks anything else. Teams don't get a Service Bus namespace — they get a module call.

```hcl
# platform/modules/messaging-queue/main.tf  — the ONLY way a team gets a queue.
# Opinions are baked in: DLQ on, dup-detection on, sensible lock, TTL required.
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
  }
}

variable "name"            { type = string }
variable "namespace_id"    { type = string }
variable "requires_session" { type = bool, default = false }
variable "message_ttl"     { type = string  # ISO-8601, e.g. "P1D" — no unbounded queues
                             validation {
                               condition     = can(regex("^P", var.message_ttl))
                               error_message = "message_ttl must be an ISO-8601 duration, e.g. P1D."
                             } }

resource "azurerm_servicebus_queue" "this" {
  name         = var.name
  namespace_id = var.namespace_id

  # --- platform guardrails: not overridable by consuming teams ---
  dead_lettering_on_message_expiration     = true
  requires_duplicate_detection             = true
  duplicate_detection_history_time_window  = "PT10M"   # the Azure default, made explicit
  lock_duration                            = "PT1M"    # default; renew in code for longer work
  max_delivery_count                       = 10        # default; DLQ after 10 attempts
  default_message_ttl                      = var.message_ttl
  requires_session                         = var.requires_session
  max_size_in_megabytes                    = 5120
}

output "queue_name" { value = azurerm_servicebus_queue.this.name }
```

Then the platform ships: a **Helm chart** for the consumer with the KEDA `ScaledObject` pre-wired, a **Python base class** (§4) that every consumer subclasses, a **Grafana/Azure Monitor dashboard** JSON with the five queue metrics from §11, and an **alert pack**. A team's PR to onboard a new integration should be ~20 lines of YAML, not a new architecture.

**If they push back — "Isn't that over-engineering for one client?"** — It's not for one client; it's how a GDS unit gets leverage across engagements. The first engagement pays for the module, the next twelve consume it. That is the difference between a delivery team and a platform team, and it's the difference the "Platform Engineer" in the title is pointing at.

---

## 3. Azure Service Bus

### Q10. Walk me through Service Bus's object model.
`[EASY]` `[opener]`

**Answer:** A **namespace** is the scaling and security boundary — one FQDN, `<name>.servicebus.windows.net`, and on Premium it owns dedicated messaging units. Inside it live **queues** (one logical consumer group) and **topics** (broadcast). A topic has **subscriptions**, and each subscription behaves exactly like a queue with its own DLQ, delivery counts and lock semantics. Subscriptions carry **rules**, each of which is a **filter** plus an optional **action**. Every queue and subscription automatically has a **dead-letter subqueue** and, if it forwards, a **transfer dead-letter subqueue**.

```text
Namespace  (contoso-payments.servicebus.windows.net)
 ├─ Queue: payment-instructions
 │   ├─ $deadletterqueue
 │   └─ $Transfer/$DeadLetterQueue   (only if auto-forwarding / send-via)
 └─ Topic: trade-events
     ├─ Subscription: risk        rule: sql   "notional > 1000000"
     │    └─ $deadletterqueue
     ├─ Subscription: settlement  rule: correlation  Subject = "TradeConfirmed"
     └─ Subscription: audit       rule: TrueFilter  (everything)
```

Hard numbers: **2,000 subscriptions per topic**, **2,000 SQL filters per topic**, **100,000 correlation filters per topic**, filter condition string max **1,024 characters**, rule action max **1,024 characters** with max **32 expressions**, **10,000 queues+topics per namespace** on Standard (**1,000 per messaging unit, capped at 16,000** on Premium).

---

### Q11. SQL filters vs correlation filters — which and why?
`[MEDIUM]` `[very common; the throughput answer is the senior part]`

**Answer:** A **correlation filter** matches on exact equality against a fixed set of system properties (`CorrelationId`, `MessageId`, `Subject`/`Label`, `ReplyTo`, `To`, `SessionId`, `ContentType`) plus exact equality on user properties. A **SQL filter** evaluates a SQL92-subset boolean expression over system and user properties, so you get `>`, `LIKE`, `IN`, `AND/OR`, `IS NULL`.

**Prefer correlation filters.** They're hash-lookup cheap, which is why Azure allows **100,000** of them per topic but only **2,000** SQL filters. If your routing is "give me the events whose type is X", that's a correlation filter and it will scale. Reach for SQL only when you genuinely need a range or pattern predicate.

```xml
<!-- Correlation filter, ARM/Bicep shape -->
<Rule name="settlement-only">
  <Filter type="CorrelationFilter">
    <Subject>TradeConfirmed</Subject>
    <Properties>
      <Property key="assetClass" value="FX" />
    </Properties>
  </Filter>
</Rule>
```

```sql
-- SQL filter: only large non-INR trades, and stamp a priority the consumer can read
-- Filter:
notional > 1000000 AND currency <> 'INR' AND settlementDate IS NOT NULL
-- Action (SetRuleAction) — mutates the message copy delivered to THIS subscription only:
SET priority = 'high'; SET routedBy = 'risk-rule-v3'
```

The **action** part is the bit most candidates have never used: a rule action rewrites properties on the per-subscription copy, so `risk` sees `priority='high'` while `audit` sees the original. That's server-side enrichment with no compute.

**If they push back — "What happens if my SQL filter throws?"** — If `EnableDeadLetteringOnFilterEvaluationExceptions` is on, the offending message plus the error lands in that subscription's DLQ. Microsoft explicitly warns against leaving it on in production where messages routinely match no subscription, because you'll flood the DLQ. The correct production posture: keep a catch-all `TrueFilter` subscription (often the audit one) so every message has at least one match, and alert on its depth as an unrouted-message detector.

---

### Q12. Peek-lock vs receive-and-delete. Explain the lock lifecycle precisely.
`[MEDIUM]` `[NEAR-CERTAIN — and the numbers are where people fall down]`

**Answer:** `ReceiveAndDelete` settles the message the instant the broker puts it on the wire — at-most-once, zero round trips, and if your process dies the message is gone. `PeekLock` is the default and the right default: the broker hands you the message under an **exclusive lock**, other consumers can't see it, and you must explicitly settle with **complete**, **abandon**, **dead-letter** or **defer**.

The numbers: **default lock duration is 1 minute; the maximum configurable is 5 minutes.** If your processing can exceed that, you call `renew_message_lock()` — or better, register the message with an `AutoLockRenewer`. Every time a lock expires or you abandon, the message's **delivery count** increments; when it exceeds **MaxDeliveryCount (default 10)** the broker moves it to the DLQ with reason `MaxDeliveryCountExceeded`.

Three lock-loss traps that are pure interview gold:
1. **The lock is tied to the receiver and its connection.** Close the receiver before settling and the settlement never reaches the service — the message is redelivered and the delivery count climbs. Settle *inside* the `with` block.
2. **The service closes an idle connection after 10 minutes**, which drops the lock.
3. **Locks are volatile**: a service update, an OS update, or changing a property on the entity while you hold the lock will lose it. You get `MessageLockLostException`. Importantly, when the lock is lost this way, **the delivery count is not incremented**.

```text
receive (PeekLock)
   |-- lock granted, locked_until_utc = now + lock_duration (default 60s)
   |
   |-- complete_message()      -> removed. done.
   |-- abandon_message()       -> unlocked immediately, delivery_count += 1, back to front of queue
   |-- dead_letter_message()   -> DLQ, with your reason + description
   |-- defer_message()         -> stays, retrievable ONLY by sequence_number (you must store it)
   |-- (do nothing, lock expires)-> redelivered, delivery_count += 1
   |
   `-- delivery_count > MaxDeliveryCount (10) -> DLQ, reason MaxDeliveryCountExceeded
```

**If they push back — "Why not just set lock duration to 5 minutes everywhere?"** — Because the lock duration is also your **failure detection time**. If a consumer pod is OOM-killed holding a 5-minute lock, that message is invisible for 5 minutes. Keep the lock short (60s) and renew from code, so a dead pod's messages come back in seconds while a slow-but-alive pod keeps its lock. That's the platform default I'd bake into the module.

---

### Q13. Sessions. How do they give you FIFO, and what's the catch?
`[MEDIUM]` `[HIGH-VALUE — this is the "do you actually know Service Bus" question]`

**Answer:** A sender sets `SessionId` on the message (it maps to AMQP 1.0's `group-id`). On a session-enabled entity, a receiver **accepts a session** and takes an **exclusive lock on every message with that SessionId — including ones that haven't arrived yet**. Because only one receiver can hold a session at a time and it receives that session's messages in order, you get FIFO. **The ordering is per-session, never global.** Different sessions are dispatched to different receivers concurrently, so the entity as a whole is still parallel — sessions are how Service Bus demultiplexes one queue into N ordered sub-queues.

The catches, in order of how often they bite:
- **Enabling sessions is not optional per message.** Once `requiresSession=true`, a message sent without a `SessionId` is dead-lettered with reason `Session ID is null`. You cannot mix session and non-session traffic on one entity.
- **Message expiry is session-wide.** If *one* message in a session passes its TTL, the system drops or dead-letters **all** messages in that session.
- **Delivery count semantics change.** If the session lock expires, delivery count increments. If you close the session with messages locked but uncompleted, it does not.
- **Replaying a DLQ'd message breaks the order.** Microsoft says this explicitly: a dead-lettered message moved back to the queue gets a new enqueue time and sequence number, so its original position in the session is lost.
- **Throughput ceiling per session is one consumer.** Choose the key at the finest granularity your business rules allow.

**Session state** is a bonus most people don't know: `set_state()` / `get_state()` store an opaque blob (**256 KB on Standard, 100 MB on Premium**) against the session inside the broker. It survives consumer failure, so a new pod that accepts the session can read the last checkpoint and resume mid-workflow. That is a genuine distributed-checkpoint primitive and it's the cleanest answer to "how do you resume a partially-processed batch?" (see §9).

**If they push back — "How do you pick the session key on a payments system?"** — Not `"payments"`, and not the message type. Order matters per *account* (you can't apply a debit before the credit that funds it) so `SessionId = account_id`. That gives you millions of sessions, near-linear parallelism, and exactly the invariant the business cares about. If a single institutional account is 80% of volume you have a hot session and you escalate that as a design constraint rather than discovering it in production.

---

### Q14. Enumerate every reason a message ends up in the dead-letter queue.
`[MEDIUM]` `[EXACTLY the kind of enumerate-the-list question EY L1 asks]`

**Answer:** Five system reasons, plus filter-evaluation, plus application-initiated. The `DeadLetterReason` property tells you which.

| `DeadLetterReason` | Cause |
|---|---|
| `MaxDeliveryCountExceeded` | Delivered more than `MaxDeliveryCount` (default **10**) times without settling — abandoned, or lock expired, or you closed the receiver before settling |
| `TTLExpiredException` | Message exceeded its TTL and `deadLetteringOnMessageExpiration` is on. (Deferred messages are exempt — by design they are not purged on expiry) |
| `HeaderSizeExceeded` | Message header/properties exceeded the quota — each property max **32 KB**, cumulative all properties max **64 KB** |
| `Session ID is null` | Message sent without a `SessionId` to a session-enabled entity |
| `MaxTransferHopCountExceeded` | Auto-forward chain passed through more than **4** queues/topics |
| *(filter exception)* | `EnableDeadLetteringOnFilterEvaluationExceptions` is on and a subscription's SQL rule threw |
| *(anything you set)* | Application called `dead_letter_message(reason=..., error_description=...)` — put the exception type in reason and the stack trace in description |

Separately, the **transfer DLQ** (`<entity>/$Transfer/$DeadLetterQueue`) catches auto-forward/send-via failures and lives on the **source** entity, not the destination: destination disabled or deleted, or destination over its entity size.

Paths, which they sometimes ask for literally:
```text
<queue>/$deadletterqueue
<topic>/Subscriptions/<subscription>/$deadletterqueue
<queue>/$Transfer/$DeadLetterQueue
```

Two operational facts to volunteer: **there is no automatic cleanup of the DLQ** — messages sit there until you drain them, and they **count against the entity's storage quota**, so an unmonitored DLQ will eventually wedge the live queue. And **TTL is not observed on the DLQ**, so nothing ages out on its own.

**If they push back — "So how do you replay a DLQ?"** — Three tiers, and I'd name all three. For an operator, **Service Bus Explorer in the portal** peeks, edits and resubmits individually or in batches. For repeatable ops, a **replay job** (code in §4.3) that receives from `$deadletterqueue`, checks the reason, optionally repairs, resends to the main entity with a *new* `MessageId` and a `replayOf` property carrying the original, then completes the DLQ copy. For governance, that job runs as an **on-demand Azure DevOps pipeline with an approval gate** so a human authorises the replay and the audit trail is the pipeline run — which is exactly the control a financial-services auditor wants to see.

---

### Q15. What is deferral and when would you use it?
`[HARD]` `[differentiator — almost nobody knows this]`

**Answer:** `defer_message()` leaves the message in the entity but takes it out of the normal retrieval order. It becomes retrievable **only** by its `SequenceNumber`, which you must persist yourself. It's the answer to out-of-order arrival in a workflow: message 3 of a saga arrives before message 2, so you defer 3, record its sequence number against the correlation ID, and when 2 lands you fetch 3 back by number and process both.

Two things that make it interview-worthy: a deferred message is **not** dead-lettered on TTL expiry (by design), and if you lose the sequence number, the message is effectively orphaned — it will sit there consuming quota with no way to address it. So deferral always comes with a durable side table.

```python
# defer
seq = msg.sequence_number
receiver.defer_message(msg)
db.execute("INSERT INTO deferred (correlation_id, seq) VALUES (%s, %s)", (cid, seq))

# later, when the prerequisite arrives
rows = db.fetchall("SELECT seq FROM deferred WHERE correlation_id = %s ORDER BY seq", (cid,))
deferred = receiver.receive_deferred_messages(sequence_numbers=[r["seq"] for r in rows])
for m in deferred:
    process(m)
    receiver.complete_message(m)
```

**If they push back — "Why not just abandon and let it be redelivered?"** — Because abandon increments the delivery count, so a message waiting on a slow prerequisite will burn through `MaxDeliveryCount` and land in the DLQ for no reason. Deferral doesn't increment it. That's the whole point.

---

### Q16. Scheduled messages — what are they and what are the limits?
`[EASY-MEDIUM]`

**Answer:** Set `ScheduledEnqueueTimeUtc` on the message (or use the schedule API) and the message doesn't materialise in the queue until that instant. Before then it can be **cancelled**, which deletes it. The schedule API returns the scheduled message's `SequenceNumber` — that's the handle you cancel with. This is a reliable distributed time-based scheduler with no cron, no timer table and no Quartz.

Three gotchas worth stating: the sequence number returned is only valid while the message is in the scheduled state — on activation the message is appended as if enqueued now and gets a **new** `SequenceNumber`. Messages **larger than 1 MB can only be scheduled via the regular send API** with the property set, not the schedule API. And **there is no recurrence** — a message is enqueued once, so "every night at 2am" means your job schedules the next one when it processes the current one.

Use it for: retry-after-a-delay without a sleeping consumer, 2FA timeouts, "chase this unconfirmed trade in 30 minutes", and — in insurance/banking — genuinely long timers measured in weeks. Scheduled messages plus duplicate detection also gives you a cheap **debounce**.

**If they push back — "Isn't that what Durable Functions timers are for?"** — Both work; the difference is who owns the state. Durable Functions gives you the timer *inside* an orchestration with replay-based checkpointing (see [Azure Integration Services §6](02-azure-integration-services.md)). A scheduled Service Bus message is the right primitive when the waiting thing is a *message*, not an orchestration — no orchestrator instance sitting around, no history table growth, and any consumer can pick it up.

---

### Q17. Duplicate detection — how does it actually work?
`[MEDIUM]`

**Answer:** Enable it on the queue or topic and Service Bus tracks the **application-set `MessageId`** of every message sent during a rolling window. A new send with a previously-seen `MessageId` is **accepted (the send succeeds) and silently dropped**. No other part of the message is considered — same `MessageId`, different body, still dropped.

The window: **default 10 minutes, minimum 20 seconds, maximum 7 days.** Keep it as small as your producer's retry horizon, because every recorded ID must be matched against every new send — a 7-day window on a high-throughput entity is a real throughput tax. Not supported on Basic tier.

The critical design point is **`MessageId` must be derivable from business context**, not a fresh GUID. Microsoft's own example is `12345.2017/payment` — order number plus message subject. If a producer crashes mid-send and restarts, it must reconstruct the *same* ID, otherwise dedup does nothing.

Partitioning changes the key: with partitioning **enabled**, uniqueness is `MessageId + PartitionKey`; with it **disabled** (the default), `MessageId` alone. And scheduled messages participate — send a scheduled message then a duplicate non-scheduled one and the second is dropped.

**If they push back — "Then I don't need an idempotent consumer, right?"** — Wrong, and this is trap #4 in §14. Duplicate detection protects against *duplicate sends*. It does nothing about *duplicate deliveries*, which happen every time a consumer crashes between doing the work and calling `complete_message`. You need both.

---

### Q18. Transactions and "send via" — what can Service Bus actually make atomic?
`[HARD]`

**Answer:** Service Bus supports transactions that group operations against **one entity, or against a set of entities routed through one "send-via" entity**, into a single atomic unit. Up to **100 messages per transaction**. The classic use is the atomic **receive-and-send**: complete the input message and send the output message as one unit, so you can never have processed-but-not-forwarded or forwarded-but-not-processed.

`SendVia` (transfer queue) is the mechanism: you open a sender to the destination but declare a *via* entity, so the send is first written to the via entity in the same transaction as the receive-settlement, and Service Bus then transfers it. Failures in that transfer land in the **transfer DLQ of the source entity**.

**What it cannot do:** it is not a distributed transaction across Service Bus and your database. There is no two-phase commit with SQL Server, Cosmos or a partner API. That is precisely the gap the **transactional outbox** exists to fill (§10.2). Naming that boundary unprompted is a strong senior signal — it's the same point [Azure Integration Services §1](02-azure-integration-services.md) makes about Outbox not being in Microsoft's own pattern catalog.

**If they push back — "So how do you make DB-write-plus-message-send atomic?"** — You don't. You write the message into an outbox table in the *same local DB transaction* as the business write, and a relay publishes it afterwards with at-least-once semantics plus dedup on `MessageId`. §10.2 has the SQL and the poller.

---

### Q19. Auto-forwarding — what is it and where's the trap?
`[MEDIUM]`

**Answer:** A queue or subscription can be configured to automatically forward every message it receives to another queue or topic in the same namespace, with no consumer and no code. The canonical use is a topic whose subscriptions auto-forward into per-team queues, so publishers see one topic and each team owns a queue with its own DLQ and scaling.

The trap is the **hop limit: 4**. A message that passes through more than four chained entities is dead-lettered with `MaxTransferHopCountExceeded`. Chains grow accidentally — a "temporary" bridging queue added by another team is how you get to five. The other trap is that transfer failures (destination disabled, deleted, or over its size quota) land in the **source's** transfer DLQ, which nobody is watching. Add `TransferDeadLetterMessageCount` to the alert pack.

**If they push back — "Why not just have each team subscribe directly to the topic?"** — Often you should. Auto-forward earns its place when the consuming team needs entity-level settings the subscription can't give them independently, or when you're building a **messaging bridge** across namespaces/regions and want the topology declarative rather than a running relay process you have to operate.

---

### Q20. Standard vs Premium — what actually changes?
`[MEDIUM]` `[near-certain, and the numbers matter]`

**Answer:** Premium buys you **resource isolation** — dedicated CPU and memory in units called **messaging units**, purchasable as **1, 2, 4, 8 or 16** per namespace, adjustable at will and billed hourly on the highest allocation in that hour. Standard is shared multi-tenant capacity billed per operation with variable latency and a **1,000 operations/second** ceiling.

| | Standard | Premium |
|---|---|---|
| Max message size | **256 KB** | **100 MB** over AMQP (default 1 MB per entity, raise it per queue/topic); 1 MB for HTTP; **1 MB for any batch** |
| Namespace size | 400 GB | **1 TB per messaging unit** |
| Entities per namespace | 10,000 | 1,000 per MU, max 16,000 |
| Networking | IP firewall via ARM/CLI only | **VNet service endpoints, Private Endpoints, service tags, portal firewall** |
| Encryption | Microsoft-managed keys | **+ customer-managed keys (CMK)** |
| DR | Geo-disaster recovery (metadata) | **Geo-Replication (metadata *and* message data)** |
| JMS | JMS 1.1, queues only | **JMS 1.1 and JMS 2.0** |
| Partitioning | 16 partitions, per entity, at creation | Namespace-level, **1, 2 or 4** partitions, fixed at namespace creation; MUs must be a multiple |
| Express entities | Supported | **Not supported** (isolated runtime) |
| Availability zones | Yes | Yes |

Sizing rule from Microsoft: start at **1–2 MUs** (or 1 MU per partition); scale **down** below 25% CPU, scale **up** above 75% CPU, and scale up above **60% memory** because memory climbs fast.

For a financial-services engagement, Premium is usually forced by three non-performance reasons: **Private Link** (no public endpoints), **CMK** (client holds the key material), and **Geo-Replication** (RPO on message data, not just topology). Lead with those in an EY answer, not with throughput — it shows you think about compliance, which is what the FS business unit sells.

**If they push back — "Client says Premium is too expensive for a low-volume queue."** — Then the honest answer is Standard plus the claim-check pattern for large payloads, and I'd say so. But I'd also point out that Premium's price is per messaging unit per hour regardless of message count, so the comparison is not "Premium vs Standard for this queue", it's "one Premium namespace shared across the whole integration estate vs N Standard namespaces". Consolidating twelve teams' queues onto one 2-MU Premium namespace is usually cheaper *and* gets everyone Private Link. That's the platform argument.

---

### Q21. What's the JMS 2.0 support for, given nobody here writes Java?
`[EASY]` `[EY-shaped: it's a migration question]`

**Answer:** It exists so a client can lift an existing IBM MQ, ActiveMQ or WebLogic JMS application onto Azure with a configuration change and a driver swap rather than a rewrite. In an EY Digital Engineering context that is a very common first phase: move the broker to Premium Service Bus over AMQP with the JMS 2.0 client, prove parity, *then* strangle the Java app itself. Standard only supports a JMS 1.1 subset focused on queues, so a topic-using JMS workload forces Premium.

**If they push back — "Would you recommend that or a rewrite?"** — Broker-first, always. It de-risks: one variable changes, the app is untouched, and rollback is a connection string. A rewrite bundles broker migration and application migration into one change with no clean rollback point. Same reasoning as the strangler-fig approach in [System Design §7](08-system-design-integration.md).

---

### Q22. How do you authenticate to Service Bus without a connection string?
`[MEDIUM]` `[ties to `06-auth-and-security.md`]`

**Answer:** Microsoft Entra ID with a **managed identity** and Azure RBAC. Three built-in roles: **Azure Service Bus Data Owner**, **Data Sender**, **Data Receiver**. On AKS this is **Workload Identity** — the pod's service account is federated to a user-assigned managed identity, `DefaultAzureCredential` picks up the projected token, and there is no secret anywhere. Connection strings (SAS) are the fallback for on-prem senders and legacy clients that can't do OAuth; scope those to a single entity, never the namespace, and rotate on a schedule.

```python
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient

# On AKS with Workload Identity, or locally with az login — same code, no secrets.
client = ServiceBusClient(
    fully_qualified_namespace="contoso-payments.servicebus.windows.net",
    credential=DefaultAzureCredential(),
)
```

**If they push back — "What about a partner sending us messages from their own datacentre?"** — They don't get to send to Service Bus directly. They call an APIM-fronted REST endpoint with client-certificate mTLS or OAuth2 client credentials, and APIM (or a thin Function behind it) is the only thing holding a Service Bus identity. That keeps the broker off the internet, gives you throttling and schema validation at the edge, and gives the auditor one place to look. Details in [Auth & Security](06-auth-and-security.md) and [Azure Integration Services §3](02-azure-integration-services.md).

---

### Q23. Give me the Bicep for a session-enabled queue with all the guardrails.
`[MEDIUM]` `[IaC is JD responsibility 6 — have one block ready]`

```bicep
// modules/servicebus-queue.bicep — the platform's golden queue.
@description('Existing Service Bus namespace name.')
param namespaceName string

@description('Queue name, lowercase-hyphenated.')
param queueName string

@description('Enable sessions for per-key FIFO.')
param requiresSession bool = false

@description('ISO-8601 message TTL. Unbounded queues are not permitted.')
param defaultMessageTimeToLive string = 'P1D'

@description('Max message size in KB. Premium only; 1024 default, up to 102400.')
@minValue(1024)
@maxValue(102400)
param maxMessageSizeInKilobytes int = 1024

resource namespace 'Microsoft.ServiceBus/namespaces@2021-11-01' existing = {
  name: namespaceName
}

resource queue 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = {
  parent: namespace
  name: queueName
  properties: {
    lockDuration: 'PT1M'                             // 60s; renew in code for longer work
    maxDeliveryCount: 10                             // DLQ on the 11th attempt
    requiresSession: requiresSession
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'     // Azure default, stated explicitly
    deadLetteringOnMessageExpiration: true           // never silently drop
    defaultMessageTimeToLive: defaultMessageTimeToLive
    maxSizeInMegabytes: 5120
    maxMessageSizeInKilobytes: maxMessageSizeInKilobytes
    enablePartitioning: false                        // Premium partitions at namespace level
    enableBatchedOperations: true
  }
}

output queueName string = queue.name
output queueId string = queue.id
```

**If they push back — "Why Bicep and not Terraform?"** — On a Microsoft-shop client with Azure-only scope, Bicep wins: no state file to secure, ARM does the drift detection, and `what-if` gives a plan. The moment the estate spans AWS or needs non-Azure providers (GitHub, Datadog, Entra app registrations), Terraform wins because one state and one plan covers everything. I'd hold both and pick per engagement. See [CI/CD & IaC](05-cicd-iac-and-gitops.md).

---

### Q24. How do you autoscale a Service Bus consumer on AKS?
`[MEDIUM]` `[bridges to JD responsibility 7]`

**Answer:** **KEDA** with the `azure-servicebus` scaler, scaling on **queue length**, with Workload Identity for auth so there's no connection string in the cluster. KEDA drives a standard HPA underneath, so the Kubernetes mechanics are unchanged — KEDA just supplies an external metric that the HPA couldn't get on its own. Crucially it can scale **to zero**, which plain HPA cannot.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: payment-consumer
  namespace: integration
spec:
  scaleTargetRef:
    name: payment-consumer          # the Deployment
  minReplicaCount: 0                # scale to zero between batch windows
  maxReplicaCount: 30
  pollingInterval: 15               # seconds between metric checks
  cooldownPeriod: 300               # seconds at zero-activity before scaling to 0
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: payment-instructions
        namespace: contoso-payments
        messageCount: "20"          # target backlog per replica
      authenticationRef:
        name: azure-workload-identity
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: azure-workload-identity
  namespace: integration
spec:
  podIdentity:
    provider: azure-workload
```

Two platform details: set `terminationGracePeriodSeconds` on the Deployment longer than your worst-case message processing time so a scale-down doesn't kill a consumer mid-message, and handle `SIGTERM` (code in §4.3) so the pod stops accepting new messages and finishes in flight. Without both, scaling down manufactures redeliveries and inflates delivery counts toward the DLQ.

**If they push back — "Why not just scale on CPU?"** — Because a queue consumer's CPU is near zero while it waits on I/O, so CPU-based HPA never scales up under backlog and never scales down when idle. The signal that matters is **backlog**, not utilisation. Same reason you'd scale a Kafka consumer on **consumer group lag**, not CPU. More in [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md).

---

### Q25. A message is stuck being redelivered forever. Debug it.
`[MEDIUM]` `[troubleshooting = JD responsibility 9]`

**Answer:** It isn't stuck forever — it will DLQ after `MaxDeliveryCount`. The question is why it's failing. I'd work down five causes in order:

1. **The consumer is throwing before settling.** Check logs correlated by `MessageId`. If the same `MessageId` appears with an incrementing `delivery_count`, it's a genuine processing failure — a poison message. Fix: catch, classify, and `dead_letter_message()` immediately for non-retryable errors instead of letting it burn ten attempts.
2. **Lock expiry — the work takes longer than the lock.** Symptom: no exception in the logs, but delivery count climbs and you see `MessageLockLostException` on `complete`. Fix: `AutoLockRenewer` or a shorter unit of work.
3. **Settling after the receiver closed.** Symptom: reason is `MaxDeliveryCountExceeded` and logs show receiver-closed/lock-lost on complete. Fix: settle inside the receiver's scope.
4. **A pod is being SIGKILLed** — OOM, or `terminationGracePeriodSeconds` too short. Symptom: delivery counts climb in lockstep with pod restarts. Check `kubectl get events` and the OOMKilled reason.
5. **Downstream is down** and every attempt fails identically. Symptom: every message's delivery count climbs together, not just one. This is not a poison message, it's an outage — the fix is a circuit breaker that stops consuming rather than a DLQ that fills with 200k valid messages.

Distinguishing 5 from 1 is the senior move: **one message failing is a poison message; all messages failing is an outage, and DLQing them all is the wrong response.**

```python
# Classify before you retry. This belongs in the shared consumer base class.
try:
    handle(payload)
except (ValidationError, SchemaError, json.JSONDecodeError) as exc:
    # Deterministic. Retrying 10 times changes nothing and delays the DLQ signal.
    receiver.dead_letter_message(
        msg,
        reason=type(exc).__name__,
        error_description=traceback.format_exc()[:4096],
    )
except (httpx.ConnectError, httpx.ReadTimeout, TransientDbError):
    receiver.abandon_message(msg)   # transient: let delivery_count + backoff do its job
    circuit.record_failure()        # and trip the breaker if this keeps happening
```

**If they push back — "How do you prove to the client which of the five it was?"** — The DLQ message carries `DeadLetterReason` and `DeadLetterErrorDescription`; if the consumer template always writes the exception type into reason and the stack trace into description, the DLQ *is* the evidence. Plus an Application Insights query joining on `MessageId` gives the full attempt history. That's the runbook entry, and writing runbooks is JD responsibility 9.

---

### Q26. 30-second whiteboard: draw Service Bus message flow.
`[reference]`

```text
                      +----------------------------------------+
  Producer  --send-->  |  TOPIC  trade-events                   |
  (MessageId=          |    dup-detect window PT10M on MessageId|
   "TRD-9931.confirm") +--+----------------+----------------+---+
                          |                |                |
              SQL filter  |    Correlation |     TrueFilter |
              notional>1M |    Subject=    |     (catch-all,|
                          |    TradeConfirmed    unrouted    |
                          |                |     detector)  |
                     +----v----+      +----v----+      +----v----+
                     | sub:risk|      |sub:settle|     |sub:audit|
                     +----+----+      +----+-----+     +----+----+
                          | peek-lock (60s, renewable to 5m)
                     +----v-------------------------+
                     | consumer pods (KEDA, msg=20) |
                     +----+-------------------+-----+
                          | complete          | abandon / lock expiry
                          v                   v  delivery_count += 1
                        gone            back to front of queue
                                              |
                                    > MaxDeliveryCount (10)
                                              v
                              sub:risk/$deadletterqueue
                              reason=MaxDeliveryCountExceeded
                                              |
                                   replay job (approval-gated)
                                     new MessageId + replayOf
                                              v
                                        back to topic
```

---

## 4. Service Bus in Python — sender, sessions, DLQ replay

> These three files *are* the "golden consumer template" from Q9. Read them once; you only need to be able to sketch the shape on a whiteboard, not recite them.

### Q27. Show me a producer that handles batching, claim-check and trace propagation.
`[MEDIUM]` `[CODE — they may ask you to write a chunk of this live]`

```python
"""platform_messaging/sender.py — the sanctioned Service Bus producer."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.blob import BlobServiceClient
from opentelemetry import trace
from opentelemetry.propagate import inject

# Service Bus Standard caps a message at 256 KB *including* system + user properties.
# Leave headroom for the properties we add; anything larger takes the claim-check path.
CLAIM_CHECK_THRESHOLD_BYTES = 192 * 1024

tracer = trace.get_tracer(__name__)


class PlatformSender:
    def __init__(
        self,
        namespace: str,
        entity: str,
        claim_check_account_url: str,
        claim_check_container: str = "claim-check",
    ) -> None:
        credential = DefaultAzureCredential()
        self._client = ServiceBusClient(
            fully_qualified_namespace=namespace, credential=credential
        )
        self._sender = self._client.get_queue_sender(queue_name=entity)
        self._blobs = BlobServiceClient(
            account_url=claim_check_account_url, credential=credential
        )
        self._container = claim_check_container

    # ---------- message construction ----------

    def build(
        self,
        payload: dict[str, Any],
        *,
        message_id: str,
        session_id: str | None = None,
        subject: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        schedule_utc: datetime | None = None,
        ttl: timedelta | None = None,
    ) -> ServiceBusMessage:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        props: dict[str, Any] = {
            "schemaVersion": "1",
            "causationId": causation_id or "",
        }

        # --- claim check: broker carries the pointer, blob carries the payload ---
        if len(body) > CLAIM_CHECK_THRESHOLD_BYTES:
            blob_name = f"{message_id}/{uuid.uuid4()}.json"
            container = self._blobs.get_container_client(self._container)
            try:
                container.create_container()
            except ResourceExistsError:
                pass
            container.upload_blob(name=blob_name, data=body, overwrite=False)
            props["claimCheck"] = "blob"
            props["claimCheckContainer"] = self._container
            props["claimCheckBlob"] = blob_name
            props["claimCheckBytes"] = len(body)
            body = b"{}"   # the pointer message carries no payload

        # --- W3C trace context rides in application properties, not the body ---
        carrier: dict[str, str] = {}
        inject(carrier)                      # writes traceparent (+ tracestate if present)
        props.update(carrier)

        msg = ServiceBusMessage(
            body=body,
            message_id=message_id,           # duplicate detection keys on THIS
            session_id=session_id,           # per-key FIFO; required if requiresSession
            subject=subject,                 # maps to Label; correlation filters match it
            correlation_id=correlation_id or message_id,
            content_type="application/json",
            application_properties=props,
        )
        if schedule_utc is not None:
            msg.scheduled_enqueue_time_utc = schedule_utc
        if ttl is not None:
            msg.time_to_live = ttl
        return msg

    # ---------- sending ----------

    def send_one(self, msg: ServiceBusMessage) -> None:
        with tracer.start_as_current_span("servicebus.send"):
            self._sender.send_messages(msg)

    def send_many(self, messages: Iterable[ServiceBusMessage]) -> int:
        """Batch up to the broker's limit; ValueError signals 'batch full, flush it'.

        Batches cap at 1 MB on every tier and every protocol — including Premium,
        where a *single* message may be 100 MB but a batch may not.
        """
        sent = 0
        batch = self._sender.create_message_batch()
        for msg in messages:
            try:
                batch.add_message(msg)
            except ValueError:
                self._sender.send_messages(batch)
                sent += len(batch)
                batch = self._sender.create_message_batch()
                batch.add_message(msg)
        if len(batch) > 0:
            self._sender.send_messages(batch)
            sent += len(batch)
        return sent

    def close(self) -> None:
        self._sender.close()
        self._client.close()


if __name__ == "__main__":
    sender = PlatformSender(
        namespace="contoso-payments.servicebus.windows.net",
        entity="payment-instructions",
        claim_check_account_url="https://contosointegration.blob.core.windows.net",
    )
    try:
        msg = sender.build(
            {"account": "GB29NWBK60161331926819", "amount": "1250.00", "ccy": "GBP"},
            message_id="PMT-2026-08-25-0009931",   # derivable from business context, NOT a GUID
            session_id="GB29NWBK60161331926819",   # order matters per account
            subject="PaymentInstructionReceived",
            schedule_utc=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        sender.send_one(msg)
    finally:
        sender.close()
```

**The three things to point at when you walk someone through this:** `message_id` is business-derived so duplicate detection actually works; the claim-check threshold is 192 KB not 256 KB because properties count toward the limit; and `inject(carrier)` is what makes the trace survive the broker hop (§11).

**If they push back — "Why `send_messages` in a batch instead of a loop of awaits?"** — A loop of awaited sends costs one full round trip each; Microsoft's own guidance shows ten sequential sends at 70 ms RTT taking 8 seconds versus well under one second when overlapped or batched. But never fire-and-forget without checking the result — that fills the client's invisible task queue until memory exhaustion and hides send errors.

---

### Q28. Show me a session receiver.
`[MEDIUM]` `[CODE]`

```python
"""platform_messaging/session_consumer.py — per-key FIFO consumer with checkpointing."""
from __future__ import annotations

import json
import logging

from azure.identity import DefaultAzureCredential
from azure.servicebus import (
    NEXT_AVAILABLE_SESSION,
    AutoLockRenewer,
    ServiceBusClient,
)
from azure.servicebus.exceptions import OperationTimeoutError

log = logging.getLogger(__name__)


def run_session_consumer(namespace: str, queue: str) -> None:
    client = ServiceBusClient(namespace, DefaultAzureCredential())

    # Renews BOTH the session lock and individual message locks in a background thread.
    # Cap it: an unbounded renewer will hold a session open through a hung handler.
    renewer = AutoLockRenewer(max_lock_renewal_duration=600)

    with client:
        while True:
            try:
                # NEXT_AVAILABLE_SESSION blocks until any unlocked session has messages.
                receiver = client.get_queue_receiver(
                    queue_name=queue,
                    session_id=NEXT_AVAILABLE_SESSION,
                    max_wait_time=30,
                )
            except OperationTimeoutError:
                continue   # no session became available in the window; loop

            with receiver:
                session = receiver.session
                renewer.register(receiver, session, max_lock_renewal_duration=600)
                log.info("acquired session %s", session.session_id)

                # Session state is a broker-side checkpoint: 256 KB Standard / 100 MB Premium.
                raw_state = session.get_state()
                state = json.loads(raw_state) if raw_state else {"processed": 0}

                for msg in receiver:
                    renewer.register(receiver, msg, max_lock_renewal_duration=300)
                    try:
                        payload = json.loads(b"".join(msg.body))
                        handle_in_order(session.session_id, payload)
                    except Exception:
                        log.exception(
                            "handler failed session=%s message_id=%s delivery_count=%s",
                            session.session_id, msg.message_id, msg.delivery_count,
                        )
                        # Abandon, not dead-letter: in a FIFO session, skipping a message
                        # silently corrupts the ordering guarantee the session exists for.
                        receiver.abandon_message(msg)
                        break   # release the session so a healthy pod can retry from here

                    receiver.complete_message(msg)
                    state["processed"] += 1
                    state["lastMessageId"] = msg.message_id
                    session.set_state(json.dumps(state).encode("utf-8"))

                log.info("session %s done, processed=%s", session.session_id, state["processed"])


def handle_in_order(session_id: str, payload: dict) -> None:
    ...  # your business logic; guaranteed to see this session's messages in order
```

**If they push back — "Why `break` out of the session on failure instead of dead-lettering?"** — Because the entire value proposition of a session is ordered processing. If message 4 fails and I DLQ it and carry on with 5, I have silently violated the guarantee — and Microsoft warns that a replayed DLQ message gets a new sequence number, so I can never restore the order. Releasing the session lets the message be retried in place. It also means one poison message stalls one account, not the whole queue, which is the right blast radius. The escape hatch is the delivery count: after ten attempts the broker DLQs it anyway and the session unblocks, and by then my DLQ-depth alert has already paged someone.

---

### Q29. Write the DLQ replay handler, with graceful shutdown.
`[HARD]` `[CODE — explicitly requested territory; also the runbook artefact]`

```python
"""platform_messaging/dlq_replay.py

Drain a dead-letter queue, optionally repair, and resubmit to the live entity.
Designed to run as a Kubernetes Job triggered from an approval-gated pipeline,
so every replay has a named approver and an audit trail.

    python -m platform_messaging.dlq_replay \
        --namespace contoso-payments.servicebus.windows.net \
        --queue payment-instructions \
        --reason MaxDeliveryCountExceeded \
        --max 5000 --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
import uuid
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.servicebus import (
    ServiceBusClient,
    ServiceBusMessage,
    ServiceBusSubQueue,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dlq-replay")

_shutdown = threading.Event()


def _on_signal(signum: int, _frame: Any) -> None:
    # SIGTERM arrives on pod eviction / scale-down / Job cancellation.
    # Set the flag; do NOT exit here — in-flight messages must be settled first.
    log.warning("received signal %s — draining, will not take new messages", signum)
    _shutdown.set()


signal.signal(signal.SIGTERM, _on_signal)
signal.signal(signal.SIGINT, _on_signal)


def repair(reason: str | None, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return a repaired payload, or None to leave the message in the DLQ."""
    if reason == "TTLExpiredException":
        return payload                              # stale but valid; resubmit as-is
    if reason == "MaxDeliveryCountExceeded":
        return payload                              # downstream was down; retry now
    if reason in {"ValidationError", "SchemaError"}:
        return None                                 # deterministic; a human must fix it
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--subscription", default=None, help="set to replay a topic sub's DLQ")
    ap.add_argument("--topic", default=None)
    ap.add_argument("--reason", default=None, help="only replay this DeadLetterReason")
    ap.add_argument("--max", type=int, default=1000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    client = ServiceBusClient(args.namespace, DefaultAzureCredential())
    replayed = skipped = 0

    with client:
        if args.topic and args.subscription:
            dlq = client.get_subscription_receiver(
                topic_name=args.topic,
                subscription_name=args.subscription,
                sub_queue=ServiceBusSubQueue.DEAD_LETTER,
                max_wait_time=10,
            )
            sender = client.get_topic_sender(topic_name=args.topic)
        else:
            dlq = client.get_queue_receiver(
                queue_name=args.queue,
                sub_queue=ServiceBusSubQueue.DEAD_LETTER,
                max_wait_time=10,
            )
            sender = client.get_queue_sender(queue_name=args.queue)

        with dlq, sender:
            while replayed + skipped < args.max and not _shutdown.is_set():
                batch = dlq.receive_messages(max_message_count=20, max_wait_time=10)
                if not batch:
                    log.info("dead-letter queue drained")
                    break

                for msg in batch:
                    reason = msg.dead_letter_reason
                    desc = msg.dead_letter_error_description

                    if args.reason and reason != args.reason:
                        dlq.abandon_message(msg)     # leave it for a different run
                        skipped += 1
                        continue

                    body = b"".join(msg.body)
                    try:
                        payload = json.loads(body) if body else {}
                    except json.JSONDecodeError:
                        log.error("unparseable dlq message %s reason=%s", msg.message_id, reason)
                        dlq.abandon_message(msg)
                        skipped += 1
                        continue

                    fixed = repair(reason, payload)
                    if fixed is None:
                        log.info("leaving %s in dlq (reason=%s)", msg.message_id, reason)
                        dlq.abandon_message(msg)
                        skipped += 1
                        continue

                    if args.dry_run:
                        log.info("DRY RUN would replay %s reason=%s desc=%.120s",
                                 msg.message_id, reason, desc or "")
                        dlq.abandon_message(msg)
                        skipped += 1
                        continue

                    # New MessageId: the original is inside the duplicate-detection
                    # window, so reusing it would make the resend a silent no-op.
                    props = dict(msg.application_properties or {})
                    props.update({
                        "replayOf": msg.message_id,
                        "replayReason": reason or "",
                        "replayRunId": RUN_ID,
                    })
                    resend = ServiceBusMessage(
                        body=body,
                        message_id=f"{msg.message_id}:replay:{RUN_ID}",
                        session_id=msg.session_id,
                        subject=msg.subject,
                        correlation_id=msg.correlation_id,
                        content_type=msg.content_type,
                        application_properties=props,
                    )

                    # Order matters: send FIRST, complete SECOND. A crash between the
                    # two gives a duplicate (recoverable); the reverse loses the message.
                    sender.send_messages(resend)
                    dlq.complete_message(msg)
                    replayed += 1

    log.info("replay finished run_id=%s replayed=%s skipped=%s shutdown=%s",
             RUN_ID, replayed, skipped, _shutdown.is_set())
    return 0


RUN_ID = uuid.uuid4().hex[:12]

if __name__ == "__main__":
    sys.exit(main())
```

**The three points to make out loud about this file:** (1) **send-then-complete, never the reverse** — you choose duplicates over loss, and the new `MessageId` plus an idempotent consumer absorbs the duplicate; (2) **a new `MessageId` is mandatory** because reusing the original inside the dedup window makes the resend a silent no-op — that is a genuinely nasty production bug and knowing it marks you out; (3) **SIGTERM sets a flag rather than exiting** so in-flight messages get settled, which is the same discipline every consumer on AKS needs (see [Microservices, Containers & Kubernetes §3](04-microservices-containers-kubernetes.md) on PID 1 and signals).

**If they push back — "How do you stop someone replaying 200,000 messages by accident?"** — Three controls. `--max` is mandatory and defaults low. `--dry-run` is the documented first step in the runbook. And the Job only runs from an Azure DevOps pipeline with an environment approval gate, so the replay is authorised by a named person and the pipeline run *is* the audit record. On a banking engagement that last control is not optional — it's what makes the operation defensible in a regulatory review.

---

## 5. Azure Event Grid

### Q30. What is Event Grid, in one paragraph?
`[EASY]`

**Answer:** Event Grid is a fully-managed **event routing service** built on push. Publishers send small events to a **topic**; **event subscriptions** attached to that topic each declare a filter and a handler endpoint; Event Grid delivers a matching event to each handler over HTTP and retries on failure according to a fixed exponential schedule. It is **at-least-once**, gives **no ordering guarantee**, and it is not storage — an event lives at most **1 day** on a classic topic (7 days on a Namespace topic) and there is no replay.

The reason it exists is that the alternative — every service polling every other service — doesn't scale and costs money while idle. Event Grid inverts it: nothing polls, and you pay per operation.

---

### Q31. Topic types: system, custom, domain, partner. Distinguish them.
`[MEDIUM]` `[enumerate-the-list question]`

| Type | What it is | Use when |
|---|---|---|
| **System topic** | Built into a first-party Azure resource (Storage, Key Vault, Resource Groups, Event Hubs, ACR, Media Services…). Free, no provisioning, fixed event schema | "React to Azure itself" — blob landed, secret near expiry, image pushed |
| **Custom topic** | You create it; your application publishes to its endpoint | Your own domain events — `TradeConfirmed`, `PolicyIssued` |
| **Domain** | A *management* construct: one endpoint, up to **100,000 topics** inside it, one subscription-per-tenant | Multi-tenant SaaS — one publish endpoint, per-tenant isolation and authorisation without 100,000 resources |
| **Partner topic** | A third-party SaaS (Auth0, Tribal, SAP…) publishes into your Azure subscription via the Partner Events model | SaaS→Azure integration without the SaaS holding your credentials |

Limits worth quoting: **100 custom topics per Azure subscription per region**, **500 event subscriptions per topic** (100 for subscriptions scoped at the Azure-subscription level, and that one cannot be raised), **100 domains per subscription**, **50 domain-scope event subscriptions**, publish rate **5,000 events or 5 MB/sec** per custom topic or domain, and **event size 1 MB, which cannot be increased**. Note the billing quirk: an "event" for quota and pricing is a **64 KB chunk**, so a 128 KB event counts as two.

**If they push back — "When would you pick a domain over 100 custom topics?"** — When the tenants are opaque to you and you want a single publish endpoint plus per-tenant RBAC. The domain gives you one place to publish and Event Grid does the routing to the per-tenant topic; you avoid 100 ARM resources, 100 endpoints and 100 sets of keys. That's exactly the shape in [System Design §8](08-system-design-integration.md) for multi-tenant SaaS integration.

---

### Q32. EventGridEvent schema vs CloudEvents 1.0 — which and why?
`[MEDIUM]` `[a "are you current?" question]`

**Answer:** **CloudEvents 1.0**, always, for new work. It's a CNCF open specification with bindings for HTTP, AMQP, MQTT and Kafka, so the same envelope survives the whole journey rather than being translated at every hop. Microsoft's own guidance now says to prefer it and calls the Event Grid schema "proprietary, non-extensible" — use it only when you can't use CloudEvents. Event Grid Namespaces support CloudEvents only.

**CloudEvents 1.0** — required attributes are `specversion`, `id`, `source`, `type`:

```json
{
  "specversion": "1.0",
  "id": "TRD-9931-confirm",
  "source": "/ey/contoso/trading/booking-service",
  "type": "com.contoso.trading.TradeConfirmed",
  "time": "2026-08-25T09:14:02.113Z",
  "subject": "trades/TRD-9931",
  "datacontenttype": "application/json",
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "data": { "tradeId": "TRD-9931", "notional": 4250000, "ccy": "USD" }
}
```

**EventGridEvent schema** — the older, Azure-specific envelope:

```json
{
  "id": "TRD-9931-confirm",
  "topic": "/subscriptions/.../providers/Microsoft.EventGrid/topics/trading",
  "subject": "trades/TRD-9931",
  "eventType": "Contoso.Trading.TradeConfirmed",
  "eventTime": "2026-08-25T09:14:02.113Z",
  "dataVersion": "1.0",
  "metadataVersion": "1",
  "data": { "tradeId": "TRD-9931", "notional": 4250000, "ccy": "USD" }
}
```

Map the fields when you speak: `eventType`→`type`, `eventTime`→`time`, `dataVersion`→(gone; use `type` versioning or an extension attribute), `topic`→`source`. `id` and `subject` are the same in both. **CloudEvents has no `dataVersion`** — you version in the `type` string (`...TradeConfirmed.v2`) or an extension attribute, and that catches people out.

**If they push back — "Does the schema choice actually matter?"** — Yes, for two reasons that are architectural, not cosmetic. First, the CloudEvents `traceparent` extension attribute is a *standard* place to put W3C trace context, so distributed tracing works across broker hops without a bespoke convention per team (§11). Second, the same CloudEvents envelope is what Dapr, Knative, Kafka and MQTT all speak, so an event that starts life in Event Grid can be consumed by a Kafka client without a translation layer. That's a real portability argument on a client who is not 100% Azure.

---

### Q33. Give me Event Grid's retry policy exactly.
`[HARD]` `[HIGH-VALUE — verified numbers; almost nobody can quote these]`

**Answer:** Event Grid waits **30 seconds** for a response after delivering. If none arrives, it queues the event for retry. The **exponential backoff schedule, best-effort**, is:

```text
10 s -> 30 s -> 1 min -> 5 min -> 10 min -> 30 min -> 1 h -> 3 h -> 6 h -> every 12 h up to 24 h
```

A small randomisation is added to every step, and Event Grid may **skip** retries entirely if the endpoint is consistently unhealthy.

The retry policy has two knobs and **whichever expires first wins**: **max delivery attempts, 1–30, default 30**, and **event time-to-live, 1–1440 minutes, default 1440**. Microsoft's own worked example: at TTL 30 minutes, the schedule only fits ~6 attempts, so setting max attempts to 10 changes nothing.

**Only 200, 201, 202, 203 and 204 count as success.** Everything else is a failure. Specific behaviours:

| Status | Behaviour |
|---|---|
| 400 Bad Request | **Not retried** — dead-lettered immediately |
| 413 Payload Too Large | **Not retried** — dead-lettered immediately |
| 403 Forbidden | **Not retried** |
| 401 Unauthorized | Not retried for webhooks; retried after ≥5 min for Azure resource endpoints |
| 404 Not Found | Retry after ≥5 minutes (Azure resource endpoints) |
| 408 Request Timeout | Retry after ≥2 minutes |
| 503 Service Unavailable | Retry after ≥30 seconds |
| All others | Retry after ≥10 seconds |

Dead-lettering: **off by default** — if you don't configure it, failed events are **dropped**. When on, the target is a **blob container**. There is a deliberate **five-minute delay** between the last delivery attempt and the write to the dead-letter location (to reduce blob operations), and **if the dead-letter destination is unavailable for four hours, the event is dropped**. TTL expiry is only checked at the *next scheduled attempt*, so an event can outlive its TTL on paper.

**Delayed delivery / probation** is the part that surprises people: if roughly the first 10 events to an endpoint fail, Event Grid assumes the endpoint is sick and delays *all* subsequent retries **and new deliveries** — in some cases for hours. Probation durations are per-error: Busy 10 s, TimedOut 10 s, SocketError 30 s, NotFound / ResolutionError / Disabled / Full / Unauthorized / Forbidden 5 min, InvalidAzureFunctionDestination 10 min.

**If they push back — "So what do you set in production?"** — For a notification (thumbnail, cache invalidation): defaults, no dead-letter, accept the drop. For anything that matters: **dead-lettering on, always**, plus an Event Grid subscription *on the dead-letter blob container* so a `BlobCreated` event on the DLQ container pages someone — DLQ monitoring via the same service, which is a nice thing to say. And if the event drives money, don't terminate Event Grid at your handler at all: terminate it at a **Service Bus queue** and let a durable consumer do the work.

---

### Q34. How does filtering work on an event subscription?
`[MEDIUM]`

**Answer:** Three layers, cheapest first. **Event type filtering** — a simple list of `eventType`/`type` values. **Subject filtering** — `subjectBeginsWith` and `subjectEndsWith`, which is a prefix/suffix match and is why the storage system topic puts the container and blob path in `subject`. **Advanced filtering** — up to a modest number of operator-based conditions on any field in the event including inside `data`, with operators like `NumberGreaterThan`, `StringIn`, `StringContains`, `BoolEquals`, `IsNullOrUndefined`.

```bash
# Only .csv blobs landing in the inbound container, over 1 MB, from the EU tenant.
az eventgrid event-subscription create \
  --name payments-inbound \
  --source-resource-id "$STORAGE_ID" \
  --endpoint-type servicebusqueue \
  --endpoint "$QUEUE_ID" \
  --included-event-types Microsoft.Storage.BlobCreated \
  --subject-begins-with "/blobServices/default/containers/inbound/" \
  --subject-ends-with ".csv" \
  --advanced-filter data.contentLength NumberGreaterThan 1048576 \
  --advanced-filter data.clientRequestId StringBeginsWith "eu-" \
  --deadletter-endpoint "$STORAGE_ID/blobServices/default/containers/eg-deadletter" \
  --max-delivery-attempts 10 \
  --event-ttl 120
```

Two platform notes: filter at the **subscription**, not in the handler — an event you filter out is an event you don't pay for and don't have to scale for. And keep filters simple: this is the same "smart endpoints, dumb pipes" argument Microsoft makes about Service Bus subscription rules. Complex business predicates in a subscription filter become undebuggable routing logic that lives in ARM instead of in code review.

**If they push back — "Where do you draw the line?"** — My rule: a filter may reference *identity and category* (type, tenant, container, size, region) but never *business state* (`data.status == 'PENDING_APPROVAL' && data.amount > limit`). Identity is stable and testable; business state changes every sprint and belongs in a service with unit tests.

---

### Q35. What are the supported Event Grid handlers?
`[EASY]`

**Answer:** Azure Functions, Webhooks (any public HTTPS endpoint), Event Hubs, **Service Bus queues and topics**, Storage Queues, Relay Hybrid Connections, Azure Automation runbooks, and Azure Monitor alerts. The two that matter for this JD are **Service Bus queue** (durability, see Q6) and **webhook**, because a webhook is how you reach anything outside Azure.

Webhooks require **endpoint validation**: on subscription creation Event Grid sends a `SubscriptionValidationEvent` with a `validationCode`, and your endpoint must echo it back (or, for CloudEvents, respond to the HTTP OPTIONS handshake with the `WebHook-Allowed-Origin` header). Azure-native handlers skip this. You can also attach **up to 10 custom HTTP headers** to delivered events, each up to **4,096 bytes** — that's how you satisfy a partner endpoint that demands a static API key header.

```python
# FastAPI handler for both the validation handshake and real events.
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.options("/eventgrid")
async def cloudevents_handshake(request: Request) -> Response:
    # CloudEvents 1.0 abuse-protection handshake.
    origin = request.headers.get("WebHook-Request-Origin", "eventgrid.azure.net")
    return Response(status_code=200, headers={
        "WebHook-Allowed-Origin": origin,
        "WebHook-Allowed-Rate": "120",
    })

@app.post("/eventgrid")
async def receive(request: Request):
    events = await request.json()
    if not isinstance(events, list):
        events = [events]
    for ev in events:
        # EventGridEvent-schema validation handshake.
        if ev.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
            return {"validationResponse": ev["data"]["validationCode"]}
        handle(ev)
    return Response(status_code=202)   # 202 counts as success; return fast, work async
```

**If they push back — "Why 202 and not 200?"** — Both are success. I return 202 deliberately because Event Grid gives me a **30-second** response budget and, with batching on, **all-or-none** semantics for the batch. Acknowledging fast and doing the work asynchronously means one slow item can't fail an entire batch of up to 5,000 events. If the work must be synchronous, I lower `maxEventsPerBatch` so the batch is provably completable inside 30 seconds.

---

### Q36. Event Grid output batching — what are the settings?
`[MEDIUM]`

**Answer:** Off by default — Event Grid sends one event per HTTP request, wrapped in a single-element array. Turn it on per subscription with two settings: **max events per batch (1–5,000)** and **preferred batch size in kilobytes (1–1,024)**. Both are best-effort ceilings, not floors — Event Grid never *delays* an event to fill a batch, so at low rates you'll see batches of one.

Two behaviours to know: **all-or-none** — there is no partial success, so if you 500 on event 900 of 1,000 the whole batch is retried; and a single event larger than the preferred size is still delivered in its own batch rather than dropped.

**If they push back — "What batch size do you pick?"** — Whatever my handler can *provably* finish in under 30 seconds at p99, then halve it. Microsoft's own wording is "subscribers should be careful to only ask for as many events per batch as they can reasonably handle in 30 seconds." I'd start at 100, measure, and treat the number as a tuned parameter in the Helm values file, not a constant in code.

---

### Q37. Event Grid vs Service Bus topics — both do pub/sub. Choose.
`[MEDIUM]` `[the sneaky version of Q5]`

**Answer:** **Push vs pull, and notification vs command.** Event Grid pushes to subscribers who don't have to be listening infrastructure — a webhook, a Function, a Logic App — and it's designed for large fan-out of small, disposable facts. A Service Bus topic requires each subscriber to *pull* from a durable subscription queue, and every subscription gets the full enterprise feature set: DLQ, sessions, delivery counts, transactions, duplicate detection.

Decide on three questions. **Does a subscriber need to be offline for hours and still get everything?** Service Bus — its subscription holds messages until consumed; Event Grid gives up after at most 24 hours and drops if no dead-letter. **Does order matter?** Service Bus sessions; Event Grid has no ordering at all. **How many subscribers, and are they yours?** Event Grid handles 500 subscriptions per topic and reaches things you don't own; Service Bus tops out at 2,000 subscriptions but they're all durable queues you operate.

**If they push back — "Can I use both for the same event?"** — Yes, and it's the standard shape: publish to Event Grid, and have *one* of the subscriptions be a Service Bus queue for the subscriber that needs guarantees while the rest are Functions and webhooks. You get Grid's reach and Bus's durability where it matters, and you only pay for durability where you need it.

---

### Q38. Event Grid Namespaces MQTT — one paragraph, in case they ask.
`[HARD]` `[good-to-have]`

**Answer:** The Namespace resource includes a managed **MQTT 3.1.1 and 5.0 broker** with client authentication by X.509 certificate (self-signed or CA-signed), **client groups** and **topic spaces** for authorisation, and **routing** of MQTT messages into Event Grid topics so device traffic joins the normal event fabric. Relevant limits: **10,000 MQTT sessions per TU**, **1,000 inbound messages/sec per TU** and per session, max message size **512 KB**, session expiry default **8 hours** (configurable), 50 subscriptions per session, and shared subscriptions for competing-consumer semantics over MQTT.

For this JD it matters in one context: **Power and Utilities** is a named EY industry group, and smart-meter / SCADA telemetry is an MQTT problem. Being able to say "Event Grid Namespaces gives you a managed MQTT broker with Entra-integrated routing into the same event fabric, so you don't stand up Mosquitto on VMs" is a credible answer in that vertical.

**If they push back — "IoT Hub does that too."** — It does, and IoT Hub gives you device twins, direct methods, per-device provisioning via DPS and file upload. Event Grid Namespaces MQTT is the leaner choice when you want pub/sub at scale and *not* a device management plane — a large fleet publishing telemetry that fans out to many subscribers. If the client needs device lifecycle management, IoT Hub; if they need a broker, Namespaces.

---

## 6. Azure Event Hubs

### Q39. What is Event Hubs and how is it structured?
`[EASY]` `[opener]`

**Answer:** Event Hubs is a **partitioned, append-only log** for high-volume event ingestion — Microsoft's managed equivalent of Kafka, and it literally speaks the Kafka protocol. A **namespace** contains **event hubs** (= Kafka topics). Each event hub has **partitions** — independent ordered segments. Producers append, optionally with a **partition key** that hashes to a partition. **Consumer groups** are independent views of the whole stream; within a consumer group, each partition is read by one consumer at a time, and each consumer tracks its position by **checkpointing** an offset to a blob container.

The mental model to state: **reading does not consume.** Data is deleted by *retention*, not by acknowledgement — 1 day on Basic, 7 days on Standard, up to **90 days** on Premium and Dedicated. That's what makes replay possible and it's the whole reason to choose Hubs over a queue.

---

### Q40. Throughput Units vs Processing Units vs Capacity Units.
`[MEDIUM]` `[a pure quota question — they're testing whether you've operated it]`

**Answer:** Three tiers, three currencies.

| | Basic | Standard | Premium | Dedicated |
|---|---|---|---|---|
| Currency | TU | **TU** | **PU** | **CU** |
| Max | 40 TU | **40 TU** | **16 PU** | **10 CU** (more by support request) |
| Ingress per unit | 1 MB/s or 1,000 events/s | 1 MB/s or 1,000 events/s | no fixed per-PU limit | no fixed per-CU limit |
| Egress per unit | 2 MB/s or 4,096 events/s | 2 MB/s or 4,096 events/s | — | — |
| Partitions per hub | **32** | **32** | **100** (and 200 per PU namespace-wide) | **1,024** (2,000 per CU) |
| Consumer groups per hub | **1** | **20** | **100** | **1,000** |
| Max event size | 256 KB | **1 MB** | 1 MB | **20 MB** |
| Retention | 1 day | 7 days | **90 days** | **90 days** |
| Storage included | 84 GB per TU | 84 GB per TU | 1 TB per PU | 10 TB per CU |
| Event hubs per namespace | 10 | 10 | 100 per PU | 1,000 |
| Brokered connections | 100 | 5,000 | 10,000 per PU | 100,000 per CU |
| Kafka endpoint | **No** | Yes | Yes | Yes |
| Capture | No | priced separately | included | included |

**Auto-Inflate** scales TUs up automatically on a Standard namespace when you hit the ingress limit — it scales **up only, never down**, so you still need an alert and a manual scale-down, and it works with the Kafka endpoint too.

The number that bites: **egress is 2 MB/s per TU, but that's shared across all consumer groups.** Four consumer groups each reading the full stream at 1 MB/s ingress need 4 MB/s egress = 2 TU minimum, and people size for ingress and get throttled on egress.

**If they push back — "How do you size it?"** — Ingress in MB/s, ceiling-divided by 1; egress = ingress × number of consumer groups, ceiling-divided by 2; take the larger, add 30% headroom, then check the events/sec limits separately because small events hit the 1,000 events/s per TU wall long before the 1 MB/s wall. Then the partition count separately (Q42) — partitions are not the throughput dial, TUs are.

---

### Q41. Offset vs sequence number vs checkpoint. Precisely.
`[MEDIUM]` `[HIGH-VALUE discriminator]`

**Answer:** Three different things people conflate. The **offset** is a byte-position marker within a partition — opaque, monotonically increasing, and the thing you pass to "start reading from here". The **sequence number** is a per-partition logical counter of events — useful for gap detection and arithmetic ("am I 40,000 events behind?"). The **checkpoint** is *your* durable record, written by the client library to a blob container, saying "consumer group G has processed partition P up to offset O". Event Hubs itself does **not** track your position — unlike Service Bus, the broker has no idea what you've consumed.

Consequences worth stating:
- **Checkpointing is at-least-once.** You process, then checkpoint. A crash between the two replays from the last checkpoint. Checkpoint frequency is a direct tradeoff: often = more storage ops and lower replay volume; rarely = cheaper and a bigger replay.
- **Losing the checkpoint store resets you** to the `starting_position` — usually `@latest` (skip everything) or `-1` (from the beginning). Deleting a checkpoint container "to clean up" is a classic outage.
- **Checkpoint blobs are also the partition-ownership store** — the load balancer between competing consumers in a group uses the same container. So the container is shared state and it needs the same care as a database.

**If they push back — "How often should you checkpoint?"** — Not per event, unless events are worth more than the blob write. My default in the template is **every N events or every T seconds, whichever first** (say 100 / 10 s), and always **after** the side effect is durable. If reprocessing is expensive, checkpoint more often; if the consumer is idempotent, checkpoint less often and accept the replay. It is the same knob as Kafka's `auto.commit.interval.ms`, just explicit.

---

### Q42. How do you choose the partition count, and why does over-partitioning hurt?
`[HARD]` `[senior question — the "hurt" half is what separates answers]`

**Answer:** Partition count is your **maximum consumer parallelism within a consumer group**, because one partition is read by one consumer at a time. So the floor is `ceil(required_throughput / per_consumer_throughput)`, and you add headroom because on Basic and Standard **you cannot change the partition count after creation** — you'd have to create a new event hub and migrate. (Premium and Dedicated support dynamic partition scale-out.)

Over-partitioning hurts in five concrete ways:
1. **Ordering granularity gets coarser relative to volume** — more partitions means a given key's neighbours are spread further apart, and any cross-partition ordering assumption breaks harder.
2. **Consumer overhead**: each partition needs a reader, a checkpoint blob, an ownership lease and a rebalance participant. 200 partitions with 3 consumers means each consumer juggles ~67 leases.
3. **Rebalance cost** scales with partitions — every scale event redistributes more leases and pauses more consumption.
4. **Small batches**: fixed ingress spread over more partitions means fewer events per partition per fetch, so per-request overhead dominates and effective throughput *drops*.
5. **Idle partitions cost real money** in checkpoint storage operations and, on Premium, count against the 200-per-PU namespace ceiling.

Under-partitioning hurts one way, but it's fatal: you cannot add consumers, and on Basic/Standard you cannot fix it in place.

**Rule of thumb to say out loud:** "Partitions = expected peak MB/s ÷ what one consumer can handle, rounded up, then doubled for headroom, capped by tier. For most enterprise integration workloads that's **4 to 32**, not 200. 200 is a Netflix number, and if I'm proposing it I should be able to show the throughput math that demands it."

**If they push back — "What if you get it wrong on Standard?"** — Then you stand up a new event hub with the right count, dual-write from producers (or run a bridge consumer), let consumers drain the old hub to its retention horizon, and cut over. That's a real migration with a real change window — which is exactly why the number goes in a design review, not a ticket.

---

### Q43. What is Event Hubs Capture and when do you use it?
`[MEDIUM]` `[directly relevant to the batch/stream bridge in §9]`

**Answer:** Capture automatically writes the stream to Blob Storage or ADLS Gen2 in **Apache Avro**, with no code and no consumer. You configure a **time window (default 5 minutes, min 1, max 15)** and a **size window (default 300 MB, min 10 MB, max 500 MB)**, and it's **first-wins** — whichever triggers first closes the file. Each partition captures independently.

Path format, which they sometimes ask for:
```text
{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}
https://acct.blob.core.windows.net/container/ns/hub/0/2026/08/25/09/15/00.avro
```

Three facts that make it interview-worthy: Capture **bypasses the TU/PU egress quota** because it copies from internal storage, so it doesn't steal bandwidth from your real consumers. It **emits empty files when no events occur**, giving downstream batch jobs a predictable cadence marker — which is genuinely useful as a "the window closed" signal. And if the storage account is temporarily unavailable, Capture **backfills** from the event hub's own retention once it recovers. Not available on Basic; included in Premium/Dedicated, priced separately on Standard; enabling it on an existing hub captures only events arriving *after* you turn it on.

**If they push back — "Why not just have a consumer write to blob?"** — Because you'd be operating a consumer group, checkpoints, scaling, failure handling and a file-rolling strategy to produce something Microsoft gives you as a checkbox that doesn't consume your egress budget. The only reason to hand-roll it is a format Capture doesn't emit — and the portal's no-code editor can now land **Parquet** in ADLS via Stream Analytics if that's the need.

**This is the direct answer to the JD's "batch jobs using event streaming":** Capture is the officially sanctioned lambda-architecture seam — the same stream feeds a real-time consumer *and* a nightly batch job over the captured Avro, with no second ingestion path and no reconciliation between them.

---

### Q44. The Kafka protocol endpoint — what is it and what does it NOT support?
`[HARD]` `["we speak Kafka to Event Hubs" is a real migration answer — know the caveats]`

**Answer:** Event Hubs exposes a **Kafka endpoint on port 9093** so existing Kafka clients connect with a configuration change and no code change. Supported on **Standard, Premium and Dedicated only — not Basic**. It accepts **Apache Kafka 1.0 and later** clients. Authentication is `SASL_SSL` with either `PLAIN` (username literally `$ConnectionString`, password = the connection string) or **`OAUTHBEARER`** for Microsoft Entra with Azure RBAC, which is what you'd actually use.

The conceptual mapping: Kafka cluster → namespace, topic → event hub, partition → partition, consumer group → consumer group, offset → offset.

What is **not** vanilla:
- **Compression**: only `gzip`, and only on **Premium and Dedicated**. Standard is `none`.
- **Kafka transactions**: public preview, **Premium and Dedicated only**.
- **Kafka Streams**: public preview, **Premium and Dedicated only** — and **ksqlDB will never work**, because Confluent's licence forbids competing managed services from offering it.
- **Generated SAS tokens** aren't supported on the Kafka endpoint (connection-string SAS is).
- No broker-side ACL model — authorisation is Azure RBAC, not Kafka ACLs.
- Kafka consumer groups per namespace: **1,000**. Consumer group name limit 256 chars for Kafka vs 50 for AMQP.

Also worth volunteering: the three protocols are **concurrent** — you can produce with a Kafka client and consume with the AMQP SDK or an Azure Functions Event Hub trigger, and Capture and Geo-DR work with Kafka traffic. That protocol bridging is genuinely the killer feature.

**If they push back — "So should a client migrate from self-managed Kafka to Event Hubs?"** — It depends on exactly one thing: what they use beyond produce/consume. If it's a plain pipeline, yes — they delete a ZooKeeper-less-but-still-real cluster, a Cruise Control, an upgrade treadmill and a 3am pager, and the change is a config file. If they run Kafka Connect at scale, ksqlDB, Kafka Streams topologies, or depend on broker ACLs and log compaction semantics, the migration is a project, not a config change, and I'd scope it as one. That honest answer scores better than "yes, Azure is better."

---

### Q45. How does the Event Processor balance partitions across consumers?
`[MEDIUM]`

**Answer:** Through the **checkpoint store**, which doubles as an ownership store. Each `EventHubConsumerClient`/`EventProcessor` instance claims partition **leases** as blobs with an ETag; it renews its leases on a timer, and periodically compares how many it owns against the fair share (`partitions / active_owners`). If it owns fewer than its share, it steals an expired or over-allocated lease with an ETag-conditional write — optimistic concurrency, so exactly one instance wins. When an instance dies, its leases stop being renewed, expire, and get claimed by survivors.

Consequences: **scale-out is eventually consistent**, not instant — expect tens of seconds of churn after a scale event. Two consumer *groups* never contend, because ownership is per group. And there's a hard ceiling: **5 non-epoch receivers per consumer group per partition**; the processor uses epoch (exclusive) receivers precisely so ownership is unambiguous.

**If they push back — "What if two pods think they own the same partition?"** — With epoch receivers the broker enforces it: the higher epoch wins and the older receiver is disconnected. That's the guarantee that makes checkpointing safe. If you're using plain non-epoch receivers you get up to 5 readers on the same partition and no exclusivity — which is fine for a debugging tail, and wrong for a processing pipeline.

---

### Q46. Show me an Event Hubs consumer in Python.
`[MEDIUM]` `[CODE]`

```python
"""platform_messaging/eventhub_consumer.py"""
from __future__ import annotations

import logging
import signal
import threading

from azure.eventhub import EventData, PartitionContext
from azure.eventhub import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
from azure.identity import DefaultAzureCredential

log = logging.getLogger(__name__)
_stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *_: _stop.set())

CHECKPOINT_EVERY = 100          # events
_counts: dict[str, int] = {}


def on_event(ctx: PartitionContext, event: EventData | None) -> None:
    if event is None:
        return                                   # max_wait_time elapsed with no data
    handle(event.body_as_json())

    n = _counts.get(ctx.partition_id, 0) + 1
    _counts[ctx.partition_id] = n
    if n % CHECKPOINT_EVERY == 0:
        # ALWAYS after the side effect is durable. Checkpoint == "I have processed
        # up to here"; checkpointing first turns a crash into silent data loss.
        ctx.update_checkpoint(event)


def on_partition_initialize(ctx: PartitionContext) -> None:
    log.info("acquired partition %s", ctx.partition_id)


def on_partition_close(ctx: PartitionContext, reason) -> None:
    log.info("released partition %s reason=%s", ctx.partition_id, reason)


def on_error(ctx: PartitionContext | None, error: Exception) -> None:
    pid = ctx.partition_id if ctx else "n/a"
    log.exception("partition=%s error=%s", pid, error)


def main() -> None:
    cred = DefaultAzureCredential()
    checkpoint_store = BlobCheckpointStore(
        blob_account_url="https://contosointegration.blob.core.windows.net",
        container_name="eh-checkpoints",       # ALSO the partition-ownership store
        credential=cred,
    )
    client = EventHubConsumerClient(
        fully_qualified_namespace="contoso-telemetry.servicebus.windows.net",
        eventhub_name="market-data",
        consumer_group="risk-engine",
        checkpoint_store=checkpoint_store,
        credential=cred,
    )
    with client:
        t = threading.Thread(
            target=client.receive,
            kwargs=dict(
                on_event=on_event,
                on_partition_initialize=on_partition_initialize,
                on_partition_close=on_partition_close,
                on_error=on_error,
                max_wait_time=30,
                starting_position="-1",        # "-1" = from the beginning; "@latest" = tail
            ),
            daemon=True,
        )
        t.start()
        _stop.wait()                            # block until SIGTERM
        log.info("SIGTERM — closing client, leases will be released")


def handle(payload: dict) -> None:
    ...


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

**If they push back — "Why not checkpoint every event?"** — Because each checkpoint is a blob write against a shared container, and at 5,000 events/sec across 16 partitions that's a storage bottleneck and a real bill. Checkpointing every 100 events means a crash replays at most 100 events per partition — which is free if the consumer is idempotent, and idempotency is mandatory in the template anyway. The number is a Helm value, not a constant.

---

### Q47. How do you monitor an Event Hubs consumer?
`[MEDIUM]` `[ties to §11]`

**Answer:** The one metric that matters is **lag** — the gap between the latest sequence number in a partition and the sequence number of your last checkpoint, per partition per consumer group. Event Hubs doesn't expose lag as a first-class metric the way Kafka does, so you compute it: `partition.last_enqueued_sequence_number - checkpointed_sequence_number`. Alongside it: `IncomingMessages` / `OutgoingMessages`, `ThrottledRequests` (your TU ceiling, the most common surprise), `CapturedMessages`/`CaptureBacklog`, and `QuotaExceededErrors`.

Alert on **lag growth rate**, not absolute lag. Absolute lag spikes harmlessly during a scale event or a deploy. Lag that has been monotonically increasing for 15 minutes means consumption is permanently slower than production, and that never self-heals.

**If they push back — "What's the 3am page?"** — Sustained lag growth, and `ThrottledRequests` above zero. Everything else is a ticket. Full table in §11.

---

### Q48. Event Hubs vs Kafka — when would you insist on real Kafka?
`[MEDIUM]`

**Answer:** Four situations. **Multi-cloud or on-prem** — the client's estate isn't Azure and they need one streaming platform everywhere; Confluent Cloud or self-managed spans it, Event Hubs doesn't. **Deep ecosystem dependency** — Kafka Connect with dozens of connectors, Kafka Streams topologies, ksqlDB (which Event Hubs can never offer, by licence). **Log compaction as a primary design element** — Event Hubs supports compaction but with tier-bound sizes (1 GB/partition Standard, 250 GB/partition Premium and Dedicated), and if the compacted topic *is* the system of record that ceiling is a design constraint. **Broker-level ACLs and quotas** as a compliance requirement, where the client's security model is expressed in Kafka ACLs and porting it to Azure RBAC is a real project.

Otherwise, on an Azure engagement, Event Hubs wins on operational cost: no brokers, no controller quorum, no rebalancing storms during upgrades, Entra ID auth, Private Link, and Capture for free.

**If they push back — "EY is a Microsoft shop, so always Event Hubs?"** — No, and I'd say so. In financial services, the client often already runs Confluent Platform for market data and the streaming platform is a strategic asset with a team around it. Telling them to migrate is the wrong first move; the right move is to *integrate* — Event Hubs' Kafka endpoint and MirrorMaker 2 both let Azure workloads consume the existing estate without a migration. Meeting a client where they are is a consulting skill, not a technical one, and it's a good thing to demonstrate in an EY interview.

---

## 7. Apache Kafka

### Q49. Describe Kafka's architecture.
`[EASY]` `[opener — but the version answer in Q50 is where marks are]`

**Answer:** A Kafka **cluster** is a set of **brokers**. Data lives in **topics**, each split into **partitions**, and each partition is an append-only log file on disk, replicated to `replication.factor` brokers. One replica per partition is the **leader** — all reads and writes go to it — and the others are **followers** that fetch from the leader. The set of replicas caught up with the leader is the **ISR (in-sync replicas)**. **Producers** append with an optional key that determines the partition. **Consumers** join a **consumer group**; the group's members divide the partitions between them, each partition to exactly one member, and each member tracks its position by committing an **offset** to the internal `__consumer_offsets` topic.

The one-line essence: **Kafka is a replicated, partitioned, distributed commit log — and everything else is bookkeeping on top of that.**

---

### Q50. KRaft vs ZooKeeper — what's the current state?
`[MEDIUM]` `[CURRENCY CHECK — get the version right and you look current; get it wrong and you look 2019]`

**Answer:** **ZooKeeper mode was removed in Apache Kafka 4.0** (released March 2025). 4.0 is the first major release that runs entirely without ZooKeeper — KRaft mode is the only mode, and 4.0 supports **no ZK mode and no migration from ZK mode**. If a client is still on ZooKeeper, the upgrade path is: get to **3.9** first, run the ZooKeeper-to-KRaft migration there, *then* upgrade to 4.0+. Broker upgrades to 4.0 and later require KRaft with software and metadata versions of at least **3.3.x**, which is when KRaft was declared production-ready. The `--zookeeper` flag was removed from the admin CLI tools; everything is `--bootstrap-server` now.

**KRaft** replaces ZooKeeper with an internal Raft quorum: dedicated **controller** nodes hold cluster metadata in an internal `__cluster_metadata` topic and elect a leader among themselves, while **brokers** handle data. Metadata propagation becomes a log the brokers *tail* rather than a set of ZK watches, which is why KRaft scales to far more partitions and recovers from controller failover in a fraction of the time.

Say this too: it also removes an entire distributed system from the operational surface — no separate ZK ensemble to secure, patch, monitor and back up. That's a platform-engineer answer, not a trivia answer.

**If they push back — "What's the actual benefit, apart from fewer moving parts?"** — Controller failover and broker restart times drop from minutes to seconds at high partition counts, because a new controller reads a log it already has rather than loading full state from ZooKeeper. Partition-count ceilings go up by roughly an order of magnitude. And metadata operations become linearisable through one Raft log instead of two systems that could disagree.

---

### Q51. Replication factor, ISR, leader election, `min.insync.replicas` — do the durability math.
`[HARD]` `[THE Kafka question. Have the arithmetic ready.]`

**Answer:** `replication.factor` is how many copies of each partition exist. The **ISR** is the subset of those replicas currently caught up with the leader. `min.insync.replicas` is a **broker/topic** setting that says how many replicas must be in the ISR for a write with `acks=all` to be accepted. `acks` is a **producer** setting. The guarantee comes from the *combination*, and neither side alone is enough.

**The math, and this is the answer to state:**

> With `replication.factor=3`, `min.insync.replicas=2` and `acks=all`, a write is acknowledged only once the leader plus at least one follower have it. That tolerates **one broker failure with zero data loss**. If a second broker goes down, the ISR drops to 1, which is below `min.insync.replicas`, so the producer starts getting `NOT_ENOUGH_REPLICAS` and **writes fail rather than silently becoming unreplicated**. Failing loudly is the point — you have chosen consistency over availability for that partition, deliberately.

| `acks` | Producer waits for | Loses data when |
|---|---|---|
| `0` | nothing — fire and forget | Anything at all. Never use for business data |
| `1` | leader's local write only | The leader dies before a follower fetches |
| `all` (`-1`) | all **in-sync** replicas | Only if every ISR member dies. With `min.insync=2`, that's 2 simultaneous failures |

**The classic trap: `acks=all` with `min.insync.replicas=1` is `acks=1` in disguise.** If the ISR has shrunk to just the leader, "all in-sync replicas" is one replica, the write is acked, and a leader failure loses it. Candidates say "we use acks=all so we're safe" and this is the follow-up that catches them.

Defaults, verified against Kafka 4.0 docs: producer **`acks=all`** and **`enable.idempotence=true`** are now the defaults (they were `1` and `false` in older versions — a real change worth knowing). Topic **`min.insync.replicas` defaults to 1**, so *you must set it to 2 explicitly*; the safe default is not safe out of the box.

Also: `unclean.leader.election.enable`. If it's `true`, an out-of-sync replica may be elected leader when no in-sync replica survives — availability at the cost of silent data loss. In financial services this is `false`, always, and you accept the partition going offline instead.

```bash
# The durable topic. RF=3, min ISR=2, no unclean elections.
kafka-topics.sh --bootstrap-server broker:9092 \
  --create --topic payments.instructions.v1 \
  --partitions 12 --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config unclean.leader.election.enable=false \
  --config retention.ms=604800000 \
  --config compression.type=zstd
```

**If they push back — "What does RF=3 / min.insync=2 cost you?"** — Latency (the ack waits for a second replica's fetch), 3× storage, and availability: two broker failures in one rack take that partition's writes offline. That's a deliberate trade and I'd document it in the design record. For telemetry where a lost sample is irrelevant, RF=2/`acks=1` is a legitimate, cheaper choice — the mistake is applying one policy to every topic.

---

### Q52. Idempotent producer and Kafka transactions — what do they actually guarantee?
`[HARD]`

**Answer:** The **idempotent producer** (`enable.idempotence=true`, now the default) gives each producer a **producer ID** and stamps each message with a monotonic **sequence number per partition**. The broker deduplicates on that, so a producer retry after an ambiguous ack does not create a duplicate. It also preserves per-partition ordering across retries, which naive `retries>0` breaks. Scope: **one producer session, per partition.** A producer restart gets a new PID, so it does not protect against duplicates across restarts.

**Transactions** extend that across partitions and across the consume-process-produce cycle. The producer gets a stable `transactional.id`, calls `begin_transaction()`, produces to N partitions, calls `send_offsets_to_transaction()` to include the *input* offsets in the same transaction, then `commit_transaction()`. Consumers with `isolation.level=read_committed` never see records from an aborted transaction. That's Kafka's **exactly-once semantics (EOS)**.

**The boundary that matters, and this is the senior part:** EOS is exactly-once **within Kafka only**. The moment your processor writes to Postgres, calls a partner REST API, or sends an email, that action is outside the transaction and the guarantee is gone. For those, you're back to at-least-once plus an idempotent sink.

```python
# confluent-kafka transactional consume-process-produce
from confluent_kafka import Consumer, Producer, KafkaException

producer = Producer({
    "bootstrap.servers": "broker:9092",
    "transactional.id": "enrichment-v1-worker-0",   # stable per worker, survives restart
    "enable.idempotence": True,
})
producer.init_transactions()

consumer = Consumer({
    "bootstrap.servers": "broker:9092",
    "group.id": "enrichment-v1",
    "enable.auto.commit": False,          # the TRANSACTION commits offsets, not autocommit
    "isolation.level": "read_committed",
})
consumer.subscribe(["trades.raw.v1"])

while True:
    msgs = consumer.consume(num_messages=500, timeout=1.0)
    if not msgs:
        continue
    producer.begin_transaction()
    try:
        for m in msgs:
            if m.error():
                raise KafkaException(m.error())
            producer.produce("trades.enriched.v1", key=m.key(), value=enrich(m.value()))
        # Input offsets become part of the same atomic unit as the output records.
        producer.send_offsets_to_transaction(
            consumer.position(consumer.assignment()),
            consumer.consumer_group_metadata(),
        )
        producer.commit_transaction()
    except Exception:
        producer.abort_transaction()
        raise
```

**If they push back — "What does EOS cost?"** — Throughput, because of the transaction coordinator round trips and the commit markers written into every partition; latency, because `read_committed` consumers can't read past the last stable offset until the transaction resolves; and operational complexity, because a hung transaction blocks consumption until `transaction.timeout.ms` expires. I'd only pay it for a pure Kafka-to-Kafka stream processor. For consume-and-write-to-a-database, at-least-once plus an idempotency key is simpler, cheaper and just as correct.

---

### Q53. Consumer groups and rebalancing — eager vs cooperative.
`[HARD]` `[HIGH-VALUE]`

**Answer:** A consumer group's members share the partitions of the subscribed topics, one partition to one member. When membership changes — a consumer joins, leaves, dies, or the topic's partition count changes — the group **rebalances**.

**Eager rebalancing** (`RangeAssignor`, `RoundRobinAssignor`) is stop-the-world: *every* consumer revokes *all* its partitions, the group leader recomputes the assignment, everyone gets partitions back. During that window nobody consumes anything. On a large group with a slow `poll()` loop, that's seconds of total outage on every deploy.

**Cooperative incremental rebalancing** (`CooperativeStickyAssignor`) revokes only the partitions that actually need to move, in two rounds, and consumers keep processing everything else throughout. On a rolling deploy of 20 pods, that's the difference between 20 full stop-the-world pauses and a handful of individual partition handoffs.

**Verified Kafka 4.0 defaults:** `partition.assignment.strategy` is `[RangeAssignor, CooperativeStickyAssignor]` — Range is *first*, so a fresh group negotiates eager Range unless you change it. `session.timeout.ms=45000`, `heartbeat.interval.ms=3000`, `max.poll.interval.ms=300000` (5 min), `max.poll.records=500`.

**The failure that actually happens in production:** heartbeats run on a background thread, so a consumer stuck processing looks alive to the group — until `max.poll.interval.ms` (5 min) elapses without a `poll()` call, at which point the broker evicts it, rebalances, and the evicted consumer's commit fails. Symptom: "my consumer keeps getting kicked out of the group and reprocessing the same batch." Fix: reduce `max.poll.records`, or raise `max.poll.interval.ms`, or move slow work off the poll thread. Distinguish it from `session.timeout.ms` eviction, which means the *process or network* died, not that processing was slow — different diagnosis entirely.

**If they push back — "So should everyone switch to cooperative?"** — For consumer groups that scale or deploy frequently, yes, and it needs a **two-step rolling upgrade** (first roll with both strategies listed, then roll again with only cooperative) — you cannot flip it in one deploy without a group-wide failure. Kafka 4.0 also ships the **KIP-848** next-generation consumer rebalance protocol, which moves assignment to the broker-side group coordinator and removes the group-leader stop-the-world entirely; on a greenfield 4.x cluster that's the direction of travel.

---

### Q54. Offset commit strategies.
`[MEDIUM]`

**Answer:** Three, and the choice is your delivery guarantee.

**Auto-commit** (`enable.auto.commit=true`, the default, every `auto.commit.interval.ms=5000`) commits offsets on a timer from inside `poll()`. It commits records you have *fetched*, not necessarily *processed* — so a crash mid-batch loses everything between the last commit and the crash. **At-most-once-ish, and non-deterministic.** Fine for metrics, wrong for anything else.

**Sync commit after processing** (`commit(asynchronous=False)`) is at-least-once and the default in my template. It costs a round trip per commit, so commit per batch, not per record.

**Async commit** (`commit(asynchronous=True)`) is at-least-once with better throughput and no ordering guarantee on the commits themselves. The standard idiom is async in the loop plus one **sync commit in the `finally`** on shutdown, so the last position is durable.

The rule to say: **commit after the side effect is durable, never before.** That's the same rule as Event Hubs checkpointing and Service Bus `complete_message` — one rule, three products.

**If they push back — "What about storing offsets in your own database?"** — Legitimate and sometimes right: commit the offset in the *same database transaction* as the business write, and on partition assignment seek to the stored offset instead of the committed one. That gives you genuine exactly-once for a Kafka→RDBMS sink without Kafka transactions, because the offset and the effect commit atomically in one system. The cost is that you own the offset store and the seek logic in your `on_assign` callback.

---

### Q55. Retention: time, size, and compaction.
`[MEDIUM]`

**Answer:** Two cleanup policies. `cleanup.policy=delete` (the default) discards whole log **segments** once they exceed `retention.ms` (**default 604800000 = 7 days**) or `retention.bytes` (**default -1 = unlimited**), whichever hits first. Segments roll on `segment.ms` (default 7 days) or `segment.bytes`, and **retention only ever deletes closed segments** — which is why a topic with a 1-hour retention and a 7-day `segment.ms` appears to delete nothing.

`cleanup.policy=compact` is different in kind: instead of deleting by age, it keeps **the most recent value for each key, forever**. The compacted log becomes a durable, replayable snapshot of current state. A background cleaner rewrites segments once the ratio of duplicate keys passes `min.cleanable.dirty.ratio` (default 0.5). A record with a key and a **null value is a tombstone** — it deletes the key, and is itself retained for `delete.retention.ms` (default 1 day) so consumers get a chance to see the deletion before it vanishes. You can set `cleanup.policy=compact,delete` for both.

The compaction use case to name: **a changelog / current-state topic**. `customers.v1` keyed by customer ID, compacted — any new service can bootstrap the full current customer set by reading from offset 0, then stay current from the same topic. That's event sourcing's read model and it's how Kafka Connect, Kafka Streams state stores and `__consumer_offsets` themselves work.

**If they push back — "Why not just query the source database?"** — Because a compacted topic decouples you from the source's availability, load and schema, gives every consumer the same view, and replays deterministically for a new service or a rebuild. It's the difference between N services hammering one Oracle instance and N services tailing a log. The tradeoff is eventual consistency and the operational cost of a CDC pipeline (Debezium via Kafka Connect, Q57).

---

### Q56. Schema Registry and compatibility modes — say exactly what each permits.
`[HARD]` `[HIGH-VALUE — schema evolution is in the JD's spirit and this is where people wave their hands]`

**Answer:** A Schema Registry stores versioned Avro/Protobuf/JSON-Schema definitions per subject (usually `<topic>-value`). Producers serialise with a 5-byte prefix — a magic byte plus a 4-byte schema ID — so the payload carries an ID, not the schema. Consumers fetch the writer's schema by ID and deserialise against their own reader schema. That's how you get self-describing data without paying the schema's size on every message.

The compatibility mode decides which schema changes are legal and, crucially, **who upgrades first**:

| Mode | Allowed changes | Checked against | Upgrade first |
|---|---|---|---|
| **BACKWARD** (default) | Delete a field; add an **optional** field (with a default) | The **latest** version only | **Consumers** |
| **BACKWARD_TRANSITIVE** | Same | **All** previous versions | **Consumers** |
| **FORWARD** | Add a field; delete an **optional** field | The **latest** version only | **Producers** |
| **FORWARD_TRANSITIVE** | Same | **All** previous versions | **Producers** |
| **FULL** | Add or delete **optional** fields only | The **latest** version only | Either order |
| **FULL_TRANSITIVE** | Same | **All** previous versions | Either order |
| **NONE** | Anything | Nothing | Good luck |

The sentence that shows you understand it rather than memorised it: **"BACKWARD means a consumer on the new schema can read data written with the old one — so I roll consumers first. FORWARD means a consumer on the old schema can read data written with the new one — so I roll producers first."** Everything else follows.

**BACKWARD is the default and is right for most event streams**, because in a stream you typically can't control when every consumer upgrades, and consumers reading with the new schema must cope with the historical data still sitting in the topic. FORWARD suits a fan-out where many independent consumers can't be coordinated but you control the producer.

```json
{
  "type": "record",
  "namespace": "com.contoso.trading",
  "name": "TradeConfirmed",
  "fields": [
    {"name": "tradeId",   "type": "string"},
    {"name": "notional",  "type": {"type": "bytes", "logicalType": "decimal",
                                   "precision": 18, "scale": 4}},
    {"name": "ccy",       "type": "string"},
    {"name": "bookedAt",  "type": {"type": "long", "logicalType": "timestamp-micros"}},
    {"name": "deskId",    "type": ["null", "string"], "default": null}
  ]
}
```

`deskId` is the BACKWARD-compatible addition: a union with `null` **and an explicit `default`**. Drop the default and the registry rejects the schema — a nullable field without a default is a breaking change, because a consumer reading old data has nothing to fill it with. That single missing line is the most common schema-evolution mistake.

**If they push back — "What if you genuinely need a breaking change?"** — You don't break the subject; you **version the topic**: `trades.confirmed.v1` and `trades.confirmed.v2`, dual-publish for a migration window, migrate consumers one at a time, then retire v1. That's the same discipline as URI versioning for a REST API ([API Design](01-api-design-rest-soap-graphql-openapi.md)) — the contract is immutable once published, and a new contract gets a new name. Flipping the registry to NONE to "unblock the release" is how you end up with an undebuggable topic.

---

### Q57. Kafka Connect — what is it and why does it matter for this JD?
`[MEDIUM]` `[DIRECTLY maps to JD responsibility 2: "connectors and adapters for SaaS, ERP, CRM and legacy systems"]`

**Answer:** Kafka Connect is a framework and a runtime for moving data between Kafka and external systems **declaratively** — you POST JSON config to a REST API instead of writing and operating a producer/consumer application. **Source connectors** pull into Kafka; **sink connectors** push out. It runs in **distributed mode** as a cluster of workers that share connector **tasks**, rebalance on failure, and persist their configuration, offsets and status in internal Kafka topics — so the workers themselves are stateless and disposable, which is exactly what you want on Kubernetes.

Why it matters here: this JD's responsibility 2 is *"develop and maintain microservices, connectors, and adapters for SaaS, ERP, CRM, and legacy systems."* Kafka Connect is the answer that scales — a JDBC source against a legacy Oracle, **Debezium** for CDC off SQL Server/Postgres/MySQL/Oracle without touching the application, a Salesforce or SAP source, sinks to blob, Snowflake, Elasticsearch, JDBC. **Single Message Transforms (SMTs)** do per-record mapping (mask a field, route by content, rename, flatten) inline, without a stream processor.

`POST /connectors` on a Connect worker, body:

```json
{
  "name": "core-banking-cdc",
  "config": {
    "connector.class": "io.debezium.connector.sqlserver.SqlServerConnector",
    "tasks.max": "1",
    "database.hostname": "core-sql.internal",
    "database.names": "CoreBanking",
    "topic.prefix": "corebanking",
    "table.include.list": "dbo.accounts,dbo.postings",
    "schema.history.internal.kafka.bootstrap.servers": "broker:9092",
    "schema.history.internal.kafka.topic": "schema-history.corebanking",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081",

    "transforms": "mask,route",
    "transforms.mask.type": "org.apache.kafka.connect.transforms.MaskField$Value",
    "transforms.mask.fields": "customer_pan,customer_dob",
    "transforms.mask.replacement": "****",
    "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.route.regex": "corebanking\\.dbo\\.(.*)",
    "transforms.route.replacement": "banking.$1.v1"
  }
}
```

The platform framing: Connect turns "write another integration service" into "add a JSON file to a Git repo", which is the paved road again. And PII masking as an SMT means the sensitive field never lands in a topic at all — a control you can show an auditor.

**If they push back — "When would you write a consumer instead of using Connect?"** — When the work is genuinely business logic rather than movement plus light transformation, when you need to call an API mid-flight and handle its failures, when you need multi-record state, or when no connector exists and writing one (a Java `SourceTask`) costs more than a small Python consumer. My rule: **movement and mapping → Connect; decisions → code.**

---

### Q58. Kafka Streams vs ksqlDB — 30 seconds.
`[EASY-MEDIUM]`

**Answer:** **Kafka Streams** is a Java client library — no cluster, it runs inside your app — for stateful stream processing: joins, windowed aggregations, and local state stores backed by compacted changelog topics for fault tolerance. **ksqlDB** is a server that lets you express the same things in SQL. Neither is Python, which is the honest caveat: from Python you'd use **Faust**/**Quix Streams**, or push the processing into **Azure Stream Analytics**, **Spark Structured Streaming** or **Flink**.

And know the licensing landmine (Q44): **ksqlDB's licence forbids competing managed services from offering it**, so it will never appear on Event Hubs. If a client's design depends on ksqlDB, they are committing to self-managed Kafka or Confluent Cloud.

**If they push back — "You're a Python developer, is that a problem?"** — Not for this JD, which lists Python first. For heavy stateful stream processing I'd use the right tool rather than force Python: Azure Stream Analytics for windowed SQL over Event Hubs, or Flink where the client already runs it. Python's place is the consumer, the connector glue and the API layer — which is where the integration work actually is.

---

### Q59. Show me a production Kafka producer and consumer in Python.
`[MEDIUM]` `[CODE]`

```python
"""platform_messaging/kafka_io.py — confluent-kafka producer + consumer."""
from __future__ import annotations

import json
import logging
import signal
import sys
from typing import Any

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer, TopicPartition

log = logging.getLogger(__name__)

COMMON = {
    "bootstrap.servers": "broker-1:9093,broker-2:9093,broker-3:9093",
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "OAUTHBEARER",       # Entra ID against Event Hubs' Kafka endpoint
    # For self-managed Kafka with SCRAM instead:
    # "sasl.mechanism": "SCRAM-SHA-512", "sasl.username": ..., "sasl.password": ...,
}


# ---------------------------------------------------------------- producer

def build_producer() -> Producer:
    return Producer({
        **COMMON,
        "enable.idempotence": True,    # default in 4.0; state it so intent is explicit
        "acks": "all",                 # default in 4.0; pairs with min.insync.replicas=2
        "compression.type": "zstd",    # NOTE: Event Hubs' Kafka endpoint supports gzip only
        "linger.ms": 20,               # batch window; default is 5
        "batch.size": 65536,
        "max.in.flight.requests.per.connection": 5,   # safe up to 5 WITH idempotence
        "delivery.timeout.ms": 120000,
    })


def _on_delivery(err, msg) -> None:
    if err is not None:
        # This is the ONLY place a produce failure surfaces. Never leave it empty.
        log.error("delivery failed topic=%s key=%s err=%s", msg.topic(), msg.key(), err)
        return
    log.debug("delivered %s[%d]@%d", msg.topic(), msg.partition(), msg.offset())


def publish(p: Producer, topic: str, key: str, value: dict[str, Any],
            traceparent: str | None = None) -> None:
    headers = [("content-type", b"application/json")]
    if traceparent:
        headers.append(("traceparent", traceparent.encode()))   # survives the broker hop
    p.produce(
        topic=topic,
        key=key.encode(),          # key -> partition -> ordering scope. Choose it deliberately.
        value=json.dumps(value, separators=(",", ":")).encode(),
        headers=headers,
        on_delivery=_on_delivery,
    )
    p.poll(0)                      # serve delivery callbacks without blocking


# ---------------------------------------------------------------- consumer

_running = True


def _stop(*_: Any) -> None:
    global _running
    _running = False


signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT, _stop)


def build_consumer(group_id: str) -> Consumer:
    return Consumer({
        **COMMON,
        "group.id": group_id,
        "enable.auto.commit": False,                        # we commit after processing
        "auto.offset.reset": "earliest",                    # default is "latest"
        "isolation.level": "read_committed",                # ignore aborted transactions
        "partition.assignment.strategy": "cooperative-sticky",
        "max.poll.interval.ms": 300000,
        "session.timeout.ms": 45000,
        "max.partition.fetch.bytes": 1048576,
    })


def on_assign(consumer: Consumer, partitions: list[TopicPartition]) -> None:
    # With the cooperative protocol you MUST use incremental_assign, not assign.
    log.info("assigned %s", [(p.topic, p.partition) for p in partitions])
    consumer.incremental_assign(partitions)


def on_revoke(consumer: Consumer, partitions: list[TopicPartition]) -> None:
    log.info("revoking %s", [(p.topic, p.partition) for p in partitions])
    try:
        consumer.commit(asynchronous=False)   # flush position before letting go
    except KafkaException as exc:
        log.warning("commit on revoke failed: %s", exc)
    consumer.incremental_unassign(partitions)


def run(topic: str, group_id: str) -> int:
    consumer = build_consumer(group_id)
    consumer.subscribe([topic], on_assign=on_assign, on_revoke=on_revoke)
    dlq = build_producer()

    try:
        while _running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            try:
                handle(json.loads(msg.value()))
            except (ValueError, KeyError) as exc:
                # Poison record: deterministic failure. Kafka has no DLQ, so we build one.
                dlq.produce(
                    f"{topic}.dlq",
                    key=msg.key(),
                    value=msg.value(),
                    headers=[
                        ("dlq.reason", type(exc).__name__.encode()),
                        ("dlq.source.topic", topic.encode()),
                        ("dlq.source.partition", str(msg.partition()).encode()),
                        ("dlq.source.offset", str(msg.offset()).encode()),
                    ],
                    on_delivery=_on_delivery,
                )
                dlq.flush(10)          # the DLQ write MUST be durable before we commit past it

            # Commit AFTER the side effect. Sync, per message here for clarity;
            # in production commit per batch to cut round trips.
            consumer.commit(message=msg, asynchronous=False)
    finally:
        log.info("shutting down: final commit + close (releases partitions immediately)")
        try:
            consumer.commit(asynchronous=False)
        except KafkaException:
            pass
        consumer.close()
        dlq.flush(30)
    return 0


def handle(payload: dict) -> None:
    ...


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(run("trades.confirmed.v1", "risk-engine-v1"))
```

**The four things to point at:** `enable.auto.commit=False` plus commit-after-processing is the at-least-once contract; the DLQ is hand-built because **Kafka has none**; `dlq.flush()` before the commit means you never commit past a record whose DLQ copy didn't land; and `consumer.close()` in the `finally` triggers an immediate, graceful group leave rather than a `session.timeout.ms` eviction 45 seconds later.

---

### Q60. How do you monitor consumer lag?
`[MEDIUM]` `[EY-plausible ops question]`

**Answer:** Lag is `log_end_offset - committed_offset`, per partition per consumer group. Sources, in order of preference: **`kafka-consumer-groups.sh --describe`** for a human at a terminal; the **AdminClient API** (`list_consumer_group_offsets` + `list_offsets`) for programmatic checks; **JMX** `records-lag-max` from the consumer itself; and **Burrow** or the **Kafka Lag Exporter** for Prometheus. On AKS, KEDA's `kafka` scaler reads lag directly and turns it into replicas, so the same signal drives both the alert and the autoscaler.

```bash
kafka-consumer-groups.sh --bootstrap-server broker:9092 \
  --describe --group risk-engine-v1
# GROUP          TOPIC                 PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID
# risk-engine-v1 trades.confirmed.v1   0          8842301         8842355         54   risk-engine-0
```

Alert on **rate of change**, not absolute value — same rule as Event Hubs (Q47). Also watch **partition skew**: if one partition's lag is 100× the others, that's a hot key, not a slow consumer, and adding pods will not help.

**If they push back — "Lag is 2 million and rising. What do you do first?"** — Check whether it's all partitions or one. All partitions → the consumer is globally slower than the producer: scale out (up to the partition count), then look at what the handler does per record — nearly always a synchronous downstream call that should be batched. One partition → hot key; the fix is a repartition or a compound key, and that's a code change with a migration, not an incident action. Either way I'd first confirm the consumers are actually alive and not stuck in a rebalance loop from `max.poll.interval.ms` (Q53) — a rebalancing group has huge lag and zero throughput, and looks exactly like "too slow" on a dashboard.

---

### Q61–Q68. Kafka rapid depth
`[reference — one-liners for follow-ups]`

- **Q61. How is the partition chosen?** With a key: `murmur2(key) % num_partitions` — deterministic, so the same key always lands on the same partition *for a fixed partition count*. **Adding partitions rehashes future messages and breaks ordering for existing keys** — that alone is why partition count is a design decision. Without a key: sticky batching (fill a batch for one partition, then switch), not the old round-robin.
- **Q62. What's `__consumer_offsets`?** An internal compacted topic, 50 partitions by default, holding each group's committed offsets keyed by (group, topic, partition). Compaction is why it doesn't grow forever.
- **Q63. What is a rack-aware assignment?** `broker.rack` plus a rack-aware replica assignment spreads a partition's replicas across racks/availability zones, so an AZ loss doesn't take a partition below `min.insync.replicas`. In Azure that means brokers across all three zones. Non-negotiable in financial services.
- **Q64. Max message size?** Topic `max.message.bytes` defaults to **1048588** bytes (~1 MB). Raising it means also raising the broker's `replica.fetch.max.bytes` and the consumer's `max.partition.fetch.bytes` — three settings, and missing one gives you a stuck partition. Better answer: **claim-check** (§10.4).
- **Q65. What does `linger.ms` do?** Waits up to that long to fill a batch before sending. Default **5 ms**. Raising it trades latency for throughput and compression ratio. `batch.size` (default 16384) is the other half.
- **Q66. Tiered storage?** KIP-405: offload closed segments to object storage so a topic can retain months without local disk. Available for production use in recent 3.x/4.x. Relevant when a regulator requires seven years of an audit stream.
- **Q67. How do you delete a customer's data from Kafka (GDPR/DPDP)?** You can't edit a log. Three options: **compacted topic + tombstone** (null value for that key) so compaction eventually removes it; **crypto-shredding** — encrypt per subject and destroy the key, which is the only approach that works on a non-compacted topic; or short retention plus the system of record living in a database. Have this one ready — data-subject deletion is a live question on any EU/UK financial-services engagement.
- **Q68. `retries` and ordering?** With `enable.idempotence=true` (the 4.0 default), the broker's sequence numbers preserve per-partition order even with `max.in.flight.requests.per.connection=5` and retries. Without idempotence, anything above 1 in-flight request can reorder on retry — which is the historical reason people set `max.in.flight=1` and paid for it in throughput.

---

## 8. RabbitMQ

### Q69. Explain the AMQP 0-9-1 model.
`[MEDIUM]` `[opener — and it's the model, not the product, that they're testing]`

**Answer:** The thing that makes RabbitMQ different from every Azure service is that **producers never publish to a queue**. They publish to an **exchange** with a **routing key**. The exchange consults its **bindings** and decides which queues get a copy. Consumers subscribe to queues. That indirection is the whole design: routing topology is a broker-side configuration you can change without touching either side of the wire.

Four exchange types:

| Type | Routing rule | Use for |
|---|---|---|
| **direct** | routing key equals binding key, exactly | Point-to-point, severity routing (`payment.failed`) |
| **fanout** | ignores the routing key, copies to every bound queue | Broadcast — cache invalidation, "config changed" |
| **topic** | pattern match with `*` = one word, `#` = zero or more words | The workhorse: `trade.fx.confirmed`, bound as `trade.fx.*` or `trade.#` |
| **headers** | matches on header key/values with `x-match: all|any` | When the routing dimension isn't a string hierarchy |

```text
                 exchange: trade-events (topic)
publish rk="trade.fx.confirmed"
   |
   +-- binding "trade.fx.*"   --> queue: fx-desk
   +-- binding "trade.#"      --> queue: audit          (# = zero or more words)
   +-- binding "*.*.confirmed"--> queue: settlement
   +-- (no binding matches)   --> alternate-exchange, or the message is DROPPED SILENTLY
```

**The default exchange** is a nameless direct exchange to which every queue is automatically bound by its own name — that's why `basic_publish(exchange='', routing_key='my-queue')` "publishes to a queue". It's a convenience, not a different mechanism.

**If they push back — "Compare that to Service Bus topics."** — Same intent, different mechanics. Service Bus evaluates **SQL or correlation filters on message properties** at each subscription; RabbitMQ matches a **routing key against binding patterns** at the exchange. RabbitMQ is faster and more limited — routing is a string hierarchy you must design up front. Service Bus can filter on arbitrary properties including numeric comparisons. And RabbitMQ **silently drops** a message that matches no binding unless you configure an alternate exchange, which is the single most common RabbitMQ production surprise.

---

### Q70. Ack, nack, reject, and prefetch.
`[MEDIUM]`

**Answer:** RabbitMQ delivers under manual acknowledgement by default in any sane setup (`auto_ack=False`). The consumer then settles:
- **`basic_ack`** — processed, remove it.
- **`basic_nack(requeue=True)`** / **`basic_reject(requeue=True)`** — failed, put it back. **The trap: this requeues to the *front* of the queue and redelivers immediately, so a permanently-failing message becomes a hot loop that pins a CPU.**
- **`basic_nack(requeue=False)`** — failed, don't retry: routed to the **dead-letter exchange** if one is configured, otherwise dropped.
- `basic_nack` can settle multiple messages at once (`multiple=True`); `basic_reject` handles exactly one. That's the only real difference.

**Prefetch (`basic_qos(prefetch_count=N)`)** is how many unacknowledged messages the broker will push to one consumer. **The default is unlimited**, which means RabbitMQ shovels the entire queue into your slowest consumer's socket buffer, memory blows up, and load balancing across consumers disappears. Setting prefetch is not optional.

```python
channel.basic_qos(prefetch_count=20)   # never leave this unset
```

Rule of thumb: prefetch ≈ enough to cover network round-trip latency during processing, so ~1 for slow heavyweight work (fair dispatch, one at a time), and tens-to-hundreds for fast small messages. Note that **quorum queues do not support global QoS** — prefetch is per-consumer only there.

**If they push back — "How do you do a delayed retry then, if requeue is immediate?"** — Dead-letter it into a **delay queue with a TTL** that dead-letters back (Q71). That's the canonical RabbitMQ retry-with-backoff, and knowing it is the difference between having used RabbitMQ and having read about it.

---

### Q71. Build retry-with-backoff and a DLQ in RabbitMQ.
`[HARD]` `[the signature RabbitMQ pattern]`

**Answer:** RabbitMQ has no native delayed retry, so you build one out of **DLX + per-queue message TTL**, which forms a loop: work queue → (nack) → retry exchange → retry queue with a TTL and no consumer → (TTL expiry dead-letters it) → back to the work exchange. Multiple retry queues with increasing TTLs give you the backoff ladder.

```text
                          nack(requeue=False)
  [work.q] ---------------------------------> [retry.exchange]
     ^                                              |
     |                                     rk=retry.5s / retry.30s / retry.5m
     |                                              v
     |                                  [retry.5s.q  TTL=5000ms,  DLX=work.exchange]
     |                                  [retry.30s.q TTL=30000ms, DLX=work.exchange]
     |                                  [retry.5m.q  TTL=300000ms,DLX=work.exchange]
     |                                              |
     +----------------- TTL expires, dead-lettered back ---------------+

  attempts exhausted (x-death count) -> [parked.q]  (the real DLQ; humans look here)
```

```python
"""platform_messaging/rabbit.py — quorum queues, publisher confirms, DLX retry ladder."""
from __future__ import annotations

import json
import logging

import pika
from pika.exchange_type import ExchangeType

log = logging.getLogger(__name__)

WORK_EXCHANGE = "work.exchange"
RETRY_EXCHANGE = "retry.exchange"
PARKED_EXCHANGE = "parked.exchange"
WORK_QUEUE = "payments.work"
PARKED_QUEUE = "payments.parked"
LADDER_MS = [5_000, 30_000, 300_000]     # 5s -> 30s -> 5m, then park


def declare_topology(ch: pika.adapters.blocking_connection.BlockingChannel) -> None:
    ch.exchange_declare(WORK_EXCHANGE, ExchangeType.topic, durable=True)
    ch.exchange_declare(RETRY_EXCHANGE, ExchangeType.topic, durable=True)
    ch.exchange_declare(PARKED_EXCHANGE, ExchangeType.topic, durable=True)

    # Quorum queue: Raft-replicated, majority (N/2)+1. Replaces mirrored classic
    # queues, which were REMOVED in RabbitMQ 4.0.
    ch.queue_declare(
        WORK_QUEUE,
        durable=True,
        arguments={
            "x-queue-type": "quorum",
            "x-dead-letter-exchange": RETRY_EXCHANGE,
            "x-dead-letter-routing-key": "retry.5s",
            "x-delivery-limit": 5,          # quorum-queue poison guard (default 20 in 4.0+)
        },
    )
    ch.queue_bind(WORK_QUEUE, WORK_EXCHANGE, routing_key="payments.#")

    for ms in LADDER_MS:
        label = f"{ms // 1000}s" if ms < 60_000 else f"{ms // 60_000}m"
        qname = f"payments.retry.{label}"
        ch.queue_declare(
            qname,
            durable=True,
            arguments={
                "x-queue-type": "quorum",
                "x-message-ttl": ms,                       # nothing consumes this queue
                "x-dead-letter-exchange": WORK_EXCHANGE,   # TTL expiry sends it BACK
                "x-dead-letter-routing-key": "payments.retry",
            },
        )
        ch.queue_bind(qname, RETRY_EXCHANGE, routing_key=f"retry.{label}")

    ch.queue_declare(PARKED_QUEUE, durable=True, arguments={"x-queue-type": "quorum"})
    ch.queue_bind(PARKED_QUEUE, PARKED_EXCHANGE, routing_key="#")


def attempt_count(props: pika.BasicProperties) -> int:
    """x-death is stamped by the broker on every dead-letter hop."""
    deaths = (props.headers or {}).get("x-death") or []
    return sum(int(d.get("count", 0)) for d in deaths)


def on_message(ch, method, props, body) -> None:
    try:
        handle(json.loads(body))
    except (ValueError, KeyError) as exc:
        log.error("permanent failure: %s", exc)
        ch.basic_publish(PARKED_EXCHANGE, method.routing_key, body, properties=props)
        ch.basic_ack(method.delivery_tag)
        return
    except Exception as exc:
        n = attempt_count(props)
        if n >= len(LADDER_MS):
            log.error("attempts exhausted (%d), parking: %s", n, exc)
            ch.basic_publish(PARKED_EXCHANGE, method.routing_key, body, properties=props)
            ch.basic_ack(method.delivery_tag)
        else:
            label = (f"{LADDER_MS[n] // 1000}s" if LADDER_MS[n] < 60_000
                     else f"{LADDER_MS[n] // 60_000}m")
            log.warning("transient failure, retry in %s: %s", label, exc)
            ch.basic_publish(RETRY_EXCHANGE, f"retry.{label}", body, properties=props)
            ch.basic_ack(method.delivery_tag)
        return

    ch.basic_ack(method.delivery_tag)


def main(amqp_url: str) -> None:
    conn = pika.BlockingConnection(pika.URLParameters(amqp_url))
    ch = conn.channel()
    declare_topology(ch)

    ch.confirm_delivery()          # publisher confirms: basic_publish raises on nack
    ch.basic_qos(prefetch_count=20)  # NEVER leave prefetch unlimited (the default)
    ch.basic_consume(WORK_QUEUE, on_message, auto_ack=False)

    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()
    finally:
        conn.close()


def handle(payload: dict) -> None:
    ...


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main("amqps://user:pass@rabbit.internal:5671/%2f")
```

**If they push back — "Why not the rabbitmq_delayed_message_exchange plugin?"** — It's simpler and I'd use it where it's available: one exchange, `x-delay` header per message, arbitrary delays. But it's a community plugin, delayed messages are held in the exchange rather than a replicated queue, and managed offerings often don't have it enabled. The DLX+TTL ladder uses only core, durable, replicated primitives, which is why it's what I'd put in a platform template.

---

### Q72. Quorum queues vs classic mirrored queues.
`[MEDIUM]` `[CURRENCY CHECK — the removal is the thing to know]`

**Answer:** **Classic queue mirroring was removed in RabbitMQ 4.0.** Quorum queues are the replicated queue type now, full stop. They implement replication with the **Raft** consensus algorithm — a leader and followers, with a write acknowledged once a **majority, `(N/2)+1`**, has it. That's a fundamentally safer model than classic mirroring, which had well-known split-brain and message-loss modes under network partitions.

What quorum queues **don't** support: non-durable queues (they're always durable), exclusive queues, server-named queues, and **global QoS prefetch**. They **do** support message TTL and priorities (0–31), contrary to the widespread belief that they don't — that belief is out of date and correcting it is a nice signal.

Poison-message handling is built in: **`x-delivery-limit`, default 20** as of 4.0. Exceed it and the message is dropped or dead-lettered. Quorum queues also track `delivery-count` (incremented only on genuine failures) separately from `acquired-count`, which is a more honest poison-message signal than the classic redelivery flag.

**If they push back — "So when would you still use a classic queue?"** — Single-node dev environments, and genuinely transient queues — an exclusive, auto-delete, server-named reply queue for RPC, which quorum queues cannot be. Anything durable and production-facing is a quorum queue. There are also **streams** (`x-queue-type: stream`) if you want Kafka-like replayable semantics inside RabbitMQ, which is worth one sentence if they push further.

---

### Q73. Publisher confirms — what problem do they solve?
`[MEDIUM]`

**Answer:** By default `basic_publish` is fire-and-forget — it returns as soon as the bytes hit the socket, so a broker that's down, a full disk, or a rejected message all look like success. **Publisher confirms** (`confirm_delivery()`) put the channel into confirm mode: the broker returns `basic.ack` once the message is safely handled (persisted, if the message is persistent and the queue durable), or `basic.nack` if it couldn't be. In pika's `BlockingChannel` this makes `basic_publish` raise `pika.exceptions.NackError` on failure, which is what you want.

Pair it with **`mandatory=True`**, which makes the broker return an unroutable message instead of silently dropping it — that's the guard against the "no binding matched" failure mode from Q69. In pika you get `UnroutableError`.

Confirms plus persistent messages (`delivery_mode=2`) plus durable queues plus quorum replication is the full durability chain. Missing any link and the chain is only as strong as that link — a persistent message on a transient queue is still lost on restart.

**If they push back — "Doesn't waiting for confirms kill throughput?"** — Waiting for each one does, exactly like awaiting each Service Bus send. The high-throughput idiom is asynchronous confirms with a sliding window: publish N, track the delivery tags, handle acks/nacks as they arrive, block only when the window is full. `BlockingChannel` gives you the simple synchronous version; `SelectConnection` or `aio-pika` gives you the windowed one. Same tradeoff, same shape, in every broker.

---

### Q74. RabbitMQ vs Kafka. Give me the honest comparison.
`[MEDIUM]` `[NEAR-CERTAIN follow-up]`

**Answer:** **RabbitMQ is a broker that routes and tracks individual messages; Kafka is a replayable distributed log.** That single sentence generates every other difference.

| | RabbitMQ | Kafka |
|---|---|---|
| Storage model | Message removed on ack | Append-only log, removed by retention |
| Replay | No | **Yes**, any consumer group, from any offset |
| Routing | **Broker-side, per message** (exchanges, bindings, patterns) | None — consumer filters, or a stream processor |
| Competing consumers | **Native**, per message | Per *partition* — parallelism capped by partition count |
| Per-message lifecycle | **Yes** — ack/nack/DLX/TTL/priority per message | No — offsets only; DLQ is a topic you build |
| Ordering | Per queue, degrades with multiple consumers | Per partition, strict |
| Throughput | Very high for a broker; lower than Kafka at scale | Highest, by design |
| Priority | **Yes** (0–255 classic, 0–31 quorum) | No |
| Typical latency | Sub-millisecond to low ms | Low ms, tunable by `linger.ms` |
| Operationally | Simple; one binary; Raft for quorum queues | Heavier; brokers + KRaft controllers + registry + Connect |

**Choose RabbitMQ** for task distribution and RPC-ish workloads with complex routing, per-message priority, and per-message retry policy — a job queue, a workflow, a notification dispatcher. **Choose Kafka** for event streams that many teams consume independently, that must be replayable, and that feed analytics as well as operations.

The tell for RabbitMQ: *"different messages need to go to different places based on their content, and I need per-message retry and priority."* The tell for Kafka: *"three teams want this same data and one of them will want to reprocess history."*

**If they push back — "The client has both. Rationalise them."** — I wouldn't, not automatically. They're solving different problems and a forced consolidation usually means re-implementing one system's features badly inside the other. What I *would* rationalise is the operational surface — one auth model, one IaC module set, one observability stack, one on-call runbook covering both. That's the platform answer: standardise the *paved road*, not necessarily the *broker*.

---

### Q75. How does RabbitMQ fit an Azure engagement at all?
`[MEDIUM]` `[EY-shaped]`

**Answer:** Three ways, and it's worth naming them because the JD explicitly lists RabbitMQ alongside the Azure services. **Lift-and-shift**: the client already runs RabbitMQ on-prem and the fastest path to cloud is RabbitMQ on AKS (via the Cluster Operator) or a managed offering like CloudAMQP, with the application untouched. **AMQP 1.0 bridging**: Service Bus speaks AMQP 1.0; RabbitMQ speaks 0-9-1 natively but has an AMQP 1.0 plugin, so you can bridge rather than migrate. **Shovel and Federation**: RabbitMQ's own plugins for moving messages between brokers across a WAN — the standard tool for a hybrid on-prem/cloud transition where both sides run for months.

The honest framing for an interview: if a client is going all-in on Azure, Service Bus replaces RabbitMQ and the migration is mostly a routing-topology-to-topic-filter translation exercise. If they're multi-cloud or have deep AMQP 0-9-1 dependencies, RabbitMQ on Kubernetes is a perfectly good answer and you keep the topology.

**If they push back — "Map a RabbitMQ topology to Service Bus."** — Topic exchange → Service Bus **topic**. Binding pattern → **subscription with a correlation filter on `Subject`**, or a SQL filter with `LIKE` if the pattern is genuinely hierarchical. Queue → **subscription** (durable) or **queue** (direct). DLX+TTL ladder → **scheduled messages** or the built-in `MaxDeliveryCount`→DLQ, which is simpler. `x-delivery-limit` → `MaxDeliveryCount`. Prefetch → the SDK's `prefetch_count`. Publisher confirms → the SDK settles sends explicitly by default, so you get it for free. That mapping table is a genuinely useful thing to be able to produce on a whiteboard.

---

### Q76. What's the one RabbitMQ number people get wrong?
`[EASY]` `[trap-flavoured]`

**Answer:** **Prefetch defaults to unlimited.** Not 1, not 100 — unlimited. A fresh consumer with `basic_qos` unset will have the entire queue pushed at it, which destroys fair dispatch across consumers and can OOM the process. Every RabbitMQ consumer in the platform template sets it explicitly, and code review rejects one that doesn't.

Runner-up: **an unroutable message is silently dropped.** No error, no log, no DLQ — unless you publish with `mandatory=True` or configure an `alternate-exchange` on the exchange. Both belong in the template.

---

## 9. Batch meets stream — JD responsibility 4

> *"Implement Batch Jobs using event streaming and asynchronous messaging using Kafka, Service Bus, Event Grid, or RabbitMQ."*
> The wording is odd but the intent is clear and it is a real, common requirement: **run bulk workloads over a broker instead of cron-and-a-file-share.** Most candidates hear "batch" and start talking about Data Factory, which is a different answer to a different question. This section is the one to be fluent in.

### Q77. What does "batch jobs using event streaming" even mean, and why would you do it?
`[MEDIUM]` `[FRAME THE WHOLE SECTION WITH THIS ANSWER]`

**Answer:** It means decomposing a bulk workload into individually-tracked asynchronous units of work carried by a broker, instead of a single monolithic job reading a file and looping. The trigger is an event (a file landed, a window closed), the work items are messages, and completion is itself an event.

Why you'd do it — five reasons, and they're the ones the client will actually feel:

1. **Partial failure becomes survivable.** A monolithic job that dies at record 1.4 million of 2 million either restarts from zero or has hand-rolled resumption. With messages, 1.4 million completed, 12 failed and are in the DLQ, and the rest keep going.
2. **Elastic throughput.** The batch's parallelism becomes a consumer count you can scale from 0 to 30 with KEDA, and back to 0 when the window closes. No 8-hour VM that's idle for 16.
3. **Back-pressure for free.** If the downstream API allows 50 requests/second, the queue absorbs 2 million records at whatever rate they arrive and the consumers drain at 50/s. A loop over a file just DDoSes the partner.
4. **One code path.** The same consumer serves the nightly bulk load and the real-time trickle. You are not maintaining a batch ETL *and* an event handler that must stay behaviourally identical — which is the classic source of "the nightly reconciliation disagrees with the real-time feed."
5. **Observability and audit.** Every record has a message ID, a trace ID, a delivery count and a terminal state. "What happened to record 918,224?" becomes a query instead of a grep through a log file.

The cost is honest and you should state it: **you lose set-based operations.** A batch job can do one `MERGE` of 2 million rows; a message-per-record design does 2 million single-row operations, which is slower and more expensive against a relational target. That is precisely when ADF is the right answer instead (Q85).

**If they push back — "So this is just a job queue."** — Yes, and that's the point. The insight isn't novel, it's that most enterprises still run bulk integration as cron plus a shared drive plus a Python script with no retry, no idempotency, no observability and a 3am pager when it half-completes. Converting that to a broker-driven pipeline is a large fraction of real integration modernisation work, and it's what the JD is describing.

---

### Q78. Design it: 2 million records land nightly on SFTP; push them into a downstream REST API.
`[HARD]` `[THE WORKED DESIGN — rehearse this end to end; it is the most likely scenario question in this file]`

**Answer — say the shape first, then the detail:**

> "I'd split it into four stages with a broker between each: **land and register**, **split and enqueue**, **process with competing consumers**, and **aggregate and report**. Event Grid notices the file, a splitter chunks it into Service Bus messages under a batch header, a KEDA-scaled consumer pool drains the queue against the partner's rate limit, and a completion aggregator watches a counter to emit a single `BatchCompleted` event plus an error report. Every record is idempotent on a natural key so the whole batch can be re-run safely."

```text
 1. LAND
    SFTP (Azure Storage SFTP-enabled account) -> container: /inbound/positions/
        |  Microsoft.Storage.BlobCreated
        v
    Event Grid system topic, filtered subjectBeginsWith=/inbound/positions/, subjectEndsWith=.csv
        -> Service Bus queue: batch-control

 2. SPLIT  (one consumer, a Kubernetes Job or a single-replica Deployment)
    - Read blob as a STREAM (never load 2M rows into memory)
    - Compute batchId = sha256(blobName + etag)[:16]     <- deterministic; re-runs are idempotent
    - INSERT batch_header(batch_id, total, status='SPLITTING')   [rows counted as we stream]
    - For each chunk of 500 records:
        * write chunk to blob /staging/{batchId}/{seq}.jsonl        <- CLAIM CHECK
        * send Service Bus message: {batchId, seq, blobUri, count}  <- ~300 bytes
    - UPDATE batch_header SET total = <chunks>, status='DISPATCHED'
    - send batch-control message {batchId, 'DISPATCH_COMPLETE', total}

 3. PROCESS  (KEDA, min 0 / max 30, messageCount=5)
    for each chunk message:
      - download the chunk blob (claim check)
      - for each record:
          * idempotency check on natural key (batchId, recordKey) in a dedupe table
          * POST to partner API with Idempotency-Key: {batchId}:{recordKey}
          * retry transient with exponential backoff + FULL JITTER, honour Retry-After
          * on permanent failure: INSERT batch_error(batch_id, record_key, code, detail)
      - INSERT batch_chunk_result(batch_id, seq, ok_count, err_count)  [PK = (batch_id, seq)]
      - complete_message()

 4. AGGREGATE
    - after each chunk result: SELECT count(*) FROM batch_chunk_result WHERE batch_id = ?
      if count == batch_header.total -> emit BatchCompleted
    - belt and braces: a scheduled Service Bus message fires at T+2h; if the batch is
      still incomplete, emit BatchIncomplete and page.  (Never rely only on the happy path.)
    - BatchCompleted -> Event Grid -> Logic App: write the error CSV to /reports/,
      email ops, close the run in the control table.
```

**The design decisions to call out unprompted — this is what separates a senior answer:**

| Decision | Why |
|---|---|
| **Chunk of 500, not 1 message per record** | 2M individual messages is 2M broker operations and 2M DB round trips. 4,000 chunk messages is a rounding error in cost, and a chunk is still small enough that a failure loses at most 500 records of progress |
| **Claim check for the chunk payload** | 500 records won't fit in 256 KB; the message carries a blob URI and stays ~300 bytes. Also means a retry re-reads the same immutable blob |
| **`batchId` derived from blob name + ETag** | Re-uploading the same file produces the same batch ID, so dedupe makes the whole re-run a no-op. A GUID would silently double-process |
| **Chunk result table with PK `(batch_id, seq)`** | The completion counter is idempotent — a redelivered chunk can't double-count. Counting completed messages instead would be a race |
| **A scheduled timeout message** | Fan-out/fan-in with a counter cannot detect "a chunk never arrived". The T+2h scheduled message is the only thing that catches a lost chunk |
| **Errors to a table, not to the DLQ** | Per-*record* business failures aren't poison *messages*. The DLQ is for messages the consumer couldn't process; a rejected record is data the business needs to see in a report |
| **`Idempotency-Key` header on the partner call** | Pushes dedupe to the far side too, so a network timeout followed by a retry doesn't double-post |
| **KEDA min 0** | The consumer pool costs nothing for the 22 hours a day the batch isn't running |

**Rate limiting against the partner:** if they allow 50 req/s, that's the *global* budget, so per-pod rate = 50 ÷ replicas, and I'd cap `maxReplicaCount` accordingly rather than trusting a distributed limiter. Alternatively put APIM in front with `rate-limit-by-key` and let the gateway own the budget ([Azure Integration Services §3](02-azure-integration-services.md)) — better, because the limit then holds no matter how many consumers exist.

**If they push back — "2 million records through a REST API at 50/s is 11 hours. That won't fit the window."** — Correct, and that's the most important thing in the design, so I'd surface it in the first conversation, not in production. Three options in order: (1) ask the partner for a **bulk endpoint** — most have one, and 2M records in 4,000 batched calls fits in minutes; (2) negotiate a higher rate limit for the batch window; (3) if neither, the honest answer is that the requirement and the interface are incompatible and the client needs to know before we build. Spotting that the arithmetic doesn't work *is* the senior contribution. Anyone can write the consumer.

---

### Q79. How do you track completion of a batch spread across N async messages?
`[HARD]` `[the bit everyone fumbles]`

**Answer:** Three mechanisms, and I'd name all three because they suit different scales.

**1. Batch header plus an idempotent counter** (the design above). A control row holds the expected total; each chunk writes a result row keyed on `(batch_id, seq)`; completion is `count(results) == total`. **The primary key is what makes it idempotent** — a redelivered chunk overwrites rather than double-counts. Cheap, works at any scale, and the control table doubles as the audit record.

**2. Durable Functions fan-out/fan-in.** The orchestrator dispatches N activity functions and `yield context.task_all(tasks)` blocks until all complete, with replay-based checkpointing so the orchestrator survives restarts. Right when N is in the hundreds-to-low-thousands and you want the aggregation logic to read like code rather than SQL. Wrong at N=4,000+ because the orchestration history table grows with every event.

```python
# Durable Functions (Python v2) fan-out / fan-in
import azure.durable_functions as df

def orchestrator(context: df.DurableOrchestrationContext):
    batch = context.get_input()
    chunks = yield context.call_activity("SplitBatch", batch)

    tasks = [context.call_activity("ProcessChunk", c) for c in chunks]
    results = yield context.task_all(tasks)          # fan-in; survives host restarts

    summary = {
        "batchId": batch["batchId"],
        "ok": sum(r["ok"] for r in results),
        "errors": sum(r["err"] for r in results),
    }
    yield context.call_activity("PublishBatchCompleted", summary)
    return summary

main = df.Orchestrator.create(orchestrator)
```

**3. Service Bus session state as the checkpoint.** Put every chunk of a batch in one **session** keyed by `batchId`; the consumer holds the session and keeps a running counter in **session state** (256 KB Standard / 100 MB Premium). When the counter hits the total, emit completion. Elegant — the checkpoint lives in the broker, no database — but it serialises the batch to one consumer, so it only suits batches where ordering matters more than throughput.

**And regardless of mechanism: a timeout.** A counter can only observe messages that arrive; it can never detect one that didn't. A **scheduled Service Bus message** set at dispatch time for T+SLA is the watchdog. Without it, a lost chunk means a batch that is *silently* 99.97% complete forever, and that is the failure mode that actually burns people.

**If they push back — "What if the total isn't known up front — a streaming source?"** — Then completion isn't a count, it's a **watermark**: an explicit end-of-stream sentinel message, or a quiet period (no messages for T), or a window boundary. For a file you always know the total after the split, which is why the splitter writes it. For a genuinely unbounded source, "batch complete" isn't a meaningful concept and you should say so and reframe to windows.

---

### Q80. The claim-check pattern — implement it.
`[MEDIUM]` `[named explicitly in Microsoft's Cloud Design Patterns; near-certain if payload size comes up]`

**Answer:** When the payload exceeds the broker's message limit — 256 KB on Service Bus Standard, 1 MB on Event Grid and Event Hubs Standard, 64 KB on Storage Queues, ~1 MB on Kafka by default — you write the payload to blob storage and put **a pointer in the message**. The consumer fetches the payload on receipt. The broker moves metadata; the storage layer moves bytes.

Producer side is in §4 Q27. Consumer side:

```python
"""Claim-check resolution on the consumer, with a Premium-tier bypass."""
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

blobs = BlobServiceClient(
    "https://contosointegration.blob.core.windows.net", DefaultAzureCredential()
)


def _s(v) -> str:
    """Service Bus returns application_properties keys and values as bytes."""
    return v.decode() if isinstance(v, (bytes, bytearray)) else str(v)


def resolve_payload(msg) -> dict:
    props = {_s(k): _s(v) for k, v in (msg.application_properties or {}).items()}

    if props.get("claimCheck") != "blob":
        return json.loads(b"".join(msg.body))          # small message, inline

    client = blobs.get_blob_client(props["claimCheckContainer"], props["claimCheckBlob"])
    return json.loads(client.download_blob().readall())
```

**Four operational points to raise, because the pattern is easy and the operations are not:**
- **Lifecycle management.** Claim-check blobs are garbage after processing. A storage lifecycle rule deleting `claim-check/**` after 30 days is mandatory, or the container grows forever and the bill with it.
- **Access.** The consumer needs RBAC on the container, or the message carries a **short-lived user-delegation SAS** (the Valet Key pattern). Never a long-lived account-key SAS in a message that might sit in a DLQ for a week.
- **The DLQ paradox.** If a message dead-letters and the blob has already been lifecycle-deleted, the DLQ message is unreplayable. Set the blob TTL longer than your DLQ drain SLA — that's an actual production incident, not a hypothetical.
- **Immutability.** Write the blob once with `overwrite=False`. A retry that rewrites the payload can change what a redelivered message sees, which turns an idempotent consumer into a non-deterministic one.

**If they push back — "Service Bus Premium does 100 MB. Why bother?"** — Three reasons. It's **AMQP-only and single messages only** — a *batch* is capped at 1 MB on every tier including Premium. Large messages measurably reduce throughput and increase latency, and Microsoft's own guidance says to keep payloads small even where 100 MB is allowed. And it doesn't port: the same code against Standard, Event Grid, Storage Queues or Kafka breaks. The claim check works everywhere and costs one blob read.

---

### Q81. How do you make a batch re-runnable?
`[HARD]`

**Answer:** Three properties, and you need all three.

**Deterministic identity.** The batch ID and every record key must be derivable from the input, not generated. `batchId = sha256(blobName + etag)[:16]` means re-uploading the identical file produces the identical batch ID, so dedupe recognises the re-run. A `uuid4()` makes every re-run a fresh double-processing.

**Idempotent record processing.** Every record's effect is keyed on `(batch_id, record_key)` in a dedupe table checked before the side effect, and the downstream call carries an `Idempotency-Key`. Re-running then costs time and nothing else.

**Explicit resumability.** The chunk result table *is* the resume point: on re-run, the splitter skips chunks that already have a result row. That turns "restart the failed batch" from a 2-million-record replay into a 12-chunk replay.

```sql
-- The control tables. This is the whole mechanism.
CREATE TABLE batch_header (
    batch_id      VARCHAR(32)  PRIMARY KEY,          -- sha256(blob+etag), deterministic
    source_blob   VARCHAR(512) NOT NULL,
    total_chunks  INT          NULL,                 -- known only after the split
    status        VARCHAR(16)  NOT NULL,             -- SPLITTING|DISPATCHED|COMPLETE|FAILED
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ  NULL
);

CREATE TABLE batch_chunk_result (
    batch_id   VARCHAR(32) NOT NULL,
    seq        INT         NOT NULL,
    ok_count   INT         NOT NULL,
    err_count  INT         NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (batch_id, seq)                      -- makes the counter idempotent
);

CREATE TABLE batch_error (
    batch_id   VARCHAR(32)  NOT NULL,
    record_key VARCHAR(128) NOT NULL,
    error_code VARCHAR(64)  NOT NULL,
    detail     TEXT         NULL,
    PRIMARY KEY (batch_id, record_key)               -- a retry overwrites, never duplicates
);

-- Resume: which chunks still need dispatching?
SELECT s.seq
FROM   generate_series(0, (SELECT total_chunks - 1 FROM batch_header WHERE batch_id = $1)) AS s(seq)
WHERE  NOT EXISTS (
    SELECT 1 FROM batch_chunk_result r
    WHERE r.batch_id = $1 AND r.seq = s.seq
);
```

**If they push back — "The source file changed between runs, so the ETag changed and it's a new batch ID."** — Correct, and that's the desired behaviour: a different file is a different batch. The problem case is the opposite — an operator re-uploads the *same* file to force a re-run, gets the same ETag and the same batch ID, and dedupe makes it a no-op. So the runbook needs an explicit **force re-run** path: an operator-supplied `runAttempt` folded into the record key, executed through the same approval-gated pipeline as the DLQ replay. Design the escape hatch deliberately rather than letting someone discover `TRUNCATE` at 2am.

---

### Q82. Ordering within a batch — does it matter, and how do you get it?
`[MEDIUM]`

**Answer:** Usually it doesn't and you should check before paying for it, because ordering costs you the parallelism that made this design worth doing. Ask: are the records independent facts (positions, customers, prices) or a sequence of mutations to shared state (postings against an account)? Independent → no ordering, full parallelism. Mutations → ordering per entity, not per batch.

If you need it, use the **session/partition key at the entity level**: `SessionId = account_id`, or Kafka `key = account_id`. Chunk *by key* rather than by row number so all of one account's records live in one chunk and are processed in file order inside it. That gives you per-account ordering with batch-wide parallelism — the same "smallest scope that satisfies the invariant" answer as Q4.

If you genuinely need whole-batch ordering, you have a single-threaded batch and the design collapses to a loop, at which point say so and use ADF or a plain job. Don't pretend a queue gives you something it doesn't.

**If they push back — "What about a header record that must land before its details?"** — Two clean options. **Chunk them together** so header and details are in one message and one transaction — usually the right answer for a parent-child file format. Or **two-phase**: dispatch all headers, wait for that wave to complete via the counter, then dispatch details. The second is what Durable Functions fan-out/fan-in expresses naturally, and it's a legitimate use of the orchestrator.

---

### Q83. Micro-batching and batch windows — when do you use them?
`[MEDIUM]`

**Answer:** Micro-batching is accumulating messages for a short window and processing them as a set, to amortise a fixed per-operation cost. You use it when the downstream cost is dominated by the *call*, not the *payload* — a database `MERGE`, a bulk API endpoint, a vector-DB upsert, a blob write. Processing 500 records in one `MERGE` versus 500 single-row upserts is often a 50× difference.

Mechanisms, by broker: Service Bus `receive_messages(max_message_count=100, max_wait_time=5)` and settle each one after the bulk operation succeeds; Kafka `consume(num_messages=500, timeout=1.0)` then one commit; Event Grid **output batching** on the subscription; Event Hubs `on_event_batch`; RabbitMQ prefetch plus `basic_ack(multiple=True)`.

Two rules that are easy to get wrong: **settle only after the bulk operation is durable**, and settle *all* of them — a partial failure inside a batch means either the whole batch retries (so the bulk operation must be idempotent) or you split the batch and settle individually. And **always bound the wait**, so a quiet period doesn't hold messages hostage past their TTL; `max_wait_time` is what makes it a *window* rather than a *hang*.

```python
# Service Bus micro-batching against a bulk downstream.
with client.get_queue_receiver("positions", max_wait_time=5) as receiver:
    while running:
        msgs = receiver.receive_messages(max_message_count=100, max_wait_time=5)
        if not msgs:
            continue
        rows = [resolve_payload(m) for m in msgs]
        try:
            bulk_merge(rows)                    # ONE round trip; must be idempotent
        except TransientError:
            for m in msgs:
                receiver.abandon_message(m)     # whole window retries
            continue
        for m in msgs:
            receiver.complete_message(m)        # settle only after durability
```

**If they push back — "What's the risk?"** — Latency (a message waits up to the window) and blast radius (one poison record can fail a window of 100). Mitigation: on batch failure, fall back to processing that window one at a time so you isolate the offending record and DLQ only it. That two-mode consumer — bulk on the happy path, single-record on failure — is the pattern worth naming, and it's exactly how Kafka Connect's `errors.tolerance` handling behaves.

---

### Q84. Partial failure and per-item error reporting.
`[MEDIUM]`

**Answer:** The rule: **distinguish a failed *message* from a failed *record*.** A failed message — the consumer couldn't do its job at all (downstream down, blob unreadable, deserialisation broken) — is retried and eventually dead-lettered. A failed record — the data is invalid, the account doesn't exist, the amount breaches a limit — is a *business outcome*, and it belongs in an error table and a report, not in a DLQ. Confusing the two produces a DLQ full of perfectly valid messages nobody can act on and a business that never learns which of its records were rejected.

So each chunk consumer produces two outputs: a result row (`ok_count`, `err_count`) and zero-or-more `batch_error` rows keyed `(batch_id, record_key)` so retries overwrite rather than duplicate. On completion the aggregator renders the error rows to a CSV in `/reports/{batchId}/errors.csv` and notifies. That CSV is what the business actually wants, and producing it is often the difference between a delivered integration and one that gets escalated.

**If they push back — "The client wants the whole batch to fail if any record fails."** — All-or-nothing across 2 million records via a REST API means a distributed transaction, which you don't have. What you can offer is: (a) **validate-then-commit** — a first pass validates every record and rejects the file before any side effect, which is usually what "all or nothing" actually means; or (b) **compensation** — process everything, then reverse on failure, which requires the partner to support reversal. I'd propose (a), because it's cheap and it's almost always the real requirement.

---

### Q85. When is Azure Data Factory the right answer instead?
`[MEDIUM]` `[MUST be able to say this — otherwise you look like someone with a hammer]`

**Answer:** When the work is **set-based data movement rather than per-record business processing**. Concretely, ADF wins when:

- The source and sink are both **data stores** — SQL to SQL, SFTP to ADLS, SAP to Synapse — and no partner API is in the middle.
- You need **bulk copy performance**: ADF's Copy activity with staged copy and PolyBase/COPY INTO moves tens of millions of rows in a way 4,000 REST calls never will.
- You need a **self-hosted integration runtime** to reach an on-prem SQL Server or SAP HANA behind a firewall.
- The transformation is **schema-level** — mapping data flows, schema drift handling — not business logic.
- It's an **SSIS lift-and-shift**.
- The client's data team owns it and wants a visual pipeline with run history, not a container.

**The honest split I'd say out loud:** *"ADF for bulk data movement; broker-driven batch for bulk business processing. If the destination is a table, ADF. If the destination is an API with per-record semantics, rate limits and per-record error reporting, messaging. And the two compose — ADF lands and stages the file, then drops one message on a queue to kick off the per-record stage."*

That composition is often the real architecture: ADF does what it's good at (moving 2M rows from SFTP to ADLS efficiently, with retries and lineage), and the messaging pipeline does what it's good at (per-record API calls with idempotency, back-pressure and error reporting). Proposing the hybrid rather than defending one tool is the senior answer. See [Azure Integration Services §7](02-azure-integration-services.md) for ADF depth.

**If they push back — "So why not do the whole thing in ADF with a Web activity per row?"** — Because ADF's ForEach with a Web activity is billed per activity run and capped at modest parallelism; 2 million activity runs is both slow and expensive, and you get no DLQ, no idempotency layer and no per-record retry policy. ADF's execution model is designed for tens-to-hundreds of activities moving large volumes each, not millions of tiny activities. Knowing the tool's grain is the point.

---

## 10. The patterns senior interviewers grill on

### Q86. Idempotent consumer — three implementations, and when each is right.
`[HARD]` `[NEAR-CERTAIN at senior level]`

**Answer:** At-least-once delivery makes an idempotent consumer mandatory, not optional. Three implementations, in ascending order of cost:

**1. Natural idempotency.** The operation is already safe to repeat — `UPSERT` on a primary key, `SET status='CONFIRMED'`, writing a blob with a deterministic name. Free. Always check for this first; a surprising fraction of handlers are naturally idempotent and people bolt on machinery they don't need. The tell is that the operation is *absolute* rather than *relative*: `SET balance = 100` is idempotent, `balance = balance + 50` is not.

**2. Dedupe table on a business key.** Insert `(message_id)` or `(entity_id, operation)` with a unique constraint *before* the side effect, in the same transaction; a duplicate key violation means "already done, ack and move on." Costs one write per message. This is the default in the platform template.

**3. Idempotency key propagated downstream.** For side effects you don't own, send an `Idempotency-Key` header and let the receiver dedupe. Necessary when the side effect is a partner API call — a dedupe table on your side doesn't help if you crashed *after* the call and *before* recording it.

```python
"""platform_messaging/idempotency.py — the dedupe used by the consumer base class."""
from __future__ import annotations

import psycopg
from psycopg.errors import UniqueViolation

DDL = """
CREATE TABLE IF NOT EXISTS processed_message (
    consumer   VARCHAR(64)  NOT NULL,      -- scope per consumer group; two consumers
    message_id VARCHAR(128) NOT NULL,      -- of the same topic must not block each other
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (consumer, message_id)
);
CREATE INDEX IF NOT EXISTS ix_processed_message_at ON processed_message (processed_at);
"""


def process_once(conn: psycopg.Connection, consumer: str, message_id: str, fn) -> bool:
    """Run fn() at most once for this (consumer, message_id). True if it ran."""
    with conn.transaction():                       # ONE transaction: claim + effect
        try:
            conn.execute(
                "INSERT INTO processed_message (consumer, message_id) VALUES (%s, %s)",
                (consumer, message_id),
            )
        except UniqueViolation:
            return False                           # already processed; ack the message
        fn(conn)                                   # side effect shares the transaction
    return True
```

**Why the insert goes first and inside the same transaction:** if you did the work then recorded it, a crash between the two replays the work. If you recorded it in a separate transaction and then crashed, the message is marked done but the work never happened — silent data loss, which is worse. One transaction makes claim and effect atomic. This only works when the side effect is in the *same database*; if it isn't, you're in outbox territory (Q87) or idempotency-key territory.

**Retention:** `processed_message` grows forever unless you prune it. Delete rows older than your maximum possible redelivery horizon — DLQ drain SLA plus the broker's TTL. A nightly `DELETE ... WHERE processed_at < now() - interval '30 days'` on the index, or table partitioning by day if the volume warrants it.

**If they push back — "What's the key: `MessageId` or a business key?"** — Prefer the **business key** (`order_id`, `trade_id + version`) because it survives things `MessageId` doesn't: a redelivery from the DLQ replay job with a *new* `MessageId` (§4 Q29), a re-publish from an upstream retry, or two different producers reporting the same fact. `MessageId` only catches broker-level redelivery. Use both if you can — `MessageId` for the cheap fast path, business key for correctness.

---

### Q87. The transactional outbox. Show me the SQL and the relay.
`[HARD]` `[THE senior pattern question. Have this fully loaded.]`

**Answer:** The problem: you must update your database *and* publish a message, and there is no distributed transaction between Postgres and Service Bus. Write the DB first and the broker call fails → the world never hears about it. Publish first and the DB write fails → you've announced something that didn't happen. Both are unacceptable in financial services.

The outbox: **write the message into a table in the same local transaction as the business change**, then a separate **relay** reads the table and publishes. The DB transaction is atomic, so the message is durable exactly when the business change is. The relay gives you at-least-once publication, which duplicate detection and an idempotent consumer absorb.

```sql
CREATE TABLE outbox (
    id             BIGSERIAL    PRIMARY KEY,
    aggregate_type VARCHAR(64)  NOT NULL,
    aggregate_id   VARCHAR(128) NOT NULL,
    message_id     VARCHAR(128) NOT NULL UNIQUE,   -- deterministic; drives dup-detection
    subject        VARCHAR(128) NOT NULL,          -- event type
    session_id     VARCHAR(128) NULL,              -- ordering scope, if any
    payload        JSONB        NOT NULL,
    traceparent    VARCHAR(64)  NULL,              -- trace context captured at write time
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    published_at   TIMESTAMPTZ  NULL,
    attempts       INT          NOT NULL DEFAULT 0
);

-- Partial index: the relay only ever scans unpublished rows, so the index stays tiny
-- even when the table holds months of history.
CREATE INDEX ix_outbox_unpublished ON outbox (id) WHERE published_at IS NULL;
```

```sql
-- The business transaction. ONE transaction, two statements. This is the whole pattern.
BEGIN;
  UPDATE account
     SET balance = balance - 1250.00
   WHERE account_id = 'GB29NWBK60161331926819'
     AND balance >= 1250.00;

  INSERT INTO outbox (aggregate_type, aggregate_id, message_id, subject, session_id,
                      payload, traceparent)
  VALUES ('Account', 'GB29NWBK60161331926819',
          'PMT-2026-08-25-0009931',                       -- business-derived, NOT a GUID
          'PaymentDebited',
          'GB29NWBK60161331926819',
          '{"amount":"1250.00","ccy":"GBP"}'::jsonb,
          '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01');
COMMIT;
```

```python
"""platform_messaging/outbox_relay.py — the polling publisher.

Run N replicas. SKIP LOCKED is what makes N safe: each replica claims a disjoint
set of rows without blocking on the others.
"""
from __future__ import annotations

import json
import logging
import signal
import threading
import time

import psycopg
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

log = logging.getLogger("outbox-relay")
_stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *_: _stop.set())

CLAIM_SQL = """
SELECT id, message_id, subject, session_id, payload, traceparent
FROM   outbox
WHERE  published_at IS NULL
ORDER  BY id                 -- id order == commit order per session; preserves ordering
LIMIT  %s
FOR UPDATE SKIP LOCKED       -- the load-bearing clause: no two relays claim the same row
"""


def relay_once(conn: psycopg.Connection, sender, batch: int = 100) -> int:
    # One transaction: claim rows, publish, mark published. If we crash after the
    # send but before COMMIT, the rows unlock and are republished -> at-least-once.
    with conn.transaction():
        rows = conn.execute(CLAIM_SQL, (batch,)).fetchall()
        if not rows:
            return 0

        messages = []
        for _id, message_id, subject, session_id, payload, traceparent in rows:
            props = {"schemaVersion": "1"}
            if traceparent:
                props["traceparent"] = traceparent
            messages.append(ServiceBusMessage(
                body=json.dumps(payload, separators=(",", ":")).encode(),
                message_id=message_id,     # duplicate detection makes the replay a no-op
                session_id=session_id,
                subject=subject,
                content_type="application/json",
                application_properties=props,
            ))

        sender.send_messages(messages)     # <= 1 MB per batch on EVERY tier
        conn.execute(
            "UPDATE outbox SET published_at = now(), attempts = attempts + 1 "
            "WHERE id = ANY(%s)",
            ([r[0] for r in rows],),
        )
    return len(rows)


def main(dsn: str, namespace: str, entity: str) -> None:
    client = ServiceBusClient(namespace, DefaultAzureCredential())
    with client, client.get_queue_sender(entity) as sender, psycopg.connect(dsn) as conn:
        idle = 0.05
        while not _stop.is_set():
            try:
                n = relay_once(conn, sender)
            except Exception:
                log.exception("relay batch failed; backing off")
                time.sleep(2.0)
                continue
            # Adaptive poll: tight when busy, back off to 1s when idle.
            idle = 0.05 if n else min(idle * 2, 1.0)
            _stop.wait(idle)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main("postgresql://app@pg:5432/core", "contoso-payments.servicebus.windows.net",
         "payment-events")
```

**The four things to say about `FOR UPDATE SKIP LOCKED`:** it lets you run N relay replicas with no leader election, no distributed lock and no coordination — each claims rows nobody else holds. `ORDER BY id` preserves commit order. Without `SKIP LOCKED` the replicas serialise on the same rows and you've built a distributed queue with one worker. And it's the same primitive you'd use for any "claim work from a table" problem — SQL Server's equivalent is `WITH (UPDLOCK, READPAST)`, which is worth naming if the client is on SQL Server.

**Alternative to polling: the log tail.** **Debezium** via Kafka Connect reads the database's write-ahead log and publishes outbox inserts with zero polling and lower latency, using its dedicated outbox event router SMT. Cosmos DB's **change feed** does the same job natively. Naming both — "poll for simplicity, CDC for latency and scale" — is the complete answer.

**If they push back — "Doesn't this give duplicates?"** — Yes, deliberately: at-least-once. A crash between the send and the commit republishes. That's absorbed by the deterministic `message_id` plus Service Bus duplicate detection on the send side, and an idempotent consumer on the receive side. **Duplicates are recoverable; lost messages are not** — so every design decision in this pattern trades toward duplication. That sentence is the pattern's philosophy and it's worth saying.

---

### Q88. The inbox pattern.
`[MEDIUM]`

**Answer:** The outbox's mirror image on the receive side: before processing, the consumer writes the incoming message's ID into an **inbox** table in the same transaction as the side effect; a duplicate key means "already handled". It is Q86's dedupe table, named as a pattern because it pairs with the outbox to give end-to-end effective-once across two services that share no transaction.

The version worth knowing is the **two-phase inbox** for when processing is slow: phase one durably records the message and acks the broker immediately (so the lock isn't held and the delivery count doesn't climb); phase two processes from the inbox table on your own schedule with your own retry policy. You've moved the message from the broker's reliability domain into your database's, which is the right move when processing takes minutes and the broker's lock is measured in seconds.

**If they push back — "Isn't that just re-implementing the queue in your database?"** — Partly, yes, and that's the cost. You'd only do it when broker semantics genuinely don't fit: processing longer than the maximum lock duration (5 minutes on Service Bus), or a retry policy that must survive a redeploy, or the need to query pending work relationally. Otherwise the simple inbox — dedupe check inside the processing transaction — is enough and I'd default to that.

---

### Q89. Saga: choreography vs orchestration, with a worked compensation.
`[HARD]` `[NEAR-CERTAIN at senior level]`

**Answer:** A saga is how you get a business transaction across services without a distributed transaction: a sequence of local transactions, each with a **compensating action** that semantically undoes it. Compensation is not rollback — you can't un-charge a card, you issue a refund, and the refund is visible in the ledger. That distinction is the interesting part.

**Choreography**: each service listens for events and emits its own. No coordinator. Loosely coupled, no single point of failure, but the process exists nowhere — you reconstruct it by reading five codebases, and cyclic dependencies creep in.

**Orchestration**: a coordinator (Durable Functions, Logic App, a state machine service) explicitly calls each step and drives compensation. The process is legible in one place and easy to observe; the coordinator is a dependency and can become a distributed monolith if you put business logic in it.

**My rule: choreography for 2–3 steps, orchestration for 4+, and always orchestration where an auditor must see the process.** In financial services that's nearly always orchestration — "show me the state of this transaction" has to be answerable.

```text
ORDER -> PAYMENT -> INVENTORY, with compensation

  happy path
    1. OrderService     : CreateOrder(status=PENDING)          [local txn]
    2. PaymentService   : AuthorizeAndCapture(orderId, 1250)   [local txn]
    3. InventoryService : ReserveStock(orderId, sku, qty)      [local txn]
    4. OrderService     : ConfirmOrder(status=CONFIRMED)       [local txn]

  failure at step 3 (out of stock) -> compensate backwards
    3'. InventoryService: nothing to undo (it failed)
    2'. PaymentService  : RefundPayment(orderId)          <- NOT a rollback; a new ledger entry
    1'. OrderService    : CancelOrder(status=CANCELLED, reason=OUT_OF_STOCK)
    +   Notify the customer. The customer MUST be told; a silent compensation is a complaint.
```

```python
# Durable Functions orchestrator — compensation is explicit, and it is code, not config.
import azure.durable_functions as df


def order_saga(context: df.DurableOrchestrationContext):
    order = context.get_input()
    completed: list[str] = []

    try:
        yield context.call_activity("CreateOrder", order)
        completed.append("order")

        yield context.call_activity("CapturePayment", order)
        completed.append("payment")

        yield context.call_activity("ReserveStock", order)
        completed.append("stock")

        yield context.call_activity("ConfirmOrder", order)
        return {"status": "CONFIRMED", "orderId": order["orderId"]}

    except Exception as exc:
        # Compensate in reverse. Every compensation must itself be idempotent,
        # because the orchestrator replays and may re-invoke it.
        if "stock" in completed:
            yield context.call_activity("ReleaseStock", order)
        if "payment" in completed:
            yield context.call_activity("RefundPayment", order)
        if "order" in completed:
            yield context.call_activity("CancelOrder",
                                        {**order, "reason": str(exc)[:200]})
        yield context.call_activity("NotifyCustomer",
                                    {**order, "outcome": "CANCELLED"})
        return {"status": "CANCELLED", "orderId": order["orderId"], "reason": str(exc)[:200]}


main = df.Orchestrator.create(order_saga)
```

**The four things that make this a senior answer:** compensations are **idempotent** (the orchestrator replays); the `completed` list means you only compensate what actually happened; the customer is **notified**, because a silent compensation generates a complaint and a regulatory issue; and the return value records *why*, so the state is auditable.

**If they push back — "What if the compensation itself fails?"** — Then you have a **stuck saga**, and there is no clever answer — you cannot compensate a compensation forever. What you do is: retry the compensation with backoff, and after N attempts move the saga into a `NEEDS_MANUAL_INTERVENTION` state, emit an alert, and expose it in an operations view. Every real saga implementation has that terminal state, and a design that doesn't have one is incomplete. In banking there's usually a suspense account for exactly this: money parks there until a human resolves it. Naming the suspense account is the domain-fluency signal.

---

### Q90. Exponential backoff with full jitter — give me the formula and why the jitter.
`[MEDIUM]` `[explicitly requested; the "why" is what's being tested]`

**Answer:** Plain exponential backoff makes every failed client retry at the same moments — 1s, 2s, 4s, 8s — so a downstream that went down under load gets hit by a perfectly synchronised thundering herd the instant it tries to recover, and falls over again. Jitter breaks the synchronisation by randomising the delay. AWS's canonical analysis compared the variants and **Full Jitter came out best**: fewer total calls than decorrelated jitter, and dramatically less client work and server load than no jitter at all.

```text
Full Jitter        sleep = random(0, min(cap, base * 2 ** attempt))
Equal Jitter       sleep = base + random(0, min(cap, base * 2 ** attempt))
Decorrelated       sleep = min(cap, random(base, sleep * 3))
```

```python
"""platform_messaging/backoff.py"""
from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def full_jitter(attempt: int, base: float = 0.1, cap: float = 30.0) -> float:
    """sleep = random(0, min(cap, base * 2**attempt))  — AWS 'Full Jitter'."""
    return random.uniform(0.0, min(cap, base * (2 ** attempt)))


def retry(fn: Callable[[], T], *, attempts: int = 6, base: float = 0.1,
          cap: float = 30.0, retry_on: tuple[type[Exception], ...] = (Exception,)) -> T:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except retry_on as exc:
            last = exc
            # Honour a server-supplied Retry-After over our own schedule — the server
            # knows when it will be ready and we do not.
            hint = getattr(exc, "retry_after", None)
            delay = float(hint) if hint else full_jitter(attempt, base, cap)
            time.sleep(delay)
    raise last  # type: ignore[misc]
```

**Say this about the "why":** it isn't about being polite. Synchronised retries turn a brief downstream blip into a **self-sustaining outage** — the recovering service is knocked over by the retry storm, everyone backs off in lockstep, and the storm repeats on the next boundary. That's a metastable failure, and jitter is the cheapest possible fix. Pair it with a **retry budget** (cap total retries as a fraction of traffic) and a **circuit breaker** (Q91) so you stop retrying a service that's clearly down.

**If they push back — "The broker already retries. Why do you need this?"** — Different layers. The broker retries *delivery of the message to me* (delivery count → DLQ). This retries *my call to a downstream* inside a single message's processing. Without it, a transient 503 from a partner burns a delivery attempt and pushes the message toward the DLQ for no reason. With it, three in-process retries over a couple of seconds absorb the blip and the message completes normally. Both layers, doing different jobs. Getting that distinction crisp is the mark of someone who has actually run this.

---

### Q91. Circuit breaker in a message consumer — what's different?
`[MEDIUM]`

**Answer:** The three states are standard — **closed** (calls pass), **open** (calls fail fast for a cooldown), **half-open** (one probe decides whether to close or re-open). What's different in a consumer is that **fast-failing is the wrong response**. In a synchronous API, an open breaker returns 503 to the caller and that's the end of it. In a consumer, fast-failing means you rip through the entire queue in seconds, burn every message's delivery count, and dump the whole backlog into the DLQ — an outage in a downstream becomes a data-loss incident in your DLQ.

So in a consumer, an open circuit must **stop consuming**, not fail fast. Concretely: stop the receiver (or pause the Kafka partitions), sleep for the cooldown, then resume. The messages stay in the queue where they belong, and the broker does the load-levelling it exists to do.

```python
# The consumer-shaped breaker: STOP CONSUMING, don't fail fast.
if breaker.is_open():
    log.warning("circuit open for %s — pausing consumption for %ss",
                breaker.name, breaker.cooldown)
    _stop.wait(breaker.cooldown)      # messages remain queued; delivery counts untouched
    continue
```

On Kubernetes this composes nicely with autoscaling: an open breaker can also flip the pod's readiness probe, which takes it out of rotation, and KEDA's queue-length signal keeps the replica count where it needs to be for the eventual drain. On Service Bus specifically, Premium namespaces and APIM both have server-side circuit breakers you can use instead of hand-rolling one ([Azure Integration Services §3](02-azure-integration-services.md)).

**If they push back — "How do you tune the thresholds?"** — Failure *rate* over a rolling window, not consecutive failures, because at high throughput a burst of five consecutive failures means nothing. Something like: open at >50% failures over 20+ calls in 30 seconds; cooldown 30s with full jitter so N pods don't probe simultaneously; half-open admits one call. And **exclude business failures** — a 422 from a validation rule is not a downstream health signal, and counting it will trip the breaker on bad data rather than a bad dependency.

---

### Q92. Poison message handling — the full decision tree.
`[MEDIUM]`

**Answer:**

```text
message fails
  |
  +-- Is the failure DETERMINISTIC? (schema invalid, unparseable, business rule violated,
  |     referenced entity will never exist)
  |     -> DEAD-LETTER IMMEDIATELY with reason + stack trace.
  |        Do NOT burn 10 delivery attempts on something that cannot succeed:
  |        it delays the DLQ alert and wastes downstream calls.
  |
  +-- Is the failure TRANSIENT? (timeout, 503, deadlock, throttled)
  |     -> in-process retry with full jitter (Q90)
  |     -> still failing? abandon; let delivery_count climb toward the DLQ
  |     -> failing for EVERY message? that's an outage: open the breaker and STOP
  |        consuming (Q91). Do not DLQ 200k valid messages.
  |
  +-- Is it a per-RECORD business rejection inside a batch message?
        -> that is DATA, not a poison message. Error table + report (§9 Q84).
```

The classification lives in the consumer base class so every team gets it identically, and the exception taxonomy is part of the platform contract: `PermanentError` → dead-letter, `TransientError` → retry, `BusinessRejection` → error table. A handler raising a bare `Exception` is treated as transient, which is the safe default.

**If they push back — "How do you know it's a real outage and not ten unlucky messages?"** — A rolling failure-rate window across the consumer group, exported as a metric. If failures correlate with a single `MessageId` it's poison; if they're uniform across distinct message IDs and started at a timestamp, it's an outage. That distinction is a dashboard panel and an alert rule, and it's in the platform's alert pack rather than in each team's head.

---

### Q93. Competing consumers and back-pressure.
`[MEDIUM]`

**Answer:** **Competing consumers** is N instances pulling from one queue; the broker's lock guarantees one message to one consumer, so scaling is just adding pods. It requires idempotency (a redelivery may land on a different pod) and it gives up ordering unless you use sessions/keys.

**Back-pressure** is what stops a fast producer destroying a slow consumer. In a pull-based broker you get it structurally — the queue absorbs the burst and consumers pull at their own rate; that's Microsoft's **Queue-Based Load Levelling** pattern and it's the main reason to put a queue in front of a fragile legacy backend. What you must add is a **bound**: message TTL so a backlog can't grow forever, an alert on queue depth and age-of-oldest-message, and a producer-side response when the queue is over a threshold — shed load, return 429 at the API edge, or slow the batch splitter.

In push-based systems (Event Grid → webhook, RabbitMQ without prefetch) you have **no natural back-pressure** and must create it: Event Grid gets a Service Bus queue as its destination; RabbitMQ gets `prefetch_count`; a webhook consumer returns 429/503 so the sender's retry policy backs off.

**If they push back — "The queue grew to 4 million messages overnight. What now?"** — First establish whether it's still growing: a stable 4M is a completed burst that will drain; a growing 4M is a permanent throughput deficit and no amount of waiting fixes it. Then scale consumers to the limit of the *downstream*, not the queue — usually the downstream is the constraint, so more pods just move the queue into the partner's rate limiter. Then check TTL, because messages that expire during the drain dead-letter en masse and you'd rather know first. And the real fix is upstream: the producer should not have been allowed to emit 4M messages into a queue whose consumers drain at 500/s, which is a capacity-planning conversation and a design record entry.

---

### Q94. Correlation ID vs causation ID.
`[MEDIUM]` `[small, precise, and it separates people]`

**Answer:** **Correlation ID** identifies the whole business transaction and is copied unchanged onto every message it spawns — it answers *"show me everything that happened because a customer clicked buy."* **Causation ID** is the ID of the *immediate parent* message that caused this one — it answers *"what directly triggered this message?"* Correlation gives you the set; causation gives you the tree.

```text
HTTP POST /orders        correlationId=C1   messageId=M1   causationId=(none)
 └─ OrderCreated         correlationId=C1   messageId=M2   causationId=M1
     ├─ PaymentRequested correlationId=C1   messageId=M3   causationId=M2
     │   └─ PaymentFailed correlationId=C1  messageId=M4   causationId=M3
     └─ StockReserved    correlationId=C1   messageId=M5   causationId=M2
```

```python
def derive(parent, payload: dict) -> ServiceBusMessage:
    """Every message the platform emits derives from its parent this way."""
    return ServiceBusMessage(
        body=json.dumps(payload).encode(),
        message_id=new_deterministic_id(payload),
        correlation_id=parent.correlation_id or parent.message_id,   # inherit, or start it
        application_properties={"causationId": parent.message_id},   # always the parent
    )
```

These are **not** the same as the W3C trace context, and the distinction is worth making: `traceparent` is for *technical* tracing tools (App Insights, Jaeger) and its span IDs are per-hop and short-lived. Correlation and causation IDs are **business-domain identifiers** that live in your event store and are queryable months later when someone asks what happened to order 9931. Carry both.

**If they push back — "Isn't that redundant with the trace ID?"** — Traces are sampled and expire; App Insights retention is 30–90 days and head sampling may have dropped the very trace you need. Business correlation IDs live in your database as long as the record does, and they survive the trace backend being replaced. On a regulated engagement, "we can't answer that because the trace was sampled out" is not an acceptable answer to a regulator.

---

### Q95–Q100. Pattern rapid depth
`[reference]`

- **Q95. Competing consumers vs partitioned consumers?** Competing = any consumer takes any message, maximum elasticity, no ordering (Service Bus queue, RabbitMQ). Partitioned = a key binds to one consumer, ordering preserved, elasticity capped at the partition/session count (Kafka, Event Hubs, Service Bus sessions). You choose by whether you need ordering.
- **Q96. Priority queues?** RabbitMQ has native priority (0–255 classic, 0–31 quorum). Service Bus and Kafka do not — you emulate with **separate entities per priority** and a consumer that drains high before low. Say the caveat: strict priority starves the low queue, so real implementations use a weighted poll (e.g. 4 high : 1 low) instead.
- **Q97. Messaging bridge?** Moving messages between two brokers or two namespaces — RabbitMQ Shovel/Federation, Kafka MirrorMaker 2, Service Bus auto-forward across namespaces via a relay, or Azure's own Messaging Bridge pattern. The hybrid on-prem-to-cloud transition tool.
- **Q98. Anti-corruption layer?** A translation boundary so a legacy system's model doesn't leak into your domain: a consumer that reads the legacy shape and publishes the canonical shape. In messaging this is usually a dedicated "adapter" consumer per legacy system — which is literally JD responsibility 2.
- **Q99. Event-carried state transfer vs event notification?** A notification says "OrderCreated, id=9931" and the consumer calls back for detail — small messages, coupling to the source's availability. State transfer puts the full state in the event — bigger messages, but consumers work when the source is down. In a distributed integration estate, **prefer state transfer**, because the whole point of decoupling is surviving the other system's downtime. Watch the message size limit; that's when the claim check appears.
- **Q100. Sequence-gap detection?** When ordering matters and you can't have sessions, the producer stamps a monotonic per-key sequence number and the consumer tracks the last-seen value per key: `n+1` → process; `≤ n` → duplicate, drop; `> n+1` → gap, so buffer/defer and alert. Cheap, and it turns a silent ordering violation into an alert.

---

## 11. Observability — JD responsibility 8

### Q101. What do you monitor on a queue, and which of those pages someone at 3am?
`[MEDIUM]` `[NEAR-CERTAIN — "observability" is named in the JD]`

**Answer:** Five signals, and only two of them page.

| Signal | What it tells you | Threshold shape | 3am page? |
|---|---|---|---|
| **Queue depth** (`ActiveMessages`) | Backlog size | Rate of change, not absolute | **No** — a spike is often a normal burst |
| **Age of oldest message** | Whether the backlog is *moving* | > SLA (e.g. 15 min) | **YES** — this is the real SLA breach |
| **DLQ depth** (`DeadletteredMessages`) | Messages that failed terminally | Any increase from zero | **YES** — messages are stuck and someone must act |
| **Consumer lag** (streams) | Distance behind the head | Monotonic growth over 15 min | **YES** for streams |
| **Processing latency** (p50/p95/p99) | Per-message handler health | p99 > 2× baseline | No — ticket |
| **Active consumer count** | Are consumers even running? | == 0 with depth > 0 | **YES** — silent total failure |
| **Throttled requests** | You've hit a tier limit | > 0 | Ticket, unless sustained |
| **Abandon / lock-lost rate** | Consumers failing or too slow | > 1% of receives | Ticket |

**The senior point, and make it explicitly: depth is the wrong alert.** Queue depth spikes during every normal burst and every deploy, so alerting on it produces noise and people stop reading the alerts. **Age of the oldest message** is the signal that actually maps to a business SLA — "no payment instruction waits more than 15 minutes" is a statement the business understands and a queue with 4 million messages that are all 8 seconds old is perfectly healthy. Depth is a capacity-planning metric; age is an SLA metric.

**DLQ depth is the one that always pages**, because a non-empty DLQ means messages exist that no automated process will ever handle. Alert on *any* increase, not on a threshold — one dead-lettered payment is an incident.

**If they push back — "What about a dashboard?"** — Depth, age-of-oldest and DLQ depth per entity; lag per partition per consumer group for streams; handler latency percentiles and error rate; and consumer replica count overlaid on depth so you can see whether autoscaling responded. That's one Grafana/Workbook JSON shipped with the platform module — every team gets the same dashboard, which means an on-call engineer can read *any* team's queue at 3am without learning a new layout. That standardisation is worth more than any individual panel.

---

### Q102. How does a distributed trace survive a broker hop?
`[HARD]` `[EXPLICITLY the thing most people miss — high-value]`

**Answer:** It doesn't, unless you make it. HTTP propagation works because every framework auto-instruments headers. A broker breaks the chain: the producer's span ends when the send returns, the consumer's span starts fresh minutes later on a different machine, and unless the **W3C trace context travels inside the message**, you get two unrelated traces and no way to connect them.

So the trace context must ride in the **message properties/headers**, not the body:

| Broker | Where it goes |
|---|---|
| Service Bus | `application_properties["traceparent"]` (and `tracestate`) |
| Event Hubs / Kafka | Kafka record **headers**: `traceparent`, `tracestate` |
| Event Grid | CloudEvents **extension attribute** `traceparent` (a first-class part of the envelope) |
| RabbitMQ | `BasicProperties.headers` |
| Storage Queue | Inside the body — it has no header concept. Wrap the payload in an envelope |

The header format, exactly (W3C Trace Context, a W3C Recommendation since **23 November 2021**):

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ^^ ^------------------------------^ ^--------------^ ^^
             |  trace-id, 32 hex                 parent-id/span-  trace-flags,
             version, 2 hex                      id, 16 hex       2 hex (01 = sampled)

tracestate: rojo=00f067aa0ba902b7,congo=t61rcWkgMzE     (max 32 key/value pairs)
```

```python
"""platform_messaging/tracing.py — producer inject / consumer extract."""
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind, Link

tracer = trace.get_tracer("platform.messaging")


def inject_into(props: dict) -> dict:
    """Producer side: writes traceparent (+ tracestate) into a plain dict."""
    with tracer.start_as_current_span("publish", kind=SpanKind.PRODUCER):
        inject(props)          # uses the globally configured W3C propagator
    return props


def consume_with_trace(msg, handler) -> None:
    """Consumer side: rebuild the context from the message and continue the trace."""
    carrier = {
        (k.decode() if isinstance(k, bytes) else k):
        (v.decode() if isinstance(v, bytes) else v)
        for k, v in (msg.application_properties or {}).items()
    }
    ctx = extract(carrier)                      # <- the load-bearing line

    # CONSUMER span linked to the producer's context. Use a link rather than a
    # plain parent for batches, where one span consumes N differently-traced messages.
    with tracer.start_as_current_span(
        "process",
        context=ctx,
        kind=SpanKind.CONSUMER,
        links=[Link(trace.get_current_span(ctx).get_span_context())],
        attributes={
            "messaging.system": "servicebus",
            "messaging.destination.name": "payment-instructions",
            "messaging.message.id": msg.message_id,
            "messaging.servicebus.message.delivery_count": msg.delivery_count,
        },
    ):
        handler(msg)
```

**Say this:** the Azure SDKs do some of this automatically via `Diagnostic-Id`/`traceparent`, and OpenTelemetry's messaging semantic conventions define the attribute names above — but on a mixed estate (a Java producer, a Python consumer, a Logic App in the middle, a partner's webhook) automatic instrumentation is uneven. So the platform template does it **explicitly**, and code review checks for it. The result is one end-to-end trace from the API gateway, through the broker, to the downstream call — which is what "observability" in the JD actually means.

**If they push back — "Why a Link instead of a parent span?"** — Because a consumer that micro-batches 100 messages processes 100 different traces in one span; it can only have one parent, but it can have 100 links. Links express "this span was caused by these" without lying about the hierarchy. For one-message-per-span, a parent is fine and simpler. Knowing when each applies is the detail that shows real OTel use rather than a copied snippet.

---

### Q103. What's the difference between Application Insights and OpenTelemetry here?
`[MEDIUM]`

**Answer:** OpenTelemetry is the **vendor-neutral SDK, wire protocol and semantic conventions**; Application Insights is a **backend**. The current Azure recommendation is to instrument with the OpenTelemetry SDK and export to Application Insights via the Azure Monitor OTLP exporter — you keep the Azure-native experience (Application Map, end-to-end transaction view, KQL) while the instrumentation stays portable if the client later moves to Grafana Cloud or Datadog.

For messaging specifically, App Insights gives you two things that are hard to build: the **Application Map** drawing the broker as a node between producer and consumer, and **end-to-end transaction details** showing the queue wait time as a visible gap. Both depend entirely on the trace context actually crossing the broker (Q102) — without that, the map shows two disconnected islands, which is the usual state of an uninstrumented estate.

**If they push back — "Sampling?"** — Head-based sampling at the SDK is cheapest but you lose the failed traces you most wanted. For messaging I'd sample successes aggressively (5–10%) and keep **100% of anything that dead-lettered, abandoned, or exceeded a latency threshold**, using an OTel tail-sampling collector or App Insights' adaptive sampling with a custom rule. And note the compliance angle: on a financial-services engagement, sampling decisions need to be documented, because "we sampled it out" is not a defensible answer to an audit query.

---

### Q104. What logs do you write from a consumer?
`[EASY-MEDIUM]`

**Answer:** Structured JSON, one line per message outcome, with a fixed field set so a single KQL query works across every consumer on the platform:

```python
log.info(
    "message_processed",
    extra={
        "messageId": msg.message_id,
        "correlationId": msg.correlation_id,
        "causationId": props.get("causationId"),
        "sessionId": msg.session_id,
        "entity": "payment-instructions",
        "consumer": "payment-consumer-v3",
        "deliveryCount": msg.delivery_count,
        "enqueuedTimeUtc": msg.enqueued_time_utc.isoformat(),
        "queueLatencyMs": (now - msg.enqueued_time_utc).total_seconds() * 1000,
        "processingMs": elapsed_ms,
        "outcome": "completed",         # completed|abandoned|deadlettered|deferred
        "traceId": trace_id,
    },
)
```

Two things to call out. **`queueLatencyMs`** — enqueued time to processing start — is the age-of-oldest-message metric measured per message, and it's the one number that tells you whether the system is meeting its SLA. And **never log the payload**: it's PII on a financial-services engagement and it violates the client's own data-handling policy. Log identifiers and let the operator look up the record in the source system if they need the content.

**If they push back — "What about the DLQ message content for debugging?"** — The content stays in the DLQ, which is inside the client's security boundary and covered by the namespace's encryption and RBAC. The log records that a message was dead-lettered, its ID, and the reason. An operator with the right role reads the payload from the DLQ via an audited tool. That separation — identifiers in logs, content in the broker — is what keeps a log aggregator from becoming an unmanaged copy of the client's customer data.

---

### Q105. Compliance and auditability — what does financial services add?
`[MEDIUM]` `[EY DE + FS framing; connects to the business-unit context]`

**Answer:** Five things that don't come up on a retail engagement:

1. **Data residency.** Messages must not leave the jurisdiction. That constrains the namespace region, the geo-replication secondary, the Capture storage account, the trace backend, and the log workspace — and people forget the last two, which is where a residency breach usually happens.
2. **Encryption with customer-managed keys.** Service Bus Premium and Event Hubs Premium/Dedicated support CMK; Standard does not. If the client must hold the key material, the tier is decided for you.
3. **Immutable audit of message flow.** Diagnostic settings on the namespace exporting operational and runtime audit logs to an immutable storage account with a legal hold, plus per-message identifiers in a queryable store. Note Event Hubs **runtime audit logs are Premium and Dedicated only**.
4. **Right to erasure (GDPR / India's DPDP Act).** A log you cannot edit meets a regulation that says you must delete. The answers are tombstones on a compacted topic, crypto-shredding, or keeping personal data out of the stream entirely and carrying a pseudonymous key — which is the cleanest and the one I'd propose first.
5. **Segregation of duties.** The person who deploys the consumer must not be the person who can replay the DLQ unilaterally. That's why the replay job is an approval-gated pipeline (§4 Q29) — the gate *is* the control, and the pipeline run is the evidence.

**If they push back — "Does that change the architecture or just the config?"** — Mostly the config, but three of them change the *tier*, and tier changes are architecture: CMK forces Premium, runtime audit logs force Premium/Dedicated, and Private Link forces Premium on Service Bus. So the compliance conversation has to happen before the sizing conversation, not after — otherwise you cost the engagement on Standard and discover in the security review that you need Premium.

---

## 12. The AWS mirror table

The JD says "Azure or AWS" and names EKS and CloudFormation, so don't be caught flat. Lead Azure; know the mapping.

| Azure | AWS | Notes on the difference |
|---|---|---|
| Service Bus **queue** | **SQS** (Standard or FIFO) | SQS Standard is at-least-once, no ordering; **SQS FIFO** gives ordering per `MessageGroupId` — the direct analogue of a Service Bus **session** |
| Service Bus **topic + subscriptions** | **SNS → SQS fan-out** | SNS alone has no durable subscription; the standard pattern is SNS topic fanning out to per-consumer SQS queues. SNS filter policies ≈ correlation filters |
| Service Bus **DLQ** | SQS **redrive policy** → a DLQ you create | AWS's DLQ is a separate queue you must create; Azure's is a built-in subqueue |
| Service Bus `MaxDeliveryCount` | SQS `maxReceiveCount` | Same concept, same role |
| Service Bus **peek-lock** | SQS **visibility timeout** | Default 30 s, max 12 h — longer than Service Bus's 5-minute max lock |
| Service Bus **duplicate detection** | SQS FIFO **content-based dedup** (5-min window, fixed) | Azure's window is configurable 20 s–7 d; AWS's is fixed at 5 minutes |
| Service Bus **scheduled messages** | SQS **delay queues / `DelaySeconds`** (max 15 min) or EventBridge Scheduler | SQS caps at 15 minutes; Service Bus schedules arbitrarily far out |
| **Event Grid** | **EventBridge** | EventBridge has richer rule-based filtering, a schema registry, an archive-and-replay feature Event Grid lacks, and Pipes/Scheduler |
| Event Grid **system topics** | EventBridge **default event bus** (AWS service events) | Same idea: first-party events for free |
| **Event Hubs** | **Kinesis Data Streams** (or **MSK** for real Kafka) | Kinesis shards ≈ partitions; 1 MB/s in, 2 MB/s out per shard — near-identical to a TU. MSK is managed Apache Kafka |
| Event Hubs **Capture** | Kinesis **Firehose** to S3 | Firehose is more configurable (JSON, Parquet, transformation Lambda) |
| Event Hubs **consumer group** | Kinesis **enhanced fan-out consumer** | Enhanced fan-out gives each consumer its own 2 MB/s, unlike the shared quota |
| **Storage Queue** | **SQS Standard** | Closest AWS equivalent by cost and simplicity |
| **KEDA on AKS** | KEDA on EKS, or **Lambda event source mapping** | Lambda's SQS/Kinesis event source mapping is the serverless equivalent of a scaled consumer |
| **Bicep / ARM** | **CloudFormation / CDK** | Terraform spans both |
| Managed identity + RBAC | **IAM roles for service accounts (IRSA)** | Same shape: federate a K8s service account to a cloud identity, no secrets |

**The line to have ready:** *"The primitives map almost one-to-one — the differences that actually bite are ordering (SQS FIFO's `MessageGroupId` vs Service Bus sessions), that AWS makes you create the DLQ explicitly, and that EventBridge has archive-and-replay while Event Grid doesn't. I'd lead with Azure on a Microsoft-shop client and I can design the same architecture on AWS."*

---

## 13. 30-second whiteboard versions

### 13.1 Service Bus vs Event Grid vs Event Hubs (the one you will be asked)

```text
    "what IS the message?"
             |
   +---------+-----------+-------------------+
   |                     |                   |
 COMMAND              NOTIFICATION        TELEMETRY
 "do this"            "this happened"     "here's a value"
 must not be lost     small, disposable   high volume, replayable
   |                     |                   |
 SERVICE BUS          EVENT GRID          EVENT HUBS
 pull, AMQP           push, HTTP          pull, log
 DLQ, sessions,       retry schedule,     partitions, consumer
 dup-detect, txns     dead-letter to blob groups, offsets, Capture
 256KB / 100MB Prem   1 MB, no ordering   1 MB, 90d retention, Kafka API

 Combine them: Grid notices -> Bus does the work -> Hubs records the stream.
```

Spoken: *"Command → Service Bus. Notification → Event Grid. Telemetry stream → Event Hubs. And in practice I combine them: Grid to notice, Bus to do the work reliably, Hubs when several teams need the same data and one will replay it."*

### 13.2 The batch-over-messaging pipeline (JD responsibility 4)

```text
 SFTP/blob                Event Grid           Service Bus            KEDA pods
 ---------                ----------           -----------            ---------
 file lands  --BlobCreated--> filtered --> [batch-control] --> SPLITTER (1x)
                                                                  |
                            chunk = 500 records -> blob (claim check)
                            + message {batchId, seq, blobUri}
                                                                  v
                                                          [work queue] --> N consumers
                                                                  |         idempotent
                                                                  |         backoff+jitter
                                                                  |         rate-limited
                                                    +-------------+-------------+
                                                    |                           |
                                          chunk_result (PK batchId,seq)   batch_error rows
                                                    |                           |
                                          count == total? --> BatchCompleted --> error CSV
                                                    |                           + notify
                                          scheduled msg at T+2h = watchdog
```

Spoken: *"Event Grid triggers a splitter that chunks the file 500 records at a time into claim-checked messages. A KEDA-scaled consumer pool drains the queue idempotently against the downstream's rate limit. Each chunk writes a result row keyed on batch and sequence, so the completion counter is idempotent; when the count matches the total we emit BatchCompleted and render an error CSV. A scheduled message at T+2h is the watchdog for a chunk that never arrives."*

### 13.3 The transactional outbox

```text
  ONE local DB transaction
  +---------------------------------------------+
  |  UPDATE account SET balance = balance - 1250 |
  |  INSERT INTO outbox (message_id, payload...) |   message_id is DERIVED, not random
  +---------------------------------------------+
                     | COMMIT
                     v
              [outbox table]
                     |  N relay replicas:
                     |  SELECT ... WHERE published_at IS NULL
                     |  ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED
                     |  -> send -> UPDATE published_at -> COMMIT
                     v
              [Service Bus]   dup-detection on message_id absorbs the replay
                     v
              idempotent consumer  (dedupe table on business key)

  crash between send and COMMIT -> republish -> duplicate -> absorbed.
  Duplicates are recoverable. Lost messages are not.
```

---

## 14. Interviewer traps

> The wrong answer most candidates give, and the one that scores. Read this section last before the interview.

**Trap 1 — "Kafka and Service Bus are basically the same, just different vendors."**
**Wrong.** They are different *shapes*. Service Bus is a broker that tracks the lifecycle of each individual message — lock, delivery count, DLQ, dead-letter reason, session. Kafka is a replayable log where the only per-consumer state is an integer offset; it has **no DLQ, no per-message retry, no competing consumers within a partition, no server-side content filtering**. Microsoft says this in its own docs. Say: *"Kafka is a log, Service Bus is a broker. If I need to sideline one bad message and retry it three times, that's a broker. If I need three teams to replay last week independently, that's a log."*

**Trap 2 — "Event Grid guarantees delivery."**
**Wrong.** It is **at-least-once, best-effort**, with **no ordering guarantee**. Dead-lettering is **off by default** — if you don't configure it, failed events are silently **dropped**. It gives up after **at most 24 hours** (TTL default 1440 minutes) or **30 attempts**, whichever comes first. It puts consistently-failing endpoints into **probation** and skips deliveries. Say: *"Event Grid is durable-ish delivery for disposable events. If the event drives money, I terminate it at a Service Bus queue and let a durable consumer do the work."*

**Trap 3 — "`acks=all` means we can't lose data."**
**Wrong** unless `min.insync.replicas ≥ 2`. `acks=all` waits for all replicas *currently in the ISR* — and `min.insync.replicas` **defaults to 1**, so if the ISR has shrunk to just the leader, `acks=all` is `acks=1` and a leader failure loses the write. Say: *"`replication.factor=3` plus `min.insync.replicas=2` plus `acks=all` — that tolerates one broker loss with zero data loss and fails writes loudly if a second goes down. And `unclean.leader.election.enable=false`, always, in financial services."*

**Trap 4 — "Service Bus duplicate detection means I don't need an idempotent consumer."**
**Wrong.** Duplicate detection is **send-side only**: it drops a second send with the same `MessageId` inside the window. It does nothing about **redelivery**, which happens every time a consumer crashes between doing the work and calling `complete_message`. You need both. Say: *"Dup detection protects the send; an idempotent consumer protects the receive. Effectively-once means at-least-once delivery plus an idempotent consumer — that's the whole sentence."*

**Trap 5 — "Sessions give you FIFO on the queue."**
**Wrong.** Sessions give FIFO **within a session**, never across the entity. There is no global ordering in Service Bus, ever. And enabling sessions is entity-wide: once `requiresSession=true`, a message without a `SessionId` is dead-lettered with reason `Session ID is null`. Say: *"Ordering is per-key, and the design question is what the smallest key is that satisfies the business invariant — usually per-account or per-order, not global."*

**Trap 6 — "More partitions means more throughput."**
**Wrong, past a point.** Partitions set your maximum consumer *parallelism*; throughput on Event Hubs is set by **throughput units**, and on Kafka by broker/disk/network. Over-partitioning costs you: more rebalance churn, more checkpoint/lease overhead, smaller batches per fetch (so *worse* effective throughput), and on Basic/Standard Event Hubs you **cannot change the count after creation**. Say: *"Partitions are the parallelism dial, TUs are the throughput dial. For most enterprise integration workloads that's 4 to 32 partitions, not 200 — and I'd show the arithmetic before proposing 200."*

**Trap 7 — "We'll DLQ anything that fails."**
**Wrong** when the failure is an outage. If the downstream is down, every message fails identically and a fast-failing consumer will drain the whole queue into the DLQ in minutes — turning a dependency outage into a data-recovery incident. Say: *"One message failing is a poison message: dead-letter it. Every message failing is an outage: open the circuit breaker and **stop consuming** so the broker does the load-levelling it's there for. Fast-failing is right for an API and wrong for a consumer."*

**Trap 8 — "Alert on queue depth."**
**Wrong metric.** Depth spikes on every normal burst and every deploy, so a depth alert is noise and people learn to ignore it. **Age of the oldest message** is the SLA signal — a 4-million-message queue whose oldest message is 8 seconds old is healthy. Say: *"Depth is a capacity metric; age-of-oldest is the SLA metric. The two that page at 3am are age-of-oldest past SLA, and any increase in DLQ depth from zero."*

**Trap 9 — "OpenTelemetry handles the tracing automatically."**
**Wrong across a broker.** HTTP propagation is automatic; a broker hop is not. The `traceparent` has to be written into the **message properties/headers** by the producer and **extracted** by the consumer, or you get two disconnected traces and an Application Map showing two islands. Say: *"The trace context rides in the message properties — `application_properties['traceparent']` on Service Bus, Kafka record headers, or the CloudEvents `traceparent` extension attribute. It's `inject()` on the way out and `extract()` on the way in, and it's in the platform template because auto-instrumentation is uneven on a mixed estate."*

**Trap 10 — "Batch means Data Factory."**
**Wrong half the time,** and the JD explicitly asks for batch over messaging. ADF is for **set-based data movement** — store to store, bulk copy, self-hosted IR to on-prem. Broker-driven batch is for **bulk business processing** — per-record API calls with idempotency, rate limits, per-record error reporting and partial-failure survival. Say: *"If the destination is a table, ADF. If the destination is an API with per-record semantics, messaging. And they compose — ADF lands and stages the file, then drops one message to kick off the per-record stage."*

**Trap 11 — "Kafka gives you exactly-once."**
**Half wrong.** Kafka's EOS is exactly-once **within Kafka** — a transaction spanning consume, process and produce, plus the input offsets. The moment you write to Postgres, call a partner API or send an email, the guarantee stops at the broker boundary. Say: *"EOS is real and it's Kafka-to-Kafka. For consume-and-write-to-a-database I'd use at-least-once plus an idempotency key — simpler, cheaper, and just as correct end to end."*

**Trap 12 — "RabbitMQ mirrored queues for HA."**
**Out of date.** Classic queue mirroring was **removed in RabbitMQ 4.0**. Quorum queues are the replicated type now — Raft, majority `(N/2)+1`, with a built-in `x-delivery-limit` (default 20) for poison messages. Also correct the common myth: quorum queues **do** support message TTL and priorities (0–31); what they don't support is non-durable, exclusive, server-named queues and global QoS. Same currency check on the Kafka side: **ZooKeeper mode was removed in Kafka 4.0** and KRaft is the only mode; migrating from ZK means going through 3.9 first.

**Trap 13 — "Just increase the lock duration if processing is slow."**
**Wrong instinct.** The maximum is **5 minutes**, so it doesn't scale, and lock duration doubles as your **failure-detection time** — a 5-minute lock means an OOM-killed pod's message is invisible for 5 minutes. Say: *"Keep the lock short — 60 seconds — and renew from code with an `AutoLockRenewer`. A dead pod's messages come back in seconds while a slow-but-alive pod keeps its lock. If the work genuinely takes longer than 5 minutes, the message shouldn't be holding a broker lock at all — that's the two-phase inbox: record it durably, ack immediately, and process on my own schedule."*

---

## 15. Rapid fire

| # | Q | A |
|---|---|---|
| 1 | Service Bus Standard max message size? | **256 KB**, including system and user properties |
| 2 | Premium max message size? | **100 MB** over AMQP (default 1 MB per entity, raise it); 1 MB over HTTP; **1 MB for any batch, all tiers** |
| 3 | Default lock duration? Maximum? | **1 minute**; maximum **5 minutes** |
| 4 | Default `MaxDeliveryCount`? | **10** |
| 5 | Duplicate detection window: default / min / max? | **10 minutes** / 20 seconds / 7 days |
| 6 | Every system dead-letter reason? | `MaxDeliveryCountExceeded`, `TTLExpiredException`, `HeaderSizeExceeded`, `Session ID is null`, `MaxTransferHopCountExceeded` (+ filter-evaluation, + application-set) |
| 7 | DLQ path syntax? | `<queue>/$deadletterqueue`; `<topic>/Subscriptions/<sub>/$deadletterqueue` |
| 8 | Auto-forward hop limit? | **4** |
| 9 | Messages per Service Bus transaction? | **100** |
| 10 | Subscriptions per topic? | **2,000** |
| 11 | SQL filters vs correlation filters per topic? | **2,000** SQL vs **100,000** correlation — prefer correlation |
| 12 | Service Bus Premium messaging units? | **1, 2, 4, 8 or 16** |
| 13 | Session state size? | **256 KB** Standard, **100 MB** Premium |
| 14 | What does deferral do? | Removes the message from normal retrieval order; retrievable **only by `SequenceNumber`**, which you must persist. Does **not** increment delivery count |
| 15 | Event Grid retry schedule? | 10 s, 30 s, 1 m, 5 m, 10 m, 30 m, 1 h, 3 h, 6 h, then every 12 h up to 24 h — with randomisation, best-effort |
| 16 | Event Grid max attempts / TTL defaults? | **30 attempts** (1–30); **1440 minutes** TTL (1–1440); first to expire wins |
| 17 | Which HTTP codes count as success to Event Grid? | **200, 201, 202, 203, 204** — nothing else |
| 18 | Which codes are never retried? | **400**, **413**, **403** (and 401 for webhooks) |
| 19 | Event Grid dead-letter target and delay? | A **blob container**; **5-minute delay** after the last attempt; dropped if the target is unavailable for **4 hours** |
| 20 | Event Grid max event size? | **1 MB**, cannot be increased. Billing counts a "event" as a **64 KB chunk** |
| 21 | Event subscriptions per Event Grid topic? | **500** (100 at Azure-subscription scope) |
| 22 | Event Grid output batching limits? | 1–**5,000** events per batch; preferred size 1–1,024 KB; **all-or-none** semantics; off by default |
| 23 | Event Hubs partitions per hub? | **32** Basic/Standard, **100** Premium (200 per PU namespace-wide), **1,024** Dedicated |
| 24 | One throughput unit gives you? | **Ingress 1 MB/s or 1,000 events/s; egress 2 MB/s or 4,096 events/s.** Max 40 TU |
| 25 | Event Hubs retention by tier? | **1 day** Basic, **7 days** Standard, **90 days** Premium and Dedicated |
| 26 | Consumer groups per event hub? | **1** Basic, **20** Standard, **100** Premium, **1,000** Dedicated |
| 27 | Which tiers have the Kafka endpoint? | **Standard, Premium, Dedicated** — not Basic. Port **9093**, `SASL_SSL`, `PLAIN` or `OAUTHBEARER` |
| 28 | Event Hubs Capture windows? | Time **default 5 min** (1–15); size **default 300 MB** (10–500 MB); **first wins**; **Avro** |
| 29 | Offset vs sequence number vs checkpoint? | Byte position / logical per-partition counter / **your** durable record in blob storage — the broker tracks nothing |
| 30 | Which Kafka version removed ZooKeeper? | **4.0** (March 2025). KRaft only; no ZK mode, no migration *from* ZK in 4.0 — migrate via **3.9** first |
| 31 | Kafka 4.0 producer defaults for `acks` and `enable.idempotence`? | **`acks=all`** and **`enable.idempotence=true`** — both are now defaults |
| 32 | Default `min.insync.replicas`? | **1** — which is why you must set it to 2 explicitly |
| 33 | Default topic retention? | **604800000 ms = 7 days**; `retention.bytes` = **-1** (unlimited) |
| 34 | Default `max.poll.interval.ms` / `session.timeout.ms`? | **300000 (5 min)** / **45000 (45 s)** |
| 35 | Eager vs cooperative rebalancing? | Eager revokes **everything** from everyone (stop-the-world); cooperative-sticky revokes only what must move, in two rounds |
| 36 | What is log compaction for? | Keeping the **latest value per key forever** — a replayable current-state topic. Null value = **tombstone** (deletes the key) |
| 37 | Schema Registry default compatibility? Who upgrades first? | **BACKWARD**; **consumers first**. FORWARD = producers first. FULL = either order. `_TRANSITIVE` = checked against all versions, not just the latest |
| 38 | What is Kafka Connect for? | Declarative source/sink connectors (JDBC, Debezium CDC, SaaS) with SMTs — the JD's "connectors and adapters" answer |
| 39 | RabbitMQ exchange types? | **direct, fanout, topic, headers** (+ the nameless default direct exchange) |
| 40 | RabbitMQ default prefetch? | **Unlimited** — always set `basic_qos(prefetch_count=N)` |
| 41 | Classic mirrored queues — status? | **Removed in RabbitMQ 4.0.** Use quorum queues (Raft, majority `(N/2)+1`, `x-delivery-limit` default **20**) |
| 42 | How do you delay a retry in RabbitMQ? | **DLX + per-queue message TTL** ladder — nack to a retry queue with a TTL whose DLX points back at the work exchange |
| 43 | What does `mandatory=True` do? | Returns an unroutable message instead of silently dropping it — the guard against "no binding matched" |
| 44 | Storage Queue message size / TTL / max per read? | **64 KB** / default 7 days, `-1` = never / **32** messages per `Get Messages`; visibility timeout default **30 s**, max **7 days** |
| 45 | Claim-check pattern? | Payload to blob, **pointer in the message**. Watch the lifecycle rule vs your DLQ drain SLA, or DLQ'd messages become unreplayable |
| 46 | Transactional outbox in one line? | Write the message to a table in the **same local transaction** as the business change; a relay publishes it with `SELECT … FOR UPDATE SKIP LOCKED` |
| 47 | Why `SKIP LOCKED`? | Lets N relay replicas claim **disjoint** rows with no leader election and no blocking. SQL Server: `WITH (UPDLOCK, READPAST)` |
| 48 | Full jitter formula? | `sleep = random(0, min(cap, base * 2 ** attempt))` — AWS found it the best-performing variant |
| 49 | Why jitter at all? | Synchronised retries create a thundering herd that knocks over the recovering service — a metastable failure. Jitter is the cheapest fix |
| 50 | Saga: choreography vs orchestration? | Events with no coordinator vs an explicit coordinator. **2–3 steps → choreography; 4+ or an auditor → orchestration.** Compensation is a new forward action, not a rollback |
| 51 | What if a compensation fails? | Retry with backoff, then a terminal `NEEDS_MANUAL_INTERVENTION` state plus an alert. In banking, a suspense account |
| 52 | Correlation ID vs causation ID? | Correlation = the whole business transaction (inherited unchanged); causation = the **immediate parent** message ID. One gives the set, the other the tree |
| 53 | Is `traceparent` the same as a correlation ID? | No. `traceparent` is W3C technical trace context, sampled and short-lived; correlation IDs are business identifiers that live as long as the record |
| 54 | `traceparent` format? | `00-<32 hex trace-id>-<16 hex span-id>-<2 hex flags>`; W3C Recommendation since **23 Nov 2021**; `tracestate` holds up to 32 vendor pairs |
| 55 | Which two queue alerts page at 3am? | **Age of oldest message past SLA**, and **any increase in DLQ depth**. Depth alone is noise |
| 56 | Effectively-once, in one sentence? | **At-least-once delivery plus an idempotent consumer** |
| 57 | SQS FIFO's equivalent of a Service Bus session? | `MessageGroupId` |
| 58 | Azure equivalent of EventBridge / Kinesis? | Event Grid / Event Hubs. EventBridge has archive-and-replay; Event Grid does not |
| 59 | When is ADF the right answer? | Set-based store-to-store movement, bulk copy, self-hosted IR to on-prem, SSIS lift-and-shift. Not per-record API calls |
| 60 | How do you delete a customer's data from Kafka? | Compacted topic + tombstone, or **crypto-shredding** (encrypt per subject, destroy the key), or keep PII out of the stream and carry a pseudonymous key |

---

**Last-30-seconds refresher before you walk in:** Command→Bus, Notification→Grid, Stream→Hubs, cheap→Storage Queue. Ordering is per session/partition key, never global. Effectively-once = at-least-once + idempotent consumer. `RF=3` + `min.insync.replicas=2` + `acks=all`. ZooKeeper gone in Kafka 4.0; mirrored queues gone in RabbitMQ 4.0. Alert on **age of oldest**, not depth. `traceparent` rides in the message properties. Batch over messaging = chunk + claim check + idempotent counter + a scheduled watchdog. And every answer ends with the platform framing: *a reusable template, not a one-off consumer.*
