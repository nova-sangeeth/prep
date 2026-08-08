# API Styles: REST vs gRPC vs GraphQL

> REST for broad, cacheable public APIs; gRPC for fast internal service-to-service; GraphQL for flexible, client-driven aggregation.

## What it is & why it matters

The API contract shapes coupling, performance, and developer experience. Three
dominant styles:
- **REST:** resource-oriented HTTP/JSON, stateless, uses verbs + status codes.
  Ubiquitous, cacheable, human-debuggable. Default for public APIs.
- **gRPC:** Protobuf over HTTP/2, binary, contract-first (`.proto`), supports
  streaming. Low latency, strongly typed, great for internal microservices.
- **GraphQL:** single endpoint, client specifies exactly which fields it needs.
  Eliminates over/under-fetching; ideal for varied frontends aggregating many
  backends.

## How it works

```
REST:    GET /users/42/orders        -> JSON, cacheable, 1 resource/call
gRPC:    rpc GetUser(Req) returns(User) over HTTP/2, binary protobuf, streams
GraphQL: POST /graphql { user(id:42){ name orders{ total } } } -> exact shape
```

REST maps CRUD to GET/POST/PUT/PATCH/DELETE on resource URIs. gRPC generates
client/server stubs from a `.proto` schema and multiplexes calls over one HTTP/2
connection (incl. bidirectional streaming). GraphQL resolves a typed query graph
server-side, fetching from underlying services/DBs and assembling the response.

## Tradeoffs / variants

| Dimension | REST | gRPC | GraphQL |
|---|---|---|---|
| Payload | JSON (text) | Protobuf (binary) | JSON |
| Transport | HTTP/1.1+ | HTTP/2 | HTTP |
| Contract | OpenAPI (optional) | `.proto` (required) | SDL schema (required) |
| Streaming | Limited (SSE/WS) | First-class bidi | Subscriptions |
| Browser | Native | Needs grpc-web/proxy | Native |
| Caching | HTTP caching native | Manual | Hard (POST, custom) |
| Fetching | Fixed per endpoint | Fixed per method | Client-shaped, no over-fetch |
| Best for | Public/CRUD APIs | Internal microservices | Aggregation/mobile BFF |

## When to use · pitfalls

REST: public-facing, cache-heavy, simple CRUD, max interoperability. gRPC:
east-west traffic, performance-critical, polyglot internal services, streaming.
GraphQL: rich clients hitting many backends, rapidly evolving field needs, mobile
bandwidth concerns. Common real-world: gRPC internally + REST/GraphQL gateway at
the edge.

Cross-cutting concerns (ask about these in interviews):
- **Idempotency:** GET/PUT/DELETE idempotent; POST is not — use an
  **idempotency key** for safe retries on payments/creates.
- **Pagination:** prefer **cursor/keyset** (`?after=cursor`) over `OFFSET` —
  offset is O(n) and skips/dupes rows on inserts.
- **Versioning:** URI (`/v2/`) or header for REST; new fields in protobuf are
  backward-compatible (never reuse field numbers); GraphQL deprecates fields
  rather than versioning.
- **Error handling:** REST uses HTTP status + error body; gRPC uses status codes;
  GraphQL returns `200` with an `errors` array (tooling caveat).

Pitfalls: GraphQL **N+1 resolver** explosion (use DataLoader/batching) and
unbounded/expensive queries (depth/cost limits). gRPC needs a **proxy for
browsers**. REST chattiness causes over/under-fetching across many round trips.

## Interview soundbites
- "REST for public and cacheable, gRPC for internal and fast, GraphQL for client-driven aggregation."
- "gRPC = protobuf over HTTP/2: binary, typed, streaming — perfect east-west."
- "GraphQL kills over/under-fetching but invites N+1 — batch with DataLoader."
- "Make POST safe to retry with an idempotency key."
- "Use cursor pagination, not OFFSET — offset degrades and skips rows under writes."
- "Protobuf evolves by adding fields and never reusing field numbers."
