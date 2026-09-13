# Cloud, Azure OpenAI & Production Deployment / LLMOps

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

## Table of Contents

| § | Section | Q# |
|---|---------|----|
| 1 | [Azure OpenAI — Core Concepts](#1-azure-openai--core-concepts) | Q1–Q8 |
| 2 | [Authentication, Networking & Secrets](#2-authentication-networking--secrets) | Q9–Q13 |
| 3 | [Quota, Throughput & Reliability (429s, PTU)](#3-quota-throughput--reliability-429s-ptu) | Q14–Q20 |
| 4 | [Azure AI Platform for RAG](#4-azure-ai-platform-for-rag) | Q21–Q25 |
| 5 | [AWS & GCP Equivalents (breadth)](#5-aws--gcp-equivalents-breadth) | Q26–Q28 |
| 6 | [Containerizing a FastAPI + LLM Service](#6-containerizing-a-fastapi--llm-service) | Q29–Q33 |
| 7 | [Kubernetes, Scaling & Serverless](#7-kubernetes-scaling--serverless) | Q34–Q39 |
| 8 | [Caching, Multi-Tenancy & Graceful Degradation](#8-caching-multi-tenancy--graceful-degradation) | Q40–Q43 |
| 9 | [CI/CD & Release Strategy](#9-cicd--release-strategy) | Q44–Q47 |
| 10 | [LLMOps & Observability](#10-llmops--observability) | Q48–Q51 |
| 11 | [Security, OWASP LLM Top 10 & Compliance](#11-security-owasp-llm-top-10--compliance) | Q52–Q55 |
| 12 | [Production Readiness Checklist](#12-production-readiness-checklist) | — |
| 13 | [Red Flags / Do NOT say](#13-red-flags--do-not-say) | — |
| 14 | [Rapid-Fire (last 10 min before you walk in)](#rapid-fire-last-10-min-before-you-walk-in) | — |

---

## 1. Azure OpenAI — Core Concepts

### Q1. Explain the Azure OpenAI object hierarchy: resource, deployment, model, model version.
`[EASY]`

**Answer:** Four levels. **Subscription → Resource → Deployment → (Model, Model version)**.

| Level | What it is | Key detail |
|---|---|---|
| **Resource** | An Azure Cognitive Services account of kind `OpenAI`, in one region | Gives you the endpoint `https://<name>.openai.azure.com/`, keys, RBAC scope, private endpoint attach point |
| **Deployment** | A *named* instance of a model you create inside the resource | This name is what you pass as `model=` in the SDK. e.g. deployment `chat-prod` |
| **Model** | The base model family, e.g. `gpt-4o`, `gpt-4o-mini`, `text-embedding-3-large` | Availability is **per region** |
| **Model version** | Dated snapshot, e.g. `2024-08-06` | Pinned or `Auto-update to default` |
| **Deployment type** | Standard (regional), Global Standard, Data Zone, Provisioned (PTU), Batch | Controls where inference runs + pricing |

**Gotcha:** the single biggest Azure-vs-OpenAI trip-up — on public OpenAI `model="gpt-4o"` is the model; on Azure `model="<your-deployment-name>"`. If your deployment is called `gpt4o-prod`, you pass `gpt4o-prod`.

**Follow-up they will ask:** *"How do you keep prod stable when Microsoft retires a model version?"* → Pin the version explicitly (never auto-update in prod), subscribe to the model-retirement notification, keep a *second* deployment on the new version behind a feature flag, run your eval set against it, then flip the flag. Deployment name stays the same in a canary by creating `chat-prod-v2` and switching config, not by editing the live deployment.

---

### Q2. Azure OpenAI vs public OpenAI API — what actually differs?
`[MEDIUM]`

**Answer:** Same models, same wire format, different *enterprise envelope*. The API contract is ~identical (chat completions, embeddings, tool calling, streaming); everything around it changes.

| Dimension | OpenAI (api.openai.com) | Azure OpenAI |
|---|---|---|
| Model reference | `model="gpt-4o"` | `model="<deployment-name>"` |
| Versioning | Model snapshot only | Model snapshot **+** `api-version` query param |
| Endpoint | Single global | Per-resource, per-region `*.openai.azure.com` |
| Auth | `Authorization: Bearer sk-...` | `api-key:` header **or** Entra ID bearer token |
| Identity/RBAC | Org + project API keys | Full Azure RBAC, managed identity, no long-lived secret needed |
| Networking | Public internet | Private Endpoint / Private Link, VNet, `publicNetworkAccess: Disabled`, firewall rules |
| Data residency | Limited — global endpoint; regional/EU data residency exists only on some enterprise tiers | Choose region / data zone (EU, US); **Global Standard** may process anywhere in the geo |
| Training on your data | Not used for training by default (API) | Contractually not used; prompts/completions stored ≤30 days for abuse monitoring, and that can be **turned off** via approved Limited Access application |
| Content filtering | Model-level safety | Separate configurable **Azure AI Content Safety** filter per deployment, plus Prompt Shields |
| Quota | Org tier rate limits | Explicit **TPM quota** you allocate per deployment, per region |
| Purchasing | Pay-as-you-go | PAYG, **PTU** reserved capacity, Batch, Azure commitment/EA discounts |
| Compliance | SOC2 etc. | Inherits Azure compliance surface (ISO, HIPAA BAA, FedRAMP in some clouds), Azure Policy, Purview |
| Support | OpenAI support | Microsoft enterprise support / your existing Azure agreement |

**Say this line in the interview:** "We chose Azure OpenAI not for the model but for the *perimeter*: private endpoints, managed identity instead of API keys, per-deployment quota isolation per tenant, and a data-residency story we could put in front of a bank's risk team."

---

### Q3. What is the `api-version` query parameter and why does Azure have it?
`[MEDIUM]`

**Answer:** Azure pins the **API surface** (request/response schema, available features) separately from the model. Every classic Azure OpenAI call carries `?api-version=YYYY-MM-DD[-preview]`.

- **GA versions** (e.g. `2024-10-21`) — stable, supported, safe for prod.
- **Preview versions** (e.g. `2025-01-01-preview`) — needed for newest features (Assistants, "On Your Data" extensions, newest params). Can break; never pin prod to preview unless a feature demands it, and then own the upgrade risk.
- Newer surface: Azure also exposes an OpenAI-compatible **`/openai/v1/`** path that lets you use the plain `OpenAI` client with `base_url=".../openai/v1/"` and drop `api-version`. Mention it as "the direction Microsoft is moving", but code the classic `AzureOpenAI` client in an interview — it's what every existing codebase uses.

**Gotcha:** a 404 or "Unrecognized request argument" from Azure is 90% of the time a wrong/old `api-version`, not a wrong deployment name.

---

### Q4. Write the code to call Azure OpenAI chat completions with an API key.
`[EASY]`

**Answer:** `openai` Python SDK ≥1.x, `AzureOpenAI` class. Endpoint + api-version + deployment name.

**Code:**
```python
# pip install "openai>=1.60"
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],   # https://myres.openai.azure.com/
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-10-21",                              # GA
)

resp = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"],           # DEPLOYMENT name, not "gpt-4o"
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Summarise RAG in two lines."},
    ],
    temperature=0.2,
    max_tokens=256,
)

print(resp.choices[0].message.content)
print(resp.usage.prompt_tokens, resp.usage.completion_tokens)
```

**Gotcha:** `openai.ChatCompletion.create(...)` and `openai.api_type = "azure"` are the **removed 0.x API**. If you write that on the whiteboard you signal you haven't touched the SDK since 2023. Same for `from langchain.llms import OpenAI` — it's `from langchain_openai import AzureChatOpenAI` now.

**Second gotcha:** `max_tokens` is the classic chat-completions param and still works for the GPT-4o family, but it is **deprecated in favour of `max_completion_tokens`**, and the reasoning models (o-series and later) **reject `max_tokens` outright** with a 400. Write `max_completion_tokens` for anything new; know that `max_tokens` is what you'll find in existing code.

**Async version** (what a FastAPI service actually uses):
```python
from openai import AsyncAzureOpenAI

aclient = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-10-21",
    max_retries=0,        # we own retry policy; see Q16
    timeout=30.0,
)
```

---

### Q5. Now do it with Microsoft Entra ID / managed identity — no API key at all.
`[MEDIUM]`

**Answer:** Use `azure-identity`'s `DefaultAzureCredential` + `get_bearer_token_provider` against scope `https://cognitiveservices.azure.com/.default`, pass it as `azure_ad_token_provider`. The provider is called per request and handles token refresh.

**Code:**
```python
# pip install "openai>=1.60" "azure-identity>=1.19"
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),                       # MI in Azure, az-cli/VS Code locally
    "https://cognitiveservices.azure.com/.default",
)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,         # <-- instead of api_key
    api_version="2024-10-21",
)
```
Async: `from azure.identity.aio import DefaultAzureCredential` + `get_bearer_token_provider` from `azure.identity.aio`, passed to `AsyncAzureOpenAI`.

**RBAC roles you must name:**

| Role | Grants |
|---|---|
| `Cognitive Services OpenAI User` | Call inference (chat/embeddings), list deployments. **This is what your app pod gets.** |
| `Cognitive Services OpenAI Contributor` | Above + create/manage deployments, fine-tune |
| `Cognitive Services Contributor` | Manage the resource (control plane), read keys |

**Why this is the right answer:** no secret to rotate, no secret to leak, per-workload identity so audit logs show *which* service called, and you can revoke by removing a role assignment. On AKS use **Workload Identity** (federated service-account token → user-assigned managed identity); on App Service/Container Apps/VM just enable the system-assigned identity.

**Gotcha:** Entra auth requires the resource to have a **custom subdomain** (which the standard `https://<name>.openai.azure.com/` form gives you). Also: RBAC role assignments can take a few minutes to propagate — a fresh 401 right after `az role assignment create` is usually just propagation.

---

### Q6. `deployment_name` vs `model` — where does each appear across SDKs?
`[EASY]`

**Answer:** In Azure, the deployment name is the routing key everywhere; `model` in the response body is informational.

```python
import os

# openai SDK  -> model= is the deployment name
client.chat.completions.create(model="chat-prod", messages=[...])

# LangChain 0.3  (pip install langchain-openai)
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
llm = AzureChatOpenAI(
    azure_deployment="chat-prod",        # deployment
    api_version="2024-10-21",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    temperature=0,
)
# AzureOpenAIEmbeddings picks up AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY from env
emb = AzureOpenAIEmbeddings(azure_deployment="embed-3-large", api_version="2024-10-21")

# REST
# POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-10-21
```

**Follow-up:** *"Why is that a good design?"* → It decouples code from model choice. Swapping `gpt-4o` → `gpt-4o-mini` is a deployment change + config change, zero code change, and lets you A/B by pointing two configs at two deployments.

---

### Q7. How does the Azure OpenAI content filter work, and how do you handle it in code?
`[MEDIUM]`

**Answer:** A **separate safety system** wrapping every deployment, applied to both prompt and completion. Four harm categories — **hate, sexual, violence, self-harm** — each scored at severity **safe / low / medium / high**. Default policy blocks **medium and high**. Additional optional filters: **Prompt Shields** (jailbreak / indirect injection in documents), **protected material for text and code**, **groundedness detection**, custom blocklists.

Behaviour you must know:

| Where blocked | What you observe |
|---|---|
| **Prompt** blocked | HTTP **400**, body `error.code == "content_filter"`, with `innererror.content_filter_result` showing which category tripped |
| **Completion** blocked | HTTP **200**, `choices[0].finish_reason == "content_filter"`, content truncated/empty |
| **Annotate-only** mode | Nothing blocked; severities returned in `prompt_filter_results` / `choices[].content_filter_results` so you can decide |
| Streaming | Filtering is applied in chunks; a stream can be cut mid-way with `finish_reason="content_filter"` |

**Code:**
```python
import openai

def safe_chat(client, deployment: str, messages: list[dict]) -> str:
    try:
        r = client.chat.completions.create(model=deployment, messages=messages, max_tokens=512)
    except openai.BadRequestError as e:
        body = getattr(e, "body", None) or {}
        if (body.get("code") or body.get("error", {}).get("code")) == "content_filter":
            # log category+severity for audit, return a safe canned message
            return "I can't help with that request."
        raise

    choice = r.choices[0]
    if choice.finish_reason == "content_filter":
        return "The response was withheld by our safety policy."
    return choice.message.content or ""
```

**Gotcha (real production pain):** legitimate domains false-positive. Healthcare ("self-harm risk assessment"), insurance claims (violence), security research (harmful content). Fix path: request a **modified content filter** (severity thresholds raised, or annotate-only for specific categories) through the Azure Limited Access process — you do *not* just retry.

**Follow-up:** *"Do you still need your own guardrails if Azure filters?"* → Yes. Azure filters harm categories; it does **not** stop prompt injection reliably, PII leakage, off-topic use, hallucinated financial advice, or an agent calling a dangerous tool. Layer: input validation → content filter → business guardrail (topic/PII/grounding check) → output schema validation → tool allow-list.

---

### Q8. Regional model availability is inconsistent. What's your strategy?
`[MEDIUM]`

**Answer:** Treat "region" as a deployment concern, not a code concern, and design for **multi-region from day one** because quota and model availability differ per region and change over time.

Playbook:
1. **Pick a primary region** by three constraints in order: data-residency/legal → model + version availability → quota headroom & latency from your compute.
2. **Deployment type choice.** *Standard (regional)* = data processed in that region, strictest residency. *Data Zone* = processed within a geography (EU / US) — better availability, still bounded. *Global Standard* = best availability & throughput, weakest residency. State the trade-off out loud; it's an architect-level signal.
3. **Deploy the same logical deployment name into 2+ regions.** Config holds a list of endpoints; the client picks primary, fails over on 429/5xx (Q17).
4. **Keep compute near the model.** Cross-region calls add 30–150 ms per hop; for an agent doing 6 LLM calls that's up to ~1 s of pure network.
5. **Embeddings must not drift.** If you re-embed on a different model/version your vector index is invalid. Pin the embedding model version, store `embedding_model` + `dim` as index metadata, and re-index deliberately.
6. **Front it with Azure API Management** (or a small internal gateway) so region routing, retries, token metering and per-tenant quotas live in one place instead of in every service.

---

## 2. Authentication, Networking & Secrets

### Q9. Where do secrets live for an Azure-hosted Python AI service?
`[EASY]`

**Answer:** Ideally **nowhere** — use managed identity. For the secrets you genuinely can't avoid (3rd-party API keys, DB passwords), use **Azure Key Vault** and never environment-baked values in the image.

Order of preference:
1. **Managed identity + RBAC** (Azure OpenAI, Storage, Service Bus, Cosmos, AI Search all support it). Zero secrets.
2. **Key Vault + managed identity to read it**, injected at runtime via the **Key Vault CSI Secrets Store driver** (AKS) or Key Vault references (App Service / Container Apps `@Microsoft.KeyVault(...)`).
3. **Kubernetes Secret / env var** — only for low-sensitivity config; base64 is not encryption; enable etcd encryption + RBAC.
4. **Never:** secret in the Docker image, in git, in the CI log, in the prompt, in a client-side call.

**Code (runtime fetch, cached):**
```python
import os
from functools import lru_cache
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

@lru_cache(maxsize=1)
def _kv() -> SecretClient:
    return SecretClient(vault_url=os.environ["KEY_VAULT_URL"],
                        credential=DefaultAzureCredential())

@lru_cache(maxsize=32)
def secret(name: str) -> str:
    return _kv().get_secret(name).value
```

**Gotcha:** cache secrets (Key Vault is rate-limited and adds latency) but give the cache a TTL so rotation actually takes effect — `lru_cache` forever means a rotated key never propagates until restart. In prod use a TTL cache or restart-on-rotation via Event Grid.

---

### Q10. How do you network-isolate Azure OpenAI so traffic never touches the public internet?
`[MEDIUM]`

**Answer:** **Private Endpoint + Private DNS + `publicNetworkAccess: Disabled`.**

1. Create a **Private Endpoint** for the Azure OpenAI resource into your app's VNet subnet → it gets a private IP.
2. Link the **Private DNS zone** `privatelink.openai.azure.com` to the VNet so `myres.openai.azure.com` resolves to the private IP.
3. Set the resource's `publicNetworkAccess = Disabled` (or a firewall allow-list of your egress IPs / VNet subnets as a weaker alternative).
4. Do the same for Key Vault (`privatelink.vaultcore.azure.net`), AI Search (`privatelink.search.windows.net`), Storage, Cosmos.
5. Egress control: route outbound through **Azure Firewall / NAT Gateway** with FQDN rules so a compromised pod can't exfiltrate.
6. Combine with Entra auth — network isolation is *not* authentication; you need both (defense in depth).

**Follow-up:** *"Your CI runner is outside the VNet, how does it deploy?"* → Control-plane operations (creating deployments) go over ARM, which is separate from the data plane; or use a self-hosted runner / private build agent inside the VNet for anything that needs data-plane access (e.g. eval runs against the private endpoint).

---

### Q11. Multi-tenant SaaS on one Azure OpenAI resource — how do you isolate tenants?
`[HARD]`

**Answer:** Isolation happens at four layers, and you should name all four.

| Layer | Mechanism |
|---|---|
| **Identity** | Tenant ID from a validated JWT, never from a request body/header the client controls |
| **Data** | Per-tenant vector index or a mandatory `tenant_id` filter pushed into every retrieval query at the data-access layer, not in the prompt. Enforce in code that no query object leaves without the filter |
| **Quota / noisy neighbour** | Per-tenant token budget in Redis (sliding window on *tokens*, not requests). Optionally separate Azure OpenAI **deployments** per tier so a whale tenant's TPM can't starve others |
| **Blast radius** | Separate resource/subscription for regulated or largest tenants; separate encryption keys (CMK) if contractually required |

**Code (token-budget guard):**
```python
import os, time
import redis.asyncio as redis

r = redis.from_url(os.environ["REDIS_URL"])

async def check_and_consume(tenant: str, tokens: int, limit_per_min: int) -> bool:
    """Fixed-window token budget. Returns False if the tenant is over budget."""
    key = f"tpm:{tenant}:{int(time.time() // 60)}"
    used = await r.incrby(key, tokens)
    if used == tokens:
        await r.expire(key, 120)
    return used <= limit_per_min
```
This is the simple **fixed-window** version (cheap, one round trip, but allows a 2× burst across a window boundary); Q39 has the token-bucket Lua script if you need smooth refill. Reserve an estimate before the call (`estimated_prompt_tokens + max_tokens`), reconcile with `response.usage` after. Return **429 with `Retry-After`** to the tenant, not a 500.

**Gotcha:** never rely on the system prompt for tenant isolation ("only answer about tenant Acme"). That's one prompt injection away from a cross-tenant data breach — which is a reportable incident, not a bug.

---

### Q12. What does "Azure doesn't train on your data" actually mean, technically?
`[MEDIUM]`

**Answer:** Three separate claims, and you should separate them:
1. **No training.** Your prompts/completions/embeddings/fine-tuning data are not used to train or improve Microsoft or OpenAI models. Contractual, in the product terms.
2. **Abuse monitoring retention.** By default prompts+completions can be stored **up to 30 days** in the same region, encrypted, accessible only to authorized Microsoft reviewers on a confirmed abuse signal.
3. **You can turn (2) off.** Approved customers (Limited Access / "modified abuse monitoring" application) get **zero data retention** — no storage at all. Regulated clients almost always want this; it takes an approval cycle, so raise it early in a project.

Also: fine-tuned models are **your** private weights in your resource; the base model isn't updated by your data. Your data is encrypted at rest with Microsoft-managed keys by default, **customer-managed keys (CMK)** optional.

---

### Q13. Compare identity options for a Python app calling Azure OpenAI.
`[EASY]`

**Answer:**

| Option | Rotation | Audit granularity | Use when |
|---|---|---|---|
| API key (`api-key` header) | Manual, 2 keys for zero-downtime rotation | Resource-level only — can't tell who called | Local dev, quick POC, non-Azure compute with no federation |
| Service principal + client secret | Manual, secret expiry | Per-SP | Non-Azure compute (on-prem, other cloud) |
| **Managed identity** (system or user-assigned) | **Automatic, no secret** | Per-identity | **Any Azure compute — default choice** |
| Workload Identity Federation (AKS, GitHub Actions OIDC) | Automatic, no secret | Per service account / per repo+branch | AKS pods, CI/CD deploys |
| On-behalf-of user token | Per user session | **Per end user** | When you need the *user's* identity in audit logs / downstream ACLs |

`DefaultAzureCredential` walks a chain (env vars → workload identity → managed identity → Azure CLI → …), which is exactly why the same code works on your laptop and in the cluster. In prod, prefer the **specific** credential (`ManagedIdentityCredential(client_id=...)`) to avoid slow fallback attempts and surprise identities.

---

## 3. Quota, Throughput & Reliability (429s, PTU)

### Q14. Explain TPM and RPM quota on Azure OpenAI.
`[MEDIUM]`

**Answer:** Quota is **Tokens-Per-Minute (TPM)**, allocated per **subscription × region × model family**, and you then split that pool across deployments.

- You assign TPM when creating a deployment; the sum across deployments can't exceed your regional quota.
- **RPM is derived from TPM** — Azure provisions requests-per-minute proportionally (commonly **6 RPM per 1,000 TPM** for GPT chat models). So a 10K TPM deployment ≈ 60 RPM. Small-prompt/high-request workloads hit the **RPM** wall long before the TPM wall.
- The limiter is evaluated on **short sliding windows (~1s and ~10s)**, not a clean 60-second bucket — so a burst of 50 requests in one second 429s even if your minute-average is fine. **Smooth your traffic.**
- Rate limiting counts **prompt tokens + `max_tokens` you requested** (an estimate), reconciled against actual usage. Setting `max_tokens=4096` "just in case" burns quota you never use.

**Follow-up:** *"You're at 60 RPM and need 300."* → (a) request quota increase, (b) spread across regions/deployments with a router, (c) batch multiple items per call, (d) drop `max_tokens` to a realistic value, (e) cache, (f) move the high-volume path to a cheaper/smaller model, (g) PTU for the guaranteed floor.

---

### Q15. PTU vs pay-as-you-go — when do you buy provisioned throughput?
`[HARD]`

**Answer:** PTU (Provisioned Throughput Units) buys **reserved capacity** with predictable latency and no per-token billing; PAYG bills per token with shared, best-effort capacity.

| | Pay-as-you-go (Standard/Global Standard) | Provisioned (PTU) |
|---|---|---|
| Billing | Per 1K tokens consumed | Per PTU per hour/month/year (reservations discount heavily) |
| Capacity | Shared pool, subject to 429 under load | Reserved, yours |
| Latency | Variable, noisy-neighbour sensitive | Consistent, much tighter p99 |
| Overflow | 429 → you retry | 429 when you exceed your PTU; optional **spillover** to a PAYG deployment |
| Min commitment | None | Minimum PTU allocation per model + region |
| Good for | Spiky, low/medium volume, dev, experiments | Steady high volume, latency SLAs, interactive UX |

**How to decide (say this):** "Compute the break-even. Take steady-state tokens/min at peak, convert to required PTU using Microsoft's capacity calculator in the portal, price that against your monthly PAYG token spend. Below break-even, PAYG. Above it — or when a latency SLA exists — PTU for the baseline and PAYG spillover for the peak. That hybrid is the standard enterprise shape."

Also mention **Batch deployments**: async, 24-hour turnaround target, roughly **50% cheaper**, and it doesn't consume your interactive quota. Perfect for nightly re-embedding, bulk classification, eval runs, backfills.

---

### Q16. What exactly does a 429 look like and how do you respond?
`[MEDIUM]`

**Answer:** HTTP **429**, and Azure tells you how long to wait via the **`Retry-After`** header (seconds) or **`retry-after-ms`** (milliseconds). **Honour the header first**; only fall back to exponential backoff with jitter if it's absent. Never retry immediately, never retry in a tight loop, and cap total attempts.

**Code (production-shaped, async):**
```python
import asyncio, random, logging
import openai
from openai import AsyncAzureOpenAI

log = logging.getLogger(__name__)

def _retry_after_seconds(exc: openai.APIStatusError) -> float | None:
    h = getattr(getattr(exc, "response", None), "headers", None) or {}
    if (ms := h.get("retry-after-ms")):
        try: return float(ms) / 1000.0
        except ValueError: pass
    if (s := h.get("retry-after")):
        try: return float(s)
        except ValueError: pass
    return None

async def chat_with_retry(client: AsyncAzureOpenAI, *, deployment: str,
                          messages: list[dict], max_attempts: int = 5, **kw):
    base, cap = 1.0, 30.0
    for attempt in range(max_attempts):
        try:
            return await client.chat.completions.create(
                model=deployment, messages=messages, **kw
            )
        except openai.RateLimitError as e:              # 429 (subclass of APIStatusError -> must come first)
            last, wait = e, _retry_after_seconds(e)
        except openai.APIStatusError as e:              # 5xx only
            if e.status_code < 500:
                raise                                    # 400/401/403/404 -> never retry
            last, wait = e, None
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            last, wait = e, None

        if attempt == max_attempts - 1:
            raise last                                   # bare `raise` here would fail:
                                                         # exc_info is cleared once the except block exits
        if wait is None:                                 # decorrelated jitter backoff
            wait = min(cap, random.uniform(base, base * 3 * (2 ** attempt)))
        log.warning("azure_openai_retry attempt=%s sleep=%.2fs", attempt + 1, wait)
        await asyncio.sleep(wait)
```

**Gotcha:** the OpenAI SDK retries internally (`max_retries=2` by default, i.e. **3 HTTP calls** per `create()`). If you also wrap it in `tenacity` with 5 attempts you get 3 × 5 = **15 real calls** and a worst-case latency in the minutes. **Set `max_retries=0` on the client if you own the retry policy** — or use the SDK's and don't wrap. Pick one. Interviewers love this one.

**Follow-up:** *"What if you're streaming and the 429 happens mid-stream?"* → Retrying restarts generation from scratch. Either buffer the first chunk before flushing headers to the client, or emit an SSE `error` event and let the UI retry. Don't silently restart into the same open stream — the user sees duplicated text.

---

### Q17. Beyond retry — what's the full resilience stack for LLM calls?
`[HARD]`

**Answer:** Six layers, in order of when they fire:

1. **Timeout** (per attempt, e.g. 30 s non-streaming / 120 s streaming). Without it a hung socket ties up a worker slot forever.
2. **Retry** with `Retry-After` + jitter, only on 429/5xx/connection errors.
3. **Bulkhead** — a semaphore capping in-flight LLM calls per process so one slow model can't consume every worker.
4. **Circuit breaker** — after N consecutive failures, stop calling for T seconds and fail fast. Prevents retry storms making an incident worse.
5. **Fallback** — secondary deployment in another region, then a cheaper/smaller model, then cached/canned answer.
6. **Graceful degradation** — return retrieval results without generation ("here are the 3 most relevant passages"), or queue the request for async delivery. A degraded answer beats a 500.

**Code (breaker + region fallback, dependency-free):**
```python
import time, asyncio
from dataclasses import dataclass, field
from openai import AsyncAzureOpenAI          # needed: dataclass annotations are evaluated at class creation
# chat_with_retry as defined in Q16

@dataclass
class CircuitBreaker:
    fail_threshold: int = 5
    reset_after: float = 30.0
    _fails: int = 0
    _opened_at: float = 0.0

    @property
    def is_open(self) -> bool:
        if self._fails < self.fail_threshold:
            return False
        if time.monotonic() - self._opened_at > self.reset_after:
            self._fails = self.fail_threshold - 1     # half-open: allow one probe
            return False
        return True

    def record(self, ok: bool) -> None:
        if ok:
            self._fails = 0
        else:
            self._fails += 1
            self._opened_at = time.monotonic()

@dataclass
class Router:
    """Ordered endpoints: primary region, secondary region, cheap model."""
    targets: list[tuple[AsyncAzureOpenAI, str]]
    breakers: dict[int, CircuitBreaker] = field(default_factory=dict)
    sem: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(64))

    async def chat(self, messages: list[dict], **kw):
        last: Exception | None = None
        for i, (client, deployment) in enumerate(self.targets):
            cb = self.breakers.setdefault(i, CircuitBreaker())
            if cb.is_open:
                continue
            try:
                async with self.sem:
                    r = await chat_with_retry(client, deployment=deployment,
                                              messages=messages, max_attempts=2, **kw)
                cb.record(True)
                return r
            except Exception as e:
                cb.record(False)
                last = e
        raise RuntimeError("all LLM targets unavailable") from last
```

**Say this about the `except Exception`:** in real code you narrow it — a `BadRequestError` (malformed messages, content filter, context-length exceeded) will fail identically on every target, so failing over just burns latency and trips all your breakers. Fail over on 429/5xx/connection errors only; re-raise 4xx immediately.

---

### Q18. How do you handle a request that takes 4 minutes (deep agent run)?
`[MEDIUM]`

**Answer:** **Don't hold an HTTP connection.** Switch to an async job pattern:

`POST /jobs` → returns `202 Accepted` + `job_id` → work goes onto a queue (Azure Service Bus / Redis / SQS) → a worker pool executes the agent → client polls `GET /jobs/{id}` or receives an SSE/WebSocket push / webhook on completion.

Why: load balancers, API gateways and browsers all have idle timeouts (see Q37); a 4-minute synchronous request will be cut somewhere you don't control, and a redeploy mid-request loses the work. A queue gives you retries, dead-lettering, backpressure, and independent scaling of API vs workers.

**Python options:** `arq` (asyncio-native, Redis, best fit for async LLM code), `Celery` (mature, huge ecosystem, sync-first), `Dramatiq`, or **Azure Service Bus + a plain asyncio consumer**. For LangGraph specifically: use a **checkpointer** so a worker crash resumes mid-graph instead of restarting.

**Gotcha:** make jobs **idempotent** (idempotency key from the client) and set **visibility timeout > worst-case runtime**, otherwise the queue redelivers while the first worker is still running and you pay twice and may double-write.

**Middle ground:** if the UX needs live feedback, keep the connection but **stream progress events** (SSE) — a stream that emits a token every second never hits an idle timeout.

---

### Q19. Streaming through load balancers breaks. Why, and what's the fix?
`[HARD]`

**Answer:** Because intermediaries **buffer** by default. nginx/ALB/App Gateway/CDN accumulate the response before forwarding, so the browser sees nothing for 20 seconds and then everything at once — streaming silently becomes non-streaming.

Fixes, layer by layer:

| Layer | Fix |
|---|---|
| **nginx** | `proxy_buffering off;` `proxy_cache off;` `proxy_read_timeout 300s;` `chunked_transfer_encoding on;` and use **HTTP/1.1** upstream (`proxy_http_version 1.1; proxy_set_header Connection "";`) |
| **App code** | Send header `X-Accel-Buffering: no` (nginx honours it per-response), `Cache-Control: no-cache`, `Content-Type: text/event-stream` |
| **AWS ALB** | Raise idle timeout (default **60s**); ALB doesn't buffer, but CloudFront in front of it may — disable caching for the SSE path |
| **Azure** | App Gateway: raise request timeout; **Front Door**: raise origin response timeout and bypass caching for the stream route |
| **Cloudflare / CDN** | Bypass cache + disable compression on the SSE route (gzip buffering kills streams) |
| **Gunicorn/uvicorn** | Use **async** workers; sync workers can't stream concurrently |
| **Keep-alive** | Emit an SSE comment `: ping\n\n` every 15 s so idle timers never fire during long first-token latency |

**Code (FastAPI SSE endpoint that survives proxies):**
```python
import json, os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncAzureOpenAI

app = FastAPI()
aclient = AsyncAzureOpenAI(                      # built once at import/lifespan, reused
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-10-21",
)

async def token_stream(messages: list[dict], deployment: str):
    stream = await aclient.chat.completions.create(
        model=deployment, messages=messages, stream=True,
        stream_options={"include_usage": True},          # usage in the final chunk
    )
    try:
        async for chunk in stream:
            if chunk.choices and (delta := chunk.choices[0].delta.content):
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            if getattr(chunk, "usage", None):        # only the final chunk; its `choices` is []
                yield f"data: {json.dumps({'usage': chunk.usage.model_dump()})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

@app.post("/chat/stream")
async def chat_stream(body: dict):
    return StreamingResponse(
        token_stream(body["messages"], deployment="chat-prod"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",     # <-- the line that fixes nginx
        },
    )
```

**Gotcha:** with SSE, an exception thrown *after* the first byte cannot become an HTTP 500 — headers are already sent. That's why the generator catches and emits an `event: error` frame. Also disable response compression middleware on this route.

---

### Q20. What's your timeout budget for a RAG endpoint?
`[MEDIUM]`

**Answer:** Budget top-down from the user-facing SLO and make every inner timeout strictly smaller than its caller's.

Example for a p95 SLO of 6 s:

| Hop | Timeout | Note |
|---|---|---|
| Browser / client | 60 s | streaming, so wall-clock is fine |
| API gateway / ingress | 65 s | must exceed app |
| App request deadline | 45 s hard cap | returns partial/degraded past this |
| Embedding call | 3 s, 1 retry | tiny payload; if it's slow, something is wrong |
| Vector search | 1 s | else drop to keyword-only |
| Reranker | 2 s | optional stage — skip on timeout, don't fail |
| LLM (non-stream) | 30 s | |
| LLM first token (stream) | 10 s | if no first token in 10 s, fail over to region 2 |

**Rules:** total inner timeouts + retries must be **less than** the outer deadline, or you return a gateway 504 while still burning tokens. Propagate a deadline (`asyncio.timeout()` / `contextvars`) rather than hardcoding per-call values, and **cancel** downstream work when the client disconnects (`await request.is_disconnected()`), otherwise you pay for tokens nobody reads.

---

## 4. Azure AI Platform for RAG

### Q21. What is Azure AI Foundry and how does it relate to Azure OpenAI?
`[EASY]`

**Answer:** **Azure AI Foundry** (formerly Azure AI Studio; it absorbed Azure OpenAI Studio) is the unified portal + SDK for building GenAI apps on Azure. Azure OpenAI is one *model provider* inside it.

What it gives you:
- **Model catalog** — OpenAI models plus Meta/Mistral/Cohere/Microsoft Phi and others, deployable as serverless APIs or managed endpoints.
- **Projects & hubs** — a workspace with shared connections (to AI Search, Storage, Key Vault), RBAC, and per-project isolation.
- **Prompt flow** — visual + YAML orchestration of prompt → retrieval → Python nodes, with built-in batch evaluation and one-click deploy to a managed online endpoint.
- **Evaluations** — built-in metrics (groundedness, relevance, coherence, fluency, similarity) plus safety evaluators, runnable on a dataset.
- **Content Safety** and tracing/monitoring integration with Application Insights.

**How to position it in the interview:** "Foundry is great for prototyping, evaluation and for non-engineers to iterate on prompts. Our production serving path was our own FastAPI service calling the Azure OpenAI endpoint directly — I didn't want a portal in the critical path. We used Foundry's evaluation SDK in CI."

---

### Q22. Azure AI Search for RAG — what do you need to know?
`[MEDIUM]`

**Answer:** It's Azure's managed retrieval engine and the default vector store in Azure RAG architectures.

Key capabilities to name:
- **Vector search** with HNSW (tunable `m`, `efConstruction`, `efSearch`) or exhaustive KNN; metrics cosine / dotProduct / euclidean.
- **Hybrid search** — BM25 keyword + vector in one query, fused with **RRF (Reciprocal Rank Fusion)**. This is the single biggest quality win over pure vector.
- **Semantic ranker** — an L2 cross-encoder-style reranker over the top ~50 results, returns `@search.rerankerScore` and extractive captions/answers. Costs extra; usually worth it.
- **Filters** — OData filter expressions on `filterable` fields. Essential for tenant/ACL enforcement: `filter="tenant_id eq 'acme' and group_ids/any(g: search.in(g, 'g1,g2'))"`.
- **Integrated vectorization** — indexers + skillsets chunk and embed documents automatically (Text Split skill + AzureOpenAIEmbedding skill), so you don't build an ingestion pipeline for simple cases.
- **Index / Indexer / Skillset / Data source** — the four ARM objects; know the words.
- **Security trimming** — store the ACL group IDs on the doc, resolve the user's groups from their token, and push it into the filter. Never filter after retrieval.

**Gotcha:** vector fields have a fixed `dimensions` — changing embedding model means a **new index** and a re-index, plus an alias swap for zero downtime. Use **index aliases** so app config never changes.

---

### Q23. What is Azure OpenAI "On Your Data" and would you ship it?
`[MEDIUM]`

**Answer:** A server-side RAG feature: you pass a `data_sources` block on the chat completions call and Azure does retrieval (from AI Search, Cosmos, Blob) + prompt assembly + citation generation for you.

**Code:**
```python
import os
# `client` = AzureOpenAI(...) from Q4, but with a PREVIEW api-version, e.g. "2025-01-01-preview"

resp = client.chat.completions.create(
    model="chat-prod",
    messages=[{"role": "user", "content": "What is our refund window?"}],
    extra_body={
        "data_sources": [{
            "type": "azure_search",
            "parameters": {
                "endpoint": os.environ["SEARCH_ENDPOINT"],
                "index_name": "policies",
                "authentication": {"type": "system_assigned_managed_identity"},
                "query_type": "vector_semantic_hybrid",
                "top_n_documents": 5,
                "strictness": 3,
                "in_scope": True,
                "embedding_dependency": {
                    "type": "deployment_name",
                    "deployment_name": "embed-3-large",
                },
            },
        }]
    },
)
answer = resp.choices[0].message.content
citations = resp.choices[0].message.model_extra["context"]["citations"]
```
(Preview-surface feature — needs a preview `api-version`.)

**Verdict to give:** "Excellent for a two-day PoC and for demos with citations out of the box. I wouldn't ship a complex product on it: you lose control of chunking, query rewriting, reranking, multi-index routing, ACL logic and prompt content — and those are exactly the levers that move accuracy. We used it to prove value in week one, then replaced it with an explicit pipeline."

---

### Q24. Prompt Flow — what is it and when is it useful?
`[EASY]`

**Answer:** Azure's DAG-based orchestration tool for LLM apps: nodes are LLM prompts (Jinja2 `.jinja2` files), Python functions, or built-in tools; the flow is defined in `flow.dag.yaml`. Runs locally via the `promptflow` CLI/VS Code extension or in Foundry.

Where it earns its place:
- **Batch runs + evaluation flows** over a golden dataset — you get a comparison table across prompt variants.
- **Variants** — define 3 versions of a prompt node and evaluate them side by side.
- **Traceability** — every node's input/output logged; good for prompt engineers who aren't Python devs.
- Deploy to a managed online endpoint with autoscale.

**Where it doesn't fit:** cyclic/agentic control flow (use LangGraph), heavy custom Python, or teams that already have a FastAPI service. Say: "We kept orchestration in LangGraph and borrowed Prompt Flow's evaluation flows for the offline scoring harness."

---

### Q25. How do you monitor and control Azure OpenAI cost?
`[MEDIUM]`

**Answer:** Three levels: platform, application, and design.

**Platform**
- Azure Cost Management: **budgets + alerts** per resource group; tag every resource with `env`, `product`, `cost-center`.
- Azure Monitor metrics on the resource: *Azure OpenAI Requests*, *Processed Prompt Tokens*, *Generated Completion Tokens*, plus 429 counts. Alert on token-rate anomalies — a runaway agent loop shows up here first.
- Separate deployments (or resources) per environment so dev spend never hides inside prod.

**Application** — log `usage.prompt_tokens` / `completion_tokens` / `cached_tokens` on **every** call with dimensions `tenant`, `feature`, `model`, `user`, and compute cost in your own code from a price table in config:
```python
PRICES = {  # USD per 1M tokens — keep in config, refresh from the pricing page
    "gpt-4o":      {"in": 2.50, "out": 10.00},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}
def cost_usd(model: str, pin: int, pout: int) -> float:
    p = PRICES[model]
    return (pin * p["in"] + pout * p["out"]) / 1_000_000
```

**Design (the biggest lever, in order of impact)**
1. **Model routing** — small model for classification/extraction/routing, big model only for final synthesis. Typically 60–80% cost cut.
2. **Prompt caching** — keep the long static prefix (system prompt, few-shots, schema) **at the front** and identical; cached input tokens are discounted (commonly ~50% on pay-as-you-go).
3. **Semantic + exact caching** (Q40) — 20–40% hit rate on real support traffic.
4. **Retrieval discipline** — top-k 20 → 5 after reranking is a direct 4× cut on prompt tokens.
5. **`max_tokens` realistic**, and instruct brevity — output tokens cost ~4× input.
6. **Batch API** for offline work (~50% cheaper).
7. **Per-tenant/per-user budget caps** so one bug can't produce a five-figure bill overnight.

**Say a number:** "We cut cost/query from ~$0.031 to ~$0.009 with a mini-model router plus caching plus dropping top-k from 20 to 5, with no measurable drop in answer quality on our 200-question eval set."

---

## 5. AWS & GCP Equivalents (breadth)

### Q26. Give me the Azure → AWS → GCP mapping.
`[EASY]`

**Answer:**

| Capability | Azure | AWS | GCP |
|---|---|---|---|
| Managed LLM API | Azure OpenAI | **Amazon Bedrock** | **Vertex AI** (Gemini + Model Garden) |
| GenAI dev portal | Azure AI Foundry | Bedrock Studio / SageMaker | Vertex AI Studio |
| Managed RAG | AI Search + "On Your Data" | Bedrock **Knowledge Bases**, Kendra | Vertex AI Search / RAG Engine |
| Vector store | Azure AI Search, Cosmos DB, PostgreSQL `pgvector` | OpenSearch Serverless (vector engine), Aurora/RDS `pgvector`, MemoryDB | Vertex Vector Search, AlloyDB/Cloud SQL `pgvector` |
| Agents | AI Foundry Agent Service, Semantic Kernel | Bedrock **Agents** | Vertex AI **Agent Builder / ADK** |
| Guardrails | Content filter + Content Safety | Bedrock **Guardrails** | Vertex safety filters / Model Armor |
| Secrets | Key Vault | Secrets Manager / Parameter Store | Secret Manager |
| Identity | Entra ID + managed identity | IAM roles / IRSA | IAM + Workload Identity |
| Serverless container | Container Apps / Functions | Fargate / Lambda | Cloud Run |
| Managed K8s | AKS | EKS | GKE |
| Queue | Service Bus / Storage Queues | SQS | Pub/Sub |
| Tracing | Application Insights | CloudWatch + X-Ray | Cloud Trace |

---

### Q27. Bedrock in one minute — what's the API and what's distinctive?
`[MEDIUM]`

**Answer:** Bedrock is multi-provider (Anthropic, Meta, Mistral, Amazon Nova, Cohere, AI21) behind **one** API, with IAM instead of API keys. The modern unified call is **`converse` / `converse_stream`** on the `bedrock-runtime` boto3 client — it normalises messages, system prompts, tool use and streaming across every provider, so you don't hand-roll each vendor's JSON body (`invoke_model` is the older per-model-JSON path).

**Code:**
```python
import boto3
brt = boto3.client("bedrock-runtime", region_name="us-east-1")   # IAM auth, no key

resp = brt.converse(
    modelId="<inference-profile-or-model-id>",
    messages=[{"role": "user", "content": [{"text": "Summarise RAG in two lines."}]}],
    system=[{"text": "You are concise."}],
    inferenceConfig={"maxTokens": 256, "temperature": 0.2},
)
print(resp["output"]["message"]["content"][0]["text"])
print(resp["usage"])          # inputTokens / outputTokens / totalTokens
```
Distinctive pieces: **Guardrails** (attach a policy ID to filter topics/PII/harm, with a contextual-grounding check), **Knowledge Bases** (managed chunk+embed+retrieve, `retrieve_and_generate`), **Agents** (managed tool-calling with action groups), **provisioned throughput** (the PTU analogue), and **cross-region inference profiles** for capacity.

---

### Q28. Vertex AI in one minute.
`[EASY]`

**Answer:** Google's managed platform. Gemini models via the **`google-genai`** SDK (`from google import genai`; `genai.Client(vertexai=True, project=..., location=...)`), which is the current unified SDK replacing the older `vertexai.generative_models` and `google-generativeai` packages. Auth via **ADC** (Application Default Credentials) / service accounts / Workload Identity — same "no API key in code" story as Azure MI. Vertex adds Model Garden (open models), Vertex AI Search & RAG Engine for managed RAG, Vector Search (ScaNN-based ANN), Agent Builder/ADK for agents, grounding-with-Google-Search, and safety filters with configurable thresholds. Long context (1M+ tokens on Gemini Pro tiers) is its headline differentiator.

**Interview move:** don't oversell. "I've worked deepest on Azure OpenAI; I know the Bedrock `converse` API and Vertex's shape well enough to port a service, and the abstraction we wrote (a `ChatProvider` protocol) meant swapping providers was a ~200-line adapter."

---

## 6. Containerizing a FastAPI + LLM Service

### Q29. Write a production multi-stage Dockerfile for a FastAPI + LLM service.
`[MEDIUM]`

**Answer:** Multi-stage, slim base, `uv` for fast reproducible installs, cache mount for layers, **non-root** user, no build toolchain in the runtime image.

**Code (`Dockerfile`):**
```dockerfile
# syntax=docker/dockerfile:1.9

########## Stage 1: build the virtualenv ##########
FROM python:3.11-slim-bookworm AS builder

# uv: pin an exact released tag in real projects
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/app/.venv

WORKDIR /app

# Dependency layer: changes only when lockfile changes -> maximal cache reuse
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# App layer
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

########## Stage 2: runtime ##########
FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tini \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    PORT=8000

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/healthz || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn_worker.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "180", \
     "--graceful-timeout", "60", \
     "--keep-alive", "75", \
     "--access-logfile", "-", "--error-logfile", "-"]
```

Pip-only variant of the dependency layer (if they don't use `uv`):
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt
```

**Points to say out loud:** slim over alpine (musl breaks/slows manylinux wheels for numpy, tokenizers, pydantic-core); layer order = lockfile before source; non-root UID 10001 matches a `runAsNonRoot` pod security context; `tini` reaps zombies and forwards SIGTERM so graceful shutdown works; `.dockerignore` excludes `.git`, `.venv`, `tests`, `*.ipynb`, `.env`.

**Gotcha:** `uvicorn_worker.UvicornWorker` comes from the separate `uvicorn-worker` package — the in-tree `uvicorn.workers.UvicornWorker` is deprecated in recent uvicorn. Know both names.

---

### Q30. How many gunicorn workers, and why is the answer different for an LLM service?
`[HARD]`

**Answer:** The classic formula `workers = (2 × CPU cores) + 1` is for **sync/WSGI** workers where one worker = one concurrent request and the bottleneck is CPU. **An LLM service is ~99% I/O wait**, so that formula massively under-provisions concurrency and over-provisions memory.

| Workload | Model | Sizing |
|---|---|---|
| Flask/Django sync, CPU-bound | 1 request per worker | `(2 × cores) + 1` |
| FastAPI `async def`, LLM/network-bound | 1 worker = 1 event loop = **thousands** of concurrent awaits | **`workers ≈ cores`** (often 1–4); concurrency comes from the loop, not the worker count |
| FastAPI with `def` (sync) endpoints | Runs in a threadpool (AnyIO, default 40 threads) | Threads cap concurrency; convert to `async def` or raise the threadpool limiter |

**Sizing an async LLM service properly:**
1. Concurrency ceiling is set by your **upstream quota**, not your CPU. If Azure gives you 60 RPM and each call takes 3 s, ~3 concurrent calls saturate it. More workers just produce more 429s.
2. Set workers = number of CPU cores available to the container (`cpu limit`), typically 1–4 in K8s, because each worker is a separate process with its own memory (~200–500 MB for a LangChain app — a real constraint).
3. Cap in-flight work explicitly with `--limit-concurrency` (uvicorn) or an `asyncio.Semaphore`, and shed load with 429 beyond it. Unbounded queueing turns into timeouts for everyone.
4. Scale *horizontally* (more pods) rather than more workers per pod — better failure isolation and simpler autoscaling.

**Gotcha (the #1 real bug):** a blocking call inside `async def` — `requests.post()`, `time.sleep()`, a sync SDK client, `psycopg2`, a local tokenizer/embedding model — **blocks the entire event loop**, so all N concurrent requests on that worker stall. Fix: use async clients (`AsyncAzureOpenAI`, `httpx.AsyncClient`) or push blocking work off with `await asyncio.to_thread(fn, ...)`.

**Follow-up:** *"How do you prove your worker count is right?"* → Load test with a realistic latency distribution (locust/k6), plot p95 latency and 429 rate vs concurrency, find the knee. Report the number.

---

### Q31. How do you shut a container down without dropping in-flight LLM requests?
`[MEDIUM]`

**Answer:** Graceful drain, coordinated across K8s and the app.

1. K8s sends **SIGTERM** and simultaneously removes the pod from Endpoints — but ingress/kube-proxy update is *eventually* consistent, so add a `preStop` sleep of 5–15 s to let load balancers stop sending new traffic before you stop accepting it.
2. Gunicorn/uvicorn stop accepting new connections, finish in-flight requests within `--graceful-timeout`.
3. `terminationGracePeriodSeconds` must be **> preStop sleep + graceful-timeout + slack** (for a 120 s LLM call: preStop 10 + graceful 120 → set 150).
4. FastAPI **lifespan** closes the httpx/OpenAI clients, flushes traces, drains the queue consumer.

```yaml
lifecycle:
  preStop:
    exec: { command: ["sh", "-c", "sleep 10"] }
terminationGracePeriodSeconds: 150
```
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from openai import AsyncAzureOpenAI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm = AsyncAzureOpenAI(...)           # startup
    yield
    await app.state.llm.close()                     # shutdown

app = FastAPI(lifespan=lifespan)                    # <- lifespan is wired at construction
```
Note the deprecated form: `@app.on_event("startup")` / `@app.on_event("shutdown")` still work but are **deprecated since FastAPI 0.93** in favour of the `lifespan` context manager above. Don't write `on_event` in an interview.

**Gotcha:** SSE streams are long-lived; a rolling deploy will cut them. Either cap stream duration, or have the client auto-reconnect with `Last-Event-ID` and resume from stored partial state.

---

### Q32. Image size and startup time are bad. What do you attack?
`[EASY]`

**Answer:** In order of payoff:
1. **Multi-stage** — don't ship compilers, headers, `uv`, test deps. (Typical 1.2 GB → 300 MB.)
2. **Audit dependencies.** `torch` pulled in transitively by a sentence-transformers import you don't use is ~2 GB. If you need CPU torch, install the CPU wheel index explicitly.
3. **Layer ordering** — lockfile layer before source layer, so a code change rebuilds only the last layer.
4. **`.dockerignore`** — stops the build context (and secrets) from bloating the image.
5. **Bake model artifacts** you always need (tokenizer files, small reranker) into the image rather than downloading at boot — network at startup is a cold-start and an outage dependency.
6. **`UV_COMPILE_BYTECODE=1`** — precompiles `.pyc` so the first request doesn't pay import compilation.
7. **Lazy imports** for heavy optional paths; move them behind the function that needs them.
8. Measure: `docker history <img>` shows exactly which layer is fat.

---

### Q33. What goes in `/healthz` vs `/readyz` for an LLM service?
`[MEDIUM]`

**Answer:** **Liveness = "is this process wedged?"** — must be cheap, local, and **must not call any dependency**. **Readiness = "can I serve traffic right now?"** — may check dependencies that are required to serve.

```python
from fastapi import FastAPI, HTTPException

@app.get("/healthz")          # liveness: no I/O
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")           # readiness: warm + deps reachable
async def readyz():
    if not app.state.warm:                       # model/tokenizer/index loaded
        raise HTTPException(503, "warming")
    if not await app.state.vectordb.ping():      # cached, cheap, 200ms timeout
        raise HTTPException(503, "vectordb")
    return {"status": "ready"}
```

**The critical gotcha:** never put "call Azure OpenAI" in the **liveness** probe. A provider outage would then fail liveness on every pod, K8s restarts them all, and you turn a degraded service into a total outage with a CrashLoopBackOff. Even in readiness, prefer a **cached** dependency status (updated by a background task) over a live call — otherwise probes themselves consume quota and can trigger 429s.

For slow warmup (loading an embedding model, warming a cache), use a **`startupProbe`** with `failureThreshold × periodSeconds > worst-case warmup`; liveness/readiness don't start until it passes, so you never get restart loops during a slow boot.

---

## 7. Kubernetes, Scaling & Serverless

### Q34. Sketch the Kubernetes manifest for this service — what matters?
`[MEDIUM]`

**Answer:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: rag-api }
spec:
  replicas: 3
  strategy:
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }   # never lose capacity
  selector: { matchLabels: { app: rag-api } }
  template:
    metadata:
      labels: { app: rag-api, azure.workload.identity/use: "true" }
    spec:
      serviceAccountName: rag-api            # federated -> managed identity
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
      - name: api
        image: myacr.azurecr.io/rag-api:1.14.2   # never :latest
        ports: [{ containerPort: 8000 }]
        resources:
          requests: { cpu: "500m", memory: "1Gi" }
          limits:   {              memory: "2Gi" }   # memory limit yes, CPU limit usually no
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities: { drop: ["ALL"] }
        startupProbe:
          httpGet: { path: /readyz, port: 8000 }
          periodSeconds: 5
          failureThreshold: 24                      # up to 120s warmup
        readinessProbe:
          httpGet: { path: /readyz, port: 8000 }
          periodSeconds: 5
        livenessProbe:
          httpGet: { path: /healthz, port: 8000 }
          periodSeconds: 20
          failureThreshold: 3
        lifecycle:
          preStop: { exec: { command: ["sh","-c","sleep 10"] } }
      terminationGracePeriodSeconds: 150
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector: { matchLabels: { app: rag-api } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: rag-api-pdb }
spec:
  minAvailable: 2
  selector: { matchLabels: { app: rag-api } }
```

**Talking points:** `maxUnavailable: 0` for zero-capacity-loss rollouts; **PDB** so a node drain/upgrade can't take the service to zero; **no CPU limit** (CFS throttling adds tail latency and this workload is I/O bound — keep the *request* for scheduling); memory limit yes (OOM protection); image digest/tag pinned; workload identity instead of secrets; zone spread for AZ failure.

**Gotcha in this manifest:** `readOnlyRootFilesystem: true` means anything the process writes needs an explicit `emptyDir` — `/tmp` and the `HF_HOME`/tokenizer cache from the Dockerfile in Q29 are the two that bite. Mount `emptyDir` volumes at `/tmp` and `/home/appuser/.cache`, or the pod crashes on first tokenizer load.

---

### Q35. Why is CPU-based HPA wrong here, and what do you scale on?
`[HARD]`

**Answer:** Because pods waiting on an LLM sit at **2–5% CPU while completely saturated** on concurrency. CPU-based HPA never triggers; latency climbs; users queue. It's the classic mistake for LLM gateways.

Scale on a **concurrency / backlog** signal:

| Signal | How |
|---|---|
| **In-flight requests per pod** | App exposes a Prometheus gauge `llm_inflight_requests`; HPA on `Pods` metric, target e.g. 20 |
| **Queue depth** | KEDA `azure-servicebus` / `redis` / `aws-sqs` scaler on queue length — best for the async-job pattern |
| **RPS per pod** | KEDA/Prometheus `sum(rate(http_requests_total[1m])) / pods` |
| **p95 latency** | Lagging and oscillation-prone; use as an alert, not a scaler |

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: rag-api }
spec:
  scaleTargetRef: { name: rag-api }
  minReplicaCount: 3
  maxReplicaCount: 40
  cooldownPeriod: 120
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus.monitoring:9090
      query: sum(llm_inflight_requests)      # total in-flight across pods
      threshold: "20"                        # -> ~20 in-flight per pod
  - type: azure-servicebus
    metadata:                                # `namespace` is required when using pod/workload identity
      namespace: sb-ai-prod                  # (instead of a connection-string secret)
      queueName: agent-jobs
      messageCount: "50"
    authenticationRef: { name: keda-workload-identity }
```

**The hard part to mention:** scaling out **does not create capacity** if the bottleneck is Azure OpenAI TPM — more pods just multiply 429s. So HPA is right for the *serving* tier, but you must pair it with a **token-aware admission control**: cap concurrent upstream calls globally (a Redis-backed distributed semaphore or a gateway like APIM), and shed/queue beyond it. Say this — it separates people who've run this in prod from people who've read a blog.

Also add HPA behaviour tuning: `scaleDown.stabilizationWindowSeconds: 300` so long streaming requests aren't killed by flapping.

---

### Q36. Where does agent state live if pods are stateless?
`[MEDIUM]`

**Answer:** **Outside the pod, always.** Any in-process dict dies on a rollout and breaks when the load balancer routes turn 2 to a different pod. Sticky sessions are a smell, not a solution.

| State | Store | Notes |
|---|---|---|
| Conversation history | Redis (hot, TTL) or Cosmos/Postgres (durable) | Key by `conversation_id`; store trimmed + summarised form |
| LangGraph checkpoints | Postgres/Redis checkpointer (`AsyncPostgresSaver`) | Enables resume-after-crash and human-in-the-loop |
| Long-term / semantic memory | Vector store, namespaced by user | Written asynchronously, not on the hot path |
| Scratchpad within one run | In-memory is fine — it dies with the run anyway | |
| Uploaded files / artifacts | Blob storage, signed URLs | Never the pod filesystem (`readOnlyRootFilesystem: true`) |
| Cache | Redis | Shared across pods, that's the point |
| Idempotency keys / locks | Redis with TTL | Prevents double-execution on retry |

**Follow-up:** *"Two requests for the same conversation land on two pods simultaneously."* → Take a short-lived Redis lock per `conversation_id` (`SET key val NX PX 30000`), or serialize per conversation through a queue partitioned by conversation ID. Without this you get interleaved writes and a corrupted history.

---

### Q37. Serverless for LLM APIs — what are the limits that bite?
`[MEDIUM]`

**Answer:** Cold starts and request timeouts. Know approximate numbers:

| Platform | Max request/exec time | Notes |
|---|---|---|
| **AWS Lambda** | 15 min execution | Behind API Gateway (REST) the integration timeout is 29 s by default (raisable via quota); **Function URLs + response streaming** bypass that and are the right shape for token streaming |
| **Azure Functions** | Consumption: 5 min default / 10 min max; Premium & Dedicated: configurable, effectively unbounded | Consumption cold starts hurt for fat AI dependency trees |
| **Azure Container Apps** | Long-running HTTP supported; scale-to-zero optional; KEDA built in | Usually the best Azure fit for a containerized LLM API |
| **Google Cloud Run** | Request timeout default 5 min, **max 60 min** | Streaming supported; min-instances kills cold start |
| **API Gateway (AWS REST)** | 29 s default integration timeout | The single most common "why did my LLM call 504" |
| **Azure API Management** | Configurable per-operation backend timeout | Raise it for LLM routes |

**Cold start reality for AI apps:** the image is fat (`langchain` + `openai` + `tiktoken` + maybe `torch`) so imports alone can be 3–10 s. Mitigations: **min instances / provisioned concurrency ≥ 1**, trim dependencies, lazy-import heavy modules, precompile bytecode, and keep model artifacts in the image.

**Verdict to give:** "For a chat/RAG API with streaming and steady traffic I'd pick Container Apps or Cloud Run (or AKS if the org already runs K8s) over Functions/Lambda — scale-to-zero savings don't compensate for cold-start latency on an interactive UX. Lambda/Functions are great for the *event-driven* parts: ingestion, embedding backfills, webhook handlers."

---

### Q38. Where does the API gateway fit, and what does it do for you?
`[MEDIUM]`

**Answer:** One choke point in front of every LLM route. Put **Azure API Management** (or Kong/Envoy/APISIX) there and it earns its keep:

- **AuthN/AuthZ** — JWT validation, subscription keys, mTLS — before your app burns CPU.
- **Rate limiting & quotas per tenant/subscription** — including APIM's LLM-specific **token-limit** and **token-metric** policies that count prompt/completion tokens, which is the right unit for LLM traffic.
- **Load balancing / failover across multiple Azure OpenAI backends** (multi-region, PTU-then-PAYG spillover) via a backend pool with circuit breaker rules.
- **Semantic caching** policy (APIM can cache on embedding similarity).
- **Timeouts / retries / request size limits**.
- **Observability** — one place emitting token metrics per subscriber to App Insights.
- **Payload safety** — strip/deny obvious injections, block oversized prompts.

**Gotcha:** the gateway must be configured for **streaming pass-through** (no buffering) or it defeats SSE — same class of problem as Q19.

---

### Q39. How do you rate-limit per tenant across many pods?
`[MEDIUM]`

**Answer:** Central store, atomic operation. Redis with a Lua script (or a token-bucket library) so the check-and-decrement is one round trip and race-free.

**Code (token bucket in Lua — continuous refill, atomic check-and-decrement, called from Python):**
```python
import time
import redis.asyncio as redis

LUA = """
local key    = KEYS[1]
local rate   = tonumber(ARGV[1])   -- tokens refilled per second
local burst  = tonumber(ARGV[2])   -- bucket capacity
local now    = tonumber(ARGV[3])
local cost   = tonumber(ARGV[4])

local b = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(b[1]) or burst
local ts     = tonumber(b[2]) or now

tokens = math.min(burst, tokens + (now - ts) * rate)
local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end
redis.call('HSET', key, 'tokens', tokens, 'ts', now)   -- HMSET is deprecated since Redis 4.0
redis.call('EXPIRE', key, math.ceil(burst / rate) + 60)
return {allowed, tostring(tokens)}
"""

class TokenBucket:
    def __init__(self, r: redis.Redis):
        self._script = r.register_script(LUA)

    async def allow(self, tenant: str, cost: int, rate: float, burst: int) -> bool:
        ok, _ = await self._script(keys=[f"rl:{tenant}"],
                                   args=[rate, burst, time.time(), cost])
        return bool(ok)
```
Charge `cost` in **estimated tokens** (`estimated_prompt_tokens + max_tokens`, e.g. counted with `tiktoken`), not requests — a 30-token question and a 30k-token document analysis are not the same load. Return `429` with `Retry-After` and a clear body. Emit a metric per tenant so you can see who's being throttled before they raise a ticket.

---

## 8. Caching, Multi-Tenancy & Graceful Degradation

### Q40. Design a cache for LLM responses. Exact vs semantic.
`[HARD]`

**Answer:** Two tiers.

**Tier 1 — exact cache.** Key = SHA-256 of `(normalized_prompt, model, temperature, top_p, tool_schema_version, retrieved_doc_ids, tenant)`. Cheap, safe, ~5–15% hit rate on real traffic. Only cache when `temperature == 0` (deterministic intent); caching a creative-mode response is wrong.

**Tier 2 — semantic cache.** Embed the query, ANN-search a cache index, and if `cosine ≥ threshold` (start at **0.95**, tune on your data; below ~0.90 you *will* serve wrong answers) return the stored response.

**Code:**
```python
import hashlib, json
import numpy as np

def exact_key(prompt: str, model: str, ctx_ids: list[str], tenant: str) -> str:
    payload = json.dumps(
        {"p": " ".join(prompt.split()).lower(), "m": model,
         "c": sorted(ctx_ids), "t": tenant},
        sort_keys=True,
    )
    return "llm:" + hashlib.sha256(payload.encode()).hexdigest()

class SemanticCache:
    """Redis-backed; in prod use a real vector index (Redis Search / pgvector)."""
    def __init__(self, embed, store, threshold: float = 0.95, ttl: int = 3600):
        self.embed, self.store, self.threshold, self.ttl = embed, store, threshold, ttl

    async def get(self, query: str, tenant: str) -> str | None:
        v = np.asarray(await self.embed(query), dtype=np.float32)
        v /= np.linalg.norm(v)
        hit = await self.store.top1(tenant=tenant, vector=v)      # ANN, tenant-filtered
        if hit and float(hit.score) >= self.threshold:
            return hit.answer
        return None

    async def put(self, query: str, answer: str, tenant: str) -> None:
        v = np.asarray(await self.embed(query), dtype=np.float32)
        v /= np.linalg.norm(v)
        await self.store.upsert(tenant=tenant, vector=v, answer=answer, ttl=self.ttl)
```

**Correctness rules you must state:**
- **Namespace by tenant/user** — a shared cache is a cross-tenant data leak waiting to happen.
- **Never cache personalized or permission-scoped answers** across users; include the ACL/group set in the key if you do.
- **Invalidate on corpus change** — include a corpus/index version in the key, bump it on re-index. Otherwise you serve last month's policy forever.
- **TTL everything** (1–24 h typical) — LLM answers go stale.
- Track `cache_hit_rate`, and **sample cache hits into your eval set** so a bad cached answer doesn't live for a month.
- Don't semantic-cache negations: "Can I cancel?" vs "Can I *not* cancel?" embed at ~0.93 similarity and mean opposite things. This is exactly why the threshold is high.

---

### Q41. What does graceful degradation look like for a RAG chatbot?
`[MEDIUM]`

**Answer:** A documented ladder, each rung cheaper/safer than the last, with a metric per rung.

| Failure | Degradation |
|---|---|
| Primary region 429/5xx | Failover to secondary-region deployment |
| Both regions degraded | Downgrade to smaller/faster model, note it in the response metadata |
| LLM entirely unavailable | Return **retrieval-only**: top-3 passages with citations and "AI summary unavailable" |
| Vector DB down | Fall back to BM25/keyword search, or a cached FAQ index |
| Reranker times out | Skip it, use raw vector order (quality dips, service lives) |
| Over tenant budget | 429 with `Retry-After` + upgrade CTA, never a 500 |
| Total outage | Static help-centre links + a "create a ticket" path |

**Principle:** never return a blank screen or a stack trace. Every degradation is **explicit in the response payload** (`"degraded": true, "reason": "llm_unavailable"`) so the UI can label it and your dashboards can count it. Also: **feature-flag** each rung so you can force degradation during an incident without a deploy.

---

### Q42. How do you stop a runaway agent from bankrupting you?
`[MEDIUM]`

**Answer:** Hard limits at four levels, enforced in code, not in the prompt:

1. **Per-run**: max iterations (e.g. 12), max wall-clock (e.g. 120 s), max total tokens (e.g. 60k), max tool calls.
2. **Per-conversation/user/day**: token and cost budget in Redis; block with a clear message when exhausted.
3. **Per-tenant/month**: budget + alert at 50/80/100%.
4. **Platform**: Azure Cost Management budget alerts + an anomaly alert on the token metric (catches what your code missed).

Plus **loop detection**: hash `(tool_name, args)` per run — if the same call repeats 3 times, break and return what you have. And **cancel on client disconnect** so an abandoned browser tab doesn't keep an agent running.

```python
import time
from dataclasses import dataclass, field

class BudgetExceeded(RuntimeError):
    """Raised by the agent loop; caught at the API boundary -> 429/partial answer."""

@dataclass
class RunBudget:
    max_steps: int = 12
    max_tokens: int = 60_000
    deadline_s: float = 120.0
    steps: int = 0
    tokens: int = 0
    started: float = field(default_factory=time.monotonic)

    def check(self) -> None:
        if self.steps >= self.max_steps:
            raise BudgetExceeded("max_steps")
        if self.tokens >= self.max_tokens:
            raise BudgetExceeded("max_tokens")
        if time.monotonic() - self.started > self.deadline_s:
            raise BudgetExceeded("deadline")
```

---

### Q43. Blue-green vs canary for a model or prompt change.
`[HARD]`

**Answer:** Different tools for different risks, and for LLM changes **canary is almost always right**.

| | Blue-green | Canary |
|---|---|---|
| Mechanism | Two full environments, flip 100% of traffic | Shift 1% → 5% → 25% → 100% gradually |
| Rollback | Instant (flip back) | Fast (dial to 0%) |
| Cost | 2× infra during cutover | Marginal |
| Detects | Hard failures | **Quality regressions**, which is what LLM changes cause |
| Best for | Infra/schema changes | **Prompt/model/retrieval changes** |

Why canary for GenAI: a new model version rarely *fails* — it silently gets worse in one segment (longer answers, different tone, dropped citations, more refusals). You need statistically meaningful traffic and **quality** metrics (thumbs-down rate, citation rate, refusal rate, groundedness score, escalation-to-human rate, p95 latency, cost/query), not just error rate. Bake a wait period into each step — an hour of 5% traffic to accumulate signal.

**Also mention shadow testing (the safest first step):** send a copy of real production traffic to the candidate model, **don't** return its output, and score both offline. Zero user risk, real distribution. Do this before canary for a model-version bump. Watch out: shadowing doubles token cost, so sample (5–10%) and strip PII if the shadow target is a different provider.

**And feature flags:** `model_version` as a flag with percentage rollout keyed on a stable hash of `user_id` (so a user doesn't flip between models mid-conversation — that's a jarring UX and it poisons your A/B stats).

**Rollback plan must include:** the prompt is versioned in git with the code, the model version is pinned config, the eval scores for the previous version are stored, and the flag flip takes <60 s with no deploy.

---

## 9. CI/CD & Release Strategy

### Q44. Write the GitHub Actions pipeline for this Python AI service.
`[MEDIUM]`

**Answer:** Lint → type → test → **eval** → build → scan → push (OIDC, no secrets) → deploy → smoke.

**Code (`.github/workflows/deploy.yml`):**
```yaml
name: build-and-deploy
on:
  push: { branches: [main] }
  pull_request:

permissions:
  contents: read
  id-token: write          # required for Azure OIDC federated login
  packages: write

env:
  IMAGE: myacr.azurecr.io/rag-api

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy app
      - run: uv run pytest -q --cov=app --cov-fail-under=80
      - name: Secret scan
        uses: gitleaks/gitleaks-action@v2
      - name: Dependency audit
        run: uv run pip-audit || true      # gate on it once the backlog is clean

  eval:
    needs: quality
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - name: Golden-set eval (gates the merge)
        env:
          AZURE_OPENAI_ENDPOINT: ${{ vars.AOAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY:  ${{ secrets.AOAI_KEY_EVAL }}
        run: uv run python -m evals.run --dataset evals/golden.jsonl --min-score 0.82

  build:
    needs: quality
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - run: az acr login --name myacr
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ env.IMAGE }}:${{ github.sha }},${{ env.IMAGE }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
      - name: Scan image
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: ${{ env.IMAGE }}:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: '1'
          ignore-unfixed: true

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production        # protection rules -> manual approval
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - uses: azure/setup-kubectl@v4
      - run: az aks get-credentials -g rg-ai -n aks-prod
      - run: |
          kubectl set image deployment/rag-api api=${{ env.IMAGE }}:${{ github.sha }}
          kubectl rollout status deployment/rag-api --timeout=300s
      - name: Smoke test
        run: curl -fsS https://api.example.com/readyz
```

**Points to make:** OIDC federated credentials (`id-token: write` + `azure/login@v2`) mean **no long-lived Azure secret in GitHub**; the image is tagged with the commit SHA (immutable, traceable, rollback = `kubectl rollout undo` or re-set the old SHA); the **eval job gates the PR** — that's the LLM-specific part interviewers want to hear; `environment: production` gives you approvals + audit.

---

### Q45. Infrastructure as Code — what would you use on Azure?
`[EASY]`

**Answer:** **Terraform** if the org is multi-cloud or already invested (huge provider ecosystem, mature state/plan workflow); **Bicep** if it's Azure-only (native ARM, no state file to manage, first-day support for new Azure resources, `what-if` preview). Both fine — the answer is "declaratively, in git, reviewed, applied by CI, never by hand in the portal."

What you'd codify: resource group, Azure OpenAI resource **and its model deployments** (with pinned versions and TPM capacity), AI Search, Key Vault + access policies/RBAC, ACR, AKS/Container Apps, VNet + subnets + private endpoints + private DNS zones, Log Analytics + App Insights, managed identities + role assignments, budgets and alert rules.

**The point to make:** "Model deployment name, model version and TPM capacity are infrastructure, not app config. Putting them in Terraform means a model upgrade is a reviewed PR with a diff, not someone clicking in the portal at 11pm."

---

### Q46. How do you version prompts and models?
`[MEDIUM]`

**Answer:** Treat prompts as **code + data**: they live in git, are immutable once released, and are referenced by ID from the running app.

- **Storage:** `prompts/answer_v3.jinja2` in the repo, loaded at startup. Semantic version in the filename or front-matter. A DB-backed prompt registry (or Langfuse/LangSmith prompt management) is fine *if* changes still go through review and can be rolled back — the risk of an editable-in-prod prompt is that nobody can explain last Tuesday's regression.
- **Every request logs:** `prompt_id`, `prompt_version` (hash of the template), `model`, `model_version`, `deployment`, `retriever_version`, `index_version`, `temperature`, and the app `git_sha`. Without this you cannot correlate a quality drop with a change — this is the single most valuable LLMOps habit.
- **Release gate:** every prompt change runs the golden eval set in CI (Q44) and must not regress beyond a threshold.
- **Rollout:** feature flag with a percentage + stable user hash; canary; instant flag rollback.
- **Config, not code, for model choice:** `MODEL_DEPLOYMENT=chat-prod-v2` so rollback is a config change.

**Say this:** "We had a regression where answers stopped citing sources. Because every trace carried `prompt_version` and `git_sha` we bisected it to a prompt edit in 15 minutes and rolled back with a flag flip, no deploy."

---

### Q47. What's in the deployment runbook for a model-version upgrade?
`[MEDIUM]`

**Answer:** Concrete sequence:

1. **Read the model card / changelog** for behaviour and API deltas (params removed, tokenizer change, tool-calling format change).
2. **New deployment** `chat-prod-v2` in the same resource (via IaC), pinned to the new version, with its own TPM allocation.
3. **Offline eval**: run the golden set (≥200 items) against both. Compare accuracy/groundedness/citation rate/refusal rate/latency/cost. Record the table.
4. **Shadow** 5–10% of production traffic for 24–48 h; score offline; diff distributions, not just averages (regressions hide in one segment).
5. **Canary** 1% → 5% → 25% → 100% with a bake time and explicit rollback criteria (e.g. thumbs-down rate up >2pp, p95 latency up >30%, citation rate down >5pp).
6. **Monitor** cost/query — new models change token efficiency in both directions.
7. **Rollback** = flag to 0%; keep the old deployment alive for at least 2 weeks.
8. **Decommission** old deployment; update IaC; note the retirement date of the new version in the calendar.

---

## 10. LLMOps & Observability

### Q48. What do you log for every LLM call, and what must you never log?
`[MEDIUM]`

**Answer:**

**Always log (structured JSON, one event per call):** `request_id`, `trace_id`, `conversation_id`, `tenant_id`, `user_id` (pseudonymous), `route/feature`, `model`, `deployment`, `model_version`, `prompt_id` + `prompt_version`, `git_sha`, `temperature`, `prompt_tokens`, `completion_tokens`, `cached_tokens`, `computed_cost_usd`, `latency_ms`, `time_to_first_token_ms`, `finish_reason`, `retry_count`, `http_status`, `cache_hit`, retrieval metadata (`doc_ids`, `scores`, `top_k`, `index_version`), tool calls (`name`, arg **schema**, duration, success), and the user feedback signal when it arrives.

**Never log:** API keys/tokens, raw PII (names, emails, phone, account numbers, health data), full document contents from a regulated corpus, and — in high-compliance environments — the raw prompt/completion at all.

**Prompt/completion text policy:** default to **redact-then-sample**. Redact with a PII detector (Azure AI Language PII detection, Presidio) before it leaves the process, sample 1–5% for debugging, short retention (7–30 days), separate access-controlled sink, and honour deletion requests (GDPR/DPDP) — which means logs must be **keyed by user** so you can actually delete them.

**Code (redaction at the logging boundary):**
```python
import re

PATTERNS = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "PHONE_IN": re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b"),
    "PAN":   re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),          # India PAN
    "AADHAAR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "CARD":  re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}

def redact(text: str) -> str:
    for label, rx in PATTERNS.items():
        text = rx.sub(f"[{label}]", text)
    return text
```
Say out loud: "Regex is the cheap first pass; for anything regulated I'd use a proper NER-based detector (Azure AI Language / Presidio) because names and addresses don't match regex."

---

### Q49. How do you trace an agent run end to end?
`[MEDIUM]`

**Answer:** **OpenTelemetry** with the **GenAI semantic conventions** (still marked experimental — say so, it shows you read the spec) so traces are vendor-portable, exported to whatever backend the org has: Azure **Application Insights**, Langfuse, LangSmith, Grafana Tempo, Datadog.

Span shape for one agent run:
```
POST /chat                       (root, HTTP span)
├─ retrieve.embed                gen_ai.operation.name=embeddings
├─ retrieve.vector_search        db.system=azure.search, top_k=20
├─ rerank                        model=cross-encoder, k=20->5
├─ chat plan                     gen_ai.operation.name=chat, tokens in/out
├─ tool.get_order_status         args-schema, duration, ok/err
├─ chat synthesize               tokens in/out, finish_reason
└─ guardrail.output_check
```

Attributes to set (GenAI conventions): `gen_ai.system` (`az.ai.openai`), `gen_ai.operation.name` (`chat`/`embeddings`), `gen_ai.request.model`, `gen_ai.request.temperature`, `gen_ai.request.max_tokens`, `gen_ai.response.model`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`.

```python
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

async def call_llm(messages, deployment):
    with tracer.start_as_current_span("chat") as span:
        span.set_attribute("gen_ai.system", "az.ai.openai")
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", deployment)
        r = await aclient.chat.completions.create(model=deployment, messages=messages)
        span.set_attribute("gen_ai.usage.input_tokens", r.usage.prompt_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", r.usage.completion_tokens)
        span.set_attribute("gen_ai.response.finish_reasons",
                           [c.finish_reason or "" for c in r.choices])   # OTel rejects None in a sequence
        return r
```
Correlate everything with a single `trace_id` propagated from the ingress through the queue (put the traceparent in the message headers — this is where most teams lose the trace).

**Dashboards to name:** p50/p95 latency + TTFT, tokens/min and cost/day by feature and tenant, 429 rate by deployment, cache hit rate, retrieval recall proxy (% answers with ≥1 citation), thumbs-down rate, guardrail-block rate, tool error rate, agent steps per run distribution.

---

### Q50. How do you evaluate quality continuously, and detect drift?
`[HARD]`

**Answer:** Three loops running at different cadences.

**1. Offline / CI (per PR).** A **golden set** of 150–300 real questions with reference answers and expected source docs. Metrics: retrieval **recall@k** and **MRR**; generation **groundedness/faithfulness**, **answer relevance**, **context precision** (RAGAS-style, LLM-as-judge); plus deterministic checks (JSON schema valid, citation present, refuses when it should). Gate the merge on a threshold. Keep temperature 0 and pin the judge model — otherwise your gate is noisy.

**2. Online (continuous).** Proxy metrics on live traffic since you have no ground truth: thumbs up/down rate, copy/regenerate clicks, conversation length, escalation-to-human rate, refusal rate, empty-retrieval rate, citation rate, p95 latency, cost/query. Sample 1–2% of traffic through an LLM-judge for groundedness.

**3. Drift detection (weekly).** Three distinct drifts, name them:
- **Input drift** — user questions shift (new product launch). Detect by clustering query embeddings and watching cluster mass over time; a spike in low-max-similarity queries means "questions our corpus doesn't cover."
- **Corpus drift** — documents changed; stale chunks. Detect via index freshness + a canary set of questions whose answers you know changed.
- **Model drift** — the provider updated the model behind an auto-updating deployment. **Prevent it** by pinning versions; detect it by running the golden set nightly and alerting on a score delta.

**Say a number:** "Nightly golden-set run, alert if faithfulness drops more than 3 points or recall@5 drops more than 5 points week over week."

---

### Q51. Runbook: "the LLM is returning garbage in production." Walk me through it.
`[HARD]`

**Answer:** Triage in this order — cheapest and most likely first. Never start by blaming the model.

1. **Scope it (2 min).** All users or one tenant? All routes or one? Started when? Correlate with the deploy timeline — 80% of incidents are "something changed."
2. **Check what changed** using logged versions (Q46): `git_sha`, `prompt_version`, `model_version`, `index_version`, feature flags, config. Roll back the most recent one first; investigate after.
3. **Is it retrieval or generation?** Pull a failing trace. Look at retrieved chunks. If the right document isn't in the context, it's a **retrieval** bug (bad index, missing filter, wrong embedding model after a re-index, ACL over-filtering, empty results silently proceeding). If the right document *is* there and the answer ignores it, it's **generation** (prompt regression, model change, context truncation dropping the relevant chunk, lost-in-the-middle ordering).
4. **Check the boring infra causes:** `finish_reason == "length"` (truncation — `max_tokens` too small), `finish_reason == "content_filter"`, a silently failing tool returning an error string that the model then narrates, a truncated/failed JSON parse falling back to a default, an expired index alias.
5. **Check the provider:** Azure status page, your 429/5xx rate, latency spike, an auto-updated model version.
6. **Mitigate before you fix:** roll back the flag/prompt/deploy, or force a degradation rung (Q41), or route to the secondary region/model.
7. **Verify** with the golden set against production config.
8. **Post-incident:** add the failing questions to the golden set permanently — that's the regression test. Add a monitor for the signal you wished you'd had.

**Killer line:** "The reason we could do steps 2 and 3 in minutes is that every response carries a `trace_id` the user can quote, and every trace stores the retrieved chunk IDs and all component versions. Observability is what makes an LLM system debuggable at all — you can't step through a model."

---

## 11. Security, OWASP LLM Top 10 & Compliance

### Q52. List the OWASP Top 10 for LLM Applications with one mitigation each.
`[HARD]`

**Answer:** (2025 list.) Know all ten by name — this is the single most quotable security artefact in GenAI interviews.

| # | Risk | One-line mitigation |
|---|---|---|
| **LLM01** | **Prompt Injection** (direct & indirect via retrieved content) | Treat all retrieved/user text as untrusted data, delimit + label it, keep instructions in the system role, never let model output trigger privileged actions without policy checks; use Prompt Shields/injection classifiers |
| **LLM02** | **Sensitive Information Disclosure** | PII detection + redaction on input and output, per-user ACL filters at retrieval time, no secrets in prompts, scrub logs |
| **LLM03** | **Supply Chain** | Pin + hash-lock dependencies and models, scan images (Trivy), verify model/dataset provenance, private registries, SBOM |
| **LLM04** | **Data and Model Poisoning** | Validate and source-control the ingestion corpus, restrict who can write to the vector index, checksum documents, review fine-tune data |
| **LLM05** | **Improper Output Handling** | Never `eval()`/exec model output; parameterized SQL only; HTML-escape before render; validate against a Pydantic schema; sandbox any code execution |
| **LLM06** | **Excessive Agency** | Least-privilege tools, read-only by default, allow-list of actions, human approval for irreversible/high-value operations, per-run budgets |
| **LLM07** | **System Prompt Leakage** | Assume the system prompt is public — put no secrets, keys, or authorization logic in it; enforce authorization in code |
| **LLM08** | **Vector and Embedding Weaknesses** | Tenant-scoped indexes + mandatory metadata filters, sanitize documents before embedding, access-control the vector store, watch for embedding-inversion exposure |
| **LLM09** | **Misinformation / overreliance** | Ground with RAG + require citations, groundedness scoring, refuse when retrieval is empty, UI disclaimers, human review for high-stakes output |
| **LLM10** | **Unbounded Consumption** (DoS / wallet drain) | Per-user + per-tenant rate and token limits, max input length, max steps/iterations, timeouts, cost alerts, circuit breakers |

---

### Q53. Concretely, how do you secure a RAG service handling confidential documents?
`[HARD]`

**Answer:** Defense in depth, layer by layer, and each layer has a named control.

**Identity & access**
- Entra ID / OIDC on the API; validate JWT signature, audience, issuer, expiry — every request.
- **Enforce document ACLs at query time**: resolve the caller's group memberships from their token, push them into the vector-store filter. Never post-filter, never prompt-filter.
- Managed identity for all Azure-to-Azure calls; least-privilege RBAC (`Cognitive Services OpenAI User`, not Contributor).

**Data**
- Classify the corpus (public / internal / confidential / restricted). Restricted content may need a separate index, separate resource, and CMK.
- Encryption in transit (TLS 1.2+) and at rest (default MMK; CMK if contractually required).
- **Data minimisation** — don't embed fields you'll never retrieve on; strip PII from chunks where possible.
- Zero-retention configuration on Azure OpenAI for regulated data (Q12).

**Network**
- Private endpoints for OpenAI/Search/KeyVault/Storage; `publicNetworkAccess: Disabled`; egress via firewall with FQDN rules; WAF in front of the ingress.

**Application**
- Input validation and max prompt length; output schema validation; injection heuristics on retrieved chunks; content filter enabled.
- Tool allow-list; no shell/SQL/HTTP-to-arbitrary-URL tools; sandbox code execution (gVisor/Firecracker/no-network container).
- Per-tenant rate + token limits.

**Audit & governance**
- Immutable audit log: who asked what, which documents were retrieved, what was returned, which model. Retain per policy.
- Diagnostic settings on the Azure OpenAI resource → Log Analytics; Defender for Cloud; Azure Policy to block non-compliant resources.
- Documented DPIA / model card / responsible-AI review for the use case.

---

### Q54. GDPR and India's DPDP Act — what actually changes in your design?
`[MEDIUM]`

**Answer:** Five concrete engineering consequences (don't recite law — name the design changes):

1. **Lawful basis + purpose limitation** → you must be able to say why each field is processed. Practically: a data inventory, and no "log everything just in case."
2. **Data residency** → pick a **regional** (not Global Standard) Azure OpenAI deployment in the required geography; keep the vector store and logs in-region too. India's DPDP Act permits transfers except to government-restricted countries, but sectoral rules (RBI for financial data) are stricter — so for BFSI clients in Chennai, assume "keep it in India."
3. **Right to erasure / correction** → you must be able to delete a user's data *everywhere*: primary DB, vector index (delete by `user_id` metadata filter), cache, logs, traces, and any eval dataset that captured it. Design keys for deletability on day one; retrofitting this is brutal. Note that you cannot un-train a fine-tuned model — so **don't fine-tune on personal data**; use RAG, where deletion is a row delete.
4. **Consent + notice (DPDP)** → clear notice that AI is processing the input, consent records, and a **Consent Manager** integration where applicable. Children's data has extra restrictions.
5. **Breach notification + accountability** → DPDP requires notifying the Data Protection Board and affected users; GDPR is 72 hours to the supervisory authority. So: incident runbook, audit logs, and a **Significant Data Fiduciary** posture (DPO, DPIA, audits) if you're at scale.

Add: **automated decision-making** — if the LLM's output materially affects someone (credit, hiring, claims), keep a human in the loop and log the rationale. And the **DPDP Rules** were notified with phased timelines, so confirm current obligations with the client's legal team rather than asserting dates.

---

### Q55. What is your model/data governance story?
`[MEDIUM]`

**Answer:** Four artefacts and one process.

- **Model registry / inventory** — every model in use: provider, version, deployment, owner, use case, data classification it may touch, approved regions, retirement date.
- **Model card per use case** — intended use, known limitations, eval results, safety testing (red-team results), fallback behaviour, human-oversight requirement.
- **Data lineage** — for each index: source system, ingestion job, classification, refresh cadence, ACL model, retention. Azure **Purview** if the org has it.
- **Prompt registry** — versioned, reviewed, linked to eval results (Q46).
- **Process:** a lightweight AI review board sign-off before a new use case goes live (risk tier → required controls), plus periodic re-evaluation. For EU exposure, map the use case to **EU AI Act** risk tiers — high-risk uses (employment, credit, essential services) carry documentation, logging and human-oversight obligations.

---

## 12. Production Readiness Checklist

Print this. If an interviewer asks "is your service production-ready?", walk the list.

**Reliability**
- [ ] Timeouts on every external call; total budget < gateway timeout
- [ ] Retry with `Retry-After` + jitter, on 429/5xx only, retries not double-stacked with the SDK
- [ ] Circuit breaker + multi-region/multi-model fallback
- [ ] Graceful degradation ladder defined and feature-flagged
- [ ] Bulkhead/semaphore capping in-flight LLM calls
- [ ] Long jobs on a queue with idempotency keys and DLQ
- [ ] Graceful shutdown: preStop, graceful-timeout, terminationGracePeriod sized for the longest request
- [ ] Load tested; knee-point concurrency known and documented

**Scalability**
- [ ] Stateless pods; all state in Redis/DB/blob
- [ ] HPA/KEDA on concurrency or queue depth, **not** CPU
- [ ] Upstream TPM/RPM quota known; admission control so scaling out doesn't just create 429s
- [ ] Exact + semantic cache with tenant namespacing and corpus-version invalidation
- [ ] Per-tenant rate & token limits

**Security**
- [ ] Managed identity / no API keys in code or image; Key Vault for the rest
- [ ] Private endpoints, `publicNetworkAccess: Disabled`, controlled egress
- [ ] Non-root container, read-only rootfs, dropped capabilities, image scanned in CI
- [ ] Per-user ACL filters enforced at retrieval, in code
- [ ] Content filter on + custom guardrails (injection, PII, topic, grounding)
- [ ] Tool allow-list; irreversible actions require human approval
- [ ] OWASP LLM Top 10 reviewed and mapped to controls

**Observability**
- [ ] Structured logs with `trace_id`, tokens, cost, all component versions
- [ ] OTel traces spanning retrieval → LLM → tools, propagated through the queue
- [ ] Dashboards: latency/TTFT, tokens & cost by tenant & feature, 429s, cache hit rate, guardrail blocks, thumbs-down
- [ ] Alerts: error rate, p95 latency, 429 rate, cost anomaly, quality-score drop
- [ ] PII redaction before logs leave the process; retention policy set

**Quality / LLMOps**
- [ ] Golden eval set ≥150 items, gated in CI
- [ ] Nightly eval run with drift alerting
- [ ] Prompts + model versions pinned in git/config, never editable in prod without review
- [ ] Shadow → canary → 100% rollout with defined rollback criteria
- [ ] User feedback captured and fed back into the eval set

**Operations**
- [ ] IaC for everything, including model deployments and TPM
- [ ] Blue/green or canary deploy, rollback tested (not just documented)
- [ ] Runbooks: garbage output, provider outage, cost spike, quota exhaustion
- [ ] Cost budget + alerts at 50/80/100%
- [ ] On-call owner, SLO defined (e.g. 99.5% availability, p95 < 6 s), error budget

---

## 13. Red Flags / Do NOT say

- ❌ "I use `openai.ChatCompletion.create()`" — removed in openai 1.x. Instant credibility loss.
- ❌ "In Azure you pass `model='gpt-4o'`" — you pass the **deployment name**.
- ❌ "We store the API key in the Docker image / in `.env` committed to git."
- ❌ "We autoscale on CPU." — for an I/O-bound LLM service this is the classic wrong answer.
- ❌ "We just retry on 429 in a loop." — no `Retry-After`, no jitter, no cap = retry storm.
- ❌ "Azure OpenAI trains on our data." — it does not. Getting this backwards in a client-facing role is bad.
- ❌ "We put the tenant restriction in the system prompt." — that's not isolation, that's a hope.
- ❌ "We don't need our own guardrails, Azure filters content." — different threat models.
- ❌ "We tested it manually, it looked good." — for a 6-year engineer, no eval set is a red flag.
- ❌ Naming a tool you've never run. If they ask a follow-up you can't answer, the whole answer collapses. Say "I've read about X, I've shipped Y."
- ❌ Overclaiming multi-cloud. Say "deepest on Azure, working knowledge of Bedrock/Vertex."
- ⚠️ Hedge honestly on fast-moving specifics: "PTU minimums and exact model availability change per region — I'd check the capacity calculator in the portal before committing to a number."

---

## Rapid-Fire (last 10 min before you walk in)

1. **What goes in `model=` on Azure?** → The **deployment name**, not `gpt-4o`.
2. **Client + endpoint?** → `AzureOpenAI`/`AsyncAzureOpenAI` (openai ≥1.x), `https://<res>.openai.azure.com/openai/deployments/{d}/chat/completions?api-version=...`
3. **Entra auth in one line?** → `get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")` passed as `azure_ad_token_provider=`; RBAC role `Cognitive Services OpenAI User`.
4. **Quota unit?** → TPM; RPM derived at roughly **6 RPM per 1,000 TPM**; limiter uses ~1s/10s windows, so bursts 429 first.
5. **429 header?** → `Retry-After` (s) / `retry-after-ms`. Honour it, then jittered backoff, cap attempts.
6. **Default SDK retries?** → `max_retries=2` (= 3 HTTP calls). Set 0 if you wrap it yourself, or 5 outer attempts becomes 15 real calls.
7. **PTU vs PAYG?** → Reserved capacity + predictable latency + hourly/reserved pricing vs per-token shared best-effort; hybrid = PTU baseline + PAYG spillover. Batch API ≈50% cheaper, off interactive quota.
8. **Content filter?** → hate/sexual/violence/self-harm × safe-low-medium-high, blocks medium+. Prompt blocked = **400 `content_filter`**; completion blocked = **200 with `finish_reason="content_filter"`**.
9. **Private networking?** → Private Endpoint + `privatelink.openai.azure.com` DNS zone + `publicNetworkAccess: Disabled`.
10. **Secrets?** → Managed identity first; Key Vault + CSI driver for the rest. Never in the image or git.
11. **Streaming broken behind nginx?** → `proxy_buffering off;` + `X-Accel-Buffering: no` response header.
12. **Async worker count for an LLM API?** → ≈ cores (1–4); concurrency comes from the event loop, scale out with pods. `(2 × cores) + 1` is **WSGI/sync only**.
13. **Worst async bug?** → A blocking call inside `async def` freezes the entire event loop for every concurrent request.
14. **HPA metric?** → In-flight requests or queue depth via KEDA. **Not CPU** — LLM pods idle at ~3% CPU while saturated.
15. **Liveness probe rule?** → Never call an external dependency in it, or a provider outage CrashLoops every pod. Slow warmup → `startupProbe`.
16. **4-minute agent run?** → `202` + job ID + queue + worker + poll/SSE. Never a synchronous HTTP request.
17. **Timeouts that bite?** → AWS API Gateway REST 29 s, ALB idle 60 s, Cloud Run 5 min default / 60 min max, Lambda 15 min exec, Azure Functions Consumption 10 min max.
18. **Where does agent state live?** → Redis/Postgres/blob — never in-process. LangGraph checkpointer for resumability.
19. **Semantic cache threshold?** → Start at cosine **0.95**; namespace by tenant; include corpus/index version in the key; TTL everything.
20. **Canary vs blue-green for a prompt/model change?** → Canary — LLM regressions are quality regressions and need traffic to detect. Shadow traffic first: score offline, don't return the output.
21. **What must every LLM log carry?** → `trace_id`, tokens in/out, cost, `model_version`, `prompt_version`, `git_sha`, `finish_reason`. OTel: `gen_ai.system`, `gen_ai.operation.name`, `gen_ai.usage.input_tokens/output_tokens`.
22. **OWASP LLM01 / LLM05 / LLM06 / LLM10?** → Prompt Injection; Improper Output Handling; Excessive Agency; Unbounded Consumption.
23. **Biggest cost lever?** → Model routing (small model for the easy 80%), then caching, then cutting top-k, then realistic `max_tokens`.
24. **LLM-specific CI gate + secretless deploy?** → Golden-set eval with a minimum score on every PR; OIDC federated credentials + `azure/login@v2` with `permissions: id-token: write`.
25. **Fine-tune on personal data?** → No — you can't delete it later. Use RAG, where erasure is a row delete. (Bedrock breadth: unified API is `bedrock-runtime.converse`/`converse_stream`.)

---

*Section 10 of the Virtusa L1 prep set. Pair with [03 — API frameworks](03-api-frameworks-fastapi-flask-django.md) for the FastAPI internals and [11 — System Design](11-system-design-genai.md) for the end-to-end architectures.*
