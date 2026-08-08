# Design URL Shortener (TinyURL)

## 1. Requirements
- **Functional:**
  - `shorten(longUrl, [customAlias], [ttl]) -> shortUrl` — generate a short key for a long URL.
  - `GET /{key}` — redirect to the original URL.
  - Optional custom aliases (vanity URLs), optional expiration.
  - Per-link analytics: click count, referrer, geo, device.
- **Non-functional:**
  - **Scale:** read-heavy, ~100:1 read:write. Billions of stored URLs over years.
  - **Latency:** redirect p99 < 50ms (it's on the user's critical path before they reach the destination).
  - **Availability:** 99.99% for reads — a dead shortener breaks every embedded link. Writes can tolerate slightly lower.
  - **Consistency:** redirects can be eventually consistent (a freshly created link being unavailable for a few ms is fine); key uniqueness must be strongly enforced.
  - **Durability:** never lose a mapping — a lost key permanently breaks public links.

## 2. Back-of-envelope estimates
- Assume **100M new URLs/day** (write).
  - Writes: 100M / 86400 ≈ **1,160 writes/s** (peak ~2x → ~2.3k/s).
  - Reads at 100:1 → 10B/day → **~116k reads/s** (peak ~250k/s).
- **Key space:** base62, length 7 → 62^7 ≈ 3.5 × 10^12 ≈ 3.5 trillion keys. At 100M/day that's ~96 years. Length 7 is the sweet spot.
- **Storage:** per row ≈ key(7) + longURL(~500 avg) + metadata(~100) ≈ ~600 bytes. 100M/day × 365 ≈ 36.5B rows/yr × 600B ≈ **~22 TB/yr** (before replication/compression).
- **Bandwidth:** redirect response is tiny (just a 301 + Location header, ~500B). 250k/s × 500B ≈ **125 MB/s** egress for redirects. Dominated by request volume, not payload.
- **Cache:** 20% of links drive 80% of traffic. Hot set ≈ a few hundred GB of mappings → fits comfortably across a Redis cluster, giving very high hit rates.

## 3. API
```
POST /api/v1/urls
  body: { longUrl, customAlias?, ttlSeconds?, userId }
  -> 201 { shortUrl, key, expiresAt }

GET /{key}
  -> 301/302 Location: <longUrl>   (or 404 if missing/expired)

GET /api/v1/urls/{key}/stats
  -> 200 { clicks, uniqueVisitors, topReferrers[], byCountry{} }

DELETE /api/v1/urls/{key}   (auth required)
```

## 4. High-level design
```
            +-----------+
 client --> |  CDN/edge | (cache 301s for popular keys)
            +-----+-----+
                  |
            +-----v------+        +------------------+
            | API / LB   | -----> | Key Gen Service  |--> [Counter / Zookeeper range alloc]
            +-----+------+        +------------------+
                  |
        +---------+----------+
        |                    |
   +----v----+          +----v-----+
   |  Redis  |  miss    |  Datastore (KV/NoSQL)  |
   |  cache  +--------->|  key -> longUrl row     |
   +---------+          +-------------------------+
                  |
            +-----v------+   (async, fire-and-forget)
            | Analytics  |--> Kafka --> stream proc --> OLAP store
            +------------+
```
- **CDN/edge:** caches redirect responses for the hottest keys; absorbs most read traffic.
- **API/LB:** validates, routes; stateless and horizontally scalable.
- **Key Gen Service:** produces unique short keys (see deep dive).
- **Redis cache:** read-through cache of key→longUrl, the primary defense for 116k+ reads/s.
- **Datastore:** durable source of truth (NoSQL KV — key is the partition key).
- **Analytics pipeline:** click events pushed to Kafka asynchronously; never on the redirect critical path.

## 5. Data model & storage choice
```
urls (partition key = key)
  key         CHAR(7)   PK
  long_url    TEXT
  user_id     UUID
  created_at  TIMESTAMP
  expires_at  TIMESTAMP NULL
  -- analytics kept separate, not here

clicks (append-only event log, partitioned by key+day)
  key, ts, referrer, country, device, ip_hash
```
**Choice: NoSQL key-value store (DynamoDB / Cassandra) over a relational DB.**
Why: the access pattern is a pure point-lookup by primary key — no joins, no range scans, no relational integrity needs. KV stores give O(1) partition-key reads, trivial horizontal sharding by key, and predictable latency at scale. A single relational table would need manual sharding and gives us nothing in return. Analytics goes to a separate column-oriented/OLAP store because its access pattern (aggregations, scans) is the opposite of the redirect path.

## 6. Deep dives

### Key generation: counter+base62 vs hashing
- **Hash (MD5/SHA of longURL, take first 7 chars):**
  - Pros: stateless, dedupes identical URLs naturally.
  - Cons: **collisions** — 7 chars from a 128-bit hash will collide; every write needs a read-check-retry, adding latency and a race. Also leaks nothing useful and isn't shorter.
- **Counter + base62 (chosen):**
  - Maintain a global monotonic counter; encode the integer in base62 → guaranteed-unique, no collision check.
  - **Distributed counter problem:** a single counter is a bottleneck/SPOT. Fix: use a **range allocator** — each app server requests a block of IDs (e.g. 1000) from a central coordinator (Zookeeper / a DB sequence / a Redis `INCRBY`). Servers hand out keys locally from their block; refill when exhausted. This eliminates per-write coordination.
  - **Predictability concern:** sequential counters make keys guessable/enumerable. Mitigate by base62-encoding a scrambled/obfuscated counter (e.g. multiply by a large coprime mod 62^7, or interleave bits) so keys look random but stay unique.
- **Custom aliases:** stored in the same table; on creation do a conditional write (`PUT IF NOT EXISTS`) to enforce uniqueness atomically and reject if taken.

### Redirect path & caching
- **Read-through cache:** check Redis → on miss read datastore, populate cache with a TTL. With 80/20 skew, hit rate is very high, so the datastore sees a small fraction of 116k/s.
- **301 vs 302:**
  - **301 (Permanent):** browsers and intermediate caches cache the mapping → subsequent clicks skip our servers entirely. Great for load reduction, **bad for analytics** (we never see repeat clicks) and bad if the link must change/expire.
  - **302 (Found/Temporary):** every click hits us → full analytics and the ability to change/expire the target, at the cost of more traffic.
  - **Decision:** default to **302** when analytics or mutability matter (most product cases); use 301 only for static, immutable links where load matters more than tracking. Many real services choose 302 precisely so they can count clicks.

### Analytics
- Redirect handler emits a click event **asynchronously** (write to Kafka, don't block the 302). Stream processor aggregates into per-link counters and dimensional rollups (referrer/geo/device) in an OLAP store. Exact-but-eventual counts; for very hot links, approximate counters (HLL for unique visitors) keep cardinality cheap.

## 7. Bottlenecks & scaling
- **First to break: the central counter** under write growth. Fix already baked in — block/range allocation so the coordinator is hit once per 1000 keys, not per write.
- **Redis hot keys:** a viral link can hammer a single cache shard. Fix: rely on CDN/edge caching of the 301/302 for the hottest keys, and/or replicate hot keys across cache nodes.
- **Datastore hot partitions:** key is high-cardinality and random-ish, so writes spread evenly; reads are cache-shielded. Add read replicas if cache misses spike.
- **Analytics write amplification:** never let it touch the redirect path — Kafka buffers bursts; backpressure degrades analytics, not redirects.
- **Cleanup of expired links:** background sweeper / TTL on the row; lazily 404 on read if `expires_at` passed.

## 8. Tradeoffs / talking points
- Counter+base62 beats hashing: no collision checks, guaranteed-unique, but needs a distributed ID strategy (range allocation) and obfuscation to avoid enumeration.
- 301 saves load but kills analytics and mutability; 302 is the safer default — state this tradeoff explicitly.
- Read-heavy system → cache + CDN do the heavy lifting; the DB is almost an afterthought on the read path.
- KV/NoSQL is the right call because the workload is point-lookups; resist the urge to reach for SQL.
- Keep analytics fully async — durability of the click event is less important than redirect latency/availability.
- 7-char base62 gives ~95 years of runway at 100M/day; document the length math so growth doesn't surprise you.
