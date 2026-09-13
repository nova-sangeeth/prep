# Rapid-Fire Cheatsheet — read this last

> EY GDS — **DE-Cloud Integration Platform Engineer** (Digital Engineering, Financial Services) — prep pack file 11

**What this file buys you in the interview:** the final 60 minutes before you dial in. Everything else in the pack teaches; this file only *reloads*. It is one-liners, decision tables and verified numbers — no teaching, no prose. If you read one file on the morning of, read §1 (the EY-logged verbatim set — these questions were literally asked at EY), §2 (10-minute final scan) and §14 (the 270-item rapid fire).

> **Honesty rule — read this before anything else.** Everywhere this file says *"I do X"* or *"we set Y"*, that is **design intent, not a delivery credential.** Say it in the conditional — *"the way I'd set that up is…"*, *"the pattern I'd reach for is…"* — unless you have actually shipped it. You have **not** worked in a bank and have **not** run a platform team; claiming either is the one mistake this pack cannot recover from, because the follow-up question ("which bank? what was the volume?") arrives within ten seconds. What you *have* shipped — production LLM systems calling enterprise APIs under rate limits, with retries, idempotency and observability — is real, transferable and enough. Lead with it, and let the FS vocabulary in §10 show you can hold the conversation, not that you have lived it.

**The one-sentence frame for the whole interview:** *"I build the paved road — reusable pipeline templates, golden Helm charts, shared APIM policy fragments, versioned Terraform modules — so that twenty integration teams ship the same way, with the same guardrails, and the platform team is not a ticket queue."* That is the difference between a Platform Engineer and an API developer, and this JD says **Platform Engineer**.

**JD re-weighting you must internalise:** CI/CD occupies **3 of 9** responsibilities (pipelines + security scanning + IaC). GitOps (ArgoCD/Flux) and Kubernetes/Helm moved from *good-to-have* into the **explicit responsibility list**. Financial Services is the industry context — compliance, auditability, data residency, ISO 20022/SWIFT. Do not lead with APIM policy trivia; lead with the paved road.

## Table of Contents

| § | Section | Size |
|---|---------|------|
| 1 | [The EY-Logged Verbatim Set](#1-the-ey-logged-verbatim-set) | 12 Q, full format |
| 2 | [10-Minute Final Scan](#2-10-minute-final-scan) | 25 items |
| 3 | [Comparison Tables](#3-comparison-tables) | 22 tables |
| 4 | [Numbers to Memorize](#4-numbers-to-memorize-verified) | verified only |
| 5 | [Azure → AWS → GCP Mapping](#5-azure--aws--gcp-mapping) | 1 table |
| 6 | [HTTP Status Decision Table](#6-http-status-decision-table) | 1 table |
| 7 | [Name That Pattern](#7-name-that-pattern) | 26 rows |
| 8 | [Command Crib](#8-command-crib) | 30+ commands |
| 9 | [Acronym Decoder](#9-acronym-decoder-95) | 95 |
| 10 | [Financial Services One-Liners](#10-financial-services-one-liners) | 22 |
| 11 | [Interviewer Traps](#11-interviewer-traps) | 15 |
| 12 | [30-Second Whiteboard Versions](#12-30-second-whiteboard-versions) | 3 |
| 13 | [Verbal Etiquette & Recovery](#13-verbal-etiquette--recovery) | rules |
| 14 | [Rapid Fire — 270 One-Liners](#14-rapid-fire--270-one-liners) | 270 |

**Sibling files:** [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md) · [API Design](01-api-design-rest-soap-graphql-openapi.md) · [Azure Integration Services](02-azure-integration-services.md) · [Messaging & Event Streaming](03-messaging-and-event-streaming.md) · [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md) · [CI/CD & IaC](05-cicd-iac-and-gitops.md) · [Auth & Security](06-auth-and-security.md) · [Python for Integration](07-python-for-integration-and-coding-round.md) · [System Design](08-system-design-integration.md) · [Behavioural & HR](09-behavioral-ey-and-hr.md) · [GenAI → Integration Bridge](10-genai-to-integration-bridge.md)

---

## 1. The EY-Logged Verbatim Set

These twelve are **not hypotheticals**. Every one is attributed to a real EY interview in the sourced reports (AmbitionBox EY-tagged DevOps and GDS Senior Consultant entries). Answer each in the first two sentences, then stop and let them pull.

---

### Q1. "How do you check resources using Terraform?"
`[EY-LOGGED]` `[DEVOPS ROUND]` `[NEAR-CERTAIN]`

**Answer:** Three different questions hide in that one. To see what Terraform *thinks* it manages I use `terraform state list` and `terraform state show`. To see what it *would* change I use `terraform plan`, and to detect out-of-band drift specifically I use `terraform plan -refresh-only`. To assert ongoing invariants I use `check` blocks and `precondition`/`postcondition`, which fail the plan instead of failing in production.

```bash
terraform state list                                   # every address in state
terraform state show azurerm_servicebus_queue.orders   # full attributes of one resource
terraform plan -out=tfplan -var-file=env/prod.tfvars   # desired vs actual
terraform show -json tfplan | jq -r '.resource_changes[] | "\(.change.actions|join(","))\t\(.address)"'
terraform plan -refresh-only                           # drift only, no config diff
terraform apply -refresh-only                          # accept the drift into state
terraform state rm azurerm_servicebus_queue.legacy     # stop managing, do not destroy
terraform import azurerm_resource_group.rg /subscriptions/<subId>/resourceGroups/rg-int-prd
```

```hcl
resource "azurerm_servicebus_queue" "orders" {
  name         = "orders"
  namespace_id = azurerm_servicebus_namespace.ns.id

  max_delivery_count                      = 10
  lock_duration                           = "PT1M"
  dead_lettering_on_message_expiration    = true
  requires_duplicate_detection            = true
  duplicate_detection_history_time_window = "PT10M"
}

# Terraform 1.5+ check block: a continuous platform guardrail, not a one-off assertion.
check "dlq_guardrail" {
  assert {
    condition     = azurerm_servicebus_queue.orders.dead_lettering_on_message_expiration
    error_message = "Golden path: every queue must dead-letter on TTL expiry."
  }
}
```

**If they push back — "how do you check drift across 40 subscriptions, not one?"** — You do not run `plan` by hand. You run a scheduled drift-detection pipeline per stack that executes `terraform plan -detailed-exitcode` and treats exit code `2` as "drift, raise a ticket"; you push the plan JSON into Log Analytics for a drift dashboard; and you close the loop by removing human write access to the portal so the only path to change is a PR. Drift detection without removing portal access is theatre.

---

### Q2. "Explain the Docker expose and publish commands."
`[EY-LOGGED]` `[DEVOPS ROUND]` `[NEAR-CERTAIN]`

**Answer:** `EXPOSE` is documentation, `--publish` is the thing that actually works. `EXPOSE 8000` in a Dockerfile writes metadata saying "this image listens on 8000" — it opens nothing, and a container with `EXPOSE` alone is unreachable from the host. `-p 8080:8000` at `docker run` creates the real host-to-container port mapping. The only functional link between them is `-P` (capital P), which publishes every `EXPOSE`d port to a random ephemeral host port.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker run -d -p 8080:8000 orders-api:1.4.2         # host 8080 -> container 8000 (explicit)
docker run -d -p 127.0.0.1:8080:8000 orders-api:1.4.2  # bind to loopback only
docker run -d -P orders-api:1.4.2                   # publish all EXPOSEd ports to random host ports
docker port <container_id>                          # what got mapped
docker inspect --format '{{json .Config.ExposedPorts}}' orders-api:1.4.2
```

**If they push back — "so is EXPOSE useless?"** — No, it is a contract. `-P` reads it, Docker Compose and orchestrators surface it, and it tells the next engineer which port to map without reading the CMD. Also the second half of that Dockerfile line matters more in interviews: `--host 0.0.0.0`. Bind to `127.0.0.1` inside a container and no port mapping on earth will reach it — that is the single most common "my container won't respond" bug, and it has nothing to do with `EXPOSE`.

---

### Q3. "How does HPA work in Kubernetes?"
`[EY-LOGGED]` `[DEVOPS ROUND]` `[NEAR-CERTAIN]`

**Answer:** The HorizontalPodAutoscaler is a control loop in kube-controller-manager that runs every **15 seconds** by default, reads the current metric for the pods behind a scale target, and computes `desiredReplicas = ceil(currentReplicas × currentMetricValue / desiredMetricValue)`. If the ratio is within a **0.1 (10%) tolerance** of 1.0 it does nothing. With multiple metrics it computes a proposal per metric and takes the **maximum**. Scale-up is immediate — no stabilization window, and it may add the greater of 4 pods or 100% of current replicas per 15 s. Scale-down waits out a **300-second stabilization window** and is capped at 100% per 15 s.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orders-api
  namespace: integration
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders-api
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  # This block restates the upstream defaults explicitly. Know which side each policy
  # belongs to - getting it backwards is the classic "memorised it wrong" tell.
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300     # default (--horizontal-pod-autoscaler-downscale-stabilization)
      policies:                           # default scaleDown has ONE policy: Percent 100 / 15 s
        - type: Percent
          value: 100
          periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0       # default - scale up is not damped
      policies:                           # default scaleUp has TWO policies...
        - type: Pods
          value: 4
          periodSeconds: 15
        - type: Percent
          value: 100
          periodSeconds: 15
      selectPolicy: Max                   # ...and takes whichever allows the bigger jump
```

**If they push back — "your consumer is CPU-idle but the queue has 50,000 messages. What does HPA do?"** — Nothing, and that is the honest answer. CPU-based HPA cannot see a queue. For queue-driven integration workloads you use **KEDA**, which is an external metrics adapter plus a `ScaledObject` that reads Service Bus active message count, Kafka consumer lag or Event Hub lag, and — crucially — can scale to **zero**, which plain HPA cannot (`minReplicas` must be ≥ 1 without the alpha `HPAScaleToZero` gate). KEDA creates and drives an HPA underneath; it does not replace it. On this JD, KEDA is the right answer for "Batch Jobs using event streaming".

---

### Q4. "What is the difference between git pull and git fetch?"
`[EY-LOGGED]` `[DEVOPS ROUND]`

**Answer:** `git fetch` downloads remote objects and updates the remote-tracking refs — `origin/main` — and touches nothing in your working tree. `git pull` is `git fetch` followed immediately by a merge (or a rebase with `--rebase`) into your current branch. Fetch is safe and read-only; pull mutates your branch and can leave you in a conflict state.

```bash
git fetch --prune origin                # update origin/*, delete stale remote-tracking refs
git log --oneline HEAD..origin/main     # what is on the remote that I don't have
git diff HEAD origin/main -- infra/     # review before integrating
git pull --rebase --autostash origin main
git config --global pull.rebase true    # team default: linear history, clean GitOps diffs
```

**If they push back — "why does this matter for a platform engineer?"** — Because in GitOps the Git history *is* the deploy history. Merge commits from careless `git pull` scramble the audit trail that a financial-services client will be asked to produce, and they make `git bisect` on a bad prod release much harder. So the settings I'd insist on are `pull.rebase=true`, linear history required on the protected branch, and signed commits — which makes the manifest repo read as an ordered, attributable ledger of every production change.

---

### Q5. "What are the objects in a Kubernetes service?"
`[EY-LOGGED]` `[DEVOPS ROUND]`

**Answer:** A Service is a stable virtual IP plus a DNS name that load-balances to a set of pods selected by labels. Its own key fields are `spec.selector`, `spec.ports` (with `port`, `targetPort`, optional `nodePort`), `spec.type` and `spec.clusterIP`. The object it *produces* is the one interviewers are usually fishing for: the endpoints controller writes matching pod IPs into **EndpointSlice** objects (the modern replacement for the legacy `Endpoints` object). If EndpointSlices are empty, the Service is a black hole.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orders-api
  namespace: integration
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: orders-api
  ports:
    - name: http
      port: 80          # the Service's port
      targetPort: 8000  # the container's port
      protocol: TCP
```

```bash
kubectl get svc orders-api -n integration -o wide
kubectl get endpointslices -n integration -l kubernetes.io/service-name=orders-api
kubectl describe svc orders-api -n integration     # "Endpoints: <none>" == selector mismatch
```

**Service types, in one line each:** `ClusterIP` — internal only, the default. `NodePort` — a port on every node, 30000–32767. `LoadBalancer` — provisions a cloud LB (Azure Standard LB on AKS). `ExternalName` — a CNAME, no proxying, useful as a seam when strangling a legacy endpoint. **Headless** (`clusterIP: None`) — no VIP, DNS returns pod IPs, which is what StatefulSets use.

**If they push back — "Service vs Ingress vs Gateway API?"** — Service is L4 inside the cluster. Ingress is L7 HTTP routing into the cluster, but its extension model is annotation soup, which is exactly why every vendor implemented it differently. **Gateway API** is the successor: role-oriented CRDs — `GatewayClass` owned by the platform team, `Gateway` owned by the cluster operator, `HTTPRoute` owned by the app team. That role split is a platform-engineering answer, and it is the one to give on this JD.

---

### Q6. "What is the difference between async and await?"
`[EY-LOGGED]` `[GDS SENIOR CONSULTANT]`

**Answer:** `async` marks a function as a coroutine so calling it returns a coroutine object instead of running; `await` is the point inside a coroutine where it yields control back to the event loop until an awaitable completes. `async` declares, `await` suspends. The practical consequence: an `async def` with no `await` in it gives you zero concurrency, and one blocking call inside a coroutine freezes the entire event loop and every other request on that worker.

```python
import asyncio
import httpx

URLS = ["https://api.internal/orders", "https://api.internal/customers", "https://api.internal/pricing"]

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url, timeout=10.0)   # suspends here; loop runs other tasks
    return resp.status_code

async def main() -> list[int]:
    async with httpx.AsyncClient() as client:
        # gather -> concurrent. A for-loop with await inside -> sequential.
        return await asyncio.gather(*(fetch(client, u) for u in URLS))

asyncio.run(main())
```

**If they push back — "so async makes it faster?"** — Only for I/O-bound work. Python asyncio is single-threaded cooperative concurrency; it overlaps *waiting*, not *computing*. For CPU-bound work it is strictly slower than a thread pool and much slower than `multiprocessing`. In an integration service the win is real and large — a FastAPI worker awaiting Service Bus, an APIM-fronted backend and SQL concurrently handles orders of magnitude more in-flight requests than a sync worker of the same size.

---

### Q7. "What is a thread pool?"
`[EY-LOGGED]` `[GDS SENIOR CONSULTANT]`

**Answer:** A thread pool is a bounded set of pre-created worker threads fed by a shared work queue, so you pay thread-creation cost once and cap concurrency deliberately instead of spawning a thread per task. In Python it is `concurrent.futures.ThreadPoolExecutor`; its default `max_workers` since 3.8 is `min(32, os.cpu_count() + 4)`. In an async service the thread pool is where you exile blocking calls so they cannot stall the event loop.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

import zeep  # blocking SOAP client - the classic legacy integration case


def call_legacy_soap(order_id: str) -> dict:
    client = zeep.Client("https://erp.internal/OrderService?wsdl")
    return client.service.GetOrder(orderId=order_id)


async def get_order(order_id: str) -> dict:
    # asyncio.to_thread uses the loop's default ThreadPoolExecutor.
    return await asyncio.to_thread(call_legacy_soap, order_id)


async def get_orders_bounded(ids: list[str]) -> list[dict]:
    # Explicit pool = explicit backpressure on a fragile legacy backend.
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="soap") as pool:
        loop = asyncio.get_running_loop()
        return await asyncio.gather(*(loop.run_in_executor(pool, call_legacy_soap, i) for i in ids))
```

**If they push back — "why bound it at 8?"** — Because the pool size is a contract with the downstream system, not a performance dial. A 30-year-old SOAP ERP with a 20-connection limit does not get faster when I send it 200 concurrent calls; it gets slower and then it falls over and takes the whole integration estate with it. Bounding the pool is the **Bulkhead** pattern, and it is the cheapest form of Queue-Based Load Levelling you can implement in-process.

---

### Q8. "Multithreading vs multiprocessing in Python."
`[EY-LOGGED-ADJACENT]` `[VERY LIKELY FOLLOW-UP TO Q7]`

**Answer:** Threads share one interpreter and one memory space, so on CPython the GIL lets only one thread execute bytecode at a time — threads win for I/O-bound work and buy you nothing for CPU-bound work. Processes each get their own interpreter and GIL, so they achieve true parallelism on multiple cores, at the cost of process startup and having to pickle everything across the boundary. Rule of thumb: **I/O → asyncio first, threads second; CPU → processes.**

| Axis | `threading` / `ThreadPoolExecutor` | `multiprocessing` / `ProcessPoolExecutor` | `asyncio` |
|---|---|---|---|
| Parallel on N cores | No (GIL) | Yes | No |
| Memory | Shared | Separate, pickled IPC | Shared |
| Switch cost | ~µs | ~ms (fork/spawn) | ~ns (function call) |
| Blocking call safe | Yes | Yes | **No** — freezes the loop |
| Good for | Blocking SDKs, SOAP, legacy drivers | Parsing 10 GB of EDI, embeddings, compression | Thousands of concurrent HTTP/AMQP calls |

**If they push back — "isn't the GIL gone?"** — Careful, and this is a good place to be precise: CPython 3.13 shipped an **optional** free-threaded build (PEP 703) behind a build flag, and 3.14 continues that work; it is not the default interpreter you get from `python:3.12-slim` or from Azure Functions. So in production today the GIL is still the operating assumption. Saying "the GIL is gone" is the wrong answer; saying "there is an experimental free-threaded build, but I still design as if the GIL is there" is the senior one.

---

### Q9. "What is MRO in Python?"
`[EY-LOGGED-ADJACENT]` `[PYTHON DEPTH PROBE]`

**Answer:** Method Resolution Order is the deterministic, linearised sequence of classes Python searches when it resolves an attribute. Since 2.3 it is computed by the **C3 linearisation** algorithm, which guarantees three things: a class precedes its parents, parents keep their declaration order, and the result is monotonic. It is what makes cooperative `super()` work correctly across a diamond.

```python
class Adapter:
    def send(self) -> str:
        return "Adapter"

class RetryMixin(Adapter):
    def send(self) -> str:
        return "Retry -> " + super().send()

class MetricsMixin(Adapter):
    def send(self) -> str:
        return "Metrics -> " + super().send()

class SapAdapter(RetryMixin, MetricsMixin):
    pass

print([c.__name__ for c in SapAdapter.__mro__])
# ['SapAdapter', 'RetryMixin', 'MetricsMixin', 'Adapter', 'object']
print(SapAdapter().send())
# Retry -> Metrics -> Adapter
```

**If they push back — "when does C3 fail?"** — When no consistent linearisation exists, Python raises `TypeError: Cannot create a consistent method resolution order (MRO)` at class-creation time — e.g. `class D(B, C)` and `class E(C, B)` combined. The practical takeaway for a platform engineer: `super()` is not "call my parent", it is "call the next class in *this instance's* MRO", which is why mixins must call `super()` unconditionally to stay cooperative.

---

### Q10. "classmethod vs staticmethod."
`[EY-LOGGED-ADJACENT]` `[PYTHON DEPTH PROBE]`

**Answer:** A `classmethod` receives the class as its first argument `cls`, so it participates in inheritance and is the natural home for alternative constructors. A `staticmethod` receives nothing implicit — it is a plain function that lives in the class namespace for cohesion. If the method needs to construct or dispatch on the class, use `classmethod`; if it is a pure helper, use `staticmethod`.

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderEvent:
    order_id: str
    amount_minor: int      # money in minor units. Never float.
    currency: str

    @classmethod
    def from_service_bus(cls, body: bytes) -> "OrderEvent":
        """Alternative constructor. `cls` means CorporateOrderEvent.from_service_bus()
        returns a CorporateOrderEvent, not an OrderEvent."""
        d = json.loads(body)
        return cls(
            order_id=d["orderId"],
            # Decimal, not float: float("1.15") * 100 is 114.99999999999999,
            # so int(...) silently books ₹1.14. In payments that is an audit finding.
            amount_minor=int(Decimal(str(d["amount"])) * 100),
            currency=d.get("currency", "INR"),
        )

    @staticmethod
    def is_retryable(dead_letter_reason: str) -> bool:
        """Pure predicate. No class, no instance."""
        return dead_letter_reason in {"MaxDeliveryCountExceeded", "TTLExpiredException"}


class CorporateOrderEvent(OrderEvent):
    pass


assert type(CorporateOrderEvent.from_service_bus(b'{"orderId":"1","amount":"10.50"}')) is CorporateOrderEvent
```

**If they push back — "why not just a module-level function?"** — Often you should, and saying so is a signal of taste rather than dogma. The reason to keep it on the class is discoverability and the polymorphism in that `assert`: a subclass gets the correct constructor for free. A module function would hard-code `OrderEvent(...)` and silently break every subclass — which in an adapter hierarchy of twelve ERP variants is a real bug, not a style debate.

---

### Q11. "Write a query for the second highest salary."
`[EY-LOGGED]` `[RECURS ACROSS EY ROLES]`

**Answer:** I write the window-function version because it is the one that handles ties and is portable, and I state the tie semantics before I write anything — "second highest *distinct* salary, or second row?" Those are different queries and getting asked which is the actual test.

```sql
-- 1. Window function. DENSE_RANK -> second highest DISTINCT salary, ties collapsed.
SELECT DISTINCT salary AS second_highest
FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
  FROM employee
) ranked
WHERE rnk = 2;

-- 2. No window functions available (older MySQL / interviewer constraint).
SELECT MAX(salary) AS second_highest
FROM employee
WHERE salary < (SELECT MAX(salary) FROM employee);

-- 3. LIMIT/OFFSET. Fastest, but returns ZERO ROWS (not NULL) when there is no 2nd salary.
--    The outer SELECT is what forces a single NULL row - this is the LeetCode-correct form.
SELECT (
  SELECT DISTINCT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET 1
) AS second_highest;

-- 4. Nth highest per department - the follow-up they actually want.
SELECT department_id, salary
FROM (
  SELECT department_id, salary,
         DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rnk
  FROM employee
) t
WHERE rnk = 2;
```

**If they push back — "which one would you ship?"** — Version 1 or 4. Version 2 is O(2 scans) and breaks the moment they say "per department". Version 3 is the fastest with an index on `salary DESC` but its empty-result behaviour has burned every candidate who wrote it from memory. And `RANK()` vs `DENSE_RANK()` is the trap: with salaries 100, 100, 90, `RANK()` returns nothing at rank 2 while `DENSE_RANK()` returns 90.

---

### Q12. "Convince me to adopt AWS for our company." (or Azure)
`[EY-LOGGED]` `[EY SENIOR ANALYST — PERSUASION IS EXPLICITLY TESTED]`

**Answer:** I would not start by convincing you of a cloud; I would start by asking what would make this decision *wrong*, because in financial services the constraints usually decide it before the feature comparison does. Then: **what is your existing identity provider, where is your data allowed to live, what does your existing licensing look like, and what can your team already operate on day one?** If the answer to the first is Entra ID and to the third is an EA with Microsoft, the technical comparison is largely academic — the integration and identity tax of a second cloud will exceed any per-service advantage.

**The four-move structure — use it whichever cloud they name:**

| Move | What you say |
|---|---|
| 1. Reframe | "Adopt for *what workload*? A greenfield data platform and a 15-year-old core banking integration estate are different decisions." |
| 2. Constraints first | Identity/SSO, data residency and regulator, existing EA/licensing, in-house skills, egress cost, exit clause. |
| 3. Then, and only then, differentiators | AWS: breadth, maturity of EKS/Lambda, market share, best-in-class primitives. Azure: Entra ID as the single identity plane, EA discount surface, first-party SAP/D365/M365 connectivity, Azure Integration Services as a coherent iPaaS, and — for EY specifically — the **$1bn, five-year EY–Microsoft alliance announced in May 2026**. |
| 4. Close with the reversible decision | "Land on one primary cloud, but keep the integration layer portable: containers not proprietary runtimes, OpenTelemetry not a vendor agent, Terraform not ARM-only, and a documented exit path. That is how you buy the discount without buying the lock-in." |

**If they push back — "stop hedging, pick one"** — Then Azure, and here is the single reason: **identity**. Every integration in a bank terminates in an authorisation decision, and Entra ID with managed identities and Conditional Access removes stored credentials from the entire estate — APIM to backend, Function to Service Bus, GitHub Actions to a subscription via OIDC federation. On AWS I would rebuild that with IAM roles, IRSA and an external IdP and get 90% of the way there with three times the moving parts. If the client's identity plane were Okta and their data estate were already on S3, I would give you the mirror-image answer, and I would mean it.

---

## 2. 10-Minute Final Scan

Priority ordered. If you can say all 25 in one sentence each, you are ready.

| # | Thing | The one sentence |
|---|---|---|
| 1 | **Your platform-engineer frame** | "I build the paved road — templates, golden charts, shared policy fragments, self-service modules — not one app." |
| 2 | **Service Bus vs Event Grid vs Event Hubs** | Broker for commands with guaranteed delivery / router for discrete reactive events / firehose for telemetry streams with replay. |
| 3 | **GitOps in one sentence** | Git is the desired state, an in-cluster agent pulls and reconciles continuously, drift is auto-healed, and the audit trail is the Git log. |
| 4 | **Push vs pull deployment** | Push needs cluster credentials in the CI system; pull keeps credentials inside the cluster and gives you continuous reconciliation. |
| 5 | **HPA formula** | `ceil(replicas × current/target)`, 15 s loop, 10% tolerance, max across metrics; scale-up undamped (4 pods or 100%/15 s), scale-down 300 s stabilization then 100%/15 s. |
| 6 | **KEDA vs HPA** | KEDA adds event-source metrics (queue depth, consumer lag) and scale-to-zero; it drives an HPA underneath. |
| 7 | **Liveness vs readiness vs startup** | Liveness restarts, readiness removes from EndpointSlice, startup gates the other two for slow boots. |
| 8 | **Idempotency** | Client-supplied `Idempotency-Key` + a dedupe table keyed on business ID + Service Bus `MessageId` duplicate detection. |
| 9 | **At-least-once is the default** | Exactly-once end-to-end does not exist; you get at-least-once delivery plus an idempotent consumer. |
| 10 | **DLQ discipline** | Every queue has a DLQ, a redrive path, an alert on depth > 0, and a runbook naming the owner. |
| 11 | **Terraform state** | Remote backend in Azure Storage with blob-lease locking, one state per env, never commit `.tfstate`. |
| 12 | **OIDC federation in CI** | `permissions: id-token: write` + a federated credential on the app registration — zero stored cloud secrets. |
| 13 | **Security scanning taxonomy** | SAST=code, DAST=running app, SCA=dependencies, IaC scan=templates, secret scan=history. All four gates or none. |
| 14 | **Managed identity** | System-assigned dies with the resource; user-assigned is shareable and survives — use user-assigned for platform components. |
| 15 | **APIM `validate-jwt`** | Validates signature via OpenID config, `iss`, `aud`, `exp`, and required claims, at the edge, before the backend. |
| 16 | **SOAP → REST façade** | APIM API from WSDL + `xml-to-json` / `json-to-xml` + `set-body` templating; the ACL pattern, not a passthrough. |
| 17 | **RFC 9457** | Problem Details for HTTP APIs, obsoletes 7807, `application/problem+json`, members `type/status/title/detail/instance`. |
| 18 | **Batch via streaming** | Chunk the batch into messages, land the payload in Blob and pass a claim check, drive workers with KEDA, reconcile on a watermark. |
| 19 | **Saga** | Orchestrated (Durable Functions / Logic App with compensating branches) beats choreographed when a human has to debug it. |
| 20 | **Blue-green vs canary** | Blue-green flips 100% at once and rolls back instantly; canary shifts a percentage with automated metric analysis (Flagger/Argo Rollouts). |
| 21 | **Observability trio** | Metrics for alerting, traces for causality, logs for detail — one W3C `traceparent` correlated across APIM, Service Bus and AKS. |
| 22 | **FS compliance hook** | Immutable audit trail, data residency, PII minimisation, four-eyes approval on prod, evidence you can hand a regulator. |
| 23 | **Your GenAI pivot** | "An agent platform is an integration platform" — use once, in L2, not in L1. |
| 24 | **STAR is the literal rubric** | EY scores relevant experience / action taken / result. Three sentences of situation, five of action, one of measured result. |
| 25 | **Sub-grade is the money** | SC1 vs SC3 is an ~₹11L spread at overlapping experience — the fitment conversation, not L1, decides it. See [PLAN.md](PLAN.md). |

---

## 3. Comparison Tables

### 3.1 Service Bus vs Event Grid vs Event Hubs vs Storage Queue

| | **Service Bus** | **Event Grid** | **Event Hubs** | **Storage Queue** |
|---|---|---|---|---|
| Model | Broker, pull | Router, push (+ pull in namespaces) | Stream/log, pull by offset | Broker, pull |
| Unit | Message (a command) | Event (a fact) | Event (telemetry datum) | Message |
| Max size | 256 KB Std / up to 100 MB Premium AMQP | 1 MB | 1 MB Std, 20 MB Dedicated | 64 KB |
| Ordering | FIFO via **sessions** | None | Per partition | None |
| Replay | No (once consumed, gone) | No | **Yes**, by offset within retention | No |
| DLQ | Native + transfer DLQ | Native (blob/queue/SB) | No | No (build your own) |
| Dedupe | Native, `MessageId` window | No | No | No |
| Consumers | Competing consumers | Fan-out to ≤ 500 subs/topic | Consumer groups + partitions | Competing consumers |
| Transactions | Yes | No | No | No |
| Pick when | Money, orders, "must not lose, must not double-process" | "Something happened, whoever cares should react" | 50k events/s, replay, downstream analytics | You already have a storage account and need cheap and simple |

### 3.2 Kafka vs RabbitMQ vs Service Bus

| | **Kafka** | **RabbitMQ** | **Azure Service Bus** |
|---|---|---|---|
| Model | Distributed commit log | AMQP 0-9-1 broker with exchanges | Managed AMQP 1.0 broker |
| Retention | Time/size based; consumers replay | Until acked, then deleted | Until settled or TTL |
| Ordering | Per partition | Per queue | Per session |
| Routing | Consumer picks topic/partition | Exchange types: direct, topic, fanout, headers | Topic + SQL/correlation filters |
| Scale unit | Partitions | Queues + consumers | Partitions (Premium) + MUs |
| Consumer position | Offset owned by consumer group | Broker-owned ack | Broker-owned lock |
| Ops burden | High, but lower since **Kafka 4.0 (Mar 2025) removed ZooKeeper** — KRaft is the only mode; or offload to Confluent / the Event Hubs Kafka endpoint | Medium | Lowest (PaaS) |
| Killer feature | Replay + stream processing + log compaction | Flexible routing, low latency, plugins | Sessions, dedupe, DLQ, transactions, Entra ID auth |
| Pick when | Event sourcing, CDC, analytics fan-out, high throughput | Complex routing on-prem, RPC-ish workloads | Enterprise Azure integration, FS transactional messaging |

### 3.3 Logic Apps vs Functions vs Data Factory vs APIM

| | **Logic Apps** | **Azure Functions** | **Data Factory** | **APIM** |
|---|---|---|---|---|
| Nature | Low-code workflow | Code, event-triggered | Bulk data movement | API gateway + lifecycle |
| Unit of work | Action | Execution | Pipeline activity / DIU | Request |
| Latency | ms–s | ms | minutes | single-digit ms |
| Connectors | 1,400+ managed | Bindings + SDKs | 90+ data connectors, SHIR for on-prem | N/A |
| Long-running | 90 days | 30 min default (unbounded on Premium/Flex) | Hours | No — `forward-request` defaults to **300 s** and values > 240 s may not be honoured (idle-connection drops) |
| Who reads it | Business analyst | Developer | Data engineer | API consumer |
| Do NOT use for | Tight loops, per-request latency | Workflows a BA must read | Per-record event integration | Business logic or DB calls |

### 3.4 Terraform vs Bicep vs ARM vs Pulumi

| | **Terraform** | **Bicep** | **ARM JSON** | **Pulumi** |
|---|---|---|---|---|
| Language | HCL, declarative | DSL → transpiles to ARM | JSON | Real code (Python/TS/Go/C#) |
| State | Explicit state file (remote backend + lock) | Stateless — Azure RM is the state | Stateless | Explicit state (Pulumi Cloud/self-managed) |
| Multi-cloud | Yes, ~4,000 providers | **Azure only** | Azure only | Yes |
| Day-0 support for new Azure features | Lags (provider release) | Day one | Day one | Lags |
| Preview | `terraform plan` | `az deployment group what-if` | `what-if` | `pulumi preview` |
| Modules | Registry + private modules | Modules + **Azure Verified Modules (AVM)** | Linked/nested templates | Component resources |
| Drift | `plan -refresh-only` | Redeploy is idempotent; no drift report | Same | `pulumi refresh` |
| Pick when | Multi-cloud, or one language across estate | Azure-only shop wanting zero state ops | Never by hand (generated only) | Team wants loops/tests in a real language |

**The senior line:** "Bicep is a better *authoring* experience for Azure-only; Terraform is a better *platform* because the state file gives me a plan, drift detection and a module registry other teams consume. On this JD I'd default to Terraform for the shared platform and accept Bicep where a client is Azure-native and wants day-one resource support."

### 3.5 Azure DevOps vs GitHub Actions vs Jenkins vs GitLab CI

| | **Azure DevOps** | **GitHub Actions** | **Jenkins** | **GitLab CI** |
|---|---|---|---|---|
| Config | YAML pipelines | YAML workflows | Groovy Jenkinsfile / UI | `.gitlab-ci.yml` |
| Reuse primitive | **Templates** (`extends`, `template:`) | **Reusable workflows** + composite actions | Shared libraries | `include:` + `extends:` |
| Hosted runners | Microsoft-hosted (2-core, 7 GB, ~10 GB free disk) | GitHub-hosted + larger runners | Self-managed | GitLab-hosted / self-managed |
| Secretless cloud auth | Workload identity federation service connection | OIDC (`id-token: write`) | Plugin-dependent | OIDC (`id_tokens:`) |
| Approvals/gates | Environments + checks + Azure Boards link | Environments + required reviewers | Plugin | Protected environments |
| Governance strength | Strongest (enterprise gates, audit, work-item traceability) | Strong and improving | Weakest without effort | Strong |
| Pick when | Enterprise/FS client already on ADO | Repo already on GitHub, want OIDC + Actions ecosystem | Legacy estate you inherit | GitLab shop |

**The platform answer:** "Whichever tool, the deliverable is the same: a versioned, reusable pipeline *template* with the build, test, SAST/SCA/secret/IaC scan, sign, SBOM, and deploy stages baked in, so a new integration service gets a compliant pipeline by referencing eight lines, not by copying 300."

### 3.6 ArgoCD vs Flux

| | **Argo CD** | **Flux CD** |
|---|---|---|
| Shape | One application (controller + API + **web UI**) | A set of CRD controllers (source, kustomize, helm, notification, image) |
| Current API groups | `argoproj.io/v1alpha1` for `Application`, `ApplicationSet`, `AppProject` (still v1alpha1 — say it, don't guess a v1) | `source.toolkit.fluxcd.io/v1` (`GitRepository`), `kustomize.toolkit.fluxcd.io/v1` (`Kustomization`), `helm.toolkit.fluxcd.io/v2` (`HelmRelease`) |
| Default reconciliation | **120 s + up to 60 s jitter** (`timeout.reconciliation` in `argocd-cm`) ≈ 3 min | Per-object `.spec.interval`, **required field**; docs use `5m0s`/`10m0s` |
| Multi-tenancy | `AppProject` with source/destination/resource allow-lists | Namespace + RBAC + `Kustomization` `serviceAccountName` |
| Multi-app pattern | App-of-Apps, ApplicationSet generators | `Kustomization` tree, `GitRepository` per source |
| UI | Rich, first-class — matters to auditors and support teams | CLI-first (`flux` CLI); UI via Weave GitOps |
| Helm handling | Renders with `helm template` (no Tiller, no Helm release history by default) | `HelmRelease` CR — a real Helm release with history |
| Progressive delivery | **Argo Rollouts** | **Flagger** |
| Image automation | Argo CD Image Updater (separate) | Built-in image reflector + automation controllers |
| Pick when | You want a UI, app-centric view, and enterprise RBAC | You want small composable controllers and Kubernetes-native everything |

**Say this:** "Both are CNCF graduated and both do the same job correctly. I'd choose Argo CD for a consulting engagement because the UI is what lets a client's support team see sync status without kubectl — and on a Big-4 delivery that visibility is worth more than architectural elegance."

### 3.7 Push vs Pull Deployment

| | **Push (CI deploys)** | **Pull (GitOps agent)** |
|---|---|---|
| Who initiates | CI runner outside the cluster | Agent inside the cluster |
| Credentials | Cluster admin creds live in CI | None leave the cluster; agent has read on Git |
| Network | CI must reach the API server (public or peered) | Cluster reaches out to Git — works with a private API server |
| Drift | Undetected until next deploy | Continuously reconciled, `selfHeal` reverts it |
| Audit | CI logs | **Git history = the audit trail** |
| Rollback | Re-run an old pipeline | `git revert`, agent converges |
| Multi-cluster | N × credentials in CI | N × agents, one repo |
| Weakness | Blast radius of a compromised CI runner | Secrets need a separate story (SOPS/ESO/Sealed Secrets) |

### 3.8 Sealed Secrets vs SOPS vs External Secrets vs Secrets Store CSI Driver

| | **Sealed Secrets** | **SOPS (+ age/KMS)** | **External Secrets Operator** | **Secrets Store CSI Driver** |
|---|---|---|---|---|
| Where the ciphertext lives | In Git (`SealedSecret` CR) | In Git (encrypted YAML) | **Not in Git** — a reference only | Not in Git — a `SecretProviderClass` reference |
| Source of truth | The cluster's sealing key | Your KMS/age key | Key Vault / Secrets Manager / Vault | Key Vault / Vault |
| Materialises as | K8s `Secret` | K8s `Secret` | K8s `Secret` (synced) | **Mounted file** (optionally also a Secret) |
| Rotation | Re-seal and commit | Re-encrypt and commit | Automatic on refresh interval | On pod restart / rotation poller |
| Cluster portability | Poor — sealed to one cluster's key | Good | Good | Good |
| Best for | Small teams, no external vault | Flux-native repos, multi-env | **The enterprise default** | When you want secrets as files, never as etcd objects |

**Say this:** "For a regulated client I'd default to External Secrets or the CSI driver with Key Vault plus workload identity, because the regulator's question is 'who can read this secret and when did they' — and only the vault has that log. Sealed Secrets puts ciphertext in Git, which is fine until you need key rotation across 30 clusters."

### 3.9 Flagger vs Argo Rollouts

| | **Flagger** | **Argo Rollouts** |
|---|---|---|
| Home | Flux ecosystem (works standalone) | Argo ecosystem |
| Object | Decorates an existing `Deployment` via a `Canary` CR | Replaces `Deployment` with a `Rollout` CR |
| Traffic shaping | Service mesh / ingress (Istio, Linkerd, NGINX, Gateway API) | Same, plus a built-in weighted-replica mode with no mesh at all |
| Analysis | `MetricTemplate` + webhooks, automatic rollback on failed checks | `AnalysisTemplate` + `AnalysisRun` |
| UI | None (Grafana dashboards) | Argo CD UI + `kubectl argo rollouts` plugin |
| Strategies | Canary, A/B, blue-green | Canary, blue-green, experiments |
| Pick when | You already run Flux | You already run Argo CD, or you want progressive delivery without a mesh |

### 3.10 REST vs GraphQL vs gRPC vs SOAP

| | **REST** | **GraphQL** | **gRPC** | **SOAP** |
|---|---|---|---|---|
| Contract | OpenAPI (optional in practice) | SDL schema (mandatory) | `.proto` (mandatory) | WSDL + XSD (mandatory) |
| Transport | HTTP/1.1+ | HTTP POST (usually) | HTTP/2 | HTTP, JMS, SMTP |
| Payload | JSON | JSON | Protobuf binary | XML |
| Caching | HTTP caching works natively | Hard (one POST URL) | No HTTP caching | No |
| Streaming | SSE / chunked | Subscriptions (WS) | **First-class bidi streaming** | No |
| Errors | Status codes + RFC 9457 | Always 200 + `errors[]` | Status codes (`google.rpc.Status`) | SOAP Fault |
| Rate limiting | Per route, easy | Hard — needs query cost analysis | Per method | Per operation |
| Browser | Native | Native | Needs gRPC-Web proxy | Painful |
| Pick when | Public/partner APIs, default | Aggregating many backends for many client shapes | Internal service-to-service, low latency, polyglot | You inherited it, or the partner is a bank/insurer that mandates it |

### 3.11 APIM vs Apigee vs Kong

| | **Azure APIM** | **Google Apigee** | **Kong** |
|---|---|---|---|
| Model | Azure PaaS (+ self-hosted gateway container) | GCP PaaS (+ hybrid) | OSS/enterprise, self-hosted or Konnect SaaS |
| Policy language | **XML policy documents**, four scopes | Policies + JS/Java callouts | Lua plugins + declarative config |
| Identity | Native Entra ID, managed identity to backends | Native Google IAM / OAuth | Plugin (OIDC enterprise) |
| Hybrid | Self-hosted gateway on AKS/Docker | Apigee hybrid on any k8s | Native — it's just a container |
| Dev portal | Built-in, customisable | Built-in, strongest | Enterprise add-on |
| K8s-native | Partial (self-hosted gw) | Partial | **Best** — Kong Ingress Controller, Gateway API |
| Pick when | Azure shop (this JD) | Deep analytics/monetisation needs | Cloud-agnostic, k8s-native platform, cost-sensitive |

### 3.12 Liveness vs Readiness vs Startup Probes

| | **Liveness** | **Readiness** | **Startup** |
|---|---|---|---|
| Failure action | **Restart the container** | Remove pod from Service EndpointSlice | Kill container; blocks the other two until it passes |
| Answers | "Is it wedged?" | "Should it get traffic right now?" | "Has it finished booting?" |
| Should check deps? | **No** — never check the DB in liveness | Yes, check critical deps | No |
| Typical | `GET /healthz` — process alive, event loop responsive | `GET /readyz` — DB pool + Service Bus reachable | `GET /healthz` with a high `failureThreshold` |
| Defaults | `initialDelaySeconds 0`, `periodSeconds 10`, `timeoutSeconds 1`, `successThreshold 1`, `failureThreshold 3` | same | same, but set `failureThreshold × periodSeconds` > worst-case boot |

**The classic outage:** liveness probe queries the database; the database has a blip; every pod in every replica set fails liveness simultaneously and restarts; the restart storm prevents recovery. **Liveness must never depend on anything external.**

### 3.13 Deployment vs StatefulSet vs DaemonSet vs Job/CronJob

| | **Deployment** | **StatefulSet** | **DaemonSet** | **Job / CronJob** |
|---|---|---|---|---|
| Identity | Random pod names, interchangeable | **Stable ordinal names** `web-0`, `web-1` | One per node | Run to completion |
| Storage | Shared/none | `volumeClaimTemplates` → per-pod PVC that survives reschedule | Usually hostPath | Ephemeral |
| Network | Service VIP | **Headless Service** → stable per-pod DNS | Node-local | N/A |
| Ordering | None | Ordered create/scale/delete | N/A | N/A |
| Use for | Stateless APIs, workers, integration services | Kafka brokers/KRaft controllers, etcd, Postgres, anything with per-instance identity | Log agent, node exporter, CNI, security agent | Batch, migrations, nightly reconciliation |

### 3.14 HPA vs VPA vs Cluster Autoscaler vs KEDA

| | **HPA** | **VPA** | **Cluster Autoscaler** | **KEDA** |
|---|---|---|---|---|
| Scales | Replica count | Requests/limits per pod | **Nodes** | Replica count from event sources |
| Trigger | CPU/memory/custom/external metrics | Historical usage | Unschedulable pods / underused nodes | Queue depth, consumer lag, cron, 70+ scalers |
| Scale to zero | No (without alpha gate) | N/A | Node pools to 0 | **Yes** |
| Conflicts | — | **Conflicts with HPA on the same resource metric** | — | Wraps HPA, no conflict |
| For this JD | Baseline CPU scaling | Right-sizing recommendations, `updateMode: "Off"` in prod | Pair with HPA always | **The answer for message-driven batch workers** |

### 3.15 Blue-Green vs Canary vs Rolling

| | **Rolling** | **Blue-Green** | **Canary** |
|---|---|---|---|
| K8s default? | **Yes** (`maxSurge 25%`, `maxUnavailable 25%`) | No — needs two stacks + a switch | No — needs mesh/ingress or Rollouts/Flagger |
| Infra cost | 1× + surge | **2×** | 1× + small surge |
| Blast radius during rollout | All users see a mix of versions | Zero until the flip, then 100% | Only the canary cohort |
| Rollback speed | Slow (roll back through the same process) | **Instant** (flip the selector back) | Fast (shift weight to 0) |
| Needs schema compat | Yes | Yes (both versions hit the same DB) | Yes |
| Automated verdict | No | Manual smoke test | **Yes** — metric analysis auto-promotes or auto-aborts |
| FS reality | Fine for internal | Common for regulated releases with a change window | Best, but needs mature SLO metrics first |

### 3.16 At-Most-Once vs At-Least-Once vs Exactly-Once

| | **At-most-once** | **At-least-once** | **"Exactly-once"** |
|---|---|---|---|
| Mechanism | Ack before processing (`ReceiveAndDelete`) | Ack after processing (`PeekLock` + Complete) | At-least-once delivery + idempotent/transactional consumer |
| Failure result | Message lost | Message duplicated | Effect applied once |
| Cost | Cheapest | Redelivery + dedupe logic | Coordination, dedupe store, or Kafka transactions |
| Where it's real | Kafka `EOS` within Kafka (`transactional.id` + `read_committed`) — **only inside Kafka** | The default everywhere | Not across an arbitrary network boundary |
| Say this | "Exactly-once *delivery* is impossible in a distributed system. Exactly-once *processing* is achievable, and it is spelled at-least-once delivery plus an idempotent consumer." |

### 3.17 APIM Revisions vs Versions

| | **Revision** | **Version** |
|---|---|---|
| Visible to consumer | **No** — same URL | **Yes** — `/v2`, `?api-version=`, or a header |
| Purpose | Non-breaking change, staged and tested before going current | Breaking change, run old and new in parallel |
| URL | `;rev=3` for testing only | Part of the public contract |
| Lifecycle | Make current, with a change-log entry | Deprecate with `Sunset` (RFC 8594) + `Deprecation` (RFC 9745) headers |
| Rollback | Set the previous revision current — instant | Consumers must migrate |
| Rule of thumb | If a consumer's existing call still works → revision. If it breaks → version. |

### 3.18 System-Assigned vs User-Assigned Managed Identity

| | **System-assigned** | **User-assigned** |
|---|---|---|
| Lifecycle | Created with, and **deleted with**, the resource | Independent Azure resource |
| Cardinality | 1 resource ↔ 1 identity | 1 identity ↔ many resources |
| RBAC grants | Re-granted on every recreate — Terraform destroy/create breaks them | Grant once, survives redeploys |
| Federation (`WIF`) | n/a | Add federated credentials for GitHub Actions / AKS workload identity |
| Pick | Single-purpose resource, tight blast radius | **Platform default** — stable object ID for IaC, shared across a service's Function + Logic App + AKS workload |

### 3.19 id_token vs access_token (vs refresh_token)

| | **id_token** | **access_token** | **refresh_token** |
|---|---|---|---|
| Spec | OIDC | OAuth 2.0 (RFC 6749) | OAuth 2.0 |
| Audience | **The client** | **The resource/API** | The authorization server |
| Contents | Who the user is: `sub`, `iss`, `aud`, `exp`, `nonce`, `iat` | What the caller may do: `scp`/`roles`, `aud`, `exp` | Opaque |
| Format | Always a JWT | JWT or opaque — **format is not guaranteed** | Opaque |
| API should validate | **Never** — an API that accepts an id_token is a finding | Yes | Never sees it |
| Lifetime | Short | Short (Entra: ~60–90 min, variable) | Long, rotate on use |

**The trap:** sending the `id_token` as the bearer token to your API. It has the wrong `aud`, carries no scopes, and means the API is authorising on identity rather than delegation.

### 3.20 authorization_code + PKCE vs client_credentials

| | **authorization_code + PKCE** | **client_credentials** |
|---|---|---|
| Actor | A **user** delegating to an app | A **service** acting as itself |
| User present | Yes | No |
| Claims | `sub` = user, `scp` = delegated scopes | No `sub` user; `roles` = app permissions |
| PKCE | RFC 7636; **RFC 9700 requires it for *all* authorization-code clients**, confidential ones included (OIDC `nonce` is the only accepted alternative for confidential clients) | N/A |
| Consent | User or admin consent | Admin consent only |
| In this JD | Developer portal sign-in, partner web apps | **The default for every integration** — Logic App → API, Function → Service Bus, daemon → APIM |
| Never use | — | For anything where "who is the user" must appear in the audit log |

### 3.21 SAST vs DAST vs SCA vs IaC Scanning vs Secret Scanning

| | **SAST** | **DAST** | **SCA** | **IaC scanning** | **Secret scanning** |
|---|---|---|---|---|---|
| Input | Source code | Running app | Manifests/lockfiles | Terraform/Bicep/K8s/Helm | Repo + history |
| Finds | Injection, unsafe deserialisation, hardcoded crypto | Auth bypass, XSS, misconfig at runtime | Vulnerable/licensed dependencies | Public storage, no TLS, open NSG, privileged pods | Committed keys, tokens, connection strings |
| Stage | PR gate | Post-deploy to a test env | PR gate + nightly | **Plan stage — before apply** | Pre-commit + push protection |
| Tools | CodeQL, Semgrep, Bandit (Python) | OWASP ZAP, Burp | Trivy, Dependabot, `pip-audit`, Snyk | Checkov, tfsec, Trivy misconfig, KICS | Gitleaks, TruffleHog, GitHub push protection |
| False positives | High | Low | Low | Medium | Low |
| The JD wants | The JD names "SECURITY SCANNING" in responsibility 5 — name all five, then say **push protection + PR gate + nightly full scan + SBOM at build**. |

### 3.22 The Bonus Table — CQRS vs Event Sourcing vs Outbox

| | **CQRS** | **Event Sourcing** | **Transactional Outbox** |
|---|---|---|---|
| What it is | Separate read model from write model | State = the replay of an append-only event log | Write the message to a DB table in the same transaction as the state change; a relay publishes it |
| Solves | Divergent read/write scaling and shapes | Full audit history, temporal queries | The **dual-write problem** (DB commit succeeds, broker publish fails) |
| Cost | Eventual consistency between models | Schema evolution of events, snapshots, high skill floor | A relay process + dedupe downstream |
| Azure shape | Cosmos read model fed by change feed | Event Hubs/Kafka + projections | SQL outbox table + polling publisher, or Cosmos change feed → Function |
| FS relevance | High (regulatory read models) | High (audit trail is the point) | **Highest — this is the one to name unprompted** |

---

## 4. Numbers to Memorize (verified)

Every number below was checked against the vendor's own docs before it went in this table. If a number is not here, do not say it.

### 4.1 Azure Service Bus — *Microsoft Learn, service-bus-quotas / dead-letter-queues / duplicate-detection / message-transfers-locks-settlement*

| Thing | Value |
|---|---|
| Max message size, Basic & Standard | **256 KB** |
| Max message size, Premium | 1 MB default per entity; **up to 100 MB** single message over AMQP; **1 MB** over HTTP/SBMP; **1 MB** for any batch |
| Queue/topic size | 1–5 GB, or **80 GB** with partitioning (Basic/Std) / natively (Premium) |
| Namespace size | 400 GB Basic/Std; **1 TB per messaging unit** Premium |
| Subscriptions per topic | **2,000** (all tiers) |
| SQL filters per topic | 2,000 · Correlation filters per topic: **100,000** |
| Concurrent connections per namespace | **AMQP 5,000**, Net Messaging 1,000 |
| Concurrent receive requests per entity | 5,000 |
| Messages per transaction | **100** |
| **Lock duration** | **default 1 minute, maximum 5 minutes** |
| **MaxDeliveryCount default** | **10** |
| **Duplicate detection window** | **default 10 minutes**, min 20 seconds, **max 7 days** |
| Auto-forward max hops | **4** (`MaxTransferHopCountExceeded`) |
| Idle connection closed after | 10 minutes |
| DLQ path | `<queue>/$deadletterqueue` · `<topic>/Subscriptions/<sub>/$deadletterqueue` |
| Transfer DLQ path | `<queue>/$Transfer/$DeadLetterQueue` |
| Message property size | 32 KB per property, 64 KB cumulative header |
| Peek max / DeleteMessages max | 250 / 500 per call |

### 4.2 Azure Event Grid — *Microsoft Learn, event-grid/quotas-limits*

| Thing | Value |
|---|---|
| Max event size (custom/system/partner topics) | **1 MB** (cannot be increased) |
| Billing chunk | **64 KB** — a 128 KB event counts as two events |
| Publish rate per custom topic | **5,000 events/s or 5 MB/s**, whichever first |
| Event subscriptions per topic | **500** (100 for Azure-subscription-scoped) |
| Custom topics per Azure subscription | 100 · Domains: 100, with **100,000 topics per domain** |
| Retry/TTL on a basic-tier topic | **24 hours** — this is the retry time-to-live, not a queue you can replay from |
| Events per batch | 5,000 |
| Namespace (Standard tier) max event size / batch / events per request | 1 MB / 1 MB / 1,000 |
| Namespace topic retention | **7 days** |
| Namespace ingress / egress per TU | 1,000 events/s or 1 MB/s · up to 2,000 events/s or 2 MB/s |
| MQTT max message size | 512 KB |

### 4.3 Azure Event Hubs — *Microsoft Learn, event-hubs/event-hubs-quotas*

| Thing | Basic | Standard | Premium | Dedicated |
|---|---|---|---|---|
| Max publication size | 256 KB | **1 MB** | 1 MB | 20 MB |
| Consumer groups per hub | 1 | **20** | 100 | 1,000 |
| Partitions per hub | 32 | **32** | 100 (200/PU namespace cap) | 1,024 (2,000/CU) |
| Max retention | 1 day | **7 days** | 90 days | 90 days |
| Brokered connections/ns | 100 | 5,000 | 10,000/PU | 100,000/CU |
| Event storage | 84 GB/TU | 84 GB/TU | 1 TB/PU | 10 TB/CU |

**Throughput unit (Basic/Standard):** ingress **1 MB/s or 1,000 events/s**; egress **2 MB/s or 4,096 events/s**. Max **40 TUs**. Non-epoch receivers per consumer group: **5**.

### 4.4 Azure Queue Storage — *Microsoft Learn, storage-queues-introduction*

| Thing | Value |
|---|---|
| Max message size | **64 KB** |
| Message TTL | default **7 days**; from REST version 2017-07-29 any positive value, or **-1 = never expires** |
| Capacity | Millions of messages, up to the storage account limit |

### 4.5 Apache Kafka broker defaults — *kafka.apache.org/documentation/#brokerconfigs*

**Say this before any Kafka number:** Kafka **4.0 (18 March 2025) removed ZooKeeper entirely** — KRaft is the only mode, 3.9 is the bridge release you migrate through, and brokers/tools/Connect now require Java 17. The 4.x line has continued since. If you say "ZooKeeper quorum" in 2026 you have dated yourself by a full major version.

| Config | Default |
|---|---|
| `message.max.bytes` | **1048588** (~1 MB) |
| `log.retention.hours` | **168** (7 days) |
| `log.segment.bytes` | **1073741824** (1 GiB) |
| `min.insync.replicas` | **1** (production: set to 2 with RF=3) |
| `replica.lag.time.max.ms` | **30000** (ISR eviction threshold) |
| `num.partitions` | **1** |
| `offsets.retention.minutes` | **10080** (7 days) |
| `default.replication.factor` | **1** |
| `group.initial.rebalance.delay.ms` | **3000** |

### 4.6 Kubernetes — *kubernetes.io HPA + probes + pod-lifecycle docs*

| Thing | Value |
|---|---|
| HPA formula | `desiredReplicas = ceil(currentReplicas × currentMetricValue / desiredMetricValue)` |
| HPA sync period | **15 s** (`--horizontal-pod-autoscaler-sync-period`) |
| HPA tolerance | **0.1** (10%) |
| HPA initial readiness delay / CPU initialization period | 30 s / 5 min |
| HPA multiple metrics | Takes the **maximum** proposal |
| Default `scaleDown` | `stabilizationWindowSeconds: 300`, **one** policy: `Percent 100` per 15 s |
| Default `scaleUp` | `stabilizationWindowSeconds: 0`, **two** policies: `Pods 4` and `Percent 100` per 15 s, `selectPolicy: Max` |
| Native sidecars (`initContainers` with `restartPolicy: Always`) | beta 1.29, **GA/stable 1.33** |
| Probe defaults | `initialDelaySeconds 0` · `periodSeconds 10` (min 1) · `timeoutSeconds 1` (min 1) · `successThreshold 1` · `failureThreshold 3` |
| Pod default termination grace | **30 s** |
| NodePort range | 30000–32767 |
| RollingUpdate defaults | `maxSurge 25%`, `maxUnavailable 25%` |

### 4.7 AKS — *Microsoft Learn, azure-subscription-service-limits*

| Thing | Value |
|---|---|
| Max nodes per cluster | **5,000** (VMSS + Standard LB) |
| Max nodes per node pool | 1,000 · Max node pools per cluster: 100 |
| Max clusters per subscription | 5,000 |
| Max pods per node, **Azure CNI** | **250 max, 30 default** |
| Max pods per node, **kubenet** | **250 max, 110 default** — but **kubenet retires 31 March 2028**; Azure CNI Overlay is the recommended plugin for new clusters |
| Max load-balanced services per cluster | 300 (Standard LB) |

### 4.8 Azure API Management — *Microsoft Learn, azure-subscription-service-limits*

| Thing | Classic | v2 | Consumption |
|---|---|---|---|
| **Policy document size** | **512 KiB** | 512 KiB | **16 KiB** |
| Cached response size | 2 MiB | 2 MiB | 2 MiB |
| Buffered payload size | 500 MiB | 2 MiB | 2 MiB |
| Request payload size | Unlimited | 1 GiB | 1 GiB |
| `validate-content` body size | **100 KiB** | 100 KiB | 100 KiB |
| Concurrent backend connections per HTTP authority | 2,048 per unit | 2,048 | Unlimited |
| Backend timeout (`forward-request`) | **300 s default**; > 240 s may not be honoured | same | same |

Self-hosted gateways: **Developer 5, Premium 100** (no other tier supports them). API operations: Premium/Premium v2 **75,000**, Standard/Standard v2 50,000, Basic/Basic v2 10,000, Developer/Consumption 3,000. Workspaces per instance: 100.

**Tier currency — do not describe APIM as if it's still 2023.** The **v2 tiers are the modern line**: Basic v2 and Standard v2 (Standard v2 adds outbound VNet integration), and **Premium v2 went GA in November 2025** with a new architecture where VNet *injection* needs no route tables or service endpoints, plus availability zones and custom CA certs. Classic Premium is still the answer for a client already on it; Premium v2 is the answer for greenfield. Consumption remains the 16 KiB-policy serverless tier.

### 4.9 Azure Functions — *Microsoft Learn, functions-scale*

| Thing | Value |
|---|---|
| Plan currency | **Consumption is now the legacy plan** — Flex Consumption is the recommended serverless host, and Linux Consumption retires 30 September 2028. Say "Flex Consumption" for greenfield. |
| Timeout, Consumption | **default 5 min, max 10 min** |
| Timeout, Flex Consumption / Premium / Dedicated / Container Apps | **default 30 min, max unbounded** (Dedicated requires Always On) |
| **HTTP response ceiling** | **230 seconds**, regardless of plan — Azure Load Balancer idle timeout |
| Max request size | 210 MB · Max request URL 8,192 chars · Max query string 4,096 |
| Max instances | Flex 1,000 · Premium Windows 100 / Linux 20–100 · Consumption Windows 200 / Linux 100 |
| Language worker startup timeout | 60 s (not configurable) |
| Scale-in grace period | 60 min (Flex/Premium), 10 min during platform updates |

### 4.10 Azure Logic Apps — *Microsoft Learn, logic-apps-limits-and-config*

| Thing | Consumption | Standard |
|---|---|---|
| Max run duration | **90 days** | Stateful **90 days**, stateless **5 min** |
| Run history retention | 90 days | 90 days |
| **HTTP outbound request timeout** | **120 s** | **225 s** (default) |
| Retry attempts | default **4**, max 90 | default 4 |
| Retry interval | — | default **7 s** |
| Message size | 100 MB | 100 MB |
| Message size per action **with chunking** | 1 GB | 1,073,741,824 bytes (1 GB) |
| Content chunk size | varies per connector | **52,428,800 bytes (52 MB)** |
| For-each array items | 100,000 | stateful 100,000 / stateless 100 |
| For-each concurrency | default **20**, max **50** | same |
| Until loop iterations | default 60, max 5,000 | stateful max 5,000 / stateless 100 |
| Until loop timeout | **PT1H** | stateful PT1H / stateless PT5M |
| Trigger concurrency | default 25, max 100 | default 100, max 100 |
| `splitOn` debatch | 100,000 (concurrency off) / 100 (on) | same |
| XSLT map file | 8 MB | — |

### 4.11 CI/CD platforms — *docs.github.com/actions/reference/limits · learn.microsoft.com azure-devops/pipelines/agents/hosted*

| Thing | Value |
|---|---|
| GitHub Actions — max job time | **6 hours** |
| GitHub Actions — max workflow run time | **35 days** (incl. waiting/approvals) |
| GitHub Actions — max matrix jobs | **256** per workflow run |
| GitHub Actions — `GITHUB_TOKEN` rate limit | **1,000 requests/hour/repository** (15,000 GHEC) |
| GitHub Actions — self-hosted job | max 5 days execution; queued job cancelled after **24 hours** |
| GitHub Actions — concurrent jobs | 20 (Free) → 500 (Enterprise); larger runners 1,000 |
| Azure Pipelines — MS-hosted free tier | 1 parallel job, **60 min per job**, **1,800 min/month**, private projects (org must be linked to a valid Azure subscription; **public projects are retired** — no new ones) |
| Azure Pipelines — paid parallel job | **360 min (6 h)** per job, no monthly cap |
| Azure Pipelines — MS-hosted agent hardware | 2-core, 7 GB RAM, 14 GB SSD, **~10 GB free disk**, Standard_DS2_v2 |

### 4.12 GitOps — *argo-cd.readthedocs.io/faq · fluxcd.io/flux/components/source/gitrepositories*

| Thing | Value |
|---|---|
| Argo CD default reconciliation | **120 s + up to 60 s jitter ≈ 3 minutes** (`timeout.reconciliation`, `timeout.reconciliation.jitter` in `argocd-cm`) |
| Flux `GitRepository.spec.interval` | **Required field**; docs use `5m0s` / `10m0s` |
| Flux `GitRepository.spec.timeout` | default **60s** |

### 4.13 Specs — *rfc-editor.org*

| RFC | What |
|---|---|
| **9457** | Problem Details for HTTP APIs — **obsoletes 7807**; `application/problem+json`, `application/problem+xml`; members `type`, `status`, `title`, `detail`, `instance` |
| 9110 | HTTP Semantics |
| 6749 / 6750 | OAuth 2.0 Framework / Bearer Token Usage |
| 7519 / 7515 / 7517 | JWT / JWS / JWK |
| 7636 | PKCE · 7662 Introspection · 7009 Revocation · 7523 `private_key_jwt` |
| 8414 | AS Metadata · 8705 mTLS-bound tokens · 8693 Token Exchange · 8707 Resource Indicators |
| 9068 | JWT profile for OAuth access tokens · 9126 PAR · 9207 `iss` in the authorization response |
| **9449** | DPoP — Demonstrating Proof of Possession |
| **9700** | Best Current Practice for OAuth 2.0 Security (published January 2025 — this is what "modern OAuth" means) |
| *(no RFC)* | **OAuth 2.1 is still an IETF Internet-Draft** (`draft-ietf-oauth-v2-1`, rev 15, March 2026), not a published standard. It consolidates RFC 6749 + 6750 + the BCP: PKCE mandatory, implicit and ROPC removed, exact redirect-URI matching. Correct line: *"2.1 isn't an RFC yet, but Entra, Okta and Auth0 already behave as if it is, so I design to it."* Calling it "the OAuth 2.1 standard" is the tell. |
| 8594 / 9745 | `Sunset` header / `Deprecation` header |
| 6902 / 7396 | JSON Patch / JSON Merge Patch |
| 6585 | 429 Too Many Requests |

### 4.14 Python

| Thing | Value |
|---|---|
| `ThreadPoolExecutor` default `max_workers` (3.8+) | `min(32, os.cpu_count() + 4)` |
| Free-threaded (no-GIL) CPython | **Optional build** from 3.13 (PEP 703) — not the default interpreter |

---

## 5. Azure → AWS → GCP Mapping

The JD names **AKS/EKS/GKE** and **CloudFormation**, so know all three columns. Lead Azure.

| Capability | **Azure** | **AWS** | **GCP** |
|---|---|---|---|
| Managed Kubernetes | AKS | EKS | GKE |
| Container registry | ACR | ECR | Artifact Registry |
| Serverless functions | Azure Functions | Lambda | Cloud Run functions |
| Serverless containers | Container Apps | App Runner / ECS Fargate | Cloud Run |
| API gateway | **API Management** | API Gateway (+ AWS AppSync for GraphQL) | Apigee / API Gateway |
| Enterprise message broker | **Service Bus** | **Amazon SQS + SNS** (FIFO queues) / Amazon MQ | Pub/Sub |
| Event router | **Event Grid** | **EventBridge** | Eventarc |
| Event stream | **Event Hubs** (Kafka endpoint) | **Kinesis Data Streams** / MSK | Pub/Sub / Managed Kafka |
| Simple queue | Storage Queue | SQS Standard | Pub/Sub |
| Workflow / low-code | **Logic Apps** | **Step Functions** (code-first) | Workflows |
| Durable orchestration | Durable Functions | Step Functions | Workflows |
| ETL / bulk data | Data Factory / Synapse | Glue / DataSync | Dataflow / Data Fusion |
| Secrets | **Key Vault** | Secrets Manager / Parameter Store | Secret Manager |
| Identity | **Entra ID** + managed identity | IAM + IAM roles / IRSA | Cloud IAM + Workload Identity |
| IaC native | **Bicep / ARM** | **CloudFormation / CDK** | **Infrastructure Manager** (Terraform-based) / Config Connector — *Deployment Manager reached end of support 31 March 2026; do not name it* |
| CI/CD native | Azure DevOps / GitHub Actions | CodePipeline + CodeBuild | Cloud Build |
| Observability | Azure Monitor + App Insights + Log Analytics (KQL) | CloudWatch + X-Ray | Cloud Monitoring + Cloud Trace |
| Private networking to PaaS | Private Endpoint / Private Link | VPC Endpoint / PrivateLink | Private Service Connect |
| Hybrid on-prem data gateway | Self-hosted IR (SHIR) / on-prem data gateway | DataSync agent / Direct Connect | — |
| Object storage | Blob Storage | S3 | Cloud Storage |
| Managed Postgres | Azure Database for PostgreSQL | RDS / Aurora | Cloud SQL / AlloyDB |
| CDN / WAF | Front Door + WAF | CloudFront + AWS WAF | Cloud CDN + Cloud Armor |
| Service mesh | **Istio add-on for AKS** (the OSM add-on is end-of-support 30 Sep 2027 and upstream OSM is retired) | **ECS Service Connect / VPC Lattice** — *App Mesh shuts down 30 Sep 2026* | **Cloud Service Mesh** (renamed from Anthos Service Mesh) |

---

## 6. HTTP Status Decision Table

| Situation | Code | Notes |
|---|---|---|
| GET/PUT/PATCH succeeded with a body | **200** | |
| POST created a resource | **201** | Must include `Location` |
| Accepted for async processing | **202** | Include `Location` to a status endpoint. **The long-running-integration answer.** |
| Succeeded, no body | **204** | DELETE, or PUT with no representation |
| Partial content / range | 206 | Rare in integration |
| Resource moved permanently | 301 | |
| Client should use cache | **304** | With `ETag` / `If-None-Match` |
| Temporary redirect preserving method | 307 / 308 | 308 = permanent |
| Malformed JSON / schema violation | **400** | Body = RFC 9457 problem details |
| No credentials, or invalid/expired token | **401** | Must send `WWW-Authenticate` |
| Valid token, insufficient scope/role | **403** | 401 vs 403 is a favourite trap |
| Resource does not exist — **or exists but you may not know it does** | **404** | Use 404 over 403 to avoid enumeration on sensitive resources |
| Wrong verb for this resource | 405 | Must send `Allow` |
| `Accept` header unsatisfiable | 406 | |
| Request timed out waiting on the client | 408 | |
| **Business conflict / optimistic-concurrency failure** | **409** | Duplicate order, version mismatch |
| Resource intentionally removed | 410 | Better than 404 for a retired API version |
| `If-Match` precondition failed | **412** | The correct code for optimistic locking with `ETag` |
| Payload too large | 413 | |
| Unsupported media type | 415 | |
| **Syntactically valid but semantically wrong** | **422** | Well-formed JSON, invalid IBAN. FastAPI/Pydantic default. |
| Resource locked (WebDAV, RFC 4918) | 423 | |
| **Rate limit / quota exceeded** | **429** | Must send `Retry-After` (RFC 6585) |
| Header fields too large | 431 | |
| Unhandled server exception | **500** | Never leak a stack trace |
| Not implemented | 501 | |
| **Upstream returned garbage** | **502** | Gateway/backend contract broken |
| **Dependency down / circuit breaker open / shedding load** | **503** | Send `Retry-After` |
| **Upstream timed out** | **504** | The one APIM returns when your backend blows the timeout |

**The two rules to say out loud:** (1) 4xx means "don't retry the same request unchanged"; 5xx and 429 mean "retry with exponential backoff and jitter". (2) Every non-2xx body should be RFC 9457 `application/problem+json` with a correlation ID in an extension member — that is what makes a support ticket solvable.

---

## 7. Name That Pattern

| Symptom the interviewer describes | Pattern | Implementation on this stack |
|---|---|---|
| "Payload is 5 MB but the queue caps at 256 KB" | **Claim Check** | Write to Blob, put the SAS URI in the message |
| "Legacy backend falls over above 50 rps" | **Queue-Based Load Levelling** | Service Bus queue in front, bounded consumer concurrency |
| "One sick dependency is taking down everything" | **Circuit Breaker** (+ Bulkhead) | APIM backend `circuitBreaker` rule; bounded thread/connection pools |
| "The same order got created twice" | **Idempotent Consumer** | `MessageId` + SB duplicate detection + dedupe table on business key |
| "DB commit succeeded but the event never published" | **Transactional Outbox** | Outbox table in the same tx + polling relay, or Cosmos change feed → Function |
| "Step 4 of 6 failed; steps 1–3 already charged the customer" | **Saga with compensation** | Durable Functions orchestrator with explicit compensating activities |
| "Consumer needs 10 minutes; the HTTP caller waits 30 seconds" | **Async Request-Reply** | `202` + `Location` + status endpoint (Durable Functions gives it free) |
| "One partner sends XML, another JSON, a third fixed-width" | **Anti-Corruption Layer** + Canonical Model | APIM façade + per-partner adapter → one internal canonical schema |
| "Mobile app makes 12 calls to render one screen" | **Gateway Aggregation** / BFF | APIM `send-request` ×N in inbound, merge in outbound |
| "Every service reimplements auth and throttling" | **Gateway Offloading** | Move to APIM policy at the product scope |
| "Salesforce updates SAP updates Salesforce, forever" | **Loop prevention / originator stamping** | Stamp `x-origin-system`, filter it on the return path, plus a watermark |
| "We need to migrate off the monolith without a big bang" | **Strangler Fig** | APIM routes by path; move one operation at a time to the new service |
| "Multiple consumers each need every message" | **Publish-Subscribe** | SB topic + subscriptions with SQL filters, or Event Grid |
| "Ten workers, each message processed once" | **Competing Consumers** | One SB queue, N consumers, `PeekLock` |
| "Order matters for a given customer, not globally" | **Sessions / partition key** | SB `SessionId` = customer ID; Kafka key = customer ID |
| "Poison message loops forever" | **Dead Letter Channel** | `maxDeliveryCount: 10` → DLQ + alert + redrive runbook |
| "Batch of 2M rows must not be one giant transaction" | **Chunking + checkpointing** | Split into messages, checkpoint a watermark, resume from it |
| "Downstream is only available 02:00–04:00" | **Store and Forward** | Queue with long TTL, scheduled consumer, KEDA cron scaler |
| "We must prove which version of the config was live on the 14th" | **GitOps / config as code** | Signed commits in the manifest repo; `git log` is the evidence |
| "Cluster drifted because someone kubectl-ed it" | **Reconciliation loop / self-heal** | Argo CD `selfHeal: true` + remove human write RBAC |
| "New release broke 3% of requests and nobody noticed for an hour" | **Progressive delivery / canary analysis** | Flagger or Argo Rollouts with a `MetricTemplate` + auto-rollback |
| "Two teams keep copying the same 300-line pipeline" | **Golden path / paved road** | Reusable workflow or ADO template + a `platform-` Helm library chart |
| "A tenant's spike starves everyone else" | **Bulkhead / throttling per key** | APIM `rate-limit-by-key` on the subscription key; per-tenant queue |
| "We cannot find where the request went across five hops" | **Distributed tracing / Correlation ID** | W3C `traceparent` propagated APIM → SB `CorrelationId` → AKS OTel |
| "Secrets are in the pipeline as variables" | **Secretless / workload identity** | OIDC federation to Entra; Key Vault + External Secrets in-cluster |
| "The schema changed and 40 consumers broke overnight" | **Schema registry + contract testing** | Event Hubs Schema Registry / AsyncAPI + Pact in the PR gate |

---

## 8. Command Crib

### 8.1 "The pod won't start / won't serve"

```bash
kubectl get pods -n integration -o wide --sort-by=.status.startTime
kubectl describe pod orders-api-7d9f-abcde -n integration          # Events at the bottom = the answer
kubectl logs deploy/orders-api -n integration --previous            # logs of the crashed container
kubectl logs deploy/orders-api -n integration -c istio-proxy --tail=100
kubectl get events -n integration --sort-by=.lastTimestamp | tail -30
kubectl get endpointslices -n integration -l kubernetes.io/service-name=orders-api
kubectl debug -it pod/orders-api-7d9f-abcde -n integration --image=nicolaka/netshoot --target=orders-api
kubectl exec -it deploy/orders-api -n integration -- env | sort
kubectl port-forward -n integration svc/orders-api 8080:80
```

**Read the reason like a table:** `ImagePullBackOff` = registry auth or wrong tag · `CrashLoopBackOff` = app exits, read `--previous` logs · `CreateContainerConfigError` = missing ConfigMap/Secret key · `Pending` = unschedulable, `describe` shows the taint/resource reason · `OOMKilled` = raise the memory limit or fix the leak · `Running` but not `Ready` = readiness probe failing.

### 8.2 "The rollout went wrong"

```bash
kubectl rollout status deploy/orders-api -n integration --timeout=180s
kubectl rollout history deploy/orders-api -n integration
kubectl rollout undo deploy/orders-api -n integration --to-revision=7
kubectl rollout restart deploy/orders-api -n integration            # re-pull secrets/config, no image change
kubectl set image deploy/orders-api orders-api=acrprd.azurecr.io/orders-api:1.4.3 -n integration
kubectl annotate deploy/orders-api -n integration kubernetes.io/change-cause="bump to 1.4.3"  # --record is deprecated; annotate instead
```

### 8.3 "Is it a scaling problem?"

```bash
kubectl get hpa -n integration
kubectl describe hpa orders-api -n integration                      # ScalingActive/AbleToScale conditions
kubectl top pod -n integration --containers
kubectl get scaledobject,scaledjob -n integration                   # KEDA
kubectl get pdb -A                                                  # what's blocking a drain
kubectl drain aks-nodepool1-vmss000003 --ignore-daemonsets --delete-emptydir-data
```

### 8.4 Helm

```bash
helm lint ./charts/integration-service --strict
helm template rel ./charts/integration-service -f values/prod.yaml | kubectl apply --dry-run=server -f -
helm upgrade --install orders-api ./charts/integration-service \
  -n integration -f values/prod.yaml --atomic --wait --timeout 5m
helm history orders-api -n integration
helm rollback orders-api 4 -n integration
helm get values orders-api -n integration --all                     # computed values incl. defaults
helm diff upgrade orders-api ./charts/integration-service -f values/prod.yaml   # helm-diff plugin
helm dependency update ./charts/integration-service
```

`--atomic` implies `--wait` and rolls back automatically on failure. That one flag is the difference between a Helm release and a Helm incident.

### 8.5 Terraform

```bash
terraform init -backend-config=backends/prod.hcl -upgrade
terraform fmt -recursive -check && terraform validate
terraform plan -out=tfplan -var-file=env/prod.tfvars -lock-timeout=5m
terraform show -json tfplan | jq -r '.resource_changes[] | select(.change.actions != ["no-op"]) | "\(.change.actions|join(","))\t\(.address)"'
terraform apply tfplan
terraform plan -detailed-exitcode                                   # exit 0 = no change, 2 = drift
terraform state list && terraform state show azurerm_kubernetes_cluster.aks
terraform state mv azurerm_servicebus_queue.old azurerm_servicebus_queue.orders
terraform force-unlock 3f6a1e9c-0b3d-4a2b-9f10-7c1b2d3e4f56
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
terraform output -raw aks_kubeconfig > ~/.kube/aks
```

### 8.6 Azure CLI

```bash
az aks get-credentials -g rg-int-prd -n aks-int-prd --overwrite-existing
az acr build -r acrintprd -t orders-api:$(git rev-parse --short HEAD) .
az deployment group what-if -g rg-int-prd -f infra/main.bicep -p infra/prod.bicepparam
az servicebus queue show -g rg-int-prd --namespace-name sb-int-prd -n orders \
  --query "{maxDelivery:maxDeliveryCount, lock:lockDuration, dlqOnExpiry:deadLetteringOnMessageExpiration}"
az servicebus queue show -g rg-int-prd --namespace-name sb-int-prd -n orders \
  --query "countDetails"                                            # activeMessageCount + deadLetterMessageCount
az apim api list --service-name apim-int-prd -g rg-int-prd -o table
az monitor app-insights query --app ai-int-prd --analytics-query \
  "requests | where success == false | summarize count() by resultCode, name | order by count_ desc"
az role assignment create --assignee-object-id <mi-object-id> --assignee-principal-type ServicePrincipal \
  --role "Azure Service Bus Data Sender" --scope <queue-resource-id>
```

### 8.7 Argo CD / Flux / git

```bash
argocd app get orders-api-prod --refresh
argocd app diff orders-api-prod
argocd app sync orders-api-prod --prune --dry-run
argocd app history orders-api-prod && argocd app rollback orders-api-prod 12
argocd app set orders-api-prod --sync-policy automated --auto-prune --self-heal

flux get sources git -A
flux get kustomizations -A
flux reconcile kustomization apps --with-source
flux suspend helmrelease orders-api -n integration

git fetch --prune origin
git log --oneline --graph HEAD..origin/main
git pull --rebase --autostash origin main
git revert --no-edit <sha>            # the GitOps rollback: revert the manifest commit
```

---

## 9. Acronym Decoder (95)

**Azure & integration:** **AIS** Azure Integration Services · **APIM** API Management · **AKS** Azure Kubernetes Service · **ACR** Azure Container Registry · **ADF** Azure Data Factory · **ASB** Azure Service Bus · **EG** Event Grid · **EH** Event Hubs · **IR** Integration Runtime · **SHIR** Self-Hosted Integration Runtime · **ASE** App Service Environment · **PE** Private Endpoint · **VNet** Virtual Network · **NSG** Network Security Group · **SAS** Shared Access Signature · **MU** Messaging Unit · **TU/PU/CU** Throughput / Processing / Capacity Unit · **AVM** Azure Verified Modules · **KQL** Kusto Query Language

**Identity & security:** **MI** Managed Identity · **SAMI/UAMI** System-/User-Assigned Managed Identity · **SPN** Service Principal Name · **WIF** Workload Identity Federation · **OIDC** OpenID Connect · **PKCE** Proof Key for Code Exchange · **DPoP** Demonstrating Proof of Possession (RFC 9449) · **JWKS** JSON Web Key Set · **JWT/JWS/JWE/JWA/JWK** the JOSE family · **mTLS** mutual TLS · **OBO** On-Behalf-Of flow · **CIBA** Client-Initiated Backchannel Authentication · **PAR** Pushed Authorization Request · **HSM** Hardware Security Module · **CMK/BYOK** Customer-Managed Key / Bring Your Own Key · **SNI** Server Name Indication · **HSTS** HTTP Strict Transport Security · **CORS** Cross-Origin Resource Sharing · **SSRF** Server-Side Request Forgery · **BOLA/BFLA** Broken Object-/Function-Level Authorization · **IDOR** Insecure Direct Object Reference · **WAF** Web Application Firewall · **CRS** OWASP Core Rule Set · **OPA** Open Policy Agent

**Messaging:** **DLQ** Dead-Letter Queue · **TDLQ** Transfer Dead-Letter Queue · **CQRS** Command Query Responsibility Segregation · **CDC** Change Data Capture · **KRaft** Kafka Raft — the built-in metadata quorum; **the only mode since Kafka 4.0 (Mar 2025), which removed ZooKeeper outright** · **ISR** In-Sync Replicas · **AMQP** Advanced Message Queuing Protocol · **MQTT** Message Queuing Telemetry Transport · **SBMP** Service Bus Messaging Protocol (retiring) · **EOS** Exactly-Once Semantics · **TTL** Time To Live

**Kubernetes & delivery:** **HPA/VPA** Horizontal/Vertical Pod Autoscaler · **CA** Cluster Autoscaler · **KEDA** Kubernetes Event-Driven Autoscaling · **CRD/CR** Custom Resource Definition / Custom Resource · **PDB** Pod Disruption Budget · **CNI** Container Network Interface · **CSI** Container Storage Interface · **RBAC** Role-Based Access Control · **SA** ServiceAccount · **QoS** Quality of Service class (Guaranteed/Burstable/BestEffort) · **VMSS** Virtual Machine Scale Set · **AGIC** Application Gateway Ingress Controller · **ESO** External Secrets Operator · **SOPS** Secrets OPerationS

**Supply chain & observability:** **IaC** Infrastructure as Code · **SAST/DAST/SCA** Static / Dynamic / Software Composition Analysis · **SBOM** Software Bill of Materials · **SLSA** Supply-chain Levels for Software Artifacts · **CVE/CVSS/NVD** vulnerability ID / scoring / database · **OTel** OpenTelemetry · **SLI/SLO/SLA** Indicator / Objective / Agreement · **RPO/RTO** Recovery Point / Time Objective · **MTTR/MTTD** Mean Time To Recover / Detect

**API & legacy:** **REST/SOAP/WSDL/XSD/XSLT** · **MTOM** Message Transmission Optimization Mechanism · **WS-Security** SOAP message-level security · **EDI/X12/EDIFACT/AS2** B2B document standards and transport · **ETL/ELT/EAI/ESB/iPaaS** integration architecture generations · **ACL** Anti-Corruption Layer · **BFF** Backend For Frontend · **MCP** Model Context Protocol · **RAG** Retrieval-Augmented Generation

**Financial services:** **ISO 20022** the XML/JSON financial messaging standard that replaced SWIFT MT on the cross-border leg (CBPR+ coexistence ended 22 Nov 2025) · **SWIFT MT/MX** legacy FIN message types / ISO 20022 XML messages · **CBPR+** Cross-Border Payments and Reporting Plus — the ISO 20022 usage guidelines for the Swift network · **RBI** Reserve Bank of India (payment-data localisation directive, 2018) · **FIX** Financial Information eXchange protocol (trading) · **FpML** Financial products Markup Language (derivatives) · **SEPA** Single Euro Payments Area · **ACH/NEFT/RTGS/UPI/NACH** US / Indian payment rails · **IBAN/BIC/LEI/ISIN** account / bank / legal-entity / security identifiers · **KYC/AML/CDD** Know Your Customer / Anti-Money Laundering / Customer Due Diligence · **PCI DSS** card data security standard · **DORA** EU Digital Operational Resilience Act · **DPDP** India's Digital Personal Data Protection Act, 2023 · **SOX** Sarbanes-Oxley · **SOC 2** service-organisation controls report · **NAV/AUM** Net Asset Value / Assets Under Management · **OMS/EMS** Order / Execution Management System · **T+1** trade date plus one settlement cycle

**EY-internal:** **GDS** Global Delivery Services · **DE** Digital Engineering (the `DE-` requisition prefix) · **SC1/2/3** Senior Consultant sub-grades · **CIS** Candidate Information Sheet · **Mercury** EY's SAP ERP · **EY Canvas** the audit workflow hub with the embedded multiagent framework · **EY Fabric / EY Nexus / EY Badges** internal platform, client solution accelerator, and learning credential programme

---

## 10. Financial Services One-Liners

The JD says EY has "a separate business dedicated exclusively to the financial services marketplace" and names Asset Management, Banking & Capital Markets, Insurance, Private Equity. Expect at least one of these to be dropped casually. One sentence each; do not bluff depth.

| Term | Say this |
|---|---|
| **ISO 20022** | The ISO standard for financial messaging — rich, structured XML (and JSON) with far more remittance data than legacy SWIFT MT. **The CBPR+ MT/MX coexistence period ended 22 November 2025**: cross-border payment instructions on the Swift network are now ISO 20022-native. The next cliff is **14 November 2026**, when fully unstructured postal addresses stop being accepted and non-compliant messages are rejected outright. |
| **SWIFT MT vs MX** | MT is the legacy fixed-field FIN format (MT103 = single customer credit transfer, MT202 = bank-to-bank cover); MX is the ISO 20022 XML equivalent (`pacs.008`, `pacs.009`). **Do not say "banks are running both in parallel" as if it's current** — for CBPR+ that ended in Nov 2025. The honest 2026 line: *"Coexistence closed on the Swift leg, so the translation problem moved inward — the MT↔MX adapter now sits between the ISO-native gateway and the domestic rails and core systems that still speak MT-shaped or proprietary formats. That's exactly the anti-corruption-layer job."* |
| **`pacs` / `pain` / `camt`** | ISO 20022 message families: `pacs` = interbank payments clearing and settlement, `pain` = customer-to-bank payment initiation, `camt` = cash management and statements. |
| **FIX protocol** | The session+application protocol for order flow between buy-side, sell-side and exchanges; tag=value pairs over a persistent session with sequence numbers and gap fill — think "the trading world's AMQP". |
| **T+1 settlement** | Trades settle one business day after execution. **US, Canada and Mexico moved 27–28 May 2024; India is already T+1; the EU, UK and Switzerland move together on 11 October 2027.** It compresses every downstream reconciliation window, which is why batch-to-streaming migrations became urgent in post-trade — and why the 2027 European date is live programme work at every bank right now. Naming that date unprompted is the single cheapest way to sound current in front of an FS panel. |
| **Straight-through processing (STP)** | A transaction that completes end-to-end with zero manual intervention; the STP rate is the KPI your integration platform is judged on. |
| **Reconciliation / breaks** | Comparing two systems' views of the same population and reporting the differences ("breaks"); every batch integration in a bank needs a reconciliation and an exception queue, not just a happy path. |
| **NAV** | Net Asset Value — the per-unit valuation of a fund, struck daily; NAV pipelines are hard-deadline batch jobs where "late" is a regulatory event, not a latency metric. |
| **AUM** | Assets Under Management — the asset-management industry's size metric. |
| **Custodian** | The institution that holds securities on behalf of the owner; a major integration counterparty for any asset manager (positions, corporate actions, settlement instructions). |
| **Corporate actions** | Dividends, splits, mergers — events that change the meaning of a position; notoriously the messiest data-integration domain in capital markets. |
| **KYC / AML / CDD** | Identity verification, transaction monitoring for money laundering, and ongoing due diligence — the reason PII flows in a bank need lineage, retention rules and access logs. |
| **PCI DSS** | The card-data standard; the integration consequence is network segmentation, tokenisation, and never letting a PAN touch a log or a message body you don't control. |
| **DORA** | The EU Digital Operational Resilience Act — in force since 16 Jan 2023 and **applying since 17 January 2025**, so it is a live compliance regime, not an upcoming one. Mandates ICT risk management, incident reporting and **third-party/ICT provider oversight**; the register of information on ICT contractual arrangements went to the ESAs from 30 April 2025. It is why your cloud exit plan and your vendor register are engineering artefacts now. |
| **DPDP Act** | India's Digital Personal Data Protection Act, 2023 — consent, purpose limitation, data-fiduciary obligations, penalties to ₹250 crore. **The DPDP Rules were notified 14 November 2025 with phased compliance over 18 months**, so full obligations land around May 2027. Directly relevant: you would be delivering from India into global clients, and the notice/consent and breach-reporting mechanics become platform requirements (retention clocks, deletion jobs, access logs). |
| **RBI data localisation** | RBI's April 2018 *Storage of Payment System Data* directive: payment system data must be stored **only in India**. Processing abroad is allowed, but the data must be deleted from foreign systems and brought back **within one business day or 24 hours of processing, whichever is earlier**. The architectural consequence is concrete — India-region stamps, no cross-border replication of payment data, and a scheduled repatriate-and-purge job that you must be able to evidence. |
| **Data residency** | The contractual/regulatory requirement that data stay in a jurisdiction; drives paired-region design, regional APIM instances, and the "global routing, regional processing" topology. |
| **Immutable audit trail** | Append-only, tamper-evident record of who changed what, when, and on whose approval — in a platform role that is signed Git commits + environment approvals + Azure Activity Log retention, not a bespoke audit table. |
| **Four-eyes / SoD** | Segregation of Duties: the person who wrote the change cannot be the person who approves it to production. Implemented as branch protection + required reviewers + ADO environment approvals. |
| **RegTech reporting** | Regulator-mandated periodic submissions (e.g. transaction reporting); characterised by hard deadlines, exact schemas, replay requirements and penalties — the textbook case for event sourcing + a replayable stream. |
| **Idempotency in payments** | A duplicate payment is not a bug, it is an incident with money attached; every payment API takes a client-supplied idempotency key and every consumer is idempotent on the end-to-end transaction ID. |
| **Ledger vs balance** | The ledger is the append-only truth; the balance is a projection. Never mutate the balance directly — that is CQRS with a regulator attached. |
| **Market data** | High-volume, low-latency, licence-encumbered price feeds; the integration constraint is usually the vendor's redistribution licence, not the throughput. |

**The sentence that lands with an FS panel:** *"In financial services the interesting requirement is almost never throughput — it's provability. I design so that for any transaction I can answer: what came in, what we did with it, who approved the code that did it, and can I replay it."*

---

## 11. Interviewer Traps

| # | The trap | What most candidates say (**wrong**) | What to say (**right**) |
|---|---|---|---|
| 1 | "You can guarantee exactly-once delivery, right?" | "Yes, Service Bus/Kafka gives exactly-once." | "Exactly-once *delivery* is impossible across a network boundary. I get exactly-once *processing* from at-least-once delivery plus an idempotent consumer. Kafka's EOS is real but only for Kafka-to-Kafka transactions with `read_committed`." |
| 2 | "How do you make the liveness probe robust?" | "Have it check the database so we know the pod is really healthy." | "Liveness must never check an external dependency. A DB blip would restart every pod simultaneously and prevent recovery. Deps go in **readiness**." |
| 3 | "So GitOps means the pipeline runs `kubectl apply`?" | "Yes, our CD stage deploys to the cluster." | "That's push CD, not GitOps. GitOps is a pull agent inside the cluster reconciling against Git continuously — which is what gives you drift auto-heal and keeps cluster credentials out of CI." |
| 4 | "Terraform state — where do you keep it?" | "In the repo" / "locally, we commit it." | "Never in Git — it contains secrets in plaintext. Remote backend in Azure Storage with blob-lease locking, one state per environment, versioning and soft delete on the container." |
| 5 | "Which is faster for our CPU-heavy transformation, threads or asyncio?" | "asyncio, it's the modern way." | "Neither — the GIL means both are single-core for CPU work. That's `ProcessPoolExecutor`, or push the transform out of Python entirely. asyncio wins for I/O, not compute." |
| 6 | "Just put the JWT validation in the microservice." | "Sure, we validate in every service." | "I validate at the edge in APIM **and** in the service — defence in depth. But the platform answer is a shared APIM policy fragment so twenty teams get identical `validate-jwt` semantics instead of twenty subtly different ones." |
| 7 | "Store the API key in a Kubernetes Secret." | "Done — Secrets are encrypted." | "K8s Secrets are **base64, not encrypted**, at rest in etcd unless you enable encryption-at-rest or use a KMS provider. In Azure I use workload identity + Key Vault via External Secrets or the CSI driver, so the credential never becomes a Kubernetes object at all." |
| 8 | "Retry the failed call until it works." | "We retry with exponential backoff." | "Backoff alone still hammers a dead backend. Retry must be paired with a **circuit breaker** and a cap, and it must be restricted to idempotent operations — retrying a non-idempotent POST is how you double-charge a customer." |
| 9 | "Just bump `maxDeliveryCount` to 1000 so nothing dead-letters." | "Good idea, fewer DLQ alerts." | "That converts a fast failure into a slow one — a poison message would loop for hours and block throughput. Keep it at 10, alert on DLQ depth, and build a redrive runbook. The DLQ is a feature, not a failure." |
| 10 | "Which cloud is better?" | Picks one and defends it. | Reframe to constraints first (identity, residency, licensing, skills), *then* differentiate, then close with a reversible decision. EY logged "convince me to adopt AWS" — they are testing structure, not loyalty. |
| 11 | "Canary deployments — how do you decide to promote?" | "We watch Grafana and promote manually." | "Manual promotion is not progressive delivery, it's a slow rollout. The verdict has to be automated: Flagger/Argo Rollouts running an `AnalysisTemplate` against error rate and p99 latency, auto-promote on pass, auto-rollback on fail." |
| 12 | "We need to move a 40 GB nightly file — put it on the queue." | "Chunk it into 256 KB messages." | "Claim check: land the file in Blob, publish a message with the URI and a manifest, then fan out work items per chunk with KEDA scaling the workers off queue depth. The queue carries pointers and control, never bulk payload." |
| 13 | "So banks are still running MT and ISO 20022 side by side?" | "Yes, everyone's mid-migration, that's why you need translation." | "Not on the Swift cross-border leg — **CBPR+ coexistence ended 22 November 2025**, and the next cliff is structured postal addresses on 14 November 2026. The translation problem didn't vanish, it moved inward: the ISO-native gateway now has to face domestic rails and core systems that still speak the old shapes. That's an anti-corruption layer, and it's permanent." |
| 14 | "You'd build this on OAuth 2.1, right?" | "Yes, we're fully OAuth 2.1 compliant." | "OAuth 2.1 is still an Internet-Draft, so 'compliant' isn't a thing you can claim yet. What I'd build to is RFC 9700 — the security BCP — which is where 2.1 gets its content: PKCE on every authorization-code flow, no implicit, no ROPC, exact redirect-URI matching. Entra already behaves that way." |
| 15 | "How much of this have you run in production?" | Vague scope-creep, or a silent implication that all of it. | Draw the line yourself, cleanly: "Production for me is LLM systems integrating enterprise APIs — retries, idempotency keys, rate-limit backoff, tracing. AKS, Terraform and Argo CD I've built and operated at project scale, not as a twenty-team platform. What I'm describing here is how I'd build the paved road, and I'd rather be precise about that than have you find out in week three." **This answer wins points. The bluff loses the offer.** |

---

## 12. 30-Second Whiteboard Versions

### 12.1 The Paved Road (the answer to "what would you build here?")

```text
                     ┌──────────────────────── PLATFORM TEAM OWNS ───────────────────────┐
  App team writes:   │  Reusable CI template   Golden Helm library   Terraform modules    │
    - app code       │  (build/test/SAST/SCA/  (probes, HPA, PDB,    (SB queue, APIM API,  │
    - values.yaml    │   secret/IaC scan/SBOM/  NetworkPolicy,        AKS namespace, MI +   │
    - one 8-line     │   sign/deploy)           OTel sidecar)         RBAC, Key Vault)     │
      workflow ref   │  Shared APIM policy fragments (validate-jwt, rate-limit, problem+json)│
                     └───────────────────────────────────────────────────────────────────┘
                                            │
   PR ──► CI (build + 5 scan gates + SBOM + cosign) ──► push image to ACR
                                            │
                                  bump tag in MANIFEST REPO (PR, 2 approvals, signed)
                                            │
                     Argo CD (in-cluster, pull) reconciles ~every 3 min, selfHeal: true
                                            │
                  Argo Rollouts canary 10% ─► AnalysisTemplate (err rate, p99) ─► promote | abort
                                            │
   Guardrails everywhere: OPA/Gatekeeper admission · Azure Policy · branch protection ·
   env approvals (four-eyes) · everything auditable from the Git log.
```

**Say:** "Two teams copying a 300-line pipeline is the failure mode. My deliverable is that an integration team gets a compliant pipeline, a hardened chart and a self-service Service Bus queue by writing about twenty lines — and cannot opt out of the scan gates."

### 12.2 Batch-via-Streaming (the JD's "Batch Jobs using event streaming")

```text
  SFTP / partner drop / nightly extract
              │
              ▼
   Blob landing zone  ──Event Grid "BlobCreated"──►  Splitter Function
              │                                            │
              │  (payload STAYS in Blob - claim check)      │  emits N work items
              ▼                                            ▼
        manifest.json                            Service Bus queue "batch-work"
     (batch_id, chunk count,                       msg = {batch_id, chunk_uri,
      checksum, watermark)                                seq, idempotency_key}
                                                           │
                                          KEDA ScaledObject on queue depth
                                          (scale 0 ──► 50 workers ──► 0)
                                                           │
                             ┌─────────────────────────────┴───────────────┐
                             ▼                                             ▼
                    idempotent worker                              poison ──► DLQ
                 (upsert on business key)                        (alert + redrive runbook)
                             │
                             ▼
                   completion counter == chunk count
                             │
                             ▼
              reconciliation: counts + checksums + exception report ──► "BatchCompleted" event
```

**Say:** "This replaces cron-and-a-shared-drive with something that has backpressure, per-chunk retry, scale-to-zero cost, and a reconciliation you can hand an auditor. The batch becomes a stream of work items; the payload never enters the broker."

### 12.3 Hybrid Integration Topology (the FS-flavoured system design)

```text
   Partner / SaaS / mobile
            │  HTTPS + OAuth2 client_credentials
            ▼
   Front Door + WAF (OWASP CRS)
            ▼
   APIM (Premium, VNet-injected, multi-region)
     policies: validate-jwt · rate-limit-by-key · quota-by-key · validate-content
               · set-header traceparent · problem+json on error · circuit breaker
            │                                    │
            │ sync (seconds; hard 230 s          │ async (fire-and-forget)
            │  ceiling only if a Function         │
            │  is in the path)                    │
            ▼                                    ▼
   AKS: FastAPI services                Service Bus (Premium, sessions,
   (workload identity → Key Vault,       dedupe 10 min, DLQ, PE-only)
    OTel → App Insights)                          │
            │                                     ├─► Logic App Standard (SAP/Salesforce connectors)
            │                                     ├─► Azure Function (custom transform)
            ▼                                     └─► Event Grid ─► 3 downstream subscribers
   Private Endpoint ──► Key Vault / SQL / Storage
            │
            ▼
   ExpressRoute / SHIR ──► on-prem core banking (SOAP), mainframe (MQ)

   Cross-cutting: one traceparent end-to-end · Azure Monitor + Log Analytics (KQL) ·
   Terraform modules per component · Argo CD for the AKS half · Bicep/Terraform for PaaS ·
   data residency: regional stamps, global Front Door routing, no PII crossing the boundary.
```

---

## 13. Verbal Etiquette & Recovery

**The single most important warning in this pack.** A logged EY candidate was accused of using outside help *because their answers kept improving across follow-ups*, and the interview was ended early. So:

> **Commit to an answer, then refine.** Give your best answer in the first 15 seconds. If you then improve it, say *why* out loud — "actually, let me correct myself: I said X, but if the payload can exceed 256 KB that's wrong, it needs a claim check." Visible reasoning reads as competence. Silent escalating perfection reads as cheating.

**The 3-step recovery for a question you cannot answer:**

1. **Name the boundary honestly, in one sentence.** "I haven't run Flagger in production."
2. **Bridge to the nearest thing you have done.** "I have done canary-style rollouts by percentage-splitting traffic at the gateway and watching error rate before widening — same control loop, done manually."
3. **State how you'd close it, concretely and with a timescale.** "Flagger is a `Canary` CR plus a `MetricTemplate`; I'd have it running against a test service in a day, and I'd want the SLO metrics defined before I automated the verdict."

Never do: a long silence, a bluff, "I've heard of it", or an apology. One sentence of honesty buys more credit than three minutes of hedging.

**Whiteboard / verbal rules:**

| Rule | Why |
|---|---|
| Restate the requirement before you draw anything | Half of "failed" design rounds are answers to the wrong question |
| Ask the six scoping questions, then stop asking | Caller waiting? Volume/shape? Failure contract? Network path? Who operates it? Security model? |
| Draw boxes left-to-right in dataflow order | The panel is following you, not admiring the diagram |
| Say the trade-off before they ask for it | "I'm choosing Service Bus over Event Grid here, and the cost is I now own a consumer and a DLQ" |
| Put numbers on it early | "5,000 msg/s at 2 KB = 10 MB/s — that's 10 TUs on Event Hubs Standard" beats "it'll scale" |
| Never say "it depends" and stop | Say what it depends on, then pick |
| Use their vocabulary | If they say "middleware", say middleware. Correcting terminology loses points you cannot get back |
| Own the mistake fast | "That's wrong — the 230-second ceiling is on Functions HTTP, not the whole plan" |
| When time is short, say the 30-second version and offer depth | "That's the shape — want me to go deeper on the failure handling?" |
| For behaviourals, hit the rubric explicitly | EY scores **relevant experience → action taken → result**. Three sentences of context, five of *your* actions, one with a number in it |
| Never criticise a previous employer or a client | Big-4 panels weight this heavily |
| End every technical answer with a period, not a question mark | Rising intonation reads as uncertainty on a video call |

---

## 14. Rapid Fire — 270 One-Liners

Grouped by source file, **ordered by likelihood on this updated JD**. Everything marked `[EY]` is attributed to a real logged EY interview.

### A. CI/CD, IaC & GitOps — 3 of 9 JD responsibilities · see [05-cicd-iac-and-gitops.md](05-cicd-iac-and-gitops.md)

1. `[EY]` How do you check resources in Terraform? → `state list` / `state show` for inventory, `plan` for change, `plan -refresh-only` for drift.
2. Where does Terraform state live? → Remote backend (Azure Storage container) with blob-lease locking; never in Git.
3. Why one state per environment? → Blast radius and lock contention; a prod apply must never be blocked by a dev apply.
4. `terraform plan -detailed-exitcode` codes? → 0 no changes, 1 error, 2 changes present — the drift-detection pipeline's contract.
5. What is a Terraform module? → A reusable directory of config with inputs/outputs — the unit of the paved road.
6. Module versioning? → Pin `version = "~> 2.1"` from a private registry; never `ref=main`.
7. `count` vs `for_each`? → `for_each` keys resources by a stable map key so removing one doesn't re-index the rest.
8. What is `depends_on` for? → Explicit ordering when Terraform can't infer it from references; a smell if overused.
9. What is a `check` block? → Terraform 1.5+ continuous assertion that reports without blocking apply — platform guardrails.
10. `precondition` vs `postcondition`? → Pre runs before the resource is created; post runs after and can reference `self`.
11. What is `moved`? → A config block to refactor addresses without destroy/recreate.
12. Terraform workspaces — use them for environments? → Generally no; separate state + separate directories is clearer and safer.
13. What is drift? → Reality diverging from state, usually because someone used the portal; fix by removing portal write access.
14. Terraform vs Bicep in one line? → Bicep is a better Azure authoring experience; Terraform is a better platform because of state, plan and modules.
15. What is `az deployment group what-if`? → Bicep/ARM's `plan` equivalent.
16. Bicep is stateless — what does that mean? → Azure Resource Manager *is* the state; there is no state file to lock or corrupt.
17. What is AVM? → Azure Verified Modules — Microsoft-published, tested Bicep/Terraform modules, the closest thing to an official paved road.
18. ARM JSON — when do you write it? → Never by hand; you read it as Bicep's compile output.
19. What is CloudFormation's Terraform equivalent concept? → Stacks and change sets ≈ state and plan; drift detection is built in.
20. What are the five scan gates? → SAST, DAST, SCA, IaC scanning, secret scanning.
21. Where does IaC scanning run? → At the **plan** stage, before apply — Checkov/tfsec/Trivy misconfig on the plan JSON.
22. What is an SBOM? → A machine-readable inventory of everything in your artifact (SPDX or CycloneDX); the JD's compliance hook.
23. What is SLSA? → A supply-chain framework of build-integrity levels — provenance attestation for your artifacts.
24. What is image signing? → `cosign sign` + an admission policy that refuses unsigned images; closes the "who built this" gap.
25. OIDC federation in CI, in one line? → `permissions: id-token: write` plus a federated credential on the app registration — no stored cloud secret.
26. Why is that better than a service principal secret? → Nothing to rotate, nothing to leak, short-lived tokens scoped to a repo+branch.
27. GitHub Actions reuse primitive? → Reusable workflows (`uses: org/repo/.github/workflows/x.yml@v1`) and composite actions.
28. Azure DevOps reuse primitive? → `extends` a pipeline template from a versioned repo resource — plus `templates` for step groups.
29. How do you stop teams bypassing the template? → Required checks on protected branches + ADO "required template" enforcement + policy-as-code.
30. `[EY]` git pull vs git fetch? → Fetch updates remote-tracking refs only; pull = fetch + merge/rebase into your branch.
31. Why enforce linear history? → The Git log becomes the deployment audit trail; merge noise destroys `git bisect` and regulator evidence.
32. What is trunk-based development? → Short-lived branches into one trunk with feature flags; the prerequisite for real CD.
33. Blue-green vs canary in one line each? → Blue-green flips 100% and rolls back instantly; canary shifts a percentage with automated metric analysis.
34. What is GitOps? → Declarative desired state in Git, pulled and continuously reconciled by an in-cluster agent, with drift auto-healed.
35. Argo CD default reconciliation interval? → ~3 minutes (`timeout.reconciliation` 120 s + up to 60 s jitter).
36. Flux's equivalent? → A required `.spec.interval` per object; Git op timeout defaults to `60s`.
37. `selfHeal` — what does it do? → Reverts manual cluster changes back to Git state on the next reconcile.
38. `prune` — what does it do? → Deletes cluster resources that no longer exist in Git; without it, deleted manifests leave orphans.
39. App-of-Apps vs ApplicationSet? → App-of-Apps is a parent Application managing children; ApplicationSet templates Applications from a generator (git dirs, clusters, matrix).
40. Argo `AppProject`? → The multi-tenancy boundary — allowed repos, destinations and resource kinds per team.
41. How do you do secrets in GitOps? → External Secrets Operator or the Key Vault CSI driver with workload identity; SOPS/Sealed Secrets if there's no vault.
42. GitOps rollback? → `git revert` the manifest commit; the agent converges. Never `kubectl edit`.
43. Two repos or one? → App code and manifests in **separate repos**, so a manifest bump doesn't retrigger the whole build pipeline.
44. What promotes dev → prod in GitOps? → A PR that changes an image tag in the next environment's overlay, with approvals — the promotion *is* a PR.
45. Progressive delivery tooling? → Flagger (Flux-side) or Argo Rollouts (Argo-side); both do canary with automated analysis and rollback.
46. GitHub Actions max job time? → 6 hours; max workflow run 35 days; matrix max 256 jobs.
47. Azure Pipelines free tier limits? → 1 parallel job, 60 min per job, 1,800 min/month for private projects; paid jobs run up to 360 min.
48. How do you enforce four-eyes on prod? → Protected branch + required reviewers + ADO/GitHub environment approvals; SoD is an FS control, not a nicety.
49. What's in your "golden pipeline"? → build → unit test → SAST/SCA/secret scan → container build → image scan → SBOM → sign → integration test → IaC plan+scan → deploy → smoke → canary analysis.
50. What breaks the build vs what warns? → CRITICAL/HIGH vulns and any secret finding break; MEDIUM warns with an expiry date on the exception.

### B. Kubernetes, Docker & Helm — now core per the JD · see [04-microservices-containers-kubernetes.md](04-microservices-containers-kubernetes.md)

51. `[EY]` Docker EXPOSE vs publish? → EXPOSE is metadata; `-p host:container` creates the actual mapping; `-P` publishes all EXPOSEd ports randomly.
52. `[EY]` How does HPA work? → `ceil(replicas × current/target)` every 15 s, 10% tolerance, max across metrics; scale-up has no stabilization window (4 pods or 100% per 15 s), scale-down has a 300 s one (then 100% per 15 s).
53. `[EY]` Objects in a Kubernetes Service? → selector, ports (port/targetPort/nodePort), type, clusterIP — and the EndpointSlices the controller creates.
54. Service types? → ClusterIP, NodePort (30000–32767), LoadBalancer, ExternalName, headless (`clusterIP: None`).
55. Endpoints vs EndpointSlice? → EndpointSlice is the scalable replacement; empty slices mean selector/label mismatch.
56. Liveness vs readiness? → Liveness restarts the container; readiness pulls it out of the Service. Never check external deps in liveness.
57. Startup probe? → Gates liveness/readiness for slow-booting apps; set `failureThreshold × periodSeconds` above worst-case boot.
58. Probe defaults? → `initialDelaySeconds 0`, `periodSeconds 10`, `timeoutSeconds 1`, `successThreshold 1`, `failureThreshold 3`.
59. Default pod termination grace? → 30 seconds.
60. What happens on pod delete? → SIGTERM + removal from EndpointSlice concurrently → grace period → SIGKILL. Add a `preStop` sleep to drain.
61. QoS classes? → Guaranteed (requests == limits), Burstable, BestEffort — eviction order is BestEffort first.
62. Requests vs limits? → Requests drive scheduling; limits drive throttling (CPU) and OOMKill (memory).
63. Should you set CPU limits? → Often no — CFS throttling causes latency spikes. Always set memory limits.
64. Deployment vs StatefulSet? → Stable identity, ordered operations and per-pod PVCs vs interchangeable pods.
65. DaemonSet use case? → One pod per node: log shipper, node exporter, CNI, security agent.
66. Job vs CronJob? → Run-to-completion vs scheduled run-to-completion; set `backoffLimit` and `activeDeadlineSeconds`.
67. What is a PDB? → Pod Disruption Budget — the minimum available during *voluntary* disruptions like node drains.
68. RollingUpdate defaults? → `maxSurge 25%`, `maxUnavailable 25%`.
69. How do you roll back? → `kubectl rollout undo deploy/x --to-revision=N`; in GitOps, `git revert`.
70. HPA vs VPA vs CA vs KEDA? → Replicas / pod size / nodes / event-driven replicas with scale-to-zero.
71. Why KEDA for this JD? → It scales integration workers off Service Bus depth, Kafka lag or Event Hub lag — and to zero.
72. Can HPA scale to zero? → No, not without the alpha `HPAScaleToZero` feature gate. KEDA can.
73. Init container vs sidecar? → Init runs to completion before app containers; sidecars run alongside. **Native sidecars** are init containers with `restartPolicy: Always` — beta in 1.29, **GA in 1.33** — and they fixed the old bug where a Job never finished because the mesh sidecar kept running.
74. ConfigMap vs Secret? → Both are key-value; Secrets are **base64, not encrypted** at rest by default.
75. How should secrets really work on AKS? → Workload identity → Key Vault via CSI driver or External Secrets; the credential never becomes a K8s object.
76. What is workload identity on AKS? → A federated ServiceAccount token exchanged for an Entra token — no secrets, no NMI sidecar. It is the **only** supported option now: AAD Pod Identity was deprecated in 2022, archived in 2023, and the managed add-on lost support in September 2025. Never propose pod identity.
77. RBAC objects? → Role/ClusterRole (permissions) + RoleBinding/ClusterRoleBinding (grants) + ServiceAccount (identity).
78. NetworkPolicy default? → Without one, all pod-to-pod traffic is allowed; a default-deny policy per namespace is the baseline control.
79. Taints vs tolerations vs affinity? → Taints repel from a node, tolerations allow, affinity attracts.
80. `topologySpreadConstraints`? → Spread replicas across zones/nodes to survive a zone failure.
81. Ingress vs Gateway API? → Ingress is annotation-driven L7; Gateway API is role-split CRDs (GatewayClass/Gateway/HTTPRoute) — the platform-team answer.
82. AKS max pods per node? → Azure CNI 250 max / 30 default; kubenet 250 max / 110 default.
83. AKS max nodes per cluster? → 5,000 with VMSS + Standard LB.
84. What is AGIC? → Application Gateway Ingress Controller — Azure's L7 + WAF as your Ingress.
85. Multi-stage Dockerfile — why? → Build deps stay out of the runtime image: smaller surface, fewer CVEs, faster pulls.
86. Distroless / non-root — why? → No shell to exploit; `USER 1000` + `readOnlyRootFilesystem: true` + drop all capabilities.
87. Why does `.dockerignore` matter? → It keeps `.git`, `.env` and `node_modules` out of the build context and out of the image.
88. Docker layer caching rule? → Copy the dependency manifest and install *before* copying source, so code changes don't bust the dependency layer.
89. PID 1 problem? → Shell-form `CMD` makes the shell PID 1 and swallows SIGTERM; use exec form or `tini`.
90. `docker run --rm -it` vs `-d`? → Foreground+cleanup vs detached; `--rm` is the reason your debug container disappeared.
91. Image tag strategy? → Immutable tags — git SHA or semver; **never** deploy `:latest`.
92. Where do image digests matter? → Pin by `@sha256:` in production manifests so a re-pushed tag can't silently change what's running.
93. Helm chart anatomy? → `Chart.yaml`, `values.yaml`, `templates/`, `charts/` (deps), `_helpers.tpl`.
94. Helm library chart? → A chart of reusable named templates other charts import — the golden-path mechanism for probes/labels/policies.
95. `helm upgrade --atomic` — why always? → Implies `--wait` and auto-rolls-back a failed release.
96. `helm template | kubectl apply --dry-run=server` — why? → Server-side validation against real CRDs and admission webhooks, without a release.
97. Helm rollback? → `helm rollback <release> <revision>`; `helm history` shows what's available.
98. Where are Helm release records stored? → As Secrets in the release namespace (Helm 3 — no Tiller).
99. Helm vs Kustomize? → Helm templates and packages with values; Kustomize patches plain YAML with overlays. Argo/Flux support both.
100. How do Argo CD and Helm interact? → Argo renders with `helm template` by default, so there is no Helm release history — use `HelmRelease` in Flux if you want it.
101. `kubectl get events --sort-by=.lastTimestamp` — why is this the first command? → Events explain scheduling, image pull, probe and OOM failures in one place.
102. Pod stuck `Pending` — first check? → `kubectl describe pod` — insufficient resources, unsatisfiable affinity, or a taint.
103. `CrashLoopBackOff` — first command? → `kubectl logs <pod> --previous`.
104. `ImagePullBackOff` — first check? → Tag exists? ACR attached to AKS or an imagePullSecret present?
105. Service returns connection refused — first check? → `kubectl get endpointslices` — if empty, the selector doesn't match pod labels.
106. What is a CRD? → A custom API type; the extension mechanism behind KEDA, Argo, Flagger, cert-manager and Gateway API.
107. What is an operator? → A CRD + a controller encoding operational knowledge as a reconcile loop.
108. What is admission control? → Validating/mutating webhooks; OPA Gatekeeper or Kyverno enforce policy at admission — the platform guardrail.
109. Microservice sizing rule? → One service per bounded context and one team; not one service per table.
110. Why is a shared database an anti-pattern? → It couples deployment and schema across teams; the interesting failure is a migration nobody coordinated.

### C. Messaging & Event Streaming — see [03-messaging-and-event-streaming.md](03-messaging-and-event-streaming.md)

111. Service Bus vs Event Grid vs Event Hubs? → Broker for commands / router for reactive events / stream for telemetry with replay.
112. Service Bus max message size? → 256 KB Standard; up to 100 MB Premium over AMQP.
113. What if the payload is bigger? → Claim check: Blob + a URI in the message.
114. Default lock duration? → 1 minute; maximum 5 minutes; renew with `RenewMessageLock`.
115. Default MaxDeliveryCount? → 10, then the message goes to the DLQ with `MaxDeliveryCountExceeded`.
116. Reasons Service Bus dead-letters? → `MaxDeliveryCountExceeded`, `TTLExpiredException`, `HeaderSizeExceeded`, `Session ID is null`, `MaxTransferHopCountExceeded`.
117. DLQ path? → `<queue>/$deadletterqueue`; the transfer DLQ is `<queue>/$Transfer/$DeadLetterQueue`.
118. Duplicate detection window? → Default 10 minutes, min 20 seconds, max 7 days, keyed on `MessageId`.
119. PeekLock vs ReceiveAndDelete? → At-least-once vs at-most-once.
120. How do you get FIFO in Service Bus? → Sessions — set `SessionId`, and a session locks to one consumer.
121. Sessions vs partitions — the trade-off? → Ordering costs you parallelism; partition by the narrowest key that preserves the business order.
122. Topic filter types? → SQL filters (2,000/topic), correlation filters (100,000/topic — cheaper), boolean true/false.
123. Subscriptions per topic? → 2,000.
124. What is auto-forward? → Chain entities server-side; max 4 hops before `MaxTransferHopCountExceeded`.
125. Scheduled messages? → `ScheduledEnqueueTime` — the broker-native delay/retry mechanism.
126. Service Bus transactions? → Send/complete atomically within one namespace; `via` entity for send-and-complete.
127. Event Grid max event size? → 1 MB; billed in 64 KB chunks.
128. Event Grid retry policy? → Exponential backoff to the endpoint with configurable max attempts and TTL, then dead-letter to Blob.
129. CloudEvents vs Event Grid schema? → CloudEvents 1.0 is the CNCF standard; use it for portability.
130. Event Grid subscriptions per topic? → 500.
131. Event Hubs partitions? → 32 on Basic/Standard (fixed at creation on those tiers), up to 1,024 Dedicated.
132. Event Hubs retention? → 1 day Basic, 7 days Standard, 90 days Premium/Dedicated.
133. Event Hubs throughput unit? → Ingress 1 MB/s or 1,000 events/s; egress 2 MB/s or 4,096 events/s; max 40 TUs.
134. What is Event Hubs Capture? → Automatic Avro landing to Blob/Data Lake — the batch bridge for a stream.
135. Event Hubs Kafka endpoint? → Speak Kafka protocol to Event Hubs with a connection-string change — the migration story.
136. Kafka default `message.max.bytes`? → 1048588.
137. Kafka default retention? → `log.retention.hours = 168` (7 days).
138. Kafka `acks` values? → `0` fire-and-forget, `1` leader only, `all` all in-sync replicas.
139. Production durability setting? → `acks=all` + `min.insync.replicas=2` with RF=3 — survives one broker loss without silent data loss.
140. Kafka default `min.insync.replicas`? → 1 — which is why you must change it.
141. What is ISR? → In-Sync Replicas; a replica falls out after `replica.lag.time.max.ms` (default 30000).
142. What is KRaft? → Kafka's built-in Raft metadata quorum. **Kafka 4.0 (March 2025) removed ZooKeeper entirely**, so KRaft is not "the new option", it is the only mode; ZooKeeper clusters migrate via the 3.9 bridge release.
143. Consumer group rebalance? → Partitions are reassigned when membership changes; use cooperative sticky assignment to avoid stop-the-world.
144. Kafka offset commit — auto or manual? → Manual, after processing, or you get at-most-once silently.
145. Log compaction? → Retains the latest value per key forever — the changelog/state-store pattern.
146. Kafka vs Service Bus in one line? → Kafka is a replayable log you position into; Service Bus is a broker that hands you a message and takes it back.
147. RabbitMQ exchange types? → direct, topic, fanout, headers.
148. When RabbitMQ over Service Bus? → On-prem, complex routing topologies, or an existing AMQP 0-9-1 estate.
149. Storage Queue max message? → 64 KB; TTL default 7 days, `-1` for never expires.
150. When is Storage Queue the right answer? → Cheap, simple, high-volume, no ordering/DLQ/dedupe needs, and you already have the storage account.
151. At-least-once + idempotent consumer = ? → Effectively-once processing. Say it exactly that way.
152. How do you make a consumer idempotent? → Upsert on a business key, or a dedupe table on `idempotency_key` with a TTL.
153. Outbox pattern? → Write the message to a table in the same transaction as the state change; a relay publishes it.
154. Poison message handling? → Bounded retries → DLQ → alert on depth → documented redrive runbook with an owner.
155. Backpressure? → Bound consumer concurrency and prefetch so the queue absorbs the spike instead of the backend.
156. What is prefetch and its danger? → Client-side buffering for throughput; too high and messages' locks expire while queued in memory.
157. Competing consumers vs pub/sub? → One message to one of N consumers vs one message to every subscriber.
158. How do you order across partitions? → You don't. Order within a partition/session and design the consumer to tolerate cross-key reordering.
159. What is a schema registry? → Central versioned schemas with compatibility rules; Event Hubs has one, and it's the fix for "40 consumers broke overnight".
160. AsyncAPI? → OpenAPI's equivalent for event-driven contracts; publish it alongside the OpenAPI spec.

### D. API Design — REST, SOAP, GraphQL, OpenAPI · see [01-api-design-rest-soap-graphql-openapi.md](01-api-design-rest-soap-graphql-openapi.md)

161. What makes an API RESTful? → Resources as nouns, HTTP verbs with their real semantics, statelessness, and representations with proper media types.
162. Richardson Maturity Model levels? → 0 one URI/one verb, 1 resources, 2 verbs + status codes, 3 hypermedia.
163. PUT vs PATCH vs POST? → Full replace (idempotent) / partial update / create-or-process (not idempotent).
164. Which methods are idempotent? → GET, HEAD, PUT, DELETE, OPTIONS, TRACE. Not POST, not PATCH.
165. Safe vs idempotent? → Safe = no side effect at all (GET); idempotent = same effect however many times.
166. How do you make POST idempotent? → Client-supplied `Idempotency-Key` header + server-side dedupe store with a TTL and the stored response.
167. Optimistic concurrency in HTTP? → `ETag` + `If-Match`, returning **412** on mismatch.
168. Pagination styles? → Offset/limit (simple, drifts under writes) vs cursor/keyset (stable, scalable). Use cursor for anything large.
169. Versioning options? → URI path `/v2`, query `?api-version=`, custom header, or media type. Path is the most operable.
170. When must you version? → Removing/renaming a field, tightening validation, changing types or semantics. Adding an optional field is not breaking.
171. How do you deprecate? → `Deprecation` (RFC 9745) + `Sunset` (RFC 8594) headers + docs + consumer telemetry + a comms plan.
172. RFC 9457? → Problem Details for HTTP APIs; obsoletes 7807; `application/problem+json`; `type/status/title/detail/instance`.
173. 401 vs 403? → Not authenticated vs authenticated but not permitted.
174. 400 vs 422? → Malformed syntax vs syntactically valid but semantically invalid.
175. 502 vs 503 vs 504? → Bad upstream response / dependency unavailable or shedding / upstream timeout.
176. What must accompany a 429? → `Retry-After`, and ideally `RateLimit-*` headers.
177. Long-running operation pattern? → `202 Accepted` + `Location` to a status resource + a terminal result URL.
178. HATEOAS — do you use it? → Rarely in enterprise integration; know it exists and that Level 3 is the theoretical top of the RMM.
179. What is OpenAPI? → The machine-readable REST contract; drives codegen, mock servers, APIM import and contract tests.
180. Design-first vs code-first? → Design-first for partner APIs (the contract is negotiated); code-first is acceptable internally with spec generation from FastAPI.
181. How do you enforce API standards at scale? → Spectral lint rules in the PR gate + a shared style guide + shared APIM policy fragments.
182. What is SOAP? → XML messaging with an envelope/header/body, described by WSDL, typically over HTTP POST with a `SOAPAction`.
183. SOAP fault structure? → `faultcode`, `faultstring`, `faultactor`, `detail` (SOAP 1.1); `Code`/`Reason`/`Detail` in 1.2.
184. What is WS-Security? → Message-level security — signed/encrypted SOAP elements and a `UsernameToken`/X.509 token, independent of TLS.
185. Why does message-level security still matter? → It survives intermediaries; TLS only protects a hop.
186. How do you expose SOAP as REST? → APIM import the WSDL as "SOAP to REST", then `xml-to-json`, `set-body` templating and `rewrite-uri` — an Anti-Corruption Layer.
187. SOAP pass-through vs SOAP-to-REST in APIM? → Pass-through proxies the envelope; SOAP-to-REST generates a REST surface over the operations.
188. What is MTOM? → Binary attachments in SOAP without base64 bloat.
189. WSDL 1.1 core elements? → `types`, `message`, `portType`, `binding`, `service`.
190. GraphQL — one advantage and one cost? → Clients fetch exactly what they need; you lose HTTP caching and easy rate limiting.
191. N+1 in GraphQL? → Nested resolvers issuing per-item queries; fix with DataLoader batching.
192. How do you rate-limit GraphQL? → Query cost/complexity analysis and depth limits, not request counts.
193. gRPC — when? → Internal service-to-service where latency and a strict contract matter; needs gRPC-Web for browsers.
194. What is a canonical data model? → One internal schema all adapters map to and from; prevents N² point-to-point mappings.
195. What is an adapter/connector in this JD's language? → The per-system translation layer between the external contract and the canonical model.
196. What is content negotiation? → `Accept`/`Content-Type`; support both JSON and XML on a partner-facing API in FS and you will use it.
197. Bulk operations? → A batch endpoint returning per-item results with `207`-style semantics, or async with a job resource.
198. Webhooks — what do you owe the consumer? → Signed payloads (HMAC), timestamp + replay window, retries with backoff, and a redelivery API.
199. CORS — what is actually happening? → A browser preflight `OPTIONS` and response headers; it is a browser policy, not server security.
200. HTTP/2 vs HTTP/1.1 for APIs? → Multiplexing removes head-of-line blocking at the HTTP layer; matters most for gRPC and chatty clients.

### E. Azure Integration Services & APIM · see [02-azure-integration-services.md](02-azure-integration-services.md)

201. What is AIS? → APIM + Logic Apps + Service Bus + Event Grid + Functions — the composable ESB.
202. APIM object model? → APIs → Operations; Products → Subscriptions; Backends; Named values; Policies; Certificates; Loggers.
203. APIM policy scopes and order? → Global → Product → API → Operation, with `<base />` controlling where the parent runs.
204. Policy sections? → `inbound`, `backend`, `outbound`, `on-error`.
205. Policy document size limit? → 512 KiB (16 KiB on Consumption).
206. `rate-limit` vs `quota`? → Short-window burst control vs long-window volume entitlement.
207. `rate-limit` vs `rate-limit-by-key`? → Per subscription vs per arbitrary expression (IP, JWT `sub`, tenant header).
208. `validate-jwt` — what does it check? → Signature via OpenID config/JWKS, `iss`, `aud`, `exp`, and required claims.
209. `validate-content` limit? → 100 KiB request/response body.
210. What is a named value? → Reusable config/secret, optionally a Key Vault reference, used as `{{name}}`.
211. APIM revisions vs versions? → Invisible non-breaking change vs consumer-visible breaking change.
212. APIM self-hosted gateway? → A container running the gateway next to on-prem/other-cloud backends, managed from the Azure control plane.
213. APIM tiers to know? → Two lines now: **classic** — Consumption (serverless, 16 KiB policies), Developer (no SLA, 5 self-hosted gateways), Basic/Standard, Premium (VNet injection, multi-region, 100 self-hosted gateways); and the **v2** line — Basic v2, Standard v2 (outbound VNet integration), and **Premium v2, GA November 2025** (VNet injection with no route tables or service endpoints, availability zones, custom CA certs). Greenfield goes v2; classic Premium stays where a client already runs it.
214. How does APIM reach a private backend? → VNet injection (Premium) or Private Link to the backend; plus Private Endpoint for inbound.
215. APIM circuit breaker? → A `circuitBreaker` rule on the Backend entity with failure thresholds and a trip duration.
216. Logic Apps Consumption vs Standard? → Multi-tenant pay-per-action vs single-tenant on App Service with built-in connectors, VNet and local dev.
217. Logic Apps max run duration? → 90 days (Consumption and Standard stateful); stateless defaults to 5 minutes.
218. Logic Apps HTTP timeout? → 120 s outbound on Consumption, 225 s on Standard.
219. Logic Apps default retry policy? → 4 attempts (exponential by default); configurable to fixed/none, max 90 on Consumption.
220. Logic Apps for-each concurrency? → Default 20, max 50.
221. What is `splitOn`? → Debatching an array trigger into one run per item — up to 100,000 with concurrency off.
222. Azure Functions HTTP ceiling? → 230 seconds, from the Azure Load Balancer idle timeout, regardless of plan. **This is a Functions/App Service limit, not an APIM one** — APIM's `forward-request` defaults to 300 s.
223. Functions Consumption timeout? → Default 5 min, max 10 min — and note Consumption is now the *legacy* plan; Flex Consumption (30 min default, unbounded max) is the current serverless answer.
224. Durable Functions patterns? → Function chaining, fan-out/fan-in, async HTTP API, monitor, human interaction, aggregator.
225. Why is a Durable orchestrator deterministic? → It replays history; non-deterministic code (`datetime.now`, random, direct I/O) corrupts replay.
226. When ADF over Logic Apps? → Bulk rows on a schedule, schema drift, staged copy, SSIS lift-and-shift.
227. What is SHIR? → Self-Hosted Integration Runtime — the on-prem agent ADF uses to reach private data sources.
228. Managed identity — system vs user-assigned? → Dies with the resource vs independent, shareable, survives redeploys. Platform default is user-assigned.
229. How does a Function authenticate to Service Bus without a connection string? → Managed identity + the `Azure Service Bus Data Sender/Receiver` RBAC role.
230. What is Azure Front Door's job here? → Global HTTP entry, WAF with OWASP CRS, and routing to regional APIM stamps.
231. Where do you correlate a trace end-to-end? → W3C `traceparent` from APIM → Service Bus `CorrelationId`/app property → OTel in AKS → App Insights.
232. What is KQL used for? → Querying Log Analytics/App Insights — the failure-triage language on Azure.
233. Logic Apps vs Power Automate? → Same engine lineage; Logic Apps is the IT-owned, IaC-deployable, VNet-capable one. Never propose Power Automate for a production integration.
234. MuleSoft/Boomi — what do you say? → "Haven't used them; I've built the same patterns — canonical model, connectors, DLQ, retry — in AIS and in code. The concepts port; the DataWeave syntax is a week."

### F. Auth & Security · see [06-auth-and-security.md](06-auth-and-security.md)

235. Default grant for service-to-service? → `client_credentials`.
236. Default grant for a user-facing app? → `authorization_code` + PKCE (RFC 7636). RFC 9700 requires PKCE for **all** authorization-code clients, not just public ones.
237. Grants that are dead? → Implicit (SHOULD NOT) and ROPC (MUST NOT), per RFC 9700.
237a. Is OAuth 2.1 out? → **Not yet — it is still an Internet-Draft** (`draft-ietf-oauth-v2-1`, rev 15, March 2026). It folds RFC 6749 + 6750 + the security BCP together: PKCE mandatory, implicit and ROPC gone, exact redirect-URI matching, no bearer tokens in query strings. Design to it, but never call it a published standard.
238. id_token vs access_token? → For the client vs for the API. An API accepting an id_token is a security finding.
239. JWT validation checklist? → Signature via JWKS, `iss`, `aud`, `exp`/`nbf` with clock skew, `alg` allow-list, and required scopes/roles.
240. The `alg: none` attack? → Never trust the header's algorithm; pin the expected algorithm server-side.
241. Scopes vs roles in Entra? → `scp` = delegated (user present); `roles` = application permissions (daemon).
242. What is mTLS and where do you use it? → Both sides present certs; APIM→backend, partner→gateway in FS, and inside a mesh.
243. What is DPoP (RFC 9449)? → Sender-constrained tokens via a per-request proof JWT — a stolen bearer token becomes useless.
244. API key vs OAuth? → A key identifies the *caller application* for metering; OAuth authorises an action. Keys are not an authorisation model.
245. Where do you terminate TLS? → At the edge (Front Door/APIM), then re-encrypt to the backend; never terminate and go plaintext inside a bank's network.
246. OWASP API Top 10 headline risk? → BOLA — object-level authorisation, i.e. "can *this* caller see *this* order", which no gateway can check for you.
247. Key Vault vs app settings? → Vault for anything secret, with references from the app, RBAC, soft-delete, purge protection, and access logs.
248. How do you rotate a secret with zero downtime? → Dual-key: provision the new one, roll consumers, revoke the old — the same shape as APIM's primary/secondary subscription keys.
249. What is Zero Trust in an integration context? → Every hop authenticates and authorises; network position grants nothing; least privilege per identity.
250. Data residency in design? → Regional stamps with regional data stores, global routing only for control plane, and an explicit list of what may cross a border.

### G. Python, System Design, GenAI & Behavioural

251. `[EY]` async vs await? → `async` declares a coroutine; `await` suspends it and yields to the event loop.
252. `[EY]` Thread pool? → Bounded pre-created workers on a shared queue; `ThreadPoolExecutor` defaults to `min(32, cpu_count+4)`.
253. `[EY]` Multithreading vs multiprocessing? → Threads share memory and the GIL (I/O-bound); processes get real parallelism (CPU-bound).
254. `[EY]` MRO? → C3 linearisation of the inheritance graph; what `super()` walks.
255. `[EY]` classmethod vs staticmethod? → Gets `cls` (alternative constructors, inheritance-aware) vs gets nothing (pure helper).
256. `[EY]` Second-highest salary? → `DENSE_RANK() OVER (ORDER BY salary DESC)` filtered to `rnk = 2`; state the tie semantics first.
257. `[EY]` Frequency of elements in an array? → `collections.Counter(arr)` — then say the manual dict version if they want to see the loop.
258. `[EY]` Cosine similarity? → The cosine of the angle between two vectors, `dot(a,b)/(||a||·||b||)`; magnitude-independent, which is why it beats Euclidean for embeddings.
259. `[EY]` Transformer architecture? → Self-attention over the whole sequence in parallel plus positional encodings, replacing recurrence — encoder/decoder stacks with multi-head attention and feed-forward blocks.
260. `[EY]` Convince me to adopt AWS/Azure? → Constraints first (identity, residency, licensing, skills), then differentiators, then a reversible decision. Structure is what's being scored.
261. Pydantic's role in integration? → Schema validation at the boundary — the code equivalent of `validate-content`, and the reason FastAPI returns 422.
262. FastAPI `Depends` — what is it really? → Middleware/DI; the in-code twin of an APIM policy.
263. `asyncio.gather` vs a for-loop of `await`? → Concurrent vs sequential — the single most common async bug.
264. How do you test an integration flow? → Contract tests against the OpenAPI/AsyncAPI, plus testcontainers for a real broker, plus a WireMock/`respx` double for the partner.
265. What is the 35-minute design shape? → Clarify → constraints → happy path → failure modes → scale numbers → security → observability → operations → trade-offs → what I'd do first.
266. Opening sentence of a design answer? → "Before I draw anything: is the caller waiting, what's the volume and shape, and what's the failure contract?"
267. Your GenAI reframe? → "An agent platform is an integration platform — tool calling is API invocation, an MCP server is a gateway for models, RAG ingestion is an ETL pipeline."
268. When do you deploy the GenAI story? → Once, in L2, on "where do you see this role going" — never as your L1 opener.
269. Why EY, in one line? → "In May 2026 EY and Microsoft committed a billion dollars over five years to scaling enterprise AI, and EY embedded a multi-agent framework — on Azure, Microsoft Foundry and Fabric — into Canvas, across 130,000 Assurance people and 160,000 audit engagements. That's the intersection of what I've built and where the platform work is." (Verified figures. Say them exactly; do not inflate them.)
270. What is EY's STAR rubric? → Relevant experience, action taken, result. Three elements, scored explicitly. See [09-behavioral-ey-and-hr.md](09-behavioral-ey-and-hr.md).

---

**Last thing before you dial in:** you have shipped production LLM systems that call enterprise APIs under rate limits, with retries, idempotency and observability. That *is* the job in this JD, with different nouns. Lead with the paved road, commit to your first answer, and put a number on everything you can.

Files: [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md) · [01](01-api-design-rest-soap-graphql-openapi.md) · [02](02-azure-integration-services.md) · [03](03-messaging-and-event-streaming.md) · [04](04-microservices-containers-kubernetes.md) · [05](05-cicd-iac-and-gitops.md) · [06](06-auth-and-security.md) · [07](07-python-for-integration-and-coding-round.md) · [08](08-system-design-integration.md) · [09](09-behavioral-ey-and-hr.md) · [10](10-genai-to-integration-bridge.md)
