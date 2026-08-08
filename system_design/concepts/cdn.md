# Content Delivery Networks (CDN)

> Cache content at globally distributed edge POPs near users to cut latency, offload origin, and absorb traffic spikes.

## What it is & why it matters

A CDN is a geographically distributed network of **edge servers (POPs)** that
cache and serve content close to users. Wins: lower latency (RTT dominated by
distance/speed of light), reduced origin load (offload), higher availability,
DDoS absorption, and bandwidth cost savings at the edge. Essential for static
assets (JS/CSS/images/video) and increasingly for dynamic acceleration and edge
compute. The user hits the nearest POP instead of crossing oceans to origin.

## How it works

DNS (often **anycast** or geo-DNS) routes the client to the nearest healthy POP.
On a cache **miss**, the edge fetches from origin (or a mid-tier shield/parent
cache), stores it, and serves subsequent **hits** locally until the object's TTL
expires.

```
   User (Mumbai) --- DNS geo/anycast ---> Edge POP (Mumbai)
                                            |  hit -> serve from cache
                                            |  miss v
                                       Shield/parent cache
                                            |  miss v
                                          Origin (us-east)
```

**Push vs pull:**
- *Pull (origin-pull):* CDN fetches on first miss, caches lazily. Easy, default;
  first user pays a slow miss; good for large/long-tail catalogs.
- *Push:* you upload/replicate assets to the CDN ahead of time. Predictable,
  good for large files or low-traffic-but-critical assets; you manage placement.

## Tradeoffs / variants

| Concern | Options | Notes |
|---|---|---|
| Population | Pull (lazy) vs Push (eager) | Pull = simplicity; Push = control/prewarm |
| Freshness | TTL (`Cache-Control: max-age`), `ETag`/`If-None-Match` | High TTL = better hit rate, staler data |
| Invalidation | Purge (slow, global) vs versioned URLs | Prefer `app.a1b2c3.js` hashing over purge |
| Routing | Anycast vs GeoDNS | Anycast self-heals via BGP; GeoDNS coarser |
| Content | Static (cache-friendly) vs Dynamic (DSA/edge) | Dynamic: TCP/TLS offload, route optimization |
| `Vary` | by encoding, device, language | Too many variants shreds hit ratio |

## When to use · pitfalls

Use for any geographically dispersed audience serving cacheable assets, video
streaming, software/large-file downloads, and to shield origin from spikes/DDoS.
Even dynamic APIs benefit from edge TLS termination and connection reuse.

Pitfalls:
- **Cache invalidation is hard.** Purges propagate slowly and inconsistently
  across POPs. The robust pattern is **immutable, content-hashed URLs** + long
  TTLs; deploy = new filename, never overwrite.
- **Don't cache personalized/auth'd responses** at a shared edge (data leak). Set
  `Cache-Control: private`/`no-store`; segment by cache key if needed.
- **TTL tuning:** too long = stale; too short = low hit ratio + origin load.
- **Cookies/`Vary` explosion** fragment the cache and tank hit rate.
- **Cold cache / thundering herd** on a popular miss → use **request
  coalescing**, a shield tier, or prewarming.
- **HTTPS at edge** needs cert management (SNI, SAN, or CDN-managed certs).

## Interview soundbites
- "CDN trades freshness for latency and origin offload — TTL is the dial."
- "Pull is lazy and simple; push prewarms and gives control."
- "Solve invalidation with content-hashed immutable URLs, not purges."
- "Latency is physics — caching near the user beats any code optimization for global reach."
- "Never cache authenticated/personalized responses on a shared edge."
- "Anycast routes to the nearest POP and reroutes around failures via BGP."
