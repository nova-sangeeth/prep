# Design a Photo-Sharing Service (Instagram)

## 1. Requirements
- **Functional:**
  - Upload a photo (+ caption); generate thumbnails/renditions.
  - View a user's profile grid and individual posts.
  - **Follow** other users; **news feed** of photos from followed accounts.
  - Likes/comments (counts).
- **Non-functional:**
  - **Scale:** ~500M DAU, read-heavy (~100:1 read:write), billions of photos stored.
  - **Latency:** feed load p99 < 200ms; image delivery fast via CDN.
  - **Availability:** high for reads (browsing is the core loop).
  - **Consistency:** eventual — a new post or like count appearing seconds late is fine.
  - **Durability:** uploaded photos must never be lost.

## 2. Back-of-envelope estimates
- **DAU ≈ 500M.** Uploads: ~100M photos/day ≈ **1,160 writes/s**, peak ~3k/s.
- **Reads:** at 100:1 → 10B/day ≈ **116k reads/s** (feed opens + grid + post views), peak ~300k/s.
- **Storage per photo:** original ~2-4 MB + renditions (thumbnail, feed-size, full) ~1 MB combined → assume ~5 MB total/photo. 100M/day × 5 MB ≈ **500 TB/day** of new media → object storage, petabytes/yr.
- **Metadata:** 100M rows/day × ~1 KB ≈ **100 GB/day** ≈ 36 TB/yr — small vs media; sharded DB + cache.
- **Feed:** store ~last few hundred post IDs per active user in cache. 500M DAU × 500 IDs × 16 B ≈ **~4 TB** in Redis (rebuildable cache).
- **Bandwidth:** image bytes dominate but are served from **CDN** (>90% hit). Origin serves cache-fill only.

## 3. API
```
POST /api/v1/photos:initUpload  { caption } -> { postId, uploadUrl (presigned) }
PUT  <presigned-url>             (client uploads original directly to blob)
POST /api/v1/photos/{id}:complete (triggers thumbnail/rendition jobs)

GET  /api/v1/feed               ?userId&cursor -> { posts[], nextCursor }
GET  /api/v1/users/{id}/photos  ?cursor       -> profile grid
POST /api/v1/follow             { followerId, followeeId }
POST /api/v1/photos/{id}/like
```

## 4. High-level design
```
 upload ==(presigned, direct)==> [Blob: originals]
                                      | event
                             +--------v--------+
                             | Image Processor | (thumbnails, renditions, EXIF strip)
                             +--------+--------+
                                      v
                             [Blob: renditions] --> [CDN edges] --> client
                                      |
                             +--------v--------+
 post -> LB -> Post Service -| Fanout Service  |-> [Feed Cache (Redis): per-user postId list]
                |            +-----------------+        (push for normal, pull for hot users)
                v
         [Metadata DB: posts, sharded by post_id]
         [Follow graph store]

 read -> LB -> Feed Service -> merge feed cache + pull hot users -> hydrate -> CDN img URLs
```
- **Post Service:** persists post metadata (source of truth), emits a "new post" event.
- **Image Processor:** generates thumbnail/feed/full renditions, strips EXIF; writes them to blob.
- **Blob + CDN:** stores image bytes; CDN serves them to users.
- **Fanout Service / Feed Cache:** pushes post IDs into followers' precomputed feeds (Redis).
- **Feed Service:** merges precomputed feed with pulled posts from high-follower accounts, hydrates, returns CDN URLs.

## 5. Data model & storage choice
```
posts (sharded by post_id; Snowflake = time-ordered)
  post_id PK, user_id, caption, image_keys{thumb,feed,full},
  created_at, like_count, comment_count

follows (graph, indexed both directions)
  follower_id, followee_id, created_at
  (followee_id -> followers) for fan-out ; (follower_id -> followees) for pull

home_feed (Redis, key = user_id) -> LIST of recent post_ids (capped)

media -> object storage (S3), keyed by post_id/rendition ; served via CDN
```
**Choices:**
- **Image bytes:** **object storage + CDN** — cheap, durable, infinitely scalable, never a DB.
- **Metadata:** sharded DB by `post_id` (Snowflake IDs give time-ordering for grids/feeds), fronted by cache. Read-heavy point/range lookups.
- **Feed:** **Redis** per-user post-ID lists — read on every app open, must be fast, rebuildable.
- **Counts (likes/comments):** separate write-optimized, eventually-consistent counters; hot and approximation-tolerant.

## 6. Deep dives

### Upload, storage & thumbnails
- Client uploads the **original directly to blob** via a presigned URL (keeps multi-MB transfers off app servers; resumable). On `complete`, the Image Processor generates a fixed ladder of **renditions** — thumbnail (grid), feed-size, full-screen — plus strips EXIF/PII and re-encodes (WebP/AVIF for size). Pre-generating renditions (vs. on-the-fly resize) trades storage for predictable, cache-friendly delivery; serve the right size per surface to cut bandwidth. All renditions land in blob and are fronted by the CDN; metadata stores only the keys.

### Feed (reusing the news-feed design)
- Same **fanout-on-write vs fanout-on-read** problem as Twitter:
  - **Push (fan-out on write):** at post time, insert the post ID into each follower's Redis feed → O(1) reads. Great for the latency-critical feed load.
  - **Pull (fan-out on read):** read-time merge of followees' recent posts → cheap writes, expensive reads.
  - **Hybrid:** push for normal users; for **high-follower accounts** (celebrities/brands), skip fan-out and **pull** their recent posts at read time, merging with the precomputed feed. Caps write amplification while keeping reads fast. This is the same hybrid as the Twitter feed — deliberately reused.
- Store **post IDs only** in feeds (not image data); **hydrate** metadata on read and return **CDN URLs** for images so the client fetches bytes from the edge, not from us.

### Follow graph
- Adjacency lists indexed **both directions** — followers (for fan-out) and followees (for pull). A user's profile grid is a simple range query on `posts` by `user_id` ordered by Snowflake ID. Counts (followers/following) maintained as denormalized, eventually-consistent counters.

### Counts & ranking
- Like/comment counts on a **separate async counter path** (events → aggregation) so a viral post's like storm never blocks the read DB. Feed ordering can be reverse-chron or a lightweight ranking over the merged candidate set (affinity, recency, engagement) computed at read time over a few hundred candidates.

## 7. Bottlenecks & scaling
- **First to break: image egress bandwidth** → CDN serves the vast majority of bytes; origin only fills caches. Pre-warm hot content.
- **Fan-out write storms** from high-follower accounts → hybrid push/pull threshold, exactly as in the feed design.
- **Feed cache hotspots/capacity** → shard Redis by user_id, cap list length, build feeds lazily only for active users (don't fan out to dormant accounts).
- **Hot post metadata** (a viral post hydrated millions of times) → cache hot rows; counts on the separate path.
- **Thumbnail/processing burst** at upload spikes → elastic, queue-driven worker pool.
- **Storage growth** → lifecycle-tier cold originals to cheaper storage; keep renditions hot.

## 8. Tradeoffs / talking points
- Architecture mirrors the Twitter news feed — the feed component is **deliberately reused** (push/pull hybrid, IDs-not-bodies, lazy build for active users).
- Object storage + CDN for images, DB for metadata only — never store blobs in the DB.
- Pre-generate a rendition ladder (storage cost) for predictable, cache-friendly, bandwidth-efficient delivery vs. on-the-fly resizing.
- Direct-to-blob presigned uploads keep large transfers off the app tier.
- Counts and ranking on async, eventually-consistent paths protect the read latency budget.
- Snowflake IDs give time-ordering for both the profile grid and feed merge for free.
