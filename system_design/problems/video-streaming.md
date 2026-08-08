# Design a Video Streaming Service (YouTube / Netflix)

## 1. Requirements
- **Functional:**
  - Upload video; transcode into multiple resolutions/bitrates.
  - Stream playback with **adaptive bitrate** (ABR) over HLS/DASH.
  - Browse/search; video metadata (title, channel, description).
  - View counts, likes/comments; recommendations.
- **Non-functional:**
  - **Scale:** billions of views/day, hundreds of hours uploaded per minute, petabytes of storage.
  - **Latency:** playback **startup < 1-2s**, near-zero rebuffering; uploads/transcodes can take minutes (async).
  - **Availability:** very high for playback; the watch path is the product.
  - **Consistency:** eventual is fine (a new video, an updated view count being slightly stale is acceptable).
  - **Durability:** uploaded masters must never be lost.

## 2. Back-of-envelope estimates
- **DAU ≈ 500M**, ~5 videos each → **2.5B views/day** ≈ 29k starts/s, peak ~75k/s. Concurrent streams in the millions.
- **Uploads:** ~500 hours/min → 720k hours/day. Raw masters huge; even post-transcode, store ~multiple renditions per video.
- **Storage:** a 1-hour 1080p video ≈ ~1-2 GB per rendition; ×~5 renditions (240p…4K) ≈ ~5-10 GB/video. 720k hours/day × ~5 GB ≈ **multiple PB/day** of new encoded content → object storage at exabyte scale over time, tiered by popularity.
- **Bandwidth (the dominant cost):** average stream ~3 Mbps. A few million concurrent streams × 3 Mbps ≈ **terabits/s** egress → impossible without a CDN; origin would melt. **>90% of bytes must be served from CDN edges.**
- **Metadata:** billions of video rows × ~few KB ≈ TBs — small relative to the media; trivially handled by a sharded DB + cache.

## 3. API
```
POST /api/v1/videos:initUpload   { title, sizeBytes } -> { videoId, uploadUrls[] (multipart/presigned) }
PUT  <presigned-part-url>         (client uploads chunks directly to blob store)
POST /api/v1/videos/{id}:complete (triggers transcoding pipeline)

GET  /api/v1/videos/{id}          -> metadata + manifest URL (.m3u8 / .mpd)
GET  <cdn>/{id}/master.m3u8       -> HLS manifest (variant playlists)
POST /api/v1/videos/{id}/view     (fire-and-forget view event)
GET  /api/v1/recommendations?userId
```

## 4. High-level design
```
 upload ==(presigned, direct)==> [Blob: raw masters]
                                       | event
                              +--------v---------+
                              | Transcoding      |  (DAG of jobs, by chunk + rendition)
                              | Pipeline (queue) |
                              +--------+---------+
                                       v
                              [Blob: HLS/DASH segments + manifests] --> [CDN edges]
                                                                            ^
 watch -> LB -> Metadata Svc -> (DB + cache) -> returns manifest URL ------>|  client
                                                                            (player fetches
                                                                             segments from CDN)
 view events -> Kafka -> stream aggregation -> view-count store
```
- **Upload service:** issues presigned multipart URLs; client uploads **directly to blob storage** (bypassing app servers).
- **Transcoding pipeline:** splits the master into chunks, encodes each into multiple renditions + packages into HLS/DASH segments; massively parallel, queue-driven.
- **Blob storage + CDN:** segments live in object storage; CDN edges cache and serve the actual bytes to viewers.
- **Metadata service:** serves video info + the manifest URL; the player then talks only to the CDN.
- **View/analytics pipeline:** async event stream → aggregated counts/recommendations.

## 5. Data model & storage choice
```
videos (sharded by video_id)
  video_id PK, channel_id, title, description, duration,
  status(uploading|transcoding|ready|failed), created_at,
  renditions[ {res, bitrate, manifestKey} ], thumbnail_key

channels / users
  channel_id, name, subscriber_count, ...

view_counts (separate, write-optimized)
  video_id -> count (approx, eventually consistent)

segments + manifests -> object storage (S3/GCS), keyed by video_id/rendition/segment
```
**Choices:**
- **Media (segments/masters):** **object storage** (S3-class) — cheap, durable (11 nines), virtually infinite, and CDN-friendly. Never a database.
- **Metadata:** sharded relational or wide-column DB by `video_id`, fronted by a cache. Small, read-heavy, point/lookup access.
- **View counts:** a **separate write-optimized, eventually-consistent counter** path (not the metadata DB) because they're hot, append-heavy, and tolerant of approximation.

## 6. Deep dives

### Upload & transcoding pipeline
- Client uploads the master **directly to blob** via presigned multipart URLs (resumable, parallel, never proxied through app servers). On `complete`, an event kicks off transcoding.
- **Transcoding as a DAG:** split the video into segments (e.g. by GOP boundaries), then for each segment × each target rendition (codec/resolution/bitrate), run an encode job. Segment-level parallelism lets thousands of workers crunch a long video in minutes. Output is packaged into **HLS (.m3u8) / DASH (.mpd)** with a master manifest listing variant streams. Failed segments retry independently. Status transitions `transcoding -> ready` flip the video's visibility.

### Adaptive Bitrate (ABR) + HLS/DASH
- Each rendition is chopped into short **segments (2-10s)**. The master manifest advertises the available bitrate ladder; the **player** measures throughput/buffer and switches renditions per segment → smooth playback as network conditions change, fast startup (begin at a low rendition, ramp up). ABR logic lives client-side; the server just serves segments + manifests statically — which is what makes pure CDN delivery possible.

### CDN strategy (the core of cost & latency)
- Segments are static, cacheable files → ideal for CDN. **Push** popular content proactively to edges; **pull** (cache-on-miss) the long tail. Geo-route viewers to the nearest edge. **Popularity tiering:** hot videos pinned at edges/SSD; cold archive in cheaper storage, pulled to origin on demand. This is what keeps origin bandwidth and cost sane — the origin serves cache-fill, not viewers.

### View counts & metadata at scale
- View events are fired **async** (fire-and-forget) → Kafka → aggregated; counts are approximate and eventually consistent (a viral video's exact count doesn't matter to the millisecond). Metadata reads are cache-shielded; a single popular video's metadata is read by millions, so cache hit rate is what matters.

### Recommendations (high level)
- **Two-stage:** candidate generation (collaborative filtering / embeddings / "watched together") narrows billions of videos to a few hundred, then a ranking model scores them per user using watch history, engagement, freshness. Precompute candidates offline; rank at request time. Out of scope to detail, but the candidate→rank funnel is the standard shape.

## 7. Bottlenecks & scaling
- **First to break: egress bandwidth.** No origin can serve terabits/s. Fix is foundational: CDN serves >90% of bytes; origin only fills caches.
- **Transcoding compute** spikes with upload bursts → elastic worker pool consuming a queue; prioritize by channel/popularity; spot/preemptible instances for cost.
- **Hot video thundering herd** at upload time (a premiere) → pre-warm/push to edges before release.
- **Metadata hot rows** → cache aggressively; counts on a separate path so they don't hammer the metadata DB.
- **Storage growth** is relentless → lifecycle policies tier cold content to cheaper/colder storage; drop rarely-watched renditions.
- **Long-tail cache misses** increase origin load → multi-tier CDN (regional shield caches) to collapse misses.

## 8. Tradeoffs / talking points
- The whole architecture is organized around making playback bytes **static and CDN-cacheable** — that's why ABR/HLS pushes adaptation to the client.
- Direct-to-blob uploads keep app servers out of the data path for huge files.
- Transcoding parallelized by segment turns hours of encoding into minutes at the cost of orchestration complexity.
- Object storage for media, DB only for metadata — never store video bytes in a database.
- View counts and recommendations live on async, eventually-consistent paths so they never threaten playback latency or availability.
- Popularity tiering (hot at edge, cold archived) is the lever that balances cost vs. latency at exabyte scale.
