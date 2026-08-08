# Design Twitter News Feed (Timeline)

## 1. Requirements
- **Functional:**
  - `postTweet(userId, content)` — publish a tweet to followers.
  - `getFeed(userId)` — return a ranked, paginated home timeline of tweets from followed accounts.
  - Follow/unfollow; user (profile) timeline.
  - Support media, retweets/replies (feed entries reference tweet IDs).
- **Non-functional:**
  - **Scale:** ~300M MAU, hundreds of millions of tweets/day, extreme fan-out skew (celebrities with 100M+ followers).
  - **Latency:** `getFeed` p99 < 200ms — it's the app's home screen. `postTweet` can be async (eventual visibility of seconds is fine).
  - **Availability:** high for reads; a missing-but-eventually-present tweet is acceptable.
  - **Consistency:** eventual. Timelines need not be globally ordered or instantly complete.

## 2. Back-of-envelope estimates
- **DAU ≈ 150M.** Avg user opens feed ~5×/day → **750M feed reads/day** ≈ 8.7k/s, peak ~25k/s (each read returns ~20 tweets, paginated).
- **Writes:** ~400M tweets/day ≈ **4.6k tweets/s**, peak ~12k/s.
- **Fan-out cost (write-time):** avg ~200 followers → 400M tweets × 200 = **80B timeline inserts/day** ≈ 925k inserts/s. This is the real workload, dominated by a few high-follower accounts.
- **Storage:**
  - Tweets: 400M/day × ~300 bytes (text+metadata, media stored separately) ≈ **120 GB/day** ≈ 44 TB/yr.
  - Precomputed timelines: store last ~800 tweet IDs per active user. 150M DAU × 800 × ~16 bytes ≈ **~2 TB**, kept in Redis. This is a cache, rebuildable from source.
- **Bandwidth:** 25k feed reads/s × 20 tweets × 300B ≈ **150 MB/s** of tweet payload (text); media served from CDN separately.

## 3. API
```
POST /api/v1/tweets            { userId, content, mediaIds[] } -> { tweetId }
GET  /api/v1/feed              ?userId&cursor&limit -> { tweets[], nextCursor }
POST /api/v1/follow            { followerId, followeeId }
DELETE /api/v1/follow          { followerId, followeeId }
GET  /api/v1/users/{id}/tweets ?cursor -> user (profile) timeline
```

## 4. High-level design
```
                         +-------------+
 post ----> LB ----> | Tweet Service | ----> [Tweet Store (sharded by tweetId)]
                         +------+------+
                                | publish event
                         +------v------+
                         |  Fanout     | --(per follower)--> [Timeline Cache (Redis)]
                         |  Service    |     skips celebrities (hybrid)
                         +-------------+
                                ^
 read ----> LB ----> | Feed Service |
                         +------+------+
                   merge: precomputed timeline (Redis)
                        + pull celebrity tweets (on read)
                        -> rank -> hydrate tweet bodies -> return
```
- **Tweet Service:** persists the tweet (source of truth), emits a "new tweet" event.
- **Fanout Service:** for normal users, pushes the tweet ID into each follower's precomputed timeline list in Redis (fan-out on write).
- **Timeline Cache (Redis):** per-user list of recent tweet IDs — the home timeline, ready to serve.
- **Feed Service:** on read, merges the precomputed list with freshly pulled tweets from followed celebrities, ranks, hydrates, paginates.

## 5. Data model & storage choice
```
tweets (sharded by tweet_id)
  tweet_id (Snowflake: time-ordered) PK, user_id, text, media_ids[], created_at, counts

follows (graph)
  follower_id, followee_id, created_at          -- indexed both directions
  (followee_id -> followers list) for fan-out
  (follower_id -> followees list) for pull

home_timeline (Redis, key = user_id)
  LIST/ZSET of recent tweet_ids (capped ~800)
```
**Choices:**
- **Tweets:** wide-column / KV store (Cassandra-style), sharded by `tweet_id`. Snowflake IDs are time-sortable so range queries by recency are cheap; write-heavy and append-only fits LSM stores.
- **Follow graph:** store adjacency lists in a horizontally-scalable store (or a dedicated graph DB for traversal-heavy features). Both directions are indexed — followers for fan-out, followees for pull.
- **Timelines:** **Redis** (in-memory lists/sorted sets). Timelines are read on every app open and must be sub-200ms; they're a rebuildable cache, so in-memory volatility is acceptable.

## 6. Deep dives

### Fan-out on write vs fan-out on read
- **Fan-out on write (push):** at post time, write the tweet ID into every follower's timeline. **Reads are O(1)** — just read your precomputed list → great for the latency-critical read path. **Cost:** write amplification proportional to follower count, and wasted work writing to inactive followers.
- **Fan-out on read (pull):** store nothing precomputed; at read time, query the latest tweets from everyone you follow and merge. **Writes are cheap**, but **reads are expensive** (fan-in across hundreds of followees) → bad for the hot read path.
- **Why not pure push:** a celebrity with 100M followers triggers 100M writes per tweet — a single post can take minutes to fully fan out and creates massive, spiky write load ("hot user problem").

### Hybrid (the real answer)
- **Push for normal users**, **pull for celebrities.** When building a user's feed:
  1. Read their precomputed timeline (tweets from the ~99.9% of accounts that are non-celebrities) from Redis.
  2. **Pull** recent tweets from the small set of celebrities they follow (those accounts are excluded from fan-out on write).
  3. Merge, rank, return.
- This caps write amplification (no 100M-write storms) while keeping reads fast (celebrity pull is a handful of accounts). The push/pull boundary is a tunable follower-count threshold.

### Feed ranking
- Two stages: **candidate generation** (the merged push+pull set, last few hundred tweets) → **ranking** (ML model scoring recency, affinity to author, engagement velocity, media type, predicted interaction). Reverse-chron is the fallback. Ranking runs at read time over the small candidate set, so it stays within the latency budget.

### Timeline storage & caching
- Store only **tweet IDs** in timelines, not bodies — keeps the per-user list tiny and avoids duplicating tweet text across millions of timelines. **Hydrate** bodies on read from the tweet store / a tweet-body cache. Cap each timeline (~800 entries); older pages fall back to pull. Only materialize timelines for **active** users (lazy-build for users who haven't logged in recently) to avoid wasting fan-out on dormant accounts.

## 7. Bottlenecks & scaling
- **First to break: fan-out write storms** from high-follower accounts. Fix: the hybrid threshold — never push for celebrities.
- **Redis timeline capacity/hotspots:** shard timeline cache by user_id; cap list length; evict dormant users' timelines and rebuild on demand.
- **Tweet store read hot spots:** a viral tweet is hydrated millions of times → cache hot tweet bodies in a dedicated layer/CDN.
- **Fan-out lag:** during spikes, fan-out is async via a queue; followers see tweets within seconds — acceptable eventual consistency.
- **Follow graph traversal at read** (pull side) for users following many celebrities → cache the celebrity tweet lists themselves so all their followers share one pull.
- **Reordering on unfollow:** don't rewrite timelines on unfollow; filter at read time or let entries age out.

## 8. Tradeoffs / talking points
- Push vs pull is a write-cost vs read-cost tradeoff; the read path is latency-critical, so we bias to push and patch its weakness (celebrities) with pull → hybrid.
- Store IDs, not bodies, in timelines: avoids enormous duplication, costs a hydration step on read.
- Eventual consistency is fine for a social feed; spend the consistency budget elsewhere.
- Only build timelines for active users — fan-out to dormant accounts is pure waste.
- Ranking happens over a small read-time candidate set, keeping the ML cost bounded within the latency budget.
- Snowflake IDs give time-ordering for free, simplifying recency queries and merge.
