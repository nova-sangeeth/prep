# EY GDS — Scripted Answers

**Role:** Integration Platform Engineer, 4–8 yrs, EY **Digital Engineering (DE)**, GDS.
**Industry context:** Financial Services first — Asset Management, Banking & Capital Markets, Insurance, Private Equity.

> **Revised against the updated JD.** The title is *Platform Engineer*, not developer. Answer at platform altitude wherever you can: the reusable pipeline template, the golden Helm chart, the shared Terraform module, the policy fragment the security team owns — not "I wrote a pipeline for my service." Same work, higher altitude, and the altitude is what's graded.
>
> Three of the nine JD responsibilities are **CI/CD, IaC and GitOps**. That block is now the heaviest thing in the document — see [§B7](#b7--cicd-iac-gitops-kubernetes-the-heaviest-jd-block).

Every question below is either **EY-attributed** (logged by a real candidate on AmbitionBox/GfG/Blind against EY or EY GDS) or **high-frequency** for this exact JD. Tags mark which.

Answers are written **spoken-answer shaped**: the first 2–3 sentences are a complete, confident, sayable answer. Detail follows for the pushback.

`[BRACKETS]` = fill in with your own project. Do not walk in with brackets unfilled.

**Rule for the whole day: commit to an answer, then refine.** A logged EY GDS candidate was accused of using outside help because their answers kept improving across follow-ups, and the interviewer ended the call early. State the answer. Then add nuance.

---

## §A — Opening. The three modal EY questions.

AmbitionBox surfaces these same three on *every* EY designation page across 670+ logged questions. They are the highest-probability questions in the entire process.

### A1. "Tell me about yourself." `EY-GDS modal #1`

**90 seconds. Not four minutes.** Three versions — know which room you're in.

**L1 (engineer) version:**

> "I'm a backend engineer, about six years, primarily Python — FastAPI and Flask. Most of my work has been building and integrating APIs: [SYSTEM], where I owned [WHAT], and more recently a set of AI systems that were really integration problems — orchestrating calls across [N] internal and third-party APIs with retries, idempotency and rate-limit handling, backed by [DATASTORE].
>
> The pattern in my work is the same one this role describes: something upstream produces data in a shape nobody downstream wants, and you build the layer that makes it reliable, secure and observable in between. On [PROJECT] that meant [SPECIFIC — e.g. cutting p95 from 4.2s to 1.6s / handling 40k requests/day with zero data loss across a downstream outage].
>
> I'm looking to do that at a larger scale on the Azure integration stack, which is why this req interested me."

**L2 (manager/director) version** — lead with delivery and client, not stack:

> "Six years, backend and integration. What I'd point to is [PROJECT], where I was the technical owner end to end — I scoped it with [STAKEHOLDER], made the architecture calls, and shipped it in [TIMEFRAME]. The measurable outcome was [NUMBER].
>
> I've worked the whole way across the delivery cycle — requirements that arrive ambiguous, a design that has to survive a stakeholder who wants it a different way, and the part nobody talks about, which is what support sees at 3am when it breaks. I've also been the person who ramped a team onto a stack they hadn't used.
>
> What draws me to EY GDS specifically is that integration work here is client-facing and varied rather than one product forever, and the EY–Microsoft investment means the AI-plus-integration work I've been doing is where the practice is going, not a side project."

**HR version** — short, warm, logistics-forward:

> "Six years in backend and API development, currently at [COMPANY] in Chennai, working in Python on [DOMAIN]. I'm on a [X]-day notice period. I'm looking for a role with more client exposure and a larger integration surface, and EY GDS is a natural fit for that."

**Pushback — "tell me more about your current role":** have a 60-second expansion ready for the *one* project you know best. Never expand into a third project unprompted.

---

### A2. "Why do you want to work for us?" / "Why EY?" `EY modal #1`

> "Three reasons, in order of how much they matter to me.
>
> First, this is a platform role inside Digital Engineering, not an application role. What I want to be doing is building the integration platform other teams consume — the pipeline templates, the deployment path, the gateway policies — rather than one service for one product. That's a different job and it's the one I want.
>
> Second, the industry focus. EY is the only professional services firm with a business dedicated exclusively to financial services, and financial services is where integration constraints actually get interesting — you can't lose a payment, you have to prove exactly-once effect, there's an auditor who will ask who approved a deployment and where the data physically lives. Those constraints make the engineering harder in a way I find genuinely interesting.
>
> Third, the direction. EY and Microsoft announced a joint investment of over a billion dollars over five years to scale enterprise AI, and EY has already put a multiagent framework into EY Canvas across 130,000 Assurance professionals and 160,000 audit engagements. I've spent two years building systems where an LLM has to call real enterprise APIs safely — that's an integration and authorisation problem before it's an AI problem, and it's clearly where this practice is going."

**Why this works:** it's specific, it's sourced, and it names three things about EY that most candidates don't know. Do not recite "building a better working world" — every candidate does, and it reads as scripted.

**Pushback — "what do you know about Digital Engineering specifically?":**
> "It's EY's industry-focused technology unit — the practice that takes a client from strategy through to actual technical design and delivery on digital transformation programmes. So an integration platform engineer there isn't maintaining a steady-state system; you're standing up the integration layer for a transformation, which means the platform has to be built to be handed over and operated, not just to work."

**Pushback — "what do you know about GDS?":** EY's global delivery network — Argentina, China, India, the Philippines, Poland, the UK and more; five teams (Assurance, Consulting, Strategy & Transactions, Tax, Enablement Services); over 90,000 people; India the largest geography.

### A3. "Tell me about a time you had to navigate a difficult work situation." `EY modal #3`

This is the STAR rubric question. EY's own careers page states they score behavioural answers on three elements: **relevant experience, action taken, result.** Structure your answer to hit all three explicitly. See [§D](#d--star-stories) for the full set.

---

### A4. "Why are you leaving your current role?"

> "Two things. The integration surface I'm working on has narrowed — I've been on [X] for [Y] months and the interesting architecture decisions are behind us. And I want client-facing work; I've enjoyed the parts of my job where I was in front of stakeholders working out what they actually needed, and I want more of that, not less."

**Never say:** manager problems, pay, "no growth," anything negative about a named person. If pressed on pay: *"Compensation isn't the driver — if it were I'd be looking at product companies. The driver is scope."*

---

## §B — L1 technical

### B1 · API design & REST `HIGH FREQUENCY — the JD leads with this`

**Q: What is a REST API?**
> "An architectural style over HTTP where you model the domain as resources with stable URIs, and use the HTTP verbs and status codes as the interface rather than inventing your own. The properties that matter in practice are statelessness — every request carries its own context, so any instance can serve it — and uniform interface, so a client that knows HTTP already knows most of your API."

**Q: When do you use POST, PUT and PATCH?**
> "POST creates and is not idempotent — call it twice, you get two resources. PUT replaces the whole resource at a known URI and is idempotent — same request twice leaves the same state. PATCH applies a partial update; it's idempotent only if you design it to be. In practice I use POST for creation at a collection endpoint, PUT when the client owns the identifier and is doing a full replace, and PATCH for partial updates using JSON Merge Patch (RFC 7386) unless the client genuinely needs the operation semantics of JSON Patch (RFC 6902)."

**Q: How do you make an API idempotent?** `TRAP`
> "For the naturally idempotent verbs — GET, PUT, DELETE — it comes free if you implement them properly. The interesting case is POST. There I use an `Idempotency-Key` header: the client generates a key, the server stores key → response in a store with a TTL, and on a repeat it returns the stored response instead of re-executing.
>
> The part people miss is the concurrent case. Two identical requests arriving at once will both miss the cache. So you insert the key first with an in-progress marker and a unique constraint — the second request loses the race and either waits or gets a 409. Without that, the whole mechanism is decorative under load."

**Q: How do you version an API?**
> "URI versioning — `/v1/orders` — for anything a third party consumes, because it's visible in logs, trivial to route in a gateway, and unambiguous for the consumer. Header or media-type versioning is cleaner in theory but it's harder to debug and harder to explain to a partner's integration team.
>
> The more important rule is what constitutes a breaking change: adding an optional field isn't, removing a field or tightening validation is. Additive changes go into the existing version. In APIM this maps directly — revisions for non-breaking changes you want to test before they go live, versions for breaking changes you expose side by side."

**Q: How do you paginate a large collection?** `TRAP`
> "Cursor or keyset pagination, not offset. Offset pagination — `LIMIT 20 OFFSET 100000` — makes the database count and discard 100,000 rows, so it gets slower the deeper you go, and if a row is inserted mid-traversal the client sees a duplicate or misses a row entirely.
>
> Keyset pagination sends an opaque cursor encoding the last sort key seen — `WHERE (created_at, id) < (:ts, :id) ORDER BY created_at DESC, id DESC LIMIT 20`. It's O(limit) regardless of depth and it's stable under concurrent writes. The tradeoff is you can't jump to page 47, which real API consumers almost never need."

**Q: How do you design errors?**
> "RFC 9457 Problem Details — the JSON object with `type`, `title`, `status`, `detail` and `instance`, served as `application/problem+json`. It obsoletes RFC 7807, which is the same shape. I add a machine-readable error code and a correlation ID so support can find the request in the logs.
>
> The rules I hold to: the status code carries the class of failure and the body carries the specifics; never return 200 with an error in the body; and never leak stack traces or internal identifiers to an external consumer."

**Q: What do the status codes mean in practice?**

| Code | Use it when |
|---|---|
| 200 | Success with a body |
| 201 | Created — include `Location` |
| 202 | Accepted, work is async — include `Location` to poll |
| 204 | Success, deliberately no body |
| 400 | Malformed — the request is not parseable/valid syntax |
| 401 | Not authenticated (no or bad credentials) |
| 403 | Authenticated, not allowed |
| 404 | Not found — also use to hide existence from an unauthorised caller |
| 409 | Conflict — version conflict, duplicate, state machine violation |
| 422 | Syntactically valid, semantically wrong |
| 429 | Rate limited — **always** include `Retry-After` |
| 502/503/504 | Upstream broken / unavailable / timed out — 503 should carry `Retry-After` too |

**Q: What is an API gateway? How is it different from a load balancer / reverse proxy?**
> "A load balancer distributes traffic across instances at L4 or L7. A reverse proxy terminates the connection and forwards it, adding things like TLS termination and caching. An API gateway is a reverse proxy that also understands your API contract — it does authentication and authorisation per operation, rate limiting and quota per consumer, request and response transformation, versioning, and it's where the developer portal and subscription keys live.
>
> Rule of thumb: if the decision needs to know *which API operation* is being called and *who* is calling it, it belongs in the gateway."

**Q: Design the API for a payment system.** `EY-logged shape`
> Clarify first: card or account-to-account? Synchronous authorisation or async settlement? Idempotency requirement? Who are the consumers?
>
> `POST /v1/payments` with `Idempotency-Key` → 202 + `Location: /v1/payments/{id}`; `GET /v1/payments/{id}` for status; `POST /v1/payments/{id}/refunds` for refunds (also idempotent); webhook to the merchant on state transition, HMAC-signed with a timestamp and replay window. State machine: `pending → authorised → captured → settled`, with `failed` and `refunded` terminals. Never expose the PAN; store a token. Every state change is an event on a queue so downstream ledger and notification consumers are decoupled.

---

### B2 · SOAP and legacy integration `THE ACTUAL JOB`

**Q: How would you expose a legacy on-prem SOAP service as a REST API?** ⭐ **Rehearse this verbatim.**

> "Front it with Azure API Management. APIM can import the WSDL directly and give you two modes — SOAP passthrough, where it proxies the SOAP call unchanged and you just get gateway-level auth, throttling and observability; or SOAP-to-REST, where APIM generates REST operations and translates the payloads.
>
> For a real modernisation I'd do SOAP-to-REST. The inbound policy takes the JSON body and produces the SOAP envelope, the outbound policy converts the SOAP response back to JSON and strips the envelope, and the on-error section maps SOAP faults onto proper HTTP status codes — because a SOAP service returns HTTP 500 with a fault body for what is really a 400 or a 404, and if you don't map that, every consumer sees your API as permanently broken.
>
> Connectivity to on-prem is the other half: either the APIM self-hosted gateway deployed inside the client's network, or Private Link/ExpressRoute back to the VNet. Which one depends on whether the client will run a container in their DC.
>
> Two things I'd insist on. First, don't let the legacy contract leak — design the REST resource model around the domain, not around the WSDL operation names, or you've just moved the legacy API to a new URL. Second, put caching and throttling at the gateway, because legacy SOAP backends usually can't take the load the new consumers will generate."

**Q: What's in a WSDL?**
> "The contract. `types` — XSD schemas for the messages; `message` — the logical payloads; `portType` — the abstract operations; `binding` — how those operations map onto a protocol, almost always SOAP over HTTP; and `service` — the concrete endpoint address. It's the same job OpenAPI does for REST, just far more verbose and with the schema language baked in."

**Q: SOAP vs REST — when would you still choose SOAP?**
> "When the contract has to be formally enforced and the transaction guarantees matter — WS-Security for message-level signing and encryption rather than just transport TLS, WS-AtomicTransaction for two-phase commit across services, and a strict machine-verifiable contract in the WSDL. Banking, insurance and telco middleware still run on it for exactly those reasons.
>
> For anything greenfield I'd use REST. But in this kind of role you don't get to choose — the ERP speaks SOAP and your job is to make it consumable."

---

### B3 · Azure Integration Services `HIGHEST LEVERAGE FOR THIS JD`

**Q: What is Azure API Management, and what are its key components?** `VERY HIGH frequency`
> "It's Azure's managed API gateway and API management plane. Three planes: the **gateway**, which sits in the request path and executes policies; the **management plane**, where you define APIs, products, subscriptions and policies; and the **developer portal**, where consumers discover APIs and get keys.
>
> The objects you work with are APIs and their operations, **products** which bundle APIs and carry the terms of use, **subscriptions** which issue keys to consumers, **backends**, and **named values** for configuration — which should be Key Vault references, not literals."

**Q: Explain APIM policies.** ⭐
> "The policy engine is the whole product. Every request runs through four sections: **inbound** before the backend, **backend** around the call itself, **outbound** after it returns, and **on-error** if anything throws. Policies are XML with C# expressions, and they compose by scope — global, then product, then API, then operation — with `<base />` marking where the parent scope's policy runs.
>
> The ones I reach for most: `validate-jwt` for token validation against Entra ID, `rate-limit-by-key` and `quota-by-key` for throttling per consumer, `set-backend-service` for routing and blue-green, `cache-lookup`/`cache-store` for response caching, `xml-to-json`/`json-to-xml` for SOAP fronting, and `set-header` to strip internal headers on the way out."

**Q: How do you secure APIs in APIM?**
> "Layered. At the edge: subscription keys for identification and quota — those aren't authentication, they identify the consumer app. Real authentication is `validate-jwt` against Entra ID checking issuer, audience and required claims. For partner-facing APIs, mutual TLS with client certificate validation. Then rate limiting and IP filtering to bound abuse, and a WAF in front via Front Door or App Gateway for the OWASP ruleset.
>
> Backend-side: APIM authenticates to the backend with its own managed identity, so no secrets exist anywhere in the config, and the backend is on a private endpoint so it can't be reached except through the gateway."

**Q: What's the difference between a subscription key and a JWT here?** `TRAP`
> "A subscription key identifies the calling application and drives quota — it's a shared secret in a header, it doesn't say anything about a user, and it's not sufficient as authentication for anything sensitive. A JWT is a signed assertion about an identity with an expiry, an audience and scopes, which you validate cryptographically at the gateway. Use the key for metering, the token for authorisation."

**Q: APIM revisions vs versions?** `TRAP`
> "Versions are consumer-facing — a breaking change gets a new version, `v1` and `v2` run side by side, and consumers migrate on their own schedule. Revisions are not consumer-facing — they're a way to make a non-breaking change, test it against a revision URL, and then promote it to current. If a change breaks an existing consumer it needs a version, not a revision."

**Q: Self-hosted vs Azure-hosted gateway?**
> "The self-hosted gateway is the same gateway packaged as a container that you run in the client's environment — their datacentre, another cloud, or a Kubernetes cluster — while the management plane and portal stay in Azure. You use it when the backend can't be exposed to Azure, or when data residency means the request body must never leave a jurisdiction. The tradeoff is you now operate that container, and its configuration sync depends on reaching the management plane."

**Q: What is Azure Logic Apps? How does it differ from Azure Functions?** `VERY HIGH frequency`
> "Logic Apps is a workflow orchestrator — a trigger plus a series of actions, defined declaratively, with a large connector library for SaaS and enterprise systems. Functions is a compute primitive — you write the code and it runs on a trigger.
>
> The call I make in practice: if the work is *connecting systems* — 'when a file lands in SFTP, transform it and post it to SAP' — Logic Apps, because the connectors, retry policies and run history are free and an operations person can read the run. If the work is *logic* — non-trivial transformation, custom algorithms, anything you'd want unit-tested — Functions. Most real integrations use both: Logic Apps for the flow, a Function for the hard step in the middle."

**Q: Logic Apps Consumption vs Standard?**
> "Consumption is multi-tenant, billed per action executed, one workflow per Logic App resource. Standard is single-tenant, runs on the Azure Functions runtime, hosts multiple workflows in one app, supports VNet integration and private endpoints, gives you local development in VS Code, and adds **stateless** workflows for low-latency short flows alongside the usual stateful ones.
>
> For an enterprise client I default to Standard — the VNet integration and predictable cost model usually decide it. Consumption is right for spiky, low-volume, internet-facing flows."

**Q: Can Logic Apps reach on-premises resources?**
> "Yes — three ways. The on-premises data gateway for the SaaS-style connectors (SQL Server, file share, SAP). VNet integration on Logic Apps Standard, so it can reach anything routable from that VNet, which combined with ExpressRoute or a site-to-site VPN gets you to the datacentre. Or you avoid the problem by having on-prem push to a queue and the workflow trigger on that — which is what I'd usually prefer, because it decouples the availability of the two sides."

**Q: What are Durable Functions and when do you use them?**
> "Durable Functions add stateful orchestration to Functions — an orchestrator function that survives process restarts by replaying its history from a durable store. It's how you do long-running or multi-step work in Azure without hand-rolling a state machine.
>
> The patterns: function chaining for sequential steps, fan-out/fan-in for parallel work with an aggregation, async HTTP API for the 202-plus-poll pattern, monitor for polling an external system, human interaction with a durable timer and an external event for approvals, and entities for stateful aggregation.
>
> For integration specifically, this is my answer to 'how do you implement a saga in Azure' — the orchestrator holds the state, calls each service, and on failure calls the compensating actions in reverse."

**Q: Logic Apps vs Functions vs Data Factory vs APIM — when do you reach for each?** ⭐

| Need | Reach for |
|---|---|
| Expose, secure, throttle, transform an API surface | APIM |
| Connect systems in a workflow with connectors, visible run history | Logic Apps |
| Custom code on an event; a hard transformation step | Functions |
| Long-running / multi-step / saga orchestration in code | Durable Functions |
| Bulk data movement and ETL at scale, scheduled | Data Factory |
| Decouple two systems so one can be down | Service Bus |

---

### B4 · Messaging & event streaming ⭐ **Rehearse verbatim**

**Q: Service Bus vs Event Grid vs Event Hub — when do you use each?** `THE single most-repeated Azure integration question`

> "One line each. **Service Bus** is an enterprise message broker — pull-based, the message is held until a consumer explicitly completes it, and it gives you ordering within a session, dead-lettering, duplicate detection, scheduled delivery and transactions. Use it when every message must be processed reliably and you care what happens when processing fails.
>
> **Event Grid** is a push-based event router for reactive notifications — small events, at-least-once delivery with exponential backoff retry, and dead-lettering to storage. Use it for 'something happened, whoever cares should react' — a blob landed, a resource changed.
>
> **Event Hubs** is a high-throughput streaming ingestion pipeline — partitioned log, consumers track their own offsets and can replay, retention is time-based. Use it for telemetry and streams where you're measuring throughput in events per second, not messages per transaction.
>
> The discriminator I actually use: **do I care about each individual message and its failure? → Service Bus. Am I reacting to a notification? → Event Grid. Am I ingesting a firehose I might want to replay? → Event Hubs.**"

**Pushback — "give me a real scenario where you chose between Service Bus and Event Grid":**
> "[YOUR PROJECT]. The determining question was what happens on failure. With Event Grid, once the retry schedule is exhausted the event goes to a dead-letter blob and it's on you to build the replay. With Service Bus, the message sits in the queue until it's explicitly completed, and the dead-letter queue is a first-class queue I can receive from and resubmit. Because [ORDER/PAYMENT/whatever] couldn't be silently lost, that decided it."

**Q: What is a dead-letter queue and how does a message get there?**
> "A sub-queue that holds messages that can't be delivered or processed. In Service Bus a message dead-letters when the delivery count exceeds `MaxDeliveryCount` — the peek-lock kept expiring because processing failed or the consumer crashed; when the message TTL expires; when the application explicitly dead-letters it after deciding it's poison; when a subscription filter throws evaluating it; or when the message exceeds a session or size constraint on forward.
>
> The operational half matters more than the definition: you need an alert on DLQ depth, and a supported way to inspect and resubmit — usually a small Function that reads the DLQ, logs the `DeadLetterReason`, and either fixes and resubmits or parks it for a human."

**Q: Peek-lock vs receive-and-delete?**
> "Receive-and-delete removes the message the moment it's delivered — at-most-once, so a crash loses it. Peek-lock hands the consumer an exclusive lock for a lock duration; the consumer processes, then calls complete to remove it, abandon to release it immediately, or dead-letter it. If the consumer dies, the lock expires and the message becomes visible again. That's at-least-once, which is what you want — and it's why the consumer must be idempotent."

**Q: How do you guarantee ordering?** `TRAP`
> "You don't get ordering and parallelism at the same time — that's the tradeoff, and it's the answer they're listening for. In Service Bus you use **sessions**: every message with the same session ID goes to one consumer, in order. So you pick a session key that's the smallest unit that needs ordering — customer ID, account ID, order ID — and you get ordering *within* that key while still processing different keys in parallel.
>
> Kafka and Event Hubs do the same thing with a partition key. Same principle: ordering is per-key, never global, unless you're willing to run a single consumer and cap throughput at one."

**Q: How do you handle a poison message?**
> "Bound the retries — `MaxDeliveryCount` in Service Bus, an explicit attempt counter otherwise — so a message that always fails goes to the DLQ instead of looping forever and blocking the queue. Then alert on DLQ depth, log the reason, and have a replay path. The failure mode you're avoiding is one bad message consuming the whole consumer's throughput indefinitely."

**Q: Explain exponential backoff with jitter.**
> "You retry after a delay that doubles each attempt — 1s, 2s, 4s, 8s — capped at a maximum, so you stop hammering a struggling dependency. The jitter is the part people leave out: if a hundred consumers all fail at the same instant and all back off by exactly the same schedule, they retry in a synchronised wave and knock the service over again. Adding randomness spreads them out. Full jitter is `sleep = random(0, min(cap, base * 2 ** attempt))`.
>
> And retry only what's retryable — a 429 or 503 or a timeout, yes; a 400 or a 401, never, because it will fail identically forever."

**Q: What is the transactional outbox pattern?**
> "It solves the dual-write problem: you need to update your database *and* publish an event, and there's no transaction spanning both — so a crash in between either loses the event or publishes an event for a change that rolled back.
>
> The outbox fixes it by writing the event into an `outbox` table in the *same* database transaction as the business change. Now it's atomic. A separate relay process polls that table and publishes to the broker, marking rows as sent — with `SELECT ... FOR UPDATE SKIP LOCKED` so multiple relay instances don't collide. Delivery is at-least-once, so consumers still need to be idempotent, but you can no longer lose an event or publish a phantom one."

**Q: Saga — choreography or orchestration?**
> "A saga replaces a distributed transaction with a sequence of local transactions plus compensating actions that undo them. **Choreography** means each service publishes events and the next reacts — no central coordinator, low coupling, but the overall flow exists nowhere in the code and debugging it means reading five services' logs. **Orchestration** means one coordinator explicitly calls each step and issues compensations on failure — the flow is readable in one place, at the cost of a component everything depends on.
>
> Beyond three or four steps I go orchestration every time, because someone has to support this at 3am. In Azure that's Durable Functions or a Logic App as the orchestrator."

**Q: Kafka — consumer groups, rebalancing, lag?**
> "A consumer group is a set of consumers sharing a topic's partitions; each partition is assigned to exactly one consumer in the group at a time, which is what bounds your parallelism at the partition count. When a consumer joins or dies, the group rebalances and partitions are reassigned — and during a rebalance you can get duplicate processing, because the new owner resumes from the last *committed* offset, which may be behind what the old owner had actually processed. Cooperative sticky assignment reduces the disruption.
>
> Consumer lag is the broker's latest offset minus the group's committed offset for that partition — it's the number one health metric, because rising lag means you're falling behind and no error is being thrown."

**Q: Kafka vs RabbitMQ vs Service Bus?**
> "Kafka is a distributed, partitioned, replayable log — consumers track offsets, messages stay for the retention period whether or not anyone read them, and it's built for very high throughput. RabbitMQ and Service Bus are brokers — the broker routes each message and removes it once acknowledged, and they give you richer per-message semantics: per-message TTL, priority, scheduled delivery, dead-lettering, complex routing.
>
> Rule: if you need to replay history or fan out the same stream to many independent consumers at high volume, Kafka. If you need reliable per-message work distribution with acknowledgement and failure handling, a broker."

---

### B5 · Python `EY-logged`

**Q: What is the difference between multithreading and multiprocessing in Python?** `EY-logged verbatim`
> "Threads share one interpreter and one memory space, and because of the GIL only one thread executes Python bytecode at a time — so threads don't give you CPU parallelism, but they do help for I/O-bound work, because the GIL is released during I/O. Processes have separate interpreters and separate memory, so they give real parallelism across cores, at the cost of process startup and having to serialise anything you pass between them.
>
> The rule: I/O-bound → threads or asyncio; CPU-bound → `multiprocessing` or push the work out of Python. For an integration workload — HTTP calls, queue reads, database round trips — it's almost always I/O-bound, so asyncio."

**Q: What is the difference between async and await?** `EY-GDS-logged verbatim`
> "`async def` declares a coroutine function — calling it doesn't run the body, it returns a coroutine object. `await` is what actually runs it, and it's the point where the coroutine yields control back to the event loop so the loop can run something else while that operation is pending.
>
> So `async` marks the function as suspendable; `await` is where the suspension happens. The consequence that matters in production: if you `await` something that isn't actually async — a blocking database driver, `time.sleep`, a CPU-heavy loop — you block the entire event loop and every other in-flight request stalls. That's the number one async bug I see. The fix is `asyncio.to_thread` or a proper async driver."

**Q: What is a thread pool?** `EY-GDS-logged verbatim`
> "A fixed set of worker threads that pull tasks off a queue, so you pay thread creation cost once instead of per task, and you bound concurrency — which is the real reason to use one. Without a bound, a thousand incoming requests create a thousand threads and you exhaust memory or the downstream's connection limit. In Python that's `concurrent.futures.ThreadPoolExecutor`; the async equivalent for bounding concurrency is `asyncio.Semaphore`."

**Q: What is the GIL?**
> "A mutex in CPython that allows only one thread to execute Python bytecode at a time. It exists because CPython's memory management — reference counting — isn't thread-safe, and a single global lock was the simplest correct answer. It's released around I/O and inside C extensions like NumPy, which is why threads still help for I/O-bound work and why NumPy can use multiple cores. It's a CPython implementation detail, not a language feature."

**Q: What are decorators?**
> "A function that takes a function and returns a replacement, applied with `@` syntax. It's how you add cross-cutting behaviour without touching the function body — in an API service that's authentication checks, retry logic, timing and structured logging, caching. Always wrap with `functools.wraps` so the name, docstring and signature survive, otherwise your logging and your OpenAPI generation both break."

**Q: Explain Python memory management.**
> "Reference counting as the primary mechanism — every object tracks how many references point at it, and it's freed the moment that hits zero — plus a generational cycle collector for reference cycles that counting alone can't free. Allocation goes through pymalloc for small objects, which manages arenas and pools rather than calling `malloc` per object. The practical consequence: memory is freed deterministically most of the time, but a cycle involving objects with references to each other waits for the collector."

**Q: What's the difference between a `@classmethod` and a `@staticmethod`?** `EY-GDS-logged`
> "A `classmethod` receives the class as its first argument, so it can construct instances and it respects subclassing — that's why alternative constructors are classmethods. A `staticmethod` receives nothing implicit; it's a plain function that lives in the class namespace for organisational reasons."

**Q: What is MRO in Python?** `EY-GDS-logged`
> "Method Resolution Order — the linearised order in which Python searches base classes for an attribute. It uses C3 linearisation, which guarantees that a class always precedes its parents and that the relative order of parents in the base list is preserved. You can inspect it with `ClassName.__mro__`. It matters with multiple inheritance and cooperative `super()` calls, and it's why Python raises a TypeError at class creation time if a consistent order can't be constructed."

---

### B6 · SQL `EY-logged — appears in at least 3 separate EY reports`

**Q: Write a SQL query to find the second highest salary.**

The answer they expect:
```sql
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```

The answer that marks you senior — say this second:
```sql
SELECT DISTINCT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
) ranked
WHERE rnk = 2;
```
> "I'd use `DENSE_RANK` rather than `RANK` because ties should share a rank — with `RANK`, two people on the top salary means there is no rank 2 at all and the query silently returns nothing. And `DENSE_RANK` generalises: change the 2 to an N and it's the Nth highest, and adding `PARTITION BY department_id` gives it to you per department without rewriting anything."

**Q: Second-highest salary per department:**
```sql
SELECT department_id, salary
FROM (
    SELECT department_id, salary,
           DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rnk
    FROM employees
) r
WHERE rnk = 2;
```

**Q: Explain the join types.**
> "INNER returns only matching rows on both sides. LEFT returns every row from the left with NULLs where the right doesn't match — that's the one you use to find *missing* records, with `WHERE right.id IS NULL`. RIGHT is the mirror and I avoid it because it reads badly; I reorder the tables instead. FULL OUTER returns everything from both with NULLs on either side. CROSS is the Cartesian product, which is either deliberate or a bug."

**Q: Explain normalization.** `EY-logged`
> "Organising tables to eliminate redundancy so a fact lives in exactly one place. 1NF: atomic values, no repeating groups. 2NF: 1NF plus no partial dependency on part of a composite key. 3NF: 2NF plus no transitive dependency — non-key columns depend on the key and nothing else.
>
> In practice I normalise the transactional side and denormalise deliberately on the read side when the join cost is measured, not assumed."

---

### B7 · CI/CD, IaC, GitOps, Kubernetes — the heaviest JD block `EY-logged verbatim on AmbitionBox`

**Three of the nine JD responsibilities live here** (build CI/CD pipelines with security scanning; provision infra with IaC; containerize and deploy on Kubernetes with Helm and GitOps). Weight it accordingly.

The five questions immediately below are logged against **EY DevOps Engineer** on AmbitionBox by real candidates. They map almost exactly onto this JD's responsibility list.

**Q: Explain the Docker `EXPOSE` and `publish` commands.** `EY-logged` `TRAP`
> "`EXPOSE` is documentation. It records in the image metadata that the container listens on a port — it does not open anything and it does not make the port reachable from the host. Publishing with `-p 8080:80` is what actually creates the host-to-container port mapping. The only functional thing `EXPOSE` does is give `docker run -P` the list of ports to map to random host ports."

**Q: How do you check resources using Terraform?** `EY-logged`
> "`terraform plan` is the main one — it refreshes state against the real infrastructure and shows the diff without changing anything, which is also how you detect drift. `terraform state list` enumerates what's tracked, `terraform state show <addr>` gives the recorded attributes of one resource, and `terraform show` prints the whole state. For a resource that exists in the cloud but not in state, `terraform import` brings it under management."

**Q: What is the Terraform state file and why store it remotely?**
> "State is Terraform's map from the resources in your configuration to the real objects in the cloud, plus cached attributes. Without it, Terraform can't tell an update from a create.
>
> It goes in a remote backend — for Azure, a storage account container — for three reasons: the team shares one source of truth instead of each engineer holding a local copy; the backend provides **state locking** so two concurrent applies can't corrupt it; and it's versioned and backed up. It also **contains secrets in plaintext** — any password or key a resource emits is in there — so the container is private, encrypted, and access-controlled like a credential store, not like a config file."

**Q: How does HPA work in Kubernetes?** `EY-logged`
> "The Horizontal Pod Autoscaler is a control loop that periodically reads a metric — by default CPU utilisation via the metrics server — compares it to a target, and scales the replica count of a Deployment. The calculation is roughly `desired = ceil(current_replicas * current_metric / target_metric)`, bounded by `minReplicas` and `maxReplicas`, with a stabilisation window so it doesn't flap.
>
> For an integration workload CPU is usually the wrong signal — a consumer waiting on a queue isn't CPU-bound. There I use **KEDA**, which scales on queue depth or Kafka consumer lag directly, and can scale to zero. That's the answer that shows you've actually run this."

**Q: What are the objects in a Kubernetes service?** `EY-logged`
> "A Service gives a stable virtual IP and DNS name in front of a set of Pods selected by label, and load-balances across the ready ones. Types: **ClusterIP** — internal only, the default; **NodePort** — exposed on a port on every node; **LoadBalancer** — provisions a cloud load balancer, which on AKS is an Azure Load Balancer; **ExternalName** — a DNS CNAME to something outside the cluster. A **headless** service, `clusterIP: None`, skips the virtual IP and returns pod IPs directly, which is what StatefulSets use for stable per-pod DNS.
>
> Under the hood the Service selects Pods, the EndpointSlice tracks the ready pod IPs, and kube-proxy programs the routing."

**Q: Difference between `git pull` and `git fetch`?** `EY-logged`
> "`git fetch` downloads the remote's commits and updates your remote-tracking branches, but doesn't touch your working branch. `git pull` is `fetch` followed immediately by `merge` (or `rebase` if configured) into your current branch. So fetch is safe and lets you inspect what changed first; pull can produce a merge commit or a conflict you weren't expecting."

**Q: A pod is in CrashLoopBackOff. Walk me through it.** `VERY HIGH frequency`
> "CrashLoopBackOff means the container starts, exits, and the kubelet is backing off before restarting it — so the container *is* running and then dying, which is different from ImagePullBackOff or Pending.
>
> Sequence: `kubectl describe pod` first, for the exit code and the events — exit 137 is OOMKilled or SIGKILL, exit 1 is an application error. Then `kubectl logs <pod> --previous`, because the current container may not have produced logs yet and I need the *previous* instance's output. Then check whether the liveness probe is killing it — a liveness probe pointed at a dependency, or with too short an `initialDelaySeconds`, kills a healthy but slow-starting app in a loop. Then config: a missing ConfigMap key or Secret, or a bad command. Then resources: if it's exit 137 with no OOM in the app logs, the memory limit is too low.
>
> The classic one in an integration service is a liveness probe that checks the downstream database. The database blips, every pod fails liveness at once, they all restart, and now you've turned a dependency blip into a full outage. Liveness answers 'is this process wedged'; readiness answers 'can I serve traffic right now'. Dependency checks belong in readiness."

**Q: Liveness vs readiness vs startup probe?** `TRAP`
> "Liveness: if it fails, the kubelet restarts the container. Readiness: if it fails, the pod is removed from Service endpoints but keeps running. Startup: disables the other two until the app has started, for slow-booting applications.
>
> The trap is putting a dependency check in liveness — see above. Liveness should check only whether *this process* is wedged, ideally nothing more than 'the event loop is responsive'."

**Q: How do you handle secrets in a pipeline?**
> "Never in the YAML and never in the repo. In Azure DevOps: a variable group linked to Key Vault, or better, a service connection using **workload identity federation** so the pipeline gets a short-lived token via OIDC and there's no service principal secret to rotate at all. Same in GitHub Actions — `azure/login` with federated credentials and `permissions: id-token: write`.
>
> At runtime the application shouldn't hold secrets either — managed identity to Key Vault, or the CSI Secret Store driver mounting them into the pod. Plus `gitleaks` in CI to catch anything committed by accident."

**Q: Explain deployment strategies.**
> "**Recreate** — stop the old, start the new; downtime, but safe when two versions can't coexist. **Rolling** — replace instances gradually, controlled by `maxSurge` and `maxUnavailable`; the default and usually right. **Blue-green** — run both environments and flip traffic at once; instant rollback, double the infrastructure. **Canary** — send a small slice of traffic to the new version, watch the metrics, then ramp; safest and the most operationally involved.
>
> The hard version for integration workloads: a message consumer with in-flight messages can't just be killed. You need graceful shutdown — trap SIGTERM, stop accepting new messages, finish or abandon what's in flight, then exit — with `terminationGracePeriodSeconds` long enough to actually complete. And if the message schema changed, both versions have to handle both schemas during the rollout, which means schema changes ship one release *ahead* of the code that needs them."

---

**Q: How do you build a CI/CD pipeline for an integration service?** `JD responsibility 5`
> "Build once, promote everywhere. One build produces one immutable artifact — a container image with a digest — and that exact digest is what moves through dev, test and prod. Nothing gets rebuilt per environment, because then you're not deploying what you tested.
>
> Stages: build and unit test → static analysis and dependency scan → build the image and scan it → publish to ACR → contract tests against the OpenAPI spec → `terraform plan` gated on approval → deploy to AKS via Helm → smoke test → promote.
>
> The platform-engineering part, and the part I'd argue for: none of that lives in a per-service pipeline file. It lives in a **template** — an Azure DevOps template that services `extends`, or a reusable GitHub Actions workflow they call. Teams supply parameters; they don't get to skip the scanning stages. That's how you make the secure path the easy path instead of relying on twelve teams each remembering."

**Q: How do you handle secrets in a pipeline?** ⭐ `TRAP`
> "Never in YAML, never in the repo. The modern answer is **workload identity federation** — the pipeline presents an OIDC token from the CI provider, Entra ID trusts that federated credential, and the pipeline gets a short-lived Azure token. There is no client secret in existence, so there's nothing to rotate and nothing to leak.
>
> In Azure DevOps that's a service connection configured for workload identity federation. In GitHub Actions it's `permissions: id-token: write` plus `azure/login` with `client-id`, `tenant-id` and `subscription-id` and no `client-secret`. Where a secret genuinely must exist, it's in Key Vault and referenced by a variable group — never inlined.
>
> At runtime the application shouldn't hold secrets either: managed identity to Key Vault, or the Secret Store CSI driver mounting them into the pod. Plus `gitleaks` with push protection so nothing gets committed by accident.
>
> The trap is answering 'I use secret variables in the pipeline, they're masked in the logs.' Masking is not protection — anyone who can edit the pipeline can exfiltrate the value."

**Q: The JD names "security scanning" in the CI/CD responsibility. What do you scan and where?** `JD responsibility 5`
> "Five categories, each at a different stage, and I'd distinguish what **gates** the build from what only **reports** — because if everything gates, teams start bypassing the pipeline.
>
> - **Secret scanning** — `gitleaks`, plus GitHub push protection. Gates, and it gates at push time, not at build time. A committed secret is already compromised.
> - **SAST** — CodeQL or SonarQube; `bandit` for Python. Gates on high severity, reports the rest.
> - **SCA / dependency scanning** — Dependabot, `pip-audit`, Snyk. Gates on known-exploitable criticals; reports everything else, because a CVE with no fix available shouldn't block a release.
> - **Container image scanning** — Trivy in the pipeline, plus ACR and Defender for Containers scanning what's already published, since a CVE can be disclosed after you shipped.
> - **IaC scanning** — Checkov or tfsec against the Terraform, plus the Bicep linter. This is the one people skip and it's the one that catches a public storage account before it exists.
>
> Then **DAST** or API fuzzing — ZAP, or `schemathesis` driven off the OpenAPI spec — against a deployed test environment, not in the build.
>
> Two things I'd add for a financial-services client: an **SBOM** generated per build with Syft or CycloneDX so you can answer 'are we exposed to this CVE' in minutes rather than days, and image signing with `cosign` so the cluster can verify provenance.
>
> The honest operational problem is false positives. If you don't run an allowlist with an expiry and an owner on every suppression, scanning becomes theatre — everyone suppresses everything and nobody reads the report."

**Q: What is GitOps, and why pull instead of push?** ⭐ `JD responsibility 7`
> "GitOps means the desired state of the cluster lives in Git, and a controller running *inside* the cluster continuously reconciles the actual state toward it. Git is the source of truth, not the pipeline.
>
> The pull model matters for one concrete reason: in a push model your CI system holds cluster admin credentials, so anyone who can compromise the pipeline owns the cluster, and your blast radius is every environment the pipeline can reach. In a pull model the agent pulls from Git and nothing outside the cluster holds credentials to it.
>
> The second benefit is drift. Someone runs `kubectl edit` at 2am during an incident. In a push model that change silently persists until the next deploy overwrites it — and nobody knows. With `selfHeal` enabled the controller detects the divergence and reverts it, and you can see it happened.
>
> And the third is the audit answer, which is why financial-services clients like it: what's running in production is exactly what's in the Git commit, signed and reviewed. 'Prove the code in prod is the code that was approved' becomes a `git log`."

**Q: ArgoCD or Flux?**
> "Both implement the same model, so I'd pick on the operating context rather than on features.
>
> **ArgoCD** for multi-team, multi-cluster estates — it has a real UI, an Application CRD with visible sync and health status, Projects for multi-tenancy and RBAC, ApplicationSets for generating apps across clusters, and sync waves for ordering. The UI matters more than engineers like to admit: it's what lets a support engineer see at a glance that prod is out of sync.
>
> **Flux** when you want the GitOps Toolkit as composable controllers and everything driven from Git with no UI to secure — GitRepository, Kustomization, HelmRelease, plus image automation controllers that can write image tag updates back to Git.
>
> For an EY client with several teams sharing clusters I'd default to ArgoCD, mainly for the multi-tenancy and the visibility. I'd pick Flux if the client's platform team wanted a lighter, fully-declarative footprint."

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: order-integration
  namespace: argocd
spec:
  project: integration
  source:
    repoURL: https://github.com/acme/integration-manifests.git
    targetRevision: main
    path: charts/order-integration
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: integration-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 10s
        factor: 2
        maxDuration: 5m
```

**Q: How do you manage secrets in GitOps? You can't commit them.** `TRAP`
> "Right — and the wrong answer is 'commit them encrypted and decrypt in the cluster,' which is only *half* wrong. Four options:
>
> **External Secrets Operator** is what I'd pick for Azure: the manifest in Git contains only a *reference* to a Key Vault secret, and the operator materialises the actual Kubernetes Secret in-cluster. Nothing sensitive ever enters Git, and rotation happens in Key Vault with no commit.
>
> **Secret Store CSI driver** mounts Key Vault secrets straight into the pod as files, so no Kubernetes Secret object exists at all. Cleanest, but the app has to read from a path rather than an env var.
>
> **Sealed Secrets** encrypts with a controller-held key so the sealed value is safe in Git — but it's cluster-bound and rotation means re-sealing every secret.
>
> **SOPS** with a KMS or Key Vault key — good developer ergonomics, works with Flux natively, but the ciphertext lives in Git forever, so a future key compromise is retrospective.
>
> For a financial-services client I'd go External Secrets or the CSI driver, because 'the secret was never in the repository' is a much easier statement to make to an auditor than 'it was in the repository but encrypted'."

**Q: What is progressive delivery? How does a canary decide to roll back?**
> "Progressive delivery is shifting a small fraction of real traffic to a new version, watching metrics, and either ramping or rolling back automatically — so the decision is made by data instead of by someone watching a dashboard.
>
> Flagger or Argo Rollouts drive it. You define a canary with a step schedule — 5%, 10%, 25% — an interval, and metric checks against Prometheus: success rate above 99%, p99 latency under a threshold. At each step it evaluates; if a check fails more than the allowed number of times it halts and reverts traffic to the primary. It needs something underneath that can actually split traffic — a service mesh, or an ingress controller that supports weighted routing.
>
> The integration-specific caveat: canary is a *request-path* mechanism. It works for a synchronous API. For a **message consumer** there's no traffic to split — both versions pull from the same queue. There you run the new version at low replica count against the same subscription and compare error rates and processing latency, or you use a separate subscription with a filter. Saying that unprompted is what shows you've actually done this rather than read about it."

**Q: You're deploying a message consumer. How do you avoid losing in-flight messages?** ⭐ `TRAP`
> "Graceful shutdown, and it has to be explicit — the default will lose messages.
>
> Kubernetes sends SIGTERM, waits `terminationGracePeriodSeconds`, then SIGKILLs. So the consumer traps SIGTERM, stops pulling new messages, finishes or abandons what's already in flight, closes the receiver, and exits. `terminationGracePeriodSeconds` has to exceed your worst-case message processing time or the kernel kills you mid-transaction.
>
> Because you're using peek-lock, anything abandoned goes back on the queue and another consumer picks it up — so the guarantee is at-least-once and the consumer must be idempotent regardless.
>
> The one people miss: if the message **schema** changed, both versions run simultaneously during a rolling update. So a schema change ships one release *ahead* of the code that requires it — release N understands both shapes, release N+1 starts writing the new one. Skip that and your rollout breaks in the middle with half the consumers unable to parse."

```python
import asyncio, signal, logging
from azure.servicebus.aio import ServiceBusClient

log = logging.getLogger(__name__)

async def main(conn_str: str, queue: str) -> None:
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown.set)

    async with ServiceBusClient.from_connection_string(conn_str) as client:
        async with client.get_queue_receiver(queue, max_wait_time=5) as receiver:
            while not shutdown.is_set():
                for msg in await receiver.receive_messages(max_message_count=10, max_wait_time=5):
                    try:
                        await handle(msg)
                        await receiver.complete_message(msg)
                    except Exception:
                        log.exception("processing failed, abandoning for redelivery")
                        await receiver.abandon_message(msg)
            log.info("SIGTERM received; receiver closed, in-flight drained")
```

**Q: What does "platform engineer" mean to you, versus a developer?** `THE FRAMING QUESTION`
> "A developer optimises for their service shipping. A platform engineer optimises for *every* service shipping, which is a different problem — the output isn't an application, it's a paved road.
>
> Concretely: instead of writing a pipeline, you write the template twelve teams extend, with the scanning and approval gates baked in so they can't be skipped. Instead of provisioning a Service Bus namespace, you write the Terraform module that provisions it correctly — private endpoint, managed identity, diagnostic settings wired up — so nobody has to get it right from scratch. Instead of documenting your deployment, you write the runbook and the golden Helm chart.
>
> The test I'd apply: if a team can do the right thing faster than the wrong thing, the platform is working. If the secure path is slower, everyone routes around it and you've built governance theatre."

### B8 · Auth & security `VERY HIGH frequency`

**Q: What are the four roles in OAuth 2.0?**
> "Resource owner — the user who owns the data. Client — the application asking for access. Authorization server — issues tokens. Resource server — the API that accepts them. The distinction people blur is client versus resource owner: in `client_credentials` there *is* no resource owner, the client is acting as itself."

**Q: Which OAuth flow for service-to-service integration?**
> "`client_credentials`. There's no user in the loop — the service authenticates as itself with a client ID and either a secret, a `private_key_jwt`, or a client certificate, and gets an access token scoped to what it's allowed to do. In Azure the better version is a **managed identity**, where the platform issues the token and no credential exists in your configuration at all.
>
> For anything with a user in front of it, `authorization_code` with PKCE. Implicit and resource-owner-password are both deprecated — implicit because the token comes back in the URL fragment where it leaks through history and referrers, ROPC because it requires the app to handle the user's actual password."

**Q: What is PKCE and why is it now the default?**
> "Proof Key for Code Exchange. The client generates a random `code_verifier`, sends its hash as the `code_challenge` on the authorization request, and sends the original verifier when redeeming the code. So an attacker who intercepts the authorization code can't exchange it without the verifier. It was introduced for mobile apps that can't hold a secret, but it's now recommended for confidential clients too, because it defends against code interception regardless of client type."

**Q: id_token vs access_token?** `TRAP — the #1 OIDC mistake`
> "The id_token is OIDC's assertion *to the client* about who the user is — audience is the client, and it's for the client to know it has a logged-in user. The access_token is OAuth's credential for calling an API — audience is the API.
>
> Never accept an id_token as an API access token. It's addressed to a different audience, it carries no scopes, and accepting it means anyone who can get a user signed in to any app can call your API."

**Q: How do you validate a JWT?** ⭐
> "Eight checks, in order:
> 1. **Signature** — against the issuer's public key, fetched from the JWKS endpoint and selected by the `kid` header. Cache the JWKS, refresh on unknown `kid`, so key rotation doesn't take you down.
> 2. **`alg`** — pin the algorithms you accept. Never trust the token's own `alg` header, or you're open to `alg: none` and to HS256 confusion where an attacker signs with your public key as an HMAC secret.
> 3. **`iss`** — the expected issuer, exactly.
> 4. **`aud`** — your API's identifier. This is the check that stops a valid token for a different API being replayed at yours.
> 5. **`exp`** — not expired, with only a small clock skew allowance.
> 6. **`nbf`** — not before.
> 7. **Scopes or roles** — that the token actually authorises this operation.
> 8. **Object-level authorisation** — that this subject may touch *this specific record*. That's OWASP API Security #1, BOLA, and it's the one that gets skipped.
>
> Signature validity is not authorisation. A perfectly valid token from the right issuer still doesn't mean this user may read invoice 4471."

**Q: How do you revoke a JWT?** `TRAP`
> "You largely can't — that's the tradeoff you accept when you choose stateless validation, and the honest answer is to say so rather than pretend. Three mitigations: keep access tokens short-lived, five to fifteen minutes, and handle revocation at refresh time; maintain a deny-list of `jti` values for the remaining lifetime for the cases that genuinely need immediate kill; or use reference tokens with introspection, which gives real-time revocation at the cost of a call to the authorization server on every request."

**Q: What is mTLS and where do you terminate it?**
> "Mutual TLS — both sides present certificates during the handshake, so the server authenticates the client cryptographically at the transport layer rather than trusting something in a header. For partner integrations it's the strongest option, and it's often a contractual requirement in financial services.
>
> Termination: at APIM for a partner-facing API, using a `validate-client-certificate` policy that checks the thumbprint or issuer; at the ingress controller for cluster-internal; or via a service mesh sidecar for east-west traffic, which is the only way to get mTLS everywhere without changing every application. The real cost of mTLS is certificate lifecycle — distribution, expiry monitoring and rotation — not the handshake."

**Q: Is an API key secure enough?** `TRAP`
> "For identification and quota, yes. For authorisation of anything sensitive, no. An API key is a bearer secret with no expiry, no audience, no scopes and no user context — anyone who has it is you, forever, until someone rotates it. I use keys to identify the calling application for metering and throttling, and a JWT or mTLS for the actual authorisation decision. If a key is the only control, then it needs rotation with primary/secondary keys, hashing at rest, IP allow-listing and a short rotation period."

**Q: How would you secure an API that a client's partner consumes?** `SCENARIO`
> "Layered, from the outside in.
>
> Edge: Front Door or App Gateway with a WAF on the OWASP core ruleset, TLS 1.2 minimum, and DDoS protection. Gateway: APIM, with mTLS for partner authentication plus `validate-jwt` if there's a token, a subscription key to identify which partner is calling, and `quota-by-key` and `rate-limit-by-key` per partner so one partner can't starve the others. Contract: an OpenAPI spec with request validation at the gateway, so malformed payloads never reach the backend.
>
> Backend: private endpoint, unreachable except through the gateway; APIM authenticates to it with managed identity; every secret in Key Vault. Data: field-level encryption for anything sensitive, tokenised identifiers rather than raw ones, and object-level authorisation enforced in the service — the partner's token must not let them enumerate another partner's records.
>
> Operations: correlation ID on every request, audit log of every call with the partner identity, alerting on 401/403 spikes and on quota exhaustion — and the audit log must never contain the token itself."

---

## §C — L2 scenario questions

L2 is a Manager, Senior Manager or Director. They are assessing whether you can sit in front of a client. Answer with **structure, then the trade-off, then the failure mode.**

**Q: You have three API consumers — an internal mobile app, a third-party partner, and a public web app. Each has different security and throttling requirements. How do you design the APIM policy structure without duplicating code?**
> "Use the policy scope hierarchy rather than writing three policy sets.
>
> Global scope gets what's true for everyone — correlation ID injection, security headers, standard error handling in `on-error`. Then a **product** per consumer class: an internal product, a partner product, a public product. Each product carries its own authentication and its own `quota-by-key` and `rate-limit-by-key` — the partner gets mTLS plus a low quota, the public product gets a token plus aggressive throttling and response caching, internal gets a token from the corporate tenant and a high limit.
>
> The APIs themselves are defined once and associated with multiple products. Operation-level policies stay for genuinely per-operation concerns. Each level uses `<base />` so the parent's policy still runs, and the shared fragments live in policy fragments so a change happens once.
>
> The failure mode I'd design against: putting consumer-specific logic in the API scope with `if` statements on the subscription key. It works on day one and it's unmaintainable by the fourth consumer."

**Q: A company wants to integrate a legacy on-premises ERP with a new cloud CRM. How do you approach it?**
> "First I'd establish six things before drawing anything: which direction the data flows, whether it's real-time or batch, the volume and peak, whether the ERP can be modified at all, what the source of truth is per entity, and what the acceptable staleness is. Most of the design falls out of those answers.
>
> Assuming near-real-time, ERP as source of truth for customer master, and no ability to modify the ERP: I'd put an APIM instance in front of whatever interface the ERP exposes — usually SOAP or a database — with the self-hosted gateway or Private Link for connectivity. Change detection on the ERP side either through a CDC mechanism or a polling job on a timestamp column, publishing to Service Bus. A Logic App or Function consumes, maps to a **canonical model** rather than mapping ERP-shape directly to CRM-shape, and calls the CRM. Failures dead-letter with an alert; the mapping is idempotent so a replay is safe.
>
> The canonical model is the decision I'd defend hardest: point-to-point mapping is faster to build and becomes an N-squared problem the moment a third system shows up."

**Q: How do you sync master data bidirectionally between two systems without an infinite loop?**
> "The loop happens because A writes to B, B emits a change event, and that propagates back to A, which emits again. Three mechanisms, and I'd use all three.
>
> First, **origin tagging** — stamp each write with the system that originated it and skip propagating a change whose origin is the system you're about to send it to. Second, **content hashing** — hash the business fields and skip the write if the incoming payload hashes to what's already stored; this also protects you from loops caused by a system that touches an audit field on every write. Third, **field-level ownership** — decide per field which system is authoritative and only propagate the fields that system owns, which eliminates most of the conflict surface entirely.
>
> And then a conflict resolution rule for genuine simultaneous edits, which for master data is usually last-write-wins on a monotonic timestamp, with the losing version kept for audit rather than discarded."

**Q: How do you design a webhook delivery service? A subscriber is down for six hours.**
> "Accept-and-queue at the edge: the producer's write path never calls the subscriber synchronously — it enqueues, returns immediately, and a delivery worker does the calling. Otherwise a slow subscriber becomes your latency.
>
> Per-subscriber ordering with a session or partition key on the subscriber ID, so one subscriber's backlog doesn't block another's. Retry with exponential backoff and jitter over a long horizon — minutes, then hours — with a cap. Sign every payload with HMAC plus a timestamp, and have subscribers reject anything outside a replay window. Include an idempotency key so the subscriber can dedupe, since you're at-least-once by design.
>
> For the six-hour outage specifically: a **circuit breaker per subscriber**. After N consecutive failures, stop attempting and park that subscriber's events, so you're not burning workers on a dead endpoint. Probe periodically; when it recovers, drain the backlog at a rate limit rather than firing six hours of events in ten seconds and knocking it over again. Bound the backlog by retention, expose delivery status in the subscriber's portal, and dead-letter past the horizon with a notification — because at some point 'they've been down for three days' is their problem, not yours, and the system should say so rather than accumulate forever."

**Q: "Convince me to adopt Azure for our company."** `EY-logged as the AWS variant — persuasion is explicitly tested`

They are testing consulting instinct. **Do not launch into features.**

> "Before I argue for it, I'd want to know three things: what your team already knows, what your existing licensing and identity estate look like, and whether there's a regulatory or data residency constraint. Those usually decide it more than any feature comparison.
>
> If you're already a Microsoft shop — Microsoft 365, Entra ID for identity, SQL Server on-prem — then the argument is straightforward. Identity is the big one: your users and service principals already exist in Entra, so authentication and conditional access carry across instead of being rebuilt. Licensing benefits like Azure Hybrid Benefit make Windows and SQL migrations materially cheaper. Your team's existing .NET and SQL Server skills transfer directly, which is a real cost even though it never appears in a TCO model.
>
> Where I'd argue *against* it: if your team is already deep in AWS, the migration cost is real and the feature gap in most areas isn't wide enough to justify it. And I'd resist a multi-cloud strategy adopted for its own sake — it usually means you build to the lowest common denominator and pay for two sets of expertise.
>
> So my honest answer is that it depends on your starting point, and I'd rather scope that in a week than give you a generic answer today."

**That last paragraph is the point.** A Big4 manager is listening for someone who qualifies before advocating and who will tell a client something they don't want to hear.

---

## §D — STAR stories

EY's own careers page: they use behavioural interviewing scored on **relevant experience → action taken → result.** Structure explicitly. **Every story ends with a number.** No metric = not a story.

Fill in six of these on Day 4. Six is enough — most map onto multiple prompts.

| Story | Triggered by | Your version |
|---|---|---|
| Hard deadline delivered | "Tell me about a time you worked under pressure" / "a tight deadline" | `[ ]` |
| Production incident you owned | "Describe a time something went wrong" / "a difficult situation" | `[ ]` |
| Design decision you got wrong | "A time you made a mistake" / "something you'd do differently" | `[ ]` |
| Disagreed with a senior | "A time you disagreed with your manager/architect" | `[ ]` |
| Ambiguous requirements | "Unclear requirements" / "a difficult stakeholder" | `[ ]` |
| Learned a new stack fast | "How do you handle unfamiliar technology" — **and the Azure gap question** | `[ ]` |

### Worked example — the shape to copy

**Prompt:** *"Tell me about a time you had to navigate a difficult work situation."*

> **Situation.** "We had a nightly job that pushed [X] records into a downstream partner API. It had run fine for a year. Then the partner silently introduced rate limiting, and the job started failing about 60% of the way through — every night, and because it wasn't idempotent, re-running it created duplicates. Two teams were blaming each other and it had been going on for four days when I picked it up."
>
> **Task.** "I owned getting it stable that week, and separately getting the two teams out of the standoff, because the technical fix was actually the easier half."
>
> **Action.** "I stopped the argument by getting the data first — I pulled the response headers and found they were returning 429 with `Retry-After`, which our client was ignoring entirely and treating as a generic failure. That reframed it from a blame question to a bug on our side, which took the heat out of the meeting.
>
> Then three changes. I made the client respect `Retry-After` and added exponential backoff with jitter, because our retries were synchronised and making it worse. I added an idempotency key derived from the record's natural key so a re-run couldn't duplicate. And I made the job checkpoint its progress so a restart resumed instead of starting from zero.
>
> I also raised it with the partner — not as an escalation, just to ask what their published limits were, which nobody on our side had ever checked."
>
> **Result.** "The job went from failing nightly to zero failures over the following [N] weeks. Runtime went from [A] to [B] because we stopped hammering a throttled endpoint. The duplicate records already created — about [N] — I cleaned up with a reconciliation script. And I wrote up the retry pattern as a shared utility, which two other teams picked up."

**Why this scores:** the difficulty is interpersonal *and* technical; the action includes a judgement call (get data before arguing); the result is quantified; it ends with impact beyond the immediate fix. That's the three-element rubric hit exactly.

### The number rule

Every story needs one. If you genuinely don't have a measured number, use a magnitude you can defend: *"roughly 40,000 records a day," "about a 4-hour window," "three teams affected."* Never invent a precise-sounding number you can't defend under a follow-up.

---

## §E — The gap question ⭐

**This is the question that decides the offer.** Rehearse until fluent.

**Q: "Your background is Python and AI. This role is an Azure integration platform. Convince me."**

> "Fair question, and I'd rather answer it directly than talk around it.
>
> What I have done is the substance of integration work. [PROJECT] was orchestrating calls across [N] internal and third-party APIs — which means I've built the things this role is about: idempotency keys so a retry doesn't double-charge, exponential backoff with jitter because a naive retry storm took down a downstream once, dead-letter handling with a replay path, correlation IDs so support can trace a request across four hops, and OAuth client-credentials with token caching and rotation. Those aren't AI problems. They're integration problems that happened to sit inside an AI system.
>
> What I haven't done is own that platform at enterprise scale on this specific stack. I've used [WHAT YOU'VE ACTUALLY USED — be honest]. I have not run a production APIM instance or owned an ArgoCD estate. I'd rather say that now than have you find it in week two.
>
> What I'd point at as evidence I close the gap fast: [CONCRETE — 'I picked up [STACK] in [TIMEFRAME] on [PROJECT] and shipped [WHAT]']. The concepts port directly. APIM policies are a request pipeline — I've written middleware. Service Bus sessions are ordered partitioned consumption — same idea as a partition key. GitOps is a reconciliation loop, which is the same control-loop model as everything else in Kubernetes. What I'd be learning is a platform's vocabulary and its sharp edges, not a new way of thinking.
>
> And the direction of travel runs the other way too. EY put a billion dollars into the Microsoft AI alliance and shipped a multiagent framework into Canvas across 130,000 people. That work is integration — an agent calling an enterprise API safely is an authorisation, rate-limiting and audit problem before it's an AI problem. There won't be many people in your integration practice who've built both sides of that."

**The four beats:** *own the gap → show the transferable substance is real, with specifics → give evidence of ramp speed → land on the thing they can't easily hire.*

**Never:** apologise, over-explain, claim experience you don't have, or say "I'm a fast learner" without an example attached.

---

**Q: "This is a platform engineering role. Have you built a platform?"** `NEW — the JD title question`

> "Not at the scale you're describing, and I'd separate two things.
>
> What I have done is build the shared layer for a team — [EXAMPLE: the retry-and-idempotency utility three teams adopted / the FastAPI service template / the shared client library]. So I understand the difference between shipping something that works for me and shipping something twelve people depend on: it needs a contract, versioning, a migration path, and documentation that survives me leaving.
>
> What I haven't done is own the full paved road — the pipeline templates, the golden Helm charts, the module registry — as my primary job. But I know what the test is: if a team can do the right thing faster than the wrong thing, the platform works. If the secure path is slower than the shortcut, everyone routes around it and you've built governance theatre. That principle transfers whether it's a Python library or a Terraform module."

---

**Q: "Have you used APIM / ArgoCD / Terraform in production?"** — when the honest answer is no.

> "No. [WHAT'S ADJACENT THAT YOU HAVE DONE]. What I know concretely is the model: [THE MECHANICS — e.g. for APIM: the four policy sections, that policies compose by scope with `<base />`, `validate-jwt` against Entra, `rate-limit-by-key` for throttling, products as the packaging unit, revisions versus versions].
>
> Where I'd expect to be slow initially is the operational side — the tier limits, the sharp edges, and the CI/CD story for changing it safely. Is your estate single-instance or multi-region?"

**Three parts, then a question that shows you understand the problem shape.** The question is what turns an admission into a conversation.

---

**Q: "You have no financial services background."** `NEW — near-certain given the JD`

> "No, I don't, and I won't pretend otherwise — you'd find it in one follow-up.
>
> What I'd say is that the constraints you work under are ones I've built for, even if the domain vocabulary is new. Immutable audit trail of what ran and who approved it. Exactly-once *effect* on an operation that must not be applied twice — which is idempotency keys and a dedupe store, because exactly-once *delivery* isn't achievable. Data residency and knowing physically where a record lives. Separation of duties in the deployment path. Reconciliation as a first-class component rather than something you bolt on when the numbers don't match.
>
> What I'd need to learn is the domain layer — the message standards, ISO 20022 and where it's replacing SWIFT MT, the settlement and cut-off windows, what a reconciliation break actually means to the business. That's vocabulary and process, and it's learnable in weeks. The engineering underneath it isn't different; the tolerance for getting it wrong is.
>
> Which industry group would I be working with — is it banking and capital markets, or insurance?"

**The move:** convert the deficit into the specific list of what you'd learn, then ask a question that makes them talk. Do not claim adjacent experience you don't have. See [Financial Services Integration](12-financial-services-integration.md).


## §F — HR, grade and CTC

**This block is worth more than any technical hour.** SC1 → SC2 → SC3 is ₹13.6L → ₹19.2L → ₹24.9L at *overlapping* experience.

⚠️ **The JD says 4–8 years.** A wide band gives the recruiter room to map you to the bottom of it. At 6 years you are in the upper half — say that explicitly, with the mapping, *before* a number lands on the table. Do not let "the range for this role starts at..." go unanswered.

### Before the HR call, know these three numbers

| | Your number |
|---|---|
| **Target CTC** | `[ ]` — anchor at the top of the ₹20.5L–₹22.6L band for 6–9 yrs, higher if you have a competing offer |
| **Floor** | `[ ]` — the number below which you say no. Decide it *before* the call, not during |
| **Target sub-grade** | Senior Consultant **2** minimum. SC3 if you can evidence it |

### Q: "What is your current CTC?"

Answer it — in India, refusing usually stalls the process. But immediately reframe:

> "My current fixed is [X]. I'd say up front that I'm looking at this move on scope rather than on a percentage — I've looked at the EY GDS Senior Consultant band for six-to-nine years in engineering, and [TARGET] is where I'd be expecting to land. Where does this position map on rank and sub-grade?"

**Why it works:** you've answered, anchored on *their* band rather than a multiple of your current, and turned the question into a question about grade — which is where the real money is.

### Q: "What are your expectations?"

> "[TARGET] fixed. I've based that on the Senior Consultant band for this experience level rather than on a percentage over my current, because I think grade is the right frame for this conversation."

**Give a number, not a range.** A range gets read as your floor.

### The grade conversation — say this explicitly

> "Can I confirm the rank and sub-grade this position is mapped to? I'm asking because I understand Senior Consultant runs 1 through 3, and at six years I'd expect to map to Senior Consultant 2 or 3 rather than 1."

⚠️ **Two things to check on the offer letter before anything else:**

1. **Title.** If it says **Technology Consultant**, that's ₹9.5L–₹12.5L territory at EY GDS across 1–7 yrs — AmbitionBox's own note is *36% below the IT Services & Consulting industry average*. That is a materially different job from Senior Consultant. Query it.
2. **Sub-grade.** SC1 at six years is a down-level. Push back with your experience mapping, politely and once.

### Notice period

- Modal EY GDS notice is **60 days** (n=16,912: 2mo 65%, 3mo 15%, 1mo 12%). If you're told 90 as a blanket policy, that's a forum myth for non-manager grades — the offer letter is what controls.
- **Buyout:** exists, but is discretionary and reportedly counselor-dependent. If buyout of *your current* notice matters, get the reimbursement **in the offer letter in writing**. A verbal assurance from a recruiter is worth nothing at joining time.

### Structure

EY GDS is **90.4% fixed / 9.6% variable** company-wide — Senior Consultant 3 is 92.1% fixed. So a quoted CTC here is close to real take-home fixed, unlike a product company. **A ₹22L EY GDS offer is not comparable to a ₹22L offer with a 30% variable component** — it's better. Say this to yourself when comparing offers.

### The CIS trap

You may get a "Fill in the Candidate Information Sheet" email plus a MyEY portal login request the same day, asking for Aadhaar, payslips and UAN — **before** anyone verbally confirms selection. Candidates consistently report this does not by itself mean an offer. Fill it in, and keep every other process running until you have a signed letter.

### BGV

EY's background verification is thorough. Be ready to explain: any employment gap, any overlapping dates, dual employment (a red line), and education documents. Do not round dates on your CV.

---

## §G — Questions to ask them

Pick two or three per round. Asking nothing reads as disinterest.

**In L1 (engineer):**
1. What does the integration stack look like on this engagement — Azure-native, or IBM ACE / MuleSoft? *(EY has live reqs for both: Chennai req 1734008 is IBM App Connect Enterprise; Bengaluru req 1724333 is Cloud Integration Platform Engineer.)*
2. Is the APIM estate single-instance or multi-region, and how are policy changes deployed — through CI/CD or the portal?
3. What does the on-call and incident model look like for integration services?

**In L2 (manager/director):**
4. **Which client and which unit is this req for?** *(Bench and redeployment is a live employee complaint at GDS — a thread on the redeployment process was posted around July 2026. Some GDS positions also carry a client round after EY's rounds. Ask.)*
5. Do I work directly with the client's engineers, or through an onshore lead?
6. What does the first 90 days look like — is there an engagement waiting, or a ramp period?
7. Where does the EY.ai and Canvas agent work touch the integration practice?

**In HR:**
8. What rank and sub-grade is the position mapped to?
9. What's the RTO expectation for this team specifically? *(GDS India is commonly reported as 2 days/week, ~8–10 days a month, but it varies by service line.)*
10. Is this engagement aligned to a US or UK shift?

**Never ask:** about hikes or promotion timelines in the first round; about WFH before an offer; anything answerable from ey.com.

---

## §H — The 15 highest-probability questions, ranked

Reweighted against the updated JD. If you prepare nothing else, prepare these.

| # | Question | Where |
|---|---|---|
| 1 | Tell me about yourself | [§A1](#a1-tell-me-about-yourself-ey-gds-modal-1) |
| 2 | What projects have you worked on? Elaborate. | [§A1](#a1-tell-me-about-yourself-ey-gds-modal-1) + [§D](#d--star-stories) |
| 3 | Why do you want to work for us? | [§A2](#a2-why-do-you-want-to-work-for-us--why-ey-ey-modal-1) |
| 4 | Tell me about a time you navigated a difficult situation | [§D](#d--star-stories) |
| 5 | Your background is Python/AI — convince me | [§E](#e--the-gap-question-) |
| 6 | Service Bus vs Event Grid vs Event Hub | [§B4](#b4--messaging--event-streaming--rehearse-verbatim) |
| 7 | **What is the Terraform state file / how do you check resources?** `EY-logged` | [§B7](#b7--cicd-iac-gitops-kubernetes--the-heaviest-jd-block) |
| 8 | **How do you handle secrets in a pipeline?** | [§B7](#b7--cicd-iac-gitops-kubernetes--the-heaviest-jd-block) |
| 9 | **What is GitOps and why pull instead of push?** | [§B7](#b7--cicd-iac-gitops-kubernetes--the-heaviest-jd-block) |
| 10 | **What do you scan in CI, and what gates the build?** | [§B7](#b7--cicd-iac-gitops-kubernetes--the-heaviest-jd-block) |
| 11 | A pod is in CrashLoopBackOff — walk me through it `EY-logged` | [§B7](#b7--cicd-iac-gitops-kubernetes--the-heaviest-jd-block) |
| 12 | How would you expose a legacy SOAP service as REST? | [§B2](#b2--soap-and-legacy-integration-the-actual-job) |
| 13 | How do you make an API idempotent? | [§B1](#b1--api-design--rest-high-frequency--the-jd-leads-with-this) |
| 14 | **You have no financial services background.** | [§E](#e--the-gap-question-) |
| 15 | Second highest salary in SQL `EY-logged` | [§B6](#b6--sql-ey-logged--appears-in-at-least-3-separate-ey-reports) |

**Bolded rows are new or promoted** because the updated JD makes CI/CD, IaC, GitOps and financial services core rather than optional.

---

*Companion: [PLAN.md](PLAN.md) for the 4-day schedule and interview-day sequence. Updated JD in [jd.txt](jd.txt).*
