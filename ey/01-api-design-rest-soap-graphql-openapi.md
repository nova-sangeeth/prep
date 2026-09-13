# API Design & Protocols — REST, SOAP, GraphQL, OpenAPI

> EY GDS — API & Integration Developer (Senior / Rank 42) prep

**What this file buys you:** the JD's very first line is *"API Development and Integration (REST, SOAP, GraphQL, OpenAPI/Swagger)"*. Two of those four are gaps for you. This file gets you to the point where you can hold a 20-minute contract-design conversation, draw a SOAP-to-REST facade on a whiteboard, and say the sentence *"an MCP tool is just an API operation with a schema and a governance problem"* and have it land. Everything here is stated in **spoken-answer shape**: the first 2–3 sentences of each answer are the whole answer; the rest is ammunition for the follow-up.

**If you only have 50 minutes:** §2 (status codes), §3 (idempotency), §4 (pagination), §8 (RFC 9457), §11–12 (SOAP + APIM SOAP-to-REST — this is the actual job), §14 (OpenAPI), then the Traps and Rapid-Fire.

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [REST Fundamentals & Resource Modelling](#1-rest-fundamentals--resource-modelling) | Q1–Q6 |
| 2 | [Status Code Discipline](#2-status-code-discipline) | Q7–Q11 |
| 3 | [Idempotency](#3-idempotency) | Q12–Q15 |
| 4 | [Pagination, Filtering, Sorting](#4-pagination-filtering-sorting) | Q16–Q19 |
| 5 | [Versioning & Deprecation](#5-versioning--deprecation) | Q20–Q23 |
| 6 | [PATCH, Content Negotiation, Bulk](#6-patch-content-negotiation-bulk) | Q24–Q27 |
| 7 | [Long-Running Operations](#7-long-running-operations) | Q28–Q31 |
| 8 | [Errors — RFC 9457 Problem Details](#8-errors--rfc-9457-problem-details) | Q32–Q34 |
| 9 | [CORS, Caching, Compression](#9-cors-caching-compression) | Q35–Q39 |
| 10 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 vs gRPC](#10-http11-vs-http2-vs-http3-vs-grpc) | Q40–Q44 |
| 11 | [SOAP — The Gap You Must Close](#11-soap--the-gap-you-must-close) | Q45–Q54 |
| 12 | [Exposing SOAP as REST in Azure APIM](#12-exposing-soap-as-rest-in-azure-apim) | Q55–Q59 |
| 13 | [GraphQL](#13-graphql) | Q60–Q70 |
| 14 | [OpenAPI / Swagger](#14-openapi--swagger) | Q71–Q79 |
| 15 | [AsyncAPI — Contracts for Events](#15-asyncapi--contracts-for-events) | Q80–Q81 |
| — | [Interviewer Traps](#interviewer-traps) | 12 |
| — | [30-Second Whiteboard Versions](#30-second-whiteboard-versions) | 3 |
| — | [Rapid Fire](#rapid-fire) | 40 |

**Sibling files:** [Auth & Security](06-auth-and-security.md) covers OAuth2/OIDC/JWT/mTLS in depth — this file only touches auth where it changes the *contract*.

---

## 1. REST Fundamentals & Resource Modelling

### Q1. What is REST, and what is the Richardson Maturity Model?
`[EASY]`

**Answer:** REST is an architectural style — stateless client-server, uniform interface, resources identified by URIs, representations transferred over a cacheable protocol. The Richardson Maturity Model is a four-level scale for how RESTful an HTTP API actually is: **Level 0** = one URI, one verb (RPC tunnelled over HTTP POST — SOAP lives here); **Level 1** = many resources, still one verb; **Level 2** = resources plus correct HTTP verbs and status codes; **Level 3** = hypermedia controls (HATEOAS). Almost every production enterprise API is Level 2, and that is a deliberate choice, not a failure.

| Level | What you have | Real-world example |
|---|---|---|
| 0 | `POST /api` with an action in the body | SOAP, JSON-RPC, XML-RPC |
| 1 | `POST /orders`, `POST /customers` — resources, one verb | Legacy "REST-ish" APIs |
| 2 | `GET/POST/PUT/PATCH/DELETE` + real status codes | Stripe, Azure ARM, ~95% of enterprise APIs |
| 3 | Responses carry links describing what you can do next | HAL, JSON:API, ODATA, ACME/Let's Encrypt |

**Say this:** *"I target Level 2 and treat Level 3 as opt-in per-resource. Hypermedia pays off when the client is a generic browser or a long-lived partner integration you cannot redeploy; it costs you payload size and client complexity everywhere else."*

**If they push back — "so REST without HATEOAS isn't REST?"** — Correct by Fielding's dissertation, and irrelevant in delivery. I'd rather ship a well-documented OpenAPI contract at Level 2 than a hypermedia API that no client library understands. The one place I *do* use links is long-running operations and pagination, where the server genuinely owns the next-URI.

---

### Q2. How do you model resources? Walk me through designing an Orders API.
`[MEDIUM]`

**Answer:** Nouns, plural, lowercase, hyphenated. Collections and items: `/orders` and `/orders/{orderId}`. Containment gets one level of nesting: `/orders/{orderId}/lines`. Anything else becomes a top-level resource with a filter, because deep nesting couples your URI structure to a data model that will change. Verbs never appear in the path — if I genuinely need an action that isn't CRUD, I model it as a sub-resource that can be created.

```
GET    /v1/orders?status=pending&createdAfter=2026-08-01&sort=-createdAt&limit=50
POST   /v1/orders                          201 + Location
GET    /v1/orders/{orderId}
PATCH  /v1/orders/{orderId}                merge-patch+json
DELETE /v1/orders/{orderId}                204 (or 202 if async)
GET    /v1/orders/{orderId}/lines
POST   /v1/orders/{orderId}/cancellations  201  <- the "action as resource" trick
GET    /v1/customers/{customerId}/orders   convenience alias for ?customerId=
```

Rules I state out loud:

- **Identifiers are opaque strings**, never a leaked DB auto-increment. Use ULIDs/UUIDv7 so they sort by creation time; that also makes keyset pagination trivial.
- **No verbs in paths.** `POST /orders/{id}/cancel` is common and I accept it, but `POST /orders/{id}/cancellations` is better because the cancellation now has an ID, a timestamp, a reason, and an audit trail — and it becomes idempotent-able.
- **Nesting max two levels.** `/customers/{c}/orders/{o}/lines/{l}` is a maintenance bomb; make `/order-lines/{l}` real.
- **Plural everywhere**, including singletons — except true singletons like `/orders/{id}/status`.
- **Query params for filtering, never for identity.** `/orders?id=5` is wrong; `/orders/5` is right.

**If they push back — "our client wants `/getOrderById`"** — That's Level 1 RPC. I'd expose `/orders/{id}` and, if the client cannot change, put the alias in the gateway with a `rewrite-uri` policy so the ugly shape never reaches the service. That's exactly what APIM is for.

---

### Q3. Which HTTP methods are safe and which are idempotent?
`[EASY — but they will check]`

**Answer:** Per RFC 9110 §9.2.1, the **safe** methods are `GET`, `HEAD`, `OPTIONS`, `TRACE` — they must not have observable side effects on the server. Per §9.2.2, the **idempotent** methods are all of those plus `PUT` and `DELETE`. `POST` and `PATCH` are **not** idempotent. Every safe method is idempotent; the reverse is not true.

| Method | Safe | Idempotent | Cacheable | Body |
|---|---|---|---|---|
| GET | ✅ | ✅ | ✅ | no |
| HEAD | ✅ | ✅ | ✅ | no |
| OPTIONS | ✅ | ✅ | ❌ | rare |
| TRACE | ✅ | ✅ | ❌ | no |
| PUT | ❌ | ✅ | ❌ | yes |
| DELETE | ❌ | ✅ | ❌ | rare |
| POST | ❌ | ❌ | only w/ explicit freshness | yes |
| PATCH | ❌ | ❌ | ❌ | yes |

Two nuances that separate a senior answer:

1. **Idempotent ≠ same status code.** `DELETE /orders/5` twice → `204` then `404` (or `204` again). Idempotency is about *server state*, not the response.
2. **PATCH can be idempotent** if the patch document is absolute (`{"status": "cancelled"}` — merge-patch), and is definitely not if it is relative (`{"op": "add", "path": "/tags/-", "value": "x"}` — JSON Patch append).

**If they push back — "so retries are safe on PUT?"** — Safe from a state perspective, yes. But not free: a retried `PUT` after a network timeout can still clobber a concurrent write. That's what `If-Match` + ETag is for — optimistic concurrency, `412 Precondition Failed` on conflict.

---

### Q4. PUT vs POST vs PATCH — when do you use each?
`[EASY]`

**Answer:** `POST` when the server assigns the identifier — it creates a subordinate resource under the collection and returns `201` with a `Location`. `PUT` when the client owns the identifier and is sending the complete representation — it's a full replace, and it can create-or-replace at a known URI. `PATCH` when you're sending a partial change document.

```
POST /v1/orders            -> 201 Location: /v1/orders/01J8XZ...   (server picks ID)
PUT  /v1/orders/01J8XZ...  -> 200/204   full replace; missing fields are cleared
PATCH /v1/orders/01J8XZ... -> 200/204   partial; only what's in the body changes
```

The trap people fall into: using `PUT` for partial updates. If your `PUT` handler ignores absent fields, you have implemented `PATCH` and mislabelled it, and the first client that sends a trimmed payload silently loses data.

**If they push back — "can PUT create?"** — Yes, and that's the correct pattern for client-generated IDs — file uploads to a known path, config documents, idempotent upsert of a partner record keyed by their reference number. Return `201` if you created, `200`/`204` if you replaced.

---

### Q5. What does statelessness actually buy you, and where do you break it?
`[MEDIUM]`

**Answer:** Statelessness means every request carries everything needed to process it — no server-side session affinity. In practice that buys horizontal scale-out, zero-downtime rolling deploys, and the ability to put a gateway or load balancer in front without sticky sessions. It's why a JWT bearer token beats a session cookie for an API.

Where you legitimately break it, and how you contain it:

| Stateful thing | Where you actually put it |
|---|---|
| Auth session | JWT with `exp`/`aud`/`iss`, validated at the gateway (`validate-jwt`) |
| Idempotency records | Redis / Azure Cache for Redis, TTL 24h |
| Long-running job state | Durable Functions orchestration / Logic Apps stateful run history |
| Pagination cursor | Encoded into the opaque cursor, not held server-side |
| Rate-limit counters | Gateway-local (APIM `rate-limit-by-key`) — note these are per-gateway-instance, never globally exact |

**If they push back — "isn't a cache server state?"** — It's *shared* state, not *session* state. The distinction that matters is whether request N+1 must land on the same process as request N. If it must, you cannot autoscale or drain a node.

---

### Q6. How does an API gateway differ from a load balancer and a reverse proxy?
`[MEDIUM — asked verbatim in REST rounds]`

**Answer:** A load balancer works at L4/L7 and distributes traffic across identical backends — it doesn't know what an API is. A reverse proxy terminates the client connection and forwards to a backend, adding TLS termination, caching, rewriting. An API gateway is a reverse proxy that is **API-aware**: it knows about products, subscriptions, operations, schemas, and per-consumer policy — auth, quota, transformation, versioning, and observability keyed by *who is calling which operation*.

```
Client -> [ APIM gateway ]  validate-jwt / rate-limit-by-key / quota
                            xml-to-json / set-backend-service / cache-lookup
                            circuit breaker on the backend entity
       -> [ Load balancer ] round-robin across N identical pods
       -> [ Service pods ]
```

Downsides to name proactively — this is what gets you marked as senior:

- **It's a single point of failure and a shared blast radius.** One bad global policy takes down every API.
- **Latency tax** — an extra hop, plus policy evaluation.
- **It becomes a place to hide business logic.** Transformation policies are fine; if order-total calculation ends up in a `set-body` expression, you have built a distributed monolith that no one can unit test.
- **Capacity is not a throttle.** When APIM reaches capacity it does *not* start returning 429 — it degrades like an overloaded web server: rising latency, dropped connections, timeouts. Clients must retry.

**If they push back — "how do you scale it?"** — In APIM classic you scale units and watch the composite **Capacity** metric; Microsoft's guidance is to scale at **60–70% sustained** (evaluate over 30 minutes), and at **40%** if you're running a single unit because capacity has to be reserved for guest-OS updates. A scale operation takes roughly 30 minutes, so autoscale rules with a 5-minute window are useless. In v2 tiers the metric is different — `CPU Percentage of Gateway` / `Memory Percentage of Gateway`; the classic Capacity metric reads 0 there.

---

## 2. Status Code Discipline

### Q7. 201 vs 202 vs 204 — when do you return each?
`[MEDIUM]`

**Answer:** `201 Created` when the resource now exists and you can point at it — you must include a `Location` header, and you should return the representation. `202 Accepted` when you've taken the request but processing is not complete — the resource may never exist; return a status/operation URI to poll. `204 No Content` when the action succeeded and there is deliberately nothing to send back — typical for `DELETE` and for `PUT`/`PATCH` when the client already knows the new state.

```http
HTTP/1.1 201 Created
Location: /v1/orders/01J8XZQ4M7K3TR5S9WBYE2N6HD
Content-Type: application/json
ETag: "W/\"7f3a\""

{"orderId":"01J8XZQ4M7K3TR5S9WBYE2N6HD","status":"pending","total":499.00}
```

```http
HTTP/1.1 202 Accepted
Location: /v1/orders/01J8XZ.../operations/9d2c
Retry-After: 5
Content-Type: application/json

{"operationId":"9d2c","status":"running","resource":"/v1/orders/01J8XZ..."}
```

RFC 9110 section references if they want them: 201 = §15.3.2, 202 = §15.3.3, 204 = §15.3.5, 206 = §15.3.7, 304 = §15.4.5.

**If they push back — "why not just 200 for everything?"** — Because the gateway, the CDN, and every generated client behave differently on 201 vs 202. A `202` tells a client "poll, don't retry", which is the difference between a working integration and a thundering herd on a slow ERP.

---

### Q8. 400 vs 422 — what's the actual rule?
`[MEDIUM — a favourite]`

**Answer:** `400 Bad Request` means the server could not understand the request at all — malformed JSON, a broken query string, wrong content type framing. `422 Unprocessable Content` means the syntax was fine and the *semantics* failed — the JSON parsed, the schema matched structurally, but `startDate` is after `endDate` or the SKU doesn't exist. As of RFC 9110 §15.5.21, 422 is core HTTP, not a WebDAV extension any more, so there's no longer an excuse to avoid it.

```python
# FastAPI: pydantic gives you 422 for free on schema failure.
# You add 422 for business-rule failure and reserve 400 for unparseable input.
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

app = FastAPI()

class OrderWindow(BaseModel):
    start: date
    end: date
    sku: str = Field(min_length=3, max_length=32)

    @model_validator(mode="after")
    def check_range(self) -> "OrderWindow":
        if self.end < self.start:
            raise ValueError("end must be on or after start")
        return self

@app.post("/v1/order-windows", status_code=201)
def create_window(w: OrderWindow) -> dict:
    if not sku_exists(w.sku):
        raise HTTPException(status_code=422, detail=f"unknown sku {w.sku}")
    return {"id": "ow_1", "sku": w.sku}
```

**Honest caveat to say out loud:** FastAPI returns `422` for *request validation* errors by default, which is arguably over-broad — a missing required field is closer to `400`. I don't fight the framework; I document it and keep the error envelope consistent. What I never do is return `200` with `{"success": false}`.

**If they push back — "409 vs 422?"** — `409 Conflict` is about a clash with the *current state of the resource* (duplicate order number, stale ETag on a non-conditional write, concurrent modification). `422` is about the request content being unprocessable regardless of state. Rule of thumb: if retrying later with the identical body could succeed, it's `409`; if it can never succeed, it's `422`.

---

### Q9. Design your 429 response.
`[MEDIUM]`

**Answer:** `429 Too Many Requests` comes from RFC 6585 (which also defines 428, 431 and 511). It must carry `Retry-After` (RFC 9110 §10.2.3) — either delta-seconds or an HTTP-date — and should carry the rate-limit headers so a well-behaved client can self-pace instead of hammering.

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1756134000
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Subscription 'partner-acme' exceeded 1000 calls per 60s.",
  "instance": "/v1/orders",
  "retryAfterSeconds": 30
}
```

APIM does this for you — `rate-limit-by-key` returns 429 and writes `Retry-After` (rename with `retry-after-header-name`), plus `remaining-calls-header-name` and `total-calls-header-name` if you set them:

```xml
<rate-limit-by-key calls="1000"
                   renewal-period="60"
                   counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)"
                   remaining-calls-header-name="X-RateLimit-Remaining"
                   total-calls-header-name="X-RateLimit-Limit"
                   retry-after-header-name="Retry-After" />
```

**Numbers that make this credible:** `renewal-period` on `rate-limit-by-key` is a sliding window with a **maximum of 300 seconds**. Counters are tracked **independently per gateway instance and per region** — Microsoft's own doc says *"Because of the distributed nature of throttling architecture, rate limiting is never completely accurate."* And in **v2 tiers the algorithm is a token bucket**, while classic uses a sliding window; if you apply the same counter-key at two scopes with different limits in v2, behaviour is unpredictable.

**If they push back — "what's the client supposed to do?"** — Honour `Retry-After` exactly, then exponential backoff **with jitter** on top. Without jitter, every throttled client retries at the same instant and you get a synchronised stampede. See §3 for retry-safety.

---

### Q10. A client sends a request your API can't serve because the caller is unauthenticated vs unauthorised vs the resource doesn't exist for them. Which codes?
`[MEDIUM]`

**Answer:** `401 Unauthorized` = no credentials or invalid credentials — and it **must** include a `WWW-Authenticate` header, which almost nobody does. `403 Forbidden` = credentials are valid, you're just not allowed. `404 Not Found` = it doesn't exist, or you're deliberately hiding existence from an unauthorised caller.

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="orders", error="invalid_token", error_description="The token expired at 2026-08-25T09:14:00Z"
```

The security nuance: for multi-tenant APIs, returning `403` on someone else's resource leaks existence (an enumeration oracle). For anything sensitive I return `404` for both "missing" and "not yours". I document that behaviour so it isn't mistaken for a bug.

**If they push back — "405 vs 404?"** — `405 Method Not Allowed` when the URI matches a known resource but the verb is wrong, and RFC 9110 §15.5.6 says the response **must** carry an `Allow` header listing what is permitted. `404` when the URI itself doesn't route.

---

### Q11. Give me your status-code cheat sheet for an enterprise API.
`[EASY]`

| Code | Use it when | Must include |
|---|---|---|
| 200 | Read succeeded, or write returning the new state | body |
| 201 | Resource created | `Location` |
| 202 | Accepted for async processing | `Location` (operation), `Retry-After` |
| 204 | Success, deliberately no body | — |
| 206 | Range request satisfied | `Content-Range` |
| 301 / 308 | Permanent move (308 preserves method+body) | `Location` |
| 304 | Conditional GET, unchanged | `ETag` |
| 400 | Unparseable / malformed | problem+json |
| 401 | No / bad credentials | `WWW-Authenticate` |
| 403 | Authenticated, not permitted | problem+json |
| 404 | Not found (or hidden) | problem+json |
| 405 | Wrong verb on a real resource | `Allow` |
| 406 | Can't satisfy `Accept` | problem+json |
| 409 | State conflict / duplicate / concurrent | problem+json |
| 410 | Was here, deliberately gone forever | problem+json |
| 412 | `If-Match` / `If-Unmodified-Since` failed | problem+json |
| 415 | Unsupported `Content-Type` | `Accept-Post`/`Accept-Patch` |
| 422 | Parsed fine, semantically invalid | problem+json |
| 428 | You require a conditional request and got none | problem+json |
| 429 | Throttled | `Retry-After` |
| 500 | Your bug | problem+json, **no stack trace** |
| 502 / 503 / 504 | Bad backend / unavailable / backend timeout | `Retry-After` on 503 |

**One-liner to say:** *"5xx means 'my fault, retry is reasonable'. 4xx means 'your fault, retrying the same thing will fail the same way' — with the single exception of 429."*

---

## 3. Idempotency

### Q12. How do you make a POST safely retryable?
`[HARD — Tier 2 near-certain for an integration role]`

**Answer:** With an idempotency key. The client generates a UUID per logical operation and sends it in the `Idempotency-Key` request header; the server stores the key plus a fingerprint of the request and the eventual response, and on a retry with the same key it replays the stored response instead of re-executing. That turns "the network timed out and I don't know if the order was placed" from a business incident into a no-op.

The IETF work is `draft-ietf-httpapi-idempotency-key-header` — version **-07**, published **15 October 2025**, Standards Track, **still a draft, not an RFC**. Say that; it shows you read specs rather than blog posts. It specifies:

| Situation | Status |
|---|---|
| Header missing on an operation that requires it | `400 Bad Request` |
| Same key, **different** request payload | `422 Unprocessable Content` |
| Same key, original request **still in flight** | `409 Conflict` |

Key scope and expiry are explicitly left to the resource owner — you must document them. I use *(tenant, endpoint, key)* as the scope and a 24-hour TTL.

```python
# FastAPI idempotency middleware backed by Azure Cache for Redis.
# Scope = (subscription/tenant, method, path, key). TTL 24h.
import hashlib
import json
from typing import Callable

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse

app = FastAPI()
r = redis.from_url("rediss://cache.redis.cache.windows.net:6380", decode_responses=True)

IDEMPOTENT_METHODS = {"POST", "PATCH"}
TTL_SECONDS = 86_400


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://api.example.com/problems/idempotency",
            "title": title,
            "status": status,
            "detail": detail,
        },
    )


@app.middleware("http")
async def idempotency(request: Request, call_next: Callable) -> Response:
    if request.method not in IDEMPOTENT_METHODS:
        return await call_next(request)

    key = request.headers.get("Idempotency-Key")
    if not key:
        return _problem(400, "Missing Idempotency-Key", "This operation requires an Idempotency-Key header.")

    body = await request.body()
    fingerprint = hashlib.sha256(body).hexdigest()
    tenant = request.headers.get("X-Tenant-Id", "public")
    slot = f"idem:{tenant}:{request.method}:{request.url.path}:{key}"

    # SET NX is the atomic claim. Winner executes; everyone else replays or 409s.
    claimed = await r.set(slot, json.dumps({"state": "in_flight", "fp": fingerprint}),
                          nx=True, ex=TTL_SECONDS)
    if not claimed:
        stored = json.loads(await r.get(slot))
        if stored["fp"] != fingerprint:
            return _problem(422, "Idempotency key reuse",
                            "This Idempotency-Key was used with a different request payload.")
        if stored["state"] == "in_flight":
            resp = _problem(409, "Request in progress",
                            "The original request with this Idempotency-Key is still being processed.")
            resp.headers["Retry-After"] = "2"
            return resp
        return JSONResponse(status_code=stored["status"], content=stored["body"],
                            headers={"Idempotency-Replayed": "true"})

    response = await call_next(request)
    payload = b"".join([chunk async for chunk in response.body_iterator])
    await r.set(slot, json.dumps({
        "state": "done",
        "fp": fingerprint,
        "status": response.status_code,
        "body": json.loads(payload or b"null"),
    }), ex=TTL_SECONDS)
    return Response(content=payload, status_code=response.status_code,
                    headers=dict(response.headers), media_type=response.media_type)
```

**If they push back — "why the payload fingerprint?"** — Without it, a buggy client that reuses one key for two different orders silently gets the first order's response for the second order. The fingerprint turns a silent data-loss bug into a `422`.

---

### Q13. How does this look on the messaging side rather than the HTTP side?
`[HARD — bridges to the Service Bus question they always ask]`

**Answer:** Same idea, different mechanism. On Azure Service Bus you set a unique `MessageId` on the producer and enable **duplicate detection** on the queue/topic — the broker discards a repeat of the same `MessageId` inside the detection window. Then you make the consumer idempotent anyway, because at-least-once delivery survives every broker feature. Microsoft's own guidance says it plainly: *"The typical mechanism for identifying duplicate message deliveries is by checking the message-id. The sender can and should set the message-id to a unique value"* and *"Designing for idempotent message handling becomes critical."*

```python
import uuid
from azure.identity.aio import DefaultAzureCredential
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

async def publish_order(order_id: str, payload: bytes) -> None:
    cred = DefaultAzureCredential()
    async with ServiceBusClient("sb-ey-prod.servicebus.windows.net", cred) as client:
        async with client.get_queue_sender("orders") as sender:
            msg = ServiceBusMessage(
                payload,
                message_id=f"order:{order_id}",       # duplicate-detection key
                correlation_id=str(uuid.uuid4()),      # traceability
                content_type="application/json",
                subject="OrderCreated",
            )
            await sender.send_messages(msg)            # ALWAYS await the send
```

Numbers worth quoting: Service Bus default **PeekLock duration is 1 minute, maximum 5 minutes** (renew beyond that); default **MaxDeliveryCount is 10** and dead-lettering on exceeding it **cannot be disabled**, only raised; an idle connection is closed after **10 minutes**, which drops your lock. Max message size is **256 KB on Basic/Standard**; **Premium supports up to 100 MB over AMQP but the per-entity default is still 1 MB** and the 100 MB is opt-in. That 256 KB ceiling is precisely why the **Claim Check** pattern exists — put the blob URI in the message, not the blob.

**If they push back — "what about exactly-once?"** — There is no exactly-once delivery over a network. There is at-least-once delivery plus idempotent processing, which is observationally exactly-once. Kafka's "exactly-once" is the same trick: idempotent producer (`enable.idempotence=true`, PID + per-partition sequence number), transactions, and consumers at `isolation.level=read_committed`.

---

### Q14. What's an idempotent consumer, concretely?
`[MEDIUM]`

**Answer:** A consumer that records the identity of every message it has already applied, in the **same transaction** as the business write, and skips anything it has seen. The canonical implementation is a `processed_messages` table with a unique constraint on the message id.

```sql
CREATE TABLE processed_messages (
    message_id   VARCHAR(200) NOT NULL PRIMARY KEY,
    handler      VARCHAR(100) NOT NULL,
    processed_at DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
);
```

```python
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

def handle_order_created(session: Session, message_id: str, order: dict) -> bool:
    """Returns True if applied, False if it was a duplicate. One transaction, no dual write."""
    try:
        with session.begin():
            session.execute(
                text("INSERT INTO processed_messages (message_id, handler) VALUES (:m, :h)"),
                {"m": message_id, "h": "handle_order_created"},
            )
            session.execute(
                text("INSERT INTO orders (id, customer_id, total) VALUES (:i, :c, :t)"),
                {"i": order["orderId"], "c": order["customerId"], "t": order["total"]},
            )
        return True
    except IntegrityError:
        session.rollback()
        return False
```

**If they push back — "what if the write goes to a different system than the DB?"** — Then you have a dual-write problem and you need the **Transactional Outbox**: write the business row and an outbox row in one local transaction, then a relay publishes from the outbox. Worth knowing: **Outbox is not in Microsoft's Azure Architecture Center cloud design patterns catalog** — the closest entries are *Idempotent Consumer* and *Event Sourcing*. Outbox comes from the microservices.io vocabulary. On Azure you implement it with a Cosmos DB change feed driving a Function, or a SQL table plus a polling publisher.

---

### Q15. What's your retry policy for calling a flaky downstream?
`[MEDIUM]`

**Answer:** Exponential backoff with full jitter, a bounded attempt count, retry only on `408`, `429`, `502`, `503`, `504` and connection-level errors, honour `Retry-After` when present, and wrap the whole thing in a circuit breaker so a persistently dead backend stops eating your thread budget. Retry without a circuit breaker turns a backend outage into a self-inflicted DDoS.

```python
import asyncio
import random
import httpx

RETRYABLE = {408, 429, 500, 502, 503, 504}

async def call_with_retry(client: httpx.AsyncClient, url: str, *, attempts: int = 5) -> httpx.Response:
    base, cap = 0.5, 20.0
    for attempt in range(attempts):
        try:
            resp = await client.get(url, timeout=httpx.Timeout(10.0, connect=3.0))
            if resp.status_code not in RETRYABLE:
                return resp
            hinted = resp.headers.get("Retry-After")
            delay = float(hinted) if hinted and hinted.isdigit() else None
        except (httpx.ConnectError, httpx.ReadTimeout):
            resp, delay = None, None
        if attempt == attempts - 1:
            if resp is not None:
                return resp
            raise httpx.ConnectError(f"exhausted {attempts} attempts to {url}")
        # full jitter: sleep U(0, min(cap, base * 2**attempt))
        window = min(cap, base * (2 ** attempt))
        await asyncio.sleep(delay if delay is not None else random.uniform(0, window))
    raise AssertionError("unreachable")
```

Microsoft's own pattern pairing to cite: *"pair Retry with Circuit Breaker so the app retries transient faults but stops retrying when a fault persists."* In APIM the circuit breaker lives on the **backend entity**, not as a policy:

```bicep
resource ordersBackend 'Microsoft.ApiManagement/service/backends@2024-05-01' = {
  parent: apim
  name: 'orders-erp'
  properties: {
    url: 'https://erp.internal/OrderService.svc'
    protocol: 'http'
    circuitBreaker: {
      rules: [
        {
          name: 'erp-5xx'
          failureCondition: {
            count: 10
            interval: 'PT1M'
            statusCodeRanges: [ { min: 500, max: 599 } ]
            errorReasons: [ 'Server errors' ]
          }
          tripDuration: 'PT1M'
          acceptRetryAfter: true
        }
      ]
    }
  }
}
```

Three limits to state proactively: circuit breaker is **not supported in the Consumption tier**, only **one rule per backend** is allowed, and because gateway instances don't synchronise, **tripping is approximate per-instance**. When tripped, APIM returns `503` to the client without calling the backend.

**If they push back — "why full jitter and not just exponential?"** — Because plain exponential backoff synchronises clients: everyone throttled at T retries at T+1s, T+3s, T+7s together. Full jitter spreads them uniformly and is what AWS's own architecture blog measured as best. Event Grid does the same thing natively — its retry ladder is 10s, 30s, 1min, 5min, 10min, 30min, 1hr, 3hr, 6hr, then every 12 hours up to 24 hours, and the docs say it adds *"a small randomization to all retry steps."*

---

## 4. Pagination, Filtering, Sorting

### Q16. Offset pagination vs cursor/keyset — which and why?
`[MEDIUM — near-certain]`

**Answer:** Keyset (cursor) pagination, unless the client genuinely needs to jump to page 47. Offset pagination breaks in two ways: it's **O(offset)** in the database because `OFFSET 100000` still scans and discards 100,000 rows, and it's **unstable under concurrent writes** — insert a row on page 1 while a client is paging and they see a duplicate on page 2; delete one and they skip a record entirely. Keyset uses the last seen sort key as the anchor, so it's an index seek and it's stable.

```sql
-- Offset: degrades linearly, and shifts under concurrent inserts
SELECT id, created_at, total
FROM orders
WHERE tenant_id = @t
ORDER BY created_at DESC, id DESC
OFFSET 100000 ROWS FETCH NEXT 50 ROWS ONLY;

-- Keyset: index seek, constant cost, stable
SELECT id, created_at, total
FROM orders
WHERE tenant_id = @t
  AND (created_at, id) < (@last_created_at, @last_id)   -- composite tiebreaker
ORDER BY created_at DESC, id DESC
FETCH NEXT 50 ROWS ONLY;
-- needs: CREATE INDEX ix_orders_tenant_created ON orders(tenant_id, created_at DESC, id DESC)
```

The **composite tiebreaker is the part people forget**. If `created_at` is not unique, keyset on `created_at` alone will drop or repeat rows at page boundaries. Always append a unique column.

```python
import base64
import json
from datetime import datetime
from typing import Any

def encode_cursor(created_at: datetime, row_id: str) -> str:
    raw = json.dumps({"c": created_at.isoformat(), "i": row_id}, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")

def decode_cursor(cursor: str) -> dict[str, Any]:
    pad = "=" * (-len(cursor) % 4)
    return json.loads(base64.urlsafe_b64decode(cursor + pad))
```

Response shape:

```json
{
  "data": [ { "id": "01J8XZ...", "total": 499.00 } ],
  "pagination": {
    "limit": 50,
    "nextCursor": "eyJjIjoiMjAyNi0wOC0yNVQwOToxNDowMFoiLCJpIjoiMDFKOFhaIn0",
    "hasMore": true
  }
}
```

**If they push back — "the client wants a total count"** — Total count is the expensive part, not the paging. I offer it as an opt-in (`?includeTotal=true`) with an approximate count from statistics, or I return `hasMore` only. Computing an exact `COUNT(*)` on every page of a 40-million-row table is how you take down a database.

**If they push back — "keyset can't sort by arbitrary user-chosen columns"** — True, and that's the honest trade-off. Keyset requires a total ordering backed by an index. For a report-style endpoint with ten sortable columns and small result sets, offset is fine; for a firehose feed or an export, keyset is mandatory. I pick per endpoint, not per API.

---

### Q17. How do you design filtering and sorting conventions?
`[EASY]`

**Answer:** Simple, flat query parameters with a documented operator suffix, and a single `sort` parameter using a leading `-` for descending. I do not build a general-purpose query language unless the API is explicitly analytical — that's how you end up accidentally reimplementing OData and exposing a SQL-injection surface through a `$filter` string.

```
GET /v1/orders?status=pending&status=shipped        # repeated key = OR
GET /v1/orders?total[gte]=100&total[lt]=1000        # bracketed operator
GET /v1/orders?createdAfter=2026-08-01T00:00:00Z    # explicit named params beat generic ops
GET /v1/orders?sort=-createdAt,total                # - = desc, comma = tiebreakers
GET /v1/orders?fields=id,status,total               # sparse fieldsets
GET /v1/orders?expand=customer                      # controlled embedding
```

Rules: allow-list every sortable and filterable field (never pass a client string into `ORDER BY`), cap `limit` server-side (I default 50, max 200), and return `400`/`422` on an unknown filter rather than silently ignoring it — silent ignore is how a client thinks they filtered and they didn't.

**If they push back — "why not OData? Azure supports it."** — APIM does have a `validate-odata-request` policy and OData is genuinely good for analytical/CRUD-over-entities surfaces, especially Dynamics-adjacent work. I'd use it when the consumer is a Power Platform / Excel client that speaks OData natively. For a partner-facing REST API I'd avoid it because the query surface you have to defend is enormous.

---

### Q18. How do you page a SOAP or legacy backend that has no paging?
`[HARD — very likely for this JD]`

**Answer:** You don't push paging down; you either buffer at the facade or you flip the contract to async. If the legacy call returns 40,000 rows in one shot, I make the REST facade a `202`-style export: accept the request, run the SOAP call in a Function or Logic App, write the result to Blob, and hand the client a paged read over the blob or a SAS download URL.

The forcing constraints, with real numbers:

| Constraint | Limit |
|---|---|
| APIM buffered payload size | **500 MiB** classic, **2 MiB** on v2 and Consumption |
| APIM total request duration | unlimited classic/v2, **30 seconds** on Consumption |
| APIM cached response size | **2 MiB** all tiers |
| Logic Apps outbound HTTP timeout | **120 s** Consumption, **225 s** Standard |
| Azure Functions HTTP response | **230 s** hard ceiling (Load Balancer idle timeout), regardless of `functionTimeout` |
| On-prem data gateway | **2 MB** write, **8 MB** compressed read |

That last one is the one that bites in EY-shaped work: the on-premises data gateway caps read responses at 8 MB compressed, which forces Claim Check on anything bigger.

**If they push back — "can't you just raise the timeout?"** — Not past 230 seconds on an HTTP-triggered Function, because that's the Azure Load Balancer idle timeout, not a Functions setting. That's exactly why the Durable Functions **async HTTP API** pattern exists: return `202` with `Location`, poll the status endpoint.

---

### Q19. What's your response envelope?
`[EASY]`

**Answer:** For collections: a `data` array plus a `pagination` object. For single resources: the resource itself at the top level, no wrapper. For errors: `application/problem+json` per RFC 9457. Consistency matters more than which shape you pick — the failure mode is three teams inventing three envelopes inside one API product.

```json
// collection
{"data":[...],"pagination":{"limit":50,"nextCursor":"...","hasMore":true}}
// single
{"orderId":"01J8XZ...","status":"pending","total":499.00}
// error
{"type":"https://api.example.com/problems/sku-unknown","title":"Unknown SKU","status":422,"detail":"SKU 'AB' is not in the catalogue.","instance":"/v1/orders","sku":"AB"}
```

**If they push back — "why not wrap single resources too?"** — Because it forces every client to unwrap for no gain, and it breaks direct schema reuse between the collection element type and the item response. The one exception is when you need to attach per-response metadata (`_links`, `_meta`) — then wrap, and wrap consistently.

---

## 5. Versioning & Deprecation

### Q20. How do you version an API, and what do enterprise clients actually pick?
`[MEDIUM — near-certain]`

**Answer:** Four options — URI path, custom header, media-type (content negotiation), and query parameter. Enterprises overwhelmingly pick **URI path versioning** (`/v1/orders`) because it is visible in logs, cacheable, routable at the gateway, testable from a browser, and trivially explainable to a partner. Media-type versioning is the most architecturally pure and the most operationally painful.

| Strategy | Example | Pros | Cons |
|---|---|---|---|
| **URI path** | `/v1/orders` | Visible, cacheable, routable, easy for partners | "Not RESTful" (the URI should identify the resource, not the representation) |
| **Custom header** | `X-API-Version: 2` | Clean URIs | Invisible in logs/CDN keys, easy to forget, needs `Vary` |
| **Media type** | `Accept: application/vnd.example.order.v2+json` | Purist-correct, per-resource granularity | Awkward to test, breaks naive clients, needs `Vary: Accept` |
| **Query param** | `?api-version=2026-08-01` | Azure ARM's own choice; easy | Pollutes cache keys, easy to omit |

Azure itself uses date-based query-param versioning (`?api-version=2024-05-01`) for ARM, which is a good precedent to name because you're interviewing for an Azure role.

**In APIM**, versioning is a first-class concept and it's worth naming the distinction:

- **Version** = a breaking change, visible to the consumer. Path, query string, or header scheme, grouped into a *version set*.
- **Revision** = a non-breaking change to an existing version, made online, testable via `;rev=n`, promoted to current with a changelog entry and rollback.

```bash
az apim api release create \
  --resource-group rg-int-prod \
  --service-name apim-ey-prod \
  --api-id orders-v1 \
  --release-id r-2026-08-25 \
  --api-revision 3 \
  --notes "Add cancellations sub-resource; no breaking change"
```

**If they push back — "how many versions do you run?"** — Two: current and previous. More than that and every bug fix becomes an N-way backport. I gate the retirement on measured traffic per version per subscription, which APIM gives me for free in Application Insights.

---

### Q21. How do you deprecate an endpoint properly?
`[MEDIUM]`

**Answer:** Announce it in the response headers, not just in a wiki. `Deprecation` (RFC 9745, March 2025) carries a Structured Field Date saying when deprecation takes effect; `Sunset` (RFC 8594, May 2019) carries an HTTP-date saying when it stops working; a `Link` with `rel="deprecation"` points at the migration guide. RFC 9745 states normatively that the Sunset timestamp **MUST NOT be earlier than** the Deprecation timestamp.

```http
HTTP/1.1 200 OK
Deprecation: @1756080000
Sunset: Sat, 28 Feb 2026 23:59:59 GMT
Link: <https://developer.example.com/guides/orders-v2-migration>; rel="deprecation"; type="text/html"
Link: </v2/orders>; rel="successor-version"
```

```xml
<!-- APIM: bolt it on at API scope without touching the backend -->
<outbound>
    <base />
    <set-header name="Deprecation" exists-action="override">
        <value>@1756080000</value>
    </set-header>
    <set-header name="Sunset" exists-action="override">
        <value>Sat, 28 Feb 2026 23:59:59 GMT</value>
    </set-header>
    <set-header name="Link" exists-action="append">
        <value>&lt;https://developer.example.com/guides/orders-v2-migration&gt;; rel="deprecation"</value>
    </set-header>
</outbound>
```

Process, not just headers: minimum **6 months** of overlap for external partners, per-subscription traffic reports pushed to the account team monthly, a scheduled brownout (return `410 Gone` for one hour on two announced dates) so silent clients discover the problem before the deadline, then `410 Gone` permanently — never `404`, because `410` says "this was deliberate."

**If they push back — "how do you know who's still calling?"** — APIM logs `context.Subscription.Id` and `context.Api.Name` per request into Application Insights; a KQL query over `requests` grouped by subscription over 30 days gives you the exact migration list.

---

### Q22. What counts as a breaking change?
`[EASY]`

**Answer:** Anything a conforming client could observe and choke on. Breaking: removing or renaming a field, changing a type, adding a required request field, tightening validation, changing a status code, changing error semantics, changing default sort or page size, changing an enum's meaning. Non-breaking: adding an optional request field, adding a response field, adding a new endpoint, adding a new enum value **only if you documented that clients must tolerate unknown values**.

That last caveat is the one people miss. If your OpenAPI declares `status: {enum: [pending, shipped]}` and a generated client deserialises into a closed enum, adding `cancelled` breaks it. Either document forward-compatibility as a client obligation from day one, or model it as an open string with a documented value list.

**If they push back — "how do you enforce it?"** — Spec diffing in CI. `oasdiff` (or `openapi-diff`) fails the pipeline on a breaking change unless the PR bumps the major version. See §14 and [CI/CD](05-cicd-iac-and-gitops.md).

---

### Q23. Same question for events — how do you version a message schema?
`[HARD]`

**Answer:** Schema Registry plus backward-compatible evolution. Only add optional fields with defaults; never remove or retype a field in place; carry an explicit `schemaVersion` and an `eventType` in the envelope so consumers can route. For a hard break you publish a new topic/subject rather than mutating the existing one, and dual-publish during migration.

On Azure the registry lives in an **Event Hubs namespace** (Azure Schema Registry). Capacity: **25 MB on Standard, 100 MB on Premium, 1,024 MB on Dedicated**, with **1 MB per schema** and **25 / 1,000 / 10,000 schema versions** respectively by tier. Kafka's Confluent Schema Registry does the same job with `BACKWARD`/`FORWARD`/`FULL` compatibility modes.

**If they push back — "backward vs forward compatibility?"** — Backward = a new consumer can read old messages (you added an optional field). Forward = an old consumer can read new messages (you didn't remove anything it requires). You want both — that's `FULL` — for anything where producer and consumer deploy independently, which in an integration estate is always.

---

## 6. PATCH, Content Negotiation, Bulk

### Q24. JSON Patch vs JSON Merge Patch — which do you use?
`[MEDIUM — the JD names PATCH-heavy work]`

**Answer:** **JSON Merge Patch** (RFC 7396, media type `application/merge-patch+json`) for 90% of business APIs — you send a partial object, present keys are set, and `null` deletes. **JSON Patch** (RFC 6902, `application/json-patch+json`) when you need array element operations, atomic multi-op transactions, or optimistic concurrency via `test`. Note the RFC number trap: JSON Merge Patch is **RFC 7396, which obsoletes RFC 7386** — the older number is still all over the internet.

**JSON Merge Patch (RFC 7396)** — the RFC's own example:

```http
PATCH /v1/articles/1 HTTP/1.1
Content-Type: application/merge-patch+json

{"title":"Hello!","phoneNumber":"+01-123-456-7890","author":{"familyName":null},"tags":["example"]}
```

Applied to `{"title":"Goodbye!","author":{"givenName":"John","familyName":"Doe"},"tags":["example","sample"],"content":"unchanged"}` it yields `{"title":"Hello!","author":{"givenName":"John"},"tags":["example"],"content":"unchanged","phoneNumber":"+01-123-456-7890"}`.

Two hard limitations you must name: **you cannot set a field to `null`** (null means delete), and **arrays are replaced wholesale**, never element-wise.

**JSON Patch (RFC 6902)** — six operations, `add`, `remove`, `replace`, `move`, `copy`, `test`, applied in order and **atomically**: if any operation fails, none are applied.

```http
PATCH /v1/orders/01J8XZ HTTP/1.1
Content-Type: application/json-patch+json

[
  {"op":"test","path":"/version","value":7},
  {"op":"replace","path":"/status","value":"cancelled"},
  {"op":"add","path":"/tags/-","value":"customer-request"},
  {"op":"remove","path":"/promisedDate"}
]
```

The `test` op is a built-in optimistic-concurrency check — if `version` isn't 7, the whole patch is rejected. That's the one genuinely compelling reason to pick JSON Patch.

```python
# pip install jsonpatch  (RFC 6902)   /   the merge case is 30 lines, write it yourself
import jsonpatch
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

def merge_patch(target: dict, patch: dict) -> dict:
    """RFC 7396 §2 applyPatch, recursive."""
    if not isinstance(patch, dict):
        return patch
    if not isinstance(target, dict):
        target = {}
    for key, value in patch.items():
        if value is None:
            target.pop(key, None)
        else:
            target[key] = merge_patch(target.get(key), value)
    return target

@app.patch("/v1/orders/{order_id}")
async def patch_order(order_id: str, request: Request) -> dict:
    ct = request.headers.get("content-type", "").split(";")[0].strip()
    current = load_order(order_id)
    body = await request.json()
    if ct == "application/merge-patch+json":
        updated = merge_patch(dict(current), body)
    elif ct == "application/json-patch+json":
        try:
            updated = jsonpatch.JsonPatch(body).apply(dict(current))
        except jsonpatch.JsonPatchTestFailed:
            raise HTTPException(status_code=409, detail="precondition in test op failed")
        except jsonpatch.JsonPatchException as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    else:
        raise HTTPException(status_code=415, detail="use merge-patch+json or json-patch+json")
    return save_order(order_id, updated)
```

Notice the `415` and the `Accept-Patch` header you should advertise on `OPTIONS`:

```http
Accept-Patch: application/merge-patch+json, application/json-patch+json
```

**If they push back — "what about partial PUT?"** — There's no such thing. `PUT` is a full replace by definition; a `PUT` that ignores absent fields is a mislabelled `PATCH` and will lose data the first time a client sends a trimmed body.

---

### Q25. How does content negotiation work?
`[EASY]`

**Answer:** The client states preferences with `Accept`, `Accept-Language`, `Accept-Encoding`, `Accept-Charset`; the server picks a representation and echoes what it chose in `Content-Type` and, critically, lists the negotiation axes in `Vary` so caches don't serve the wrong variant. If the server can't satisfy `Accept`, it returns `406 Not Acceptable`.

```http
GET /v1/orders/01J8XZ HTTP/1.1
Accept: application/xml;q=0.9, application/json;q=1.0, */*;q=0.1
Accept-Encoding: br, gzip
```
```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Encoding: br
Vary: Accept, Accept-Encoding
```

Quality values run 0 to 1, three decimal places, default 1. `*/*;q=0.1` means "anything, but only if you have nothing better."

**Forgetting `Vary` is the classic production bug**: a shared cache stores the JSON response and then serves it to a client that asked for XML. In APIM the `cache-store` / `cache-lookup` pair has `vary-by-header` for exactly this:

```xml
<cache-lookup vary-by-developer="false" vary-by-developer-groups="false" downstream-caching-type="none">
    <vary-by-header>Accept</vary-by-header>
    <vary-by-header>Accept-Encoding</vary-by-header>
</cache-lookup>
```

**If they push back — "we support JSON only"** — Then I don't negotiate; I return `application/json` always and `415` on a non-JSON `Content-Type`. Content negotiation earns its complexity only when you genuinely serve multiple representations — which for this JD you will, because a SOAP-fronting facade often has to emit both `application/json` and `application/xml`.

---

### Q26. Design a bulk endpoint.
`[HARD]`

**Answer:** Two shapes. For **small, synchronous** batches: `POST /v1/orders/batch` taking an array, capped (I use 100 items), returning `207`-style per-item results so one bad row doesn't fail the batch. For **large** batches: don't do it synchronously at all — accept the payload, return `202` with an operation URI, process asynchronously, and expose a results file. The failure mode of a naive bulk endpoint is a 30-second p99 and a client that retries the whole 10,000-row batch after a timeout.

```http
POST /v1/orders/batch HTTP/1.1
Content-Type: application/json
Idempotency-Key: 6f1a1a1e-77e0-4a6e-9bf2-2d2b4a8c1f21

{"items":[{"ref":"a1","customerId":"C1","total":100},{"ref":"a2","customerId":"","total":-5}]}
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "summary": {"submitted": 2, "succeeded": 1, "failed": 1},
  "results": [
    {"ref":"a1","status":201,"orderId":"01J8XZ..."},
    {"ref":"a2","status":422,"problem":{
        "type":"https://api.example.com/problems/validation",
        "title":"Unprocessable Content","status":422,
        "detail":"customerId must not be empty; total must be > 0"}}
  ]
}
```

Design rules: the outer status is `200` (the batch was processed), each item carries its own status; the client-supplied `ref` correlates results without relying on array order; the whole batch shares one `Idempotency-Key`; and you document explicitly whether the batch is transactional. Mine are **not** transactional — partial success is the contract — because an all-or-nothing batch across a distributed backend is a saga, not an endpoint.

**If they push back — "why not 207 Multi-Status?"** — `207` is WebDAV (RFC 4918) and its body format is XML `<multistatus>`. Plenty of APIs borrow the code with a JSON body; I find it confuses generated clients and gateways, so I use `200` with per-item statuses and document it. I'll happily use `207` if the house style says so — the important part is that it's consistent.

---

### Q27. How do you handle file upload/download in a REST API?
`[MEDIUM]`

**Answer:** Don't stream large files through the API. Use the **Valet Key** pattern: the API authorises and returns a short-lived, narrowly-scoped SAS URL, and the client uploads directly to Blob Storage. The API then gets notified via Event Grid (`Microsoft.Storage.BlobCreated`) and continues processing. Small files (< a few MB) can go `multipart/form-data` through the API.

```python
from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from fastapi import FastAPI

app = FastAPI()
blob_svc = BlobServiceClient(account_url="https://stintprod.blob.core.windows.net",
                             credential=None)  # use DefaultAzureCredential + user delegation key

@app.post("/v1/documents/upload-url", status_code=201)
def upload_url(filename: str) -> dict:
    start = datetime.now(timezone.utc)
    expiry = start + timedelta(minutes=15)
    delegation_key = blob_svc.get_user_delegation_key(start, expiry)
    sas = generate_blob_sas(
        account_name="stintprod",
        container_name="inbound",
        blob_name=filename,
        user_delegation_key=delegation_key,
        permission=BlobSasPermissions(create=True, write=True),
        expiry=expiry,
        start=start,
    )
    return {"uploadUrl": f"https://stintprod.blob.core.windows.net/inbound/{filename}?{sas}",
            "expiresAt": expiry.isoformat()}
```

**Why this matters here:** the APIM buffered payload limit is **2 MiB on v2 and Consumption tiers** (500 MiB classic), the on-prem data gateway caps writes at **2 MB**, and Service Bus caps messages at **256 KB** on Standard. Every one of those pushes you toward Valet Key + Claim Check.

**If they push back — "we must proxy it for scanning"** — Then scan out-of-band: land the blob in a quarantine container, run Defender for Storage / a scanning Function, and only move it to the processing container on a clean verdict. That's Microsoft's **Quarantine** pattern, and it keeps the synchronous API path fast.

---

## 7. Long-Running Operations

### Q28. Your integration calls an ERP that takes 4 minutes. Design the API.
`[HARD — Tier 2, very likely]`

**Answer:** Asynchronous Request-Reply. The client `POST`s, you return `202 Accepted` immediately with a `Location` pointing to an operation resource and a `Retry-After` hint. The client polls that operation URI; while running it returns `200` with `status: running` and a `Retry-After`; when done it returns `303 See Other` (or `200` with a terminal status plus a link) pointing at the real resource. Optionally, the client registers a webhook so it doesn't have to poll at all.

```http
POST /v1/invoices HTTP/1.1
Idempotency-Key: 2f5a...
--
HTTP/1.1 202 Accepted
Location: /v1/operations/op_9d2c
Retry-After: 10
Operation-Location: /v1/operations/op_9d2c
```
```http
GET /v1/operations/op_9d2c
--
HTTP/1.1 200 OK
Retry-After: 10
{"id":"op_9d2c","status":"running","percentComplete":40,"startedAt":"2026-08-25T09:14:00Z"}
```
```http
GET /v1/operations/op_9d2c
--
HTTP/1.1 200 OK
{"id":"op_9d2c","status":"succeeded","resourceUri":"/v1/invoices/INV-8891",
 "startedAt":"2026-08-25T09:14:00Z","completedAt":"2026-08-25T09:18:11Z"}
```

Azure's own conventions to name: ARM uses `Azure-AsyncOperation` and `Operation-Location` headers, and Cognitive Services uses `Operation-Location`. Durable Functions implements this out of the box — the HTTP starter returns `202` with `statusQueryGetUri`, `terminatePostUri`, `sendEventPostUri`, `purgeHistoryDeleteUri`.

**The forcing constraint:** an HTTP-triggered Azure Function has a **hard 230-second ceiling** to respond, set by the Azure Load Balancer idle timeout, regardless of `functionTimeout` (which defaults to 30 min on Flex Consumption / Premium / Dedicated and is unbounded there; legacy Consumption is 5 min default, 10 max). Logic Apps' outbound HTTP timeout is **120 s multitenant / 225 s single-tenant Standard**. So a 4-minute ERP call *cannot* be synchronous on those hosts. That number is the whole reason the pattern exists — say it.

**If they push back — "why not just hold the connection?"** — Because you burn a gateway connection, a worker slot and a client socket for 4 minutes, you can't scale in without killing in-flight work, and any intermediary — Load Balancer, APIM, corporate proxy — may cut it. Polling makes the work restartable and observable.

---

### Q29. Polling vs webhook vs SSE vs WebSocket — how do you choose?
`[MEDIUM]`

| Mechanism | Direction | Use when | Watch out for |
|---|---|---|---|
| **Polling** | client pulls | Client is behind a firewall / can't host an endpoint; simplest | Wasted calls; needs `Retry-After` discipline |
| **Webhook** | server pushes HTTP | Partner can host an endpoint; low volume, discrete events | Requires HMAC signing, replay protection, retry+DLQ on your side |
| **SSE** | server pushes over one HTTP response | Streaming progress or LLM tokens to a browser; text only, auto-reconnect built in | Proxies buffer it (`X-Accel-Buffering: no`); unidirectional |
| **WebSocket** | bidirectional | Genuinely interactive; GraphQL subscriptions (`graphql-ws`) | Stateful — breaks the "no affinity" property; APIM caps **5,000 active WS connections per unit** |

```python
# SSE from FastAPI — the shape you already know from LLM streaming
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def progress(op_id: str):
    for pct in range(0, 101, 20):
        yield f"event: progress\ndata: {{\"operationId\":\"{op_id}\",\"percent\":{pct}}}\n\n"
        await asyncio.sleep(1)
    yield 'event: done\ndata: {"status":"succeeded"}\n\n'

@app.get("/v1/operations/{op_id}/stream")
async def stream(op_id: str) -> StreamingResponse:
    return StreamingResponse(
        progress(op_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
```

**If they push back — "how do you secure a webhook?"** — HMAC-SHA256 over the raw body with a shared secret, sent in a signature header alongside a timestamp; the receiver recomputes, compares in constant time, and rejects anything older than ~5 minutes to stop replay. Plus an `id` on every event so the receiver can dedupe. Then treat delivery like a queue: retry with backoff, dead-letter after N attempts, expose a redelivery endpoint.

---

### Q30. Write the webhook signature verification.
`[MEDIUM]`

```python
import hashlib
import hmac
import time
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
SECRET = b"whsec_9f2a..."           # from Key Vault, never in code
TOLERANCE_SECONDS = 300

@router.post("/webhooks/orders")
async def receive(request: Request) -> dict:
    raw = await request.body()                      # RAW bytes — never re-serialise the parsed JSON
    ts = request.headers.get("X-Signature-Timestamp", "")
    sig = request.headers.get("X-Signature", "")
    if not ts.isdigit() or abs(time.time() - int(ts)) > TOLERANCE_SECONDS:
        raise HTTPException(status_code=400, detail="stale or missing timestamp")
    expected = hmac.new(SECRET, f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=401, detail="bad signature")
    event = await request.json()
    if already_processed(event["id"]):              # idempotent consumer, see Q14
        return {"status": "duplicate-ignored"}
    enqueue(event)                                   # ack fast, process off the request path
    return {"status": "accepted"}
```

Three things that make this senior: signing the **raw body** (re-serialising changes key order and whitespace and breaks the HMAC), the **timestamp in the signed payload** (otherwise a captured request is replayable forever), and `compare_digest` (constant-time — a naive `==` is a timing oracle).

**If they push back — "why enqueue instead of processing inline?"** — Because the sender's retry policy is not yours. If you take 8 seconds to process and their timeout is 5, they retry, and you process twice. Ack in under a second, then process from a queue with your own retry and DLQ.

---

### Q31. How do you correlate a request across APIM → Function → Service Bus → Logic App?
`[HARD]`

**Answer:** One correlation ID, propagated as W3C Trace Context (`traceparent`), stamped on every hop, and emitted into Application Insights as `operation_Id`. At the gateway I generate it if absent; each downstream hop reads it, logs it, and passes it on; the async legs carry it as a message property so the trace survives the queue.

```xml
<!-- APIM inbound: ensure a correlation id exists and is visible everywhere -->
<inbound>
    <base />
    <set-variable name="correlationId"
                  value="@(context.Request.Headers.GetValueOrDefault("X-Correlation-Id", context.RequestId.ToString()))" />
    <set-header name="X-Correlation-Id" exists-action="override">
        <value>@((string)context.Variables["correlationId"])</value>
    </set-header>
    <trace source="orders-api" severity="information">
        <message>@("inbound " + context.Request.Method + " " + context.Request.Url.Path)</message>
        <metadata name="correlationId" value="@((string)context.Variables["correlationId"])" />
        <metadata name="subscriptionId" value="@(context.Subscription?.Id ?? "anon")" />
    </trace>
</inbound>
<outbound>
    <base />
    <set-header name="X-Correlation-Id" exists-action="override">
        <value>@((string)context.Variables["correlationId"])</value>
    </set-header>
</outbound>
```

Specifics worth quoting: APIM diagnostic logs capture at most **8,192 bytes** of request/response payload; Logic Apps `trackedProperties` is capped at **8,000 characters** per action and is the mechanism for pushing business identifiers into telemetry. Microsoft's own MCP guidance says to *"include correlation IDs in request headers to track requests across multiple systems and components."*

**If they push back — "show me the KQL"** —

```kusto
requests
| where timestamp > ago(24h)
| where customDimensions["correlationId"] == "8b1d...":
| project timestamp, name, resultCode, duration, cloud_RoleName, operation_Id
| union (dependencies | where operation_Id in ((requests | where customDimensions["correlationId"] == "8b1d..." | project operation_Id)))
| order by timestamp asc
```

---

## 8. Errors — RFC 9457 Problem Details

### Q32. How do you design API errors?
`[MEDIUM — near-certain]`

**Answer:** One machine-readable envelope for every error, on every endpoint, using **RFC 9457 Problem Details** with media type `application/problem+json`. Five standard members — `type` (a URI identifying the problem class, defaulting to `about:blank`), `title`, `status`, `detail`, `instance` — plus domain-specific extension members. RFC 9457 **obsoletes RFC 7807**; if you say 7807 in an interview, immediately add "now 9457" so they know you're current.

```json
{
  "type": "https://api.example.com/problems/insufficient-stock",
  "title": "Insufficient stock",
  "status": 409,
  "detail": "Order line 2 requests 40 units of SKU-8891; 12 are available.",
  "instance": "/v1/orders/01J8XZQ4M7K3TR5S9WBYE2N6HD",
  "correlationId": "8b1d1b3f-4c2f-4a1e-9d0d-6d2f7b1b0a11",
  "invalidParams": [
    {"name": "lines[2].quantity", "reason": "exceeds available stock", "available": 12}
  ]
}
```

Rules the spec actually imposes: `type` defaults to `about:blank` when absent; clients **MUST ignore extension members they don't recognise** (that's how you evolve errors safely); extension names should start with a letter, use only alphanumerics and underscores, and be at least three characters, for XML compatibility (`application/problem+xml` is the XML sibling).

House rules I add: `type` URIs are stable and documented (they are the contract; `title` and `detail` are for humans and may change); `detail` never contains a stack trace, a SQL fragment, or an internal hostname; every error carries the correlation ID so support can find it in one KQL query.

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()
BASE = "https://api.example.com/problems"

def problem(status: int, title: str, detail: str, request: Request, **ext) -> JSONResponse:
    body = {
        "type": f"{BASE}/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
        "correlationId": request.headers.get("X-Correlation-Id", "-"),
        **ext,
    }
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json")

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem(
        422, "Unprocessable Content", "The request body failed schema validation.", request,
        invalidParams=[
            {"name": ".".join(str(p) for p in e["loc"][1:]), "reason": e["msg"]}
            for e in exc.errors()
        ],
    )

@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    titles = {401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
              409: "Conflict", 415: "Unsupported Media Type", 429: "Too Many Requests"}
    return problem(exc.status_code, titles.get(exc.status_code, "Error"), str(exc.detail), request)

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    # log exc with the correlation id; do NOT leak it to the caller
    return problem(500, "Internal Server Error",
                   "An unexpected error occurred. Quote the correlationId to support.", request)
```

**If they push back — "isn't a `type` URI overkill?"** — It's the only part of the error a client can safely branch on. Status codes are too coarse (twelve different things return 409) and `title` strings get reworded by a copywriter. The URI doesn't have to resolve, but it should — a docs page per problem type is genuinely useful to partners.

---

### Q33. How do you return a consistent error envelope from the gateway, not just the service?
`[HARD — this is the integration-dev version of the question]`

**Answer:** With an `on-error` section in APIM, so gateway-generated failures (JWT rejected, rate limit, backend timeout, circuit breaker open) look identical to service-generated ones. Otherwise your partner sees RFC 9457 from the service and a raw APIM XML/JSON blob from the gateway, and their error handling breaks on the case that matters most.

```xml
<policies>
    <inbound><base /></inbound>
    <backend><base /></backend>
    <outbound><base /></outbound>
    <on-error>
        <base />
        <set-header name="Content-Type" exists-action="override">
            <value>application/problem+json</value>
        </set-header>
        <set-body>@{
            var status = context.Response?.StatusCode ?? 500;
            var reason = context.LastError?.Reason ?? "Unknown";
            var message = context.LastError?.Message ?? "Gateway error";
            var problem = new JObject(
                new JProperty("type", "https://api.example.com/problems/gateway-" + reason.ToLower()),
                new JProperty("title", reason),
                new JProperty("status", status),
                new JProperty("detail", message),
                new JProperty("instance", context.Request.Url.Path),
                new JProperty("correlationId", context.RequestId.ToString())
            );
            return problem.ToString();
        }</set-body>
    </on-error>
</policies>
```

`context.LastError` exposes `Source`, `Reason`, `Message`, `Scope`, `Section`, `Path`, `PolicyId` — that's how you distinguish "the `validate-jwt` policy rejected it" from "the backend timed out."

**If they push back — "does `on-error` fire for a 500 from the backend?"** — No. `on-error` fires when a *policy* throws or the gateway itself fails (timeouts, connection errors, policy validation failures). A clean HTTP 500 from a reachable backend flows through `outbound` normally. To normalise backend 5xx as well, add a `<choose>` in `outbound` on `context.Response.StatusCode >= 500`.

---

### Q34. What should never appear in an error response?
`[EASY]`

**Answer:** Stack traces, SQL text, internal hostnames or IPs, connection strings, framework version banners, the raw backend error body, and PII in `detail`. Everything sensitive goes to the log correlated by ID; the caller gets the ID.

Concretely, on the way out I strip: `X-Powered-By`, `Server`, `X-AspNet-Version`, `X-AspNetMvc-Version`.

```xml
<outbound>
    <base />
    <set-header name="X-Powered-By" exists-action="delete" />
    <set-header name="X-AspNet-Version" exists-action="delete" />
    <set-header name="Server" exists-action="delete" />
    <set-header name="Strict-Transport-Security" exists-action="override">
        <value>max-age=31536000; includeSubDomains</value>
    </set-header>
    <set-header name="X-Content-Type-Options" exists-action="override">
        <value>nosniff</value>
    </set-header>
</outbound>
```

**If they push back — "the client needs the backend's error to debug"** — Then give it to them in a non-production environment, behind a header the gateway only honours for a specific subscription. Never by default, and never in prod.

---

## 9. CORS, Caching, Compression

### Q35. Walk me through what happens in a CORS preflight.
`[MEDIUM]`

> **Answer:** CORS is a browser mechanism. When JavaScript on `https://portal.contoso.com` calls `https://api.contoso.com`, the browser decides whether to hand the response back to the script — and for anything beyond a trivially simple request it asks permission first with an `OPTIONS` preflight carrying `Origin`, `Access-Control-Request-Method` and `Access-Control-Request-Headers`. My server answers with `Access-Control-Allow-Origin/-Methods/-Headers` and an `Access-Control-Max-Age` so the browser caches that permission instead of re-asking on every call. The single most important thing to say out loud is that **CORS is not a security control on my API** — it constrains browsers only.

**Simple vs preflighted.** A request skips preflight only if *all* of these hold (WHATWG Fetch):

- method is `GET`, `HEAD` or `POST`;
- every author-set header is CORS-safelisted: `Accept`, `Accept-Language`, `Content-Language`, `Content-Type`, `Range`;
- if `Content-Type` is set, it parses to `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain`;
- no upload progress listeners, no `ReadableStream` body.

Two consequences that decide every real API:

1. **`Content-Type: application/json` is not safelisted.** Every JSON POST preflights.
2. **`Authorization` is not safelisted.** Every bearer-token call preflights, including `GET`.

So for a normal token-authenticated JSON API, *every* endpoint preflights. Budget for it.

**The wire trace:**

```http
OPTIONS /v1/orders HTTP/1.1
Host: api.contoso.com
Origin: https://portal.contoso.com
Access-Control-Request-Method: PATCH
Access-Control-Request-Headers: authorization,content-type,if-match,idempotency-key
```

```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://portal.contoso.com
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type, If-Match, Idempotency-Key
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 7200
Vary: Origin
```

**`Access-Control-Max-Age` — the real numbers.** Per MDN, the default when the header is absent is **5 seconds**. Browsers clamp it: **Chromium caps at 7200s (2 hours)** since v76 (it was 600s before), **Firefox caps at 86400s (24 hours)**. Sending `Access-Control-Max-Age: 86400` is therefore honest but Chrome will silently treat it as 7200. Sending nothing means a preflight on effectively every request — that is a doubling of request count against your gateway and a straight hit on p95 for the SPA.

**Exposing custom response headers.** Script can read only the CORS-safelisted *response* headers by default: `Cache-Control`, `Content-Language`, `Content-Length`, `Content-Type`, `Expires`, `Last-Modified`, `Pragma`. Everything your API actually signals with — `ETag`, `Location`, `Retry-After`, `RateLimit-Remaining`, `X-Correlation-Id`, `Deprecation`, `Sunset` — is invisible to the browser unless you list it:

```http
Access-Control-Expose-Headers: ETag, Location, Retry-After, RateLimit-Remaining, X-Correlation-Id
```

This is the bug that makes optimistic concurrency (§3, `If-Match`) mysteriously fail from a browser and work from Postman: the SPA never received the `ETag` it was supposed to echo back.

**If they push back — "why not just allow `OPTIONS` through to the backend?"** — Because preflight is unauthenticated by definition: the browser will not attach the `Authorization` header to an `OPTIONS`. If your backend requires auth it will answer `401` and the browser aborts before the real request ever leaves. Preflight has to be terminated at the gateway, ahead of `validate-jwt`. In APIM this is automatic — the docs state that only the `cors` policy is evaluated on the preflight `OPTIONS`; the rest of the pipeline runs on the approved request. In FastAPI, `CORSMiddleware` must sit outside your auth dependency, which it does by construction since middleware runs before routing.

---

### Q36. Why can't you use `Access-Control-Allow-Origin: *` with credentials, and how do you configure CORS properly?
`[MEDIUM — high hit rate]`

> **Answer:** Because the wildcard means "any website may read this", and credentials mean "the browser will attach the user's cookies or auth automatically". Combined, any site on the internet could silently issue authenticated requests as your logged-in user and read the responses — so the Fetch spec makes the browser reject the response outright when `Access-Control-Allow-Origin: *` meets a credentialed request. The correct pattern is an explicit allow-list, echoing back the single matching origin and adding `Vary: Origin` so caches don't cross-serve it.

The subtle part: with `credentials: "include"`, the wildcard is not honoured *anywhere* — `Access-Control-Allow-Headers: *` and `Access-Control-Expose-Headers: *` also stop meaning "all" and get compared as the literal string `*`. So a credentialed API must enumerate everything.

**The dangerous non-fix.** People "solve" this by reflecting whatever arrived in `Origin`:

```python
# NEVER DO THIS
response.headers["Access-Control-Allow-Origin"] = request.headers["origin"]
response.headers["Access-Control-Allow-Credentials"] = "true"
```

That is a wildcard with extra steps, and it is a real vulnerability class — any origin now reads authenticated responses. If you must be dynamic, match against a compiled allow-list and fail closed. Also beware sloppy suffix matching: `origin.endswith("contoso.com")` is defeated by `https://evil-contoso.com`.

**FastAPI, done correctly:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://portal.contoso.com",
        "https://portal-uat.contoso.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=[
        "Authorization", "Content-Type", "If-Match",
        "If-None-Match", "Idempotency-Key", "X-Correlation-Id",
    ],
    expose_headers=[
        "ETag", "Location", "Retry-After",
        "RateLimit-Remaining", "X-Correlation-Id",
    ],
    max_age=7200,
)
```

Never pair `allow_origins=["*"]` with `allow_credentials=True`. If your SPA is token-in-header rather than cookie-based, you often do not need credentials at all — drop `allow_credentials` and the whole class of problems goes away.

**APIM, done correctly** — and this is the platform answer, because CORS belongs at the paved-road edge, not re-implemented in every microservice:

```xml
<policies>
    <inbound>
        <!-- cors MUST be the first policy in inbound; generally only the first cors policy applies -->
        <cors allow-credentials="true" terminate-unmatched-request="true">
            <allowed-origins>
                <origin>https://portal.contoso.com</origin>
                <origin>https://portal-uat.contoso.com</origin>
            </allowed-origins>
            <allowed-methods preflight-result-max-age="7200">
                <method>GET</method>
                <method>POST</method>
                <method>PATCH</method>
                <method>DELETE</method>
            </allowed-methods>
            <allowed-headers>
                <header>authorization</header>
                <header>content-type</header>
                <header>if-match</header>
                <header>if-none-match</header>
                <header>idempotency-key</header>
                <header>ocp-apim-subscription-key</header>
            </allowed-headers>
            <expose-headers>
                <header>etag</header>
                <header>location</header>
                <header>retry-after</header>
                <header>ratelimit-remaining</header>
                <header>x-correlation-id</header>
            </expose-headers>
        </cors>
        <base />
        <validate-jwt header-name="Authorization" failed-validation-httpcode="401" />
    </inbound>
</policies>
```

Verified against the APIM `cors` policy reference: `allow-credentials` defaults to `false`; `preflight-result-max-age` defaults to **0**; `terminate-unmatched-request` defaults to `false`; the policy runs in **inbound** only, at global / workspace / product / API / operation scope, and can appear once per section. Two documented gotchas worth quoting in the interview: if you set `cors` at **product** scope and your API authenticates with a subscription key **in a header**, it will not work (the key must move to a query parameter); and if you set it at **API** scope with **header-based versioning**, it will not work either — because the preflight `OPTIONS` carries neither.

**The framing that wins the question:**

> "CORS protects the *user's browser session*, not my API. `curl`, Postman, a Python `httpx` client, a partner's Java integration, a server-side SSRF — none of them send `Origin`, none of them honour `Access-Control-Allow-Origin`. If my only defence against an unauthorised caller is CORS, I have no defence. The controls that actually protect the API are authn/authz, rate limits, IP restrictions and mTLS — CORS just decides which *web pages* are allowed to spend the user's credentials on my behalf."

**If they push back — "so a locked-down CORS policy buys nothing?"** — It buys exactly one thing, and it is worth having: it stops a malicious page from riding a logged-in user's ambient credentials. That is a real attack (it's the read-the-response half of CSRF). It is just not perimeter security, and I would fail a design review that listed CORS under "API security controls" without `validate-jwt`, rate limiting and WAF above it. See [Auth](06-auth-and-security.md) for the controls that do the work.

---

### Q37. How do you do HTTP caching for an API — ETag, Last-Modified, Cache-Control?
`[MEDIUM]`

> **Answer:** Two mechanisms that compose. `Cache-Control` handles *freshness* — how long a response may be reused without asking. Validators (`ETag`, `Last-Modified`) handle *revalidation* — when it goes stale, the client re-asks with `If-None-Match`/`If-Modified-Since` and I answer `304 Not Modified` with no body. Freshness saves the round trip; validators save the payload and the backend work. On a financial-services API I default to `private, no-store` for anything account- or position-specific and reserve real caching for reference data — instruments, calendars, FX rates, country and fee tables.

**Cache-Control directives you must be able to distinguish** (RFC 9111 §5.2.2, June 2022):

| Directive | Meaning | Where I use it |
|---|---|---|
| `max-age=N` | Fresh for N seconds in **any** cache | Reference data |
| `s-maxage=N` | Overrides `max-age` in **shared** caches only | Longer TTL at APIM/CDN, shorter in the browser |
| `no-store` | Cache MUST NOT store any part of request or response | PII, positions, statements, tokens |
| `no-cache` | May be stored, but MUST be revalidated before reuse | Cheap 304s on volatile data |
| `private` | Shared caches MUST NOT store; browser may | Per-user responses |
| `public` | May be stored even when heuristics say otherwise (e.g. `Authorization` present) | Reference data behind auth |
| `must-revalidate` | Once stale, MUST NOT be served without origin validation | Anything where stale is wrong, not just old |
| `proxy-revalidate` | `must-revalidate` for shared caches only | Gateway tier |
| `immutable` (RFC 8246) | Content will not change during freshness — skip revalidation on reload | Versioned static assets, not APIs |
| `stale-while-revalidate=N` (RFC 5861) | Serve stale up to N seconds while refreshing in background, non-blocking | Reference data — kills the latency cliff at TTL expiry |
| `stale-if-error=N` (RFC 5861) | Serve stale up to N seconds when the origin returns 500/502/503/504 | Availability cushion over a flaky legacy backend |

`no-store` vs `no-cache` is the classic trap: **`no-cache` still writes to disk.** For anything a compliance auditor cares about it is `no-store`, and if the response is genuinely secret, `Cache-Control: no-store` plus `Pragma: no-cache` for prehistoric intermediaries.

**Strong vs weak validators.** `ETag: "a1b2"` is strong — it changes if a single byte changes. `ETag: W/"a1b2"` is weak — it means "semantically equivalent", so the server may keep it stable across cosmetic changes (whitespace, key order, a re-serialised timestamp). The rule that matters: **`If-Match` and `If-Range` require a strong comparison**, so a weak ETag cannot be used for optimistic concurrency or for range requests. `If-None-Match` uses weak comparison and works with both. If you use ETags for concurrency control — and you should, see §3 — emit **strong** ETags.

`Last-Modified`/`If-Modified-Since` has one-second granularity, so two writes in the same second are indistinguishable and a client can cache a stale representation forever. Use it as a fallback for clients that only speak it, never as your primary validator.

**FastAPI, real:**

```python
import hashlib
import json
from fastapi import FastAPI, HTTPException, Request, Response

app = FastAPI()

CACHE_POLICY = "public, max-age=300, s-maxage=900, stale-while-revalidate=60, stale-if-error=86400"


def strong_etag(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return '"' + hashlib.sha256(canonical).hexdigest()[:32] + '"'


def etag_matches(if_none_match: str, etag: str) -> bool:
    if if_none_match.strip() == "*":
        return True
    for tag in if_none_match.split(","):
        tag = tag.strip()
        if tag.startswith("W/"):
            tag = tag[2:]
        if tag == etag:          # weak comparison: W/ prefix ignored on both sides
            return True
    return False


@app.get("/v1/instruments/{isin}")
def get_instrument(isin: str, request: Request, response: Response):
    doc = instrument_repo.get(isin)
    if doc is None:
        raise HTTPException(status_code=404, detail="Unknown ISIN")

    etag = strong_etag(doc)
    common = {
        "ETag": etag,
        "Cache-Control": CACHE_POLICY,
        "Vary": "Accept, Accept-Encoding, Origin",
    }

    if etag_matches(request.headers.get("if-none-match", ""), etag):
        # 304 MUST NOT carry a body, and MUST carry the validator + freshness info
        return Response(status_code=304, headers=common)

    response.headers.update(common)
    return doc
```

**`Vary` is the header everyone forgets.** It tells shared caches which request headers form part of the cache key. Omit `Vary: Accept-Encoding` and a gateway will hand a brotli-compressed body to a client that only speaks gzip. Omit `Vary: Origin` when you reflect origins and cache A's `Access-Control-Allow-Origin` gets served to B. Add `Vary: Authorization` and you have made the response per-user, which is usually a sign you should have said `private` instead. `Vary: *` means "never reusable".

**If they push back — "why not just set short TTLs everywhere?"** — Because short TTLs solve staleness by re-fetching the full payload; validators solve it by re-fetching 200 bytes of headers. On a 400 KB instrument-reference response at 50 rps, `no-cache` + ETag turns ~20 MB/s of egress into near zero while keeping the data provably current. And `stale-while-revalidate` is what stops every client stampeding the origin at the same instant when a 300-second TTL expires — without it, TTL expiry *is* your thundering-herd generator.

---

### Q38. This API sits behind APIM. What's your caching strategy, and how do you invalidate?
`[HARD — the platform-engineer version]`

> **Answer:** I cache at the gateway, not in each service, so the paved road gives every team caching without code. In APIM that is `cache-lookup` in inbound plus `cache-store` in outbound, keyed by the query parameters and headers that actually change the representation. Invalidation is the hard half: I use short TTLs plus validators as the default, an explicit `cache-remove-value` purge on the write path where correctness demands it, and a version-key indirection when a single write invalidates a whole family of cached responses.

**The policy, with the details that matter:**

```xml
<policies>
    <inbound>
        <base />
        <cache-lookup vary-by-developer="false"
                      vary-by-developer-groups="false"
                      caching-type="prefer-external"
                      downstream-caching-type="public"
                      must-revalidate="true"
                      allow-private-response-caching="false">
            <vary-by-header>Accept</vary-by-header>
            <vary-by-header>Accept-Charset</vary-by-header>
            <vary-by-header>Accept-Encoding</vary-by-header>
            <vary-by-query-parameter>asOfDate</vary-by-query-parameter>
            <vary-by-query-parameter>currency</vary-by-query-parameter>
        </cache-lookup>
        <!-- documented recommendation: rate-limit immediately AFTER cache-lookup, so a
             cache outage cannot turn into a backend stampede -->
        <rate-limit-by-key calls="200" renewal-period="60"
                           counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)" />
    </inbound>
    <backend><base /></backend>
    <outbound>
        <!-- honour the backend's own max-age, default 300s -->
        <cache-store duration="@{
            var header = context.Response.Headers.GetValueOrDefault("Cache-Control", "");
            var maxAge = Regex.Match(header, @"max-age=(?<maxAge>\d+)").Groups["maxAge"]?.Value;
            return (!string.IsNullOrEmpty(maxAge)) ? int.Parse(maxAge) : 300;
        }" />
        <base />
    </outbound>
</policies>
```

Facts to state precisely, because they are the ones interviewers check:

- **APIM performs cache lookup for HTTP `GET` requests only.** Do not promise cached `POST` search endpoints.
- **The built-in cache is volatile and is shared by all units in the same region in the same APIM instance.** It is not a durable store and it is not cross-region.
- **Internal caching is not available in the Consumption tier** — attach an external Redis-compatible cache instead (also available in every other tier, and the right answer for multi-region or larger working sets).
- `caching-type` defaults to `prefer-external` (external if configured, otherwise internal). `downstream-caching-type` defaults to `none`; `must-revalidate` defaults to `true`; `allow-private-response-caching` defaults to `false` — set it `true` only if you have thought hard about caching responses that carry `Authorization`, and then you must also `vary-by-header` on `Authorization`.
- **Cache failures are silent.** The docs are explicit: if a cache operation cannot connect, the API call does not raise — a read simply returns null to the policy expression. Your policy must have a fallback path; never write a policy that assumes a hit.
- `cache-lookup` can appear once per section and is **not supported inside a policy fragment** — so your golden template puts it in the API-scope policy, not the shared fragment.

**Cache key design.** The key is method + URL + the `vary-by-*` you declare. Two failure modes: over-keying (include a `X-Correlation-Id` and your hit rate is 0%) and under-keying (omit `currency` and you serve GBP prices to a USD caller). Note the documented interaction: when you `vary-by-query-parameter`, declare those parameters in the `rewrite-uri` template or set `copy-unmatched-params="false"`, otherwise undeclared parameters still reach the backend and your key does not describe the response.

**Invalidation — four strategies, in the order I reach for them:**

| Strategy | How | When |
|---|---|---|
| **TTL only** | `cache-store duration="60"` | Reference data where 60s of staleness is a business non-issue. Simplest thing that works; defend it. |
| **TTL + validator** | Short `s-maxage` + ETag; gateway revalidates | Volatile data where correctness matters and payload is large |
| **Explicit purge on write** | `cache-remove-value` in the write operation's outbound | Small blast radius, one key per entity |
| **Version-key indirection** | Cache under `v{n}:...`; bump `n` in a cached value on write | One write invalidates a family (e.g. a fee-schedule change invalidates every `/fees?*`) |

Explicit purge and the version key both use APIM's key-value cache policies rather than the response cache:

```xml
<!-- on POST/PUT/PATCH/DELETE /v1/instruments/{isin}: drop the entity's cached value -->
<outbound>
    <base />
    <choose>
        <when condition="@(context.Response.StatusCode >= 200 && context.Response.StatusCode < 300)">
            <cache-remove-value key="@("instrument|" + context.Request.MatchedParameters["isin"])"
                                caching-type="prefer-external" />
            <cache-remove-value key="@("fee-schedule-version")" caching-type="prefer-external" />
        </when>
    </choose>
</outbound>
```

```xml
<!-- cache an expensive derived value (or a legacy SOAP session token) under your own key -->
<inbound>
    <base />
    <cache-lookup-value key="soap-session-token" variable-name="soapToken" caching-type="prefer-external" />
    <choose>
        <when condition="@(!context.Variables.ContainsKey("soapToken"))">
            <send-request mode="new" response-variable-name="loginResponse" timeout="20" ignore-error="false">
                <set-url>https://legacy.contoso.com/AuthService.svc</set-url>
                <set-method>POST</set-method>
                <set-header name="Content-Type" exists-action="override">
                    <value>text/xml; charset=utf-8</value>
                </set-header>
                <set-header name="SOAPAction" exists-action="override">
                    <value>http://contoso.com/IAuthService/Login</value>
                </set-header>
                <set-body>@("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><Login xmlns=\"http://contoso.com/\"><user>svc-apim</user></Login></soap:Body></soap:Envelope>")</set-body>
            </send-request>
            <set-variable name="soapToken"
                          value="@(((IResponse)context.Variables["loginResponse"]).Body.As<JObject>()["token"].ToString())" />
            <cache-store-value key="soap-session-token"
                               value="@((string)context.Variables["soapToken"])"
                               duration="1500" caching-type="prefer-external" />
        </when>
    </choose>
    <set-header name="X-Session-Token" exists-action="override">
        <value>@((string)context.Variables["soapToken"])</value>
    </set-header>
</inbound>
```

That last block is a genuinely common integration pattern and pairs directly with §12 — a legacy SOAP backend issues a 30-minute session token, and you cache it at the gateway with a TTL safely inside its lifetime (1500s < 1800s) rather than logging in on every call.

**If they push back — "how do you cache a per-user response safely?"** — I usually don't. `private` plus a validator pushes it to the browser where it belongs, and the gateway does revalidation only. If I genuinely need shared caching of authenticated responses I set `allow-private-response-caching="true"` **and** `<vary-by-header>Authorization</vary-by-header>`, which makes the cache entry per-token — and then I check the hit rate, because per-token entries with 15-minute tokens usually mean I built a memory leak, not a cache. See [System Design](08-system-design-integration.md) for the read-through cache alternative inside the service.

---

### Q39. gzip vs brotli vs zstd — what do you enable, and when is compression a bad idea?
`[MEDIUM]`

> **Answer:** Content negotiation via `Accept-Encoding`: the client advertises what it can decode, I pick the best I support, set `Content-Encoding` and — critically — add `Vary: Accept-Encoding` so no shared cache mis-serves it. For dynamic JSON I use gzip as the universal floor and brotli at a low quality level where the client supports it; brotli at maximum quality is for pre-compressed static assets, not per-request encoding. And I turn compression *off* for already-compressed payloads, tiny bodies, and any response where a compression side-channel could leak a secret.

| Coding | Token | Spec | Character |
|---|---|---|---|
| gzip | `gzip` | RFC 1952 (DEFLATE, RFC 1951) | Universal. Every client, every proxy, every legacy Java stack. The floor. |
| Brotli | `br` | RFC 7932 (July 2016) | ~15–20% smaller than gzip on text at comparable CPU when tuned low; quality 0–11. Level 11 is far too slow for dynamic responses — use 4–5 dynamic, 11 for precompressed static. TLS-only in browsers. |
| Zstandard | `zstd` | RFC 8878 (Feb 2021) | Best ratio-per-CPU of the three, very fast decode, wide level range. Registered as an HTTP content coding; browser support is newer than `br`, so treat it as opportunistic, not a floor. |
| identity | `identity` | RFC 9110 | No encoding. What you send when compression is wrong. |

**Negotiation, precisely.** `Accept-Encoding: br;q=1.0, gzip;q=0.8, *;q=0.1` — q-values rank preference; `identity;q=0` means "do not send uncompressed"; `*` covers the rest. The server chooses, echoes `Content-Encoding: br`, and **must** emit `Vary: Accept-Encoding`. Note the ordering rule that trips people up: `Content-Encoding` is applied *before* transfer, so `Content-Length` describes the **compressed** length; if you also do range requests, ranges apply to the encoded bytes.

**When compression is counterproductive:**

- **Already-compressed payloads.** JPEG/PNG/WebP, MP4, ZIP/GZ, PDFs with embedded compressed streams, Parquet/Avro with Snappy inside. MDN states it plainly: compressing already-compressed media "is usually not appropriate because it can increase the file size." You burn CPU and add bytes.
- **Tiny bodies.** Below roughly 1 KB the gzip header, dictionary warm-up and framing overhead eat the gain; common gateway defaults sit around 860–1400 bytes as the minimum. A 200-byte `204`-ish JSON acknowledgement should never be compressed.
- **Latency-sensitive streaming.** Compressing an SSE or chunked stream forces buffering to fill a compression window — you trade first-byte latency for bytes. Either flush per event (losing most of the ratio) or don't compress.
- **CPU-bound gateways.** Brotli 11 on a per-request path is the classic self-inflicted outage. If you want the ratio, precompress at build time and serve the `.br` file.
- **Already-encrypted-then-compressed.** Compress *before* encrypt, never after — post-encryption data is incompressible by design.

**BREACH — the answer that marks you senior.** BREACH is a compression side-channel against HTTPS responses. If a single response body contains (a) a secret — a CSRF token, an anti-forgery token, a session identifier, an account number — and (b) attacker-controlled input that is reflected back, and (c) the body is compressed, then the attacker can vary their input and watch the *compressed response length*: when their guess matches part of the secret, the compressor deduplicates and the response gets shorter. Repeat character by character and the secret falls out, through TLS, without breaking any crypto. (CRIME was the earlier, TLS/header-compression variant; HTTP/2's HPACK is why you never put secrets in headers you also let attackers influence.)

Practical mitigations, in the order I'd apply them:

1. Do not reflect attacker-controlled input into a response that also contains a secret. This is the actual fix.
2. Disable compression selectively for those responses (`Cache-Control: no-store` endpoints returning tokens — turn off `Content-Encoding` too).
3. Randomise the secret per response (mask CSRF tokens with a fresh random pad each time) so the compressor cannot correlate.
4. Add random-length padding to the response — mitigates, doesn't cure, and costs bytes.
5. Rate-limit and alert on the request pattern: BREACH needs thousands of near-identical requests, which is exactly what `rate-limit-by-key` catches.

For a typical bearer-token JSON API the exposure is lower than for cookie-authenticated HTML — there's no ambient credential and usually no reflected input — but "lower" is not "none": an error response that echoes a user-supplied `filter` query parameter *and* includes an account identifier is the same shape.

**If they push back — "where do you actually terminate compression?"** — At the edge, once. Gateway or ingress compresses on the way out; the backend hop stays uncompressed (or gzip if it's a fat payload over a slow link). Compressing in the service *and* at the gateway means either double-encoding bugs or wasted CPU decompressing to recompress. What I do put in the golden template is the `Vary: Accept-Encoding` header and a minimum-size threshold, because those are the two things every team forgets. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md) for how that template gets enforced.

---

## 10. HTTP/1.1 vs HTTP/2 vs HTTP/3 vs gRPC

### Q40. Explain the difference between HTTP/1.1, HTTP/2 and HTTP/3.
`[MEDIUM — extremely common]`

> **Answer:** They differ in how many requests can share a connection and where head-of-line blocking lives. HTTP/1.1 sends one request at a time per connection with plain-text headers repeated in full, so clients open six connections per origin to fake concurrency. HTTP/2 multiplexes many streams over one TCP connection with binary framing and HPACK header compression — it removes head-of-line blocking at the HTTP layer but not at the TCP layer, so one lost packet still stalls every stream. HTTP/3 moves onto QUIC over UDP, where streams are independent at the transport layer, which finally kills transport-level head-of-line blocking and folds the TLS handshake into the transport.

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Spec | RFC 9112 | **RFC 9113** (June 2022, obsoletes 7540 + 8740) | **RFC 9114** (June 2022) |
| Transport | TCP | TCP | **QUIC** — RFC 9000 (May 2021), over UDP |
| Framing | Text | Binary frames, streams | Binary frames on QUIC streams |
| Concurrency | 1 in flight per conn (pipelining broken in practice) → ~6 conns/origin | Many streams, 1 conn | Many streams, 1 conn, independent |
| Header compression | none | **HPACK** (RFC 7541) | **QPACK** (RFC 9204) |
| HOL blocking | HTTP-level **and** TCP-level | TCP-level only | neither |
| TLS | separate handshake (TLS 1.2/1.3) | separate handshake | integrated, TLS 1.3 mandatory |
| Handshake | TCP 1-RTT + TLS 1–2 RTT | same | 1-RTT, or **0-RTT** on resumption |

**HTTP/1.1 keep-alive.** Persistent connections are the default in 1.1 (`Connection: close` opts out). Keep-alive removes the TCP+TLS handshake per request but not the serialisation: response *n* must complete before response *n+1* starts on that connection. Pipelining was specified to fix that and is effectively unusable because a slow first response blocks the rest and buggy intermediaries mis-handle it. Hence six connections per origin, six TLS handshakes, six congestion windows that never warm up.

**HTTP/2 specifics worth naming.** Streams are multiplexed with interleaved binary frames (`HEADERS`, `DATA`, `SETTINGS`, `WINDOW_UPDATE`, `RST_STREAM`). `SETTINGS_MAX_CONCURRENT_STREAMS` — RFC 9113 recommends it be **no smaller than 100** so as not to unnecessarily limit parallelism. Flow control is per-stream and per-connection with an **initial window of 2^16−1 = 65,535 octets**, which is why a naive h2 implementation looks slow on large uploads until you raise it. HPACK maintains a dynamic table of previously-seen header fields, so the 40 repeated headers of a REST API cost a few bytes per request after the first.

**The residual HTTP/2 problem.** All those streams ride one TCP connection, and TCP delivers bytes strictly in order. Lose one segment and the kernel holds back *every* stream's data until it's retransmitted — one slow image blocks your API response. On clean datacentre links this is invisible; on lossy mobile networks it's the dominant effect, and it's precisely why QUIC exists.

**What this means at the integration layer.** The gateway terminates h2/h3 at the edge; the hop to your backend is very often still HTTP/1.1, and that's fine for REST. Where it stops being fine is gRPC, which requires HTTP/2 end to end — so every L7 proxy, ingress and service mesh sidecar on the path must speak h2 with prior knowledge (no upgrade dance), and an L4 load balancer will pin all of a client's multiplexed RPCs to one backend pod. That is the single most common gRPC-in-Kubernetes production surprise; the fix is an L7-aware ingress or client-side load balancing via a headless Service. See [K8s](04-microservices-containers-kubernetes.md).

**If they push back — "is HTTP/2 always faster?"** — No. On a low-loss, high-bandwidth internal link with a handful of large responses, h1.1 keep-alive is competitive and simpler to debug. h2's wins are concentrated where there are many small requests and header overhead dominates, and they invert on lossy links because of the shared-TCP effect. I'd enable h2 at the edge by default and measure rather than assert.

---

### Q41. What was HTTP/2 server push for, and why is it effectively dead?
`[MEDIUM]`

> **Answer:** Server push let a server send a `PUSH_PROMISE` and then a response the client hadn't asked for yet — the idea being to ship the CSS with the HTML and save a round trip. It failed in practice because the server can't know what's already in the client's cache, so it mostly wasted bandwidth pushing things the browser already had, and it was hard to get right. Chrome disabled it by default in **Chrome 106**, other Chromium browsers followed, and the replacement is **103 Early Hints** plus `preload`.

The mechanism is still in RFC 9113 — `PUSH_PROMISE` frames and the `SETTINGS_ENABLE_PUSH` setting are specified and a client may refuse push by setting it to 0 — so "removed from the spec" is wrong and "removed from browsers" is right. HTTP/3 defines push too, and it is equally unused.

**What replaced it.** Chrome's own guidance names two things:

- **`103 Early Hints`** — an informational response the origin can send *before* the final response, listing resources the client may benefit from fetching now. It hints rather than pushes, so the client's cache decides, which is exactly the failure mode push couldn't handle.
- **`<link rel=preload>` / `Link: <...>; rel=preload` headers** — the page and browser cooperate to fetch critical resources early, at the cost of needing the page first.

**Why an integration engineer should still know this.** It is the cleanest available example of "the protocol supported it, the ecosystem rejected it" — and the same reasoning applies to features you *will* be asked to bet a platform on. When someone proposes a capability, ask who else has shipped it, whether intermediaries preserve it, and whether it degrades safely. Push degraded *badly*: proxies, CDNs and corporate middleboxes handled it inconsistently, and a wrong push cost bandwidth on exactly the constrained links it was meant to help.

**If they push back — "so is there any push-like thing you'd use in an API?"** — Yes, but not this. For server-initiated data I use SSE, WebSockets or a webhook depending on direction and durability (§7, Q29), and for event fan-out I use the messaging tier — Service Bus topics or Event Grid — not an HTTP framing trick. See [Messaging](03-messaging-and-event-streaming.md).

---

### Q42. What do 0-RTT and connection migration buy you in HTTP/3, and what's the catch?
`[HARD]`

> **Answer:** 0-RTT lets a returning client send application data in its very first flight using keys cached from a previous session — so a repeat request costs zero handshake round trips instead of the two or three TCP+TLS normally costs. Connection migration means a QUIC connection is identified by a connection ID rather than the four-tuple, so it survives the client's IP or port changing — Wi-Fi to cellular, NAT rebinding, a laptop moving between networks. The catch on 0-RTT is significant: RFC 9000 states plainly that **0-RTT provides no protection against replay attacks**, so 0-RTT data must be limited to safe, idempotent requests.

**Connection migration** (RFC 9000 §9): "Connection migration uses connection identifiers to allow connections to transfer to a new network path." Because packets carry a connection ID the server recognises, a client whose address changes keeps the same connection — no new handshake, no lost congestion-window state, no dropped in-flight requests. For a field-force mobile app hitting your integration APIs from a train, that is the difference between a stalled sync and a seamless one. TCP simply cannot do this; changing IP kills the connection.

**0-RTT and replay.** The transport does not restrict what you send in 0-RTT; it pushes the decision to the application protocol. That means an attacker who captures a 0-RTT flight can resend it, and the server will process it again. Concretely:

- 0-RTT for `GET`/`HEAD` — safe methods (§1, Q3), replay is harmless.
- 0-RTT for `POST /payments` — a replayed packet is a duplicate payment.

So the rule is: **allow 0-RTT for safe methods only, and if you cannot enforce that, disable 0-RTT.** Note the pleasing convergence with §3 — if your `POST` endpoints already require an `Idempotency-Key` and de-duplicate on it, a 0-RTT replay collapses to a cache hit on the idempotency record rather than a second payment. Idempotency is the defence that keeps paying you back at every layer.

**How a client even gets to HTTP/3.** It doesn't guess. Either the origin advertises it over an existing h1/h2 connection with `Alt-Svc: h3=":443"; ma=86400`, or the client resolves an HTTPS/SVCB DNS record carrying `alpn="h3"`. Either way there's a first connection over TCP. That matters operationally, because **QUIC is UDP/443 and plenty of corporate and bank networks block or throttle outbound UDP** — which is exactly the network your financial-services clients sit on. Design for graceful fallback to h2, never require h3, and don't put HTTP/3 on a critical-path SLA without measuring from the client's actual network.

**If they push back — "should we turn on HTTP/3 at our gateway?"** — At the public edge, yes, if the platform offers it as a checkbox: it's a free win for mobile and lossy-network clients and it fails back cleanly. Internally, no — datacentre links have near-zero loss, so QUIC's advantage evaporates while the operational cost is real: UDP is harder to load-balance, harder to capture and read, and your existing L4 tooling, connection-tracking firewalls and packet captures are all TCP-shaped. I'd rather spend that complexity budget on observability. See [System Design](08-system-design-integration.md).

---

### Q43. When would you pick gRPC over REST, and when must you not?
`[HARD — very likely for this role]`

> **Answer:** gRPC for internal, high-throughput, service-to-service calls where I control both ends, want a compiler-enforced contract across languages, and need streaming or tight latency. REST over JSON for anything a partner, a browser, or a human touches. The deciding questions are: who is the client, can they be recompiled when the contract changes, and does anyone need to debug this with curl.

**What gRPC actually is:** Protocol Buffers as the IDL and binary wire format, HTTP/2 as the transport, generated client and server stubs in every supported language, deadlines that propagate across hops, metadata as headers and a status in trailers.

**The four call types — know these cold:**

| Type | Signature in the proto | Use it for |
|---|---|---|
| **Unary** | `rpc Get (Req) returns (Res)` | Normal request/response. 90% of RPCs. |
| **Server streaming** | `rpc Watch (Req) returns (stream Res)` | Large result sets, tailing events, progress on a long job |
| **Client streaming** | `rpc Upload (stream Req) returns (Res)` | Bulk ingest, chunked upload, telemetry batches |
| **Bidirectional** | `rpc Chat (stream Req) returns (stream Res)` | Interactive reconciliation, live pricing, long-lived sessions |

**Pick gRPC when:**

- Internal service-to-service inside the cluster or mesh, both ends yours.
- High call volume where JSON parsing and header bytes are a measurable cost — protobuf is materially smaller and cheaper to parse, and HPACK removes repeated headers.
- Polyglot teams: one `.proto` generates Python, Java, Go, C# clients. The contract is compiled, not documented.
- You need real streaming semantics with flow control, not SSE-with-heartbeats.
- Strict, evolvable contracts matter — field numbers plus `reserved` give you safer evolution than a hand-maintained JSON schema.

**Do not pick gRPC when:**

- **The client is a browser.** Browsers cannot speak gRPC directly. gRPC-Web requires a proxy — Envoy's grpc-web filter is the default; there is also a Go proxy, Apache APISIX support and an nginx module. And gRPC-Web supports **unary** plus **server-streaming (only in `grpcwebtext` mode)**; **client-streaming and bidirectional streaming are not supported**. If your design depends on bidi from a browser, gRPC-Web is not the answer.
- **It's a partner-facing public API.** Partners want an OpenAPI spec, a Postman collection, and curl. Handing an asset manager a `.proto` and telling them to install `protoc` is how integrations don't get delivered.
- **Human debuggability matters more than bytes.** You cannot read a protobuf frame off the wire or from a log. Mitigate with server reflection plus `grpcurl`, but that's a mitigation, not parity.
- **Your edge infrastructure doesn't proxy h2 cleanly.** WAFs, corporate proxies, and some API gateways handle gRPC poorly or not at all — check what your APIM tier/gateway actually supports before you promise gRPC through the public edge *(verify against the current APIM gateway matrix for your tier)*.
- **You need L7 load balancing you don't have.** Long-lived h2 connections plus an L4 balancer = all RPCs pinned to one pod.

**Numbers to quote correctly.** gRPC's default **maximum receive message length is 4 MiB** (`GRPC_DEFAULT_MAX_RECV_MESSAGE_LENGTH = 4 * 1024 * 1024`); the default **max send is `-1`, i.e. unlimited**. That asymmetry is the single most common gRPC production incident — the sender happily sends 8 MB, the receiver rejects with `RESOURCE_EXHAUSTED`. Raise it explicitly on both sides, or better, stream instead of growing the message.

**Contract evolution** (this is the versioning question in gRPC clothing — see §5): field numbers are the contract, not names. Adding a new optional field is backward compatible; removing one requires `reserved 7; reserved "old_field";` so the number is never reused; changing a field's type or number is breaking. Package your proto with a version in the package name (`settlement.v1`) so a genuinely breaking change becomes `settlement.v2` served alongside.

**Error model.** gRPC status codes are not HTTP status codes. Map them deliberately at any REST facade: `INVALID_ARGUMENT`→400, `UNAUTHENTICATED`→401, `PERMISSION_DENIED`→403, `NOT_FOUND`→404, `ALREADY_EXISTS`/`ABORTED`→409, `FAILED_PRECONDITION`→412 or 422, `RESOURCE_EXHAUSTED`→429, `UNIMPLEMENTED`→501, `UNAVAILABLE`→503, `DEADLINE_EXCEEDED`→504. Note `UNAVAILABLE` and `DEADLINE_EXCEEDED` are the retryable ones — the same retry discipline as §3, Q15.

**If they push back — "why not just use REST internally too, for consistency?"** — Often that *is* the right call, and I'd say so: consistency has real value and the paved road should have one default. My rule is that gRPC has to earn its way in with a measured problem — a p99 dominated by serialisation, a fan-out where header bytes matter, or a streaming requirement REST can't express. What I won't do is run two contract ecosystems with no governance: if gRPC is on the paved road it comes with a proto registry, buf lint/breaking checks in CI, and a generated-stub publishing pipeline, exactly like OpenAPI has (§14).

---

### Q44. Show me a gRPC service — the proto and a Python server and client.
`[HARD — coding]`

> **Answer:** One `.proto` defines the service and messages, `grpc_tools.protoc` generates stubs, the server implements the generated servicer base class and the client calls through a channel. I'll show all four call types, deadlines rather than timeouts, explicit message-size limits, TLS, and server reflection so `grpcurl` can debug it.

**`proto/settlement/v1/settlement.proto`**

```proto
syntax = "proto3";

package settlement.v1;

import "google/protobuf/timestamp.proto";

option java_multiple_files = true;
option java_package = "com.contoso.settlement.v1";
option go_package = "github.com/contoso/settlement/gen/v1;settlementv1";

service SettlementService {
  // Unary
  rpc GetInstruction (GetInstructionRequest) returns (Instruction);

  // Server streaming: tail instructions as they settle
  rpc WatchInstructions (WatchInstructionsRequest) returns (stream Instruction);

  // Client streaming: bulk upload from a batch job
  rpc UploadInstructions (stream Instruction) returns (UploadSummary);

  // Bidirectional: interactive break reconciliation
  rpc Reconcile (stream ReconcileRequest) returns (stream ReconcileEvent);
}

enum SettlementStatus {
  SETTLEMENT_STATUS_UNSPECIFIED = 0;   // proto3 requires a zero value; never reuse it
  SETTLEMENT_STATUS_PENDING     = 1;
  SETTLEMENT_STATUS_MATCHED     = 2;
  SETTLEMENT_STATUS_SETTLED     = 3;
  SETTLEMENT_STATUS_FAILED      = 4;
}

message Money {
  string currency_code = 1;   // ISO 4217, e.g. "GBP"
  string amount        = 2;   // decimal STRING, never double — no binary float for money
}

message Instruction {
  string instruction_id                    = 1;
  string isin                              = 2;
  string counterparty_bic                  = 3;
  Money  consideration                     = 4;
  SettlementStatus status                  = 5;
  google.protobuf.Timestamp settlement_date = 6;
  google.protobuf.Timestamp updated_at      = 7;

  reserved 8, 9;                 // retired fields — numbers can never be reused
  reserved "legacy_account_ref";
}

message GetInstructionRequest {
  string instruction_id = 1;
}

message WatchInstructionsRequest {
  string counterparty_bic       = 1;
  SettlementStatus status_filter = 2;
}

message UploadSummary {
  int32 accepted = 1;
  int32 rejected = 2;
  repeated string rejection_reasons = 3;
}

message ReconcileRequest {
  string instruction_id = 1;
  Money  our_amount     = 2;
}

message ReconcileEvent {
  string instruction_id = 1;
  bool   matched        = 2;
  string detail         = 3;
}
```

Two design points to say aloud: **money is a decimal string, never a `double`** — IEEE-754 binary floats cannot represent 0.10 and finance will not forgive you; and every enum has an explicit `_UNSPECIFIED = 0` because proto3 has no field presence for enums, so zero must mean "not set", not "PENDING".

**Generate the stubs:**

```bash
python -m pip install grpcio grpcio-tools grpcio-reflection grpcio-health-checking
python -m grpc_tools.protoc \
  -I proto \
  --python_out=gen \
  --grpc_python_out=gen \
  --pyi_out=gen \
  proto/settlement/v1/settlement.proto
```

**`server.py`**

```python
import logging
import time
from concurrent import futures

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from settlement.v1 import settlement_pb2 as pb
from settlement.v1 import settlement_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("settlement")

_STORE: dict[str, pb.Instruction] = {}


def _now() -> Timestamp:
    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


class SettlementService(pb_grpc.SettlementServiceServicer):

    def GetInstruction(self, request, context):
        instruction = _STORE.get(request.instruction_id)
        if instruction is None:
            context.abort(grpc.StatusCode.NOT_FOUND,
                          f"instruction {request.instruction_id} not found")
        return instruction

    def WatchInstructions(self, request, context):
        seen: set[str] = set()
        while context.is_active():
            for iid, inst in list(_STORE.items()):
                if iid in seen:
                    continue
                if request.counterparty_bic and inst.counterparty_bic != request.counterparty_bic:
                    continue
                if (request.status_filter != pb.SETTLEMENT_STATUS_UNSPECIFIED
                        and inst.status != request.status_filter):
                    continue
                seen.add(iid)
                yield inst
            time.sleep(0.5)

    def UploadInstructions(self, request_iterator, context):
        accepted, rejected, reasons = 0, 0, []
        for inst in request_iterator:
            if not inst.instruction_id or not inst.isin:
                rejected += 1
                reasons.append(f"missing id/isin: {inst.instruction_id!r}")
                continue
            inst.updated_at.CopyFrom(_now())
            _STORE[inst.instruction_id] = inst
            accepted += 1
        return pb.UploadSummary(accepted=accepted, rejected=rejected,
                                rejection_reasons=reasons[:50])

    def Reconcile(self, request_iterator, context):
        for req in request_iterator:
            ours = _STORE.get(req.instruction_id)
            if ours is None:
                yield pb.ReconcileEvent(instruction_id=req.instruction_id,
                                        matched=False, detail="unknown instruction")
                continue
            matched = (ours.consideration.amount == req.our_amount.amount
                       and ours.consideration.currency_code == req.our_amount.currency_code)
            yield pb.ReconcileEvent(
                instruction_id=req.instruction_id,
                matched=matched,
                detail="" if matched else
                       f"expected {ours.consideration.currency_code} {ours.consideration.amount}",
            )


def serve() -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=32),
        options=[
            # defaults are 4 MiB receive / unlimited send — set BOTH explicitly
            ("grpc.max_receive_message_length", 16 * 1024 * 1024),
            ("grpc.max_send_message_length", 16 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 30_000),
            ("grpc.keepalive_timeout_ms", 10_000),
            ("grpc.http2.max_pings_without_data", 0),
        ],
    )
    pb_grpc.add_SettlementServiceServicer_to_server(SettlementService(), server)

    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("settlement.v1.SettlementService",
                        health_pb2.HealthCheckResponse.SERVING)

    # server reflection: this is what makes grpcurl usable against a binary protocol
    reflection.enable_server_reflection(
        (
            pb.DESCRIPTOR.services_by_name["SettlementService"].full_name,
            health_pb2.DESCRIPTOR.services_by_name["Health"].full_name,
            reflection.SERVICE_NAME,
        ),
        server,
    )

    with open("/etc/tls/tls.key", "rb") as f:
        key = f.read()
    with open("/etc/tls/tls.crt", "rb") as f:
        cert = f.read()
    credentials = grpc.ssl_server_credentials([(key, cert)])
    server.add_secure_port("[::]:8443", credentials)

    server.start()
    log.info("settlement.v1.SettlementService listening on :8443")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
```

**`client.py`**

```python
import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from settlement.v1 import settlement_pb2 as pb
from settlement.v1 import settlement_pb2_grpc as pb_grpc

CHANNEL_OPTIONS = [
    ("grpc.max_receive_message_length", 16 * 1024 * 1024),
    ("grpc.max_send_message_length", 16 * 1024 * 1024),
    ("grpc.enable_retries", 1),
    ("grpc.service_config",
     '{"methodConfig":[{'
     '"name":[{"service":"settlement.v1.SettlementService"}],'
     '"retryPolicy":{"maxAttempts":4,"initialBackoff":"0.2s","maxBackoff":"5s",'
     '"backoffMultiplier":2,"retryableStatusCodes":["UNAVAILABLE","DEADLINE_EXCEEDED"]}'
     '}]}'),
]


def instructions():
    for i in range(3):
        inst = pb.Instruction(
            instruction_id=f"INS-{i:04d}",
            isin="GB00B03MLX29",
            counterparty_bic="DEUTDEFFXXX",
            consideration=pb.Money(currency_code="GBP", amount="1250.75"),
            status=pb.SETTLEMENT_STATUS_PENDING,
        )
        inst.settlement_date.FromJsonString("2026-09-02T00:00:00Z")
        yield inst


def main() -> None:
    credentials = grpc.ssl_channel_credentials()
    with grpc.secure_channel("settlement.internal:8443", credentials,
                             options=CHANNEL_OPTIONS) as channel:
        stub = pb_grpc.SettlementServiceStub(channel)
        metadata = (("x-correlation-id", "8f3c1a2e-7b44-4f2e-9d5a-11c0de5b7a90"),)

        # client streaming
        summary = stub.UploadInstructions(instructions(), timeout=10.0, metadata=metadata)
        print(f"accepted={summary.accepted} rejected={summary.rejected}")

        # unary, with a DEADLINE (not a client-side timeout) that propagates downstream
        try:
            inst = stub.GetInstruction(
                pb.GetInstructionRequest(instruction_id="INS-0001"),
                timeout=2.0,
                metadata=metadata,
            )
            print(inst.isin, inst.consideration.currency_code, inst.consideration.amount)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                print("no such instruction")
            elif exc.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                print(f"retryable failure: {exc.code().name}: {exc.details()}")
            else:
                raise

        # server streaming
        watch = stub.WatchInstructions(
            pb.WatchInstructionsRequest(counterparty_bic="DEUTDEFFXXX"),
            timeout=30.0, metadata=metadata,
        )
        for event in watch:
            print("settled:", event.instruction_id)

        # bidirectional
        def recon_requests():
            yield pb.ReconcileRequest(instruction_id="INS-0001",
                                      our_amount=pb.Money(currency_code="GBP", amount="1250.75"))
            yield pb.ReconcileRequest(instruction_id="INS-0002",
                                      our_amount=pb.Money(currency_code="GBP", amount="9999.99"))

        for ev in stub.Reconcile(recon_requests(), timeout=15.0, metadata=metadata):
            print(ev.instruction_id, ev.matched, ev.detail)


if __name__ == "__main__":
    main()
```

**Debugging it** — the answer to "but you can't curl a binary protocol":

```bash
grpcurl -insecure settlement.internal:8443 list
grpcurl -insecure settlement.internal:8443 describe settlement.v1.SettlementService
grpcurl -insecure -d '{"instruction_id":"INS-0001"}' \
  settlement.internal:8443 settlement.v1.SettlementService/GetInstruction
```

That works only because server reflection is enabled — which is why I always enable it in non-production, and gate it behind auth in production rather than switching it off blindly.

**If they push back — "`timeout=` is just a client timeout, isn't it?"** — No, and this is the point worth making. In gRPC the client's timeout becomes a **deadline** transmitted as the `grpc-timeout` header, and every hop that respects it passes the *remaining* budget downstream. So a 2-second deadline at the edge means the service two hops in knows it has 1.4 seconds left and can abandon work instead of completing a computation nobody will read. That's a materially better failure model than HTTP's per-hop timeouts, and it's one of the genuine reasons to choose gRPC for a deep internal call chain. See [System Design](08-system-design-integration.md) for the end-to-end timeout budget this belongs to.

---

## 11. SOAP — The Gap You Must Close

### Q45. You've mostly built REST. Explain SOAP to me — what it actually is and how it differs.
`[MEDIUM — the gap question. Answer it without hedging.]`

**Answer:**

> SOAP is an XML messaging protocol, not an architectural style. Every message is an `Envelope` with an optional `Header` and a mandatory `Body`, and the whole thing is normally POSTed to a single endpoint URL — the URL identifies the *service*, and the operation is identified by the body element and the `SOAPAction` header, not by the path or the verb. The contract isn't optional the way OpenAPI is: a WSDL plus its XSD is machine-readable, code-generatable, and enforceable, and that's the reason SOAP is still everywhere in banking and insurance.

The differences that actually change how you build the integration:

| | REST/JSON | SOAP |
|---|---|---|
| Contract | OpenAPI, optional, descriptive | WSDL + XSD, mandatory, prescriptive — the server *validates* against it |
| Transport | HTTP only | HTTP is one binding; JMS, SMTP, MQ are legal bindings too |
| Payload | JSON, anything | XML only, namespace-qualified |
| Addressing | URI path + method | One endpoint URI; operation = body element + `SOAPAction` |
| Errors | HTTP status codes | `Fault` element in the Body, over **HTTP 500** (Q48) |
| Security | TLS + OAuth2 bearer at transport | WS-Security *inside the message* — survives intermediaries and store-and-forward |
| Transactions | none | WS-AtomicTransaction — real two-phase commit |
| Tooling | hand-written clients | codegen (`wsimport`, `svcutil`, `zeep`) from the WSDL |
| Richardson level | 2 | 0 — RPC tunnelled through HTTP POST |

**Say this:** *"I read a SOAP service the same way I read any integration: contract first, error model second, security model third. The WSDL gives me all three in one file, which is honestly more than most REST APIs hand me."*

**If they push back — "have you actually built against SOAP?"** — Be honest and immediately concrete: *"Not as a producer. As a consumer I work from the WSDL — generate a client with `zeep`, pin the WSDL locally so I'm not fetching `?wsdl` at boot, and treat faults as a first-class branch rather than an exception. The thing I'd want to confirm on day one is the fault taxonomy and whether the service is document/literal, because those two decide whether APIM can front it directly."*

---

### Q46. Walk me through a WSDL. What's in it?
`[MEDIUM — near-certain question]`

**Answer:**

> A WSDL has five things: `types` — the XSD that defines every element on the wire; `message` — the abstract input/output/fault payloads; `portType` — the abstract interface, a set of operations; `binding` — how that interface maps onto a concrete protocol, i.e. SOAP over HTTP, document or RPC style, literal or encoded use; and `service`/`port` — the actual endpoint URL. Abstract at the top, concrete at the bottom. I read them bottom-up: find the `service`, get the URL, follow the `binding` to see the style and the `SOAPAction`, then follow the `portType` to the messages and finally into the XSD, which is where the real contract lives.

WSDL 1.1 is a **W3C Note dated 15 March 2001** — it was never a Recommendation, which surprises people. WSDL 2.0 *is* a Recommendation (26 June 2007) and essentially nobody ships it. Assume 1.1.

A complete, minimal, valid WSDL — this is the one to sketch on a whiteboard:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<wsdl:definitions name="PolicyService"
    targetNamespace="http://insurer.example.com/policy/v1"
    xmlns:tns="http://insurer.example.com/policy/v1"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">

  <!-- 1. TYPES — the XSD. This is the actual contract. -->
  <wsdl:types>
    <xsd:schema targetNamespace="http://insurer.example.com/policy/v1"
                elementFormDefault="qualified">
      <xsd:element name="GetPolicyRequest">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="policyNumber" type="xsd:string" minOccurs="1" maxOccurs="1"/>
            <xsd:element name="asOfDate"     type="xsd:date"   minOccurs="0" maxOccurs="1"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>

      <xsd:element name="GetPolicyResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="policyNumber" type="xsd:string"/>
            <xsd:element name="status"       type="tns:PolicyStatus"/>
            <xsd:element name="premium"      type="xsd:decimal" nillable="true" minOccurs="0"/>
            <xsd:element name="insured"      type="tns:Party"   minOccurs="0" maxOccurs="unbounded"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>

      <xsd:element name="PolicyFault">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="code"    type="xsd:string"/>
            <xsd:element name="message" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>

      <xsd:complexType name="Party">
        <xsd:sequence>
          <xsd:element name="name" type="xsd:string"/>
          <xsd:element name="role" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>

      <xsd:simpleType name="PolicyStatus">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="ACTIVE"/>
          <xsd:enumeration value="LAPSED"/>
          <xsd:enumeration value="CANCELLED"/>
        </xsd:restriction>
      </xsd:simpleType>
    </xsd:schema>
  </wsdl:types>

  <!-- 2. MESSAGE — abstract payloads, one part each (multi-part = APIM won't import it) -->
  <wsdl:message name="GetPolicyIn">
    <wsdl:part name="parameters" element="tns:GetPolicyRequest"/>
  </wsdl:message>
  <wsdl:message name="GetPolicyOut">
    <wsdl:part name="parameters" element="tns:GetPolicyResponse"/>
  </wsdl:message>
  <wsdl:message name="GetPolicyFaultMsg">
    <wsdl:part name="fault" element="tns:PolicyFault"/>
  </wsdl:message>

  <!-- 3. PORTTYPE — the abstract interface -->
  <wsdl:portType name="PolicyPortType">
    <wsdl:operation name="GetPolicy">
      <wsdl:input  message="tns:GetPolicyIn"/>
      <wsdl:output message="tns:GetPolicyOut"/>
      <wsdl:fault  name="policyFault" message="tns:GetPolicyFaultMsg"/>
    </wsdl:operation>
  </wsdl:portType>

  <!-- 4. BINDING — protocol + style/use + the SOAPAction values -->
  <wsdl:binding name="PolicyBinding" type="tns:PolicyPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="GetPolicy">
      <soap:operation soapAction="http://insurer.example.com/policy/v1/GetPolicy" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
      <wsdl:fault name="policyFault"><soap:fault name="policyFault" use="literal"/></wsdl:fault>
    </wsdl:operation>
  </wsdl:binding>

  <!-- 5. SERVICE / PORT — the endpoint -->
  <wsdl:service name="PolicyService">
    <wsdl:port name="PolicyPort" binding="tns:PolicyBinding">
      <soap:address location="https://legacy.insurer.internal/policy/v1"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
```

Four things I check on any WSDL before I promise a delivery date:

1. **`style` and `use` on the binding.** `document`/`literal` = normal path. `rpc`/`encoded` = APIM cannot import it (Q50).
2. **`wsdl:import` / `xsd:import` / `xsd:include`.** Split WSDLs are the norm in big estates and **APIM doesn't support them** — you have to flatten first. For a WCF/.NET service, `?singleWsdl` returns the flattened document where `?wsdl` returns the split one. That one query-string suffix saves an afternoon.
3. **WSDL 1.1 transmission primitives.** Four exist — one-way, request-response, solicit-response, notification. In practice you'll see request-response and occasionally one-way (fire-and-forget, which is where the JD's queue-based batch work starts: see [Messaging](03-messaging-and-event-streaming.md)).
4. **Multiple `service`/`port` elements.** Legal in WSDL, and APIM proxies to exactly one — you pick it with `wsdlSelector` (service name + endpoint name) at import.

**If they push back — "what if there's no WSDL?"** — Then there is no contract, and I say so out loud. I capture live traffic or vendor samples, hand-write an XSD from them, and get it signed off — because otherwise the first schema change in the legacy system takes my facade down and nobody owns the breakage. That signed XSD becomes the contract-test fixture in the pipeline ([CI/CD & GitOps](05-cicd-iac-and-gitops.md)).

---

### Q47. Show me what a SOAP request and response actually look like on the wire.
`[MEDIUM]`

**Answer:**

> An HTTP POST to the single service endpoint, `Content-Type: text/xml` for SOAP 1.1, a `SOAPAction` header naming the operation, and an XML `Envelope` whose `Body` contains exactly one element named after the operation. The `Header` is optional and is where the cross-cutting concerns live — WS-Security tokens, correlation IDs, WS-Addressing. The response is the same shape with a `...Response` element in the Body, over HTTP 200.

**Request (SOAP 1.1):**

```http
POST /policy/v1 HTTP/1.1
Host: legacy.insurer.internal
Content-Type: text/xml; charset=utf-8
SOAPAction: "http://insurer.example.com/policy/v1/GetPolicy"
Accept: text/xml

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:pol="http://insurer.example.com/policy/v1">
  <soapenv:Header>
    <wsse:Security soapenv:mustUnderstand="1"
        xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <wsse:UsernameToken>
        <wsse:Username>svc_apim_policy</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">REDACTED</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </soapenv:Header>
  <soapenv:Body>
    <pol:GetPolicyRequest>
      <pol:policyNumber>POL-4471902</pol:policyNumber>
      <pol:asOfDate>2026-08-26</pol:asOfDate>
    </pol:GetPolicyRequest>
  </soapenv:Body>
</soapenv:Envelope>
```

**Response (HTTP 200):**

```http
HTTP/1.1 200 OK
Content-Type: text/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:pol="http://insurer.example.com/policy/v1">
  <soapenv:Body>
    <pol:GetPolicyResponse>
      <pol:policyNumber>POL-4471902</pol:policyNumber>
      <pol:status>ACTIVE</pol:status>
      <pol:premium>1249.50</pol:premium>
      <pol:insured>
        <pol:name>Ramesh Iyer</pol:name>
        <pol:role>PRIMARY</pol:role>
      </pol:insured>
      <pol:insured>
        <pol:name>Latha Iyer</pol:name>
        <pol:role>SPOUSE</pol:role>
      </pol:insured>
    </pol:GetPolicyResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

Details a senior mentions unprompted:

- **`mustUnderstand="1"`** on a header block means *if you don't implement this header, fail the message with a `MustUnderstand` fault*. It's how WS-Security is made non-optional. If your gateway strips or fails to reproduce it, you get a fault, not a silent pass.
- **`actor` (1.1) / `role` (1.2)** target a header block at a specific intermediary — that's the SOAP model of a message hop chain, which is why message-level security exists at all.
- **Repeated elements are the array.** `insured` twice = a two-element list. There is no JSON-style bracket, which is exactly why XML→JSON conversion is ambiguous for single-element arrays (Q59).
- **Empty `Header` can be omitted entirely.** Some fussy stacks reject a self-closed `<soapenv:Header/>`; most don't care.

**If they push back — "how do you debug this when it fails?"** — SOAP is text over HTTP, so I capture the raw envelope on both sides. In APIM that's request tracing plus a diagnostic setting; in Python it's `zeep`'s `HistoryPlugin` giving me `last_sent` / `last_received` as XML. First thing I diff is namespaces, second is `SOAPAction`, third is `Content-Type` — that's the order the bugs occur in.

---

### Q48. How does SOAP report errors, and what's the trap?
`[HARD — the highest-value SOAP question for an integration role]`

**Answer:**

> A SOAP service returns errors as a `Fault` element inside the Body, and in SOAP 1.1 the HTTP status for that is **500 Internal Server Error** — the spec mandates it. So "policy number not found" and "the database is down" arrive as the same HTTP status code, and the only way to tell them apart is to parse the fault. That's the single most important thing to know when you put a REST facade in front of SOAP, because it dictates your retry policy, your circuit breaker, and your alerting.

**SOAP 1.1 fault** — children are `faultcode`, `faultstring`, `faultactor`, `detail`, and they are **unqualified** (no namespace prefix), which trips up every XPath written by someone assuming otherwise:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>soapenv:Client</faultcode>
      <faultstring>Policy POL-9999999 not found</faultstring>
      <detail>
        <pol:PolicyFault xmlns:pol="http://insurer.example.com/policy/v1">
          <pol:code>POLICY_NOT_FOUND</pol:code>
          <pol:message>No policy exists with that number</pol:message>
        </pol:PolicyFault>
      </detail>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>
```

The four standard SOAP 1.1 `faultcode` values are `VersionMismatch`, `MustUnderstand`, `Client`, `Server`. `Client` means *don't retry, you sent something wrong*; `Server` means *the failure was not your fault, retrying may work*. That distinction is the only reliable retry signal in SOAP 1.1, and it's why `detail` matters: **`detail` is the only place the business error code lives**, and it's the part the WSDL actually types (`wsdl:fault`).

**SOAP 1.2 fault** — renamed and namespaced, structurally richer:

```xml
<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
  <env:Body>
    <env:Fault>
      <env:Code>
        <env:Value>env:Sender</env:Value>
        <env:Subcode><env:Value xmlns:pol="http://insurer.example.com/policy/v1">pol:POLICY_NOT_FOUND</env:Value></env:Subcode>
      </env:Code>
      <env:Reason><env:Text xml:lang="en">Policy POL-9999999 not found</env:Text></env:Reason>
      <env:Detail>
        <pol:PolicyFault xmlns:pol="http://insurer.example.com/policy/v1">
          <pol:code>POLICY_NOT_FOUND</pol:code>
        </pol:PolicyFault>
      </env:Detail>
    </env:Fault>
  </env:Body>
</env:Envelope>
```

`Client`→`Sender` and `Server`→`Receiver`; `faultstring`→`Reason/Text` (repeatable, `xml:lang`-tagged); `detail`→`Detail`; plus `Node`, `Role`, and machine-readable `Subcode` chains. SOAP 1.2's HTTP binding is looser about status codes than 1.1's mandatory 500 — but assume 500 until you've seen the backend prove otherwise, because most stacks emit 500 regardless.

**What the trap costs you if you miss it:**

| Symptom | Cause | Fix |
|---|---|---|
| Retry storm against a fragile mainframe | Your HTTP client retries all 5xx; every "not found" is a 5xx | Parse the fault; retry only `Server`/`Receiver` |
| Circuit breaker trips on a healthy backend | Error-rate breaker counts 500s; business rejections dominate | Classify before counting; breaker on `Server` faults + transport errors only |
| SLO dashboard shows 4% error rate, nobody can explain it | Business rejections in the 5xx bucket | Map faults to 4xx at the facade (Q57) so 5xx means what it means |
| Client retries a payment and double-books it | 500 looks retryable; the operation wasn't idempotent | Idempotency key at the facade (Q12) + only retry safe operations |

**Say this:** *"The rule I write into the runbook is: a SOAP 500 is not an incident until the fault code says it is."*

**If they push back — "so you'd translate every fault code to a status code by hand?"** — For the ones that matter, yes — and I keep the mapping table in the API's own repo next to the policy, reviewed like code. Everything unmapped falls through to 502 Bad Gateway with the fault code in an RFC 9457 `type` URI, so an unknown fault is visible rather than disguised. See §8 for the error envelope and Q57 for the policy.

---

### Q49. SOAP 1.1 vs SOAP 1.2 — what changes for you as an integrator?
`[MEDIUM]`

**Answer:**

> Three things bite you in practice: the envelope namespace, the `Content-Type`, and how the operation is signalled. SOAP 1.1 uses `http://schemas.xmlsoap.org/soap/envelope/` with `Content-Type: text/xml` and a mandatory separate `SOAPAction` HTTP header. SOAP 1.2 uses `http://www.w3.org/2003/05/soap-envelope` with `Content-Type: application/soap+xml`, and the action moves into an optional `action` parameter on that media type. Send 1.1 headers to a 1.2 endpoint and you get a 415 or a `VersionMismatch` fault, and it looks like a network problem until you look at the bytes.

| | SOAP 1.1 | SOAP 1.2 |
|---|---|---|
| Status | W3C Note, 8 May 2000 | W3C Recommendation, 27 April 2007 (2nd ed.) |
| Envelope NS | `http://schemas.xmlsoap.org/soap/envelope/` | `http://www.w3.org/2003/05/soap-envelope` |
| Content-Type | `text/xml` | `application/soap+xml` |
| Operation signal | `SOAPAction` HTTP header, **required** (may be `""`) | `action` parameter on the media type: `application/soap+xml; action="urn:GetPolicy"` |
| Fault children | `faultcode`, `faultstring`, `faultactor`, `detail` (unqualified) | `Code`/`Value`/`Subcode`, `Reason`/`Text`, `Node`, `Role`, `Detail` |
| Fault codes | `VersionMismatch`, `MustUnderstand`, `Client`, `Server` | + `DataEncodingUnknown`; `Sender`/`Receiver` |
| Header targeting | `actor` | `role` (+ `relay` attribute) |
| SOAP encoding | Section 5 encoding in scope | Deprecated in practice; WS-I bans it |
| Bindings | HTTP + others informally | Formal binding framework (HTTP binding + others) |

Operational notes: keep the **quotes** around the `SOAPAction` value — several stacks (classic .NET ASMX among them) reject an unquoted value. `SOAPAction: ""` is legal in 1.1 and means "no intent expressed", which forces the server to dispatch off the body element — one of the reasons document/literal *wrapped* exists (Q50).

**If they push back — "which do you meet more often?"** — 1.1, by a wide margin, because the estates that still run SOAP were built before 1.2 landed and nobody reissues a WSDL for fun. I default to 1.1 and confirm from the binding namespace in the WSDL rather than asking.

---

### Q50. document/literal vs RPC/encoded — what do you meet, and why did doc/literal win?
`[HARD — and it has a direct Azure consequence]`

**Answer:**

> `style` says how the body is laid out — `rpc` wraps parameters in an operation-named element that the *runtime* generates, `document` says the body is just an XML document you define. `use` says how it's typed — `literal` means "validates against the XSD in the WSDL", `encoded` means "typed at runtime with SOAP Section 5 encoding rules and `xsi:type` attributes everywhere". Document/literal won because it's the only combination where the message on the wire can be validated against a schema, and WS-I Basic Profile ruled SOAP encoding out. In practice you will meet **document/literal wrapped** almost always, and it matters in Azure because **API Management only supports document/literal — it explicitly does not support rpc style or SOAP encoding.**

The four combinations:

| style/use | On the wire | Verdict |
|---|---|---|
| rpc/encoded | Operation wrapper + `xsi:type` on every value, graph references | Dead. Not schema-validatable, not interoperable, banned by WS-I |
| rpc/literal | Operation wrapper generated by the runtime, children validate | Rare. Wrapper isn't in the XSD, so you can't validate the whole body |
| document/encoded | Nobody | Theoretical |
| document/literal | Body child is an element declared in the XSD | The standard |
| **document/literal wrapped** | Body has exactly one child, named for the operation, declared in the XSD, whose children are the parameters | **What you'll actually see** |

Why *wrapped* specifically: with one schema-declared root element per operation the server can dispatch off the body element even when `SOAPAction` is empty, the entire body validates in one pass, and the request/response elements map cleanly onto a generated method signature. Unwrapped doc/literal with multiple body children breaks dispatch and is why **APIM rejects messages with multiple parts** on import.

**Say this:** *"The first grep I do on an unfamiliar WSDL is `soap:binding style` and `soap:body use`. If it says `rpc` or `encoded`, the APIM import path is off the table and I'm planning a mediation component instead — a Function or Logic App that speaks the legacy dialect — and I say so before anyone puts a date on it."*

**If they push back — "what would you do with an rpc/encoded service?"** — Wrap it in a thin adapter I control: a Python or .NET service that uses a generated client (a stack that still speaks SOAP encoding) and exposes clean document/literal or REST upstream. Then APIM fronts my adapter, not the legacy service. That keeps one ugly component with one owner instead of ugliness smeared across every consumer — which is the platform-engineering answer to every legacy dialect problem.

---

### Q51. Which parts of XSD do you actually need for integration work?
`[MEDIUM — namespaces cause most real SOAP bugs]`

**Answer:**

> `complexType` with `sequence` for ordered structures, `minOccurs`/`maxOccurs` for optionality and arrays, `simpleType` with `restriction` for enums and formats, `nillable` for explicit nulls, and `targetNamespace` plus `elementFormDefault` for naming. If I had to name the one that causes the most production incidents, it's `elementFormDefault` — whether child elements are namespace-qualified — because getting it wrong produces a message that looks right, passes review, and is silently rejected by the server.

The working set:

```xml
<xsd:schema targetNamespace="http://insurer.example.com/policy/v1"
            xmlns:tns="http://insurer.example.com/policy/v1"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            elementFormDefault="qualified">

  <xsd:complexType name="Instruction">
    <xsd:sequence>                                   <!-- ORDER IS PART OF THE CONTRACT -->
      <xsd:element name="reference"  type="xsd:string"   minOccurs="1" maxOccurs="1"/>
      <xsd:element name="amount"     type="xsd:decimal"  minOccurs="1"/>   <!-- never xsd:float for money -->
      <xsd:element name="valueDate"  type="xsd:date"     minOccurs="0" nillable="true"/>
      <xsd:element name="narrative"  type="xsd:string"   minOccurs="0" maxOccurs="4"/>
      <xsd:element name="settlement" type="tns:Settlement"/>
    </xsd:sequence>
    <xsd:attribute name="channel" type="xsd:string" use="required"/>
  </xsd:complexType>

  <xsd:simpleType name="CurrencyCode">
    <xsd:restriction base="xsd:string">
      <xsd:pattern value="[A-Z]{3}"/>
    </xsd:restriction>
  </xsd:simpleType>

  <xsd:complexType name="Settlement">
    <xsd:choice>                                     <!-- exactly one of -->
      <xsd:element name="iban" type="xsd:string"/>
      <xsd:element name="accountAndSortCode" type="tns:UkAccount"/>
    </xsd:choice>
  </xsd:complexType>

  <xsd:complexType name="UkAccount">
    <xsd:sequence>
      <xsd:element name="accountNumber" type="xsd:string"/>
      <xsd:element name="sortCode"      type="xsd:string"/>
    </xsd:sequence>
  </xsd:complexType>
</xsd:schema>
```

What each one costs you if you get it wrong:

- **`sequence` means order is mandatory.** Reordering two elements produces a validation failure, not a warning. `xsd:all` allows any order but is rare and constrained.
- **`minOccurs` / `maxOccurs` default to 1.** `maxOccurs="unbounded"` is the array. A single-occurrence array is the classic JSON conversion bug (Q59).
- **`nillable="true"` ≠ `minOccurs="0"`.** Nillable means the element is *present* carrying `xsi:nil="true"` — an explicit null. `minOccurs="0"` means absent. In JSON that's `{"premium": null}` versus no `premium` key, and for a financial field those mean different things: "known to be nothing" versus "not supplied". APIM even exposes the choice: `set-body`'s `xsi-nil` attribute maps nil to `blank` (empty string, the default) or `null`.
- **`targetNamespace` is the version.** Enterprises version SOAP contracts by minting a new namespace (`/policy/v2`), which is why the same operation name can exist twice with incompatible payloads. Cross-reference §5 on versioning: namespace-versioning is the SOAP equivalent of a URI major version.
- **`elementFormDefault`.** `qualified` = child elements are in the target namespace, so `<pol:policyNumber>`. `unqualified` (the default if omitted!) = only the top-level element is namespaced, so `<pol:GetPolicyRequest><policyNumber>`. Handwritten clients get this wrong constantly.
- **Prefixes are irrelevant; namespace URIs are everything.** `soapenv:`, `soap:`, `s:` are all fine for the same URI. Never match on a prefix in code or in an XPath — bind the URI (Q54).
- **`xsd:any` / `xsd:anyType`** is the vendor's escape hatch and means the contract is partially fictional. Flag it: it's where undocumented fields live.
- **`xsd:dateTime` carries an optional timezone offset.** A legacy system that emits naive local timestamps in a `dateTime` field is a genuine finance-grade defect — put it in the mapping doc, and see [FS](12-financial-services-integration.md) on value dates and cut-offs.

**If they push back — "would you validate at the gateway?"** — Yes for the REST side: APIM's `validate-content` policy against the JSON schema, so garbage is rejected at the edge instead of producing a fault 400ms later inside a mainframe. Note the documented cap — `validate-content` inspects request/response bodies up to **100 KiB**, and the schema itself up to 4 MB — so for large batch payloads I validate structurally at the edge and let the backend do the deep validation.

---

### Q52. What's in the WS-* stack, and which parts do you care about?
`[MEDIUM — name recognition is the pass mark; one deep answer is the distinction]`

**Answer:**

> WS-* is the layer of specifications bolted onto SOAP for things HTTP doesn't give you. The four I'd expect to meet are WS-Security for message-level authentication, signing and encryption; WS-Addressing for transport-independent routing and async correlation; WS-ReliableMessaging for at-least-once/exactly-once delivery over an unreliable link; and WS-AtomicTransaction with WS-Coordination for genuine two-phase commit across services. Plus MTOM for binary attachments. The one that changes my design is WS-Security, because it means the security context lives in the message and therefore survives an intermediary — which is exactly why banks chose SOAP.

| Spec | What it does | Where you meet it |
|---|---|---|
| **WS-Security** (OASIS WSS, SOAP Message Security) | Security tokens in the `Header` — `UsernameToken` (username/password, `PasswordText` or `PasswordDigest`), X.509 binary tokens, SAML assertions — plus XML Signature over selected elements and XML Encryption of selected elements, and a `Timestamp` with `Created`/`Expires` to bound replay | Everywhere in banking/insurance. Assume it |
| **WS-Addressing** (W3C Rec, 2006) | `To`, `Action`, `MessageID`, `RelatesTo`, `ReplyTo`, `FaultTo` as SOAP headers — endpoint references, so the message routes and correlates independently of the transport | Async callbacks; SOAP over JMS/MQ; WCF `wsHttpBinding` |
| **WS-ReliableMessaging** (OASIS) | Sequences, message numbers, acknowledgements, retransmission — delivery assurances at the protocol layer | Store-and-forward links, telco OSS |
| **WS-AtomicTransaction / WS-Coordination** (OASIS) | Distributed 2PC — a coordinator, prepare/commit across participants | Core banking postings; the reason "just use a saga" isn't always the answer |
| **WS-Policy / WS-PolicyAttachment** | Machine-readable statement of the above, attached to the WSDL, so a client can be generated *with* the security requirements | WCF-generated WSDLs |
| **MTOM** (W3C Rec, 25 Jan 2005) + XOP | Sends binary as a MIME part instead of base64 inside the XML — avoids the ~33% base64 inflation and the memory cost of parsing a huge text node | Document/imaging services: policy documents, KYC scans |

**The Azure consequence, stated as a fact:** the APIM docs are explicit that **"WSDL files incorporating WS-\* specifications aren't supported"** for import, that **WCF services should use `basicHttpBinding` and `wsHttpBinding` isn't supported**, and that MTOM **"might work"** with no official support. So if the backend demands WS-Security, APIM's importer will not do it for you — you inject the `wsse:Security` header yourself in a policy (Q57), or you terminate WS-Security in a small mediation component and keep APIM for the edge concerns.

**Say this:** *"WS-Security is not TLS. TLS protects the hop; WS-Security protects the message. If the message goes through a queue, an ESB and a partner's gateway before it reaches the core, only one of those two survives the journey — and in a signed-audit environment the signed message is the evidence."* See [Auth](06-auth-and-security.md) for how that contrasts with JWT and mTLS.

**If they push back — "PasswordText over the wire? Really?"** — It's only acceptable over TLS with a short-lived service credential rotated from Key Vault, and I'd push for X.509 or a digest with a nonce and `Created` timestamp where the backend supports it. Where it can't change, the compensating controls are the ones I document: TLS 1.2+, credential in Key Vault with a rotation runbook, no credential in the policy body, and gateway-side rate limits so a leaked credential can't be used at volume.

---

### Q53. Why do enterprises still run SOAP, and where will I meet it here?
`[MEDIUM — this is a financial-services question in disguise]`

**Answer:**

> Three reasons that are actually good ones: the contract is formal and enforceable, so a vendor can be held to it and both sides can generate code from it; security is at the message level, so it survives queues, intermediaries and store-and-forward, which REST's transport-level model does not; and it has real distributed transactions, which matters when a posting must hit two ledgers or neither. The fourth reason is the honest one — these systems were bought, not built, the vendor charges for change, and nothing about a rewrite makes the regulator happier. So the integration layer absorbs the ugliness. That's the job.

Where SOAP is still first-class, and it maps onto EY's sector focus:

| Sector | Systems that speak SOAP |
|---|---|
| Banking & Capital Markets | Core banking (Finacle, Flexcube, T24), payments hubs and SWIFT adapters, custody and settlement platforms |
| Insurance | Policy administration and claims systems, reinsurance bordereaux exchanges, regulatory returns |
| Asset Management / PE | Fund administrators and transfer agents, custodian reporting, portfolio accounting vendors |
| Cross-industry | SAP (ECC/PI-PO exposes SOAP web services; RFC/BAPI behind it), Siebel and older CRM, telco OSS/BSS, credit bureaus, government tax and e-invoicing portals |

**Say this:** *"My working assumption on a financial services integration programme is: REST at the edges for the consumers, SOAP or file/queue at the core for the systems of record, and the platform's job is a paved road between them — a facade template, a fault-mapping convention, a schema registry and a runbook — so the tenth legacy adapter costs a fraction of the first."*

**If they push back — "would you recommend replacing SOAP with REST?"** — Not as a goal in itself. I'd put a REST facade in front of it so new consumers never see SOAP, and then strangle the legacy service behind the facade if and when there's a business case. The facade is the thing that buys you optionality; the rewrite is a separate decision with a separate business case. See [System Design](08-system-design-integration.md) for the strangler pattern in full.

---

### Q54. Consume this SOAP service from Python.
`[MEDIUM — you'll be asked, and this is your home ground]`

**Answer:**

> `zeep` for anything with a usable WSDL — it parses the contract, generates the types, and gives you a service proxy with real Python signatures. `lxml` plus `requests` when the WSDL is broken, the service is rpc/encoded, or I need byte-level control of the envelope. The two things I always change from the defaults: pin the WSDL as a file in the repo instead of fetching `?wsdl` at startup, and set explicit timeouts, because the default is "wait forever" and a hung mainframe socket will exhaust your worker pool.

`zeep` — current release **4.3.3**, requires Python ≥ 3.10, built on `lxml`/`requests` with SOAP 1.1 and 1.2, WS-Addressing headers and WSSE support:

```python
import os
from datetime import date

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.exceptions import Fault, TransportError, ValidationError
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

session = Session()
session.verify = "/etc/ssl/certs/corp-root-ca.pem"          # private CA on the legacy endpoint
session.mount(
    "https://",
    HTTPAdapter(
        pool_maxsize=32,
        # NOTE: retrying POST is only safe for operations the backend documents as idempotent.
        max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=(502, 503, 504),
                          allowed_methods=frozenset(["POST"])),
    ),
)

history = HistoryPlugin(maxlen=5)                            # last_sent / last_received for support tickets
transport = Transport(
    session=session,
    timeout=10,              # connect + WSDL fetch
    operation_timeout=30,    # per SOAP call — the one people forget
    cache=SqliteCache(path="/var/tmp/zeep-cache.db", timeout=3600),
)

client = Client(
    wsdl="file:///opt/contracts/PolicyService-v1.wsdl",      # pinned, version-controlled, contract-tested
    transport=transport,
    settings=Settings(strict=True, xml_huge_tree=False, raw_response=False),
    wsse=UsernameToken("svc_apim_policy", os.environ["POLICY_SVC_PASSWORD"]),
    plugins=[history],
)

# Bind explicitly rather than trusting soap:address in the WSDL — the WSDL usually
# points at the vendor's DEV box, and this is how you target per-environment endpoints.
service = client.create_service(
    "{http://insurer.example.com/policy/v1}PolicyBinding",
    os.environ["POLICY_SVC_URL"],
)


class PolicyNotFound(Exception):
    pass


def get_policy(policy_number: str) -> dict:
    try:
        result = service.GetPolicy(policyNumber=policy_number, asOfDate=date.today())
    except Fault as exc:
        # exc.code is the faultcode ('soapenv:Client'), exc.message the faultstring,
        # exc.detail the typed lxml element that carries the business error code.
        detail_code = ""
        if exc.detail is not None:
            found = exc.detail.find(".//{http://insurer.example.com/policy/v1}code")
            detail_code = found.text if found is not None else ""
        if detail_code == "POLICY_NOT_FOUND" or str(exc.code).endswith("Client"):
            raise PolicyNotFound(policy_number) from exc      # 404/400 — do NOT retry
        raise                                                  # Server fault — retryable
    except (TransportError, ValidationError):
        raise
    return serialize_object(result, dict)                      # zeep objects -> plain dict/JSON
```

Points worth saying out loud:

- **`Fault` is a normal exception path, not an error.** Branch on `exc.code` (Client vs Server) and on the typed `exc.detail`. That is the Python side of Q48.
- **`serialize_object`** turns zeep's generated objects into dicts you can hand to Pydantic — the boundary where the XML world stops.
- **In FastAPI, zeep is synchronous.** Build the `Client` once at startup (WSDL parsing is expensive) and call it via `anyio.to_thread.run_sync` / `starlette.concurrency.run_in_threadpool` so a 30-second legacy call doesn't block the event loop. zeep 4.x does ship an `AsyncClient`/`AsyncTransport` pair on httpx, but WSDL parsing itself is still synchronous, so it must happen at startup either way. See [Python](07-python-for-integration-and-coding-round.md).
- **Timeouts are load-bearing.** `timeout` covers connect and WSDL fetch, `operation_timeout` covers the call. Without the second one, one stuck backend socket takes the pod down and your HPA scales up sick replicas ([K8s](04-microservices-containers-kubernetes.md)).

**Raw `lxml` when the WSDL isn't usable** — and note the namespace handling, which is the part interviewers probe:

```python
import requests
from lxml import etree

SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"
POL = "http://insurer.example.com/policy/v1"
NS = {"s": SOAP11, "pol": POL}          # bind URIs, never trust the sender's prefixes

# Hardened parser: SOAP endpoints are a classic XXE / billion-laughs target.
PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)


def build_envelope(policy_number: str, as_of: str) -> bytes:
    env = etree.Element(etree.QName(SOAP11, "Envelope"), nsmap={"soapenv": SOAP11, "pol": POL})
    etree.SubElement(env, etree.QName(SOAP11, "Header"))
    body = etree.SubElement(env, etree.QName(SOAP11, "Body"))
    req = etree.SubElement(body, etree.QName(POL, "GetPolicyRequest"))
    etree.SubElement(req, etree.QName(POL, "policyNumber")).text = policy_number
    etree.SubElement(req, etree.QName(POL, "asOfDate")).text = as_of
    return etree.tostring(env, xml_declaration=True, encoding="UTF-8")


def call(policy_number: str, as_of: str) -> dict:
    resp = requests.post(
        "https://legacy.insurer.internal/policy/v1",
        data=build_envelope(policy_number, as_of),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": '"http://insurer.example.com/policy/v1/GetPolicy"',   # keep the quotes
        },
        timeout=(5, 30),
    )
    root = etree.fromstring(resp.content, parser=PARSER)

    # SOAP 1.1 Fault children are UNQUALIFIED — no namespace on faultcode/faultstring.
    fault = root.find(f"{{{SOAP11}}}Body/{{{SOAP11}}}Fault")
    if fault is not None:
        code = fault.findtext("faultcode", default="")
        reason = fault.findtext("faultstring", default="")
        detail = fault.find(f"detail/{{{POL}}}PolicyFault/{{{POL}}}code")
        raise RuntimeError(f"SOAP fault {code} [{detail.text if detail is not None else '-'}]: {reason}")

    resp.raise_for_status()   # after the fault check: a fault arrives as HTTP 500
    return {
        "policyNumber": root.findtext(".//pol:policyNumber", namespaces=NS),
        "status": root.findtext(".//pol:status", namespaces=NS),
        "insured": [e.findtext("pol:name", namespaces=NS)
                    for e in root.iterfind(".//pol:insured", namespaces=NS)],
    }
```

**If they push back — "why check the fault before `raise_for_status()`?"** — Because the fault *is* the 500. If you call `raise_for_status()` first you throw away the only diagnostic information in the response and turn a precise "POLICY_NOT_FOUND" into an anonymous HTTPError. Same reason the facade parses the body before deciding the status code (Q57).

---

## 12. Exposing SOAP as REST in Azure APIM

### Q55. How would you expose a legacy SOAP service as a REST API?
`[HARD — rehearse this one verbatim. PLAN.md §3.2.]`

**Answer — the 90-second spoken version:**

> "I'd treat it as two contracts, not one translation. First I design the REST contract from the domain — resources, verbs, status codes, an OpenAPI spec agreed with the consumers — and deliberately *not* from the WSDL operation list, because if `GetPolicyById` shows up as a REST path I've just moved the legacy API to a new URL and added a hop.
>
> Then I put the facade in API Management. I import the WSDL — flattened first, because APIM doesn't resolve `wsdl:import` or `xsd:include` — using SOAP-to-REST if the service is document/literal and the shapes are simple, and I hand-write the policy when the mapping is non-trivial: inbound builds the SOAP envelope and sets `SOAPAction` and `Content-Type`, outbound converts the response XML to JSON, and I map SOAP faults onto real HTTP status codes, because a SOAP service returns HTTP 500 for what is semantically a 404 or a 400, and if I don't fix that at the facade every consumer's retry logic hammers a fragile backend.
>
> Around that I put the platform concerns: OAuth2 or subscription keys terminated at the gateway with WS-Security credentials injected towards the backend from Key Vault, aggressive rate limiting because the legacy system has a fraction of the gateway's capacity, response caching for reference data, correlation IDs flowed end to end into App Insights, and a contract test in the pipeline that replays a recorded envelope against the real WSDL so a vendor schema change breaks the build and not production.
>
> Connectivity depends on where the backend lives — if it's on-prem behind a firewall, a self-hosted APIM gateway container next to the service, or VNet integration over ExpressRoute. And I'd publish it as a template: a golden policy fragment, the fault-mapping convention, the runbook. The tenth SOAP facade should be a day, not a sprint."

The one-sentence version if they cut you off: *"REST contract designed from the domain, APIM as the facade, faults mapped to real status codes, credentials at the edge, and the whole thing shipped as a reusable template."*

**If they push back — "why not just let clients call the SOAP service?"** — Because then every consumer implements XML handling, WS-Security, the fault taxonomy and the retry rules independently, and gets them subtly wrong in five different ways. The facade is where that knowledge lives once. It's also the only place I can throttle, cache, observe and version — and it's the seam that makes replacing the legacy system possible later without touching a single consumer.

**If they push back — "isn't the gateway now a single point of failure?"** — It already was, in the sense that the legacy backend is. APIM Premium gives me multi-region and availability zones, the policies are in source control and deployed by pipeline, and a self-hosted gateway fails static — it keeps serving from its in-memory (or backed-up) configuration when it can't reach Azure. Availability comes from the deployment topology, not from removing the hop.

---

### Q56. What exactly does APIM do when you import a WSDL?
`[MEDIUM — Azure-specific, very likely]`

**Answer:**

> Two import modes. **SOAP pass-through** keeps the API as SOAP — APIM publishes one operation per WSDL operation, all as `POST` to the same path, and adds gateway concerns like keys, JWT validation, rate limiting and logging without touching the payload. **SOAP-to-REST** attempts the transformation: APIM generates a REST-shaped operation per WSDL operation and auto-writes policies that build the SOAP envelope inbound and convert the XML response to JSON outbound. Pass-through is a governance win with zero payload risk; SOAP-to-REST is a modernisation move that only works cleanly for simple document/literal contracts.

```bash
# Pass-through import via CLI; --wsdl-service-name / --wsdl-endpoint-name pick the
# service and port when the WSDL declares several (the wsdlSelector property).
az apim api import \
  --resource-group rg-integration-prod \
  --service-name apim-integration-prod \
  --api-id policy-soap \
  --path policy-soap \
  --specification-format Wsdl \
  --specification-path ./contracts/PolicyService-v1-flattened.wsdl \
  --wsdl-service-name PolicyService \
  --wsdl-endpoint-name PolicyPort
```

**The documented WSDL import restrictions — know these, they are the difference between a demo and a delivery:**

| Restriction | Consequence |
|---|---|
| Only **document/literal**; **no rpc style, no SOAP-Encoding** | rpc/encoded WSDL = no import. Build a mediation component (Q50) |
| `wsdl:import`, `xsd:import`, `xsd:include` **not supported** | Flatten first — `?singleWsdl` on WCF, or the `Azure-Samples/api-management-schema-import` tool |
| WSDLs incorporating **WS-\* specifications not supported** | WS-Security must be injected by policy or terminated elsewhere |
| **Messages with multiple parts not supported** | One `wsdl:part` per message |
| WCF **`wsHttpBinding` not supported**; use `basicHttpBinding` | Ask the vendor for a basic-binding endpoint |
| **MTOM** "might work", not officially supported | Don't put a document-imaging service on this path without a spike |
| **Recursive types not supported** | Self-referencing structures (org trees, nested claims) will fail |
| Multiple `wsdl:service`/`wsdl:port` → one only | Choose with `wsdlSelector`; use a load-balanced backend pool if you need several |
| SOAP-to-REST supports **wrapped arrays only** (`maxOccurs="unbounded"` inside a `sequence` inside a wrapper `complexType`) | Non-wrapped arrays need hand-written policy |
| Only the target namespace can define message parts; other namespaces aren't preserved on export | Multi-namespace schemas lose fidelity on round-trip |

Two more practical notes from the docs: a **wildcard SOAP action** operation — `POST` with the resource `/?soapAction={any}` — catches any SOAP request that has no dedicated operation defined, which is how you cover an operation set you haven't modelled yet; and **do not use the OpenAPI specification editor in the Design tab to modify a SOAP API** — it will mangle it.

**The design rule that matters more than any of the above:**

> **Never let WSDL operation names leak into your REST resource model.** If your imported API produces `POST /policy-soap/GetPolicyById`, you have not built a REST API — you have moved a legacy API to a new URL and added a network hop, plus a gateway bill. The auto-generated operations are a *starting point* to be renamed and reshaped into resources: `GET /v1/policies/{policyNumber}`, `POST /v1/policies/{policyNumber}/cancellations`. That reshaping is the actual work, and it's the part the auto-import can't do for you.

**If they push back — "so when do you accept the auto-generated shape?"** — Internal-only, machine-to-machine, short-lived, where the consumer is one team I control and the alternative is delaying a migration. I'd still put it behind a `-legacy` product with its own deprecation date (§5) so it never becomes the public contract by accident.

---

### Q57. Show me the policy for a SOAP-to-REST operation.
`[HARD — the "can you actually do it" question]`

**Answer:**

> Four moves: inbound builds the envelope and sets the SOAP headers and backend; backend forwards with an explicit timeout; outbound detects a fault before anything else and maps it to a real status code, otherwise converts XML to JSON; on-error normalises gateway failures. The order matters — fault detection must happen before the XML-to-JSON conversion, because once the fault is JSON you've lost the typed detail.

Operation: `GET /v1/policies/{policyNumber}` over the `GetPolicy` operation from Q46.

```xml
<policies>
    <inbound>
        <base />

        <!-- Edge auth: OAuth2 in, service credential out. See 06-auth-and-security.md -->
        <validate-jwt header-name="Authorization" failed-validation-httpcode="401"
                      failed-validation-error-message="Unauthorized">
            <openid-config url="https://login.microsoftonline.com/{{tenant-id}}/v2.0/.well-known/openid-configuration" />
            <audiences>
                <audience>api://policy-facade</audience>
            </audiences>
            <required-claims>
                <claim name="roles" match="any">
                    <value>Policy.Read</value>
                </claim>
            </required-claims>
        </validate-jwt>

        <!-- Protect the fragile backend. The mainframe does not autoscale. -->
        <rate-limit-by-key calls="20" renewal-period="60"
                           counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)" />

        <set-backend-service base-url="https://legacy.insurer.internal" />
        <rewrite-uri template="/policy/v1" />

        <set-header name="Content-Type" exists-action="override">
            <value>text/xml; charset=utf-8</value>
        </set-header>
        <set-header name="SOAPAction" exists-action="override">
            <value>"http://insurer.example.com/policy/v1/GetPolicy"</value>
        </set-header>
        <!-- Never forward the caller's bearer token to the legacy backend. -->
        <set-header name="Authorization" exists-action="delete" />

        <!-- Build the envelope with XElement, not string concatenation: this escapes
             the path parameter and makes XML injection impossible by construction.
             (Liquid set-body needs a request body and throws on an inbound GET.) -->
        <set-body>@{
            XNamespace soapenv = "http://schemas.xmlsoap.org/soap/envelope/";
            XNamespace wsse    = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd";
            XNamespace pol     = "http://insurer.example.com/policy/v1";

            var asOf = context.Request.Url.Query.GetValueOrDefault("asOfDate",
                           DateTime.UtcNow.ToString("yyyy-MM-dd"));

            var security = new XElement(wsse + "Security",
                new XAttribute(soapenv + "mustUnderstand", "1"),
                new XElement(wsse + "UsernameToken",
                    new XElement(wsse + "Username", "{{policy-svc-user}}"),
                    new XElement(wsse + "Password",
                        new XAttribute("Type", "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText"),
                        "{{policy-svc-password}}")));

            var envelope = new XDocument(
                new XElement(soapenv + "Envelope",
                    new XAttribute(XNamespace.Xmlns + "soapenv", soapenv.NamespaceName),
                    new XElement(soapenv + "Header", security),
                    new XElement(soapenv + "Body",
                        new XElement(pol + "GetPolicyRequest",
                            new XElement(pol + "policyNumber", context.Request.MatchedParameters["policyNumber"]),
                            new XElement(pol + "asOfDate", asOf)))));

            return envelope.ToString();
        }</set-body>
    </inbound>

    <backend>
        <!-- Default is 300s; values above 240s may not be honoured by the network fabric.
             Pick a timeout shorter than the caller's, and document it in the runbook. -->
        <forward-request timeout="30" />
    </backend>

    <outbound>
        <base />

        <!-- 1. FAULT FIRST. A SOAP fault arrives as HTTP 500 with a 200-shaped body. -->
        <set-variable name="faultDetailCode" value="@{
            if (context.Response.StatusCode != 500) { return ""; }
            try {
                XNamespace soapenv = "http://schemas.xmlsoap.org/soap/envelope/";
                XNamespace pol     = "http://insurer.example.com/policy/v1";
                var doc   = context.Response.Body.As<XDocument>(preserveContent: true);
                var fault = doc.Descendants(soapenv + "Fault").FirstOrDefault();
                if (fault == null) { return ""; }
                // SOAP 1.1 fault children are UNQUALIFIED - no namespace here.
                var detail = fault.Descendants(pol + "code").FirstOrDefault();
                return detail != null ? detail.Value : (fault.Element("faultcode") != null ? fault.Element("faultcode").Value : "UNKNOWN_FAULT");
            } catch (Exception) { return "UNPARSEABLE_FAULT"; }
        }" />

        <choose>
            <when condition="@(context.Variables.GetValueOrDefault<string>("faultDetailCode","") == "POLICY_NOT_FOUND")">
                <return-response>
                    <set-status code="404" reason="Not Found" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/problem+json</value>
                    </set-header>
                    <set-body>@{
                        return new JObject(
                            new JProperty("type", "https://api.example.com/problems/policy-not-found"),
                            new JProperty("title", "Policy not found"),
                            new JProperty("status", 404),
                            new JProperty("instance", context.Request.Url.Path),
                            new JProperty("correlationId", context.RequestId.ToString())
                        ).ToString();
                    }</set-body>
                </return-response>
            </when>
            <when condition="@(context.Variables.GetValueOrDefault<string>("faultDetailCode","") == "POLICY_NUMBER_INVALID")">
                <return-response>
                    <set-status code="400" reason="Bad Request" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/problem+json</value>
                    </set-header>
                    <set-body>@{
                        return new JObject(
                            new JProperty("type", "https://api.example.com/problems/invalid-policy-number"),
                            new JProperty("title", "Invalid policy number"),
                            new JProperty("status", 400),
                            new JProperty("correlationId", context.RequestId.ToString())
                        ).ToString();
                    }</set-body>
                </return-response>
            </when>
            <when condition="@(context.Variables.GetValueOrDefault<string>("faultDetailCode","") != "")">
                <!-- Unmapped fault: 502, never a silent 500. The code is visible so it gets mapped tomorrow. -->
                <return-response>
                    <set-status code="502" reason="Bad Gateway" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/problem+json</value>
                    </set-header>
                    <set-body>@{
                        return new JObject(
                            new JProperty("type", "https://api.example.com/problems/backend-fault"),
                            new JProperty("title", "Backend fault"),
                            new JProperty("status", 502),
                            new JProperty("faultCode", context.Variables.GetValueOrDefault<string>("faultDetailCode","")),
                            new JProperty("correlationId", context.RequestId.ToString())
                        ).ToString();
                    }</set-body>
                </return-response>
            </when>
        </choose>

        <!-- 2. Happy path: strip the envelope, then convert. -->
        <set-body>@{
            XNamespace soapenv = "http://schemas.xmlsoap.org/soap/envelope/";
            XNamespace pol     = "http://insurer.example.com/policy/v1";
            var doc  = context.Response.Body.As<XDocument>();
            var resp = doc.Descendants(pol + "GetPolicyResponse").FirstOrDefault();
            return resp != null ? resp.ToString() : doc.ToString();
        }</set-body>

        <!-- apply="always" + consider-accept-header="false": convert unconditionally.
             Leaving consider-accept-header at its default of true means a client that
             omits Accept: application/json silently gets XML - a classic support ticket. -->
        <xml-to-json kind="javascript-friendly" apply="always" consider-accept-header="false"
                     always-array-child-elements="false" />

        <set-header name="Content-Type" exists-action="override">
            <value>application/json</value>
        </set-header>
        <set-header name="X-Correlation-Id" exists-action="override">
            <value>@(context.RequestId.ToString())</value>
        </set-header>
    </outbound>

    <on-error>
        <base />
        <set-header name="Content-Type" exists-action="override">
            <value>application/problem+json</value>
        </set-header>
        <set-body>@{
            var reason = context.LastError?.Reason ?? "GatewayError";
            var status = reason == "Timeout" ? 504 : 502;
            context.Response.StatusCode = status;
            return new JObject(
                new JProperty("type", "https://api.example.com/problems/gateway-" + reason.ToLower()),
                new JProperty("title", reason),
                new JProperty("status", status),
                new JProperty("detail", "The policy administration system did not respond in time."),
                new JProperty("correlationId", context.RequestId.ToString())
            ).ToString();
        }</set-body>
    </on-error>
</policies>
```

Six things to point at while they read it:

1. **`{{policy-svc-user}}` / `{{policy-svc-password}}`** are APIM **named values backed by Key Vault** — the credential never sits in the policy XML, and rotation is a Key Vault operation, not a deployment. The whole policy file lives in Git and deploys by pipeline (§[CI/CD & GitOps](05-cicd-iac-and-gitops.md)).
2. **`XElement` construction, not string concatenation.** A policy number of `X</policyNumber><evil>` is XML injection against the backend if you build the envelope by concatenating strings. `System.Net.WebUtility.HtmlEncode` is also available in policy expressions, but constructing the tree escapes correctly by default.
3. **`preserveContent: true`** when reading the response body for fault inspection — otherwise the body stream is consumed and the happy path has nothing left to convert.
4. **The reverse direction** — a REST `POST` with a JSON body — is where the Liquid template earns its place: `<set-body template="liquid">` with the SOAP envelope as the template and `{{body.someField}}` interpolations. Two documented gotchas: set `Content-Type` to an XML type first so Liquid binds the body correctly, and Liquid **does not work inside `return-response`** because that policy cancels the pipeline and empties the body.
5. **`json-to-xml`** is the mirror policy for that direction, with `namespace-prefix="xmlns"` and `namespace-separator=":"` so JSON keys like `"soapenv:Body"` come out as real namespaced XML.
6. **`fail-on-error-status-code="true"`** on `forward-request` is the alternative design: it routes backend 400–599 responses into `on-error` instead of `outbound`. I *don't* use it here, because a SOAP fault is a semantically successful exchange and I want it handled in `outbound` where the body is still XML.

**If they push back — "isn't that a lot of logic in a gateway?"** — It's the right amount for a mapping this shape, and it's version-controlled and tested like code. My line is drawn at orchestration: the moment the facade needs to call two backends, hold state, compensate on failure, or retry with a schedule, it stops being a policy and becomes a Function or a Logic App, and APIM goes back to being the edge ([Azure Integration Services](02-azure-integration-services.md)).

---

### Q58. The SOAP service is on-premises behind a firewall. How does APIM reach it?
`[HARD — hybrid connectivity, and people confuse these four constantly]`

**Answer:**

> Four options and they solve different problems. Put a **self-hosted gateway** — the containerised APIM data plane — inside the on-prem network next to the service, so API traffic never leaves the datacentre and only outbound 443 control traffic goes to Azure. Or keep the managed gateway and give it a network path: **VNet injection** plus **ExpressRoute or a site-to-site VPN** back to on-prem. **Private Link / private endpoints** on APIM are for *inbound* traffic to the gateway, not for reaching backends — that's the confusion I'd flag. And the **on-premises data gateway** is a Logic Apps and Power Platform component, not an APIM one.

| Option | What it is | When I choose it |
|---|---|---|
| **Self-hosted gateway** | Linux container running the APIM data plane, deployed to Docker or Kubernetes (AKS, Arc-enabled K8s, or your own cluster), federated to a cloud APIM instance. **Developer and Premium tiers only.** | Data residency or latency demands that traffic stay on-prem; the backend can't be reached from Azure at all |
| **VNet injection + ExpressRoute / S2S VPN** | Managed APIM deployed into a VNet (Developer/Premium classic, Premium v2), routing to on-prem over private circuit | You already have the circuit and want one managed control plane and data plane |
| **Private endpoint on APIM** | Inbound private IP for clients calling APIM | Consumers are inside the network. **Does not** help APIM call a private backend |
| **Outbound VNet integration** (Standard v2 / Premium v2) | Managed gateway makes outbound calls into a delegated subnet | v2-tier instance that needs to reach private backends without full injection |
| **On-premises data gateway** | Microsoft's relay agent for Logic Apps (Consumption) and Power Platform connectors — SQL, file share, SAP | Only when the flow is Logic Apps-driven. Not an APIM feature |

The self-hosted gateway facts worth quoting, because they're what an architect will probe:

- **Outbound TCP 443 only** to the configuration endpoint `<service-name>.configuration.azure-api.net` and the instance's public IP. No inbound holes in the firewall.
- It **sends a heartbeat every minute** and **polls for configuration every 10 seconds**.
- It **fails static**: on losing Azure connectivity, running gateways keep serving from the in-memory configuration; with local configuration backup enabled on a persistent volume, a *stopped* gateway can also start from the last good config. Without backup, a stopped gateway can't start. That's the question to ask before you promise availability.
- Deploy it to AKS **with the Helm chart** (which pins the version via the chart's app version rather than a rolling `latest` tag) — which is the JD's Kubernetes + Helm responsibility and your chance to link the two: see [K8s](04-microservices-containers-kubernetes.md).
- Known gaps versus the managed gateway: no built-in cache (use an external Redis-compatible one), no TLS session resumption, no client certificate renegotiation, no resource logs to Azure Monitor (metrics and local logs, or OpenTelemetry Collector, instead), and rate-limit counters synchronise across cluster replicas but **not** with the cloud gateway.

**Say this:** *"The decision is really about where the data is allowed to be. If a payment instruction can't leave the datacentre, the gateway goes to the data. If it can, the managed gateway with a private circuit is less to operate."*

**If they push back — "what about the classic tier's 'Total request duration'?"** — Worth knowing that gateway limits differ by tier: the Consumption tier caps total request duration at 30 seconds, while classic and v2 don't cap it; buffered payload size is 500 MiB on classic against 2 MiB on v2 and Consumption. A slow legacy SOAP call is exactly the workload that runs into those, so the tier choice is an architecture decision, not a procurement one.

---

### Q59. What breaks in production with a SOAP-to-REST facade, and how do you operate it?
`[HARD — this is JD responsibility 9: troubleshoot, optimise, document, runbooks]`

**Answer:**

> The failures are boringly consistent: single-element arrays collapsing into objects, namespace drift after a vendor patch, nulls that mean two different things, and faults that look like outages. The operational answer is a contract test in the pipeline that replays recorded envelopes against the current WSDL, correlation IDs flowed end to end, alerts that key on fault codes rather than HTTP 500 counts, and a runbook that tells the on-call engineer how to tell "the mainframe is down" from "someone typed a bad policy number".

| Failure | Why | Mitigation |
|---|---|---|
| `insured` is an object with one policy holder and an array with two | XML has no array marker; conversion infers it | `always-array-child-elements="true"` on `xml-to-json`, or normalise in policy. Pin it in the OpenAPI schema and contract-test both cases |
| Client gets XML instead of JSON | `consider-accept-header` defaults to **true**, and the client sent no `Accept` | Set `consider-accept-header="false"` with `apply="always"` |
| Everything breaks after a vendor release | New namespace, added mandatory element, reordered `sequence` | Pin the WSDL in Git; nightly job diffs the live `?wsdl` against it and raises a ticket before the vendor's release note arrives |
| `null` versus missing field | `nillable="true"` vs `minOccurs="0"` (Q51) | Decide per field, document it in the mapping table, and control it with `set-body`'s `xsi-nil="blank\|null"` |
| Retry storms on a healthy backend | Business faults arriving as HTTP 500 (Q48) | Map faults to 4xx at the facade; retry only `Server`/`Receiver` faults and transport errors |
| Timeouts under load | Legacy service has a small thread pool; gateway has none | Rate limit at the gateway *below* the backend's capacity, explicit `forward-request timeout`, and a circuit breaker on the APIM backend resource |
| A slow call cascades | Facade timeout longer than the caller's | Timeout budget decreasing outward: client 60s > gateway 30s > backend 25s |
| Duplicate postings | Client retried a non-idempotent SOAP operation through the facade | Idempotency key at the facade (§3) with a dedupe cache; never make a write operation look retryable if it isn't |
| Support can't trace anything | SOAP has no built-in correlation | Generate/propagate a correlation ID inbound, put it in a SOAP header if the backend accepts one, log it in App Insights, return it in the error body (§7, Q31) |

**The runbook I'd write** — one page, in the repo next to the policy, because the JD asks for operational runbooks by name:

1. **Contract**: link to the pinned WSDL, the OpenAPI spec, and the field-level mapping table (REST field → XPath → type → nullability rule).
2. **Fault map**: SOAP fault code → HTTP status → is it retryable → who owns the fix. This table *is* the triage decision tree.
3. **Diagnose in this order**: APIM request trace for the correlation ID → is it a fault or a transport error → if fault, look up the code in the fault map → if transport, check the self-hosted gateway pods / circuit-breaker state → then, and only then, call the backend team.
4. **Known-good probe**: a curl that hits a read-only operation with a fixture policy number, so on-call can prove liveness in 10 seconds.
5. **Escalation**: backend owner, vendor SLA, and the credential rotation procedure (Key Vault named value refresh) — because an expired service credential presents as a blanket 500 storm and is the most common false alarm.

**If they push back — "how do you test this without the legacy system?"** — Three layers. Contract tests replay recorded request/response envelopes against a schema-validating stub generated from the pinned WSDL, and they run on every PR. Integration tests run against the vendor's UAT endpoint on a schedule, because vendor UAT is never reliable enough to gate a build. And a synthetic transaction in production hits the read-only probe every few minutes and feeds the availability SLO. That's the split that keeps the pipeline fast and the signal honest.

## 13. GraphQL

The JD lists GraphQL fourth, and in an integration platform team you will almost certainly be asked *"when would you use it"* rather than *"write me a resolver."* Have the trade-off answer loaded first, the code second.

### Q60. What is GraphQL, and what problem does it actually solve?
`[EASY — but the follow-up is where it's won]`

> **Answer:** GraphQL is a query language and execution engine over a strongly-typed schema. The client sends a query describing exactly the shape of the data it wants and gets that shape back. The problem it solves is **over-fetching and under-fetching**: with REST, a mobile screen either pulls three fat resources it mostly discards, or makes six chatty round trips to stitch a view together. With GraphQL that screen is one request against one schema.

The current ratified specification is the **September 2025** edition (released 4 Sep 2025), which supersedes the long-standing **October 2021** edition. Nothing in day-to-day usage changed; it is clarifications plus a decade of accumulated errata.

The type system in SDL — this is a securities-domain schema, which is the right flavour of example for EY:

```graphql
scalar DateTime

type Query {
  portfolio(id: ID!): Portfolio
  portfolios(ownerId: ID!, first: Int = 20, after: String): PortfolioConnection!
}

type Mutation {
  submitInstruction(input: SubmitInstructionInput!): SubmitInstructionPayload!
}

type Subscription {
  settlementStatusChanged(portfolioId: ID!): Instruction!
}

type Portfolio {
  id: ID!
  name: String!
  baseCurrency: Currency!
  positions: [Position!]!          # non-null list of non-null Positions
  instructions(status: InstructionStatus): [Instruction!]!
}

type Position {
  instrument: Instrument!          # resolved from a different backend
  quantity: Float!
  marketValue: Money
}

type Instrument {
  isin: String!
  name: String!
}

type Money { amount: String!  currency: Currency! }

enum Currency { GBP USD EUR INR }
enum InstructionStatus { RECEIVED MATCHED SETTLED FAILED }

input SubmitInstructionInput {
  portfolioId: ID!
  isin: String!
  quantity: Float!
  side: Side!
  clientRequestId: String!         # your idempotency key — see §3
}

enum Side { BUY SELL }

type SubmitInstructionPayload {
  instruction: Instruction
  userErrors: [UserError!]!        # business errors go HERE, not in the errors array
}

type UserError { field: [String!]  message: String! }
```

Four things to point at while you say it:

- **`!` means non-null.** `[Position!]!` = the list is never null and never contains nulls. This is not cosmetic — nullability drives error propagation (Q68).
- **Everything hangs off `Query`, `Mutation`, `Subscription`** — the three root operation types. There is exactly one endpoint, usually `POST /graphql`.
- **`input` types are separate from output types.** You cannot reuse `Portfolio` as an argument.
- **The `userErrors` pattern** on mutation payloads is the industry convention (Shopify popularised it) for *expected* business failures. Reserve the transport `errors` array for things that genuinely went wrong.

**If they push back — "isn't this just OData?"** — Same motivation, different mechanism. OData bolts query semantics onto REST URLs (`$select`, `$expand`, `$filter`) and keeps HTTP caching, per-URL throttling and CDN behaviour. GraphQL replaces the URL space with a schema and loses all of that. On a partner-facing financial API I'd take OData or plain REST with sparse fieldsets; GraphQL is for a first-party BFF where one team owns both ends.

---

### Q61. Query vs mutation vs subscription — what's the actual difference?
`[EASY]`

> **Answer:** `Query` fields are read-only and the engine is allowed to resolve them **in parallel**. `Mutation` fields are executed **serially, in the order they appear in the document**, because each one can change state the next one reads. `Subscription` is a long-lived stream — one event source, one payload per event — and it needs a transport that isn't request/response, normally WebSocket or SSE.

That serial-vs-parallel rule is a genuine spec detail most candidates miss, and it's the reason you can send three mutations in one document and rely on ordering:

```graphql
mutation Rebalance {
  sell: submitInstruction(input: {portfolioId: "P1", isin: "GB0002634946", quantity: 100, side: SELL, clientRequestId: "a1"}) { instruction { id } }
  buy:  submitInstruction(input: {portfolioId: "P1", isin: "US0378331005", quantity: 50,  side: BUY,  clientRequestId: "a2"}) { instruction { id } }
}
```

`sell:` and `buy:` are **aliases** — they let you call the same field twice in one document. Note them, because aliases are also the cheapest DoS vector on a GraphQL endpoint (Q65).

Transport-wise: queries and mutations go over HTTP. Per the GraphQL-over-HTTP specification, `POST` must be supported and `GET` may be, but **`GET` must never execute a mutation** — a server should answer `405 Method Not Allowed`. Subscriptions run over `graphql-transport-ws` (the modern `graphql-ws` protocol) or SSE.

**If they push back — "so should I use subscriptions for our settlement feed?"** — Only for a browser or desktop client that is already connected. For service-to-service event flow, a subscription is a worse Kafka: no consumer groups, no replay, no partition ordering, no offset management, and it dies with the socket. Put the event on Service Bus or Kafka and let a gateway fan it out to subscriptions at the edge — see [Messaging](03-messaging-and-event-streaming.md).

---

### Q62. Explain resolvers and the resolver chain.
`[MEDIUM]`

> **Answer:** Every field in the schema has a resolver — a function with the signature `(parent, args, context, info)`. Execution walks the query tree depth-first: the root resolver returns an object, that object becomes the `parent` of the next level's resolvers, and so on. If a field has no explicit resolver, the default resolver just reads the matching attribute or key off `parent`. That chain is the whole execution model, and it's also exactly why N+1 happens.

For `{ portfolio(id:"P1") { positions { instrument { name } } } }` the engine runs:

```
Query.portfolio(parent=None, args={id:"P1"})      -> 1 call
  Portfolio.positions(parent=<Portfolio P1>)      -> 1 call, returns 200 positions
    Position.instrument(parent=<Position>)        -> 200 calls   <-- N+1
      Instrument.name(parent=<Instrument>)        -> default resolver, free
```

Strawberry, in FastAPI shape:

```python
# app/graphql/schema.py
from __future__ import annotations

import strawberry


@strawberry.type
class Instrument:
    isin: str
    name: str


@strawberry.type
class Position:
    isin: str
    quantity: float

    @strawberry.field
    async def instrument(self, info: strawberry.Info) -> Instrument:
        # naive: one downstream call per position — this is the bug
        return await info.context["instrument_client"].get(self.isin)


@strawberry.type
class Portfolio:
    id: strawberry.ID
    name: str

    @strawberry.field
    async def positions(self, info: strawberry.Info) -> list[Position]:
        rows = await info.context["db"].fetch_positions(self.id)
        return [Position(isin=r["isin"], quantity=r["quantity"]) for r in rows]


@strawberry.type
class Query:
    @strawberry.field
    async def portfolio(self, info: strawberry.Info, id: strawberry.ID) -> Portfolio | None:
        row = await info.context["db"].fetch_portfolio(id)
        return Portfolio(id=row["id"], name=row["name"]) if row else None


schema = strawberry.Schema(query=Query)
```

**If they push back — "what's in `info`?"** — The field name, the parent type, the full selection set for this field, the operation's variables, and the path. The selection set is the interesting one: you can inspect it to push projection down into SQL (only select the columns actually asked for) instead of fetching whole rows. That's the second-order optimisation after DataLoader.

---

### Q63. What is the N+1 problem in GraphQL, and how do you fix it?
`[HARD — the single most likely GraphQL question you will get]`

> **Answer:** Because resolvers run per-field-per-object, a query that returns 200 positions calls the instrument resolver 200 times — one query for the list plus N for the children. The fix is **DataLoader**: instead of resolving immediately, each resolver calls `loader.load(key)` which returns a promise, the loader collects every key requested within one tick of the event loop, and then issues **one batched call** for all of them. 201 calls becomes 2. It also gives you per-request caching, so the same ISIN requested twice is fetched once.

The batching function takes a list of keys and must return a list of results **in the same order and the same length** — that contract is where people introduce bugs.

```python
# app/graphql/loaders.py
from __future__ import annotations

import httpx
import strawberry
from strawberry.dataloader import DataLoader


@strawberry.type
class Instrument:
    isin: str
    name: str


async def load_instruments(keys: list[str]) -> list[Instrument | ValueError]:
    """One HTTP call for every ISIN requested in this tick.

    MUST return one entry per key, in key order. Returning an Exception
    instance for a key surfaces as an error on that field only.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            "https://ref-data.internal/instruments:batchGet",
            json={"isins": keys},
        )
        resp.raise_for_status()
        by_isin = {i["isin"]: i for i in resp.json()["instruments"]}

    return [
        Instrument(isin=k, name=by_isin[k]["name"])
        if k in by_isin
        else ValueError(f"unknown ISIN {k}")
        for k in keys
    ]
```

Wire one loader **per request** — never a module-level singleton, or you leak one user's cached data into another user's response:

```python
# app/main.py
from fastapi import Depends, FastAPI, Request
from strawberry.fastapi import GraphQLRouter
from strawberry.dataloader import DataLoader

from app.graphql.loaders import load_instruments
from app.graphql.schema import schema


async def get_context(request: Request) -> dict:
    # A NEW DataLoader per request: batching window + cache are request-scoped.
    return {
        "request": request,
        "instrument_loader": DataLoader(load_fn=load_instruments),
        "db": request.app.state.db,
    }


graphql_app = GraphQLRouter(schema, context_getter=get_context, graphql_ide=None)

app = FastAPI(title="Portfolio BFF")
app.include_router(graphql_app, prefix="/graphql")
```

And the resolver stops calling downstream itself:

```python
# app/graphql/schema.py — the fixed Position type
import strawberry

from app.graphql.loaders import Instrument


@strawberry.type
class Position:
    isin: str
    quantity: float

    @strawberry.field
    async def instrument(self, info: strawberry.Info) -> Instrument:
        return await info.context["instrument_loader"].load(self.isin)
```

**If they push back — "why not just join it in the first query?"** — Because the client may not have asked for `instrument`, and eagerly joining means you pay for it on every query. DataLoader keeps the cost proportional to what was actually requested. And when the child lives behind an HTTP boundary — a different microservice, an ERP, a market-data vendor — there is no join to do; batching is the only lever you have.

**Second push-back — "does the downstream support batch?"** — That is the real constraint, and it's a platform-team job: if ref-data has no `batchGet`, I add one, or put a batching facade in front of it. This is the same problem as a Logic App looping one call per row; the fix is the same shape.

---

### Q64. Why is GraphQL hard to cache?
`[HARD — a great differentiator answer]`

> **Answer:** Because HTTP caching keys on the URL and the method, and GraphQL throws both away: every request is `POST /graphql` with the query in the body. A CDN, a reverse proxy, APIM's `cache-lookup` policy, and the browser's own cache are all blind to it — `POST` isn't cacheable by default, and even if it were, there's no URL to key on. You lose the entire free layer that REST gets for nothing.

What you can do about it, in order of preference:

| Option | How it works | Cost |
|---|---|---|
| **Persisted queries over `GET`** | Client sends a SHA-256 hash in the query string; now there *is* a URL to key on, and it's a `GET` | Client tooling + a query registry (Q66) |
| **Response cache at the gateway keyed on a normalised body hash** | Hash the query + variables + auth scope, use that as the cache key | You must include auth scope in the key or you leak data |
| **Field-level / entity cache in the server** | Cache the resolved entity, not the response — Redis keyed on `Instrument:GB000...` | Correct but you build and invalidate it yourself |
| **DataLoader per-request cache** | Free, automatic, but scoped to a single request | Doesn't survive the request |

The rule I state out loud: **never cache a GraphQL response without the caller's authorisation context in the key.** In GraphQL the same document returns different data for different users far more often than a REST URL does, because authorisation is applied per field.

**If they push back — "so put Azure CDN in front of it"** — Only in front of persisted `GET` queries, and only for genuinely public data. In a financial-services engagement, positions and instructions are never edge-cacheable; reference data — instruments, calendars, currency lists — is, and that's exactly the split I'd make: public reference data behind a cached REST endpoint, entitled data behind an uncached GraphQL endpoint.

---

### Q65. How do you rate-limit and protect a GraphQL endpoint?
`[HARD]`

> **Answer:** You cannot rate-limit GraphQL the way you rate-limit REST, because "one request" is meaningless — a single 200-byte query can fan out into a million resolver calls. So you protect it in three layers: **depth limiting** to kill recursive queries, **cost/complexity analysis** to charge each query a computed number of points against a budget, and **persisted queries** to make the set of possible queries finite. Plain requests-per-minute is the last line, not the first.

The attack you are defending against, on a schema with a cycle (`Portfolio -> positions -> portfolio -> ...`):

```graphql
query Bomb {
  portfolio(id: "P1") {
    positions { portfolio { positions { portfolio { positions {
      portfolio { positions { instrument { name } } } } } } } }
  }
}
```

That is ~250 bytes and unbounded work. Aliases make it worse — 100 aliases of the same expensive field in one document is 100× the load with no extra depth.

**Layer 1 — depth limit, in the service:**

```python
import strawberry
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules, QueryDepthLimiter

from app.graphql.schema import Query, Mutation

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=8),
        AddValidationRules([NoSchemaIntrospectionCustomRule]),  # prod only — Q69
    ],
)
```

`QueryDepthLimiter` runs as a **validation rule**, i.e. before execution — the query is rejected without a single resolver firing. That's the property you want; anything that measures cost *during* execution has already paid for it.

**Layer 2 — cost analysis.** Annotate each field with a cost, multiply by list sizes (`first`/`limit` arguments), sum, and reject over budget. Shopify and GitHub both publish their formulas; GitHub's public GraphQL API budgets 5,000 points/hour with node-count-based scoring. Roll your own with the same shape: a leaf costs 1, an entity that crosses a service boundary costs 10, a paginated field multiplies its children by the requested page size.

**Layer 3 — at the gateway.** Azure APIM has a first-class policy for this on GraphQL APIs:

```xml
<inbound>
    <base />
    <validate-graphql-request error-variable-name="graphqlErrors" max-size="102400" max-depth="6">
        <authorize>
            <rule path="/__*" action="reject" />
            <rule path="/Mutation/deleteInstruction" action="reject" />
            <rule path="/Query/portfolios" action="allow" />
        </authorize>
    </validate-graphql-request>
    <rate-limit-by-key calls="600" renewal-period="60"
        counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)" />
</inbound>
```

Numbers worth knowing because they are hard limits, not guidance:

- `max-size` is **required**, in bytes, and the **maximum allowed value is 102,400 bytes (100 KB)** — you must contact Azure support to raise it.
- `max-depth` is optional and **defaults to 6**.
- The policy validates GraphQL requests with **up to 250 query fields across all levels**.
- `path="/__*"` is the introspection system — `action="reject"` is how you disable introspection at the gateway even when the backend still allows it.
- Rule actions are `allow`, `remove` (drops the field — surfaces as a *field* error), `reject` (fails the request — a *request* error), and `ignore` (fall through to the next rule). Most-specific path wins: `/Query/listUsers` beats `/Query/*`.

**If they push back — "isn't depth 6 too low?"** — For a BFF, yes; that default will reject legitimate queries on any schema with two levels of nesting plus a connection wrapper. I'd set it from the deepest query my own clients actually send, plus two, and I'd measure that from the persisted-query registry rather than guessing. The point of the low default is that it fails closed.

---

### Q66. What are persisted queries, and why do they fix both the caching and the DoS problem?
`[HARD — the answer that makes you sound like you've run one in production]`

> **Answer:** A persisted query replaces the query document with a hash. The client sends `{"extensions":{"persistedQuery":{"version":1,"sha256Hash":"..."}}}` instead of 4 KB of GraphQL. That fixes caching, because a hash is short enough to go in a `GET` query string, which gives a CDN a URL to key on; and it fixes DoS, because if you run a **safelist** — only queries registered at build time are executable — the set of possible queries is finite and every one of them has been cost-analysed offline. Arbitrary queries stop being a thing.

Two distinct mechanisms that people conflate, and the distinction is the senior part of the answer:

| | Automatic Persisted Queries (APQ) | Persisted query list / safelist |
|---|---|---|
| Registered | At runtime, on first use | At build time, from the client bundle |
| Unknown hash | Server returns `PERSISTED_QUERY_NOT_FOUND`; client retries with the full query and the server learns it | Rejected. Full stop. |
| Buys you | Bandwidth + CDN cacheability | Bandwidth + CDN + **security** |
| Is it a security control? | **No** — anything can register a query | **Yes** |

The APQ round trip, exactly:

1. Client `GET /graphql?extensions={"persistedQuery":{"version":1,"sha256Hash":"b1946ac9..."}}` — cache miss.
2. Server has never seen that hash → responds with a `PERSISTED_QUERY_NOT_FOUND` error.
3. Client retries as `POST` with **both** the `query` string and the same `extensions` block.
4. Server verifies `sha256(query) == sha256Hash`, stores it, executes, responds.
5. Every subsequent client using that hash gets step 1 as a hit — and if it went out as a `GET` with a `Cache-Control` header, the CDN answers it without touching your origin.

Apollo clients enable the `GET` half with `useGETForHashedQueries: true`; without it you get the bandwidth saving but not the cacheability.

**If they push back — "we have third-party clients, we can't build their bundles"** — Then APQ for bandwidth, and cost analysis plus depth limits for safety; the safelist only works when you own the client. And that trade-off *is* the answer to Q70: if you cannot safelist and cannot cache, you are running an uncachable, unbounded, publicly-reachable compute endpoint, which is a strange thing to hand a partner bank.

---

### Q67. What is schema federation?
`[MEDIUM–HARD]`

> **Answer:** Federation lets several teams each own a **subgraph** — their own GraphQL service and schema — while clients see one **supergraph**. A router composes the subgraph schemas into a single schema at build time, then, at query time, plans the query into sub-queries and executes them across services. The glue is the `@key` directive: a type declares its primary key, and any subgraph can extend that type by resolving it from the key. It's the GraphQL answer to "who owns the schema" in a microservices estate — which is exactly the platform-team question.

```python
# positions-subgraph — owns Portfolio, contributes positions
import strawberry


@strawberry.federation.type(keys=["id"])
class Portfolio:
    id: strawberry.ID
    name: str

    @classmethod
    async def resolve_reference(cls, id: strawberry.ID) -> "Portfolio":
        # Called by the router when another subgraph hands us {__typename, id}
        row = await db.fetch_portfolio(id)
        return cls(id=row["id"], name=row["name"])


@strawberry.type
class Query:
    @strawberry.field
    async def portfolio(self, id: strawberry.ID) -> Portfolio | None: ...


schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

```python
# risk-subgraph — does NOT own Portfolio, only adds a field to it
import strawberry


@strawberry.federation.type(keys=["id"])
class Portfolio:
    id: strawberry.ID

    @strawberry.field
    async def var_95(self) -> float:
        return await risk_engine.value_at_risk(self.id)


schema = strawberry.federation.Schema(query=Query, types=[Portfolio], enable_federation_2=True)
```

Machinery under the hood, which is what they're probing for: the router calls a reserved field `Query._entities(representations: [_Any!]!)` on each subgraph, passing `{"__typename": "Portfolio", "id": "P1"}`, and `resolve_reference` is what answers it. `Query._service { sdl }` is how the composer retrieves each subgraph's schema. Directives you'll be asked to name: `@key` (entity identity), `@external` (field owned elsewhere), `@requires` (I need this other field to compute mine), `@provides` (I can return this field inline, skip the hop), `@shareable` (Federation 2 — more than one subgraph may resolve this field).

**If they push back — "isn't this just an API gateway?"** — No, and the difference matters. A gateway routes a request to one backend. A federation router *plans and joins* — it decomposes one client query into a DAG of subgraph calls, waits, stitches the results, and returns one response. It's closer to a distributed query planner than a proxy. Which is also why it's a serious operational commitment: composition is now a build-time gate in CI, and a subgraph that breaks composition breaks everyone's deploy. Schema checks in the pipeline are non-negotiable — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

---

### Q68. How does error handling work in GraphQL?
`[HARD — a genuine trap]`

> **Answer:** The classic answer is "GraphQL always returns HTTP 200 with an `errors` array" — and for the legacy `application/json` content type that's essentially true, which is exactly the trap: your monitoring, your retry policy and your APIM `on-error` handler are all watching status codes and will see a 100% success rate while the API is broken. The spec distinguishes **request errors** (the document couldn't be parsed, validated, or the variables were wrong — no `data` key at all) from **field errors** (execution started, one resolver threw — `data` is present with a `null` in it, plus an `errors` entry).

The response shape:

```json
{
  "data": { "portfolio": { "id": "P1", "positions": null } },
  "errors": [
    {
      "message": "Ref-data timeout",
      "path": ["portfolio", "positions", 3, "instrument"],
      "locations": [{ "line": 4, "column": 7 }],
      "extensions": { "code": "DOWNSTREAM_TIMEOUT", "correlationId": "9f3c…" }
    }
  ]
}
```

**Null propagation** is the part almost nobody knows and it wins the question: when a field errors, it resolves to `null`. If that field was declared non-null (`Instrument!`), null isn't allowed there, so the error propagates **up to the nearest nullable parent** and nulls that instead. On `[Position!]!` inside `Portfolio!`, one bad instrument can null out the entire `portfolio`. **This is why over-using `!` is dangerous** — a strict schema converts a partial failure into a total one.

The modern transport rules, from the GraphQL-over-HTTP spec, apply when the response is `application/graphql-response+json`:

- Response contains a non-null `data` entry → **2xx**; a clean success is **200**.
- Response has **no** `data` entry (a request error) → **4xx or 5xx**. Unparseable document → **400**. Fails GraphQL validation → **422**.
- Mutation attempted over `GET` → **405**.
- For legacy `application/json`, servers keep the same logic but replace the `Content-Type` on 2xx responses — which is how "always 200" became folklore.

*(The current draft also reserves **294** for "data plus errors" partial success — worth knowing exists, don't build on it.)*

Operationally, what I actually do:

1. Business failures never go in `errors` — they go in the mutation payload's `userErrors` field, where they are typed and part of the contract.
2. Every `errors` entry gets `extensions.code` (a stable enum) and `extensions.correlationId`. Clients branch on `code`, never on `message`.
3. Alerting is on **`errors[].extensions.code` rate**, not HTTP status. If your dashboard only shows 5xx, GraphQL is invisible to it.
4. `message` is sanitised in prod — same rule as §8, no stack traces, no SQL, no internal hostnames.

**If they push back — "so how do you make retries work?"** — The client can't blanket-retry a 200. I classify in the client: `extensions.code` in a known-transient set (`DOWNSTREAM_TIMEOUT`, `RATE_LIMITED`) → retry with backoff and jitter; anything else → don't. And I only retry *queries*; retrying a mutation needs the same `clientRequestId` idempotency key you'd use on a REST `POST` — see §3.

---

### Q69. What is introspection and why do you disable it in production?
`[MEDIUM]`

> **Answer:** Introspection is the built-in `__schema` and `__type` meta-fields — any client can ask the server to describe its entire schema, which is how GraphiQL, Postman and codegen tools get autocompletion. In production on an externally-reachable endpoint I disable it, because it hands an attacker a complete map of every type, field, argument and deprecated-but-still-live operation. It's the GraphQL equivalent of leaving a Swagger UI with "Try it out" on your public gateway.

Two levels, use both:

```python
# service level — a validation rule, so introspection is rejected before execution
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules

extensions = [AddValidationRules([NoSchemaIntrospectionCustomRule])]
```

```xml
<!-- gateway level — APIM, for the pass-through GraphQL API -->
<validate-graphql-request max-size="102400" max-depth="8">
    <authorize><rule path="/__*" action="reject" /></authorize>
</validate-graphql-request>
```

Also disable the IDE — `GraphQLRouter(schema, graphql_ide=None)` in Strawberry — because a shipped GraphiQL page is both an introspection client and a CSRF surface.

**If they push back — "then how do our developers get the schema?"** — From the artefact, not the endpoint. The build publishes `schema.graphql` to the internal package feed or the developer portal, and codegen runs against that file. Introspection stays enabled in dev and UAT, disabled in prod. Same principle as OpenAPI: the contract is a versioned artefact in source control, not something you scrape from a running server.

**Honest caveat worth saying:** disabling introspection is defence in depth, not a control. Field-name suggestion attacks ("did you mean `settlementDate`?") and clientside bundles leak schema anyway. It raises cost; it doesn't replace authorisation on every field.

---

### Q70. When would you NOT use GraphQL?
`[MEDIUM — say this crisply and you've closed the section]`

> **Answer:** I default to REST for anything partner-facing or integration-shaped, and reach for GraphQL only when one team owns both the client and the schema and the client is genuinely view-driven. Concretely I'd say no to GraphQL for: partner and B2B APIs, simple CRUD, anything that needs HTTP caching or CDN offload, anything that needs per-endpoint throttling or per-endpoint metering, file upload/download, and any flow where the consumer is another backend service.

The list, with the actual reason for each:

| Don't use GraphQL when… | Why |
|---|---|
| **The consumer is a partner or a bank** | They want a WSDL or an OpenAPI file, a stable URL per operation, and a rate-limit contract. Handing a counterparty an introspectable schema and "just ask for what you need" is not a governance story that passes review. |
| **It's simple CRUD** | You've added an execution engine, a schema registry, a cost analyser and a new class of DoS to replace six lines of routing. |
| **You need HTTP caching** | One `POST` endpoint defeats every cache between you and the client (Q64). |
| **You need per-operation throttling or metering** | The gateway sees one operation. Product tiers, per-endpoint quotas and per-call billing all key on the endpoint, which no longer exists. |
| **You need file transfer** | Multipart uploads are a bolt-on spec; presigned URLs over REST are strictly better. |
| **The caller is another service** | Service-to-service contracts want fixed shapes for stability, not client-chosen ones. Use REST, gRPC ([§10](#10-http11-vs-http2-vs-http3-vs-grpc)) or events. |
| **You have a hard latency SLO on a fan-out** | The cost of a query is not visible from the request; a client can accidentally build a slow query and you find out in production. |

Where I *do* say yes: a **BFF for a rich internal UI** — a wealth-management advisor dashboard pulling positions, valuations, risk and CRM notes from four systems onto one screen. That's the case where over-fetching is real, the client is ours, the query set is finite and safelistable, and the alternative is either six round trips or a bespoke aggregation endpoint per screen.

**If they push back — "our client asked for GraphQL specifically"** — Then I'd scope it as a GraphQL facade in front of existing REST/SOAP services rather than a rewrite, put it behind APIM with `validate-graphql-request`, persist the query set, and keep the REST APIs as the system of record for integration partners. Two consumers, two contracts, one set of services underneath. That's the same facade pattern as [§12](#12-exposing-soap-as-rest-in-azure-apim), just with a different front door.

---

## 14. OpenAPI / Swagger

### Q71. OpenAPI 3.0 vs 3.1 — what changed and does it matter?
`[MEDIUM — a very common opener]`

> **Answer:** The headline change in 3.1 is that the Schema Object became **fully compatible with JSON Schema draft 2020-12**. In 3.0 OpenAPI used a modified subset of JSON Schema draft-04 — close enough to be confusing, different enough to break every validator. 3.1 also adds a top-level **`webhooks`** section, makes `paths` optional, and adds `mutualTLS` as a security scheme type. In practice: 3.1 if my toolchain supports it, 3.0.3 if I have to feed it to something that doesn't — and Azure APIM is that something.

Versions and dates, so you can be precise:

| Version | Released | What it brought |
|---|---|---|
| 3.0.3 | 20 Feb 2020 | The long-lived enterprise baseline |
| **3.1.0** | **15 Feb 2021** | Full JSON Schema 2020-12, `webhooks`, `jsonSchemaDialect`, `mutualTLS`, SPDX `license.identifier`, `info.summary`, `$ref` with sibling `summary`/`description` |
| 3.1.1 | 2024 | Editorial/clarification patch, no new features |
| 3.2.0 | 19 Sep 2025 | Nested/multipurpose tags, additional HTTP methods including `QUERY` |

Concrete differences you can name:

- **Nullability.** 3.0: `type: string, nullable: true`. 3.1: `type: [string, "null"]` — real JSON Schema, and `nullable` is gone.
- **`exclusiveMinimum`.** 3.0: a boolean modifier on `minimum`. 3.1: a number in its own right.
- **`example` is deprecated** in the Schema Object in favour of the JSON Schema `examples` keyword, which takes an **array**. The spec's own words: *"The `example` field has been deprecated in favor of the JSON Schema `examples` keyword. Use of `example` is discouraged, and later versions of this specification may remove it."*
- **At least one of `paths`, `components`, or `webhooks` must be present** — so a webhooks-only or schemas-only document is legal.
- `jsonSchemaDialect` lets you declare the default `$schema` for every Schema Object in the document.

**If they push back — "so should we move to 3.1?"** — Only after checking the sinks. Azure APIM supports **OpenAPI 2.0, 3.0.x up to 3.0.3, and 3.1 for import only** — Microsoft's own words are that 3.1 is *"import-compatible only, not feature-compatible"*: 3.1-specific constructs are ignored, downgraded to 3.0 behaviour, or removed on import. So on an Azure engagement my source of truth is 3.1 (because FastAPI emits it and JSON Schema tooling wants it), and my pipeline emits a **downgraded 3.0.3 artefact for APIM**. That's a paved-road decision, and it's the kind of answer that separates a platform engineer from an app developer.

---

### Q72. Design-first or code-first — which do you argue for?
`[MEDIUM — a values question disguised as a tooling question]`

> **Answer:** Design-first on any contract with more than one team or any external consumer, code-first for internal services owned end-to-end by one team. On a client engagement I argue for design-first almost every time, because the contract is the thing the client, the partner and three delivery teams agree on **before** anyone builds, and it lets frontend, backend and the integration layer proceed in parallel against a mock. The failure mode of code-first is that the contract becomes an accident of your Pydantic models.

| | Design-first | Code-first |
|---|---|---|
| Source of truth | `openapi.yaml` in Git, reviewed in a PR | Your handlers and models |
| Parallelism | Mock server from day one (Prism, WireMock) | Consumers wait for the service |
| Drift risk | Spec and code diverge → contract tests catch it | Spec always matches code — including matching its mistakes |
| Governance | Spectral lints the artefact; breaking changes gated in CI | Standards enforced by review, i.e. not enforced |
| Best for | Partner APIs, multi-team, anything in APIM | Internal service, one team, fast iteration |

The pragmatic middle I actually run: **design-first for the contract, code-first for the implementation, contract tests to bind them.** The YAML is authored and reviewed; FastAPI implements it; `schemathesis` (Q78) runs the published spec against the running service in CI and fails the build on divergence. You get the governance of design-first without asking developers to hand-maintain YAML that mirrors their models.

**Codegen and its failure modes** — since they'll ask:

- Generated clients get committed and then hand-edited. Next regeneration blows the edits away. **Rule: generated code lives in a separate package, is never edited, and is regenerated in CI, not on someone's laptop.**
- Generators materialise every `$ref` into a class, so a spec with `oneOf` and no `discriminator` produces unusable union types.
- `operationId` is what most generators use for the method name. Miss it and you get `getOrdersOrderIdLinesGet`. Set `operationId` on every operation, always — APIM uses it too (Q79).
- Server-side codegen (generate stubs from the spec) works once and then fights you forever. I generate **clients and models**, never servers.
- The generator's own version becomes a build dependency: pin it, or a minor bump silently changes your public SDK.

**If they push back — "FastAPI already generates the spec, why write YAML?"** — Because on a client engagement the spec is a deliverable that gets reviewed, versioned and signed off before the service exists, and because FastAPI's output reflects what someone typed rather than what was agreed. Where the team is one squad shipping an internal service, I happily invert it — export FastAPI's spec in CI, lint it with Spectral, diff it with oasdiff, and treat the exported artefact as the contract.

---

### Q73. Show me a real OpenAPI spec for a small integration API.
`[HARD — have this shape in your head; you may be asked to write it on a shared screen]`

> **Answer:** Here's a payment-instruction intake API — the shape I'd actually ship: cursor pagination, an idempotency key on the POST, RFC 9457 problem responses, OAuth2 client credentials plus mTLS, a `oneOf` with a discriminator on the event payload, and a webhook declared in the contract rather than in a Word document.

```yaml
openapi: 3.1.0
info:
  title: Payment Instruction API
  summary: Intake and status reporting for cross-border payment instructions.
  version: 1.4.0
  contact:
    name: Integration Platform
    email: integration.platform@example.com
  license:
    name: Proprietary
    identifier: LicenseRef-Internal-1.0
jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema

servers:
  - url: https://api.example.com/payments/v1
    description: Production
  - url: https://api-uat.example.com/payments/v1
    description: UAT

security:
  - oauth2ClientCredentials: [payments.write]

tags:
  - name: instructions
    description: Payment instructions submitted by upstream custodian systems.

paths:
  /instructions:
    get:
      operationId: listInstructions
      summary: List payment instructions
      tags: [instructions]
      parameters:
        - $ref: '#/components/parameters/Cursor'
        - $ref: '#/components/parameters/Limit'
        - name: status
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/InstructionStatus'
      responses:
        '200':
          description: A page of instructions.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InstructionPage'
        '401':
          $ref: '#/components/responses/Problem'
        '429':
          $ref: '#/components/responses/RateLimited'

    post:
      operationId: createInstruction
      summary: Submit a payment instruction
      tags: [instructions]
      security:
        - oauth2ClientCredentials: [payments.write]
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          description: Client-generated UUID. Replays return the original result.
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InstructionCreate'
            examples:
              gbpFasterPayment:
                summary: GBP domestic
                value:
                  amount: "1250.00"
                  currency: GBP
                  debtorAccount: "GB29NWBK60161331926819"
                  creditorAccount: "GB94BARC10201530093459"
                  valueDate: "2026-09-01"
      responses:
        '201':
          description: Instruction accepted.
          headers:
            Location:
              description: Canonical URI of the created instruction.
              schema:
                type: string
                format: uri-reference
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Instruction'
        '409':
          description: Idempotency-Key reused with a different payload.
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/Problem'
        '422':
          $ref: '#/components/responses/Problem'

  /instructions/{instructionId}:
    parameters:
      - name: instructionId
        in: path
        required: true
        schema:
          type: string
          pattern: '^[0-9A-HJKMNP-TV-Z]{26}$'
          description: ULID.
    get:
      operationId: getInstruction
      summary: Retrieve a payment instruction
      tags: [instructions]
      responses:
        '200':
          description: The instruction.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Instruction'
        '404':
          $ref: '#/components/responses/Problem'

webhooks:
  instructionStatusChanged:
    post:
      operationId: onInstructionStatusChanged
      summary: Sent to the registered endpoint when an instruction changes state.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InstructionEvent'
      responses:
        '204':
          description: Acknowledged. Any non-2xx triggers redelivery.

components:
  securitySchemes:
    oauth2ClientCredentials:
      type: oauth2
      description: Microsoft Entra ID client credentials flow.
      flows:
        clientCredentials:
          tokenUrl: https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token
          scopes:
            payments.read: Read instructions
            payments.write: Submit instructions
    mtls:
      type: mutualTLS
      description: Client certificate pinned per counterparty. Required in production.

  parameters:
    Cursor:
      name: cursor
      in: query
      required: false
      description: Opaque cursor from the previous page's `nextCursor`.
      schema:
        type: string
    Limit:
      name: limit
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 200
        default: 50

  responses:
    Problem:
      description: Error, as RFC 9457 Problem Details.
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Problem'
    RateLimited:
      description: Too many requests.
      headers:
        Retry-After:
          schema:
            type: integer
        RateLimit-Reset:
          schema:
            type: integer
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Problem'

  schemas:
    Money:
      type: string
      pattern: '^-?[0-9]+\.[0-9]{2}$'
      description: Decimal string. Never a float — see the traps section.
      examples: ["1250.00", "-42.05"]

    Currency:
      type: string
      enum: [GBP, USD, EUR, INR]

    InstructionStatus:
      type: string
      enum: [RECEIVED, VALIDATED, SENT, SETTLED, REJECTED]

    InstructionCreate:
      type: object
      required: [amount, currency, debtorAccount, creditorAccount, valueDate]
      additionalProperties: false
      properties:
        amount:
          $ref: '#/components/schemas/Money'
        currency:
          $ref: '#/components/schemas/Currency'
        debtorAccount:
          type: string
          minLength: 15
          maxLength: 34
        creditorAccount:
          type: string
          minLength: 15
          maxLength: 34
        valueDate:
          type: string
          format: date
        reference:
          type: [string, "null"]
          maxLength: 140

    Instruction:
      allOf:
        - $ref: '#/components/schemas/InstructionCreate'
        - type: object
          required: [id, status, createdAt]
          properties:
            id:
              type: string
            status:
              $ref: '#/components/schemas/InstructionStatus'
            createdAt:
              type: string
              format: date-time
            settledAt:
              type: [string, "null"]
              format: date-time

    InstructionPage:
      type: object
      required: [data, nextCursor]
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Instruction'
        nextCursor:
          type: [string, "null"]
          description: Null when this is the last page.

    InstructionEvent:
      oneOf:
        - $ref: '#/components/schemas/InstructionSettled'
        - $ref: '#/components/schemas/InstructionRejected'
      discriminator:
        propertyName: eventType
        mapping:
          instruction.settled: '#/components/schemas/InstructionSettled'
          instruction.rejected: '#/components/schemas/InstructionRejected'

    InstructionSettled:
      type: object
      required: [eventType, instructionId, settledAt]
      properties:
        eventType:
          type: string
          const: instruction.settled
        instructionId:
          type: string
        settledAt:
          type: string
          format: date-time

    InstructionRejected:
      type: object
      required: [eventType, instructionId, reasonCode]
      properties:
        eventType:
          type: string
          const: instruction.rejected
        instructionId:
          type: string
        reasonCode:
          type: string
          enum: [INSUFFICIENT_FUNDS, INVALID_ACCOUNT, SANCTIONS_HOLD]

    Problem:
      type: object
      required: [type, title, status]
      properties:
        type:
          type: string
          format: uri
          default: about:blank
        title:
          type: string
        status:
          type: integer
          minimum: 400
          maximum: 599
        detail:
          type: string
        instance:
          type: string
          format: uri-reference
        correlationId:
          type: string
```

Points to volunteer while it's on screen, because they're the ones an experienced reviewer looks for: `operationId` on every operation; `additionalProperties: false` on request bodies so typos are rejected instead of silently ignored; `Money` as a **string**, not `number`; `type: [string, "null"]` rather than 3.0's `nullable`; `const` on the discriminator property so each branch validates standalone; and shared `parameters` and `responses` in `components` so the pagination contract is defined once.

---

### Q74. Show me the FastAPI code that generates the equivalent spec.
`[MEDIUM — plays directly to your strength; use it to take control of the interview]`

> **Answer:** FastAPI has emitted **OpenAPI 3.1.0 with JSON Schema 2020-12 since version 0.99.0** (30 June 2023), which is also when top-level `webhooks` support and Swagger UI 5 landed. So the same contract is expressible in code, and the important trick is to be explicit about `operation_id`, `responses` and `response_model` — the defaults produce a spec you would not hand to a client.

```python
# app/main.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, FastAPI, Header, Path, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="Payment Instruction API",
    summary="Intake and status reporting for cross-border payment instructions.",
    version="1.4.0",
    contact={"name": "Integration Platform", "email": "integration.platform@example.com"},
    license_info={"name": "Proprietary", "identifier": "LicenseRef-Internal-1.0"},
    servers=[
        {"url": "https://api.example.com/payments/v1", "description": "Production"},
        {"url": "https://api-uat.example.com/payments/v1", "description": "UAT"},
    ],
    # Kill the interactive docs in production; serve the spec from the portal instead.
    docs_url=None,
    redoc_url=None,
)

router = APIRouter(prefix="/instructions", tags=["instructions"])

MONEY = r"^-?[0-9]+\.[0-9]{2}$"
ULID = r"^[0-9A-HJKMNP-TV-Z]{26}$"


class Currency(str, Enum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"
    INR = "INR"


class InstructionStatus(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    SENT = "SENT"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"


class InstructionCreate(BaseModel):
    # extra="forbid" emits additionalProperties: false
    model_config = ConfigDict(extra="forbid")

    amount: Annotated[str, Field(pattern=MONEY, examples=["1250.00"])]
    currency: Currency
    debtor_account: Annotated[str, Field(min_length=15, max_length=34, alias="debtorAccount")]
    creditor_account: Annotated[str, Field(min_length=15, max_length=34, alias="creditorAccount")]
    value_date: Annotated[date, Field(alias="valueDate")]
    reference: Annotated[str | None, Field(default=None, max_length=140)]


class Instruction(InstructionCreate):
    id: Annotated[str, Field(pattern=ULID)]
    status: InstructionStatus
    created_at: Annotated[datetime, Field(alias="createdAt")]
    settled_at: Annotated[datetime | None, Field(default=None, alias="settledAt")]


class InstructionPage(BaseModel):
    data: list[Instruction]
    next_cursor: Annotated[str | None, Field(alias="nextCursor")]


class Problem(BaseModel):
    """RFC 9457 Problem Details."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    correlation_id: Annotated[str | None, Field(default=None, alias="correlationId")]


class InstructionSettled(BaseModel):
    event_type: Annotated[Literal["instruction.settled"], Field(alias="eventType")]
    instruction_id: Annotated[str, Field(alias="instructionId")]
    settled_at: Annotated[datetime, Field(alias="settledAt")]


class InstructionRejected(BaseModel):
    event_type: Annotated[Literal["instruction.rejected"], Field(alias="eventType")]
    instruction_id: Annotated[str, Field(alias="instructionId")]
    reason_code: Annotated[
        Literal["INSUFFICIENT_FUNDS", "INVALID_ACCOUNT", "SANCTIONS_HOLD"],
        Field(alias="reasonCode"),
    ]


# Pydantic emits oneOf + a discriminator for a tagged union.
InstructionEvent = Annotated[
    InstructionSettled | InstructionRejected,
    Field(discriminator="event_type"),
]

PROBLEM_RESPONSES: dict[int | str, dict] = {
    401: {"model": Problem, "description": "Unauthenticated."},
    422: {"model": Problem, "description": "Validation failed."},
    429: {"model": Problem, "description": "Too many requests."},
}


@router.get(
    "",
    operation_id="listInstructions",
    summary="List payment instructions",
    response_model=InstructionPage,
    responses=PROBLEM_RESPONSES,
)
async def list_instructions(
    cursor: Annotated[str | None, Query(description="Opaque cursor from `nextCursor`.")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    status_filter: Annotated[InstructionStatus | None, Query(alias="status")] = None,
) -> InstructionPage:
    ...


@router.post(
    "",
    operation_id="createInstruction",
    summary="Submit a payment instruction",
    status_code=status.HTTP_201_CREATED,
    response_model=Instruction,
    responses={
        409: {"model": Problem, "description": "Idempotency-Key reused with a different payload."},
        **PROBLEM_RESPONSES,
    },
)
async def create_instruction(
    body: InstructionCreate,
    response: Response,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
) -> Instruction:
    instruction = await service.submit(body, idempotency_key)   # noqa: F821
    response.headers["Location"] = f"/instructions/{instruction.id}"
    return instruction


@router.get(
    "/{instruction_id}",
    operation_id="getInstruction",
    summary="Retrieve a payment instruction",
    response_model=Instruction,
    responses={404: {"model": Problem, "description": "Not found."}, **PROBLEM_RESPONSES},
)
async def get_instruction(
    instruction_id: Annotated[str, Path(pattern=ULID)],
) -> Instruction:
    ...


# OpenAPI 3.1 top-level `webhooks` — FastAPI 0.99+
@app.webhooks.post("instructionStatusChanged", operation_id="onInstructionStatusChanged")
async def instruction_status_changed(body: InstructionEvent) -> None:
    """Sent to the registered endpoint when an instruction changes state.

    Any non-2xx response triggers redelivery with exponential backoff.
    """


app.include_router(router)
```

Export the artefact in CI so the spec is a build output, not a running endpoint:

```python
# scripts/export_openapi.py
import json
import pathlib

from app.main import app

pathlib.Path("openapi.json").write_text(json.dumps(app.openapi(), indent=2))
print(app.openapi()["openapi"])   # -> 3.1.0
```

**If they push back — "the generated spec doesn't look like your hand-written one"** — Correct, and that's the honest bit. FastAPI puts models under `components.schemas` with its own naming, emits `anyOf` where I wrote `oneOf`, and drops in a default `422` `HTTPValidationError`. On a design-first engagement I therefore treat the YAML as truth, generate Pydantic models *from* it, and use `schemathesis` against the hand-written spec to prove the implementation conforms. Code-first is for services where I own both sides.

---

### Q75. What are your rules for `components`, `$ref` and reuse?
`[MEDIUM]`

> **Answer:** Everything that appears more than once goes in `components` and is referenced with `$ref` — schemas, parameters, responses, headers, security schemes. One canonical `Problem` schema, one `Cursor`/`Limit` parameter pair, one `RateLimited` response. The rule I hold to is that a `$ref` should point at a *concept*, not at a shape that happens to match today: `PagedResponse` and `Money` are concepts, `ObjectWithIdAndName` is coincidence, and refactoring on coincidence is how one team's change breaks another team's client.

Specifics worth stating:

- **Keep the document self-contained.** External-file `$ref`s (`./common/money.yaml#/Money`) are lovely in a monorepo and a problem everywhere else: Azure APIM **cannot resolve `$ref` pointers to external files** on import. Bundle to a single file in CI (`redocly bundle`, `swagger-cli bundle`) and publish the bundle as the artefact.
- **No recursion.** A schema that references itself is legal OpenAPI and is explicitly **unsupported by APIM**. If a domain object is genuinely a tree, flatten it to a depth-limited representation or a list with parent IDs.
- **`example` vs `examples`.** Two different things in two different places: on a **Media Type Object**, `examples` is a *map* of named Example Objects (`gbpFasterPayment: {summary, value}`) and `example` is a single inline value — they are mutually exclusive. On a **Schema Object**, `examples` is the JSON Schema keyword and takes an *array*, and singular `example` is deprecated in 3.1. Prefer named `examples` on media types — they show up as selectable dropdowns in Swagger UI and Redoc, and they're the cheapest documentation you'll ever write.
- **`$ref` siblings.** In 3.1 you may put `summary` and `description` next to a `$ref` and they override the target's. In 3.0 every sibling of `$ref` is ignored — a classic silent bug.
- **Don't over-`allOf`.** `allOf` composition is fine one level deep (`Instruction = InstructionCreate + server fields`); three levels deep and every codegen tool produces something unusable. `oasdiff flatten` exists precisely because of this.

**If they push back — "how do you share schemas across several APIs?"** — A versioned schema package: `common-schemas` repo, semver-tagged, published as an artefact; each API's build pulls the version it pins and bundles it in. Never a live URL `$ref` — that makes someone else's merge your outage.

---

### Q76. `oneOf` vs `anyOf` vs `allOf`, and what does `discriminator` actually do?
`[MEDIUM–HARD]`

> **Answer:** `oneOf` means valid against **exactly one** subschema — use it for tagged unions like event payloads. `anyOf` means valid against **at least one** — use it for genuinely overlapping constraints, and rarely. `allOf` means valid against **all** — it's composition/inheritance. `discriminator` is a **hint to tooling**, not a validation rule: it tells a code generator and a reader which property carries the type tag so they don't have to try every branch. The spec is explicit that *"the discriminator is a hint to the implementation on how to interpret the schema and does not affect validation."*

```yaml
InstructionEvent:
  oneOf:
    - $ref: '#/components/schemas/InstructionSettled'
    - $ref: '#/components/schemas/InstructionRejected'
  discriminator:
    propertyName: eventType          # REQUIRED
    mapping:                          # optional; without it the value must match a schema name
      instruction.settled: '#/components/schemas/InstructionSettled'
      instruction.rejected: '#/components/schemas/InstructionRejected'
```

The `discriminator` object has exactly two fields — `propertyName` (required) and `mapping` — and it is only legal alongside `oneOf`, `anyOf` or `allOf`.

Because it doesn't validate, you must make each branch self-validating: pin the tag with `const` (3.1) or a single-value `enum` (3.0) inside each subschema, exactly as in Q73. Without that, a payload with `eventType: instruction.settled` but a `reasonCode` field can match **both** branches, and `oneOf` then fails with a confusing "matched 2 schemas" error rather than the message you wanted.

**If they push back — "when would you use `anyOf` at all?"** — Almost never in a request body. Its honest use is a value that can satisfy multiple independent constraints — an identifier that may be a valid IBAN *or* a valid internal account reference, where both being true is fine. If you find yourself reaching for `anyOf` in a union, you wanted `oneOf`; if you reach for it to express "nullable", in 3.1 you want `type: [string, "null"]`.

---

### Q77. How do you enforce API standards across many teams?
`[HARD — the platform-engineer question]`

> **Answer:** A Spectral ruleset in CI. Design guidelines in a Confluence page get read once; a ruleset that fails the pull request gets obeyed. I publish a shared ruleset that extends `spectral:oas`, encodes our house rules — kebab-case paths, `operationId` mandatory, every 4xx returns `application/problem+json`, no `additionalProperties: true` on requests, security defined on every operation — and every API repo's pipeline runs it as a required check.

```yaml
# .spectral.yaml — published as @org/api-ruleset and extended by every API repo
extends: ["spectral:oas"]

rules:
  # --- house rules ---
  paths-kebab-case:
    description: Paths must be kebab-case.
    message: "{{property}} should be kebab-case (lowercase, hyphen-separated)"
    severity: error
    given: $.paths[*]~
    then:
      function: pattern
      functionOptions:
        match: "^(\/|[a-z0-9-.]+|{[a-zA-Z0-9_]+})+$"

  operation-id-required:
    description: Every operation needs an operationId (codegen and APIM depend on it).
    severity: error
    given: $.paths[*][get,put,post,delete,patch]
    then:
      field: operationId
      function: truthy

  problem-json-on-errors:
    description: 4xx/5xx responses must use application/problem+json (RFC 9457).
    severity: error
    given: $.paths[*][*].responses[?(@property.match(/^[45]/))].content
    then:
      field: "application/problem+json"
      function: truthy

  no-unbounded-collections:
    description: Collection GETs must declare a limit parameter.
    severity: warn
    given: $.paths[*].get
    then:
      field: parameters
      function: truthy

  security-on-every-operation:
    description: Every operation must be covered by a security requirement.
    severity: error
    given: $.paths[*][get,put,post,delete,patch]
    then:
      field: security
      function: truthy
```

```yaml
# .github/workflows/api-contract.yml
name: api-contract
on: [pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install -g @stoplight/spectral-cli
      - name: Lint the contract
        run: spectral lint openapi.yaml --ruleset .spectral.yaml --fail-severity error --format stylish
```

Two things I'd say about rollout, because "we added a linter" is not the interesting part:

1. **Start every new rule at `warn`, then promote to `error`.** Turning on 40 error-level rules against 30 existing APIs produces 4,000 failures and a team that disables the check.
2. **The ruleset is a product.** Versioned, changelogged, owned by the platform team, adopted by pinning a version — not a file copy-pasted into every repo that then drifts.

**If they push back — "what stops someone bypassing it?"** — Branch protection makes the check required, and the gateway is the backstop: APIM only imports specs published by the pipeline, so an unlinted contract has no route to production. Guardrails at both ends — the paved road makes the right thing easy, the gate makes the wrong thing impossible. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

---

### Q78. How do you test that the implementation matches the contract?
`[HARD]`

> **Answer:** Two layers. **Contract tests** — the consumer's expectations run against a provider stub and the provider's implementation, so neither side can move unilaterally (Pact, or provider-side tests generated from the spec). And **spec-driven fuzzing** with `schemathesis`, which reads the OpenAPI file, generates property-based test cases from every schema, throws them at the running service, and asserts the responses conform: status codes declared, content types declared, response bodies matching the schema, no 500s.

```bash
# generate cases from the contract, run them against the deployed UAT instance
st run openapi.yaml \
  --url https://api-uat.example.com/payments/v1 \
  --checks all \
  --max-examples 200 \
  --header "Authorization: Bearer ${TOKEN}" \
  --phases examples,coverage,fuzzing,stateful \
  --workers 4 \
  --report junit
```

The default check set — all of these run unless you narrow `--checks` — is worth being able to name:

| Check | What it catches |
|---|---|
| `not_a_server_error` | Any 5xx. The cheapest bug-finder you own. |
| `status_code_conformance` | Service returned a status the spec never declared. |
| `content_type_conformance` | Returned `text/html` where the spec said JSON. |
| `response_headers_conformance` | Declared a required response header, didn't send it. |
| `response_schema_conformance` | Body doesn't validate against the declared schema. |
| `negative_data_rejection` | Invalid input was *accepted* — the one that finds real security bugs. |
| `positive_data_acceptance` | Valid input was rejected. |
| `use_after_free`, `ensure_resource_availability` | Stateful sequencing: `GET` after `DELETE`, `GET` after `POST`. |
| `ignored_auth` | An endpoint that returns data with the auth header stripped. **This is the finding that gets escalated.** |

`schemathesis` also runs as a pytest plugin, so the same cases can execute in-process against an ASGI app with no network — fast enough to be a unit-test gate:

```python
# tests/test_contract.py
import schemathesis

from app.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
def test_api_conforms(case):
    case.call_and_validate()
```

**If they push back — "is fuzzing worth the CI minutes?"** — It is the only test that reads the contract rather than the code, so it finds the exact class of defect that unit tests structurally cannot: the spec says `maxLength: 34` and the handler doesn't check, the spec declares a `429` the service never returns, an endpoint that quietly works without a token. I run a small `--max-examples` on every PR and a long run nightly against UAT.

**Second push-back — "why Pact as well?"** — Different failure. Schemathesis proves the provider matches its own spec; Pact proves the provider matches what **consumers actually rely on**. A provider can be perfectly spec-conformant and still break a consumer that depended on a field the spec called optional.

---

### Q79. How do you catch breaking changes in CI, and how does the spec get into APIM?
`[HARD — the one that closes the loop from contract to gateway]`

> **Answer:** `oasdiff` in the pipeline, comparing the PR's spec against the spec published for the current production version, failing the build on error-level changes. Then the same artefact is imported into APIM by the release stage, so the gateway is never configured by hand — the contract in Git is the only way an operation reaches production.

```yaml
- name: Detect breaking changes against production contract
  run: |
    docker run --rm -v "$PWD:/specs" tufin/oasdiff breaking \
      /specs/published/openapi-v1.json \
      /specs/openapi.json \
      --fail-on ERR \
      --format githubactions
```

How it classifies, so you can defend it: checks are levelled `ERR` (definite break), `WARN` (potential break the definition can't resolve) and `INFO` (non-breaking). `oasdiff breaking` reports `ERR` and `WARN`; `oasdiff changelog` reports everything from `--level` up. `--fail-on ERR` exits 1 on errors only; `--fail-on WARN` on both. Its judging rule is the right one — a change is breaking if a consumer that followed the old contract can stop working under the new one, *whether or not your own server happens to be lenient*. Adding a required request property is breaking even if it has a server-side default.

Deliberate breaks are handled by version, not by exception: a new major goes to a new path (`/v2`), a new APIM API version set, and the old contract stays published until the deprecation window closes (§5). Genuine spec corrections use an ignore file (`--err-ignore`).

Then the import — this is the bit that has real, memorisable gotchas:

```bash
az apim api import \
  --resource-group rg-integration-prod \
  --service-name apim-integration-prod \
  --api-id payment-instruction-v1 \
  --path payments/v1 \
  --specification-format OpenApi \
  --specification-path ./openapi.yaml \
  --api-type http \
  --protocols https \
  --subscription-required true
```

What bites you on import, all documented:

- **Supported versions: OpenAPI 2.0 (JSON only), 3.0.x up to 3.0.3, and 3.1 for import only** — 3.1-specific constructs are ignored, downgraded or removed.
- **`components.securitySchemes`, `responses`, `parameters`, `examples`, `requestBodies`, `headers`, `links` and `callbacks` are not imported.** Security definitions are ignored outright — auth is configured as APIM policy, not from the spec.
- **Required query parameters are converted to required *template* parameters** by default. Turn that off with the "Include query parameters in operation templates" setting, or set `translateRequiredQueryParameters: query` via the REST API — otherwise `?status=` in your spec becomes `/{status}` in your gateway.
- **`operationId` becomes the Azure resource name**, lower-cased, non-alphanumerics collapsed to dashes, truncated to 76 characters. On re-import, operations are matched by that name — **all unmatched existing operations are deleted**, taking their operation-scoped policies with them. So: set `operationId` on everything, and never change `operationId` and the method/path in the same commit.
- **Size: up to 4 MB** when a spec is imported inline; larger specs must be supplied by URL.
- **API URL must be under 128 characters**, `$ref` cannot point at external files, and recursive schemas are unsupported.

**If they push back — "why not just let developers click Import in the portal?"** — Because then the gateway is a snowflake and there's no answer to "what changed on Tuesday". The spec is in Git, the pipeline lints it, diffs it, imports it, and applies the policy XML from the same repo. If someone edits it in the portal, the next deploy overwrites them — which is the point. Bicep/Terraform for the APIM instance and products, pipeline for the API definitions; see [IaC](05-cicd-iac-and-gitops.md) and [Azure Integration](02-azure-integration-services.md).

---

## 15. AsyncAPI — Contracts for Events

### Q80. What is AsyncAPI and how does it relate to OpenAPI?
`[MEDIUM — very few candidates can answer this; it's cheap differentiation]`

> **Answer:** AsyncAPI is OpenAPI for event-driven APIs. Same idea, same YAML feel, same reusable `components` and JSON Schema payloads — but instead of paths and HTTP methods it describes **servers** (the broker), **channels** (the topic, queue or subject), **messages** (headers plus payload schema), and **operations** (whether this application sends or receives on a channel). The current version is **3.0.0**, and it renamed 2.x's confusing `publish`/`subscribe` to explicit `send`/`receive` actions, because "publish" was ambiguous about whose point of view it described.

| OpenAPI | AsyncAPI 3.0 |
|---|---|
| `servers` (HTTP base URLs) | `servers` (broker host + `protocol: kafka` / `amqp` / `mqtt` / `ws`) |
| `paths` → path item | `channels` → the topic/queue, with an `address` |
| operation (`get`, `post`) | `operations` with `action: send` \| `receive` and a `channel` `$ref` |
| request/response body | `messages` — `headers`, `payload`, `contentType`, `correlationId` |
| `components.schemas` + `$ref` | `components.schemas`/`messages`/`messageTraits` + `$ref` |
| — | `bindings` — protocol-specific detail (Kafka partition key, AMQP queue durability) |
| `callbacks` / `webhooks` | `reply` — request/reply over messaging |

A real one, for the same payment domain:

```yaml
asyncapi: 3.0.0
info:
  title: Payment Settlement Events
  version: 1.2.0
  description: Settlement lifecycle events emitted by the payments platform.

servers:
  production:
    host: evhns-payments-prod.servicebus.windows.net:9093
    protocol: kafka-secure
    description: Event Hubs, Kafka-protocol endpoint.
    security:
      - $ref: '#/components/securitySchemes/saslOauth'

channels:
  instructionSettled:
    address: payments.instruction.settled.v1
    description: One event per instruction reaching a terminal settled state.
    messages:
      instructionSettled:
        $ref: '#/components/messages/InstructionSettled'

operations:
  receiveInstructionSettled:
    action: receive
    channel:
      $ref: '#/channels/instructionSettled'
    summary: Consumed by the reconciliation service.
    messages:
      - $ref: '#/channels/instructionSettled/messages/instructionSettled'

components:
  securitySchemes:
    saslOauth:
      type: oauth2
      scopes: []
      flows:
        clientCredentials:
          tokenUrl: https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token
          availableScopes: {}

  messages:
    InstructionSettled:
      name: InstructionSettled
      title: Instruction settled
      contentType: application/json
      headers:
        type: object
        properties:
          ce-id:
            type: string
          ce-type:
            type: string
            const: com.example.payments.instruction.settled.v1
          ce-source:
            type: string
          traceparent:
            type: string
            description: W3C Trace Context, propagated from the originating HTTP call.
      correlationId:
        location: $message.header#/ce-id
      payload:
        $ref: '#/components/schemas/InstructionSettledPayload'

  schemas:
    InstructionSettledPayload:
      type: object
      required: [instructionId, settledAt, amount, currency]
      additionalProperties: false
      properties:
        instructionId:
          type: string
        settledAt:
          type: string
          format: date-time
        amount:
          type: string
          pattern: '^-?[0-9]+\.[0-9]{2}$'
        currency:
          type: string
          enum: [GBP, USD, EUR, INR]
```

**If they push back — "we already have Avro schemas in a registry, isn't this duplication?"** — They solve different halves. A schema registry governs the **payload** and enforces compatibility at produce time; AsyncAPI documents the **topology** — which application sends what, on which channel, on which broker, with which headers, at which quality of service. In practice I reference the registry from the AsyncAPI document rather than restating the payload: AsyncAPI supports `schemaFormat` for Avro and Protobuf, so the contract points at the registered schema. See [Messaging](03-messaging-and-event-streaming.md).

---

### Q81. Why does an event-driven integration need a contract as much as a REST one?
`[MEDIUM — answer this like a platform engineer]`

> **Answer:** Because the coupling doesn't disappear when you remove the synchronous call — it just becomes invisible. With REST, a breaking change fails loudly at the caller. With events, a producer renames a field and the consumer keeps running, silently dropping records, and you find out at month-end reconciliation. The contract, plus registry-enforced compatibility, is what converts an invisible runtime failure into a visible build-time one.

The four things I put in place, in the order they pay off:

1. **A schema per event type, versioned, in a registry** — Azure Schema Registry in an Event Hubs namespace, or Confluent Schema Registry for Kafka. Producers serialise against it. Compatibility mode is `BACKWARD` by default so consumers can upgrade after producers; adding an optional field with a default is fine, removing or renaming one is rejected at publish time.
2. **An AsyncAPI document per application**, generated or hand-written, in the same repo as the service and published to the developer portal alongside the OpenAPI specs. One catalogue for both synchronous and asynchronous contracts — otherwise events become the undocumented shadow API of the estate.
3. **Envelope discipline.** CloudEvents-style headers (`ce-id`, `ce-type`, `ce-source`, `ce-time`) plus `traceparent` for W3C Trace Context, so correlation survives the hop from HTTP into the broker and out again — same correlation story as §7, and the reason a settlement failure can be traced back to the originating API call.
4. **Explicit versioning in the channel name** — `payments.instruction.settled.v1`. A genuinely breaking payload change gets a new topic and a period of dual-publish, because you cannot ask every consumer to redeploy on the same day. Additive changes stay in place; that's what the compatibility mode enforces.

**If they push back — "who owns the event contract, the producer or the consumer?"** — The producer owns the schema; the platform owns the *rules* the schema must obey and the CI gate that enforces them. Consumers get a veto only through the compatibility check, not through negotiation — otherwise every new consumer becomes a change request against the producer, and the loose coupling you bought the broker for is gone. That governance split — producer owns content, platform owns guardrails — is the same one I'd apply to OpenAPI, Helm charts and Terraform modules.

---

## Interviewer Traps

Twelve places the obvious answer is wrong. Each one is *"most candidates say X — the correct answer is Y."*

**1. "Use 200 with a success flag in the body."**
Most candidates default to always-200 because "the call worked." The correct answer is that the status code *is* part of the contract: gateways, retry policies, circuit breakers, CDNs and dashboards all act on it, and none of them parse your body. Always-200 makes your API invisible to every piece of infrastructure between you and the client. The one legitimate exception is GraphQL over legacy `application/json` — and that is precisely why GraphQL needs its own error monitoring (Q68).

**2. "PUT is idempotent so retries are safe."**
Most candidates stop at RFC 9110's definition. The correct answer is that idempotency guarantees the *server state* is the same after N identical requests, not that a retry is safe in a concurrent system: a retried `PUT` after a timeout can silently overwrite a write that landed in between. Idempotency plus optimistic concurrency — `ETag` and `If-Match`, `412` on mismatch — is what makes a retry actually safe.

**3. "We're idempotent because we check if the record exists."**
Most candidates describe a read-then-write. The correct answer is that read-then-write is a race, not idempotency: two concurrent replays both read "not found" and both insert. Real idempotency is a uniqueness constraint on the key — `INSERT ... ON CONFLICT DO NOTHING`, a unique index on `(tenant, idempotency_key)` — enforced by the database, plus storing the original response so the replay returns the same body, not a fresh one.

**4. "We version with `/v2` when we change the API."**
Most candidates give the mechanism and stop. The correct answer names what triggers a version: removing or renaming a field, adding a required request field, narrowing a type, tightening validation, changing a status code, or changing the meaning of an existing value. Additive changes never justify a new version. And the version is a *deprecation programme* — `Deprecation` and `Sunset` headers, a dated notice, dual-running, consumer telemetry to prove nobody is left — not a URL prefix.

**5. "Offset pagination is fine, we use `LIMIT`/`OFFSET`."**
Most candidates only cost the query. The correct answer is that offset pagination is O(offset) on the database and, worse, **incorrect under concurrent writes** — rows inserted while a client pages cause duplicates and skips. Keyset/cursor pagination on an immutable sort key is stable and constant-cost. Offset is acceptable only for small, admin-facing, human-driven grids that genuinely need "page 47".

**6. "SOAP is legacy, we'd migrate them to REST."**
Most candidates treat SOAP as a thing to be removed. The correct answer for a financial-services engagement is that SOAP is not going anywhere — a core banking platform or a policy administration system exposes a WSDL and will for the next decade — and that the job is a **facade**: expose a clean REST contract, translate at the gateway, keep the SOAP call as the implementation detail, and *keep* the parts SOAP does better where they matter (WS-Security signing, a formally typed contract). Migration is the ten-year plan; the facade ships this quarter.

**7. "GraphQL solves over-fetching, so it's better than REST."**
Most candidates recite the marketing. The correct answer is that GraphQL trades over-fetching for four new problems: no HTTP caching, no per-endpoint throttling, N+1 as the default execution model, and a query cost that isn't visible from the request. Those are acceptable for a first-party BFF and unacceptable for a partner-facing financial API. The senior signal is naming the trade, not the benefit.

**8. "GraphQL is rate-limited like any other API — requests per minute."**
Most candidates map REST throttling straight across. The correct answer is that "one request" is meaningless when a 200-byte query can fan out into a million resolver calls. You need depth limiting and complexity/cost budgets before execution, persisted queries to bound the query set, and only then requests-per-minute as a backstop. In APIM that's `validate-graphql-request` with `max-depth` and `max-size` (max 100 KB), not `rate-limit-by-key` alone.

**9. "We validate the request against the OpenAPI spec, so we're secure."**
Most candidates conflate schema validation with authorisation. The correct answer is that schema validation stops malformed input, not unauthorised access — and specifically, **APIM ignores `securitySchemes` on import**, so a spec that beautifully documents OAuth2 gives you exactly zero enforcement until you add `validate-jwt` policy. Contract and control plane are separate; see [Auth](06-auth-and-security.md).

**10. "The OpenAPI spec is generated from the code, so it's always accurate."**
Most candidates treat generation as a guarantee. The correct answer is that generation guarantees the spec matches your *handlers*, not that either matches what was agreed, and it happily generates a spec full of `additionalProperties: true`, missing `operationId`s and undeclared error responses. The contract needs its own gate — Spectral for standards, oasdiff for breaking changes, schemathesis to prove conformance — regardless of who wrote the YAML.

**11. "Async means the caller doesn't care about the response."**
Most candidates equate async with fire-and-forget. The correct answer is that the caller almost always cares — it just isn't blocking. So you owe them a `202` with a status URL, a terminal state they can poll or subscribe to, a correlation ID that survives every hop, and a documented redelivery and dead-letter behaviour. Fire-and-forget without those is not asynchronous design; it's an untraceable message.

**12. "Money is a `number` in the schema."**
Most candidates never think about it. The correct answer is that JSON numbers are IEEE 754 doubles in almost every parser, so `0.1 + 0.2` and 17-digit account balances both go wrong, and in a banking or asset-management context that is a defect that reaches a regulator. Money is a **string** with a pattern (`"1250.00"`) plus an explicit currency code, decoded to `Decimal` — never `float` — and never `float` on the way back out either.

---

## 30-Second Whiteboard Versions

Three answers you should be able to draw and narrate in half a minute, standing up, with a marker.

### A. SOAP-to-REST facade

```
Partner/Client                APIM (gateway)                     Legacy core
─────────────                 ──────────────                     ───────────
GET /v1/customers/{id}  ──▶   validate-jwt                       ┌──────────────┐
Accept: application/json      rate-limit-by-key                  │ CustomerSvc  │
                              set-backend-service ──────────────▶│   .asmx      │
                              set-method POST                    │  (WSDL/XSD)  │
                              set-header SOAPAction              └──────────────┘
                              set-body (liquid → SOAP envelope)          │
                              ◀──────────────  SOAP/XML response ────────┘
                              outbound: xml-to-json
                              on-error: problem+json
◀── 200 application/json      trace: correlation-id
```

**Say:** *"The partner gets a REST contract with an OpenAPI spec — resources, verbs, RFC 9457 errors. APIM owns the translation: `set-method` to POST, `SOAPAction` header, request body templated into the SOAP envelope, and `xml-to-json` on the way back. The WSDL is imported once so operations and schemas come across. Auth is modernised at the edge — the partner presents a JWT, and APIM holds the legacy credential in Key Vault, so nobody outside the gateway ever sees it. Correlation ID goes in on the way through and into the trace on the way back. The legacy service never changes, and when it's finally replaced I swap the backend and the partner contract doesn't move."*

**Two lines to have ready:** WSDL import only supports document/literal — no RPC style, no WS-\* — and `wsdl:import`/`xsd:include` must be merged into one document first.

### B. Idempotent POST

```
Client                      API                          Store
──────                      ───                          ─────
POST /v1/instructions       1. key = header Idempotency-Key (required, uuid)
Idempotency-Key: 7f3a…      2. fingerprint = sha256(method|path|body)
{amount: 1250.00,…}         3. INSERT (key, fingerprint, state=IN_PROGRESS)
                               ON CONFLICT DO NOTHING           ──▶ unique idx
                            ┌────────────────────────────────────────────┐
                            │ inserted?  → do the work, save response,    │
                            │              state=DONE, return 201         │
                            │ conflict + same fingerprint + DONE          │
                            │            → return SAVED response, 200     │
                            │ conflict + same fingerprint + IN_PROGRESS   │
                            │            → 409 + Retry-After              │
                            │ conflict + DIFFERENT fingerprint            │
                            │            → 422 idempotency-key-reuse      │
                            └────────────────────────────────────────────┘
TTL on the key: 24h (documented in the contract)
```

**Say:** *"The client supplies the key, because only the client knows what a retry is. I store the key with a fingerprint of the request so a reused key with a different body is an error, not a silent wrong answer. The uniqueness is a database constraint, not a read-then-write, so two concurrent replays can't both win. The original response is stored and replayed byte-for-byte — a retry must not observe a newer state. Keys expire after a documented window, and that window is in the OpenAPI description, not in someone's head."*

### C. Versioning strategy

```
  URI path            /v1/orders            ← default. Visible, cacheable, routable in APIM.
  Header              Api-Version: 2026-03  ← clean URLs, invisible in logs, easy to forget
  Query               ?api-version=2026-03  ← Azure ARM style, easy to test in a browser
  Media type          Accept: application/vnd.acme.order.v2+json  ← purest, worst DX

  MAJOR (breaking)              MINOR (additive)
  ────────────────              ────────────────
  new path /v2                  same version, add fields
  new APIM version set          consumers ignore what they don't know
  old version stays live        oasdiff --fail-on ERR keeps it honest
        │
        ├── announce: Deprecation + Sunset headers (dated), portal notice, email
        ├── dual-run both versions for the agreed window (typically 2 quarters)
        ├── measure: per-version call counts per subscription in APIM analytics
        └── retire only when the v1 curve hits zero — chase the stragglers by name
```

**Say:** *"URI versioning by default, because it's visible in logs, routable in the gateway and something a partner's change-control board can understand. Only breaking changes get a major — removing a field, adding a required field, tightening a type, changing a status code. Everything additive ships in place, and oasdiff in CI decides which is which rather than a human opinion. The version isn't a URL, it's a deprecation programme: dated `Deprecation` and `Sunset` headers, both versions live for the agreed window, and per-version telemetry per subscription so I retire on evidence, not on a date. Internally I aim for two live majors, never three."*

---

## Rapid Fire

Forty one-liners spanning the whole file. Cover the answer, ask yourself the question, say it out loud.

| # | Question | Answer |
|---|---|---|
| 1 | Safe methods? | `GET`, `HEAD`, `OPTIONS`, `TRACE` — RFC 9110 §9.2.1. |
| 2 | Idempotent methods? | Those four plus `PUT` and `DELETE`. Not `POST`, not `PATCH`. |
| 3 | 201 vs 202? | 201 = created, resource exists now, `Location` points at it. 202 = accepted, not done, `Location` points at a status resource. |
| 4 | 400 vs 422? | 400 = the request was malformed (bad JSON, bad header). 422 = syntactically fine, semantically invalid. |
| 5 | 401 vs 403? | 401 = who are you (missing/invalid credentials, must send `WWW-Authenticate`). 403 = I know who you are and you still can't. |
| 6 | 409 vs 412? | 409 = conflict with current state. 412 = your `If-Match` precondition failed. |
| 7 | What must a 429 carry? | `Retry-After`, plus `RateLimit-Limit`/`Remaining`/`Reset`, and a problem+json body. |
| 8 | Idempotency key lives where? | A client-generated UUID in the `Idempotency-Key` request header, enforced by a unique constraint. |
| 9 | Why store a request fingerprint with the key? | So a reused key with a different body returns an error instead of the wrong cached response. |
| 10 | Offset vs keyset pagination? | Offset is O(offset) and unstable under concurrent writes; keyset is constant-cost and stable. Default to keyset. |
| 11 | What makes a good cursor? | Opaque, base64, encoding the sort key + tie-breaker ID. Never a raw offset the client can arithmetic on. |
| 12 | Breaking change, name three? | Removing a field, adding a required request field, changing a type or a status code. |
| 13 | Deprecation headers? | `Deprecation` (RFC 9745) and `Sunset` (RFC 8594), plus a `Link` to the migration guide. |
| 14 | JSON Patch vs Merge Patch? | JSON Patch (RFC 6902) = ordered ops, `application/json-patch+json`, can be non-idempotent. Merge Patch (RFC 7396) = a partial doc, `null` deletes, idempotent. |
| 15 | How do you delete a field with Merge Patch? | Set it to `null`. Which is also why Merge Patch can't distinguish "delete" from "set to null". |
| 16 | Long-running operation pattern? | `202` + `Location` to a status resource + `Retry-After`; terminal state carries a link to the result. |
| 17 | Polling vs webhook? | Poll when the client is behind a firewall or the wait is short; webhook when the wait is long and the client can host an endpoint — with signature + replay protection. |
| 18 | How do you secure a webhook? | HMAC-SHA256 over timestamp + raw body in a signature header, constant-time compare, reject stale timestamps, verify before parsing. |
| 19 | RFC for problem details? | **RFC 9457** (obsoletes 7807). Media type `application/problem+json`. |
| 20 | Required problem fields? | `type`, `title`, `status`; then `detail`, `instance`, plus your extensions like `correlationId`. |
| 21 | Which header carries trace context? | `traceparent` (W3C Trace Context), with `tracestate` for vendor data. |
| 22 | CORS preflight trigger? | Non-simple method or headers → browser sends `OPTIONS` with `Access-Control-Request-Method`; server answers with `Access-Control-Allow-*` and `Max-Age`. |
| 23 | ETag: strong vs weak? | Strong = byte-identical. Weak (`W/"…"`) = semantically equivalent. Use strong for `If-Match` concurrency. |
| 24 | HTTP/2's key win? | Multiplexing many streams over one TCP connection plus HPACK header compression — kills head-of-line blocking at the HTTP layer. |
| 25 | HTTP/3's key win? | QUIC over UDP — removes TCP head-of-line blocking and gets 0-RTT connection resumption. |
| 26 | When gRPC over REST? | Internal service-to-service, high call volume, streaming, polyglot clients with a shared `.proto`. Not for browsers or partners. |
| 27 | SOAP envelope structure? | `Envelope` → optional `Header` (WS-Security, addressing) + mandatory `Body`, and `Fault` inside `Body` for errors. |
| 28 | What's in a WSDL? | `types` (XSD), `message`, `portType` (operations), `binding` (protocol/style), `service`/`port` (endpoint). |
| 29 | SOAP fault codes? | SOAP 1.1: `Client`, `Server`, `VersionMismatch`, `MustUnderstand`. SOAP 1.2 renames them `Sender`/`Receiver`. |
| 30 | APIM WSDL import limits? | Document/literal only — no RPC style, no WS-\*, no `wsdl:import`/`xsd:include`, no recursive types, `basicHttpBinding` not `wsHttpBinding`. |
| 31 | APIM policy sections? | `inbound`, `backend`, `outbound`, `on-error` — and `<base />` controls where the parent scope's policy runs. |
| 32 | GraphQL N+1 fix? | DataLoader — batch keys collected within one tick, one downstream call, per-request cache. New loader per request. |
| 33 | Why is GraphQL hard to cache? | One `POST` endpoint, no URL to key on. Persisted queries over `GET` restore it. |
| 34 | Persisted query hash? | SHA-256 of the query document, sent as `extensions.persistedQuery.{version:1, sha256Hash}`. |
| 35 | GraphQL field error vs request error? | Field error → `data` present with a null and an `errors` entry, 200. Request error → no `data`, and 4xx/5xx under `application/graphql-response+json`. |
| 36 | APIM GraphQL guardrails? | `validate-graphql-request` — `max-size` required (max 102,400 bytes), `max-depth` defaults to 6, `rule path="/__*" action="reject"` to kill introspection. |
| 37 | OpenAPI 3.1's headline change? | Full JSON Schema draft 2020-12 compatibility; plus top-level `webhooks`, optional `paths`, `mutualTLS`. |
| 38 | Which FastAPI version emits 3.1? | 0.99.0 onward (June 2023) — OpenAPI 3.1.0, JSON Schema 2020-12, webhooks, Swagger UI 5. |
| 39 | Does `discriminator` validate? | No — it's a hint to tooling. Pin the tag with `const`/`enum` in each branch or your `oneOf` will match twice. |
| 40 | AsyncAPI 3.0 vs 2.x? | `publish`/`subscribe` became explicit `send`/`receive` operations that reference channels; channels hold messages. |

Bonus, from EY-logged DevOps rounds — these come up in the same L1 and are covered in the sibling files: *git fetch vs git pull?* → `fetch` updates remote-tracking refs only; `pull` = `fetch` + `merge` (or `--rebase`). `EY-logged` — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md). *What are the objects in a Kubernetes Service?* / *How does HPA work?* → `EY-logged`, see [K8s](04-microservices-containers-kubernetes.md). *How do you check resources using Terraform?* → `EY-logged`, see [IaC](05-cicd-iac-and-gitops.md).
