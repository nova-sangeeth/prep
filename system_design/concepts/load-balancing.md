# Load Balancing

> Spread traffic across healthy nodes; L4 routes by IP/port, L7 by content — pick the algorithm and health check that match your workload.

## What it is & why it matters
A load balancer (LB) sits between clients and a pool of servers, distributing requests to maximize utilization, minimize latency, and remove single points of failure. It's the front door of any horizontally scaled tier and the thing that makes a stateless app pool actually usable. It also provides a stable virtual IP, TLS termination, and a place to do health checking and graceful drain. The LB itself must be redundant (active-active pairs, anycast, or a managed service) or it becomes the SPOF.

## How it works
Operates at one of two OSI layers:
- **L4 (transport)**: routes by IP + port, forwards TCP/UDP packets without reading payload. Fast, cheap, protocol-agnostic, can do connection-level stickiness via the 4-tuple. Can't make decisions on URL/headers/cookies.
- **L7 (application)**: terminates the connection, parses HTTP(S). Can route by path/host/header, do TLS termination, compression, rate limiting, request rewriting, and content-based routing. More CPU, slightly more latency, but far smarter.

```
                       ┌─ health checks ─┐
client ──► [ LB ] ─────┼──► app-1  ✔     │
            │          ├──► app-2  ✔     │  removed if
       picks node      ├──► app-3  ✘ ◄───┘  check fails
       per algorithm   └──► app-4  ✔
```

Typical chain: DNS / anycast → L4 LB (or cloud NLB) → L7 LB (ALB/Envoy/NGINX) → app servers. Global traffic often uses **GSLB / DNS-based** routing (geo, latency) before a regional LB takes over.

## Tradeoffs / variants
| Algorithm | How it picks | Best when | Watch out |
|---|---|---|---|
| Round-robin | Next node in rotation | Uniform requests, homogeneous nodes | Ignores load/latency; uneven request cost |
| Weighted RR | RR biased by capacity weight | Heterogeneous node sizes | Static weights drift from reality |
| Least connections | Fewest active conns | Long-lived/variable-duration requests | Conn count ≠ actual load |
| Least response time | Least conns + lowest latency | Latency-sensitive, mixed backends | Needs live latency measurement |
| IP / consistent hash | Hash(key) → node | Cache affinity, sticky-by-key, shards | Rebalancing on node change (mitigated by consistent hashing) |
| Random (+ 2 choices) | Pick 2 at random, take lighter | Large fleets, cheap & near-optimal | None major; great default at scale |

| Layer | Sees | Can do | Cost |
|---|---|---|---|
| L4 | IP, port, TCP | Fast forward, conn stickiness | Low CPU |
| L7 | Full HTTP | Path/header routing, TLS, WAF, rewrite | Higher CPU/latency |

## When to use · pitfalls
- **Health checks**: active (LB probes `/healthz`) vs passive (observe real traffic failures). Tune thresholds — too aggressive flaps nodes in/out (and can cascade load onto survivors); too lax sends traffic to dead nodes. Use **shallow** checks (is the process up) vs **deep** checks (can it reach the DB) deliberately; deep checks can take the whole fleet out if a shared dependency blips.
- **Sticky sessions** (session affinity): pin a client to one server via cookie or hash. Needed only if the server holds session state — but that reintroduces statefulness, causes uneven load, and breaks on node loss. Prefer externalizing session state (Redis/JWT) and keeping the pool stateless; use stickiness for cache locality, not correctness.
- **Connection draining / graceful shutdown**: stop new conns, let in-flight finish before removing a node — avoids 5xx on deploys.
- Pitfalls: the LB as SPOF; sticky sessions + autoscaling = hot nodes; using L4 when you need path routing; health-check storms; not accounting for TLS termination CPU; thundering retries amplifying an outage (pair with timeouts, backoff, circuit breakers).
- **Consistent hashing** deserves a callout: keeps key→node mapping stable as the fleet changes (only K/N keys move), which is why it underpins sharded caches and partitioned stores.

## Interview soundbites
- "L4 routes by IP/port and is fast; L7 reads HTTP so it can route by path, terminate TLS, and do WAF."
- "Round-robin assumes uniform requests; least-connections handles variable-duration work better."
- "Power-of-two-random-choices gives near-optimal balancing for almost no cost — a great default at scale."
- "Sticky sessions are a smell — externalize state to Redis or a JWT and keep the pool stateless."
- "Consistent hashing means adding a node moves only ~1/N of keys, not the whole map."
- "Drain connections on deploy and the LB itself must be redundant, or it's just a fancier SPOF."
