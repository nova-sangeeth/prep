# The Bridge — Turning GenAI Depth Into an Integration-Role Advantage

> EY GDS — API & Integration Developer (Senior / Rank 42) prep

**What this file buys you:** every other candidate for this req can recite APIM policies and Terraform state locking. Almost none of them can say "an MCP tool is an API operation with a governance problem" and then show the APIM policy XML that governs it. EY logged `cosine similarity` and `Transformer architecture` as real Senior Consultant technical questions, listed *AI Frameworks and Tooling* as a good-to-have, put **242 Python** and **130 "Agentic"** requisitions live in India, and announced a **$1bn+ five-year Microsoft alliance (21 May 2026)** with a multiagent framework embedded in EY Canvas across **160,000 audit engagements**. This file converts your RAG/LangGraph/Azure OpenAI background into integration-architect answers so you can answer *their* questions on *your* turf without dodging.

**Depth lives elsewhere:** RAG internals, chunking, embeddings, LangGraph state machines and agent theory are already written up in [../virtusa/](../virtusa/) — specifically [09-agent-frameworks-langchain-langgraph-mcp.md](../virtusa/09-agent-frameworks-langchain-langgraph-mcp.md), [06-rag-pipelines.md](../virtusa/06-rag-pipelines.md), [10-cloud-deployment-azure-openai-mlops.md](../virtusa/10-cloud-deployment-azure-openai-mlops.md). Do **not** re-read them for EY. This file is only the bridge.

## Table of Contents

| § | Section | Qs |
|---|---------|----|
| 1 | [The Reframe — the mapping table](#1-the-reframe--the-mapping-table) | table |
| 2 | [MCP for Integration Architects](#2-mcp-for-integration-architects) | Q1–Q8 |
| 3 | [APIM as the AI Gateway](#3-apim-as-the-ai-gateway) | Q9–Q14 |
| 4 | ["How Would EY Use AI in Integration Work?"](#4-how-would-ey-use-ai-in-integration-work) | Q15–Q19 |
| 5 | [Designing an Enterprise Agentic Integration Layer](#5-designing-an-enterprise-agentic-integration-layer) | Q20–Q26 |
| 6 | [Azure OpenAI / Foundry Operational Reality](#6-azure-openai--foundry-operational-reality) | Q27–Q30 |
| 7 | [Interviewer Traps](#7-interviewer-traps) | 9 |
| 8 | [30-Second Whiteboard Versions](#8-30-second-whiteboard-versions) | 3 |
| 9 | [12 Rehearsed Pivots](#9-12-rehearsed-pivots) | 12 |
| 10 | [Rapid Fire](#10-rapid-fire) | 34 |

---

## 1. The Reframe — the mapping table

**The whole file in one idea:** an agent platform *is* an integration platform. The nouns changed; the failure modes didn't. Memorise this table — it is what lets you answer "tell me about your integration experience" with a GenAI story and have it land as an integration answer.

| What you built (GenAI) | What EY calls it (integration) | The sentence that connects them |
|---|---|---|
| Tool / function calling | API invocation against a typed contract | "A tool definition is an OpenAPI operation with a worse spec format — same schema, same auth, same 429s." |
| MCP server | API gateway + service registry, for models instead of apps | "MCP is a service-discovery and invocation protocol whose client happens to be non-deterministic." |
| RAG ingestion pipeline | ETL / EAI batch integration with CDC | "Extract from SharePoint/SAP, transform to a canonical chunk model, load to a sink, reconcile on a watermark. That's an integration pipeline with an embedding step." |
| Vector DB upsert | Idempotent sink write keyed on a natural/business key | "Upsert by `doc_id#chunk_idx` is the Idempotent Consumer pattern; re-ingest is a replay." |
| LangGraph / agent orchestration | Workflow orchestration — Logic Apps Standard, Durable Functions | "A graph with nodes, edges, conditional routing and persisted state is a stateful workflow. Durable Functions is the same thing with an Azure Storage-backed history." |
| LangGraph checkpointer | Orchestration history / run history | "Both replay from a durable event log to survive a host restart. Durable Functions replays the orchestrator; LangGraph rehydrates from the checkpoint." |
| Agent retries a failed tool | Retry + Circuit Breaker | "Unbounded agent retries against a sick backend is exactly why Microsoft says pair Retry with Circuit Breaker." |
| Per-user token budget | `rate-limit-by-key` + `quota-by-key` | "Cost control on a token is throttling on a counter-key. Same policy, different unit." |
| Guardrails / structured-output validation | `validate-content` + canonical-model validation | "Validating LLM JSON against a Pydantic model is schema validation at the boundary — identical to rejecting a malformed EDI 850." |
| Prompt injection from a retrieved doc | Untrusted payload crossing a trust boundary | "This is not an ML problem. A third party wrote bytes that my privileged executor obeyed. That's an integration security defect." |
| Token streaming over SSE | Asynchronous Request-Reply | "Long-running op, 202 + polling or a stream. Durable Functions returns 202 with `Location: statusQueryGetUri`." |
| Human-in-the-loop approval | Human Interaction pattern | "Durable Functions `wait_for_external_event` + a durable timer, or a Logic Apps approval action. Same escalation-on-timeout design." |
| Eval / regression harness | Contract testing against the OpenAPI spec | "Golden-set evals are non-deterministic contract tests. The pass criterion is a score band, not equality." |
| Cost per LLM call | Per-transaction cost governance / chargeback | "`llm-emit-token-metric` with a `Subscription ID` dimension is chargeback telemetry." |
| Azure OpenAI / embedding endpoint | Just another rate-limited HTTP backend | "It 429s with a `Retry-After` that can be a day long. It belongs behind a backend pool with a circuit breaker like any flaky partner API." |

**Say this out loud when they ask "you're a GenAI person, why integration?":** *"I've spent three years being the person who makes enterprise systems callable — first by applications, then by models. The hard parts were never the model: they were idempotency, retries, schema drift, auth to downstream systems and cost governance. That's integration work with a different caller."*

---

## 2. MCP for Integration Architects

### Q1. What is MCP, explained to an integration architect who has never heard of it?
`[MEDIUM]`

**Answer:** MCP — Model Context Protocol — is an open client/server protocol that lets an LLM host discover and invoke capabilities exposed by a server. Messages are **JSON-RPC 2.0**, UTF-8 encoded. Architecturally it is the same shape as any service-registry-plus-invocation protocol: the client calls `tools/list` to discover, then `tools/call` to invoke, and the server returns a result. The novelty isn't the wire format — it's that the caller is a model, so the contract has to be self-describing enough for something non-deterministic to pick the right operation.

Four components: **host** (the LLM app — Copilot, Claude, Copilot Studio), **client** (one 1:1 connection per server, living inside the host), **server** (exposes capabilities), **transport**.

Three server primitives, and the control axis is the part interviewers never know:

| Primitive | Who controls it | Integration analogue |
|---|---|---|
| **Tools** | Model-controlled | An API operation the model may invoke |
| **Resources** | Application-controlled | Read-only content the host attaches as context (a file, a record) |
| **Prompts** | User-controlled | A saved template the user picks — a slash command |

**If they push back — *"so it's just REST with extra steps?"*:** For a deterministic client, yes, and I'd keep REST. MCP earns its place when the client is a model: it gives you runtime discovery (`tools/list`), a schema the model can reason over, and a session, so you don't hand-write a bespoke adapter per host application.

---

### Q2. What transports does MCP define, and which one would you put in front of an enterprise API?
`[MEDIUM]`

**Answer:** The spec defines exactly two standard transports: **stdio** (the client launches the server as a subprocess and speaks newline-delimited JSON-RPC over stdin/stdout) and **Streamable HTTP**. For anything enterprise, it's Streamable HTTP — stdio is for local developer tooling on the same machine. The older **HTTP+SSE** transport (separate `/sse` and `/messages` endpoints) is **deprecated as of protocol version `2024-11-05`** and replaced by Streamable HTTP.

Streamable HTTP mechanics worth naming:

- **One** HTTP endpoint path — e.g. `https://example.com/mcp` — supporting both **POST** and **GET**.
- Client POSTs each JSON-RPC message and **MUST** send `Accept: application/json, text/event-stream`.
- If the body is a notification or a response, the server returns **202 Accepted** with no body.
- If it's a request, the server returns either `application/json` (one object) or `text/event-stream` (an SSE stream that ends with the response).
- Optional session: server returns `Mcp-Session-Id` on the `InitializeResult`; the client echoes it on every later request. Server may return **404** to kill a session, which forces the client to re-`initialize`. Client sends **HTTP DELETE** to end one.
- `MCP-Protocol-Version: 2025-06-18` header on every request after initialisation; absent ⇒ server assumes `2025-03-26`; invalid ⇒ **400**.
- Resumability: server puts an `id` on SSE events, client reconnects with `Last-Event-ID` — this is per-stream replay, i.e. an at-least-once redelivery window.
- Security: servers **MUST** validate the `Origin` header (DNS-rebinding defence) and local servers **SHOULD** bind to 127.0.0.1, not 0.0.0.0.

**If they push back — *"why not just SSE, it's simpler?"*:** Because SSE is one-way and needed a second endpoint for client→server messages, which broke behind load balancers and made session affinity mandatory. Streamable HTTP collapses it to one endpoint, allows a plain JSON response when no streaming is needed, and gives you resumability via `Last-Event-ID`. Saying "we'd use SSE" in 2026 dates you by a year.

---

### Q3. Why would an enterprise put an MCP server in front of APIs it already has?
`[MEDIUM]`

**Answer:** Because otherwise every agent platform in the organisation builds its own adapter to the same SAP or ServiceNow API, and you get N×M integration sprawl with N copies of the auth logic. An MCP server in front of existing REST APIs is a **façade with a machine-readable contract** — one place to publish the tool catalogue, one place to enforce authZ per tool, one place to emit audit. It is the same argument that justified an ESB in 2010 and an API gateway in 2018, applied to a new class of consumer.

The second reason is **scope reduction**. Your CRM API has 300 operations; you expose 6 as tools, with narrower schemas and pre-bound tenant filters. The agent physically cannot call `DELETE /customers/{id}` because it was never published.

**If they push back — *"couldn't the agent just read the OpenAPI spec?"*:** It can, and for a small internal API that's fine. It breaks at enterprise scale for three reasons: OpenAPI specs describe hundreds of operations with no notion of "which of these should a model be allowed to pick"; there's no runtime authorisation story per operation; and specs drift from reality. An MCP server is a curated, governed subset — a published product, not raw documentation.

---

### Q4. How does authentication and authorisation work for a remote MCP server?
`[HARD]`

**Answer:** The MCP server is an **OAuth 2.1 resource server** — it never issues tokens, it validates them. The spec normatively references OAuth 2.1 (`draft-ietf-oauth-v2-1-13`), **RFC 8414** Authorization Server Metadata, **RFC 7591** Dynamic Client Registration, **RFC 9728** Protected Resource Metadata, and **RFC 8707** Resource Indicators. Authorization is optional for MCP overall, but if you're on HTTP you follow this.

The discovery dance, which is the bit worth reciting:

1. Client calls the MCP endpoint with no token → server returns **401** with a `WWW-Authenticate` header pointing at the resource metadata URL (RFC 9728 §5.1).
2. Client fetches `/.well-known/oauth-protected-resource` → gets `authorization_servers`.
3. Client fetches `/.well-known/oauth-authorization-server` from the AS (RFC 8414).
4. Optional **Dynamic Client Registration** (`POST /register`) if the client has no client_id.
5. Authorization Code + **PKCE** — mandatory — with the **`resource` parameter (RFC 8707)** carrying the MCP server's canonical URI, on **both** the authorization request and the token request.
6. Client sends `Authorization: Bearer <token>` on **every** HTTP request. Tokens **MUST NOT** appear in the query string.

Three hard rules to state proactively, because they're what separates a senior answer:

- The server **MUST validate the audience** — that the token was issued *for it*. Accepting a token minted for another service is the classic OAuth boundary break.
- **Token passthrough is explicitly forbidden.** If the MCP server calls an upstream API, it acts as an OAuth client to that API and obtains a *separate* token. It must not forward the client's token.
- Error codes: **401** missing/invalid token, **403** insufficient scope, **400** malformed request.

**If they push back — *"how do you do that in Azure?"*:** APIM in front of the MCP server, `validate-azure-ad-token` on the inbound leg, and **credential manager** (`get-authorization-context` + `set-header`) or a **managed identity** on the outbound leg — so the token the agent presented never reaches SAP. See [Auth & Security](06-auth-and-security.md) for the full OAuth2/OIDC/mTLS treatment.

---

### Q5. Show me an MCP server that wraps an existing REST API.
`[MEDIUM]`

**Answer:** In Python, the reference SDK gives you the transport and JSON-RPC plumbing; you write typed functions. The integration content is in the decorated functions — auth to the downstream, timeouts, and an idempotency key on anything that mutates.

```python
# pip install "mcp[cli]" httpx
import os
import uuid
from typing import Annotated

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("orders-mcp", stateless_http=False)

_client = httpx.AsyncClient(
    base_url=os.environ["ORDERS_API_BASE"],
    timeout=httpx.Timeout(10.0, connect=3.0),
    headers={"User-Agent": "orders-mcp/1.0"},
)


async def _bearer() -> str:
    """Client-credentials token for the DOWNSTREAM api. Never the caller's token."""
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(
            f"https://login.microsoftonline.com/{os.environ['TENANT_ID']}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["CLIENT_ID"],
                "client_secret": os.environ["CLIENT_SECRET"],
                "scope": f"{os.environ['ORDERS_API_APP_ID']}/.default",
            },
        )
        r.raise_for_status()
        return r.json()["access_token"]


@mcp.tool()
async def get_order(
    order_id: Annotated[str, Field(description="Order number, e.g. SO-10231")],
) -> dict:
    """Read a single sales order. Safe, idempotent, no side effects."""
    token = await _bearer()
    r = await _client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()


@mcp.tool()
async def hold_order(
    order_id: Annotated[str, Field(description="Order number to place on credit hold")],
    reason: Annotated[str, Field(max_length=200)],
) -> dict:
    """MUTATING. Placing a hold is retried by agents, so it carries an idempotency key."""
    token = await _bearer()
    r = await _client.post(
        f"/orders/{order_id}/holds",
        json={"reason": reason},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid5(uuid.NAMESPACE_URL, f"hold:{order_id}:{reason}")),
        },
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    # Streamable HTTP: single endpoint at /mcp supporting POST and GET.
    mcp.run(transport="streamable-http")
```

**The line to say while you write it:** *"Note the deterministic `Idempotency-Key` derived from the business inputs. An agent that times out will re-issue this call — non-deterministic callers make idempotency mandatory rather than nice-to-have."*

**If they push back — *"why not expose all 40 operations?"*:** Tool-selection accuracy degrades with catalogue size, and every published operation is attack surface. I publish the smallest set that satisfies the use case and version the catalogue like a product.

---

### Q6. Can Azure API Management host or front an MCP server? Be specific.
`[HARD]`

**Answer:** Yes, natively, and this is the strongest single thing you can bring up unprompted in this interview. APIM's built-in AI gateway can **expose a REST API it already manages as a remote MCP server** — API operations become MCP tools — and can also **front an existing MCP server** hosted elsewhere (a LangServe server, a Logic App, a Function App) for governance.

The specifics:

- **Tiers:** Developer, Basic, Basic v2, Standard, Standard v2, Premium, Premium v2. **Not Consumption.** Also works on the **self-hosted gateway**.
- **Endpoint format:** `https://<apim-name>.azure-api.net/<api-name>-mcp/mcp`.
- **Only HTTP-compatible APIs** can be exposed — other API types in APIM cannot.
- **Tools only.** APIM does **not** support MCP resources or prompts.
- **Not supported in APIM workspaces.**
- Policies apply to **all** operations exposed as tools on that server — there is no per-tool policy granularity yet.
- **Global-scope policies evaluate before MCP-server-scope policies.**
- MCP servers can be added to **Products**, so subscription-based access control works normally.
- Manageable by REST API, ARM, **Bicep**, Azure CLI and **Terraform**.

Two operational gotchas that will make you sound like you've actually shipped it:

1. **Never touch `context.Response.Body` in an MCP server policy.** It triggers response buffering, which breaks the streaming transport.
2. If Application Insights / Azure Monitor diagnostic logging is on at the **All APIs** scope, set **"Number of payload bytes to log" for Frontend Response to `0`** — otherwise response-body logging breaks MCP streaming. Log payloads selectively at API scope instead.

Governing policy on the MCP server — this is verbatim-shaped and safe to write on a whiteboard:

```xml
<policies>
  <inbound>
    <base />
    <validate-azure-ad-token tenant-id="{{tenant-id}}"
                             header-name="Authorization"
                             failed-validation-httpcode="401"
                             failed-validation-error-message="Unauthorized. Access token is missing or invalid.">
      <client-application-ids>
        <application-id>{{agent-client-app-id}}</application-id>
      </client-application-ids>
    </validate-azure-ad-token>
    <ip-filter action="allow">
      <address-range from="10.20.0.0" to="10.20.255.255" />
    </ip-filter>
    <rate-limit-by-key calls="60"
                       renewal-period="60"
                       counter-key="@(context.Request.Headers.GetValueOrDefault(&quot;agent-id&quot;, context.Request.IpAddress))"
                       remaining-calls-header-name="X-RateLimit-Remaining" />
    <trace source="mcp-governance" severity="information">
      <message>MCP tool invocation</message>
      <metadata name="agent-id" value="@(context.Request.Headers.GetValueOrDefault(&quot;agent-id&quot;, &quot;n/a&quot;))" />
      <metadata name="subscription-id" value="@(context.Subscription?.Id ?? &quot;anon&quot;)" />
    </trace>
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
```

**If they push back — *"is it GA?"*:** The core capability is documented like a GA feature across those seven tiers with no preview banner, and MCP servers in Products, tool observability, MCP versioning and Bicep support all shipped GA. Individual sub-features move fast — there's an *AI Gateway* release channel for early access — so I'd confirm status against Learn before committing it to a design doc rather than quote a status from memory.

---

### Q7. MCP vs REST vs GraphQL vs gRPC as integration surfaces — when do you pick which?
`[MEDIUM]`

**Answer:** They're not competitors; they're different consumers of the same backend. I'd keep **one** canonical service and project it onto whichever surfaces have consumers.

| Surface | Caller | Contract | Discovery | Picks it when |
|---|---|---|---|---|
| **REST/OpenAPI** | App code, partners | OpenAPI 3.x | Static spec | Default. Cacheable, proxy-friendly, everyone speaks it |
| **SOAP/WSDL** | Legacy ERP, banking, B2B | WSDL + XSD | WSDL | The counterparty mandates it. WS-Security, strict typing, existing estate |
| **GraphQL** | Rich clients, BFF | SDL schema | Introspection | Client-shaped over-fetching is the actual problem; one round trip across many entities |
| **gRPC** | Internal service-to-service | protobuf IDL | Reflection | Low latency, high volume, streaming, polyglot internal mesh |
| **Events (Service Bus / Event Grid / Kafka)** | Async consumers | Schema registry | Topic catalogue | The producer shouldn't know or wait for the consumer |
| **MCP** | LLM hosts / agents | JSON Schema per tool | `tools/list` at runtime | The caller is a model that must *choose* the operation at runtime |

The distinguishing sentence: **REST and GraphQL assume the caller knows what it wants; MCP assumes the caller has to be told what's available and then decide.** That single difference is why MCP needs runtime discovery and why per-tool authorisation matters more than per-endpoint authorisation.

**If they push back — *"so is MCP going to replace REST?"*:** No. Every APIM MCP server is *backed by* a REST API. MCP is a projection, not a replacement. The canonical model and the REST contract are still the source of truth; MCP is one more binding, like a SOAP façade over a REST service.

---

### Q8. How do agents discover which MCP servers exist across a large organisation?
`[MEDIUM]`

**Answer:** You need a registry, or you've rebuilt the ESB spaghetti with a new protocol. On Azure that's **Azure API Center**: it registers and catalogues MCP servers — both those exposed in APIM and those hosted outside it — and you can stand up the **API Center portal** as a private enterprise MCP-server registry for developers. Microsoft also ships an API Center data-plane MCP server, so the registry itself is discoverable as a tool.

The governance framing EY will recognise: this is API lifecycle management applied to tools. Registration, ownership, versioning, deprecation policy, environment (dev/UAT/prod), and a documented consumer list — the same metadata you'd hold for a managed API.

**If they push back — *"what if the tools aren't in Azure?"*:** API Center registers external MCP servers too, and APIM's "expose an existing MCP server" mode lets you front a non-Azure server so it inherits the same JWT validation, rate limiting and App Insights telemetry. The control plane is the gateway, not the hosting location.

---

## 3. APIM as the AI Gateway

> This section is the single most impressive unprompted thing you can raise in an EY integration interview: it proves you're an integration engineer who understands AI workloads, not an AI person guessing at integration.

### Q9. What does "APIM as an AI gateway" actually mean? Name the policies.
`[HARD]`

**Answer:** It means APIM ships purpose-built policies for LLM backends, so token consumption becomes a first-class governed resource the way requests-per-second always was. Four policies, exact element names:

| Policy | What it does | Tiers | Section |
|---|---|---|---|
| `llm-token-limit` | Rate-limits and/or quotas **tokens** per counter-key; 429 on rate, **403 on quota** | Developer, Basic, Basic v2, Standard, Standard v2, Premium, Premium v2 | inbound |
| `llm-emit-token-metric` | Emits token counts to Application Insights with custom dimensions | All tiers | inbound |
| `llm-semantic-cache-lookup` / `-store` | Vector-proximity cache of completions | All tiers | inbound / outbound |
| `llm-content-safety` | Azure AI Content Safety moderation + prompt shield; blocks with **403** | Developer, Basic, Basic v2, Standard, Standard v2, Premium, Premium v2 | inbound, outbound |

All four work with **OpenAI Chat Completions/Responses**, **Anthropic Messages API** (v2 tiers only), and **Google Vertex AI** schemas. `llm-content-safety` also covers **MCP tool** requests/responses and **A2A Agent APIs** managed in APIM.

**If they push back — *"is this different from `rate-limit-by-key`?"*:** Yes, and the difference matters. `rate-limit-by-key` counts *calls*; a single call can cost 200 tokens or 200,000. `llm-token-limit` counts the actual unit of cost, and it can pre-estimate prompt tokens to reject an oversized prompt before it ever hits the backend.

---

### Q10. Show me the AI gateway policy for token limiting and cost telemetry.
`[HARD]`

**Answer:** Two policies, both inbound, both keyed on the caller's subscription so cost lands on the right cost centre.

```xml
<policies>
  <inbound>
    <base />

    <!-- Cache first: a hit costs zero tokens. Threshold 0.05; above 0.2 risks mismatch. -->
    <llm-semantic-cache-lookup score-threshold="0.05"
                               embeddings-backend-id="embeddings-backend"
                               embeddings-backend-auth="system-assigned"
                               ignore-system-messages="true">
      <vary-by>@(context.Subscription.Id)</vary-by>
    </llm-semantic-cache-lookup>

    <!-- Guard the backend if the cache is unavailable. -->
    <rate-limit-by-key calls="120" renewal-period="60" counter-key="@(context.Subscription.Id)" />

    <!-- Token rate limit AND a monthly quota, on one counter-key. -->
    <llm-token-limit counter-key="@(context.Subscription.Id)"
                     tokens-per-minute="50000"
                     token-quota="100000000"
                     token-quota-period="Monthly"
                     estimate-prompt-tokens="true"
                     retry-after-header-name="Retry-After"
                     remaining-tokens-header-name="X-Tokens-Remaining"
                     remaining-quota-tokens-header-name="X-Quota-Tokens-Remaining"
                     tokens-consumed-header-name="X-Tokens-Consumed" />

    <!-- Chargeback telemetry. Max 5 custom dimensions. -->
    <llm-emit-token-metric namespace="EYIntegrationAI">
      <dimension name="Subscription ID" />
      <dimension name="API ID" />
      <dimension name="agent-id" value="@(context.Request.Headers.GetValueOrDefault(&quot;agent-id&quot;, &quot;unattributed&quot;))" />
    </llm-emit-token-metric>

    <!-- Moderation + prompt-injection shield on the way in. -->
    <llm-content-safety backend-id="content-safety-backend" shield-prompt="true">
      <categories output-type="EightSeverityLevels">
        <category name="Hate" threshold="4" />
        <category name="Violence" threshold="4" />
        <category name="SelfHarm" threshold="4" />
        <category name="Sexual" threshold="4" />
      </categories>
    </llm-content-safety>
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <llm-semantic-cache-store duration="300" />
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
```

Details to drop while explaining it:

- **429** when `tokens-per-minute` is exceeded; **403** when `token-quota` is exceeded. Different codes, different client handling.
- `token-quota-period` values are exactly `Hourly | Daily | Weekly | Monthly | Yearly`, and the window start is the UTC timestamp truncated to that unit.
- **Counters are per-gateway.** They are *not* aggregated across a multi-region deployment or across workspace gateways. Microsoft says so explicitly.
- **v2 tiers use a token-bucket algorithm; classic tiers use a sliding window.** If you configure the same `counter-key` at multiple scopes in v2, the `tokens-per-minute` values must be identical or behaviour is unpredictable.
- With `stream: true`, prompt **and** completion tokens are always *estimated* regardless of `estimate-prompt-tokens`. Image inputs are overcounted at a max of **1200 tokens** each when streaming or estimating.
- `llm-emit-token-metric`: max **5 custom dimensions** (Azure Monitor allows 10 dimension keys per metric; APIM reserves 5 for defaults). Each dimension is capped at **100 unique values** and each namespace at **1,000 active time series**; beyond that, data is **silently discarded**. Region-wide cap is 50,000 active time series per subscription per 12 hours.
- Streaming OpenAI responses omit usage unless the client sets `include_usage: true` — without it your token metrics are blank.
- Default dimension names usable with no `value`: API ID, Operation ID, Product ID, User ID, Subscription ID, Location, Gateway ID, Backend ID.

**If they push back — *"is the token limit exact?"*:** No, and I'd say so before they ask. Exact consumption isn't known until the backend responds, so concurrent requests can briefly overshoot; once responses land, subsequent calls are blocked until the window resets. The remaining-quota header is an estimate that gets more accurate as you approach the limit.

---

### Q11. How do you load-balance across multiple Azure OpenAI deployments, and drain PTU before spilling to pay-as-you-go?
`[HARD]`

**Answer:** Backend **pool** entity in APIM with **priority-based** load balancing. Priority group 1 holds the PTU deployment; priority group 2 holds the pay-as-you-go deployments, weighted. APIM only uses a lower-priority group when **every** backend in the higher-priority groups has tripped its circuit breaker. So the PTU deployment absorbs traffic until it starts 429-ing, the breaker trips, and traffic spills. Pool limit is **30 backends**.

```bicep
param apimName string
param location string = resourceGroup().location

resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimName
}

resource ptuBackend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'aoai-ptu-eastus'
  properties: {
    url: 'https://aoai-ptu-eastus.openai.azure.com/openai'
    protocol: 'http'
    credentials: {
      // Managed identity; no key anywhere. Assign "Cognitive Services User" on the AOAI resource.
      authorization: {
        scheme: 'Bearer'
        parameter: ''
      }
    }
    circuitBreaker: {
      rules: [
        {
          name: 'ptu-429-breaker'
          failureCondition: {
            count: 5
            interval: 'PT1M'
            errorReasons: [
              'Server errors'
            ]
            statusCodeRanges: [
              {
                min: 429
                max: 429
              }
              {
                min: 500
                max: 599
              }
            ]
          }
          tripDuration: 'PT1M'
          acceptRetryAfter: true
        }
      ]
    }
  }
}

resource payGoBackend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'aoai-paygo-swedencentral'
  properties: {
    url: 'https://aoai-paygo-swedencentral.openai.azure.com/openai'
    protocol: 'http'
    circuitBreaker: {
      rules: [
        {
          name: 'paygo-breaker'
          failureCondition: {
            count: 10
            interval: 'PT1M'
            errorReasons: [
              'Server errors'
            ]
            statusCodeRanges: [
              {
                min: 429
                max: 429
              }
            ]
          }
          tripDuration: 'PT30S'
          acceptRetryAfter: true
        }
      ]
    }
  }
}

resource aoaiPool 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'aoai-pool'
  properties: {
    description: 'PTU first, spill to pay-as-you-go'
    type: 'Pool'
    pool: {
      services: [
        {
          id: ptuBackend.id
          priority: 1
          weight: 1
        }
        {
          id: payGoBackend.id
          priority: 2
          weight: 1
        }
      ]
    }
  }
  dependsOn: [
    ptuBackend
    payGoBackend
  ]
}
```

Then in the API policy: `<set-backend-service backend-id="aoai-pool" />`.

Four facts that make this a senior answer:

- **`acceptRetryAfter: true` exists specifically because Azure OpenAI returns 429 with a `Retry-After` that can be as long as a day.** Microsoft documents that exact case. Without this flag your breaker resets on its own schedule and slams straight back into a backend that told you to wait 24 hours.
- **Only one circuit-breaker rule per backend** is supported.
- **Circuit breaker is not supported in the Consumption tier.**
- Load balancing and breaker tripping are **approximate** — gateway instances don't synchronise state.

**If they push back — *"why not just use Azure OpenAI's own spillover?"*:** Provisioned deployments do support spillover to a standard deployment in the same Foundry resource, per-request via the `x-ms-spillover-deployment` header. I'd use that when the spill target is in the same resource and I want it invisible. I use APIM's pool when the targets span resources, regions or subscriptions, or when I need one place that also does token quota, chargeback and content safety — which is the usual enterprise case.

---

### Q12. Semantic caching — when is it a good idea and when is it dangerous?
`[MEDIUM]`

**Answer:** Good when prompts repeat with paraphrase and answers are non-personalised — FAQ bots, doc Q&A over a static corpus, classification. Dangerous the moment the response depends on *who* is asking or *when*, because semantic caching returns responses based on **similarity, not equality**, so it can surface an answer that's correct for someone else and wrong for this caller.

Configuration facts:

- `score-threshold` is **required**, ranges 0.0–1.0, and **lower values require higher semantic similarity**. Microsoft's guidance: start around **0.05**; **above 0.2 risks cache mismatch**.
- `embeddings-backend-auth` **must** be `system-assigned`.
- `ignore-system-messages="true"` is recommended — otherwise a system-prompt change fragments the cache.
- Requires an external RediSearch-compatible cache and a paired `llm-semantic-cache-store` in outbound.
- **Always `vary-by` a user or tenant identifier** to prevent cross-user cache leakage.
- Microsoft recommends putting a `rate-limit` **immediately after** the lookup, so a cache outage doesn't dump full load on the backend.
- Consider pairing with `llm-content-safety` prompt shield — a poisoned prompt that gets cached is served repeatedly.

**If they push back — *"what's the hit rate?"*:** I wouldn't quote one; it's entirely corpus-dependent. I'd instrument it — emit a cache-hit dimension via `llm-emit-token-metric` and tune `score-threshold` against measured hit/miss ratio and a human-reviewed sample of hits, because the failure mode is a *plausible wrong answer*, not an error.

---

### Q13. How do you observe and troubleshoot an AI integration in production?
`[MEDIUM]`

**Answer:** Same three pillars as any integration, with one extra unit of measure. Correlation IDs on the way in, structured telemetry, and a token dimension.

- **Correlation:** W3C `traceparent` / App Insights `operation_Id`, propagated end to end. Microsoft's own MCP guidance says to include correlation IDs in request headers to track requests across systems. In Logic Apps, `trackedProperties` (capped at 8,000 characters per action) carries business identifiers into diagnostics.
- **APIM `trace` policy** with `<metadata>` entries writes into the test console, App Insights telemetry and resource logs — the docs literally demo capturing an `agent-id` header.
- **Token metrics** via `llm-emit-token-metric` with a `Subscription ID` dimension gives you cost-per-consumer without touching billing exports.
- **APIM diagnostic logs capture at most 8,192 bytes** of request/response payload — plan for truncation.
- KQL for the classic "find the failures" question:

```kusto
// Failed gateway calls in the last 24h, grouped by API and backend response code
ApiManagementGatewayLogs
| where TimeGenerated > ago(24h)
| where ResponseCode >= 400
| summarize Failures = count(),
            p95BackendMs = percentile(BackendTime, 95)
          by ApiId, OperationId, ResponseCode, BackendId
| order by Failures desc
```

**If they push back — *"a request is slow, where do you look first?"*:** Split total latency into gateway time vs backend time — `ApiManagementGatewayLogs` gives you both. If backend time dominates and the code is 429, it's quota; if gateway time dominates, it's policy cost — usually a synchronous content-safety call or an embeddings lookup on the cache path.

---

### Q14. What are the limits of putting policy in the gateway rather than the service?
`[MEDIUM]`

**Answer:** Three real ones, and stating them unprompted signals judgement rather than gateway-worship.

1. **Granularity.** APIM MCP-server policies apply to **all** operations exposed as tools — there's no per-tool policy yet. If tool A needs a 10/min limit and tool B needs 1000/min, you split them into two MCP servers or push the distinction into a policy expression.
2. **Accuracy.** Rate limits, token limits and circuit breakers are all approximate because gateway instances don't synchronise. That's acceptable for cost control, not for a hard financial limit — a hard limit belongs in the service, transactionally.
3. **Capacity behaviour.** When APIM itself saturates it does **not** throttle gracefully; it degrades like an overloaded web server — latency climbs, connections drop, timeouts. Microsoft's guidance is to scale when the capacity metric sustains **60–70%** (**40%** if you're on a single unit, because capacity has to be reserved for guest OS updates), with evaluation windows of 30 minutes or longer. A scale operation takes roughly 30 minutes.

**If they push back — *"so what belongs where?"*:** Gateway owns cross-cutting concerns that must be uniform and auditable — authN, coarse authZ, throttling, quota, content safety, telemetry, routing, breaker. The service owns business invariants, fine-grained authZ that needs domain data, and anything that must be transactionally exact.

---

## 4. "How Would EY Use AI in Integration Work?"

> This is a near-certain question given EY's own AI push. It is also the one where candidates either sound like a vendor brochure or sound useful. The structure that works: **name the use case, name the artefact it produces, name the limit.**

### Q15. Where does AI genuinely help in an integration delivery project?
`[MEDIUM]`

**Answer:** Five places, ranked by how much time they actually save on a Big-4 delivery engagement.

| Use case | Input → output | What it saves | The honest limit |
|---|---|---|---|
| **Legacy comprehension** | WSDL/XSD, COBOL copybooks, ESQL, undocumented stored procs → plain-English behaviour spec | The single biggest cost on any migration is *understanding* the existing estate | Output is a hypothesis. It must be validated against traffic captures or test runs before anyone codes to it |
| **Canonical-model mapping** | Source schema + target schema → draft field mapping with confidence | Weeks of mapping-spreadsheet work on an SAP/Workday/ServiceNow integration | It will confidently map `ship_dt` to `delivery_date` when the business meaning differs. Every mapping needs an SME sign-off gate |
| **Test generation from OpenAPI** | OpenAPI 3.x → contract tests, negative cases, boundary values, fuzz payloads | Coverage on the paths humans skip: 4xx bodies, enum edges, pagination cursors | It generates tests against the *spec*, not the implementation. Passing tests can still mean a wrong spec |
| **Incident/log triage** | Error text + run history + past tickets → probable cause + runbook link | First-line triage on run-and-maintain work, which is a lot of GDS delivery | Correlation not causation. Must never auto-remediate production without an approval gate |
| **Spec generation** | Existing controller code / traffic samples → OpenAPI draft | Gets undocumented internal APIs into APIM and API Center | Draft only; a generated spec that goes into a Product becomes a contract you now owe consumers |

**If they push back — *"give me the one you'd do first on a new engagement"*:** Legacy comprehension, because it's the only one where the AI is doing something the team genuinely cannot parallelise. Mapping and test generation are accelerators for work you'd do anyway; comprehension unblocks the estimate itself.

---

### Q16. "Self-healing pipelines" — is that real or marketing?
`[HARD]`

**Answer:** Partly real, and the honest split is by blast radius. I'd put automated remediation into three tiers.

- **Tier 1 — safe to automate.** Transient-fault retries with backoff and jitter, replaying a dead-lettered message after the downstream is confirmed healthy, restarting a stuck consumer, re-running an idempotent ADF copy activity. These are deterministic rules; you don't need a model, and calling them "self-healing" is generous.
- **Tier 2 — AI-assisted, human-approved.** Classify a DLQ backlog by failure signature, propose the remediation, and require an approval before it executes. Durable Functions' human-interaction pattern or a Logic Apps approval action is the right implementation.
- **Tier 3 — do not automate.** Anything that mutates business data, changes a mapping, or edits config in production. A model that "fixes" a field mapping at 2 a.m. has just made an undetected data-quality incident.

**The limit to state:** an agent that can remediate is an agent with write access to production. The security question stops being about the model and becomes about privilege — least privilege per tool, an audit trail on every invocation, and an approval gate on anything irreversible.

**If they push back — *"where would you draw the line at EY?"*:** At reversibility. If the action is reversible and idempotent, automate it and log it. If it isn't, the agent's job ends at producing a proposed change plus evidence, and a human presses go.

---

### Q17. How would you use AI to migrate a MuleSoft/Boomi/IBM ACE estate to Azure Integration Services?
`[HARD]`

**Answer:** Four phases, and AI is heavily used in the first two and barely in the last two.

1. **Inventory & comprehension (AI-heavy).** Parse every flow/process/message-flow export into a structured inventory: triggers, connectors, transformations, error handlers, external endpoints. Have the model produce a behaviour summary per flow and a dependency graph. Output is a spreadsheet plus a graph, both human-reviewed.
2. **Classification & disposition (AI-assisted).** Bucket each flow: retire, re-platform as-is, re-architect, or leave. The model proposes; the architect decides. Complexity scoring here drives the estimate, which is the commercial deliverable.
3. **Target design (human).** Pattern-by-pattern mapping: a synchronous HTTP proxy flow becomes an APIM API; an orchestration with connectors becomes a **Logic Apps Standard** workflow using built-in service-provider connectors; custom transformation logic becomes an **Azure Function**; a pub/sub fan-out becomes a **Service Bus topic** with SQL-filter subscriptions; a reactive resource trigger becomes **Event Grid**; high-volume telemetry becomes **Event Hubs** (which exposes a Kafka-compatible endpoint, and that's the answer they want for a Kafka migration).
4. **Build, test, cut over (human + generated tests).** AI generates the regression suite from the captured request/response pairs of the legacy flows. That's the highest-value AI contribution in this phase — a golden corpus you diff old vs new against.

**If they push back — *"can't AI just convert the code?"*:** For simple mediation flows it produces a plausible first draft that a developer then rewrites. For anything with stateful error handling, batching, or B2B semantics, transliteration is a trap — the platforms have different durability guarantees. I'd rather have AI produce an accurate *specification* of what the old flow did and hand that to a developer than get generated Logic Apps JSON I can't trust.

---

### Q18. How do you test something non-deterministic?
`[HARD]`

**Answer:** You stop asserting equality and start asserting properties, against a versioned golden set, with a score band as the pass criterion. Three layers:

1. **Deterministic layer** — the parts that aren't the model. Schema validation, auth, retries, idempotency, error mapping. These get normal unit and contract tests and must be 100% deterministic.
2. **Property tests on model output** — parses as valid JSON against the Pydantic/JSON Schema contract, cites only retrieved document IDs, contains no PII, calls only tools from the allow-list, calls at most N tools.
3. **Golden-set regression** — 50–200 curated cases with expected outcomes, scored (exact match where possible, judge or similarity where not), run in CI with a **threshold and a delta gate**: fail the build if the score drops more than X points versus the last release.

Every prompt, model version, retrieval config and tool catalogue is a versioned artefact. A prompt change is a code change and goes through the same PR.

**If they push back — *"how is that different from flaky tests?"*:** A flaky test is unpredictable at the same input; this is a *distribution* you measure and gate on. The mistake is running it once — you run each case N times and gate on the aggregate, and you pin `temperature=0` and the model version for the deterministic subset so drift shows up as a model-version diff, not noise.

---

### Q19. What are the honest limits — where would you tell a client "no"?
`[MEDIUM]`

**Answer:** Four places, and being the person who says this in a client meeting is what EY actually rewards.

- **Anything where a plausible wrong answer is worse than no answer** — financial postings, regulatory filings, tax determinations. The failure mode of an LLM is confident and syntactically perfect.
- **Anything requiring an auditable deterministic rule** — if a regulator can ask "why did this transaction take this path", the answer cannot be "the model decided". Put the rule in code and use the model to *draft* the rule.
- **Where the data can't leave a boundary** and the client won't deploy in-region — data residency is an architecture constraint, not a preference.
- **Where the ROI is a rounding error against the run cost.** A PTU deployment has an hourly meter whether or not traffic flows. If a use case saves two analyst-hours a week, it doesn't justify provisioned capacity.

**If they push back — *"a client insists anyway"*:** I'd document the risk, propose a scoped pilot with a measurable success criterion and a human gate, and make the pilot's exit criteria explicit up front. Saying no without offering a path is how you lose the account; saying yes without a gate is how you lose the client.

---

## 5. Designing an Enterprise Agentic Integration Layer

### Q20. Design the integration layer for an agent platform serving multiple business units.
`[HARD]`

**Answer:** Six planes. I'd draw them top-to-bottom and talk through each.

1. **Agent plane** — the hosts. Copilot Studio, a custom LangGraph service, Foundry agents. They own reasoning, nothing else.
2. **Gateway plane** — **one** APIM instance is the single ingress and egress for everything the agents touch. Inbound: `validate-azure-ad-token`, `rate-limit-by-key`, `llm-token-limit`, `llm-content-safety`. Outbound to LLMs: backend pool with priority and circuit breakers.
3. **Tool plane** — MCP servers and REST APIs, published as APIM Products so access is grantable per business unit. Each tool declares: owner, required scope, side-effect class (read / idempotent-write / irreversible), and a cost class.
4. **Orchestration plane** — long-running and human-gated work is **not** the agent's job. Durable Functions or Logic Apps Standard, so a 3-day approval survives a host restart.
5. **Data plane** — vector store, canonical entity store, cache. Ingestion is an ordinary ETL pipeline with provenance columns.
6. **Governance plane** — API Center as the registry, App Insights + Log Analytics for audit, Key Vault + managed identity for secrets, and a policy that says every tool invocation is logged with `agent-id`, `user-id`, tool name, arguments hash and outcome.

**The one-sentence design principle:** *the agent decides what to do; the integration layer decides what it's allowed to do.* Authorisation never lives in the prompt.

**If they push back — *"why not let each team run its own gateway?"*:** Because then per-agent cost attribution, tool audit and content safety are implemented N times with N different bugs, and there's no single place to revoke a compromised agent identity. One gateway, many Products.

---

### Q21. How do you do per-tool authorisation when the caller is an agent acting for a user?
`[HARD]`

**Answer:** Two identities, always separated: the **agent's** identity (workload) and the **user's** identity (on-behalf-of). Authorisation is the intersection. If either lacks the scope, the call fails.

The rules I'd enforce:

- The agent is a confidential client with its own app registration and scopes; it gets a token via **client credentials** or **on-behalf-of** depending on whether user context matters.
- **Never pass the user's token through to the downstream system.** The MCP spec forbids token passthrough; the same rule applies to any tool façade. The tool layer exchanges for a downstream token.
- **Security trimming happens in every tool, not once at the front door.** Microsoft's own agent-pattern guidance says this explicitly: agents need broad access to knowledge stores to serve all users, but must not return data the user can't see.
- Side-effect class drives extra controls: irreversible tools require an approval gate and a stronger auth assurance (`acr`/`amr` claims), not just a scope.

```python
# FastAPI tool façade: agent identity + user identity + per-tool scope.
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

SIDE_EFFECT_IRREVERSIBLE = "irreversible"


class Principal(BaseModel):
    agent_id: str
    agent_scopes: set[str]
    user_oid: str | None
    user_roles: set[str]
    auth_strength: str  # e.g. "mfa"


async def principal(
    authorization: Annotated[str, Header()],
    x_agent_id: Annotated[str, Header()],
) -> Principal:
    claims = validate_entra_token(authorization.removeprefix("Bearer "))  # audience-checked
    return Principal(
        agent_id=x_agent_id,
        agent_scopes=set(claims.get("roles", [])),
        user_oid=claims.get("oid"),
        user_roles=set(claims.get("groups", [])),
        auth_strength=(claims.get("amr") or ["pwd"])[0],
    )


def require_tool(name: str, scope: str, side_effect: str = "read"):
    async def _guard(p: Annotated[Principal, Depends(principal)]) -> Principal:
        if scope not in p.agent_scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"agent lacks {scope}")
        if side_effect == SIDE_EFFECT_IRREVERSIBLE and p.auth_strength != "mfa":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "step-up auth required")
        audit(tool=name, agent=p.agent_id, user=p.user_oid, scope=scope)
        return p

    return _guard


@app.post("/tools/cancel_shipment")
async def cancel_shipment(
    shipment_id: str,
    p: Annotated[Principal, Depends(require_tool("cancel_shipment", "tools.shipment.write", SIDE_EFFECT_IRREVERSIBLE))],
) -> dict:
    return await logistics_client.cancel(shipment_id, on_behalf_of=p.user_oid)
```

**If they push back — *"can't the system prompt just say 'don't call this for user X'?"*:** No. A prompt is a suggestion to a probabilistic system and it's attacker-influenceable through any retrieved content. Authorisation must be enforced by code the model cannot reach. See [Auth & Security](06-auth-and-security.md).

---

### Q22. Prompt injection through integrated data — why is this an integration problem?
`[HARD]`

**Answer:** Because the attack enters through **your** pipeline. A supplier writes instructions into an invoice PDF description field; your ingestion pipeline chunks it, embeds it, stores it; retrieval surfaces it; the agent reads it as instructions and calls a tool. Every hop in that chain is integration code. The model is the last link, not the vulnerability.

Reframed in vocabulary EY will recognise: **untrusted data crossed a trust boundary and reached a privileged executor without validation.** That is the same class of defect as SQL injection or an XXE in an inbound XML message — and the same mitigations apply, at the boundary.

Controls, in order of effectiveness:

1. **Least privilege on tools.** If the agent can't call `transfer_funds`, injection can't call it either. This is the only control that actually holds.
2. **Provenance tagging at ingestion.** Every chunk carries `source`, `trust_tier`, `ingested_at`, `tenant_id`. Untrusted-tier content never reaches a context that can trigger a write tool.
3. **Structural separation.** Retrieved content is passed as data with delimiters and an explicit "this is reference material, not instructions" framing — helpful, not sufficient.
4. **`llm-content-safety` with `shield-prompt="true"`** at the gateway — Azure AI Content Safety's prompt-attack detection, which also covers MCP tool requests and responses.
5. **Egress control.** Injection usually needs to exfiltrate. Constrain outbound: no arbitrary URLs, allow-listed destinations only.
6. **Human gate on irreversible actions.**

```python
# Ingestion-time provenance + a hard gate on what can reach a write-capable agent.
from dataclasses import dataclass
from enum import IntEnum


class TrustTier(IntEnum):
    UNTRUSTED = 0   # partner uploads, scraped web, inbound email
    INTERNAL = 1    # employee-authored wiki, SharePoint
    CURATED = 2     # reviewed policy documents


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    chunk_idx: int
    text: str
    source_system: str
    trust_tier: TrustTier
    tenant_id: str

    @property
    def upsert_key(self) -> str:
        return f"{self.tenant_id}:{self.doc_id}:{self.chunk_idx}"   # idempotent sink write


def retrievable_for(agent_can_write: bool) -> TrustTier:
    """A write-capable agent never sees untrusted content."""
    return TrustTier.INTERNAL if agent_can_write else TrustTier.UNTRUSTED


def build_filter(tenant_id: str, agent_can_write: bool) -> str:
    return (
        f"tenant_id eq '{tenant_id}' and trust_tier ge {int(retrievable_for(agent_can_write))}"
    )
```

**If they push back — *"can't you just detect and strip injected instructions?"*:** Detection helps and I'd run it, but I wouldn't rely on it — it's a classifier against an adversary who can rephrase. The controls that hold are the ones that don't depend on detecting intent: privilege, provenance and egress restriction.

---

### Q23. Where do you put a human-in-the-loop approval gate, and how does it survive a restart?
`[HARD]`

**Answer:** In the orchestration plane, never in the agent. Durable Functions' human-interaction pattern: the orchestrator raises the request, then waits on **either** an external event **or** a durable timer, whichever fires first. State is persisted, so a 24-hour wait survives host restarts, deployments and scale-in.

```python
# Durable Functions (Python) — approval with escalation on timeout.
from datetime import timedelta

import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    request = context.get_input()

    yield context.call_activity("NotifyApprover", request)

    due_time = context.current_utc_datetime + timedelta(hours=24)
    timeout_task = context.create_timer(due_time)
    approval_task = context.wait_for_external_event("ApprovalEvent")

    winner = yield context.task_any([approval_task, timeout_task])

    if winner == approval_task:
        timeout_task.cancel()
        decision = approval_task.result
        if decision.get("approved"):
            result = yield context.call_activity("PostToErp", request)
        else:
            result = {"status": "rejected", "by": decision.get("approver")}
    else:
        result = yield context.call_activity("EscalateToQueue", request)

    return result


main = df.Orchestrator.create(orchestrator_function)
```

The client side is the **async HTTP API** pattern, and the exact mechanics are worth quoting: the starter returns **HTTP 202 Accepted** with a `Location` header set to `statusQueryGetUri` and a `Retry-After` header; the caller polls that URL and keeps getting 202 until the instance completes or fails, at which point it returns 200. The payload also carries `sendEventPostUri` (that's how the approver's click delivers `ApprovalEvent`), `terminatePostUri` and `purgeHistoryDeleteUri`.

**If they push back — *"why not just have the agent wait?"*:** Because agents are stateless request handlers with a request timeout. HTTP-triggered functions are additionally capped at **230 seconds** by the Azure Load Balancer idle timeout regardless of `functionTimeout` — which is precisely why the 202-plus-polling pattern exists. A 24-hour approval needs durable state, not a held connection.

**Orchestrator constraint to name:** orchestrator code must be deterministic and replay-safe — no direct I/O, no `datetime.now()`, no random. Use `context.current_utc_datetime` and push all I/O into activities.

---

### Q24. How do you govern agent cost?
`[MEDIUM]`

**Answer:** Three layers, and the point is that none of them are in the agent.

1. **Hard ceiling at the gateway** — `llm-token-limit` with both `tokens-per-minute` and a `token-quota` per period, keyed on subscription or `agent-id`. Rate breach = 429, quota breach = 403. That's the circuit breaker on spend.
2. **Attribution** — `llm-emit-token-metric` with `Subscription ID` and an `agent-id` dimension gives you cost-per-consumer in App Insights without waiting for billing exports. Remember the caps: 5 custom dimensions, 100 unique values per dimension, 1,000 active time series per namespace, silently dropped beyond that.
3. **Architectural cost reduction** — semantic caching for repeat prompts; model routing (cheap model for classification, expensive model only for synthesis); PTU for predictable baseline with pay-as-you-go spill for burst.

Microsoft's own agent-orchestration guidance is quotable here: sequential and handoff patterns invoke agents one at a time so cost accumulates per step; concurrent patterns spike resource consumption; **magentic** orchestration is the most variable because the manager keeps iterating until it has a viable plan, which makes total cost hard to predict.

**If they push back — *"what's the number one cost driver?"*:** Retries and loops, not prompt size. An agent that retries a failing tool five times per turn and re-sends full conversation history costs an order of magnitude more than the same task done once. Cap tool-call depth, cap turns, and trim history — those three changes usually beat any model swap.

---

### Q25. Name the agent orchestration patterns and map them to integration patterns you already know.
`[MEDIUM]`

**Answer:** The Azure Architecture Center documents five, and it states explicitly that they *extend and complement* traditional cloud design patterns by addressing components with reasoning, learning and **nondeterministic outputs**.

| Agent pattern | What it is | Integration analogue | Main failure mode |
|---|---|---|---|
| **Sequential** | Linear pipeline; each agent processes the previous output | Pipes and Filters | Failures in early stages propagate; no parallelism |
| **Concurrent** | Agents work independently on the same input | Scatter-Gather / fan-out-fan-in | Needs conflict resolution when results contradict; resource-intensive |
| **Group chat** | Agents contribute to a shared thread, a manager controls turn order | Choreography with a mediator | Conversation loops; hard to control with many agents |
| **Handoff** | One active agent at a time, agents decide when to transfer control | Content-Based Router / dynamic routing slip | Infinite handoff loops; unpredictable routing paths |
| **Magentic** | A manager builds and adapts a task ledger — plan, build, execute | Scheduler Agent Supervisor | Slow to converge; stalls on ambiguous goals |

**The bridge sentence:** *"Sequential is Pipes and Filters, concurrent is fan-out/fan-in, handoff is a content-based router, magentic is Scheduler Agent Supervisor. The reliability engineering is identical — timeouts, retries, compensations, idempotent consumers — the only new variable is that routing is decided by a model at runtime instead of by a rule at design time."*

**If they push back — *"which would you pick for a client?"*:** Start with the least complexity that works — usually a single agent with multiple tools, or deterministic routing. Multi-agent orchestration multiplies model invocations and cost, and Microsoft's own guidance leads with "start with the right level of complexity". I escalate only when a single agent's tool catalogue gets too large for reliable selection.

---

### Q26. Design an integration where agents and traditional consumers hit the same backends.
`[HARD]`

**Answer:** One canonical service, three projections, one gateway. Concretely, for an order-management estate:

- **Backends:** SAP (on-prem, via the **on-premises data gateway** — outbound-only, no inbound ports, but note the **2 MB write / 8 MB read** payload ceilings, which force Claim Check for anything larger), a cloud OMS REST API, and a 3PL partner API.
- **Integration layer:** Logic Apps **Standard** workflows using **built-in service-provider connectors** (in-process Service Bus, SQL, Blob — higher throughput and lower cost than shared managed connections), plus Azure Functions for custom transformation.
- **Messaging:** Service Bus topics for reliable order fan-out (FIFO via sessions, duplicate detection on `MessageId`, DLQ after `MaxDeliveryCount` defaults to 10); Event Grid for reactive notifications (retry ladder 10s → 30s → 1m → 5m → 10m → 30m → 1h → 3h → 6h then every 12h up to 24h, with built-in jitter; dead-lettering is **off by default** so failed events are silently dropped unless you configure it).
- **Gateway:** APIM fronts everything. `/v1/orders` REST for apps, a SOAP passthrough for the legacy partner, and the **same** API exposed as an MCP server at `/orders-mcp/mcp` for agents.
- **Governance:** identical policies on all three projections — `validate-azure-ad-token`, `rate-limit-by-key`, correlation ID, App Insights — plus `llm-content-safety` and `llm-token-limit` only on the agent path.

**The closing sentence, which is the whole interview:** *"The agent path and the app path share one backend, one canonical model and one policy set. The only thing that differs is that the agent path adds token governance and content safety, because the caller is non-deterministic."*

**If they push back — *"what breaks first at scale?"*:** The Service Bus 256 KB message ceiling on Standard, when someone attaches a PDF. Answer is Claim Check — write the payload to Blob, put the SAS URI in the message. Premium raises single messages to 100 MB over AMQP but the **default per-entity max is still 1 MB**; the 100 MB is opt-in per queue/topic. See [System Design](08-system-design-integration.md), design 12.

---

## 6. Azure OpenAI / Foundry Operational Reality

### Q27. PTU vs standard — explain it as a capacity-planning decision.
`[MEDIUM]`

**Answer:** Standard is pay-per-token on shared capacity with **no latency SLA**; provisioned holds a fixed amount of processing capacity exclusively for your deployment whether or not requests are flowing, billed **per PTU per hour** (or via 1-month/1-year Azure Reservations) with a defined latency target per model.

The facts that matter operationally:

- A **PTU** is model-**independent** quota — you don't buy PTUs for a specific model — but the TPM a given PTU count delivers **varies by model**, and each model has a **minimum PTU count**.
- PTU quota is **per subscription, per region, per deployment type**. Quota in East US does not carry to West Europe.
- **Quota ≠ capacity.** Having quota doesn't guarantee capacity exists in the region; deployment fails if it doesn't. Capacity availability changes throughout the day, and deleting a deployment releases capacity you may not get back.
- Three deployment types: `GlobalProvisionedManaged` (routed globally), `DataZoneProvisionedManaged` (US or EU zone), `ProvisionedManaged` (single region, strict residency).
- **Reservations don't guarantee capacity** — deploy first to confirm capacity, then buy the reservation to lock the rate.
- Max provisioned throughput units per deployment: **100,000**.

```bash
# Provisioned deployment, Global PTU
az cognitiveservices account deployment create \
  --name aoai-ptu-eastus \
  --resource-group rg-integration-prod \
  --deployment-name gpt-chat \
  --model-name gpt-4.1 \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-name GlobalProvisionedManaged \
  --sku-capacity 100

# Standard (pay-as-you-go) spill target, same resource so spillover can use it
az cognitiveservices account deployment create \
  --name aoai-ptu-eastus \
  --resource-group rg-integration-prod \
  --deployment-name gpt-chat-spill \
  --model-name gpt-4.1 \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-name GlobalStandard \
  --sku-capacity 50
```

**If they push back — *"how do you size it?"*:** Three inputs — request shape (RPM, average input tokens, average output tokens), the model's output-to-input capacity ratio (output tokens cost more capacity than input), and cache rate (cached input tokens don't consume PTU capacity). You normalise to a TPM figure and divide by the model's Input-TPM-per-PTU. Foundry ships a capacity calculator; I'd use it and then load-test, not trust it.

---

### Q28. You're getting 429s from Azure OpenAI. Walk me through it.
`[HARD]`

**Answer:** Four steps, in this order.

1. **Read the response, don't guess.** A 429 carries a `Retry-After`. On Azure OpenAI backends that value can be very large — Microsoft's own APIM docs cite "for example, 1 day". Honouring it is mandatory; a fixed 5-second retry loop against a day-long backoff is how you turn a throttle into an outage.
2. **Distinguish token-rate from request-rate.** Quota is expressed as both TPM and RPM, with a documented conversion — most models are **10 RPM per 1,000 TPM**, though newer versions differ (e.g. `gpt-chat-latest` version `2026-08-06` uses **1 RPM per 1,000 TPM**). You can be under TPM and over RPM. Microsoft even documents that you may see 429s **when token usage metrics appear below quota**.
3. **Fix at the right layer.** Client: exponential backoff with jitter, bounded concurrency, honour `Retry-After`. Gateway: backend pool with priority + circuit breaker with `acceptRetryAfter: true`. Platform: raise quota, or move to PTU with spillover.
4. **Prevent recurrence.** `llm-token-limit` with `estimate-prompt-tokens="true"` rejects an oversized prompt *before* it consumes backend quota, and smooths the load that caused the burst.

```python
import asyncio
import random

import httpx

MAX_ATTEMPTS = 5


async def call_llm(client: httpx.AsyncClient, payload: dict) -> dict:
    for attempt in range(MAX_ATTEMPTS):
        r = await client.post("/chat/completions", json=payload)
        if r.status_code != 429:
            r.raise_for_status()
            return r.json()

        retry_after = r.headers.get("Retry-After")
        if retry_after is not None:
            delay = float(retry_after)
            if delay > 60:
                # Long backoff means capacity, not burst. Fail over rather than sleep.
                raise RuntimeError(f"backend throttled for {delay}s; route to spill deployment")
        else:
            delay = min(2 ** attempt, 32)

        await asyncio.sleep(delay + random.uniform(0, 1))  # jitter avoids a retry stampede

    raise RuntimeError("exhausted retries against LLM backend")
```

**If they push back — *"why the jitter?"*:** Because every caller that got 429'd at the same instant will retry at the same instant without it — synchronised retry storms are how a transient throttle becomes a sustained one. Event Grid's own retry ladder adds "a small randomization to all retry steps" for exactly this reason.

---

### Q29. What does Microsoft Foundry change for an integration developer?
`[MEDIUM]`

**Answer:** It moves the control plane. APIM's AI gateway can now be **associated with a Foundry resource** so you set token quotas and rate limits for model deployments from the Foundry UI, register agents running anywhere — Azure, other clouds, on-prem — into the Foundry control plane, and register MCP tools hosted anywhere for automatic governance and discovery. That integration is preview, so I'd flag it as directional rather than something I'd commit a delivery date to.

**Why it matters for this role:** that seam — agents on one side, enterprise systems on the other, a gateway in the middle — is exactly where "API and Integration Developer" meets "AI Frameworks and Tooling". The integration developer owns the gateway the agents call through. That's the job.

**If they push back — *"so what would you own?"*:** The tool contracts, the gateway policies, the identity and authZ model, the observability, and the reliability engineering on the backends. Not the model, not the prompts.

---

### Q30. What deprecations and deadlines are you tracking right now?
`[MEDIUM]`

**Answer:** Naming these unprompted signals run-and-maintain thinking, which is most of what GDS delivery is.

- **30 September 2026** — legacy Service Bus libraries (`WindowsAzure.ServiceBus`, `Microsoft.Azure.ServiceBus`, `com.microsoft.azure.servicebus`) retire, and SBMP protocol support ends. Migration target is `Azure.Messaging.ServiceBus` (AMQP-only). Any Big-4 estate with legacy .NET integrations has a live remediation backlog here.
- **10 November 2026** — support ends for the Azure Functions **in-process model**; migrate to the isolated worker model.
- **Azure Functions Consumption plan is now labelled legacy** — Flex Consumption is the recommended serverless host for new work.
- **MCP HTTP+SSE transport** deprecated since protocol version `2024-11-05` in favour of Streamable HTTP.
- **AKS Basic Load Balancer** support ended 30 September 2025; the **OSM add-on** ends 30 September 2027 (migrate to the Istio add-on).
- **APIM stv1** compute platform retired in 2024; note there is **no automated migration path from classic tiers to v2**.

**If they push back — *"how do you track these?"*:** Azure Updates plus the retirement pages, reviewed on a cadence, and a register per client estate mapping each deprecation to the affected components with an owner and a date. On a delivery engagement that register is a deliverable, not a personal habit.

---

## 7. Interviewer Traps

**Trap 1 — "MCP is going to replace REST APIs."**
❌ *Wrong answer:* "Yes, MCP is the new API standard."
✅ *Correct:* MCP is a projection over APIs you already have. Every APIM MCP server is backed by a REST API; the canonical model and OpenAPI contract remain the source of truth. MCP adds a discovery and invocation surface for a non-deterministic caller — like adding a SOAP façade over a REST service, not replacing it.

**Trap 2 — "We'd use SSE transport for the remote MCP server."**
❌ *Wrong answer:* naming SSE as the current remote transport.
✅ *Correct:* The spec defines **two** standard transports: stdio and **Streamable HTTP**. HTTP+SSE is **deprecated as of protocol version `2024-11-05`**. Streamable HTTP uses one endpoint for POST and GET, and can still use SSE *internally* for streamed responses — which is why people confuse them.

**Trap 3 — "The MCP server forwards the caller's token to the backend."**
❌ *Wrong answer:* "We pass the bearer token straight through to SAP."
✅ *Correct:* The MCP spec **explicitly forbids token passthrough**. The server is an OAuth 2.1 resource server: it validates that the token's audience is *itself*, then acts as an OAuth client to the upstream API and obtains a **separate** token. Passthrough creates the confused-deputy vulnerability the spec calls out by name.

**Trap 4 — "APIM's MCP support gives you tools, resources and prompts."**
❌ *Wrong answer:* listing all three.
✅ *Correct:* APIM supports **tools only** — no MCP resources, no prompts — and MCP capabilities are **not supported in APIM workspaces**. Only HTTP-compatible APIs can be exposed. Consumption tier is excluded.

**Trap 5 — "Rate limiting in APIM is exact."**
❌ *Wrong answer:* "We set 100/min and that's the hard cap."
✅ *Correct:* Microsoft states rate limiting "is never completely accurate" because of the distributed architecture. Counters are tracked **independently at each gateway**, including each region of a multi-region deployment and each workspace gateway — they are **not** aggregated. And v2 tiers use a **token bucket** while classic uses a **sliding window**, so identical counter-keys at multiple scopes must carry identical limits in v2 or behaviour is unpredictable.

**Trap 6 — "Set `llm-token-limit` and you'll never see a 429 from the model."**
❌ *Wrong answer:* conflating gateway throttling with backend quota.
✅ *Correct:* `llm-token-limit` protects *your* consumers from each other; it does nothing about the backend's own TPM/RPM quota. You still need backend-side handling: a backend pool with priority, a circuit breaker with `acceptRetryAfter: true` (because Azure OpenAI's `Retry-After` can be a day), and client retries with jitter. Microsoft documents that you can get 429s even when token metrics show you below quota.

**Trap 7 — "Prompt injection is a model problem, the AI team owns it."**
❌ *Wrong answer:* deferring it.
✅ *Correct:* The payload entered through the ingestion pipeline, crossed a trust boundary, and reached a privileged executor. That's an integration security defect, identical in shape to injection through any untrusted inbound message. Mitigations are integration controls: least privilege per tool, provenance tagging at ingestion, egress allow-listing, `llm-content-safety` with `shield-prompt`, and a human gate on irreversible actions.

**Trap 8 — "Semantic caching is free performance."**
❌ *Wrong answer:* enabling it globally.
✅ *Correct:* It returns responses based on **similarity, not equality** — Microsoft's own docs warn it can surface responses that are incorrect, outdated or unsafe for the current request. `score-threshold` **above 0.2 risks mismatch**; start around 0.05. Always `vary-by` a user or tenant identifier, or you leak one user's answer to another. And put a `rate-limit` immediately after the lookup so a cache outage doesn't flood the backend.

**Trap 9 — "We put the agent behind the gateway, so it's secure."**
❌ *Wrong answer:* treating perimeter auth as sufficient.
✅ *Correct:* Perimeter auth answers "is this a legitimate agent". It doesn't answer "should this agent, acting for this user, invoke this specific tool with these arguments". You need per-tool scopes, security trimming inside every tool (Microsoft's own agent guidance is explicit that agents need broad store access but must not return data the user can't see), idempotency on writes, and an approval gate on irreversible actions.

---

## 8. 30-Second Whiteboard Versions

### 8.1 MCP behind APIM — the enterprise agent tool plane

```
 Copilot Studio / Foundry agent / LangGraph service
        │  Streamable HTTP  POST+GET /mcp   (JSON-RPC 2.0)
        │  Authorization: Bearer   Mcp-Session-Id   MCP-Protocol-Version
        ▼
 ┌──────────────────────── Azure API Management ────────────────────────┐
 │  inbound:  validate-azure-ad-token → ip-filter → rate-limit-by-key    │
 │            → llm-content-safety(shield-prompt) → trace(agent-id)      │
 │  MCP server: https://<apim>.azure-api.net/orders-mcp/mcp              │
 │  tools ONLY (no resources / prompts) · not in workspaces              │
 │  outbound: credential manager / managed identity → downstream token   │
 └──────────────────────────────────────────────────────────────────────┘
        │                        │                       │
        ▼                        ▼                       ▼
   REST /v1/orders        Logic Apps Standard        Azure Function
   (same canonical         (built-in Service Bus,     (transformation)
    model, same policies)   SQL, Blob connectors)
        │
        ▼  on-prem data gateway (outbound only; 2 MB write / 8 MB read)
      SAP
```

**Say:** *"One canonical service, three projections — REST for apps, SOAP for the legacy partner, MCP for agents — behind one gateway with one policy set. The agent path adds token governance and content safety; everything else is identical."*

### 8.2 AI gateway load balancing — PTU first, spill on breaker

```
        client / agent
             │
             ▼
   APIM  llm-token-limit (TPM + monthly quota, counter-key = subscription)
         llm-emit-token-metric (App Insights, ≤5 dimensions)
         set-backend-service backend-id="aoai-pool"
             │
             ▼
      ┌── backend Pool (max 30) · priority-based ──┐
      │  priority 1 : AOAI PTU deployment          │  ← drains first
      │      circuitBreaker: 429/5xx ×5 in PT1M    │
      │      tripDuration PT1M, acceptRetryAfter   │
      │  priority 2 : AOAI pay-as-you-go (weighted)│  ← only when ALL of
      └────────────────────────────────────────────┘    priority 1 tripped
```

**Say:** *"Lower-priority groups are used only when every backend in the higher-priority group has tripped its breaker — that's how you drain PTU before paying per token. `acceptRetryAfter` exists specifically because Azure OpenAI's `Retry-After` can be a day long."*

### 8.3 Agentic integration layer — six planes

```
 Agent plane        Copilot Studio · Foundry agents · LangGraph service
      │             (reasoning only — no authorisation, no state)
 Gateway plane      APIM: authN · rate/token limits · content safety · routing · telemetry
      │
 Tool plane         MCP servers + REST APIs, published as APIM Products
      │             each tool: owner · required scope · side-effect class · cost class
 Orchestration      Durable Functions / Logic Apps Standard
      │             long-running work, human approval gates, compensations
 Data plane         vector store · canonical entity store · cache
      │             ingestion carries provenance: source, trust_tier, tenant_id
 Governance         API Center registry · App Insights audit · Key Vault + managed identity
```

**Say:** *"The agent decides what to do; the integration layer decides what it's allowed to do. Authorisation never lives in the prompt."*

---

## 9. 12 Rehearsed Pivots

Drop-in bridges to move onto your home turf **without dodging the question**. Each answers the question first, then pivots.

1. **On "tell me about your integration experience"** — *"Most recently I've been the person who makes enterprise systems callable by agents — which in practice is API design, OAuth to downstream systems, idempotency, retry and cost governance. Same discipline, newer caller. Before that, [X] REST integrations in FastAPI against [Y]."*

2. **On "have you used Service Bus?"** — *"Yes, for [use case]. What I'd add is that the same reliability primitives — duplicate detection on `MessageId`, DLQ after `MaxDeliveryCount` 10, PeekLock at 1 minute default and 5 minute max — became non-negotiable in my agent work, because a non-deterministic caller retries much more aggressively than an app does."*

3. **On "how do you secure an API?"** — Answer with OAuth2/JWT/mTLS/subscription keys normally, then: *"One thing I'd add for 2026 — if that API is going to be reachable by an agent, the token model changes. The MCP spec forbids token passthrough and mandates audience validation, so the façade holds two identities: the caller's and its own downstream one."*

4. **On "REST vs GraphQL vs SOAP"** — Give the standard comparison, then: *"There's a fourth surface now — MCP. It's the one where the caller has to discover operations at runtime because it's a model choosing, which is why per-tool authorisation matters more than per-endpoint."*

5. **On "what's your experience with Azure?"** — *"Azure OpenAI and Functions in production, plus APIM as an AI gateway — `llm-token-limit`, `llm-emit-token-metric`, backend pools with circuit breakers for failover across deployments. The APIM and messaging patterns transfer directly to Logic Apps and Service Bus work."*

6. **On "how do you handle a flaky third-party API?"** — Retry with exponential backoff and jitter, circuit breaker, idempotency key, DLQ. Then: *"The example I know best is Azure OpenAI, which 429s with a `Retry-After` that can be a full day — which is exactly why APIM's backend circuit breaker has an `acceptRetryAfter` flag."*

7. **On "have you done CI/CD?"** — Answer honestly about pipeline authoring, then: *"What I have deep experience of is the artefacts that go through the pipeline — prompts, tool schemas, model versions and eval thresholds are all versioned and gated in CI the same way an OpenAPI spec is. Contract-testing a spec and regression-testing a golden set are the same gate with a different assertion."*

8. **On "why should we hire someone without Logic Apps experience?"** — *"Because I've built the same thing in code. A LangGraph workflow with persisted checkpoints, conditional routing, retry policies and human approval gates is a stateful orchestration — the exact problem Durable Functions and Logic Apps Standard solve. I know what the runtime has to guarantee; I need to learn the designer, not the concepts."*

9. **On "where do you see integration going?"** — *"Toward more consumers per backend, not fewer. Apps, partners, and now agents. That pushes value into the gateway and the canonical model, because those are the only places you can enforce one policy across all three."*

10. **On "what would you do in your first 90 days?"** — *"Learn the client estate and the delivery model. Then find the thing I can do that nobody else on the team can — which is probably making existing integrations agent-callable safely, given EY's Canvas and Copilot rollout. I'd rather add a capability than duplicate one."*

11. **On "what's your biggest technical weakness for this role?"** — *"Terraform and Kubernetes at production depth — I've consumed pipelines more than I've authored them. I've closed the conceptual gap: state, locking, drift, `for_each` vs `count`, liveness vs readiness. What I need is reps against a real estate, and that's the part I'd expect to be slower on for the first month."* (Never claim depth you don't have — EY interviewers reportedly probe follow-ups hard and one candidate was accused of external help when answers evolved mid-conversation. **State your reasoning linearly and commit to an answer before refining it.**)

12. **On "any questions for us?"** — *"Which client and unit is this req for, and is there a client round? And how much of the work is greenfield Azure Integration Services versus run-and-maintain on an existing estate?"* Then: *"Given the EY.ai and Canvas rollout, is this team expected to expose integrations as tools for agents, or is that a separate practice?"* — this signals you've read what EY is actually doing.

---

## 10. Rapid Fire

- **What protocol does MCP use for messages** — JSON-RPC 2.0, UTF-8 encoded.
- **MCP's two standard transports** — stdio and Streamable HTTP. Clients SHOULD support stdio wherever possible.
- **Is HTTP+SSE still valid** — Deprecated as of protocol version `2024-11-05`; replaced by Streamable HTTP.
- **Streamable HTTP endpoint shape** — One path (e.g. `/mcp`) serving both POST and GET; client must `Accept: application/json, text/event-stream`.
- **MCP session header** — `Mcp-Session-Id`, issued on `InitializeResult`, echoed on every later request; DELETE ends it; 404 forces re-initialise.
- **MCP protocol version header** — `MCP-Protocol-Version`; absent ⇒ server assumes `2025-03-26`; invalid ⇒ 400.
- **MCP's three server primitives and their control** — Tools (model-controlled), Resources (application-controlled), Prompts (user-controlled).
- **MCP resumability mechanism** — SSE event `id` plus the client's `Last-Event-ID` header on reconnect; per-stream replay only.
- **Which OAuth RFCs does MCP mandate** — OAuth 2.1 draft, RFC 8414 (AS metadata), RFC 7591 (DCR), RFC 9728 (Protected Resource Metadata), RFC 8707 (Resource Indicators).
- **What role is an MCP server in OAuth terms** — An OAuth 2.1 **resource server**. It validates tokens; it never issues them.
- **How does an MCP client discover the auth server** — 401 + `WWW-Authenticate` → `/.well-known/oauth-protected-resource` → `authorization_servers` → RFC 8414 AS metadata.
- **What is forbidden by the MCP spec** — Token passthrough; tokens in the query string; accepting tokens not audience-bound to the server.
- **Which APIM tiers support MCP servers** — Developer, Basic, Basic v2, Standard, Standard v2, Premium, Premium v2 — plus self-hosted gateway. Not Consumption.
- **APIM MCP endpoint format** — `https://<apim-name>.azure-api.net/<api-name>-mcp/mcp`.
- **What APIM's MCP support does NOT include** — Resources, prompts, and workspaces. Tools only.
- **The APIM MCP policy trap** — Never touch `context.Response.Body`; it forces buffering and breaks the streaming transport.
- **The APIM MCP logging trap** — Set Frontend Response "payload bytes to log" to 0 at All-APIs scope, or streaming fails.
- **Policy evaluation order for MCP servers** — Global scope evaluates **before** MCP-server scope.
- **Four APIM AI gateway policies** — `llm-token-limit`, `llm-emit-token-metric`, `llm-semantic-cache-lookup`/`-store`, `llm-content-safety`.
- **`llm-token-limit` response codes** — 429 when `tokens-per-minute` exceeded, **403** when `token-quota` exceeded.
- **`token-quota-period` allowed values** — Hourly, Daily, Weekly, Monthly, Yearly.
- **Are token counters aggregated across regions** — No. Tracked independently at each gateway, including workspace and regional gateways.
- **v2 vs classic throttling algorithm** — v2 = token bucket; classic = sliding window. Same counter-key at multiple scopes in v2 must carry identical limits.
- **Max custom dimensions on `llm-emit-token-metric`** — 5 (Azure Monitor allows 10 keys; APIM reserves 5 for defaults). 100 unique values per dimension, 1,000 time series per namespace, silently dropped beyond.
- **Why are my streaming token metrics empty** — Client didn't set `include_usage: true`; many OpenAI models omit usage when streaming.
- **Semantic cache score-threshold guidance** — Start around 0.05; above 0.2 risks mismatch. Lower value = stricter similarity required.
- **Mandatory attribute on semantic cache** — `embeddings-backend-auth="system-assigned"`. And always `vary-by` a tenant/user.
- **`llm-content-safety` categories** — Hate, SelfHarm, Sexual, Violence; thresholds 0 (most restrictive) to 7; blocks with 403; `shield-prompt` for attack detection.
- **Max backends in an APIM pool** — 30. Algorithms: round-robin (default), weighted, priority-based.
- **Priority-group semantics** — Lower-priority groups are used only when **every** backend in higher-priority groups has tripped its circuit breaker.
- **Circuit breaker limits in APIM** — One rule per backend; not supported in Consumption; approximate because gateway instances don't sync; returns 503 when tripped.
- **Why does `acceptRetryAfter` exist** — Azure OpenAI backends return 429 with `Retry-After` values that can be as long as a day.
- **PTU in one line** — Dedicated, model-independent, region-scoped model processing capacity billed per PTU per hour; quota does not guarantee capacity.
- **Provisioned spillover** — Routes non-200 responses (e.g. 429 when PTUs are exhausted) to a standard deployment in the same resource; per-request via `x-ms-spillover-deployment`.
- **Typical Azure OpenAI RPM:TPM ratio** — Most models 10 RPM per 1,000 TPM; some newer versions 1 RPM per 1,000 TPM. Check the model.
- **Durable Functions async HTTP pattern** — 202 Accepted + `Location: statusQueryGetUri` + `Retry-After`; poll until 200. Payload also carries `sendEventPostUri` and `terminatePostUri`.
- **Human-in-the-loop in Durable Functions** — `wait_for_external_event` raced against `create_timer` via `task_any`; cancel the loser.
- **Orchestrator code constraint** — Must be deterministic and replay-safe: no direct I/O, no wall-clock, no random. Use `context.current_utc_datetime`.
- **Why 230 seconds matters** — Azure Load Balancer idle timeout caps HTTP-triggered function responses regardless of `functionTimeout`; hence 202 + polling.
- **Five Azure agent orchestration patterns** — Sequential, concurrent, group chat, handoff, magentic.
- **Which agent pattern has the least predictable cost** — Magentic; the manager iterates until it has a viable plan.
- **Where does prompt injection belong in a risk register** — Integration security: untrusted data crossing a trust boundary into a privileged executor.
- **Single most effective anti-injection control** — Least privilege on tools. If the agent can't call it, injection can't either.
- **How do you make an agent's tool call safe to retry** — Deterministic idempotency key derived from the business inputs, plus an idempotent consumer on the receiving side.
- **Where does agent authorisation live** — In code the model cannot reach. Never in the system prompt.
