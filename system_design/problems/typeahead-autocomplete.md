# Design a Typeahead / Search Autocomplete

## 1. Requirements
- **Functional:** As a user types a prefix, return the **top-k** (e.g. 5-10) most relevant completions, ranked primarily by popularity/frequency. Update suggestions as the corpus of queries evolves. Optionally personalize/localize.
- **Non-functional:**
  - **Scale:** ~10M DAU, each query = ~20 keystrokes × suggestion fetch → very read-heavy.
  - **Latency:** **the** defining requirement — p99 < ~100ms end-to-end (sub-50ms server-side); it must feel instant on every keystroke.
  - **Availability:** high (degrade gracefully to no-suggestions rather than error).
  - **Consistency:** eventual — a new trending term appearing minutes later is fine; freshness over strict correctness.
  - **Read:write ratio:** extremely read-heavy; suggestion data updated in batch.

## 2. Back-of-envelope estimates
- **Query QPS:** 10M DAU × ~10 searches/day × ~20 keystrokes = **2B keystrokes/day ≈ 23k req/s avg**, peak ~5x ≈ **115k req/s**. (Debouncing keystrokes cuts this materially.)
- **Read-heavy:** essentially 100% reads against the suggestion index; writes are the offline build (once per hour/day).
- **Corpus:** assume 100M distinct historical queries; avg 20 chars → ~2 GB raw terms. The **trie** with top-k cached per node is larger (precomputed lists) but still tens of GB → sharded across nodes / fits in memory.
- **Update volume:** aggregate ~5B raw query logs/day → MapReduce/stream job emits frequency counts → rebuild/patch trie. Heavy offline, light online.
- **Cache hit rate:** short prefixes (1-3 chars) are hammered → very high cache hit rate; most QPS served from cache/memory.

## 3. API
```
GET /v1/suggest?q={prefix}&limit=10&lang=en&region=US
   -> { suggestions: [ {text, score}, ... ] }       // sorted desc by score

// offline / control plane
BuildTrie(query_logs)        -> trie snapshot (versioned)
UpdateFrequencies(window)    -> aggregated counts feeding the next build
```
- Client debounces (~50-100ms) and cancels stale in-flight requests so only the latest prefix matters.

## 4. High-level design
```
   User types prefix
        │  (debounced)
        ▼
   ┌──────────┐    miss    ┌──────────────────┐
   │  CDN /   │───────────▶│  Suggest Service  │
   │  Edge    │◀───────────│ (trie lookup,     │
   │  cache   │  top-k     │  sharded by prefix)│
   └──────────┘            └─────────┬─────────┘
                                     ▼
                           ┌───────────────────┐
                           │ Trie store (in-mem │
                           │ + top-k per node), │
                           │ sharded            │
                           └─────────┬─────────┘
                                     ▲ snapshot load
   ── OFFLINE PIPELINE ──────────────┘
   Query logs ─▶ Kafka ─▶ Aggregator (MapReduce/Flink:
                          count, filter, rank) ─▶ Trie Builder
                          ─▶ versioned snapshot ─▶ hot-swap to serving
```
- **Edge/CDN cache:** absorbs the huge read volume on popular prefixes.
- **Suggest service:** resolves a prefix to its precomputed top-k; stateless, scales horizontally; sharded by prefix.
- **Trie store:** in-memory trie where each node caches the top-k completions of its prefix.
- **Offline pipeline:** aggregates raw query logs into ranked frequencies and (re)builds the trie snapshot, then hot-swaps it into serving.

## 5. Data model & storage choice
- **Serving structure:** a **trie** (prefix tree). Each node = one character; a terminal node marks a complete query with its frequency. Crucially, **cache the top-k completions directly at each node** so a lookup is O(prefix length) to the node + O(1) to read the precomputed list — no subtree traversal at query time. **Why a trie:** prefix queries are exactly what a trie answers in O(len), and precomputed top-k turns it into near-constant-time reads.
- **Source aggregation:** query logs in a data lake / Kafka; aggregated counts in a columnar store or just the MapReduce output.
- **Snapshot storage/distribution:** serialized trie shards in object storage, versioned, loaded into serving-node memory.
- **Why not a SQL `LIKE 'prefix%'`:** an index range scan + top-k sort per keystroke at 100k QPS with <50ms p99 is hopeless; the precomputed trie moves the ranking work offline.

## 6. Deep dives

### 6.1 Top-k per prefix — precompute vs realtime
- **Realtime:** on each request, find the prefix node, traverse its whole subtree, aggregate frequencies, sort top-k. Correct and fresh but **too slow** for short/popular prefixes (subtree can be enormous) at this QPS.
- **Precompute (chosen):** store the top-k list *at every trie node* during the offline build. Query = walk to the node, return its cached list. Reads become O(len). Tradeoff: more memory (k entries per node) and staleness until the next build, but it's the only way to hit the latency target.
- Hybrid: precompute for hot/short prefixes; allow realtime traversal for rare deep prefixes where subtrees are small.

### 6.2 Ranking by frequency (and beyond)
- Primary signal: historical query **frequency** (count over a window). Refinements: time-decay so trending terms rise and stale ones fade; recency weighting; personalization/localization (region, language) as separate or blended tries; spell-tolerance via edit-distance fallback. Ranking is computed offline so query-time stays cheap.

### 6.3 The update pipeline
- Raw query logs → Kafka → batch (MapReduce/Spark, e.g. hourly) or streaming (Flink) aggregation produces `(query, count)` over a sliding window, filtered for noise/PII/abuse and a minimum frequency threshold (prune the long tail).
- **Trie Builder** consumes the ranked counts and constructs a new trie with top-k per node. Output is a **versioned, immutable snapshot**.
- **Hot-swap deploy:** serving nodes load the new snapshot into memory beside the old one and atomically switch pointers — zero-downtime, no per-request rebuild. Because the trie is immutable at serving time, reads are lock-free.
- Frequency of rebuild trades freshness vs build cost (hourly is typical; trending topics may need a faster incremental path).

### 6.4 Caching
- Multi-layer: **client debounce** (don't fire on every keystroke) → **CDN/edge** for popular short prefixes → in-process LRU on suggest nodes. Short prefixes (1-3 chars) are a tiny set with massive traffic and near-100% hit rate, so caching offloads the vast majority of QPS before it reaches the trie.

### 6.5 Sharding the trie
- 100M queries → trie too big for one node and one node can't serve 100k QPS. **Shard by prefix range** (e.g. first 1-2 characters → shard): a router/consistent-hash sends `q` to the owning shard. Replicate each shard for read scale + availability.
- **Skew problem:** prefixes aren't uniform ('a', 's', 'th-' are hot; 'z', 'qx' are cold). Naive first-letter sharding overloads hot shards. Fix: shard by a **hash of a longer prefix** or **balance by historical load** (assign prefix ranges so each shard gets ~equal traffic), and replicate hot shards more.
- **Cross-shard subtlety:** sharding by the *first* character keeps every prefix's whole subtree on one shard, so a single-shard lookup answers any query — no scatter-gather. If you instead hashed the *full* query, completions for a prefix would scatter across shards and you'd need fan-out + merge per keystroke (bad). So shard granularity is chosen to keep each prefix's completions co-located.

### 6.6 Personalization & multi-tenant tries
- Pure popularity ignores the individual. Layer a small **per-user / per-session trie** (recent personal queries, history) merged at query time with the global top-k — personal hits boosted, then backfilled from global. Keep it small and in-cache so the merge stays O(k). Localized tries (per region/language) are separate snapshots selected by the request's `lang`/`region`, avoiding one giant blended index.

## 7. Bottlenecks & scaling
- **Hot short prefixes** ('a', 'th') → solved mostly by edge/CDN caching + extra replicas for those shards.
- **Latency tail** → keep the trie in memory, precompute top-k, debounce, and cache; never traverse subtrees at request time for hot prefixes.
- **Shard skew** → load-aware prefix partitioning + hash-based sharding, not naive first-letter.
- **Update cost / staleness** → batch builds with immutable hot-swap; incremental updates for trending terms.
- **Memory growth** (top-k at every node × shards × replicas) → prune low-frequency tail, cap trie depth, store compact top-k.

## 8. Tradeoffs / talking points
- Precompute top-k per node (memory + staleness) vs realtime traversal (fresh but too slow) — latency target forces precompute.
- Immutable, versioned trie snapshots + atomic hot-swap → lock-free reads and zero-downtime updates, at the cost of not being instantly fresh.
- Eventual consistency is fine here: a slightly stale suggestion list is invisible to users; latency is not.
- Shard by balanced/hashed prefix, not first letter — query distributions are heavily skewed.
- Push work offline (aggregation + ranking + build) so the online path is O(prefix length); the read path does almost no computation.
- Client-side debounce + edge cache eliminate most of the nominal QPS before it ever hits the service.
