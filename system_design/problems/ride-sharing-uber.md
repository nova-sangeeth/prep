# Design a Ride-Sharing Service (Uber/Lyft)

## 1. Requirements
- **Functional:** Riders request a ride (pickup + destination); system matches the nearest available driver; both parties see live location; fare estimate + ETA; surge pricing; trip lifecycle (request → match → en-route → in-trip → complete → pay → rate); drivers go online/offline and stream GPS.
- **Non-functional:**
  - **Scale:** ~10M DAU, ~5M active drivers at peak, ~1M concurrent trips. Drivers emit location every ~4s.
  - **Latency:** match within ~2-5s; location update write p99 < 100ms; nearby-driver query < 200ms.
  - **Availability:** matching/trip path is critical (target 99.99%). Better to occasionally over-dispatch than to drop a request.
  - **Consistency:** trip state needs strong consistency (no double-assigning a driver). Location data tolerates eventual consistency (stale by seconds is fine).
  - **Durability:** completed trips + payments are durable & auditable; in-flight location pings are ephemeral.

## 2. Back-of-envelope estimates
- **Location writes:** 5M drivers / 4s = **1.25M writes/s** sustained. This is the dominant load — everything bends around it.
- **Match/request reads:** ~1M trips/day at peak factor → request QPS ~ a few thousand/s, but each match fans out to a geo-query over candidate drivers.
- **Location storage if persisted:** 1.25M/s × 40 bytes ≈ 50 MB/s ≈ 4.3 TB/day. → **Do NOT persist raw pings to durable storage.** Keep current location in memory (Redis), persist only trip polylines (sampled) for receipts/disputes.
- **Trip storage:** 1M trips/day × ~2 KB = 2 GB/day ≈ 730 GB/yr → trivial for a sharded SQL/NoSQL store; keep hot for ~90 days, archive to object storage.
- **Bandwidth:** location ingest ~50 MB/s in; matching fan-out reads dominate egress within the cluster.

## 3. API
```
POST /v1/drivers/location        {driver_id, lat, lng, heading, ts}      -> 202
POST /v1/rides                   {rider_id, pickup, dest, product}       -> {ride_id, eta, fare_estimate}
GET  /v1/rides/{id}              -> {state, driver_loc, eta}
POST /v1/rides/{id}/cancel       {by, reason}                            -> {state}
POST /v1/drivers/{id}/status     {online|offline}                        -> {ok}
// internal RPCs
Match.FindCandidates(geo_cell, radius, product) -> [driver_id...]
Pricing.Quote(pickup, dest, demand_supply)      -> {fare, surge_mult}
```
Location updates use a long-lived gRPC/WebSocket stream, not one HTTP call per ping, to amortize connection cost.

## 4. High-level design
```
                 ┌─────────────┐
 Rider app ──────▶  API GW /   │
 Driver app ─────▶  Edge (WS)  │
                 └──────┬──────┘
        location pings  │  ride requests
            ┌───────────┼─────────────┐
            ▼           ▼             ▼
   ┌────────────┐ ┌───────────┐ ┌────────────┐
   │ Location   │ │ Matching  │ │ Trip       │
   │ Ingest svc │ │ service   │ │ service    │
   └─────┬──────┘ └─────┬─────┘ └─────┬──────┘
         ▼              ▼             ▼
   ┌──────────┐   ┌──────────┐  ┌──────────┐
   │ Geo index│◀──│ Pricing/ │  │ Trip DB  │
   │ (Redis/  │   │ Surge svc│  │ (sharded │
   │  S2 map) │   └──────────┘  │  SQL)    │
   └──────────┘                 └──────────┘
         ▲                          │
   Kafka (loc stream) ──────────────┘  (events: trip state, payments)
```
- **Edge/WS gateway:** maintains millions of persistent connections; routes pings & pushes driver-location to the matched rider.
- **Location ingest:** consumes pings, updates in-memory geo index, drops stale.
- **Geo index:** spatial structure (S2/geohash) holding current driver positions per cell.
- **Matching service:** on request, queries candidate drivers near pickup cell, ranks, dispatches offer.
- **Trip service:** owns the trip state machine (source of truth, strongly consistent).
- **Pricing/Surge:** computes fare + surge from demand/supply per zone.
- **Kafka:** decouples ingest from consumers; feeds surge, analytics, ETA models.

## 5. Data model & storage choice
- **Current driver location (hot):** Redis. Key = `cell:{s2_cell_id}` → sorted set / hash of `driver_id → {lat,lng,ts,heading}`. TTL ~10s so a driver that stops pinging falls out of dispatch automatically. **Why Redis:** 1.25M writes/s with sub-ms latency; data is ephemeral so no durability needed; in-memory is mandatory at this write rate.
- **Trips:** sharded relational store (CockroachDB / Spanner / sharded MySQL) keyed by `trip_id`, sharded by `city_id` or `trip_id`. **Why SQL:** trip state machine needs ACID transactions (assign driver ↔ mark driver busy must be atomic) and clean state transitions; volume is small enough that a partitioned SQL store handles it. `trips(id, rider_id, driver_id, state, pickup, dest, surge, fare, started_at, ended_at)`.
- **Driver/rider profile:** standard RDBMS / KV; cached.
- **Trip polylines & receipts:** object storage (S3) + metadata row; sampled GPS, not raw.

## 6. Deep dives

### 6.1 Geospatial indexing — geohash vs quadtree vs S2
The core problem: "find available drivers within radius R of point P" at high write + read rate.
- **Geohash:** encode lat/lng into a base-32 string; shared prefix ⇒ spatial proximity. Query = compute pickup geohash prefix (e.g. 6 chars ≈ 1.2 km cell) + its 8 neighbors, scan drivers in those buckets. Simple, maps cleanly to Redis keys. Downside: cell size jumps in discrete steps; boundary drivers need neighbor scan; cells distort with latitude.
- **Quadtree:** in-memory tree, recursively subdivides dense regions → adaptive resolution (dense downtown vs sparse suburb). Great query performance but rebalancing/rebuild is expensive under 1.25M writes/s, and it's harder to shard across nodes.
- **S2 (Google):** projects sphere onto cube faces → Hilbert curve → 64-bit cell IDs at 30 levels. Like geohash but with better-shaped cells, easy parent/child math, and `S2Cap`/region covering for radius queries. **Choice: S2 (or geohash if simplicity wins).** Adaptive precision via cell level, near-uniform cell areas, integer keys that shard well. Drivers indexed by leaf cell; query covers the pickup radius with a set of cells and scans only those Redis buckets.
- Hot-cell handling: pin popular city cells to dedicated shards; use cell level to keep ~hundreds of drivers per bucket.

### 6.2 Location updates at scale
- 1.25M writes/s would melt a durable DB. Path: app → WS gateway → Kafka (partitioned by `city`/`s2_parent`) → ingest workers → Redis upsert with TTL. Kafka absorbs bursts and gives replay.
- **Reduce write amplification:** only update the index when a driver crosses a cell boundary or every Nth ping; interpolate position client-side between pings. This cuts index churn dramatically.
- Riders in an active trip get the driver's location pushed directly via the gateway (no DB round trip).

### 6.3 Matching
- On request: resolve pickup cell → S2-cover the search radius → pull candidate drivers from Redis (filtered by product type, online, not on a trip) → rank by ETA (road-network ETA, not straight-line) and acceptance probability → send offer to top driver with a timeout (~15s). On decline/timeout, move to next. Expand radius if no takers.
- **Atomic assignment:** matching reserves a driver via a conditional transaction in the Trip DB / a Redis lock (`SETNX driver:{id}:lock`) to prevent two riders grabbing one driver. The trip state machine is the consistency boundary.
- Batched matching (compute a global assignment over a window of requests+drivers) reduces total wait and avoids greedy thrash in dense areas.

### 6.4 Surge pricing
- Per geo-zone, continuously compute `demand/supply` (open requests vs available drivers) over a sliding window from the Kafka stream. Multiplier from a lookup curve, smoothed to avoid oscillation, capped, and held briefly so a quoted price doesn't change mid-confirm. Surge both rations demand and pulls drivers toward hot zones.

### 6.5 ETA
- Straight-line distance is wrong (rivers, one-ways). Use a road-network engine (contraction hierarchies / precomputed graph) with live traffic from historical + current trip speeds. Cache ETAs at cell-pair granularity; refine with ML on time-of-day/weather.

## 7. Bottlenecks & scaling
- **Breaks first: the location write path.** Fix: keep it entirely in memory (Redis), partition by geo, batch/threshold updates, never write raw pings to durable storage.
- **Hot cells (downtown, airport, stadium at event end):** a single Redis shard for that cell saturates. Fix: shard the geo index by S2 cell so load spreads; split hot cells to finer levels; add read replicas for query fan-out.
- **WS connection fan-in:** millions of persistent connections. Fix: horizontally scale stateless gateways behind a connection-aware LB; consistent-hash drivers to gateway nodes.
- **Matching contention** in dense zones: batch-window assignment instead of per-request greedy locks.
- **Trip DB hot shards** per popular city: shard by city, sub-shard megacities; replicas for reads.
- **Multi-region:** pin a trip to the region of its city (data locality); cross-region only for the rare inter-city trip.

## 8. Tradeoffs / talking points
- Ephemeral-in-Redis vs durable location: we trade durability of pings for the only feasible write throughput — pings are worthless seconds later anyway.
- S2/geohash (shardable, integer keys) over quadtree (better adaptivity but rebuild cost & sharding pain) at this write rate.
- Strong consistency only where it pays: trip state & driver assignment; everything spatial is eventual.
- Threshold/boundary-only index updates trade location precision for a 5-10x write reduction.
- Push driver location to riders via the gateway instead of polling — saves a massive read load on the index.
- Surge is a control loop: must smooth and cap or it oscillates and angers users.
- Batched matching lowers wait time and avoids lock thrash, at the cost of a small added latency window.
