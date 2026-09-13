# Azure Integration Services — APIM, Logic Apps, Functions, Data Factory

> EY GDS — API & Integration Developer / Cloud Integration Platform Engineer (Senior, Rank 42)

**What this file buys you in the interview:** EY is a top-1%-of-Microsoft-partners shop; its live GDS integration reqs literally list "Logic Apps, Azure Functions, Azure APIM, AKS" and "Azure Integration Services (iPaaS)". This is the one file where you can go from *unproven* to *credible* in ~3 hours, because AIS is a small, closed, heavily-documented surface with hard numbers you can quote. Two questions are near-certain in an EY L1/L2: **"Logic Apps vs Functions — when do you pick each?"** and **"Service Bus vs Event Grid vs Event Hubs"** (the second lives in [Messaging & Event Streaming](03-messaging-and-event-streaming.md)). Everything else here is depth insurance.

**How to use it:** if you only have 60 minutes, read §1 (decision matrix), §3 (policy engine — memorise two policy blocks), §5.1 (Consumption vs Standard), §6.3 (Durable patterns), the Traps in §11, and the Rapid-Fire.

**Bridge from your stack:** APIM is *nginx + your FastAPI middleware stack, externalised and declarative*. `validate-jwt` is your `Depends(verify_token)`. `rate-limit-by-key` is slowapi. `cache-lookup` is `@lru_cache` in front of the route. Logic Apps is *Airflow/Prefect for business events*, drawn instead of coded. Durable Functions is *Celery chains/chords with automatic replay-based checkpointing*. Say those out loud in the interview — panels reward the mapping.

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [The AIS Map and The Decision Matrix](#1-the-ais-map-and-the-decision-matrix) | Q1–Q4 |
| 2 | [APIM: Architecture, Tiers, Objects](#2-apim-architecture-tiers-objects) | Q5–Q13 |
| 3 | [The APIM Policy Engine](#3-the-apim-policy-engine) | Q14–Q26 |
| 4 | [APIM: Hybrid, Observability, Competitors](#4-apim-hybrid-observability-competitors) | Q27–Q32 |
| 5 | [Azure Logic Apps](#5-azure-logic-apps) | Q33–Q41 |
| 6 | [Azure Functions & Durable Functions](#6-azure-functions--durable-functions) | Q42–Q45 |
| 7 | [Azure Data Factory / Synapse Pipelines](#7-azure-data-factory--synapse-pipelines) | Q46–Q48 |
| 8 | [Identity, Secrets, Networking Across AIS](#8-identity-secrets-networking-across-ais) | Q49–Q52 |
| 9 | [The AWS Mirror Table](#9-the-aws-mirror-table) | — |
| 10 | [30-Second Whiteboard Versions](#10-30-second-whiteboard-versions) | 3 |
| 11 | [Interviewer Traps](#11-interviewer-traps) | 12 |
| 12 | [Rapid-Fire](#12-rapid-fire) | 60 |

Sibling files: [Messaging & Event Streaming](03-messaging-and-event-streaming.md) · [CI/CD & IaC](05-cicd-iac-and-gitops.md) · [Auth & Security](06-auth-and-security.md) · [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md) · [API Design — REST/SOAP/GraphQL/OpenAPI](01-api-design-rest-soap-graphql-openapi.md)

---

## 1. The AIS Map and The Decision Matrix

### Q1. What is Azure Integration Services?
`[EASY]` `[NEAR-CERTAIN OPENER]`

**Answer:** Azure Integration Services is Microsoft's iPaaS bundle — five services that together do what a MuleSoft or Boomi does. **API Management** is the API gateway and API lifecycle plane. **Logic Apps** is the low-code workflow/orchestration engine with 1,400+ connectors. **Service Bus** is the enterprise message broker. **Event Grid** is the event router. **Azure Functions** is the code-when-you-need-code compute. Most real solutions use four of the five, and the interesting part of the job is choosing which does what.

Microsoft also markets **Data Factory** alongside these for bulk/batch data movement, and **Azure Data Factory + Logic Apps** is a classic "which one" question (§7).

The one-line positioning: *"AIS is the composable version of an ESB. Instead of one monolithic bus you get five single-purpose PaaS services, and the architecture work is the wiring."*

**If they push back — "Isn't that just five products, not a platform?"** — Fair. What makes it a platform is the shared plane underneath: Entra ID managed identity for auth everywhere, Key Vault for secrets, Azure Monitor / Application Insights for one correlated trace across all five, ARM/Bicep for one deployment model, and Private Link for one network story. That shared plane is what you lose if you mix in MuleSoft.

---

### Q2. Logic Apps vs Functions vs Data Factory vs an APIM policy vs Service Bus — when do you reach for each?
`[MEDIUM]` `[THE QUESTION — expect it in both L1 and L2]`

**Answer:** I pick on four axes: **who owns the logic, how long it runs, how much data moves, and whether the caller is waiting.** APIM policy for anything the gateway can do declaratively in single-digit milliseconds. Logic Apps when the value is in the connectors and the workflow should be legible to a business analyst. Functions when it's real code — custom transformation, an SDK, a library. Data Factory when it's bulk rows on a schedule. Service Bus whenever the producer and consumer must be decoupled and no message may be lost.

| Reach for | When | Do NOT use it for |
|---|---|---|
| **APIM policy** | Auth, throttling, header/URL rewrite, caching, small XML↔JSON shape change, mock, routing, request aggregation. Runs in the gateway, no extra hop. | Business logic, anything needing a DB call, anything long. Policy documents cap at 512 KiB (16 KiB in Consumption) — that limit exists for a reason. |
| **Logic Apps** | Multi-step business processes, SaaS connectivity (SAP, Salesforce, ServiceNow, D365, SharePoint), B2B/EDI, human approval, scheduled polling, long-running (up to 90 days). | Tight loops, per-request latency budgets, heavy compute. You pay per action execution — a 50-action loop over 10k items is a bill. |
| **Azure Functions** | Custom code: bespoke transforms, calling a Python library, complex validation, an algorithm. Also the *glue* Logic Apps can't express. | A workflow a business user must read. Also anything needing >230 s of synchronous HTTP (see the load-balancer ceiling in §6). |
| **Durable Functions** | Long-running orchestration *in code*: saga with compensation, fan-out/fan-in over thousands of items, async HTTP polling, waiting on a human for days. | Simple linear chains — a plain Logic App is cheaper to operate. |
| **Data Factory** | Bulk/batch: "copy 40M rows nightly", schema drift, staged copy, SSIS lift-and-shift, self-hosted IR to reach an on-prem SQL/SAP HANA. | Event-driven, transactional, per-record integration. ADF is minutes-granular, not milliseconds. |
| **Service Bus** | Guaranteed delivery, ordering via sessions, dead-lettering, duplicate detection, transactional send-and-receive, load levelling in front of a fragile backend. | Broadcasting cheap notifications to many subscribers (that's Event Grid) or telemetry firehoses (Event Hubs). |

**Code/config example — the same "on new order" requirement, four ways:**

```text
Requirement: partner POSTs an order; we validate, enrich from SAP, persist, notify 3 systems.

  APIM policy only .......... validate-jwt + validate-content + set-backend-service.
                             Stops at "validate". Cannot enrich. WRONG on its own.

  Logic App (Standard) ...... Request trigger -> Service Bus (built-in) -> SAP connector
                             -> SQL -> Event Grid publish. Legible, 5 actions, ~ms-to-s.
                             RIGHT for the happy path.

  Azure Function ............ Service Bus queue trigger -> custom Python enrichment
                             -> SQL via SQLAlchemy. RIGHT when the enrichment is
                             non-trivial code, e.g. a pricing model.

  Data Factory .............. WRONG. Nothing here is bulk or scheduled.

  Real answer .............. APIM (edge: authn, throttle, schema-validate)
                             -> Service Bus queue (decouple, buffer, DLQ)
                             -> Logic App Standard (orchestrate, SAP connector)
                             -> Azure Function (the one hard transform)
                             -> Event Grid (fan out "OrderCreated" to 3 subscribers)
```

Say that last block out loud — it is the answer to the EY scenario question *"A retail client has an on-prem ERP, a cloud OMS, a 3PL REST API and a mobile app. Design end-to-end order processing."*

**If they push back — "Why not just do it all in one Azure Function?"** — You can, and for a two-system point-to-point I would. It stops working when (a) you need the SAP/Salesforce connector — rewriting those in code is weeks, (b) you need run history a support analyst can read without a debugger, (c) the process spans days. That's the boundary: code for algorithms, workflow for choreography.

---

### Q3. When a client brings you a new integration requirement, what do you ask before choosing a hosting model?
`[MEDIUM]` `[EY consulting-shaped — this is an L2 question]`

**Answer:** Six questions, in this order, and I ask them before naming a single Azure service. **(1) Is the caller waiting?** Synchronous request/reply and fire-and-forget are different architectures. **(2) What's the volume and shape** — 10 messages/day of 5 MB, or 5,000/second of 2 KB? **(3) What's the failure contract** — can we drop, must we retry, must we replay, is ordering required? **(4) Where does the data live and what's the network path** — is anything on-prem, is Private Link mandated, is there a data-residency clause? **(5) Who operates it after go-live** — an EY run team, or the client's business users? That decides Logic Apps vs code. **(6) What's the security model** — OAuth2, mTLS, API keys, IP allow-list, and does the client's Entra tenant own the identities?

Only then: hosting model. Volume + latency picks the tier; the network path picks Standard v2 vs Premium APIM and Logic Apps Standard vs Consumption; the operator picks low-code vs code.

**If they push back — "Give me the one question that matters most"** — "Is the caller waiting?" Everything downstream forks on it. Synchronous means you own an end-to-end latency budget and every hop is a risk. Asynchronous means you own a queue, a DLQ, an idempotent consumer and a reconciliation story instead. Those are different projects.

---

### Q4. What integration patterns do you actually implement on AIS?
`[MEDIUM]`

**Answer:** I use Microsoft's own Cloud Design Patterns vocabulary, because it's what the Azure Architecture Center names and it maps 1:1 to services. The ones that come up on every integration project are Claim Check, Competing Consumers, Queue-Based Load Levelling, Publisher-Subscriber, Asynchronous Request-Reply, Retry + Circuit Breaker (always paired), Idempotent Consumer, Saga with Compensating Transaction, Gateway Routing/Aggregation/Offloading, and Anti-Corruption Layer.

| Pattern | Azure implementation |
|---|---|
| Request-Reply (sync) | APIM forwards to backend; or Logic App Request trigger + Response action |
| Async Request-Reply | Function returns `202` + `Location`; Durable Functions "async HTTP API" pattern gives you the status endpoint for free |
| Publisher-Subscriber | Service Bus topic + subscriptions with SQL/correlation filters, **or** Event Grid topic + event subscriptions |
| Competing Consumers | Service Bus queue + N Function instances / Logic App Standard with concurrency |
| Queue-Based Load Levelling | Service Bus queue in front of a rate-limited legacy backend |
| **Claim Check** | Write the payload to Blob, put the blob URI (SAS / Valet Key) in the message. This is the direct answer to Service Bus Standard's 256 KB message ceiling. |
| Saga / Compensating Transaction | Durable Functions orchestrator with explicit compensation activities; or a Logic App orchestrator with a Scope + `runAfter: Failed` compensation branch |
| Idempotent Consumer | Unique `MessageId` + Service Bus duplicate detection window + an idempotency table keyed on business ID |
| Retry + Circuit Breaker | Logic Apps `exponential` retry policy; APIM `circuitBreaker` rule on the backend entity |
| Throttling / Rate Limiting | APIM `rate-limit-by-key` + `quota-by-key` |
| Anti-Corruption Layer | APIM API façade over a SOAP/legacy backend with `xml-to-json` + `rewrite-uri` |
| Gateway Aggregation | APIM `send-request` ×N in inbound, merge in outbound |

**If they push back — "What about the Transactional Outbox?"** — Good catch: Outbox is **not** in Microsoft's Cloud Design Patterns catalog; it's Chris Richardson's microservices.io vocabulary. The Azure-flavoured implementation is a durable store plus a relay — a SQL outbox table with a polling publisher, or Cosmos DB change feed driving a Function — paired with Service Bus duplicate detection on `MessageId` and an idempotent consumer, because writing to the DB and the broker is not atomic. Naming that gap is a strong senior signal.

---

## 2. APIM: Architecture, Tiers, Objects

### Q5. What is Azure API Management and what are its components?
`[EASY]` `[HIGHEST-FREQUENCY APIM QUESTION]`

**Answer:** APIM is Azure's managed API gateway plus API lifecycle platform. It splits into three planes. The **gateway (data plane)** proxies every API call, evaluates policies and emits telemetry. The **management plane** is the ARM/REST surface where you define APIs, products, subscriptions, policies and named values — that's what the portal, Bicep, Terraform and CI/CD talk to. The **developer portal** is the auto-generated, customisable self-service site where consumers discover APIs, read docs and get subscription keys.

The key mental model for an interview: *APIM is not a load balancer.* Its job is contract, policy and identity — the OpenAPI-defined façade — not L4 distribution.

**The object model, in the order you'd create things:**

```text
API Management instance
 └─ APIs ................. an OpenAPI/WSDL/GraphQL-defined surface, with a URL suffix
     └─ Operations ....... GET /orders/{id} etc.; policies attach here for granularity
 └─ Products ............. a bundle of APIs + terms + a subscription requirement
     └─ Subscriptions .... issue the Ocp-Apim-Subscription-Key pair (primary + secondary)
 └─ Backends ............. named backend entities: URL, credentials, circuit breaker, pools
 └─ Named values ......... config + secrets, incl. Key Vault references, used as {{name}}
 └─ Policies ............. XML at global / product / API / operation scope
 └─ Certificates ......... client certs for mTLS to backends, CA certs
 └─ Loggers/Diagnostics .. App Insights + Event Hubs + Azure Monitor wiring
```

**If they push back — "Difference between a Product and an API?"** — An API is technical (a set of operations and a backend). A Product is commercial/operational: which APIs a given audience gets, whether a subscription is required, whether approval is needed, and what policy (usually quota and rate limit) applies to that audience. Same API, three Products — internal/partner/public — is exactly how you avoid duplicating policy per consumer.

---

### Q6. Walk me through the APIM tiers. Which would you pick for an enterprise integration platform?
`[HARD]` `[VERY LIKELY — and where most candidates are vague]`

**Answer:** There are two families now: the **classic** tiers (Consumption, Developer, Basic, Standard, Premium) and the **v2** tiers (Basic v2, Standard v2, Premium v2) which deploy in minutes instead of ~45 and have a better networking story per rupee. For an enterprise integration platform I default to **Premium (classic)** if I need multi-region active-active or a self-hosted gateway, and **Standard v2** if I only need outbound VNet integration to private backends — Standard v2 gives you that at roughly Standard money, which classic Standard cannot do at all.

**The feature table that decides it (Microsoft Learn, tier feature comparison):**

| Feature | Consumption | Developer | Basic | Basic v2 | Standard | Standard v2 | Premium | Premium v2 |
|---|---|---|---|---|---|---|---|---|
| Scale units | auto | 1 | 2 | 10 | 4 | 10 | **12 / region** | 30 |
| Built-in cache | — | 10 MB | 50 MB | 250 MB | 1 GB | 1 GB | 5 GB | 5 GB |
| VNet **injection** (full isolation) | ✗ | ✔ | ✗ | ✗ | ✗ | ✗ | **✔** | **✔** |
| VNet **integration** (reach private backends) | ✗ | ✔ | ✗ | ✗ | ✗ | **✔** | ✔ | ✔ |
| Private endpoint (inbound) | ✗ | ✔ | ✔ | ✗ | ✔ | ✔ | ✔ | ✔ |
| **Multi-region deployment** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✔ (only tier)** | ✗ |
| Availability zones | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✔ | ✔ |
| **Self-hosted gateway** | ✗ | ✔ (1 node) | ✗ | ✗ | ✗ | ✗ | **✔** | ✗ |
| Workspaces | ✗ | ✗ | ✗ | ✔ | ✗ | ✔ | ✔ | ✔ |
| Backup & restore | ✗ | ✔ | ✔ | ✗ | ✔ | ✗ | ✔ | ✗ |
| Static IP | ✗ | ✔ | ✔ | ✗ | ✔ | ✗ | ✔ | ✗ |
| Autoscale | n/a | ✗ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Developer portal | ✗ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |

Three lines that make this sound lived-in rather than memorised:

- **Multi-region is Premium classic only — not Premium v2.** That surprises people and it is the single reason a global client stays on classic today.
- **Developer tier has no SLA and incurs downtime when you scale it.** Never let a client run UAT on Developer and call it pre-prod.
- **There is no automated migration path from classic to v2.** Choosing wrong means re-platforming, so this decision is worth a whiteboard hour on day one.

**Throughput, with the caveat that gets you marked as senior** — the Azure pricing page publishes estimated maximum throughput per unit: **Developer ~500 req/s, Basic ~1,000, Standard ~2,500, Premium ~4,000**. Microsoft's own wording is *"Throughput figures are presented for information only and must not be relied upon for capacity and budget planning. Load test reflecting anticipated production conditions must be conducted."* Quote the numbers and then quote the caveat — that combination is what separates a senior answer.

**SLA:** Developer — none. Basic / Standard / all v2 — 99.95%. Premium deployed across zones or regions — 99.99%.

**If they push back — "What actually happens when APIM hits capacity?"** — It does **not** start returning 429. It degrades like any overloaded web server: latency climbs, connections get dropped, requests time out. Which is why the client must implement retry with backoff, and why you scale on the **Capacity** metric (classic) or **CPU/Memory Percentage of Gateway** (v2) at 60–70% sustained over ~30 minutes — 40% if you're running a single unit, because capacity has to be reserved for guest-OS updates. A scale operation takes roughly 30 minutes, so autoscale windows shorter than that are useless.

---

### Q7. Revisions vs versions in APIM. This one trips people up.
`[MEDIUM]` `[ASKED VERBATIM — "What is an API revision in Azure API Management?"]`

**Answer:** **Versions are for breaking changes and are visible to consumers; revisions are for non-breaking changes and are invisible until you promote one.** A version is a separate consumer-facing API — `/v1` and `/v2` coexist, each has its own subscribers, and consumers choose. A revision is a working copy of a *single* version: you branch it, edit policies and operations, test it on a private URL, then make it current — and every caller moves at once. Each version can have many revisions.

**Accessing a specific revision — exact URL form:**

```text
https://apis.contoso.com/customers;rev=3/leads?customerId=123
                                  ^^^^^^^
Append ;rev={n} to the API ID, before the query string.
NOT to the URI path — that is the classic mistake.
```

**Versioning schemes** APIM supports: **path** (`/v1/orders`), **query string** (`?api-version=v1`), and **header** (`Api-Version: v1`). Path is what 90% of enterprises pick because it's cache- and log-friendly.

**Operational details worth naming:**
- Promoting a revision to current can post a **change log** entry, which is published to the developer portal.
- You can **take a revision offline** so it's unreachable even via its `;rev=` URL — do that for anything not under active test.
- On a **non-current** revision you cannot change Name, Type, Description, "Subscription required", API version, API version description, Path, or Protocols. Try, and you get `Can't change property for non-current revision`.
- By default a revision inherits the current revision's security. Add an `ip-filter` on an in-development revision so external callers can't stumble onto it.
- Portal action **"Create Version from Revision"** promotes a revision into a beta/breaking version.

**If they push back — "How do you actually deprecate v1?"** — Announce with a `Deprecation` and `Sunset` header on every v1 response, keep it running at least 6 months, use APIM analytics to identify remaining callers by subscription, contact them, then move v1 to a Product that returns `410 Gone` with a link to migration docs. Never silently delete a version — that's a client incident, and at EY it's a client incident with your name on it.

---

### Q8. What is a subscription key, and is it authentication?
`[EASY→MEDIUM]` `[VERBATIM: "What is a subscription key?"]`

**Answer:** A subscription key is APIM's built-in **API key** mechanism: each subscription issues a primary and a secondary key, and the caller presents it in the `Ocp-Apim-Subscription-Key` header or the `subscription-key` query parameter. It **identifies the application, it does not authenticate the user** — it's a shared secret in a header, so treat it as an identifier for metering and throttling, not as a security boundary. For real security you layer `validate-jwt` (OAuth2/OIDC) or mutual TLS on top.

Two keys exist so you can rotate without downtime: issue new primary, let consumers move, regenerate secondary, swap. That rotation story is a good thing to volunteer.

```bash
# Subscription key in the header (preferred — keys in query strings land in access logs)
curl -i https://contoso-apim.azure-api.net/orders/42 \
  -H "Ocp-Apim-Subscription-Key: 8f3b1c2d4e5f6a7b8c9d0e1f2a3b4c5d"

# Same call, query param form (works, but avoid in production)
curl -i "https://contoso-apim.azure-api.net/orders/42?subscription-key=8f3b1c2d4e5f6a7b8c9d0e1f2a3b4c5d"
```

**Subscription scopes:** all-APIs, a single Product, or a single API. Product-scoped is the normal enterprise pattern because that's what carries the quota.

**If they push back — "So when do you turn subscriptions off?"** — When another mechanism already identifies the caller and you don't want a second secret to manage: an internal API behind `validate-jwt` with client-credentials tokens, or an mTLS partner channel. I'd still keep subscriptions on for anything I need to meter or bill per-consumer, because subscription ID is the natural `counter-key` for `rate-limit-by-key` and `quota-by-key`.

---

### Q9. Named values and Key Vault references — how do you keep secrets out of policies?
`[MEDIUM]`

**Answer:** Named values are APIM's global name/value store, referenced in policy as `{{myValue}}`. Three types: **Plain** (literal or policy expression), **Secret** (encrypted at rest by APIM), and **Key vault** (a reference to a Key Vault secret). I use Key Vault type for anything secret, so the secret has one home, one rotation process, and one audit trail.

**The mechanics you must state:**
- The APIM instance needs a **managed identity** (system- or user-assigned) with **Get + List** on secrets, or the **Key Vault Secrets User** RBAC role.
- Store the secret identifier **without the version**, otherwise it will never auto-rotate.
- After the secret changes in Key Vault, APIM picks it up **within 4 hours**; you can force it from the portal or the management REST API.
- Key Vault secrets used this way must be **1–4,096 characters** — APIM cannot retrieve longer values.
- If the Key Vault firewall is on, you **must** use the **system-assigned** identity (user-assigned won't work) and enable *"Allow trusted Microsoft services to bypass this firewall"*.

```xml
<!-- Named value used as both a header name and a header value -->
<set-header name="{{ContosoHeader}}" exists-action="override">
    <value>{{ContosoHeaderValue}}</value>
</set-header>

<!-- Named values compose with policy expressions and string interpolation -->
<set-header name="X-Signature" exists-action="override">
    <value>@($"v1={System.Net.WebUtility.UrlEncode("{{partner-signing-secret}}")}")</value>
</set-header>
```

```bicep
// Bicep: a Key Vault-backed named value, resolved via the APIM system-assigned identity
resource apim 'Microsoft.ApiManagement/service@2024-05-01' existing = {
  name: 'contoso-apim'
}

resource sapPassword 'Microsoft.ApiManagement/service/namedValues@2024-05-01' = {
  parent: apim
  name: 'sap-gateway-password'
  properties: {
    displayName: 'sap-gateway-password'
    secret: true
    keyVault: {
      // NOTE: no version segment -> auto-rotates within 4 hours of a KV update
      secretIdentifier: 'https://contoso-kv.vault.azure.net/secrets/sap-gateway-password'
      identityClientId: null   // null = use the APIM system-assigned identity
    }
    tags: ['sap', 'prod']
  }
}
```

**If they push back — "Are named values actually safe?"** — Not from your own API publishers, and Microsoft says so explicitly: anyone with write access to policies can read *any* named value by referencing `{{name}}` in a policy, even without read access on the named value resource. So granting policy-edit permission effectively grants read on every secret in that instance. The mitigations are RBAC discipline on `Microsoft.ApiManagement/service/apis/policies`, separate APIM instances (or workspaces) per trust boundary, and preferring managed identity over any stored credential so there's no secret to leak.

---

### Q10. What is a backend entity, and why not just put the URL in the policy?
`[MEDIUM]`

**Answer:** A **backend** is a first-class APIM resource holding the target URL, its credentials, its TLS validation settings, an optional **circuit breaker**, and — for pools — a load-balancing algorithm. You reference it with `<set-backend-service backend-id="..."/>`. Putting a raw URL in the policy works but you lose circuit breaking, load balancing, managed-identity auth to the backend and central rotation, and you end up editing N policies when a hostname changes.

```bicep
// Backend with a circuit breaker — exact ARM/Bicep property names matter in interviews
resource sapBackend 'Microsoft.ApiManagement/service/backends@2024-05-01' = {
  parent: apim
  name: 'sap-odata'
  properties: {
    protocol: 'http'
    url: 'https://sap-gw.contoso.internal/sap/opu/odata/sap/ZORDER_SRV'
    circuitBreaker: {
      rules: [
        {
          name: 'openOn5xx'
          failureCondition: {
            count: 10                       // 10 failures...
            interval: 'PT1M'                // ...within 1 minute
            statusCodeRanges: [ { min: 500, max: 599 } ]
            errorReasons: [ 'Server errors' ]
          }
          tripDuration: 'PT1M'              // stay open for 1 minute
          acceptRetryAfter: true            // honour the backend's Retry-After header
        }
      ]
    }
    tls: { validateCertificateChain: true, validateCertificateName: true }
  }
}
```

**Three limitations to volunteer, unprompted:** the circuit breaker is **not supported in the Consumption tier**; only **one rule per backend** is allowed; and because gateway instances don't synchronise state, tripping is **approximate and per-instance**. `acceptRetryAfter` exists specifically because Azure OpenAI backends return 429 with a `Retry-After` that can be very long.

**Backend pools** support round-robin (default), weighted and priority-based algorithms, up to **30 backends**, plus session affinity via a `Set-Cookie` session ID. Priority semantics are the useful bit: a lower-priority group is only used once *every* backend in the higher-priority groups has tripped its circuit breaker — which is exactly how you drain a provisioned-throughput Azure OpenAI deployment before spilling to pay-as-you-go.

**If they push back — "How does APIM authenticate to the backend?"** — Four ways on the backend entity: **managed identity** (set the resource ID, e.g. `https://cognitiveservices.azure.com`, and assign the role), client certificate, a header, or a query parameter. Managed identity first, always — nothing to store, nothing to rotate.

---

### Q11. How do you deploy and promote APIM config across dev/test/prod?
`[HARD]` `[EY scenario: "how do you handle environment-specific config without hardcoding anything?"]`

**Answer:** APIM config is ARM resources, so it goes through the same pipeline as everything else: **Bicep (or Terraform) in Git, one parameter file per environment, deployed by an Azure DevOps or GitHub Actions pipeline with environment approvals.** Environment-specific values — backend hostnames, Entra tenant/audience, rate limits — live in **named values** whose values come from pipeline variable groups or Key Vault, never from the policy XML. Policy XML is identical across environments; only the named values differ.

```yaml
# azure-pipelines.yml — APIM promotion with per-env parameters and gated prod
trigger:
  branches: { include: [ main ] }

variables:
  location: centralindia

stages:
- stage: Validate
  jobs:
  - job: WhatIf
    pool: { vmImage: ubuntu-latest }
    steps:
    - task: AzureCLI@2
      displayName: Bicep what-if (dev)
      inputs:
        azureSubscription: sc-integration-dev
        scriptType: bash
        scriptLocation: inlineScript
        inlineScript: |
          az deployment group what-if \
            --resource-group rg-int-dev \
            --template-file infra/apim.bicep \
            --parameters infra/params/dev.bicepparam

- stage: Dev
  dependsOn: Validate
  jobs:
  - deployment: DeployDev
    environment: integration-dev
    pool: { vmImage: ubuntu-latest }
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureCLI@2
            inputs:
              azureSubscription: sc-integration-dev
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az deployment group create \
                  --resource-group rg-int-dev \
                  --template-file infra/apim.bicep \
                  --parameters infra/params/dev.bicepparam

- stage: Prod
  dependsOn: Dev
  condition: succeeded()
  jobs:
  - deployment: DeployProd
    environment: integration-prod    # attach approvals + gates on this Environment
    pool: { vmImage: ubuntu-latest }
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureCLI@2
            inputs:
              azureSubscription: sc-integration-prod
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az deployment group create \
                  --resource-group rg-int-prod \
                  --template-file infra/apim.bicep \
                  --parameters infra/params/prod.bicepparam
```

**Zero-downtime API change:** create a **revision**, deploy it, smoke-test on the `;rev=N` URL, then flip it to current in a separate pipeline step. That's your blue/green for APIM.

**If they push back — "What about the APIM DevOps Resource Kit / Git integration?"** — The classic tiers expose a Git repository of the whole service configuration, and the APIM DevOps Resource Kit extracts a live instance into ARM templates. It's useful for onboarding a legacy instance you didn't build. I wouldn't start there in 2026 — Git config is **not available in the v2 tiers** and it drifts. Bicep or Terraform in your own repo, with a `what-if`/`plan` gate, is the durable answer. See [CI/CD & IaC](05-cicd-iac-and-gitops.md).

---

### Q12. How does APIM handle multi-region and disaster recovery?
`[HARD]`

**Answer:** Only **Premium (classic)** supports multi-region deployment. You keep one logical APIM instance and add gateway regions, allocating units per region independently — e.g. 1 unit in the primary and 5 in a secondary is legal. Azure fronts them with Traffic Manager-style routing so callers hit the nearest healthy gateway, and all regions pull the same configuration from the primary's management plane. **Only the primary location can be scaled in a multi-region setup** for the management components.

For DR beyond that: **Backup and restore** (available in Developer/Basic/Standard/Premium, *not* in v2) snapshots the whole service config; and because everything is IaC, my real DR plan is "redeploy from Bicep into the paired region and restore named values from Key Vault", which is faster to rehearse than a restore.

**If they push back — "What's the failure mode when the primary region is down?"** — Secondary-region gateways keep serving traffic from their last-known configuration; what you lose is the *management* plane — you can't publish changes until the primary is back. That's an acceptable trade, and it's worth stating explicitly, because it's the honest answer rather than "it just fails over".

---

### Q13. What are APIM workspaces and when would you use them?
`[MEDIUM]` `[differentiator — few candidates know this]`

**Answer:** Workspaces let multiple API teams share one APIM instance while owning their own APIs, products, subscriptions and policies, with RBAC isolation between them. It's the answer to *"we have 12 product teams and don't want 12 APIM instances or one shared blast radius"*. Available in **Basic v2, Standard v2, Premium and Premium v2**.

Two caveats to name so you don't over-sell it: **Key Vault integration for named values isn't available in workspaces**, and **request tracing isn't available in workspaces** — both matter operationally. MCP server capabilities also aren't supported in workspaces.

**If they push back — "Workspaces or separate instances?"** — Separate instances when trust boundaries are hard (different clients, different compliance regimes, different change windows). Workspaces when it's one organisation with many teams and you want shared platform policy at global scope plus team autonomy below it.

---
## 3. The APIM Policy Engine

### Q14. Explain the APIM policy pipeline.
`[MEDIUM]` `[VERBATIM: "What are inbound and outbound policies?" / "Explain the role of policies in API Management."]`

**Answer:** A policy definition is one XML document with four sections that run in a fixed order: **inbound** on the way in, **backend** for the call to the backend itself, **outbound** on the way back, and **on-error** which runs instead of the remainder of the pipeline whenever any policy or the backend throws. Inbound is where authentication, throttling, validation and rewriting live; backend holds exactly one policy (by default `forward-request`); outbound is where you reshape the response and strip internal headers; on-error is where you normalise errors so you never leak a backend stack trace.

```xml
<policies>
    <inbound>
        <base />
        <!-- authn, throttle, validate, rewrite, cache-lookup, route -->
    </inbound>
    <backend>
        <base />
        <!-- exactly ONE policy element; default is forward-request -->
    </backend>
    <outbound>
        <base />
        <!-- reshape body, set/strip headers, cache-store -->
    </outbound>
    <on-error>
        <base />
        <!-- normalise the error envelope; log context.LastError -->
    </on-error>
</policies>
```

The mental hook from your world: this is FastAPI middleware plus a `Depends()` chain plus an exception handler, but declarative and running in the gateway process instead of yours.

**If they push back — "What runs in `on-error`?"** — Anything after the failing policy in the current section is skipped, and control jumps to `on-error`. Inside it you have `context.LastError` with `.Source`, `.Reason` and `.Message`. That's where I build a stable error envelope and log a correlation ID; I never return `context.LastError.Message` to a public caller because it can contain backend detail.

---

### Q15. Policy inheritance — what does `<base />` actually do, and what's the evaluation order?
`[HARD]` `[the question that separates people who have used APIM from people who have read about it]`

**Answer:** Policies exist at four scopes — **global (All APIs) → product → API → operation** — and they don't override each other, they **nest**. The `<base />` element is the placeholder for "insert the policies from the next broader scope's matching section here". So the evaluation order is determined entirely by **where you put `<base />`**, not by the scope hierarchy on its own.

Concretely: in an API-scope `inbound` section, `<base />` before your policy means global+product inbound runs first, then yours. `<base />` after means yours runs first. **Remove `<base />` and you disconnect from the parent scope entirely** — occasionally what you want for one weird operation, almost never otherwise.

```xml
<!-- OPERATION scope. Global rate limiting runs first, then this operation's stricter cap. -->
<policies>
    <inbound>
        <base />                                  <!-- global -> product -> API inbound -->
        <rate-limit-by-key calls="5" renewal-period="60"
                           counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)" />
    </inbound>
    <backend><base /></backend>
    <outbound><base /></outbound>
    <on-error><base /></on-error>
</policies>
```

Three facts that make this answer land:
- On **outbound**, the natural reading flips: outbound runs from the narrowest scope outward, so `<base />` placement still controls order but "parent" now means the policies that wrap yours on the way out.
- A **globally scoped** policy has no parent, so `<base />` there does nothing.
- The **backend** section can contain only **one** policy element. Globally that's `forward-request`; at other scopes it defaults to `<base />`.
- The portal's **"Calculate effective policy"** button renders the fully flattened document for a scope. Mention it — it's what you actually use to debug this.

**If they push back — "Where do you put what, in a real platform?"** — Global: correlation ID generation, CORS, security headers, global IP deny list, App Insights sampling override. Product: quota and rate limit per audience, plus the auth scheme for that audience. API: backend selection, base-path rewrite, common validation. Operation: only genuinely operation-specific things — a tighter rate limit on an expensive search, a mock response on an unimplemented endpoint. Pushing policy up is how you stop copy-paste sprawl.

---

### Q16. Policy expressions — what's the syntax and what's in `context`?
`[MEDIUM]`

**Answer:** Policy expressions are **C#**, in two forms: `@(single expression)` and `@{ multi-statement block; return value; }`. They can be used for most attribute values and text values, and they get an implicit `context` object plus a subset of the .NET BCL (`System`, `System.Linq`, `System.Text.RegularExpressions`, `Newtonsoft.Json`, `System.Security.Cryptography`, etc.).

```xml
<!-- Single-expression form -->
<set-header name="X-Request-Id" exists-action="skip">
    <value>@(context.RequestId.ToString())</value>
</set-header>

<!-- Multi-statement form: derive a throttling key that degrades gracefully -->
<rate-limit-by-key calls="1000" renewal-period="60"
    counter-key="@{
        if (context.Subscription != null) { return context.Subscription.Id; }
        var jwt = context.Request.Headers.GetValueOrDefault("Authorization","")
                    .Split(' ').LastOrDefault()?.AsJwt();
        return jwt?.Subject ?? context.Request.IpAddress;
    }" />
```

The `context` members you should be able to name without thinking:

| Member | Use |
|---|---|
| `context.Request.Headers`, `.Body`, `.Url`, `.Method`, `.IpAddress`, `.MatchedParameters` | inbound inspection |
| `context.Response.StatusCode`, `.Headers`, `.Body` | outbound reshaping |
| `context.Subscription.Id`, `.Key`, `.Name` | throttling/metering key |
| `context.Product.Id`, `.Name` | per-audience branching |
| `context.User.Id`, `.Email`, `.Groups` | dev-portal identity |
| `context.Api.Id`, `.Name`, `.Version`, `.Revision` | logging dimensions |
| `context.Operation.Id`, `.Method`, `.UrlTemplate` | operation-level logic |
| `context.Variables["name"]` | pass state between policies/sections |
| `context.RequestId`, `context.Elapsed`, `context.Deployment.Region` | tracing |
| `context.LastError.Source/.Reason/.Message` | on-error only |
| `.AsJwt()`, `.AsBool()`, `.AsJObject()`, `.GetValueOrDefault()` | helper extensions |

**If they push back — "How do you read the body without breaking the request?"** — `context.Request.Body.As<JObject>(preserveContent: true)`. Without `preserveContent: true` the body stream is consumed and the backend gets nothing. That's a real production bug and a great thing to volunteer.

---

### Q17. Show me `validate-jwt` against Entra ID.
`[HARD]` `[VERBATIM: "How do you integrate APIM with Azure AD?" / "How do you secure APIs using OAuth 2.0?"]`

**Answer:** `validate-jwt` in the inbound section, pointing at the tenant's OIDC discovery document, asserting the audience (your API's application ID URI or client ID) and any required claims — typically `roles` or `scp`. APIM downloads and caches the JWKS from the OIDC metadata endpoint, so no key material lives in the policy.

```xml
<policies>
    <inbound>
        <base />
        <validate-jwt header-name="Authorization"
                      require-scheme="Bearer"
                      failed-validation-httpcode="401"
                      failed-validation-error-message="Unauthorized. Access token is missing or invalid."
                      require-expiration-time="true"
                      require-signed-tokens="true"
                      clock-skew="30"
                      output-token-variable-name="jwt">
            <openid-config url="https://login.microsoftonline.com/{{tenant-id}}/v2.0/.well-known/openid-configuration" />
            <audiences>
                <audience>api://contoso-orders</audience>
            </audiences>
            <issuers>
                <issuer>https://login.microsoftonline.com/{{tenant-id}}/v2.0</issuer>
            </issuers>
            <required-claims>
                <claim name="roles" match="any">
                    <value>Orders.Read</value>
                    <value>Orders.ReadWrite</value>
                </claim>
            </required-claims>
        </validate-jwt>

        <!-- Fine-grained authZ: writes require the stronger role -->
        <choose>
            <when condition="@(context.Request.Method != "GET" &amp;&amp; !((Jwt)context.Variables["jwt"]).Claims.GetValueOrDefault("roles","").Contains("Orders.ReadWrite"))">
                <return-response>
                    <set-status code="403" reason="Forbidden" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/json</value>
                    </set-header>
                    <set-body>{"error":"insufficient_scope","required":"Orders.ReadWrite"}</set-body>
                </return-response>
            </when>
        </choose>
    </inbound>
    <backend><base /></backend>
    <outbound><base /></outbound>
    <on-error><base /></on-error>
</policies>
```

**Defaults worth quoting:** `failed-validation-httpcode` defaults to **401**; `require-expiration-time` and `require-signed-tokens` default to **true**; `clock-skew` defaults to **0 seconds** — set it to 30–60 s or you will get intermittent failures from clock drift.

**Caching behaviour to name:** APIM pulls the OIDC configuration including the JWKS **every 1 hour** and caches it. If a token references a `kid` that's missing from the cached set, or the fetch fails, APIM re-pulls **at most once every 5 minutes**. That's the answer to "what happens when the IdP rotates signing keys" — you get a short window of failures, bounded by 5 minutes, which is why key rollover should overlap.

**Algorithms:** asymmetric **PS256, RS256, RS512, ES256**; symmetric HMAC keys must be supplied inline Base64-encoded.

**If they push back — "Why not `validate-azure-ad-token`?"** — Because it's the purpose-built shortcut: for Entra tokens it takes a tenant ID and client application IDs directly and validates issuer for you, so it's less to get wrong. I use `validate-azure-ad-token` when the issuer is definitely Entra, and `validate-jwt` when I need a non-Microsoft IdP, decryption keys, or explicit `issuer-signing-keys` for a partner. See [Auth & Security](06-auth-and-security.md) for the flows themselves.

---

### Q18. Show me rate limiting and quota, and explain how accurate it really is.
`[HARD]` `[VERBATIM: "Explain how rate limiting works in APIM."]`

**Answer:** Two policy families. **`rate-limit` / `rate-limit-by-key`** is a short-window burst control that returns **429** — think "10 calls per 60 seconds". **`quota` / `quota-by-key`** is a long-window volume cap — "1,000,000 calls per month" — and returns **403**. The `-by-key` variants let you choose the counter key: subscription ID, JWT subject, a tenant header, IP. The plain variants are product-scoped and key off the subscription automatically.

```xml
<policies>
    <inbound>
        <base />

        <!-- Burst control: per-subscription, falling back to caller IP for anonymous APIs.
             renewal-period is a sliding window in SECONDS and caps at 300. -->
        <rate-limit-by-key calls="100"
                           renewal-period="60"
                           counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)"
                           retry-after-header-name="Retry-After"
                           remaining-calls-header-name="X-RateLimit-Remaining"
                           total-calls-header-name="X-RateLimit-Limit" />

        <!-- Volume cap: only count successful, non-cached calls toward the monthly quota -->
        <quota-by-key calls="1000000"
                      renewal-period="2592000"
                      counter-key="@(context.Subscription.Id)"
                      increment-condition="@(context.Response.StatusCode >= 200 &amp;&amp; context.Response.StatusCode &lt; 300)" />
    </inbound>
    <backend><base /></backend>
    <outbound><base /></outbound>
    <on-error><base /></on-error>
</policies>
```

**Four things that make this a senior answer:**
1. Microsoft's own caveat: *"Because of the distributed nature of throttling architecture, rate limiting is never completely accurate."* Say it before they ask.
2. Counters are tracked **independently per gateway instance**, including per region in a multi-region deployment — they are **not** aggregated instance-wide. So a 100/min limit with 4 units can pass materially more than 100. If you need exact, you need an external counter (Redis) or accept the fuzziness.
3. **v2 tiers use a token-bucket algorithm; classic tiers use a sliding window.** Consequence: in v2, if you use the same `counter-key` at two scopes with different limits, behaviour is unpredictable — keep limits identical for identical keys.
4. `renewal-period` on `rate-limit-by-key` maxes out at **300 seconds**. Anything longer is a quota, not a rate limit.
5. If `increment-condition` / `increment-count` use expressions, evaluation is **deferred to the end of the outbound pipeline** — so the 429 arrives one call later than you'd naively expect.

**If they push back — the EY scenario: "Three consumers — internal mobile app, a third-party partner, and a public web app — different security and throttling. How do you structure policies without duplicating code?"** — Three **Products** over the same APIs. Product policy carries the differences: internal gets `validate-jwt` on the corporate tenant and a generous `rate-limit-by-key` on user OID; partner gets mTLS plus `ip-filter` plus a hard `quota-by-key`; public gets subscription key plus an aggressive per-IP rate limit and `cache-lookup`. The **API-scope** policy holds everything common — backend selection, rewriting, correlation ID, error normalisation — and each Product policy ends with `<base />` so it inherits global. Shared blocks that genuinely repeat go into **policy fragments** and are pulled in with `<include-fragment fragment-id="..."/>`. Zero duplication, three trust models.

---

### Q19. Show me caching in APIM.
`[MEDIUM]` `[VERBATIM: "How would you implement caching for an API endpoint? Outline the steps."]`

**Answer:** `cache-lookup` in **inbound**, `cache-store` in **outbound**, and they must be paired. Lookup varies the cache key by headers and query parameters you nominate; store sets the TTL. APIM performs cache lookup for **GET requests only**.

```xml
<policies>
    <inbound>
        <base />
        <cache-lookup vary-by-developer="false"
                      vary-by-developer-groups="false"
                      caching-type="prefer-external"
                      downstream-caching-type="none"
                      must-revalidate="true"
                      allow-private-response-caching="false">
            <vary-by-header>Accept</vary-by-header>
            <vary-by-header>Accept-Charset</vary-by-header>
            <vary-by-query-parameter>region</vary-by-query-parameter>
            <vary-by-query-parameter>page</vary-by-query-parameter>
        </cache-lookup>

        <!-- Microsoft's own recommendation: rate-limit immediately AFTER cache-lookup,
             so a cold/unavailable cache can't stampede the backend. -->
        <rate-limit calls="200" renewal-period="60" />
    </inbound>
    <backend><base /></backend>
    <outbound>
        <!-- Honour the backend's Cache-Control max-age, default 300s if absent -->
        <cache-store duration="@{
            var header = context.Response.Headers.GetValueOrDefault("Cache-Control","");
            var maxAge = Regex.Match(header, @"max-age=(?&lt;maxAge&gt;\d+)").Groups["maxAge"]?.Value;
            return (!string.IsNullOrEmpty(maxAge)) ? int.Parse(maxAge) : 300;
        }" />
        <base />
    </outbound>
    <on-error><base /></on-error>
</policies>
```

Numbers and constraints: **cached response size limit is 2 MiB**; built-in cache size is per tier (10 MB Developer → 5 GB Premium) and is **volatile and shared by all units in a region**; `caching-type` defaults to `prefer-external`; `cache-lookup` can appear **once per section** and is **not supported inside a policy fragment**.

**If they push back — "Built-in vs external cache?"** — Built-in is free, volatile, per-region and shared across units — fine for read-heavy reference data where a cold cache is only a latency blip. External (Azure Managed Redis or any Redis-compatible cache, `caching-type="external"`) is what you use when you need cache to survive scaling and restarts, need bigger capacity than the tier gives, need it shared across regions, or need it in the Consumption tier which has no built-in cache. Also: `cache-store-value`/`cache-lookup-value` let you cache arbitrary values (like a fetched partner token) rather than whole responses.

---

### Q20. SOAP-to-REST: show me the transformation policies.
`[HARD]` `[the JD literally says "REST, SOAP, GraphQL" — and this is where you differentiate]`

**Answer:** APIM imports a WSDL two ways: **SOAP passthrough** (APIM proxies SOAP unchanged, you still get policy, throttling and analytics) or **SOAP-to-REST** (APIM generates REST operations and you own the mapping). For the second, the policy chain is: build the SOAP envelope in inbound with `set-body` and a Liquid template, set `SOAPAction`, forward, then `xml-to-json` on the way out and reshape.

```xml
<policies>
    <inbound>
        <base />
        <!-- REST in: GET /customers/{id}  ->  SOAP out -->
        <set-variable name="customerId" value="@(context.Request.MatchedParameters["id"])" />
        <set-method>POST</set-method>
        <set-header name="Content-Type" exists-action="override">
            <value>text/xml; charset=utf-8</value>
        </set-header>
        <set-header name="SOAPAction" exists-action="override">
            <value>"http://contoso.com/crm/GetCustomer"</value>
        </set-header>
        <set-body>@{
            return $@"<?xml version=""1.0"" encoding=""utf-8""?>
<soap:Envelope xmlns:soap=""http://schemas.xmlsoap.org/soap/envelope/""
               xmlns:crm=""http://contoso.com/crm"">
  <soap:Body>
    <crm:GetCustomer>
      <crm:CustomerId>{context.Variables.GetValueOrDefault<string>("customerId")}</crm:CustomerId>
    </crm:GetCustomer>
  </soap:Body>
</soap:Envelope>";
        }</set-body>
        <rewrite-uri template="/CrmService.asmx" />
        <set-backend-service backend-id="legacy-crm-soap" />
    </inbound>

    <backend>
        <forward-request timeout="30" buffer-request-body="true" />
    </backend>

    <outbound>
        <base />
        <!-- SOAP fault -> proper HTTP error, before we transform -->
        <choose>
            <when condition="@(context.Response.Body.As<string>(preserveContent: true).Contains("<soap:Fault>"))">
                <return-response>
                    <set-status code="502" reason="Bad Gateway" />
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/json</value>
                    </set-header>
                    <set-body>{"error":"upstream_soap_fault","correlationId":"@(context.RequestId)"}</set-body>
                </return-response>
            </when>
        </choose>

        <xml-to-json kind="direct" apply="always" consider-accept-header="false" />

        <!-- Unwrap the SOAP envelope so the REST consumer sees a clean object -->
        <set-body>@{
            var body = context.Response.Body.As<JObject>();
            var customer = body.SelectToken("$..GetCustomerResult");
            return customer?.ToString() ?? "{}";
        }</set-body>
    </outbound>

    <on-error>
        <base />
        <set-status code="500" reason="Internal Server Error" />
        <set-header name="Content-Type" exists-action="override">
            <value>application/json</value>
        </set-header>
        <set-body>@{
            return new JObject(
                new JProperty("error", "integration_error"),
                new JProperty("source", context.LastError.Source),
                new JProperty("correlationId", context.RequestId.ToString())
            ).ToString();
        }</set-body>
    </on-error>
</policies>
```

`xml-to-json` has two `kind` values: **`direct`** (a faithful XML→JSON mapping, verbose, attributes prefixed with `@`) and **`javascript-friendly`** (drops the ceremony, easier to consume). `json-to-xml` does the reverse for REST-in/SOAP-out.

**If they push back — "Why not just let the client call SOAP?"** — Sometimes you should: passthrough plus policy gets you throttling, auth and analytics with zero mapping risk. I convert when the consumers are mobile/JS clients that can't reasonably do SOAP, when I want an OpenAPI contract for the developer portal, or when I'm strangling the legacy service — the REST façade is an **Anti-Corruption Layer** and a **Strangler Fig** in one, so I can swap the backend later without touching consumers.

---

### Q21. Show me `send-request` for auth enrichment / gateway aggregation.
`[HARD]`

**Answer:** `send-request` makes an out-of-band HTTP call from inside a policy and stores the result in a context variable. Two classic uses: **enrichment** (fetch a partner token, or look up entitlement, before forwarding) and **gateway aggregation** (call two backends and merge). Always cache the enrichment result — otherwise you've doubled every request.

```xml
<policies>
    <inbound>
        <base />

        <!-- 1. Try cache for a partner OAuth token -->
        <cache-lookup-value key="partner-token" variable-name="partnerToken" />

        <!-- 2. On miss, fetch one with client_credentials and cache it -->
        <choose>
            <when condition="@(!context.Variables.ContainsKey("partnerToken"))">
                <send-request mode="new" response-variable-name="tokenResponse"
                              timeout="10" ignore-error="false">
                    <set-url>https://partner.example.com/oauth2/token</set-url>
                    <set-method>POST</set-method>
                    <set-header name="Content-Type" exists-action="override">
                        <value>application/x-www-form-urlencoded</value>
                    </set-header>
                    <set-body>@($"grant_type=client_credentials&client_id={{partner-client-id}}&client_secret={{partner-client-secret}}&scope=orders.write")</set-body>
                </send-request>

                <set-variable name="partnerToken"
                              value="@(((IResponse)context.Variables["tokenResponse"]).Body.As<JObject>()["access_token"].ToString())" />

                <!-- Cache 55 minutes for a 60-minute token: always expire early -->
                <cache-store-value key="partner-token"
                                   value="@((string)context.Variables["partnerToken"])"
                                   duration="3300" />
            </when>
        </choose>

        <!-- 3. Attach it, and make sure the caller's own token never leaks upstream -->
        <set-header name="Authorization" exists-action="override">
            <value>@("Bearer " + (string)context.Variables["partnerToken"])</value>
        </set-header>
        <set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
    </inbound>
    <backend><base /></backend>
    <outbound><base /></outbound>
    <on-error><base /></on-error>
</policies>
```

**If they push back — "Isn't that a hidden latency cost?"** — Yes, and it's why `send-request` needs three guards: a short explicit `timeout`, a decision on `ignore-error` (do you fail open or closed?), and caching. Without caching you have added a full round-trip to every call. I also watch the **concurrent backend connections per HTTP authority** limit — **2,048 per unit** (1,024 in Developer) — because a chatty `send-request` target counts against it.

---

### Q22. Show me the rest of the policy toolkit — the ones that come up.
`[MEDIUM]`

**Answer:** Here's the working set, as one document, with real values.

```xml
<policies>
    <inbound>
        <base />

        <!-- CORS: preflight handled by the gateway, backend never sees OPTIONS -->
        <cors allow-credentials="true" terminate-unmatched-request="true">
            <allowed-origins>
                <origin>https://portal.contoso.com</origin>
            </allowed-origins>
            <allowed-methods preflight-result-max-age="3600">
                <method>GET</method><method>POST</method><method>PATCH</method><method>DELETE</method>
            </allowed-methods>
            <allowed-headers>
                <header>Authorization</header><header>Content-Type</header><header>X-Correlation-Id</header>
            </allowed-headers>
            <expose-headers>
                <header>X-Correlation-Id</header><header>X-RateLimit-Remaining</header>
            </expose-headers>
        </cors>

        <!-- IP allow-list for a partner-only API -->
        <ip-filter action="allow">
            <address-range from="203.0.113.0" to="203.0.113.255" />
            <address>198.51.100.24</address>
        </ip-filter>

        <!-- Correlation ID: reuse the caller's if present, else mint one -->
        <set-variable name="correlationId"
            value="@(context.Request.Headers.GetValueOrDefault("X-Correlation-Id", context.RequestId.ToString()))" />
        <set-header name="X-Correlation-Id" exists-action="override">
            <value>@((string)context.Variables["correlationId"])</value>
        </set-header>

        <!-- Schema validation against the imported OpenAPI (body cap: 100 KiB) -->
        <validate-content unspecified-content-type-action="prevent"
                          max-size="102400"
                          size-exceeded-action="prevent"
                          errors-variable-name="validationErrors">
            <content type="application/json" validate-as="json" action="prevent" />
        </validate-content>

        <!-- Route by tenant header to different backends -->
        <choose>
            <when condition="@(context.Request.Headers.GetValueOrDefault("X-Tenant","") == "emea")">
                <set-backend-service backend-id="orders-emea" />
            </when>
            <when condition="@(context.Request.Headers.GetValueOrDefault("X-Tenant","") == "apac")">
                <set-backend-service backend-id="orders-apac" />
            </when>
            <otherwise>
                <set-backend-service backend-id="orders-default" />
            </otherwise>
        </choose>

        <!-- Path rewrite: public /orders/{id} -> internal /api/v3/order?orderId={id} -->
        <rewrite-uri template="/api/v3/order?orderId={id}" copy-unmatched-params="false" />

        <!-- Mock an endpoint that isn't built yet (remove before go-live!) -->
        <!-- <mock-response status-code="200" content-type="application/json" /> -->
    </inbound>

    <backend>
        <!-- Explicit timeout + retry on transient failures. forward-request is the ONLY
             element allowed in this section, so the retry wraps it. -->
        <retry condition="@(context.Response.StatusCode == 429 || context.Response.StatusCode >= 500)"
               count="3" interval="2" max-interval="10" delta="2"
               first-fast-retry="false">
            <forward-request timeout="30" buffer-request-body="false" />
        </retry>
    </backend>

    <outbound>
        <base />
        <!-- Never leak backend internals -->
        <set-header name="X-Powered-By" exists-action="delete" />
        <set-header name="X-AspNet-Version" exists-action="delete" />
        <set-header name="Server" exists-action="delete" />
        <set-header name="X-Correlation-Id" exists-action="override">
            <value>@((string)context.Variables["correlationId"])</value>
        </set-header>
        <!-- Deprecation signalling for a version being retired -->
        <set-header name="Deprecation" exists-action="override">
            <value>true</value>
        </set-header>
        <set-header name="Sunset" exists-action="override">
            <value>Sat, 31 Jan 2027 23:59:59 GMT</value>
        </set-header>
    </outbound>

    <on-error>
        <base />
        <set-header name="X-Correlation-Id" exists-action="override">
            <value>@((string)context.Variables["correlationId"])</value>
        </set-header>
    </on-error>
</policies>
```

**If they push back — "What's `first-fast-retry` on `retry`?"** — When `true`, the first retry fires immediately with no wait, then the interval/exponential schedule applies. Useful when the dominant failure mode is a single dropped connection rather than backend overload. When the backend is overloaded, leave it `false` so you don't add to the stampede.

---

### Q23. `rewrite-uri` vs `set-backend-service` — what's the difference?
`[EASY→MEDIUM]` `[a common confusion, so a good clarity signal]`

**Answer:** `set-backend-service` changes **which host** the request goes to; `rewrite-uri` changes **the path and query** sent to that host. You almost always need both when fronting a legacy service, because the public contract you publish rarely matches the internal route.

```xml
<!-- Public:  GET https://api.contoso.com/orders/v1/12345?expand=lines
     Internal: GET https://legacy.internal/OrderService/Fetch?id=12345&detail=full -->
<set-backend-service base-url="https://legacy.internal/OrderService" />
<rewrite-uri template="/Fetch?id={id}&amp;detail=full" copy-unmatched-params="false" />
```

`copy-unmatched-params="false"` is the detail to mention: by default APIM appends any query parameters that weren't consumed by the template, which can silently forward a caller-supplied `?debug=true` to your backend.

**If they push back — "What about `set-backend-service` with `backend-id` vs `base-url`?"** — `backend-id` points at a backend entity, so you inherit its credentials, TLS settings, circuit breaker and pool. `base-url` is a raw string. Use `backend-id` in anything production.

---

### Q24. How do you enforce a timeout, and what's the difference between the gateway timeout and the backend timeout?
`[MEDIUM]`

**Answer:** `<forward-request timeout="30" />` in the **backend** section is the per-call backend timeout in seconds — that's the one you control. There's also a total request duration ceiling from the tier: **unlimited in classic and v2 tiers, but 30 seconds in Consumption**. So an API with a genuinely slow backend cannot live in the Consumption tier, full stop.

`buffer-request-body="true"` makes APIM read the whole request into memory before forwarding — needed if you inspect or retry the body, and it costs you against the buffered payload limit (**500 MiB classic; 2 MiB in v2 and Consumption**).

**If they push back — "Backend takes 4 minutes. Now what?"** — Don't hold the HTTP connection. Switch to **Asynchronous Request-Reply**: APIM (or a Function) accepts the request, drops it on a Service Bus queue, returns `202 Accepted` with a `Location` header pointing at a status endpoint, and the client polls. Durable Functions gives you this pattern out of the box, including the status URL. That's also the answer to the Functions 230-second load-balancer ceiling in §6.

---

### Q25. Mock responses and policy fragments — the two things that make a platform maintainable.
`[MEDIUM]`

**Answer:** `mock-response` makes APIM return a fabricated response derived from the OpenAPI examples, without calling the backend — so frontend teams can start on day one and you can test policy in isolation. **Policy fragments** are reusable XML blocks stored once and included with `<include-fragment fragment-id="..."/>` — the answer to "we have the same 40 lines of error handling in 30 APIs".

```xml
<!-- Fragment: standard-error-envelope  (defined once at instance level) -->
<fragment>
    <set-header name="Content-Type" exists-action="override">
        <value>application/problem+json</value>
    </set-header>
    <set-body>@{
        return new JObject(
            new JProperty("type",   "https://contoso.com/errors/integration"),
            new JProperty("title",  "Upstream integration error"),
            new JProperty("status", context.Response?.StatusCode ?? 500),
            new JProperty("correlationId", context.RequestId.ToString())
        ).ToString();
    }</set-body>
</fragment>
```

```xml
<!-- Used in every API's on-error -->
<on-error>
    <base />
    <include-fragment fragment-id="standard-error-envelope" />
</on-error>
```

**If they push back — "Any gotcha with fragments?"** — `cache-lookup` is **not supported inside a policy fragment**, and fragments can't be nested. Also, fragments are resolved at deploy/runtime, so a broken fragment breaks every API that includes it — treat fragment changes as a platform-wide change with its own approval.

---

### Q26. GraphQL and WebSocket in APIM — do they work?
`[MEDIUM]` `[the JD lists GraphQL]`

**Answer:** Yes to both. APIM supports **passthrough GraphQL** (front an existing GraphQL server, get schema-aware validation and policy) and **synthetic GraphQL** (define a schema in APIM and resolve fields from REST/SOAP backends with resolver policies) — that second one is genuinely useful for stitching a legacy estate. The GraphQL-specific policy is `validate-graphql-request`, which enforces max depth and size and can allow/deny specific operations, which is your defence against a malicious deeply-nested query. WebSocket APIs are also supported, with a limit of **5,000 active WebSocket connections per unit**.

```xml
<inbound>
    <base />
    <validate-graphql-request error-variable-name="graphqlErrors"
                              max-size="10240"
                              max-depth="6">
        <authorize>
            <rule path="/Mutation/deleteOrder" action="reject" />
        </authorize>
    </validate-graphql-request>
</inbound>
```

**If they push back — "REST vs GraphQL for an enterprise integration layer?"** — GraphQL wins for consumer-facing aggregation where clients have wildly different data needs (mobile vs web) and you want to kill N+1 round trips. REST wins for system-to-system, because it caches at the HTTP layer, is trivially throttled and logged per-operation, and every middleware in the estate already understands it. In an EY-style integration layer I'd expose REST to systems and consider GraphQL only at the experience/BFF tier. Depth limits are non-negotiable either way. More in [API Design](01-api-design-rest-soap-graphql-openapi.md).

---

## 4. APIM: Hybrid, Observability, Competitors

### Q27. What is the self-hosted gateway and when do you use it?
`[HARD]` `[VERBATIM: "What is the difference between self-hosted and Azure-hosted APIM gateways?" / "What is the best way to expose on-prem APIs securely using APIM?"]`

**Answer:** The self-hosted gateway is a **containerised build of the APIM data plane** that you run wherever your APIs live — in your datacentre, on another cloud, in a Kubernetes cluster — while it stays federated to a single APIM instance in Azure for configuration, policy and telemetry. You get one management plane and one developer portal across a hybrid estate, and API traffic goes **directly** to the local backend instead of hairpinning through Azure. It's available in **Developer and Premium tiers only** (Developer is limited to a single node).

**The connectivity facts that prove you've run one:**
- Linux Docker image from the Microsoft Artifact Registry; deploy to Docker, Kubernetes (there's a Helm chart), or as a cluster extension on Azure Arc-enabled Kubernetes.
- Needs **outbound TCP 443 only** — no inbound firewall holes.
- **Heartbeat every minute**; **polls for configuration updates every 10 seconds**.
- Config endpoint FQDN: `<apim-name>.configuration.azure-api.net`.
- **Fails static.** Lose connectivity to Azure and running gateways keep serving from an in-memory copy of the config. With **local configuration backup** enabled (config persisted to a volume), even a *restarted* gateway can start from the backup. Without it, a stopped gateway cannot start.
- TLS 1.2 by default. **No TLS session resumption** and **no client-certificate renegotiation** — for mTLS, clients must present the cert in the initial handshake, so enable "Negotiate Client Certificate" on the custom hostname.
- Entity limit: **5 self-hosted gateways in Developer, 100 in Premium**.

```bash
# Deploy the self-hosted gateway to AKS with Helm, pinned to a version tag
helm repo add azure-apim-gateway https://azure.github.io/api-management-self-hosted-gateway/helm-charts/
helm repo update

kubectl create namespace apim-gw

helm install contoso-gw azure-apim-gateway/azure-api-management-gateway \
  --namespace apim-gw \
  --set gateway.endpoint="contoso-apim.configuration.azure-api.net" \
  --set gateway.authKey="GatewayKey contoso-gw&20270101..." \
  --set gateway.configuration.backup.enabled=true \
  --set replicaCount=3 \
  --set service.type=ClusterIP

kubectl -n apim-gw get pods -w
```

**If they push back — "How does it authenticate to Azure?"** — Either a **gateway access token** (the `GatewayKey ...` string, which expires and must be rotated — a real operational burden) or **Microsoft Entra ID authentication**, which is the modern option and what I'd choose because it removes the rotating shared secret. In a Kubernetes deployment the key goes in a Secret, never in the Helm values file in Git — use a sealed secret or the CSI Key Vault driver. See [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md).

---

### Q28. How do you get observability across an APIM + Logic Apps + Functions chain?
`[HARD]` `[EY scenario: "Give me a real scenario where observability caught a failure before the business noticed. Write me a KQL query for failed Logic App runs in the last 24 hours."]`

**Answer:** One Application Insights resource for the whole integration, one correlation ID that survives every hop, and alerts on business-meaningful signals rather than CPU. APIM gets an Application Insights **logger** and a **diagnostic** with sampling; Logic Apps Standard writes to the same App Insights and emits business identifiers via **`trackedProperties`**; Functions inherit App Insights natively. Then everything is queryable in one workspace and one `operation_Id` stitches the trace.

**The KQL they asked for:**

```kusto
// Failed Logic App runs in the last 24 hours, worst workflows first
AzureDiagnostics
| where TimeGenerated > ago(24h)
| where ResourceProvider == "MICROSOFT.LOGIC"
| where Category == "WorkflowRuntime"
| where OperationName == "Microsoft.Logic/workflows/workflowRunCompleted"
| where status_s == "Failed"
| project TimeGenerated,
          workflow  = resource_workflowName_s,
          runId     = resource_runId_s,
          trigger   = resource_triggerName_s,
          errorCode = code_s,
          errorMsg  = error_message_s,
          correlationId = tostring(trackedProperties_correlationId_s)
| summarize failures = count(),
            firstSeen = min(TimeGenerated),
            lastSeen  = max(TimeGenerated),
            sampleRun = any(runId),
            sampleError = any(errorMsg)
        by workflow, errorCode
| order by failures desc
```

```kusto
// APIM: p95 latency and 5xx rate per API/operation, 1-hour bins
ApiManagementGatewayLogs
| where TimeGenerated > ago(24h)
| summarize calls        = count(),
            errors5xx    = countif(ResponseCode >= 500),
            p95LatencyMs = percentile(TotalTime, 95),
            p99LatencyMs = percentile(TotalTime, 99)
        by bin(TimeGenerated, 1h), ApiId, OperationId
| extend errorRatePct = round(100.0 * errors5xx / calls, 2)
| where errorRatePct > 1.0 or p95LatencyMs > 2000
| order by TimeGenerated desc, errorRatePct desc
```

```kusto
// End-to-end trace across APIM -> Function -> Logic App for one correlation ID
let cid = "0HN7A2K3L9M4P";
union isfuzzy=true requests, dependencies, traces, exceptions
| where timestamp > ago(6h)
| where customDimensions has cid or operation_Id == cid
| project timestamp, itemType, name, resultCode, duration, cloud_RoleName, operation_Id
| order by timestamp asc
```

**The APIM side of the wiring:**

```xml
<inbound>
    <base />
    <!-- Surface business dimensions into App Insights telemetry -->
    <trace source="orders-api" severity="information">
        <message>@($"Order request received for tenant {context.Request.Headers.GetValueOrDefault("X-Tenant","unknown")}")</message>
        <metadata name="correlationId" value="@((string)context.Variables["correlationId"])" />
        <metadata name="tenant" value="@(context.Request.Headers.GetValueOrDefault("X-Tenant","unknown"))" />
        <metadata name="subscriptionId" value="@(context.Subscription?.Id ?? "anonymous")" />
    </trace>
</inbound>
```

**Sampling** is the number to know: APIM's App Insights diagnostic lets you set a sampling percentage — 100% in dev, typically **1–5% in production** — and separately how many payload bytes to log, capped at **8,192 bytes** for requests and responses. Sampling is where teams accidentally lose the exact trace they needed, so my rule is: sample the happy path aggressively, but log **100% of 4xx/5xx** by using a second diagnostic setting or an `on-error` trace.

**If they push back — "Give me the real incident story"** — Frame it as: an alert on Logic App `workflowRunCompleted` failures crossing 5 in 15 minutes fired at 02:10; the tracked `correlationId` led to a Service Bus DLQ where messages were dead-lettering with `MaxDeliveryCountExceeded` because a partner's certificate had expired; we paused the consumer, fixed the cert, and resubmitted from the DLQ before the 09:00 business window. The business never saw it. That is the shape of answer EY wants — detection, diagnosis, containment, recovery, and a measurable outcome.

---

### Q29. APIM vs Apigee vs Kong vs AWS API Gateway.
`[MEDIUM]` `[the JD lists "APIM, Apigee, Kong" — expect a comparison]`

**Answer:** They all do gateway + lifecycle; they differ in deployment model, extensibility language, and where the control plane lives.

| | **Azure APIM** | **Apigee (Google)** | **Kong** | **AWS API Gateway** |
|---|---|---|---|---|
| Model | Managed PaaS; self-hosted gateway container for hybrid | Managed (Apigee X) or hybrid | OSS + Kong Konnect SaaS; you run the data plane | Fully managed, AWS-only |
| Policy/extension language | **Declarative XML + C# expressions** | JavaScript/Java callouts + XML policies | **Lua plugins** (+ Go/JS/Python PDK) | Mapping templates (VTL) + Lambda authorizers |
| Deploy anywhere | Yes (self-hosted GW, Arc, K8s) | Yes (Apigee hybrid) | **Yes — strongest here** | No |
| Developer portal | Built in, customisable | Built in, strong | Konnect portal / Dev Portal | Minimal |
| Identity integration | **Entra ID native, managed identity** | Google Cloud IAM, OAuth | Plugin-based (OIDC plugin) | IAM, Cognito, Lambda authorizer |
| Pricing shape | Per unit/hour by tier (+ Consumption per-call) | Per environment/throughput | OSS free; Konnect per service | Per million requests |
| Sweet spot | **Microsoft estate, hybrid, Entra everywhere** | API-product monetisation, analytics depth | Kubernetes-native, multi-cloud, plugin freedom | AWS-native serverless |
| Weak spot | Slow ops (30-min scale, 45-min classic deploy); XML | Cost; complexity | You own the ops; portal/analytics thinner | AWS lock-in; VTL is painful |

The honest positioning line: *"For a Microsoft-first client, APIM is not really a choice — Entra ID, Key Vault, App Insights, Bicep and Private Link all line up with zero glue. I'd argue for Kong when the client is Kubernetes-native and multi-cloud, and for Apigee when API monetisation and product analytics are the actual business case."*

**If they push back — "AWS shop wants to know why APIM at all"** — Then I'd not fight it; API Gateway plus Lambda authorizers is coherent. The one thing APIM does that AWS API Gateway doesn't is run the **same gateway** on-prem and in another cloud under one control plane. If the client's estate has a datacentre in it, that's decisive. See the mapping table in §9.

---

### Q30. What is APIM's AI gateway, and why does it matter for this role?
`[HARD]` `[YOUR DIFFERENTIATOR — the JD lists "AI Frameworks and Tooling" as good-to-have and EY asked cosine similarity / Transformers at Senior Consultant level]`

**Answer:** APIM now ships an **AI gateway**: a set of policies for governing LLM traffic, and the ability to expose managed REST APIs as **MCP servers** so agents can call them as tools. This is exactly the seam where "API and Integration Developer" meets EY's actual 2026 direction — EY and Microsoft announced a >$1bn five-year initiative in May 2026, and EY has already embedded a multi-agent framework into EY Canvas across 130,000 Assurance professionals and 160,000 audit engagements. Those agents call enterprise systems. Somebody has to govern that traffic. That's this role.

**The policy names to say out loud:**

| Policy | What it does |
|---|---|
| `llm-token-limit` | TPM limit or token quota per hour/day/week/month/year, keyed on any counter key; `estimate-prompt-tokens` pre-rejects oversized prompts; `remaining-tokens-variable-name` for headers |
| `llm-emit-token-metric` | Emits token metrics to Azure Monitor/App Insights with custom `<dimension>` elements — this is how you charge back per team |
| `llm-semantic-cache-store` / `llm-semantic-cache-lookup` | Vector-proximity caching of completions; requires Azure Managed Redis or another RediSearch-compatible external cache |
| `llm-content-safety` | Azure AI Content Safety moderation with category filtering (Hate, SelfHarm, Sexual, Violence) plus prompt-injection detection; now covers **MCP tool-call arguments and responses** |

```xml
<inbound>
    <base />
    <!-- Per-agent token budget, not per-request rate limit -->
    <llm-token-limit counter-key="@(context.Request.Headers.GetValueOrDefault("X-Agent-Id","anonymous"))"
                     tokens-per-minute="20000"
                     estimate-prompt-tokens="true"
                     remaining-tokens-header-name="X-Tokens-Remaining"
                     tokens-consumed-header-name="X-Tokens-Consumed" />

    <llm-emit-token-metric namespace="genai">
        <dimension name="AgentId"   value="@(context.Request.Headers.GetValueOrDefault("X-Agent-Id","anonymous"))" />
        <dimension name="ApiId"     value="@(context.Api.Id)" />
        <dimension name="ClientTeam" value="@(context.Subscription?.Name ?? "unknown")" />
    </llm-emit-token-metric>
</inbound>
```

**MCP specifics that show depth rather than hype:** APIM can expose any HTTP-compatible managed API as a remote MCP server — the endpoint form is `https://<apim-name>.azure-api.net/<api-name>-mcp/mcp`. Supported on Developer, Basic, Basic v2, Standard, Standard v2, Premium and Premium v2 — **not Consumption** — and on the self-hosted gateway. Limitations to state proactively: **tools only** (no MCP resources or prompts), **not supported in workspaces**, policies apply to *all* operations exposed as tools (no per-tool granularity yet), and global-scope policies evaluate **before** MCP-server-scope policies. Two operational gotchas: **do not touch `context.Response.Body` in MCP server policies** (it triggers buffering and breaks the streaming transport), and if global diagnostic logging is on, set "Number of payload bytes to log" for Frontend Response to **0** or MCP streaming fails.

**Transport:** say **Streamable HTTP** on `/mcp`. HTTP+SSE (`/sse` to establish, `/messages` for bidirectional) is **deprecated** as of protocol version 2024-11-05. Messaging is JSON-RPC 2.0. Saying "we'd use SSE" makes you sound a year behind.

**The line that lands:** *"An MCP tool is just an API operation with a schema and a governance problem. Everything I already do for a REST API — JWT validation, rate-limit-by-key, quota, IP filtering, correlation IDs, App Insights, circuit breaker on the backend, dead-letter on the async leg — applies unchanged. What changes is that the caller is non-deterministic, so idempotency and per-agent token quotas stop being nice-to-haves."*

**If they push back — "So what would you actually build for EY?"** — SAP/Workday/ServiceNow fronted by APIM, backed by Logic Apps Standard built-in connectors and Functions, Service Bus topics for fan-out, Event Grid for reactive triggers, on-prem reached via the on-premises data gateway — and then the *same* APIM instance exposing selected operations as an MCP server so EY.ai, Copilot Studio and Foundry agents call them under identical OAuth, quota, content-safety and App Insights governance. One narrative that covers the JD's core, its good-to-haves, and EY's real direction.

---

### Q31. What is Azure Front Door / Application Gateway doing in front of APIM, if anything?
`[MEDIUM]`

**Answer:** APIM is not a WAF and not a CDN. The standard enterprise topology is **Front Door (global routing + WAF + TLS offload + caching) → APIM (contract, auth, throttling, transformation) → backends**, or **Application Gateway (regional WAF) → internal APIM** when APIM is VNet-injected and must not have a public IP. Each layer has one job: Front Door does geo-routing and DDoS/OWASP filtering, App Gateway does regional L7 + WAF, APIM does API semantics.

**If they push back — "Isn't that three hops of latency?"** — It is, and I'd drop App Gateway if APIM is already internal-only behind Front Door with Private Link. The layer I never drop is the WAF, because APIM's `ip-filter` and `validate-content` are not an OWASP ruleset. If the client is cost-sensitive and the API is internal-only, Front Door goes and APIM sits behind Private Link with no public exposure at all.

---

### Q32. How would you integrate APIM with microservices on AKS?
`[HARD]` `[VERBATIM: "How would you integrate APIM in a microservices environment running on AKS?"]`

**Answer:** Two viable topologies. **APIM outside the cluster** (VNet-integrated or injected) calling AKS services through an internal ingress — simplest, one gateway, works with Standard v2 or Premium. Or **self-hosted gateway inside the cluster** as a Deployment, so north-south traffic terminates in-cluster and never leaves it — better latency and data-residency story, needs Developer or Premium tier.

Either way: APIM does **Gateway Routing** (path → service), **Gateway Offloading** (JWT validation, TLS, throttling done once at the edge instead of in every service), and **Gateway Aggregation** where a BFF-shaped endpoint is genuinely useful. Service-to-service concerns — mTLS, retries between pods, traffic splitting — belong to the service mesh (Istio add-on) or the client libraries, **not** to APIM. Mixing those two is the classic architecture smell.

```yaml
# The AKS side: internal-only ingress that only the APIM subnet can reach
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orders-ingress
  namespace: orders
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.20.1.0/24"   # APIM subnet
spec:
  ingressClassName: nginx
  rules:
  - host: orders.internal.contoso.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: orders-svc
            port:
              number: 8080
```

**If they push back — "How do the services know who the caller is?"** — APIM validates the JWT at the edge and forwards a trimmed, signed set of claims — or the original token if the services need it — plus the correlation ID. Services still verify (defence in depth), but they verify a token they can trust the shape of. What I never do is have each of 30 services independently talk to Entra ID for discovery documents; that's the offloading argument.

---
## 5. Azure Logic Apps

### Q33. Consumption vs Standard — the near-certain question.
`[HARD]` `[ASK IS ALMOST GUARANTEED]`

**Answer:** **Consumption** is the multitenant, pay-per-action-execution model: one logic app resource = exactly one workflow, running on shared compute across all Entra tenants, fully managed, easiest to start. **Standard** is the redesigned **single-tenant** runtime, hosted as an extension on the **Azure Functions runtime**, so one logic app resource holds **many** workflows that share compute — plus VNet integration and private endpoints, your own static outbound IPs, local development and debugging in VS Code, and built-in "service provider" connectors that run **in-process** instead of through shared managed API connections. For any enterprise integration platform I default to Standard.

| | Consumption (multitenant) | Standard (single-tenant) |
|---|---|---|
| Workflows per resource | **1** | many (stateful + stateless mixed) |
| Runtime | Multitenant Logic Apps | Single-tenant, on the **Azure Functions runtime** |
| Hosting targets | Azure only | Workflow Service Plan, **ASEv3 (Windows plans only)**, Hybrid on your own infra via an Azure Container Apps extension |
| Pricing | per action execution | hosting plan (+ Azure Storage transactions for stateful) |
| Connectors | managed API connections (shared) | **built-in/service-provider** in-process (Service Bus, Event Hubs, SQL Server, Blob, Cosmos DB, DB2, MQ, FTP, SFTP) **plus** managed |
| VNet / private endpoints | ✗ | ✔ native |
| Local dev + breakpoints | ✗ | ✔ VS Code (breakpoints on **actions only**, not triggers) |
| Liquid & XML transforms | needs an **integration account** | **no integration account needed** |
| Data residency | replicated to the paired region (GRS) | stays in the deployment region |
| Deployment | ARM template (app + infra together) | **zip artifact for app, ARM/Bicep for infra — separated** |
| Triggers per workflow | 1 in designer, up to 10 in JSON | exactly **1** |
| HTTP request timeout | **120 s** | **225 s** default |
| Workflow name length | 80 chars | 32 chars |

**If they push back — "Why is the Functions-runtime detail important?"** — Because it's why Standard inherits everything App Service gives you: deployment slots, VNet integration, scale rules, Key Vault references in app settings, App Insights, and a plain zip-deploy artifact your CI/CD already knows how to build. It's the difference between "we deploy an ARM template that contains our business logic" and "we build an artifact and promote it". That separation is exactly what an EY delivery pipeline needs.

---

### Q34. Stateful vs stateless workflows in Standard.
`[HARD]`

**Answer:** **Stateful** persists every action's inputs, outputs and state to external Azure Storage, so you get full run history, resubmit-after-outage, chunking, managed-connector triggers, large messages and the asynchronous operation pattern. **Stateless** keeps everything **in memory only**: no run history by default, runs **synchronously**, much faster and cheaper, but interrupted runs are **not** automatically restored — the caller must resubmit. **The type is fixed at creation; changing it later causes runtime errors.**

Microsoft's own guidance: stateless is best for runs **under 5 minutes** and total content **under 64 KB**; bigger content risks out-of-memory. Stateless can only use **push triggers** (Request, Event Hubs, Service Bus) — no Recurrence, no polling.

**Nesting behaviour matrix** (worth memorising, it's a nasty follow-up):

| Parent | Child | Behaviour |
|---|---|---|
| Stateful | Stateful | Asynchronous (or synchronous with `"operationOptions": "DisableAsyncPattern"`) |
| Stateful | Stateless | Trigger and wait |
| Stateless | Stateful | Synchronous |
| Stateless | Stateless | Trigger and wait |

**Stateless limits that differ:** for-each array items **100** (vs 100,000), Until iterations max **100** (vs 5,000), Until timeout default **PT5M** (vs PT1H), run duration default **5 minutes** (vs 90 days), retry interval range **PT1S–PT1M** (vs PT5S–P1D).

**If they push back — "When would you actually use stateless?"** — A high-volume, low-latency synchronous transform behind APIM: receive JSON, validate, reshape, respond. No run history means no storage transactions, which is a real cost line at scale. I'd still enable run history temporarily in non-prod for debugging, then turn it off.

---

### Q35. Triggers, actions and connectors — what are the categories?
`[EASY→MEDIUM]` `[VERBATIM: "What are Managed and Integrated connectors in Logic Apps?"]`

**Answer:** Three connector categories. **Built-in / service-provider** connectors run **in the same process** as the workflow runtime — HTTP, Request, Schedule, plus (in Standard) Service Bus, Event Hubs, SQL Server, Blob, Cosmos DB, DB2, MQ, FTP, SFTP. Highest throughput, lowest cost, no separate API connection resource. **Managed connectors** are the 1,400+ SaaS/PaaS connectors hosted and run by Azure on shared infrastructure — Salesforce, SAP, ServiceNow, D365, Office 365 — created as separate **API connection** Azure resources you must also deploy. **Custom connectors** wrap your own API; in Standard you can additionally author **custom built-in connectors** using the extensibility framework, which get the in-process performance profile.

Trigger types: **Recurrence** (polling on a schedule — stateful only), **Request/HTTP** (synchronous, gives you a callback URL), **push/webhook** (Event Grid, HTTP Webhook), and **connector triggers** (Service Bus queue/topic, Event Hubs, SFTP file added, SQL row inserted).

**If they push back — "Why does built-in vs managed matter commercially?"** — Because managed connector actions are billed differently and add a network hop to shared infrastructure with per-connector throttling that varies by connector — Microsoft's own limits doc just says *"Throttling limit varies based on connector."* Moving a hot path from the managed Service Bus connector to the Standard built-in one is one of the cheapest performance and cost wins available on a Logic Apps estate, and it's a good thing to have an opinion about.

---

### Q36. Show me a real workflow definition.
`[HARD]`

**Answer:** Here's a Standard stateful workflow: Service Bus trigger → validate → parallel enrichment → conditional routing → error scope with compensation. This is `workflow.json` as it lives in a VS Code project.

```json
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {},
    "triggers": {
      "When_a_message_is_received_in_a_queue": {
        "type": "ServiceProvider",
        "inputs": {
          "parameters": { "queueName": "orders-in", "isSessionsEnabled": false },
          "serviceProviderConfiguration": {
            "connectionName": "serviceBus",
            "operationId": "receiveQueueMessages",
            "serviceProviderId": "/serviceProviders/serviceBus"
          }
        },
        "splitOn": "@triggerOutputs()?['body']",
        "runtimeConfiguration": {
          "concurrency": { "runs": 20 }
        }
      }
    },
    "actions": {
      "Init_correlationId": {
        "type": "InitializeVariable",
        "inputs": {
          "variables": [
            { "name": "correlationId", "type": "string",
              "value": "@{coalesce(triggerOutputs()?['body']?['correlationId'], guid())}" }
          ]
        },
        "runAfter": {}
      },

      "Parse_order": {
        "type": "ParseJson",
        "inputs": {
          "content": "@triggerOutputs()?['body']",
          "schema": {
            "type": "object",
            "required": [ "orderId", "customerId", "lines" ],
            "properties": {
              "orderId":    { "type": "string" },
              "customerId": { "type": "string" },
              "lines":      { "type": "array" }
            }
          }
        },
        "runAfter": { "Init_correlationId": [ "Succeeded" ] }
      },

      "Process_order": {
        "type": "Scope",
        "actions": {
          "Get_customer_from_SAP": {
            "type": "Http",
            "inputs": {
              "method": "GET",
              "uri": "https://contoso-apim.azure-api.net/sap/customers/@{body('Parse_order')?['customerId']}",
              "headers": { "X-Correlation-Id": "@{variables('correlationId')}" },
              "authentication": {
                "type": "ManagedServiceIdentity",
                "audience": "api://contoso-sap-facade"
              },
              "retryPolicy": {
                "type": "exponential",
                "count": 4,
                "interval": "PT7S",
                "minimumInterval": "PT5S",
                "maximumInterval": "PT1M"
              }
            },
            "runAfter": {},
            "trackedProperties": {
              "correlationId": "@variables('correlationId')",
              "orderId": "@body('Parse_order')?['orderId']"
            }
          },

          "Route_by_value": {
            "type": "Switch",
            "expression": "@greater(body('Parse_order')?['totalValue'], 100000)",
            "cases": {
              "High_value": {
                "case": true,
                "actions": {
                  "Request_approval": {
                    "type": "ApiConnectionWebhook",
                    "inputs": {
                      "host": { "connection": { "referenceName": "office365" } },
                      "path": "/approvalmail/$subscriptions",
                      "body": {
                        "Message": {
                          "To": "finance-approvals@contoso.com",
                          "Subject": "Approve order @{body('Parse_order')?['orderId']}",
                          "Options": "Approve, Reject"
                        }
                      }
                    },
                    "runAfter": {}
                  }
                }
              }
            },
            "default": { "actions": {} },
            "runAfter": { "Get_customer_from_SAP": [ "Succeeded" ] }
          },

          "Persist_order": {
            "type": "ServiceProvider",
            "inputs": {
              "parameters": {
                "storedProcedureName": "[dbo].[usp_UpsertOrder]",
                "storedProcedureParameters": {
                  "orderId": "@body('Parse_order')?['orderId']",
                  "payload": "@string(body('Parse_order'))"
                }
              },
              "serviceProviderConfiguration": {
                "connectionName": "sql",
                "operationId": "executeStoredProcedure",
                "serviceProviderId": "/serviceProviders/sql"
              }
            },
            "runAfter": { "Route_by_value": [ "Succeeded" ] }
          }
        },
        "runAfter": { "Parse_order": [ "Succeeded" ] }
      },

      "Handle_failure": {
        "type": "Scope",
        "actions": {
          "Filter_failed_actions": {
            "type": "Query",
            "inputs": {
              "from": "@result('Process_order')",
              "where": "@equals(item()['status'], 'Failed')"
            },
            "runAfter": {}
          },
          "Send_to_error_topic": {
            "type": "ServiceProvider",
            "inputs": {
              "parameters": {
                "entityName": "integration-errors",
                "message": {
                  "contentData": "@{body('Filter_failed_actions')}",
                  "userProperties": {
                    "correlationId": "@variables('correlationId')",
                    "workflow": "@workflow()['name']",
                    "runId": "@workflow()['run']['name']"
                  }
                }
              },
              "serviceProviderConfiguration": {
                "connectionName": "serviceBus",
                "operationId": "sendMessage",
                "serviceProviderId": "/serviceProviders/serviceBus"
              }
            },
            "runAfter": { "Filter_failed_actions": [ "Succeeded" ] }
          }
        },
        "runAfter": { "Process_order": [ "Failed", "TimedOut" ] }
      }
    },
    "outputs": {}
  },
  "kind": "Stateful"
}
```

**Things to point at while they read it:** `splitOn` debatches an array trigger payload into one run per item; `runtimeConfiguration.concurrency` bounds parallel runs; `authentication: ManagedServiceIdentity` means **no stored credential anywhere**; `trackedProperties` pushes business identifiers into diagnostics (capped at **8,000 characters** per action); the `Handle_failure` scope with `runAfter: [Failed, TimedOut]` plus `@result('Process_order')` is the try/catch idiom.

**If they push back — "How do you unit-test that?"** — Logic Apps Standard runs locally in VS Code against Azurite, so I can invoke a workflow with a crafted payload and assert on run output; for CI I use the Logic Apps Standard test framework (mock the connector responses) and, pragmatically, a contract test that POSTs to the Request trigger of a deployed dev workflow and asserts the resulting Service Bus message. Full designer-level unit testing is weaker than code — that's a real trade-off of low-code and I'd say so.

---

### Q37. How do you handle errors in a Logic App?
`[MEDIUM]` `[VERBATIM: "How can you handle errors in a Logic App?"]`

**Answer:** Four layers, in order of cost. **(1) Retry policy** on the individual action — four types: `default`, `none`, `fixed`, `exponential`. **(2) `runAfter`** — change the successor's condition from `Succeeded` to include `Failed`, `Skipped`, `TimedOut` so a compensation action runs. **(3) Scopes** — group actions, treat the scope like a try block, attach a catch scope with `runAfter: Failed`, and use **`@result('ScopeName')`** to get the array of failed action objects with name, status, code, inputs, outputs and `clientTrackingId`. **(4) Terminate** with an explicit status, plus Azure Monitor alerts on `workflowRunCompleted` failures for the things retries can't fix.

**Retry policy numbers to quote:** the **Default** policy is exponential, up to **4 retries**, intervals scaling by **7.5 seconds** and capped between **5 and 45 seconds**. `count` accepts **1–90**. `interval` range is **PT5S–P1D** in Consumption and in Standard stateful; **PT1S–PT1M** in Standard stateless. For `exponential`, `maximumInterval` defaults to **P1D** in Consumption and **PT1H** in Standard; `minimumInterval` defaults to **PT5S**. Retries fire on **408, 429 and 5xx**.

```json
"Call_flaky_partner": {
  "type": "Http",
  "inputs": {
    "method": "POST",
    "uri": "https://partner.example.com/v1/shipments",
    "body": "@body('Parse_order')",
    "retryPolicy": {
      "type": "exponential",
      "count": 5,
      "interval": "PT10S",
      "minimumInterval": "PT5S",
      "maximumInterval": "PT2M"
    }
  },
  "runAfter": { "Parse_order": [ "Succeeded" ] }
}
```

**If they push back — "Retry storms?"** — Exponential with a bounded `maximumInterval` plus the built-in randomisation is the mitigation on the Logic Apps side; on the platform side I'd put a Service Bus queue in front of the flaky partner (Queue-Based Load Levelling) so retries drain at a controlled rate instead of hammering, and I'd cap `count` low with a dead-letter path rather than retrying 90 times into a dead backend. Retry plus circuit breaker, never retry alone.

---

### Q38. Control flow: foreach concurrency, until, and the debatching trap.
`[HARD]`

**Answer:** `Foreach` iterates an array — **100,000 items** in Consumption and Standard stateful, but only **100** in stateless. Its concurrency default is **20**, minimum 1, maximum **50**; set it to 1 when order matters. `Until` loops on a condition with default **60** iterations, max **5,000** (100 stateless), default timeout **PT1H** (PT5M stateless). `Condition` and `Switch` do branching; `Scope` groups.

**The trap that bites in production:** `splitOn` debatching handles **100,000 items** when trigger concurrency is **off**, but drops to **100 items** the moment you turn concurrency on. And **turning trigger concurrency on is irreversible** — once enabled, defaults become 25 runs (max 100) in Consumption and 100 (max 100) in Standard, and you cannot go back to unlimited. Maximum waiting runs: 100 Consumption, 200 Standard.

```json
"For_each_line": {
  "type": "Foreach",
  "foreach": "@body('Parse_order')?['lines']",
  "actions": {
    "Reserve_stock": {
      "type": "Http",
      "inputs": { "method": "POST", "uri": "https://inventory.internal/reserve", "body": "@item()" },
      "runAfter": {}
    }
  },
  "runtimeConfiguration": {
    "concurrency": { "repetitions": 10 }
  },
  "runAfter": { "Parse_order": [ "Succeeded" ] }
}
```

**If they push back — "50 concurrent iterations against a legacy SAP endpoint?"** — No. Concurrency has to be sized to the *slowest* dependency, not the fastest. I'd set repetitions to what the backend's connection pool tolerates (often 4–8), and if the volume needs more throughput than that, the answer isn't more concurrency — it's a queue plus competing consumers, so backpressure is explicit rather than emergent.

---

### Q39. Logic Apps limits you should know cold.
`[MEDIUM]` `[numbers = credibility]`

| Limit | Consumption | Standard |
|---|---|---|
| Run duration | 90 days | 90 days (stateful), **5 min default (stateless)** |
| Run history retention | 90 days | 90 days |
| Actions per workflow | 500 | 500 |
| Action nesting depth | 8 | 8 |
| Single action max input **or** output | **104,857,600 bytes (105 MB)** | same |
| Single action combined inputs+outputs | **209,715,200 bytes (210 MB)** | same |
| Message size | 100 MB (chunking to **1 GB**) | 100 MB (chunking to 1 GB) |
| HTTP request timeout | **120 s** | **225 s** |
| Expression character limit | 8,192 | 8,192 |
| Expression **evaluation** limit | 131,072 | 131,072 |
| Variables per workflow | 250 | 250 |
| `trackedProperties` per action | 8,000 chars | 8,000 chars |
| Action executions / 5-min rolling | 100,000 (300,000 in high-throughput preview) | same |

Also: run duration must always be **≤ retention**, or run history is deleted before jobs complete. And a Standard workflow's Request trigger accepts at most **56 API Management REST API calls per 5 minutes** — use the callback URL, not the management API.

**If they push back — "What do you do when a payload is bigger than 100 MB?"** — Claim Check. Write the payload to Blob Storage, pass the blob URI (with a short-lived SAS — the Valet Key pattern) through the workflow, and let the final consumer fetch it. That's also the mitigation for the on-premises data gateway's much tighter **2 MB write** ceiling.

---

### Q40. Integration accounts, B2B and EDI.
`[MEDIUM]` `[EY does a lot of B2B — worth 3 minutes]`

**Answer:** An **integration account** is the artifact store for B2B: trading partners, agreements, schemas (XSD), maps (XSLT/Liquid), certificates and batch configurations. It's what enables the **AS2**, **X12**, **EDIFACT** and **RosettaNet** connectors. In **Standard** you no longer need one for plain Liquid/XML transforms — those actions ship in the runtime — but you still need it for EDI trading-partner agreements.

**Numbers:** 1,000 integration accounts per subscription; one Free-tier account per region. Artifact counts by tier (Free/Basic/Standard/Premium-preview): trading agreements 10/1/1,000/unlimited; trading partners 25/2/1,000/unlimited; maps 25/500/1,000/unlimited; schemas 25/500/1,000/unlimited. Artifact capacity: assembly, XSLT map and schema each **8 MB** (files over 2 MB must be uploaded via blob storage or the REST API). **B2B message size limits (multitenant): AS2 v2 = 100 MB, AS2 v1 = 25 MB, X12 = 50 MB, EDIFACT = 50 MB** — and the docs mark these "Unavailable" for single-tenant.

**If they push back — "Walk me through an AS2 exchange"** — Partner posts an AS2 message over HTTPS to our receive workflow; we validate the signature against their certificate, decrypt with ours, return a signed **MDN** (synchronous or asynchronous per the agreement), then decode the X12 payload, validate against the schema, reconcile the **control numbers** (ISA/GS/ST) for duplicate detection, transform via XSLT to the canonical internal format, and drop it on Service Bus. Errors produce a 997 functional acknowledgement. The bits people forget are MDN handling and control-number reconciliation — name them.

---

### Q41. The on-premises data gateway — how does it work and what are the limits?
`[MEDIUM]` `[VERBATIM: "Can Logic Apps interact with on-premises resources?"]`

**Answer:** The on-premises data gateway is a Windows client app you install inside the customer network. It is **outbound-only** — no inbound firewall ports required, all cloud communication arrives as responses to the gateway's outbound polling. It's shared across Logic Apps, Data Factory, Analysis Services, Microsoft Fabric, Power BI, Power Apps and Power Automate. Two types: **standard** (multi-user, multi-source, shareable) and **personal** (single user, Power BI only). There's also a **managed VNet data gateway** that needs no install.

**The numbers that decide architecture:** **2 MB payload limit for write operations**; **2 MB request / 8 MB compressed response for reads**; **2,048 character limit on GET request URLs**; maximum **1,000 data sources per gateway cluster**; credentials are cached client-side and the cache takes roughly **5 hours** to expire, so a credential change is not immediate. Only the **last six monthly releases** are supported.

**If they push back — "2 MB is tiny. What's the alternative?"** — Three: (a) Claim Check — land the payload in Blob and pass the URI; (b) skip the gateway entirely and use **Logic Apps Standard with VNet integration** over ExpressRoute/VPN, hitting the on-prem system as a private endpoint — this is the modern answer and it has no 2 MB ceiling; (c) an **APIM self-hosted gateway** deployed on-prem so the API is exposed outward under governance instead of reached inward. For a new build I'd argue for (b) or (c); the data gateway is for when you can't get network changes approved.

---

## 6. Azure Functions & Durable Functions

### Q42. Compare the Azure Functions hosting plans.
`[HARD]` `[VERBATIM: "What is the difference between Consumption Plan and Premium Plan?"]`

**Answer:** Five options, and **Consumption is now explicitly legacy** — Microsoft's own docs say "For new serverless function apps, use the Flex Consumption plan." **Flex Consumption** is the current serverless default: pay-per-use, Linux code-only, per-function scaling to **1,000 instances**, instance memory of **512 MB / 2,048 MB / 4,096 MB**, VNet integration, and **always-ready instances** to kill cold start. **Premium** gives prewarmed instances, larger SKUs and VNet. **Dedicated (App Service)** is for predictable billing or when you already have underutilised plans. **Container Apps** is for containerised functions alongside other microservices.

| | Flex Consumption | Premium | Dedicated / ASE | Container Apps | Consumption (legacy) |
|---|---|---|---|---|---|
| Timeout default / max (min) | 30 / unbounded | 30 / unbounded | 30 / unbounded (needs Always On) | 30 / unbounded | **5 / 10** |
| Max instances | **1,000** | Windows 100, Linux 20–100 | 10–30 (100 ASE) | 300–1,000 | Windows 200, Linux 100 |
| Cold start | improved, always-ready instances | prewarmed | none | depends on min replicas | yes |
| VNet integration (outbound) | ✔ | ✔ | ✔ | ✔ | ✗ |
| Private endpoints (inbound) | ✔ | ✔ | ✔ | ✗ | ✗ |
| Max memory / instance | 4 GB | 3.5–14 GB | 1.75–256 GB | varies | 1.5 GB |
| Deployment slots | n/a | 3 | 1–20 | not supported | 2 |
| OS | Linux only | Linux + Windows | Linux + Windows | Linux (container) | Windows (Linux retired) |

**The single most important number in the whole table isn't in the table:** regardless of `functionTimeout`, **230 seconds is the maximum an HTTP-triggered function has to respond**, because of the Azure Load Balancer default idle timeout. That's why long work must use the Durable Functions async request-reply pattern (HTTP 202 + polling) or defer to a queue. Also: there's a **60-second** cap on the language worker process starting, and it isn't configurable.

**Retirement dates to know:** Linux Consumption retires **30 September 2028**; **v3-runtime** Linux Consumption apps stop running after **30 September 2026**; and Durable Functions **in-process model support ends 10 November 2026** — migrate to the isolated worker model.

**If they push back — "How do you pick, in one sentence?"** — Flex Consumption unless you need Windows, >4 GB memory, or a container; Premium if you need Windows plus VNet plus prewarmed; Dedicated if you already own the plan; Container Apps if the function is one microservice among many in the same environment.

---

### Q43. Triggers and bindings — explain input vs output binding.
`[EASY→MEDIUM]`

**Answer:** A **trigger** is what causes the function to run (exactly one per function) and carries the payload. **Bindings** are declarative connections to other services so you don't write SDK plumbing: an **input binding** fetches data *into* the function before it runs (e.g. read a Cosmos document by ID from the route), an **output binding** writes data *out* after it returns (e.g. push to a Service Bus queue or write a blob). A trigger is a special kind of input binding.

```python
# function_app.py — Python v2 programming model. Service Bus trigger in, Service Bus out.
import json
import logging

import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="EnrichOrder")
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="orders-in",
    connection="ServiceBusConnection",          # identity-based: ServiceBusConnection__fullyQualifiedNamespace
)
@app.service_bus_queue_output(
    arg_name="outmsg",
    queue_name="orders-enriched",
    connection="ServiceBusConnection",
)
def enrich_order(msg: func.ServiceBusMessage, outmsg: func.Out[str]) -> None:
    body = json.loads(msg.get_body().decode("utf-8"))

    logging.info(
        "order=%s messageId=%s deliveryCount=%s",
        body.get("orderId"), msg.message_id, msg.delivery_count,
    )

    # Idempotency: the business key travels with the message, not the broker's id
    body["enrichedAt"] = msg.enqueued_time_utc.isoformat()
    body["correlationId"] = msg.correlation_id or body.get("orderId")

    outmsg.set(json.dumps(body))
```

```json
// host.json — the Service Bus knobs that matter
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "extensions": {
    "serviceBus": {
      "maxAutoLockRenewalDuration": "00:05:00",
      "maxConcurrentCalls": 16,
      "prefetchCount": 0,
      "autoCompleteMessages": true
    }
  },
  "logging": {
    "applicationInsights": {
      "samplingSettings": { "isEnabled": true, "maxTelemetryItemsPerSecond": 20 }
    }
  }
}
```

**PeekLock behaviour to state:** the runtime receives in **PeekLock** mode, calls `Complete` on success and `Abandon` on failure automatically (`autoCompleteMessages`), and auto-renews the lock while the function runs, up to `maxAutoRenewDuration` — **default 5 minutes**. Poison handling isn't configurable in Functions; **Service Bus itself** dead-letters after `MaxDeliveryCount` (default **10**).

**If they push back — "Identity-based connection?"** — Instead of `ServiceBusConnection` holding a connection string, set `ServiceBusConnection__fullyQualifiedNamespace = contoso.servicebus.windows.net` and assign the function app's managed identity **Azure Service Bus Data Receiver/Sender**. One gotcha worth naming: for accurate **scaling** the extension calls the Service Bus Administration API, which needs the **Azure Service Bus Data Owner** role (or `Manage` on a SAS policy). Without it there's no error — it silently falls back to less accurate peek-based estimation and your scaling goes wrong.

---

### Q44. Durable Functions — what is it and what are the patterns?
`[HARD]` `[THE answer to "how do you do saga/long-running orchestration in Azure"]`

**Answer:** Durable Functions is the stateful extension to Azure Functions: you write orchestration **in code**, and the runtime handles state, checkpointing, retries and recovery by **event-sourced replay**. Four function types: the **orchestrator** (defines the workflow, must be deterministic), **activity** functions (do the actual work), **entity** functions (durable stateful objects), and the **client** (starts, queries, terminates orchestrations, sends events).

**The six patterns, by name:**

| Pattern | Use |
|---|---|
| **Function chaining** | Sequential steps where each output feeds the next |
| **Fan-out / fan-in** | Parallel work then aggregation — `task_all` |
| **Async HTTP APIs** | Long job: return `202` + status URL, client polls. `create_check_status_response` gives you this free |
| **Monitoring** | Recurring polling with a flexible interval, e.g. poll a partner until a job completes, then stop |
| **Human interaction** | Wait for an external event (approval) with a timeout — durable, can wait days |
| **Aggregator (entities)** | Accumulate events into a single stateful entity over time |

```python
# function_app.py — Durable Functions, Python v2 model.
# Order saga: reserve stock -> charge -> ship, with compensation on failure.
import json
import logging
from datetime import timedelta

import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)


# ---------- client: HTTP starter (async HTTP API pattern) ----------
@app.route(route="orders", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_order(req: func.HttpRequest, client) -> func.HttpResponse:
    payload = req.get_json()
    # Deterministic instance id = idempotency: a duplicate POST re-attaches, never re-runs
    instance_id = f"order-{payload['orderId']}"
    await client.start_new("order_orchestrator", instance_id, payload)
    logging.info("started orchestration %s", instance_id)
    return client.create_check_status_response(req, instance_id)


# ---------- orchestrator: MUST be deterministic ----------
@app.orchestration_trigger(context_name="context")
def order_orchestrator(context: df.DurableOrchestrationContext):
    order = context.get_input()
    compensations = []

    retry = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=4)

    try:
        reservation = yield context.call_activity_with_retry("reserve_stock", retry, order)
        compensations.append(("release_stock", reservation))

        payment = yield context.call_activity_with_retry("charge_payment", retry, order)
        compensations.append(("refund_payment", payment))

        # Human interaction: wait up to 24h for approval on high-value orders
        if order["totalValue"] > 100000:
            deadline = context.current_utc_datetime + timedelta(hours=24)
            approval = context.wait_for_external_event("ApprovalEvent")
            timeout = context.create_timer(deadline)
            winner = yield context.task_any([approval, timeout])
            if winner == timeout:
                raise Exception("approval_timeout")
            timeout.cancel()
            if not approval.result.get("approved"):
                raise Exception("approval_rejected")

        # Fan-out / fan-in: notify every downstream system in parallel
        notifications = [
            context.call_activity("notify_system", {"system": s, "order": order})
            for s in ("wms", "crm", "analytics")
        ]
        yield context.task_all(notifications)

        shipment = yield context.call_activity_with_retry("create_shipment", retry, order)
        return {"status": "completed", "shipmentId": shipment["id"]}

    except Exception as exc:                       # ---------- compensate in reverse ----------
        context.set_custom_status(f"compensating: {exc}")
        for activity, state in reversed(compensations):
            yield context.call_activity(activity, state)
        return {"status": "compensated", "reason": str(exc)}


# ---------- activities: where real work (and non-determinism) lives ----------
@app.activity_trigger(input_name="order")
def reserve_stock(order: dict) -> dict:
    logging.info("reserving stock for %s", order["orderId"])
    return {"reservationId": f"res-{order['orderId']}", "orderId": order["orderId"]}


@app.activity_trigger(input_name="reservation")
def release_stock(reservation: dict) -> dict:
    logging.info("releasing reservation %s", reservation["reservationId"])
    return {"released": True}


@app.activity_trigger(input_name="order")
def charge_payment(order: dict) -> dict:
    return {"paymentId": f"pay-{order['orderId']}", "amount": order["totalValue"]}


@app.activity_trigger(input_name="payment")
def refund_payment(payment: dict) -> dict:
    logging.info("refunding %s", payment["paymentId"])
    return {"refunded": True}


@app.activity_trigger(input_name="payload")
def notify_system(payload: dict) -> str:
    return f"notified {payload['system']}"


@app.activity_trigger(input_name="order")
def create_shipment(order: dict) -> dict:
    return {"id": f"shp-{order['orderId']}"}
```

**Orchestrator determinism rules — say these unprompted, they're the classic follow-up:** the orchestrator is **replayed from its event history** on every checkpoint, so it must produce identical decisions each time. That means **no `datetime.now()`** (use `context.current_utc_datetime`), **no `random`/`uuid4`** (use `context.new_guid()` or derive from input), **no I/O, no network calls, no DB access** (put those in activities), **no infinite loops without `continue_as_new()`**, and **no blocking calls** — always `yield` on `context.*`. In Python, use `yield` with `context.task_all` / `context.task_any`, not `await`.

**If they push back — "What's the storage backend?"** — Historically Azure Storage (queues + tables) as the default, with Netherite and MSSQL as alternatives. The current recommended backend is the **Durable Task Scheduler**, which brings a managed backend and a dashboard, and there's a local emulator container for development. Task hubs isolate one app's orchestrations from another's on shared storage — collide the hub name across environments and you get very confusing cross-talk.

---

### Q45. Durable Functions vs Logic Apps for orchestration.
`[MEDIUM]`

**Answer:** Same job, different owner. **Durable Functions** when the orchestration is genuinely algorithmic — dynamic fan-out over N items computed at runtime, complex compensation logic, tight loops, unit-testable business rules, and a team that lives in code and Git. **Logic Apps** when the value is in the connectors and the workflow needs to be legible to non-developers, or when the process spans days with human approval steps and a support analyst needs to read the run history without a debugger.

Cost shape differs too: Durable pays per execution and per storage transaction on the history; Logic Apps Consumption pays per action execution, which makes a 10,000-iteration loop expensive, while Logic Apps Standard is a flat plan.

**If they push back — "Which for a saga?"** — Durable, by default. Compensation logic is conditional and stateful, and expressing "undo steps 3, 2, 1 in reverse, but only the ones that actually succeeded" in a designer is painful. The exception is when every step is a SaaS connector call — then a Logic App with a compensation Scope on `runAfter: Failed` is less code to own.

---
## 7. Azure Data Factory / Synapse Pipelines

### Q46. When does an integration project use Data Factory instead of Logic Apps?
`[MEDIUM]` `[VERBATIM: "What is the difference between Azure Data Factory and Logic Apps for data integration?"]`

**Answer:** ADF is for **bulk, batch, data-shaped** movement; Logic Apps is for **event-driven, transactional, process-shaped** integration. If the unit of work is "a row" and there are millions of them on a schedule, that's ADF. If the unit of work is "an order" and it arrived just now, that's Logic Apps or Functions.

| | Data Factory | Logic Apps |
|---|---|---|
| Unit of work | datasets / millions of rows | a business message |
| Trigger style | schedule, tumbling window, storage event | event, HTTP, queue, schedule |
| Latency | minutes | seconds |
| Connectors | ~100 data stores, deep on databases and file formats | 1,400+, deep on SaaS/business apps |
| Transformation | Mapping Data Flows (Spark), or push down to the source | expressions, Liquid, XSLT, or call a Function |
| Cost driver | Data Integration Units × time, pipeline activity runs | action executions or hosting plan |
| Who reads it | data engineers | integration developers / business analysts |

There's real overlap and it's fine to say so: ADF has a Web activity and Logic Apps has a SQL connector. My rule is *"if I'd naturally describe it as a pipeline, it's ADF; if I'd describe it as a workflow, it's Logic Apps."*

**If they push back — "Can they be used together?"** — Constantly. The common pattern: a Logic App handles the event and the business process, and calls an ADF pipeline (via the ADF connector or a REST call with managed identity) when the step is "load these 4 million rows". Conversely an ADF pipeline's Web activity can fire a Logic App to send the failure notification. Also worth naming: Microsoft now positions **Data Factory in Microsoft Fabric** as "the next generation of Azure Data Factory", so for greenfield data work on a Fabric-adopting client I'd raise Fabric rather than classic ADF.

---

### Q47. Explain ADF integration runtimes.
`[MEDIUM]` `[near-certain if the panel is data-leaning]`

**Answer:** The integration runtime is the compute that ADF actually uses. Three types. **Azure IR** — fully managed serverless compute for data flows, cloud-to-cloud copy, and activity dispatch over public networks or, with Managed VNet enabled, over Private Link. **Self-hosted IR** — a Windows agent you install on-prem or in a VNet to reach private data stores; it makes **outbound HTTP-only** connections, requires the JRE, and scales out **active-active across multiple machines** for HA. **Azure-SSIS IR** — a managed cluster of VMs for lift-and-shift of existing SSIS packages, with your own SQL Database/Managed Instance hosting SSISDB.

| IR type | Public network | Private Link | Capabilities |
|---|---|---|---|
| Azure | ✔ | ✔ | Data Flow, data movement, activity dispatch |
| Self-hosted | ✔ | ✔ | data movement, activity dispatch (**no Data Flow**) |
| Azure-SSIS | ✔ | ✔ | SSIS package execution only |

**Performance numbers:** a copy activity on the Azure IR can use up to **256 Data Integration Units (DIUs)**; `parallelCopies` controls thread-level parallelism within one copy activity; **staged copy** via Blob is the documented interim-staging option. Microsoft's tuning method, worth quoting: baseline with a representative dataset large enough to take ~10 minutes, maximise a single copy activity first, then fan out with ForEach for aggregate throughput.

**Resolution precedence** (a genuinely good follow-up): self-hosted IR takes precedence over a managed-VNet Azure IR, which takes precedence over the global Azure IR. If either the source or sink linked service points at a self-hosted IR, the copy runs there.

**If they push back — "How do IRs work in CI/CD?"** — ADF requires the **same name and type** of IR across all CI/CD stages. The clean pattern is a dedicated "shared" factory that owns the integration runtimes, and every environment references them as **linked** integration runtimes. Otherwise your ARM deployment recreates the self-hosted IR registration and breaks the on-prem agent.

---

### Q48. Synapse pipelines vs ADF?
`[EASY]`

**Answer:** Synapse pipelines are essentially the ADF engine embedded in a Synapse workspace, so authoring is near-identical. Differences that matter: Synapse pipelines support only **Azure and self-hosted** IRs (**no Azure-SSIS IR**), and Synapse workspaces can restrict outbound traffic from the managed VNet whereas ADF opens all ports for outbound. You'd use Synapse pipelines when the workspace is already the analytics home; standalone ADF when the pipelines serve many consumers, or when you need SSIS.

---

## 8. Identity, Secrets, Networking Across AIS

### Q49. Managed identity — system-assigned vs user-assigned, and where do you use each?
`[MEDIUM]` `[EY scenario, VERBATIM: "Walk me through exactly how a Logic App authenticates to a downstream REST API securely — without storing any credentials anywhere."]`

**Answer:** A managed identity is a service principal in Entra ID whose credential Azure creates, rotates and never shows you. **System-assigned** is created with the resource, shares its lifecycle, and is deleted with it — one resource, one identity. **User-assigned** is a standalone resource you create once and attach to many services, surviving redeployment — which is why it's the right choice for anything IaC-managed, because role assignments stay valid across a `terraform destroy`/`apply` cycle.

**The Logic App → downstream REST API answer, end to end, no credentials:** enable a managed identity on the Logic App; in Entra, expose the target API as an app registration with an Application ID URI and app roles; grant the Logic App's identity that app role; then set the HTTP action's authentication type to `ManagedServiceIdentity` with the target `audience`. At runtime the Logic Apps runtime fetches a token from the Entra token endpoint using the identity, attaches it as a Bearer token, and caches/refreshes it. APIM in front validates it with `validate-jwt`. Nothing is stored anywhere.

```json
"Call_downstream_api": {
  "type": "Http",
  "inputs": {
    "method": "POST",
    "uri": "https://contoso-apim.azure-api.net/inventory/reserve",
    "body": "@body('Parse_order')",
    "authentication": {
      "type": "ManagedServiceIdentity",
      "identity": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-int-prod/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-integration-prod",
      "audience": "api://contoso-inventory"
    }
  },
  "runAfter": { "Parse_order": [ "Succeeded" ] }
}
```

```bash
# Terraform/Bicep aside — the CLI equivalents, useful to be able to say out loud
az logic workflow identity assign --name lg-orders --resource-group rg-int-prod

PRINCIPAL=$(az logic workflow show -n lg-orders -g rg-int-prod --query identity.principalId -o tsv)

az role assignment create \
  --assignee-object-id "$PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Azure Service Bus Data Sender" \
  --scope "/subscriptions/$SUB/resourceGroups/rg-int-prod/providers/Microsoft.ServiceBus/namespaces/sb-int-prod"
```

**One Standard-specific caveat to volunteer:** Logic Apps Standard supports the system-assigned identity **and** multiple user-assigned identities simultaneously, but only one can be used at a time — and most **built-in/service-provider connectors currently don't support selecting a user-assigned identity**; the exceptions are SQL Server and HTTP. So in Standard, the system-assigned identity is often the practical choice for built-in connectors. Also: the system-assigned identity is enabled by default and used to authenticate connections at runtime — **disable it and connections break at runtime**, which is a nasty surprise.

**If they push back — "How does the Function get a token?"** — `DefaultAzureCredential` from `azure-identity`, which resolves to the managed identity in Azure and to your `az login` locally, so the same code works in both:

```python
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

credential = DefaultAzureCredential()   # managed identity in Azure, az CLI locally
client = ServiceBusClient(
    fully_qualified_namespace="sb-int-prod.servicebus.windows.net",
    credential=credential,
)

with client, client.get_queue_sender("orders-out") as sender:
    sender.send_messages(
        ServiceBusMessage(
            body='{"orderId":"A-1001"}',
            message_id="A-1001",           # enables Service Bus duplicate detection
            correlation_id="corr-A-1001",
            content_type="application/json",
        )
    )
```

---

### Q50. Private endpoints and network isolation across AIS — what's the target-state topology?
`[HARD]`

**Answer:** Target state is: nothing in the integration estate has a public endpoint except the front door, and every hop is private. Concretely — APIM **Premium/Premium v2 VNet-injected** (or Standard v2 with VNet integration for outbound plus a private endpoint for inbound); Logic Apps **Standard** with VNet integration and private endpoints; Functions on **Flex Consumption or Premium** with VNet integration and private endpoints; Service Bus and Key Vault and Storage reached over **private endpoints** with public network access disabled; Private DNS zones so the FQDNs resolve to private IPs.

The distinction to get right, because interviewers probe it: **VNet integration** is about **outbound** — your service can reach private things. **Private endpoint** is about **inbound** — private things can reach your service, and it stops having a routable public IP. Most designs need both, in different directions.

**If they push back — "What breaks when you turn this on?"** — Three things, reliably. (1) **DNS.** Without the right Private DNS zone links, everything still resolves to the public IP and fails opaquely. (2) **The on-premises data gateway** becomes unnecessary but people leave it in, adding a 2 MB ceiling for no reason. (3) **Key Vault firewall + APIM named values** — you must use the system-assigned identity and enable "Allow trusted Microsoft services", or named-value resolution silently fails at deploy time. I'd add: if APIM is VNet-injected and you configure `openid-config` URLs, set `validate-connectivity="false"` on `validate-jwt` or the policy save fails because the endpoint can't be resolved via public DNS.

---

### Q51. How do you manage secrets across the whole integration estate?
`[MEDIUM]`

**Answer:** One rule: **prefer managed identity so there is no secret; where a secret is unavoidable, it lives in Key Vault and is referenced, never copied.** APIM references it via a **Key Vault named value** (auto-rotates within 4 hours, secret must be 1–4,096 chars, identifier without version). Functions and Logic Apps Standard reference it via a **Key Vault reference in app settings** — `@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/name/)`. Pipelines pull from Key Vault via a variable group linked to the vault, so no secret is typed into YAML. Nothing secret is ever in Git, in a Bicep parameter file, or in a policy XML.

```bicep
// Function app setting backed by Key Vault, resolved with the app's managed identity
resource fnApp 'Microsoft.Web/sites@2023-12-01' existing = { name: 'fn-orders-prod' }

resource appSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: fnApp
  name: 'appsettings'
  properties: {
    FUNCTIONS_EXTENSION_VERSION: '~4'
    FUNCTIONS_WORKER_RUNTIME: 'python'
    // identity-based Service Bus connection: no secret at all
    ServiceBusConnection__fullyQualifiedNamespace: 'sb-int-prod.servicebus.windows.net'
    // the one unavoidable partner secret, referenced not stored
    PARTNER_HMAC_KEY: '@Microsoft.KeyVault(SecretUri=https://kv-int-prod.vault.azure.net/secrets/partner-hmac-key/)'
  }
}
```

**If they push back — "How do you prove no secret is in the repo?"** — Secret scanning in the pipeline (GitHub secret scanning / `gitleaks` / Defender for DevOps), a pre-commit hook, and a policy check that fails the build on any `*.bicepparam` containing a value for a parameter marked `@secure()`. Plus Azure Policy denying resources with public network access in prod subscriptions. See [CI/CD & IaC](05-cicd-iac-and-gitops.md) and [Auth & Security](06-auth-and-security.md).

---

### Q52. How do you make an AIS integration idempotent and safe to retry?
`[HARD]` `[Tier-2 near-certain]`

**Answer:** Three layers. **At the edge**, accept an `Idempotency-Key` header on POST and cache the response against it so a client retry returns the original result rather than creating a second order. **In the broker**, set a meaningful `MessageId` on every Service Bus message — Microsoft's own wording is *"The sender can and should set the message-id to a unique value"* — and enable **duplicate detection** on the entity with a window sized to your retry horizon. **In the consumer**, make the handler idempotent: an upsert keyed on the business ID, or an idempotency table with the processed key and a TTL. Duplicate detection alone is not enough because its window is finite and it only catches identical `MessageId`s within it.

```xml
<!-- APIM: idempotent POST via an Idempotency-Key header -->
<inbound>
    <base />
    <choose>
        <when condition="@(context.Request.Method == "POST")">
            <set-variable name="idemKey"
                value="@(context.Request.Headers.GetValueOrDefault("Idempotency-Key", ""))" />
            <choose>
                <when condition="@(string.IsNullOrEmpty((string)context.Variables["idemKey"]))">
                    <return-response>
                        <set-status code="400" reason="Bad Request" />
                        <set-body>{"error":"Idempotency-Key header is required for POST"}</set-body>
                    </return-response>
                </when>
            </choose>
            <cache-lookup-value key="@("idem-" + (string)context.Variables["idemKey"])"
                                variable-name="cachedResponse" />
            <choose>
                <when condition="@(context.Variables.ContainsKey("cachedResponse"))">
                    <return-response>
                        <set-status code="200" reason="OK" />
                        <set-header name="Idempotent-Replay" exists-action="override">
                            <value>true</value>
                        </set-header>
                        <set-body>@((string)context.Variables["cachedResponse"])</set-body>
                    </return-response>
                </when>
            </choose>
        </when>
    </choose>
</inbound>
<outbound>
    <base />
    <choose>
        <when condition="@(context.Request.Method == "POST" &amp;&amp; context.Response.StatusCode >= 200 &amp;&amp; context.Response.StatusCode &lt; 300)">
            <cache-store-value key="@("idem-" + (string)context.Variables["idemKey"])"
                               value="@(context.Response.Body.As<string>(preserveContent: true))"
                               duration="86400" />
        </when>
    </choose>
</outbound>
```

**If they push back — "What about the Durable Functions angle?"** — Use a **deterministic instance ID** derived from the business key (`f"order-{orderId}"`). Starting an orchestration with an existing instance ID doesn't launch a second run — it re-attaches — so the whole saga becomes idempotent at the entry point. That's the trick in the §6 code sample, and it's worth pointing at.

---

## 9. The AWS Mirror Table

If your interviewer is an AWS person — and in a Big-4 GDS that happens — you need this mapping fluently. Say the Azure name, then the AWS name, then the one place they differ.

| Azure | AWS | The difference that matters |
|---|---|---|
| **API Management** | API Gateway (+ some of AWS AppSync) | APIM has a built-in developer portal and can run its gateway **on-prem/self-hosted**; API Gateway cannot leave AWS |
| **Logic Apps** | Step Functions (+ EventBridge Pipes / AppFlow) | Logic Apps ships 1,400+ SaaS connectors; Step Functions is state-machine-first and expects Lambda for connectivity |
| **Azure Functions** | Lambda | Lambda max timeout 15 min; Functions is unbounded off Consumption but capped at **230 s for HTTP** |
| **Durable Functions** | Step Functions | Durable is orchestration-as-code with replay; Step Functions is orchestration-as-JSON/ASL |
| **Service Bus** | SQS (queues) + SNS (topics) | Service Bus is one service doing both, plus sessions, transactions, duplicate detection, scheduled delivery |
| **Event Grid** | EventBridge | Both are push routers; EventBridge has a richer schema registry, Event Grid has MQTT and Azure-resource events built in |
| **Event Hubs** | Kinesis Data Streams (or MSK) | Event Hubs exposes a **Kafka-compatible endpoint** — the answer to any "we have Kafka" migration question |
| **Azure Data Factory** | AWS Glue + Step Functions | Glue is Spark-first and catalog-centric; ADF is copy-first with Mapping Data Flows on top |
| **AKS** | EKS | Broadly equivalent; AKS control plane is free on the Free tier |
| **Bicep / ARM** | CloudFormation | Terraform is the neutral answer for both — see [IaC](05-cicd-iac-and-gitops.md) |
| **Azure DevOps Pipelines** | CodePipeline + CodeBuild | GitHub Actions is the converging answer |
| **Key Vault** | Secrets Manager / KMS / Parameter Store | Key Vault does secrets, keys and certificates in one resource |
| **Managed identity** | IAM roles for service accounts / EC2 instance profile | Same idea: no stored credential, platform-issued token |
| **Entra ID** | IAM + Cognito | Entra is both workforce and workload identity |
| **Application Insights / Log Analytics** | CloudWatch + X-Ray | KQL is materially better than CloudWatch Logs Insights for cross-service correlation |
| **Front Door** | CloudFront + Global Accelerator | |
| **Private Endpoint** | PrivateLink / VPC endpoint | Same concept, same DNS pitfalls |
| **On-premises data gateway** | (no direct equivalent — Direct Connect + agents) | |

**The line to say if they ask "could you do this on AWS?"** — *"Yes, and the architecture wouldn't change — API gateway, broker, event router, serverless compute, orchestrator. What changes is the policy language and the identity model. The pattern vocabulary is portable; the implementation detail is what I'd have to relearn, and that's a few weeks, not a career."*

---

## 10. 30-Second Whiteboard Versions

### 10.1 "Design the integration architecture for end-to-end order processing" (the EY retail scenario)

```
   Partner / Mobile / Web
            |
      [ Front Door + WAF ]
            |
      [ APIM ]  validate-jwt (Entra) | rate-limit-by-key | quota-by-key
       |    |   validate-content | correlation-id | ip-filter (partner)
       |    +--> exposes the same ops as an MCP server for EY.ai / Copilot agents
       v
  [ Service Bus queue: orders-in ]     <- decouple, buffer, DLQ (MaxDeliveryCount 10)
            |  competing consumers
            v
  [ Logic Apps Standard ]  built-in SB connector, SAP/D365 managed connectors,
            |              managed identity, trackedProperties -> App Insights
            +--> [ Azure Function ]  the one hard transform, Python
            +--> [ SQL / Cosmos ]    persist, upsert on business key = idempotent
            v
  [ Event Grid topic: OrderCreated ] --> WMS | CRM | Analytics  (push, dead-letter to blob)

  On-prem ERP reached via: Logic Apps Standard + VNet integration over ExpressRoute
                           (NOT the on-prem data gateway - 2 MB write ceiling)
  Bulk nightly master-data sync: Azure Data Factory, self-hosted IR

  Cross-cutting: managed identity everywhere | Key Vault refs | private endpoints
                 one App Insights, one correlation-id, KQL alerts on run failures
```

Talk track, 30 seconds: *"Edge is APIM for identity, throttling and contract. First hop is a queue so a partner spike or an ERP outage never becomes a caller error. Orchestration is Logic Apps Standard because the connectors are the value and support needs readable run history; the one genuinely algorithmic step is a Function. Completion is broadcast on Event Grid so adding a fourth consumer is a subscription, not a code change. Every hop uses managed identity, so there is no credential anywhere in the design. One correlation ID threads APIM → Logic App → Function → Event Grid in Application Insights."*

### 10.2 "Logic Apps vs Functions vs ADF vs APIM policy vs Service Bus"

```
Is the caller waiting?          --NO--> queue/event: Service Bus (must not lose)
       |                                             Event Grid (reactive notify)
      YES                                            Event Hubs (telemetry stream)
       |
Can the gateway do it declaratively in <10ms?  --YES--> APIM policy
       |NO
Is it bulk rows on a schedule?  --YES--> Data Factory (Azure IR / self-hosted IR)
       |NO
Is the value in the connectors + must a non-dev read it?  --YES--> Logic Apps
       |NO                                                          (Standard)
Is it long-running/stateful orchestration in code?  --YES--> Durable Functions
       |NO
                                                   --------> Azure Function
```

### 10.3 "How do you secure an API on APIM?"

```
  Transport ....... TLS 1.2+, custom domain, mTLS for partners
                    (self-hosted GW: no cert renegotiation -> cert in initial handshake)
  Identify ........ subscription key (Ocp-Apim-Subscription-Key) = metering, NOT authn
  Authenticate .... validate-jwt / validate-azure-ad-token against Entra OIDC metadata
                    (JWKS cached 1h; re-pull on kid-miss max once / 5 min; clock-skew 30s)
  Authorize ....... required-claims on roles/scp + choose/when -> 403
  Protect ......... rate-limit-by-key (429) + quota-by-key (403) + ip-filter
                    + validate-content (schema) + validate-graphql-request (depth)
  Backend ......... managed identity to backend | client cert | circuit breaker rule
  Hide ............ strip Server/X-Powered-By; on-error returns a normalised envelope
  Observe ......... App Insights, sample 1-5% happy path but 100% of 4xx/5xx,
                    correlation-id on every hop
```

---

## 11. Interviewer Traps

**Trap 1 — "Premium v2 is just a better Premium."**
Most candidates say v2 supersedes classic. **Wrong.** Premium v2 does **not** support **multi-region deployment** — Premium classic is the only tier that does. v2 tiers also lose **backup/restore**, **static IP**, **self-hosted gateway** (Developer/Premium only), **Git config**, **direct Management API access** and **Event Grid events**, and there is **no automated migration path** from classic to v2. Correct answer: *"v2 for faster provisioning and cheaper VNet integration; classic Premium when you need active-active multi-region or the self-hosted gateway."*

**Trap 2 — "APIM starts returning 429 when it's overloaded."**
**Wrong.** APIM returns 429 only when *you* configured `rate-limit`/`quota`. At actual capacity it degrades like an overloaded web server: rising latency, dropped connections, timeouts. Correct answer includes: scale on the **Capacity** metric (classic) or **CPU/Memory Percentage of Gateway** (v2) at **60–70% sustained over ~30 min** — **40% on a single unit** — and clients must implement retry with backoff because a scale operation takes ~30 minutes.

**Trap 3 — "`rate-limit-by-key` gives you an exact limit."**
**Wrong**, and Microsoft says so: *"Because of the distributed nature of throttling architecture, rate limiting is never completely accurate."* Counters are **per gateway instance** and are **not** aggregated across units or regions. Bonus depth: **v2 uses a token bucket, classic uses a sliding window**, so identical counter keys at multiple scopes must carry identical limits in v2.

**Trap 4 — "Revisions and versions are basically the same thing."**
**Wrong.** Versions are consumer-visible and for breaking changes; revisions are internal working copies of one version, promoted atomically. Give the URL form — `;rev=3` appended to the **API ID**, before the query string, **not** to the URI path — and name the non-current-revision restriction (can't change Name, Type, Description, Subscription required, API version, Path, Protocols).

**Trap 5 — "Stateless Logic Apps are just faster stateful ones."**
**Wrong** in three ways: stateless runs **synchronously** (no async operation pattern, no chunking), keeps state **in memory only** so interrupted runs are **not** restored — the caller must resubmit — and it can only use **push triggers** (Request, Event Hubs, Service Bus): **no Recurrence**. It's for runs under **5 minutes** and content under **64 KB**. And **you cannot change the type after creation** — trying causes runtime errors.

**Trap 6 — "Set `functionTimeout` to 10 minutes and the HTTP function can run for 10 minutes."**
**Wrong.** **230 seconds** is the hard ceiling for an HTTP-triggered function to respond, from the Azure Load Balancer default idle timeout, regardless of `functionTimeout`. Correct answer: return `202 Accepted` with a status URL and poll — the **Durable Functions async HTTP API** pattern, where `create_check_status_response` gives you the endpoints for free.

**Trap 7 — Calling `datetime.now()` or `uuid4()` inside a Durable orchestrator.**
The orchestrator is **replayed from event history** on every checkpoint, so non-deterministic calls produce different decisions on replay and the orchestration corrupts or hangs. Use `context.current_utc_datetime` and `context.new_guid()`, and put **all** I/O in activity functions. Also: no infinite loops without `continue_as_new()`.

**Trap 8 — "Service Bus duplicate detection makes my consumer idempotent."**
**No.** Duplicate detection only suppresses identical `MessageId`s **within a finite window**, and only if you actually set a meaningful `MessageId`. Beyond the window, or on a redelivery after a lock loss, the consumer sees the message again. You still need an idempotent handler — upsert on a business key, or an idempotency table. Microsoft's own guidance: *"Designing for idempotent message handling becomes critical."*

**Trap 9 — Turning on Logic Apps trigger concurrency to "go faster".**
Turning trigger concurrency on is **irreversible**, and it silently drops `splitOn` debatching from **100,000 items to 100**. It also caps you at 25 (Consumption) or 100 (Standard) concurrent runs where you previously had unlimited. Correct answer: leave concurrency off unless you specifically need ordering or backpressure, and control throughput with the queue and consumer count instead.

**Trap 10 — Reading the request body in a policy without `preserveContent`.**
`context.Request.Body.As<JObject>()` consumes the stream; the backend then receives an empty body. Always `As<JObject>(preserveContent: true)` when the request will be forwarded. Same on the response side in outbound.

**Trap 11 — "The on-premises data gateway is how you reach on-prem."**
It's *a* way, and it has a **2 MB write / 8 MB compressed read** ceiling and a **~5 hour** credential cache. For a new build the better answers are Logic Apps Standard or Functions with **VNet integration** over ExpressRoute/VPN, or an **APIM self-hosted gateway** deployed on-prem. Naming the 2 MB number and then offering the alternative is a strong senior signal.

**Trap 12 — Storing a Key Vault secret identifier **with** the version in an APIM named value.**
It will never rotate. Store the versionless identifier, and know the rest: rotation lands in APIM **within 4 hours**, the secret must be **1–4,096 characters**, and with the Key Vault firewall on you **must** use the **system-assigned** identity plus "Allow trusted Microsoft services to bypass this firewall".

---

## 12. Rapid-Fire

Read the bold question, say the answer out loud, then check.

**APIM**

- **What are APIM's three planes** — Gateway (data), management (ARM/REST), developer portal.
- **Which tier for multi-region** — **Premium classic only**. Not Premium v2.
- **Which tiers do VNet injection** — Developer, Premium, Premium v2. Integration (outbound only): + Standard v2.
- **Which tiers do self-hosted gateway** — Developer (1 node) and Premium.
- **Which tiers have no SLA** — Developer. Basic/Standard/v2 = 99.95%; Premium multi-zone/region = 99.99%.
- **Scale units by tier** — Dev 1, Basic 2, Basic v2 10, Standard 4, Standard v2 10, Premium 12/region, Premium v2 30.
- **Estimated throughput per unit** — Dev ~500 rps, Basic ~1,000, Standard ~2,500, Premium ~4,000 — plus Microsoft's "load test, don't trust these" caveat.
- **Built-in cache size** — Dev 10 MB → Standard 1 GB → Premium 5 GB; Consumption has none.
- **When do you scale APIM** — capacity metric 60–70% sustained ~30 min; 40% if a single unit; scale op takes ~30 min.
- **What happens at capacity** — latency, dropped connections, timeouts. Not 429.
- **Policy sections** — inbound, backend, outbound, on-error. Backend holds exactly one policy.
- **What does `<base />` do** — inserts the parent scope's policies for that section; its position sets evaluation order.
- **Policy scopes** — global → product → API → operation.
- **Policy expression syntax** — C#: `@(expr)` or `@{ ...; return x; }`.
- **Read a body safely** — `context.Request.Body.As<JObject>(preserveContent: true)`.
- **Subscription key header** — `Ocp-Apim-Subscription-Key` (or `subscription-key` query param). Identifier, not authn.
- **Revision URL form** — `;rev=3` on the API ID, before the query string.
- **validate-jwt JWKS caching** — pulled hourly; on `kid` miss, re-pull at most once per 5 min.
- **validate-jwt defaults** — 401 on failure, `require-expiration-time` true, `require-signed-tokens` true, `clock-skew` 0 s.
- **rate-limit-by-key window cap** — `renewal-period` max **300 seconds**. Longer = use quota.
- **rate-limit vs quota response** — 429 vs 403.
- **Cache policies** — `cache-lookup` inbound, `cache-store` outbound; **GET only**; cached response max 2 MiB.
- **Circuit breaker lives where** — on the **backend entity**, not as a policy. Not in Consumption. One rule per backend.
- **Backend pool algorithms** — round-robin (default), weighted, priority. Max 30 backends.
- **Named value + Key Vault rotation** — within **4 hours**; identifier must be versionless; secret 1–4,096 chars.
- **Self-hosted gateway polling** — config every **10 s**, heartbeat every **60 s**, outbound TCP **443** only.
- **SOAP→REST policies** — `set-body` + `set-header SOAPAction` in, `xml-to-json` out (`kind="direct"` or `"javascript-friendly"`).
- **MCP endpoint form** — `https://<apim>.azure-api.net/<api>-mcp/mcp`; transport is **Streamable HTTP** (SSE deprecated).

**Logic Apps**

- **Consumption vs Standard in one line** — multitenant, 1 workflow, pay-per-action vs single-tenant on the Functions runtime, many workflows, VNet, local dev.
- **Stateless limits** — under 5 min, under 64 KB, push triggers only, no chunking, no run history, type fixed at creation.
- **Default retry policy** — exponential, **4** retries, scaling by 7.5 s, capped **5–45 s**. Fires on 408/429/5xx.
- **Retry policy types** — `default`, `none`, `fixed`, `exponential`. `count` 1–90.
- **HTTP timeout** — 120 s multitenant, **225 s** single-tenant.
- **Foreach concurrency** — default 20, max 50. Array items 100,000 (100 stateless).
- **Until loop** — default 60 iterations, max 5,000, default timeout PT1H.
- **The splitOn trap** — 100,000 items with concurrency **off**, drops to **100** when on; enabling concurrency is irreversible.
- **Try/catch idiom** — Scope + `runAfter: [Failed, TimedOut]` + `@result('ScopeName')` + Filter array.
- **trackedProperties cap** — 8,000 characters per action.
- **Message size** — 100 MB, chunking to 1 GB. Over that: Claim Check to Blob.
- **B2B message sizes** — AS2 v2 100 MB, AS2 v1 25 MB, X12 50 MB, EDIFACT 50 MB (multitenant).
- **On-prem gateway limits** — 2 MB write, 2 MB request / 8 MB compressed read, 1,000 data sources per cluster, ~5 h credential cache.

**Functions**

- **Which plan for new serverless work** — **Flex Consumption**. Consumption is legacy.
- **The 230-second rule** — max time an HTTP-triggered function has to respond, from the Load Balancer idle timeout, regardless of `functionTimeout`.
- **Flex Consumption instance sizes** — 512 MB, 2,048 MB, 4,096 MB. Max 1,000 instances per function group.
- **Premium max instances** — Windows 100, Linux 20–100.
- **Consumption timeout** — default 5 min, max 10 min.
- **Trigger vs binding** — trigger starts the function (one per function); input/output bindings move data in/out declaratively.
- **Service Bus lock renewal** — `maxAutoRenewDuration`, default **5 minutes**; PeekLock, auto Complete/Abandon.
- **Identity-based connection setting** — `<PREFIX>__fullyQualifiedNamespace` + a role assignment; scaling needs **Service Bus Data Owner**.
- **Durable function types** — orchestrator, activity, entity, client.
- **Durable patterns** — chaining, fan-out/fan-in, async HTTP APIs, monitoring, human interaction, aggregator.
- **Durable determinism rules** — no `datetime.now()`, no random/uuid, no I/O, always `yield` on `context.*`, `continue_as_new()` for eternal loops.
- **Durable fan-out API in Python** — `yield context.task_all([...])`; first-completed is `task_any`.
- **Durable idempotency trick** — deterministic instance ID from the business key.
- **In-process model end date** — 10 November 2026; migrate to the isolated worker model.

**Data Factory & cross-cutting**

- **Three integration runtimes** — Azure, Self-hosted, Azure-SSIS.
- **Which IR has no Data Flow** — Self-hosted (data movement + activity dispatch only).
- **Self-hosted IR facts** — Windows only, needs JRE, outbound HTTP only, scales out active-active.
- **Max DIUs per copy activity** — 256 on the Azure IR.
- **IR precedence** — self-hosted > managed-VNet Azure IR > global Azure IR.
- **ADF in CI/CD** — same IR name and type across all stages; use a shared factory with linked IRs.
- **ADF vs Logic Apps** — pipeline (bulk rows, scheduled) vs workflow (a business message, event-driven).
- **System vs user-assigned identity** — lifecycle-bound to one resource vs standalone and reusable; use user-assigned for IaC-managed estates.
- **VNet integration vs private endpoint** — outbound (I can reach private things) vs inbound (private things reach me, no public IP).
- **Key Vault reference syntax in app settings** — `@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/name/)`.
- **Claim Check in one line** — payload to Blob, URI (SAS/Valet Key) in the message; the fix for the 256 KB Service Bus and 100 MB Logic Apps ceilings.
- **Outbox on Azure** — not in Microsoft's pattern catalog; implement with Cosmos change feed or a SQL polling publisher + Service Bus duplicate detection + idempotent consumer.
- **AWS mapping, fastest version** — APIM→API Gateway, Logic Apps→Step Functions, Functions→Lambda, Service Bus→SQS+SNS, Event Grid→EventBridge, Event Hubs→Kinesis, ADF→Glue, AKS→EKS, Bicep→CloudFormation.
