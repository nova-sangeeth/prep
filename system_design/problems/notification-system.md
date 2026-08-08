# Design a Notification System

## 1. Requirements
- **Functional:** Send notifications across channels — **push** (APNs/FCM), **SMS** (Twilio), **email** (SES/SendGrid). Support transactional (OTP, receipts) and bulk (campaigns). Honor user preferences/opt-outs. Deduplicate. Retry on transient failures. Provide delivery status/tracking. Template rendering with personalization.
- **Non-functional:**
  - **Scale:** ~10M DAU, peaks of ~10M+ notifications in a burst (campaign), steady ~thousands/s.
  - **Latency:** transactional (OTP) p99 < 1s end-to-end to the gateway; bulk can lag minutes.
  - **Availability:** 99.99% for transactional; a third-party gateway outage must not lose messages.
  - **Reliability:** **at-least-once** delivery with **idempotency** so retries don't double-send; ordering not strictly required.
  - **Compliance:** opt-out/unsubscribe, quiet hours, rate limits per user/channel.

## 2. Back-of-envelope estimates
- **Steady load:** say 100M notifications/day → ~1,160/s average; campaign bursts push to ~50-100k/s for short windows.
- **Fanout:** a single "event" can fan out to multiple channels per user × millions of users. A 10M-user campaign at 50k/s drains in ~200s — so we need a buffer (queue) and worker autoscaling.
- **Storage (status/audit):** 100M/day × ~300 bytes (id, user, channel, status, ts) ≈ **30 GB/day** ≈ 11 TB/yr → time-series/wide-column, TTL old rows to cold storage.
- **Dedup window store:** keep notification IDs for ~24h: 100M × ~50 bytes ≈ 5 GB → Redis with TTL.
- **Bandwidth:** small per-message; the cost is request volume to third-party gateways (rate-limited), not bytes.

## 3. API
```
POST /v1/notify
  { idempotency_key, user_id|segment, template_id,
    data{...}, channels:[push,sms,email], priority, send_at? }
  -> 202 {notification_id}

GET  /v1/notifications/{id}/status -> {per_channel: {state, attempts, ts}}
PUT  /v1/users/{id}/preferences    {channel_optin, quiet_hours, frequency_cap}
POST /v1/webhooks/gateway          {provider delivery receipts}   // inbound DSN/callbacks
```
- `idempotency_key` is mandatory for transactional sends — the dedup contract.

## 4. High-level design
```
 Services ─▶ Notification API ─▶ [validate, dedup, preferences]
                                       │ enqueue
                                       ▼
                              ┌──────────────────┐
                              │  Message Queue   │  (Kafka, per-channel topics
                              │  push|sms|email  │   + priority lanes)
                              └────────┬─────────┘
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
        ┌───────────┐            ┌───────────┐            ┌───────────┐
        │ Push      │            │ SMS       │            │ Email     │
        │ workers   │            │ workers   │            │ workers   │
        └─────┬─────┘            └─────┬─────┘            └─────┬─────┘
              ▼                        ▼                        ▼
        APNs / FCM               Twilio / SNS            SES / SendGrid
              │                        │                        │
              └────────── delivery receipts (webhooks) ─────────┘
                                       ▼
                        Status store + Retry/DLQ + Analytics
        Side stores: Preferences DB | Template svc | Dedup cache (Redis)
```
- **Notification API:** validates, resolves recipients (segment → users), checks preferences/rate limits, dedups, enqueues.
- **Queue (Kafka):** decouples ingestion spikes from delivery; per-channel topics so a slow channel can't block others.
- **Channel workers:** render template, call the channel gateway, handle provider-specific errors/retries.
- **Gateways:** APNs/FCM/Twilio/SES — external, rate-limited, sometimes down.
- **Status store / DLQ:** tracks attempts/state; failed messages route to retry or dead-letter.
- **Preferences/Template/Dedup:** supporting services.

## 5. Data model & storage choice
- **Preferences:** RDBMS (Postgres) — `user_prefs(user_id, channel, opted_in, quiet_hours, freq_cap)`. Relational, low write rate, needs consistency for opt-out compliance. Cached in Redis.
- **Notification status:** wide-column / time-series (Cassandra) keyed by `notification_id`, columns per channel attempt. **Why Cassandra:** high write throughput (every attempt + receipt writes), TTL support, no need for joins. 
- **Dedup / idempotency:** **Redis** `SETNX idem:{key}` with 24h TTL — fast, ephemeral, exactly the dedup window.
- **Templates:** versioned store (DB or object storage) + a render service.
- **Queue:** **Kafka** — durable, replayable, partitioned per channel; partition key = user_id to preserve per-user ordering and even spread.

## 6. Deep dives

### 6.1 Fanout
- Two stages. **Event fanout:** a campaign/segment expands to N users — done asynchronously by a fanout worker reading the segment from the user DB and emitting one message per (user, channel) into Kafka. **Channel fanout:** one logical notification → multiple channel messages, each handled independently so email failing doesn't block push.
- For huge segments, page through users and produce in batches; never hold 10M recipients in one request.

### 6.2 Retries & idempotency
- **At-least-once + idempotency = effectively-once.** Each message carries `idempotency_key` (or derived `notification_id`). Before sending, the worker checks Redis `SETNX`; if the key already marked `sent`, it skips. This protects against queue redelivery and worker crashes after send-before-ack.
- **Retries:** transient gateway errors (5xx, 429, timeouts) → exponential backoff with jitter, capped attempts, then **DLQ**. Permanent errors (invalid number, unsubscribed, bad token) → no retry, mark failed, possibly prune the token/contact. Distinguish via provider error codes.
- **Delivery receipts:** gateways confirm async via webhooks (APNs feedback, Twilio status callbacks, SES SNS notifications). These update the status store and feed bounce handling (purge dead device tokens / hard-bounced emails).

### 6.3 Rate limiting & frequency capping
- **Provider-side:** each gateway has QPS limits; a token-bucket per provider/account throttles workers so we don't get throttled or blocked. Backpressure flows to the queue (consumer lag), not to the user.
- **User-side:** frequency cap (e.g. max 3 marketing/day) + quiet hours per timezone, enforced at enqueue time using the preferences cache. Prevents notification spam and unsubscribes.

### 6.4 User preferences & opt-out
- Checked at ingestion (cheap reject) and re-checked at send (fresh opt-out). Unsubscribe links and STOP keywords flow back via webhooks → update preferences immediately. Honoring opt-out is a hard compliance requirement (CAN-SPAM/TCPA), so it gates every send.

### 6.5 Dedup
- Beyond idempotency keys: collapse duplicate logical notifications (same user + template + content within a window) using a content hash in the dedup cache. Stops two services from independently firing the same OTP/alert.

### 6.6 Priority lanes
- Transactional (OTP) and bulk (campaign) share infra but not queues. Separate Kafka topics / worker pools so a 10M campaign can't delay an OTP. OTP path is kept short and synchronous-ish; bulk tolerates buffering.

## 7. Bottlenecks & scaling
- **Third-party gateway is the limiter** (QPS caps, outages). Fix: token-bucket throttling, multiple providers with failover (e.g. Twilio → SNS), buffer in Kafka and drain when healthy. Never drop — queue and retry.
- **Campaign burst** overwhelms workers → autoscale workers on consumer lag; isolate bulk topic from transactional.
- **Hot partition** (a celebrity/segment) → partition by user_id; pre-shard large segments.
- **Status-write amplification** (every attempt + receipt) → Cassandra with TTL; batch writes; sample analytics.
- **Dedup cache loss** → Redis is best-effort; back critical idempotency with a durable check in the status store for transactional sends.

## 8. Tradeoffs / talking points
- At-least-once + idempotency key beats trying to build exactly-once delivery (impossible across external gateways) — we make sends idempotent instead.
- Per-channel queues/topics isolate failures: a degraded SMS provider must not stall push/email.
- Separate priority lanes: correctness of OTP latency matters more than fairness with bulk.
- Push throttling/backpressure into the queue rather than failing user requests — gateways are the scarce resource.
- Opt-out and frequency caps are enforced twice (ingest + send) — compliance over efficiency.
- Provider failover adds complexity but is the only defense against single-gateway outages for transactional traffic.
- Delivery is async and eventually-consistent; the API returns 202 + a status endpoint rather than blocking on the gateway.
