# System-Design Interview Framework

> Drive the interview: clarify → estimate → API → high-level → data → deep-dive → bottlenecks → wrap. Talk while you draw.

A system-design interview is not a quiz with a right answer; it's a simulation of you as a senior engineer scoping an ambiguous problem under time pressure. The interviewer is your proxy for a PM, a teammate, and a load test. Your job is to drive — they should mostly listen, nudge, and probe.

## The step sequence

### 1. Clarify requirements & scope (functional + non-functional)
Never start drawing boxes. Pin down what you're building.
- **Functional**: the 2-4 core features. Explicitly cut the rest. "We'll support posting and reading the feed; I'll treat DMs as out of scope unless you want them."
- **Non-functional**: scale (DAU, QPS, data size), latency targets (p99), availability (how many 9s), consistency needs, read/write ratio, durability.
- **Constraints**: multi-region? mobile clients? cost ceiling? existing infra?
- Write the agreed scope in a corner of the board and reference it. This is the single highest-signal step — it shows you don't gold-plate.

### 2. Back-of-envelope estimates
Turn the scale into numbers that drive design decisions.
- QPS = DAU × actions/user/day ÷ 86,400. Apply a peak factor (×2-10).
- Storage = objects/day × size × retention. Bandwidth = QPS × payload.
- Read:write ratio decides whether you cache/replicate heavily (read-heavy) or shard writes (write-heavy).
- Memory: can the hot set / index fit in RAM? Decides caching strategy.
- State assumptions out loud; round aggressively. The point is order-of-magnitude, not arithmetic.

### 3. API design
Define the contract before internals — it forces clarity on the data flow.
- A handful of endpoints: `POST /tweets`, `GET /feed?cursor=...`. Note auth, pagination (cursor not offset), idempotency keys for writes.
- This is where you flush out the data the system actually moves.

### 4. High-level design
Draw the boxes: clients → LB → API/app servers (stateless) → caches → databases → async workers + queue → blob store/CDN.
- Show the request path for each core feature end-to-end.
- Keep app tier stateless so it scales horizontally; push state to data stores.
- Call out async vs sync paths (write to queue, fan-out later).

### 5. Data model
Schemas for the main entities, primary keys, indexes, and the access patterns they serve.
- Pick storage per workload (SQL for relational/transactional, KV for sessions, blob for media, wide-column for feeds/time-series).
- State the shard key and why. Show one hot query and how an index serves it.

### 6. Deep dives
The interviewer will steer you here; have 2-3 ready. Common targets:
- Feed generation: fan-out-on-write vs fan-out-on-read; hybrid for celebrities.
- Consistency & replication strategy; how failover works.
- Caching: what, where, invalidation, hot keys.
- Rate limiting, idempotency, dedup, ID generation (Snowflake).
- Go deep, not wide — pick the interesting/risky part and exhaust it.

### 7. Identify bottlenecks & scale
Pressure-test your own design before they do.
- Single points of failure → replicate/failover.
- Hot shards / hot keys → better key, consistent hashing, request coalescing.
- Thundering herd, cache stampede, retry storms → backoff, circuit breakers.
- Read amplification → CDN, read replicas. Write amplification → batching, LSM, queues.
- Mention monitoring, alerting, and graceful degradation.

### 8. Wrap-up
Summarize the design in 3-4 sentences, restate how it meets the NFRs, and name the top tradeoffs you'd revisit with more time/data. Leaves a senior impression.

## What interviewers actually evaluate
- **Structured thinking**: do you drive a method, or flail?
- **Scoping & prioritization**: do you build the right thing, defer the rest?
- **Tradeoff fluency**: every choice has a cost; can you name both sides?
- **Depth on demand**: can you go three layers down on one component?
- **Communication**: thinking out loud, reacting to hints, collaborating.
- **Quantitative sense**: estimates that inform decisions.

## Common mistakes
- Jumping to architecture before clarifying requirements.
- Estimating numbers you never use, or skipping estimation entirely.
- Designing for Google-scale when 1k QPS is the ask (over-engineering).
- Buzzword salad: "Kafka, Redis, Cassandra" with no justification.
- Going wide and shallow; never finishing a deep dive.
- Ignoring failure modes, monitoring, and the unhappy path.
- Defending the first idea instead of incorporating hints — hints are gifts.
- Silent thinking; the interviewer can't score what they can't hear.

## Time budget — 45 minutes
| Phase | Minutes |
|---|---|
| Clarify requirements & scope | 5-7 |
| Back-of-envelope estimates | 3-5 |
| API design | 2-3 |
| High-level design | 8-10 |
| Data model | 3-5 |
| Deep dives | 10-12 |
| Bottlenecks & scaling | 4-6 |
| Wrap-up | 2-3 |

Keep ~5 min of slack; interviewers interrupt and redirect. If short on time, protect the high-level design and one deep dive — those carry the most signal.
