# System Design

Interview-prep notes for a mid/senior engineer: building-block concepts, classic design questions, and a framework for attacking the interview.

Start with **[framework.md](framework.md)** — how to drive a 45-minute system-design round end to end.

## Concepts — building blocks

Read roughly top-to-bottom; fundamentals first.

| # | Topic | Notes |
|---|---|---|
| 1 | Scalability Basics | [`scalability-basics.md`](concepts/scalability-basics.md) |
| 2 | Back-of-the-Envelope Estimation | [`back-of-envelope-estimation.md`](concepts/back-of-envelope-estimation.md) |
| 3 | Load Balancing | [`load-balancing.md`](concepts/load-balancing.md) |
| 4 | Caching | [`caching.md`](concepts/caching.md) |
| 5 | Content Delivery Networks (CDN) | [`cdn.md`](concepts/cdn.md) |
| 6 | SQL vs NoSQL | [`sql-vs-nosql.md`](concepts/sql-vs-nosql.md) |
| 7 | Database Indexing | [`database-indexing.md`](concepts/database-indexing.md) |
| 8 | Sharding & Partitioning | [`sharding-partitioning.md`](concepts/sharding-partitioning.md) |
| 9 | Replication | [`replication.md`](concepts/replication.md) |
| 10 | CAP Theorem (and PACELC) | [`cap-theorem.md`](concepts/cap-theorem.md) |
| 11 | Consistency Models | [`consistency-models.md`](concepts/consistency-models.md) |
| 12 | Consistent Hashing | [`consistent-hashing.md`](concepts/consistent-hashing.md) |
| 13 | Message Queues & Streaming | [`message-queues.md`](concepts/message-queues.md) |
| 14 | Rate Limiting | [`rate-limiting.md`](concepts/rate-limiting.md) |
| 15 | API Styles: REST vs gRPC vs GraphQL | [`api-rest-vs-grpc.md`](concepts/api-rest-vs-grpc.md) |
| 16 | Bloom Filters | [`bloom-filters.md`](concepts/bloom-filters.md) |

## Problems — design questions

| # | Problem | Notes |
|---|---|---|
| 1 | Design a Chat System (WhatsApp / Messenger) | [`chat-system.md`](problems/chat-system.md) |
| 2 | Design a Distributed Key-Value Store (Dynamo-style) | [`distributed-key-value-store.md`](problems/distributed-key-value-store.md) |
| 3 | Design a Notification System | [`notification-system.md`](problems/notification-system.md) |
| 4 | Design a Photo-Sharing Service (Instagram) | [`photo-sharing-instagram.md`](problems/photo-sharing-instagram.md) |
| 5 | Design a Distributed Rate Limiter | [`rate-limiter.md`](problems/rate-limiter.md) |
| 6 | Design a Ride-Sharing Service (Uber/Lyft) | [`ride-sharing-uber.md`](problems/ride-sharing-uber.md) |
| 7 | Design Twitter News Feed (Timeline) | [`twitter-news-feed.md`](problems/twitter-news-feed.md) |
| 8 | Design a Typeahead / Search Autocomplete | [`typeahead-autocomplete.md`](problems/typeahead-autocomplete.md) |
| 9 | Design a Distributed Unique ID Generator | [`unique-id-generator.md`](problems/unique-id-generator.md) |
| 10 | Design URL Shortener (TinyURL) | [`url-shortener.md`](problems/url-shortener.md) |
| 11 | Design a Video Streaming Service (YouTube / Netflix) | [`video-streaming.md`](problems/video-streaming.md) |
| 12 | Design a Web Crawler | [`web-crawler.md`](problems/web-crawler.md) |

## How to use

1. Read `framework.md` first — internalize the step sequence.
2. Work the **concepts** until each soundbite is yours.
3. For each **problem**: cover the file, design it yourself on paper (requirements → estimates → API → high-level → deep dives), then compare.
4. Cross-links are intentional — e.g. Instagram reuses the Twitter feed's push/pull fanout; the KV-store leans on consistent-hashing + quorums.

