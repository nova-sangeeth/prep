# Design a Web Crawler

## 1. Requirements
- **Functional:** Given seed URLs, download pages, extract links, recursively crawl. Respect `robots.txt` and politeness. Deduplicate URLs and content. Re-crawl for freshness. Output parsed pages to a downstream store (for a search index).
- **Non-functional:**
  - **Scale:** crawl ~1B pages/month; capable of scaling to tens of billions in the corpus. Avg page ~500 KB-1 MB.
  - **Latency:** throughput-oriented, not latency-sensitive — maximize pages/sec, not per-page speed.
  - **Politeness:** never hammer one host; obey crawl-delay; identify with a User-Agent.
  - **Availability/robustness:** survive crashes mid-crawl (resumable frontier); tolerate malformed HTML, slow servers, traps.
  - **Extensibility:** pluggable for HTML now, later images/video/other content types.

## 2. Back-of-envelope estimates
- **Target:** 1B pages / 30 days ≈ **~400 pages/s** sustained (provision ~2x for bursts ≈ 800/s).
- **Download bandwidth:** 400 pages/s × 700 KB ≈ **280 MB/s ≈ 2.24 Gbps** ingress sustained.
- **Storage (raw HTML, compressed ~5:1):** 1B × 700 KB / 5 ≈ **140 TB/month** of compressed pages → object storage; metadata far smaller.
- **URL frontier size:** pages average ~10 outlinks → frontier can balloon to 10B URLs. At ~100 bytes/URL that's ~1 TB just for pending URLs → frontier must be disk-backed, not in-memory.
- **Dedup set:** to track "seen" URLs for 10B URLs, a hash set is ~hundreds of GB. A **Bloom filter** at ~10 bits/element ≈ 12.5 GB → fits in memory. This is why we use a Bloom filter.

## 3. API / interfaces
```
Frontier.Enqueue(url, priority, host)        // add discovered URL
Frontier.Next(worker_id) -> url              // politeness-aware dequeue
Fetcher.Fetch(url) -> {status, headers, body, fetch_ts}
Parser.Extract(body, base_url) -> {links[], text, content_hash}
SeenURL.Test(url_hash) -> bool               // Bloom filter
SeenContent.Test(content_hash) -> bool       // dedup near-identical pages
Robots.Allowed(host, path, ua) -> bool
```

## 4. High-level design
```
  Seeds
    │
    ▼
┌───────────────┐   dequeue   ┌──────────┐   bytes   ┌────────────┐
│ URL Frontier  │────────────▶│ Fetchers │──────────▶│  DNS       │
│ (priority +   │             │ (workers)│           │  resolver  │
│  politeness   │◀────────────│          │           │  (cached)  │
│  queues, disk)│  new URLs   └────┬─────┘           └────────────┘
└───────────────┘                  │ raw HTML
        ▲                          ▼
        │                  ┌───────────────┐
        │   extracted URLs │ Parser /      │──▶ Content store (S3)
        │◀─────────────────│ link extractor│──▶ Indexer / pipeline
        │                  └───────┬───────┘
   ┌────┴────────┐                 │ content_hash
   │ URL-seen    │◀── url hash     ▼
   │ Bloom filter│         ┌───────────────┐
   └─────────────┘         │ Content-seen  │ (dedup)
   ┌─────────────┐         │ Bloom/Simhash │
   │ robots.txt  │         └───────────────┘
   │ cache       │
   └─────────────┘
```
- **URL Frontier:** the brain — decides what to crawl next, balancing priority (freshness/importance) and politeness (per-host rate).
- **Fetchers:** large pool of async workers downloading pages.
- **DNS resolver:** cached resolution (DNS is a hidden bottleneck).
- **Parser:** extracts links + text, computes content hash.
- **URL-seen Bloom filter:** rejects already-queued URLs.
- **Content-seen / Simhash:** drops duplicate / near-duplicate content.
- **robots cache:** per-host crawl rules.
- **Content store:** durable raw + parsed pages for downstream indexing.

## 5. Data model & storage choice
- **URL Frontier:** Mercator-style two-level queue.
  - **Front queues (priority):** N queues by priority; a router assigns each URL a priority (PageRank-ish importance, change frequency).
  - **Back queues (politeness):** M queues, each mapped to exactly one host at a time; a min-heap of `(next_fetch_time, back_queue_id)` enforces per-host crawl delay. A worker pulls the host whose delay has elapsed. Backed by **Kafka/disk-backed queues** so the frontier survives restarts. **Why not in-memory:** frontier reaches billions of URLs (~TB).
- **Seen-URL set:** **Bloom filter** in memory (~12.5 GB for 10B URLs, ~1% FP). False positives cause us to skip a few real URLs (acceptable); never false negatives that re-crawl. Backed by a sharded KV (RocksDB) for exact checks where it matters.
- **Pages:** object storage (S3/GCS), compressed; key = `content_hash` or `url_hash`. Metadata (url, fetch_ts, status, etag) in a wide-column store (Bigtable/Cassandra) keyed by reversed-domain URL for locality.
- **robots.txt cache:** KV keyed by host, with TTL.

## 6. Deep dives

### 6.1 URL Frontier (priority + politeness)
- Two concerns conflict: **priority** (crawl important/fresh pages first) and **politeness** (don't overload one host). Solved by the two-level front/back queue:
  1. URL → prioritizer → one of N front queues.
  2. Front → router → one of M back queues, where each back queue holds a single host's URLs.
  3. A heap of `next_available_time` per back queue gives workers the next polite host to hit.
- Politeness default: one connection per host + a `crawl-delay` (from robots.txt or a default like 1-2s). This means a few hugely-linked hosts can't dominate throughput — we need many hosts in flight concurrently.

### 6.2 Dedup — Bloom filter & content dedup
- **URL dedup:** before enqueue, test the URL hash against the Bloom filter. Probabilistic: ~1% chance we wrongly think a new URL is seen (we lose it — fine at scale); zero chance we re-crawl a seen one. Far cheaper than a 10B-entry exact set. Normalize URLs first (lowercase host, strip fragments, sort query params, resolve relative) so trivially-different URLs collapse.
- **Content dedup:** many URLs serve identical/near-identical content (mirrors, session IDs in URL, print pages). Compute a content hash for exact dups; **SimHash/MinHash** for near-duplicates → skip indexing duplicates. Saves storage and index pollution.

### 6.3 DNS as a bottleneck
- Each fetch needs DNS resolution; public resolvers rate-limit and add 10s-100s ms latency. Fix: a **local caching DNS resolver** with a large TTL-aware cache, plus async resolution so workers don't block. DNS is frequently the silent throughput cap in real crawlers.

### 6.4 Politeness & robots.txt
- Fetch and cache `robots.txt` per host (TTL ~24h). Honor `Disallow`, `Crawl-delay`, sitemaps. Always send a descriptive User-Agent and a contact. Respect `Retry-After` on 429/503. Back off exponentially on errors per host.

### 6.5 Crawler traps & freshness
- **Traps:** infinite calendars, faceted-search URL explosions, deep self-referential paths. Defenses: cap URL length and path depth, cap pages-per-domain, detect query-param explosion, detect low content-to-URL ratio, and maintain a denylist. Content-dedup also neutralizes many trap loops (same content → dropped).
- **Freshness:** recrawl frequency adaptive to observed change rate (news site hourly, static page monthly). Use `ETag`/`If-Modified-Since` to do cheap conditional GETs (304 = no re-download). Maintain a recrawl priority queue keyed by predicted change time.

### 6.6 Distributed crawling
- Shard by **host** (hash of domain → crawler node) so politeness state for a host lives on one node (no cross-node coordination for crawl-delay). Each node runs its own frontier slice, fetcher pool, and local Bloom filter shard. A coordinator handles seed distribution and rebalancing. URLs discovered for another node's host are routed to that node.

## 7. Bottlenecks & scaling
- **DNS** breaks first → local caching resolver + async.
- **Frontier size** (TB) → disk/Kafka-backed, not memory; shard by host across nodes.
- **Bloom filter memory** → shard the filter by URL-hash range across nodes; or scalable/partitioned Bloom filters as the set grows.
- **Politeness limits throughput** for popular hosts → maximize host-level concurrency (thousands of distinct hosts in flight) rather than per-host parallelism.
- **Storage** (140 TB/mo) → compress, dedup content, tier to cold storage.
- **Slow/hostile servers** → per-request timeouts, per-host circuit breakers so one bad host can't tie up workers.

## 8. Tradeoffs / talking points
- Bloom filter trades a small false-positive (lost URLs) for ~10x memory savings vs an exact set — correct call at 10B URLs.
- Shard by host, not by URL: keeps all politeness/robots state for a host local, avoiding distributed coordination on every fetch.
- Disk/Kafka-backed frontier trades raw speed for resumability and unbounded size — non-negotiable since the frontier outgrows RAM.
- Conditional GETs (ETag/304) trade a little metadata bookkeeping for huge bandwidth savings on recrawls.
- Politeness fundamentally caps single-host throughput — scale horizontally across hosts instead.
- SimHash near-dup detection costs CPU but protects the index and storage from mirror/trap explosions.
