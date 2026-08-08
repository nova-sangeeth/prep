# Back-of-the-Envelope Estimation

> Turn DAU into QPS, storage, and bandwidth with powers of 2 and a handful of latency numbers — get to the right order of magnitude fast.

## What it is & why it matters

Capacity estimation sizes a system before you design it: how many servers, how
much storage, what bandwidth, can it fit in memory/one machine. Interviewers want
to see **structured reasoning and correct orders of magnitude**, not precision.
Round aggressively, state assumptions out loud, and use the result to justify
architecture (sharding, caching, CDN).

## Powers of 2 & units

| Power | Value | Name | Bytes |
|---|---|---|---|
| 2^10 | ~1 thousand | KB | 1 KB |
| 2^20 | ~1 million | MB | 1 MB |
| 2^30 | ~1 billion | GB | 1 GB |
| 2^40 | ~1 trillion | TB | 1 TB |
| 2^50 | ~10^15 | PB | 1 PB |

Time: 1 day ≈ **86,400 s ≈ 10^5 s**. 1 month ≈ 2.6M s. ASCII char = 1 byte.

## Latency numbers every engineer should know

| Operation | ~Latency |
|---|---|
| L1 cache reference | 0.5 ns |
| Main memory (RAM) reference | 100 ns |
| Read 1 MB sequentially from RAM | 10 µs |
| SSD random read | 100 µs |
| Read 1 MB from SSD | 1 ms |
| Round trip within same datacenter | 0.5 ms |
| Disk (HDD) seek | 10 ms |
| Read 1 MB from disk | 20 ms |
| Round trip CA ↔ Netherlands | 150 ms |

Takeaways: **memory ≈ 100,000x faster than disk seek**; cross-region RTT dwarfs
everything → cache and stay in-region; sequential >> random I/O.

## How to estimate (recipe)

1. **QPS from DAU:** `QPS = DAU × actions/user/day / 86,400`. Then
   **peak ≈ 2–3x average**.
2. **Storage:** `items/day × bytes/item × retention (days)` — add replication
   (×3) and overhead/indexes.
3. **Bandwidth:** `QPS × payload size` (split read vs write).
4. **Memory (cache):** apply the **80/20 rule** — cache the hot 20% of daily data.

## Worked example — a Twitter-like feed

Assume **200M DAU**, each posts **2 tweets/day**, reads **100 tweets/day**, tweet
= **300 bytes** text (ignore media blobs, store those in object storage/CDN).

**Write QPS**
- Writes/day = 200M × 2 = 400M
- Avg write QPS = 400M / 10^5 ≈ **4,000 QPS**
- Peak ≈ 3x ≈ **12,000 QPS**

**Read QPS**
- Reads/day = 200M × 100 = 20B
- Avg read QPS = 20B / 10^5 = **200,000 QPS**; peak ≈ **600,000 QPS**
- Read:write ≈ **50:1** → read-heavy → cache + read replicas + fan-out, and a
  CDN for media.

**Storage (text)**
- Per day = 400M × 300 B = 1.2 × 10^11 B ≈ **120 GB/day**
- Per year ≈ 120 GB × 365 ≈ **44 TB/yr**; ×3 replication ≈ **130 TB/yr** → must
  shard.

**Bandwidth**
- Write in = 4,000 QPS × 300 B ≈ 1.2 MB/s (trivial)
- Read out = 200,000 QPS × 300 B ≈ **60 MB/s ≈ 480 Mbps** steady; peak ~1.4 Gbps
  → fronting with a CDN/cache is mandatory.

**Cache sizing (hot 20%)**
- 20% of 120 GB/day ≈ **24 GB** → fits in a few RAM nodes; cache the hot feed.

Conclusion: read-dominated → distributed cache + replicas, shard the write store
(~130 TB/yr), CDN for media, fan-out-on-write for feeds.

## When to use · pitfalls

Do this early in every design interview to justify sharding, caching, and topology.
Pitfalls: forgetting **peak vs average** (use 2–3x), ignoring **replication
overhead** (×3) and index/metadata bloat, mixing bits/bytes (÷8), conflating
storage-per-day with total (multiply by retention), and over-precision — round to
one significant figure and move on.

## Interview soundbites
- "1 day is ~10^5 seconds — that's the only constant I memorize for QPS."
- "Peak is 2–3x average; always size for peak."
- "Memory is ~100,000x faster than a disk seek, so the design question is 'what fits in RAM?'"
- "Multiply storage by replication factor (~3x) and retention, not just one day."
- "Read:write ratio drives the design — 50:1 here screams caching and replicas."
- "I round to one significant figure; I'm after the order of magnitude, not the decimal."
