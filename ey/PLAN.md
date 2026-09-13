# EY GDS — Integration Platform Engineer (Digital Engineering) — Battle Plan

**Role:** Integration Platform Engineer, **4–8 years**, EY **Digital Engineering (DE)**, Global Delivery Services.
**Industry context:** Financial Services first — Asset Management, Banking & Capital Markets, Insurance, Private Equity; also Health, Government, Power & Utilities.
**Format:** one day, two rounds (L1 technical → L2 techno-managerial), HR/offer if selected.
**Budget:** 4 days × 2 hrs = **8 hours.** Updated 25 Aug 2026 against the revised JD.

> **This plan was revised after the JD changed.** The earlier version treated GitOps and Kubernetes as skippable good-to-haves. The revised JD names both as explicit responsibilities. That reversal is reflected below — Day 2 is now a full DevOps day.

---

## 1. Decoding the JD

The title says *Platform Engineer*, not developer. That is the single most useful word in the document. A platform engineer builds the **paved road** — the pipeline template every team extends, the golden Helm chart, the shared Terraform module, the APIM policy fragment the security team owns. Frame every answer that way. "I wrote a pipeline for my service" is a developer answer. "I wrote the template that twelve services extend, with the scanning gates baked in so teams can't skip them" is a platform answer. Same work, different altitude, and the altitude is what's being graded.

### The nine responsibilities, weighted

| # | Responsibility | Weight |
|---|---|---|
| 5 | CI/CD pipelines with automated testing, **security scanning**, release management | ⭐⭐⭐ |
| 6 | Provision cloud infra using **IaC** (Terraform, Bicep, ARM, CloudFormation) | ⭐⭐⭐ |
| 7 | Containerize + deploy on **Kubernetes** (AKS/EKS/GKE) with **Helm** and **GitOps** (ArgoCD/Flux) | ⭐⭐⭐ |
| 1 | REST/SOAP APIs, message queues, **event-driven architectures** | ⭐⭐⭐ |
| 4 | **Batch jobs** using event streaming + async messaging (Kafka, Service Bus, Event Grid, RabbitMQ) | ⭐⭐⭐ |
| 3 | Build and manage **API gateways** — auth, throttling, versioning, monitoring | ⭐⭐ |
| 2 | Microservices, **connectors and adapters** for SaaS, ERP, CRM, legacy | ⭐⭐ |
| 8 | Security, performance, **observability**, **compliance** | ⭐⭐ |
| 9 | Troubleshoot, optimize, **document** flows, contracts, pipelines, **operational runbooks** | ⭐ |

**Three of the nine responsibilities are CI/CD, IaC and GitOps.** That block is now the heaviest thing in the JD — heavier than APIM, heavier than Logic Apps, heavier than anything in Azure Integration Services, which the JD demotes to good-to-have.

### Signals worth reading

- **"Integration Platform Engineer"** + **"DE-"** prefix → this almost certainly maps to the live requisition **"DE-Cloud Integration Platform Engineer-GDSN02"**, Req **1724333**, Bengaluru, 4–8 yrs, found on careers.ey.com in Aug 2026. Worth confirming with the recruiter — and worth knowing the Chennai req **1734008** is a *different* role (IBM App Connect Enterprise + MuleSoft/Boomi). Ask which one you're interviewing for; the stacks barely overlap.
- **"AKS/EKS/GKE"** and **CloudFormation** in the IaC list → don't assume Azure-only. Lead Azure (EY is a Microsoft shop with a $1B Microsoft AI alliance), but have the AWS mapping ready.
- **"Implement Batch Jobs using event streaming and asynchronous messaging"** — awkwardly worded, and most candidates skim past it. It means bulk/batch workloads driven through async messaging instead of cron-and-a-file-share. It has its own section in [03](03-messaging-and-event-streaming.md) because it's a distinctive ask.
- **"security scanning"** named explicitly inside the CI/CD responsibility → expect a real question. SAST vs DAST vs SCA vs IaC scanning vs secret scanning, and what you gate the build on versus what you only report.
- **"operational runbooks"** and **"document"** → they're hiring someone who will be on the hook when it breaks at 3am. Answer operability questions like someone who has carried a pager.
- **Financial services** → compliance, auditability, data residency, separation of duties. See [12](12-financial-services-integration.md).

---

## 2. What you're walking into

Sourced from 939 EY GDS interview reports on AmbitionBox (updated 24–25 Aug 2026), EY's own careers pages, GfG/Blind writeups, and live careers.ey.com requisitions queried 25 Aug 2026.

| Fact | Number | Source quality |
|---|---|---|
| Round structure, GDS lateral tech | **L1 technical → L2 techno-managerial → HR**. No partner round in any GDS lateral tech report. | Sourced |
| Difficulty (853 EY GDS reports) | Easy 19% / **Moderate 73%** / Hard 8% | Sourced |
| Interview → offer | **<2 weeks 57%**, 2–4 weeks 27% | Sourced |
| Coding round | **Inconsistent.** ~Half of senior reports have none. When present: HackerRank easy/medium. | Sourced |
| Platform | HackerRank. No Codility. No aptitude/OA for laterals. | Sourced |
| Grade for 6 yrs | **Rank 42 = Senior / Senior Consultant** | Forum-sourced |
| Post-round | "Candidate Information Sheet" (CIS) email + MyEY + Aadhaar/payslips/UAN. **CIS ≠ offer.** | Sourced |
| Offer letter lag | 10–15 days; reportedly 3 internal approvals | Snippet-level |
| Notice period, modal | **60 days** (n=16,912: 2mo 65%, 3mo 15%, 1mo 12%) | Sourced |
| Fixed vs variable | **90.4% fixed / 9.6% variable** | Sourced |

### The money table

EY GDS Senior Consultant, **Engineering–Software & QA**, AmbitionBox (n=538, Feb 2026):

| Experience | Band |
|---|---|
| 3–6 yrs | ₹17.2L – ₹19.5L (n=78) |
| **6–9 yrs** | **₹20.5L – ₹22.6L (n=253)** |
| 9–12 yrs | ₹23.5L – ₹26L (n=205) |

Sub-grade ladder — **the biggest single variable in the process:**

| Sub-grade | Band | n | Experience |
|---|---|---|---|
| Senior Consultant **1** | ₹13.6L – ₹15.1L | 316 | 3–6 yrs |
| Senior Consultant **2** | ₹19.2L – ₹21.2L | 587 | 3–8 yrs |
| Senior Consultant **3** | ₹24.9L – ₹27.5L | 189 | 5–10 yrs |

**₹11L spread at overlapping experience.** Same job, same interview. Decided in fitment, not in L1.

⚠️ **The 4–8 year band is a negotiation risk.** A wide band gives the recruiter room to map you to the bottom of it. At 6 years you are in the upper half — say so explicitly, with the mapping, before a number is put on the table.

⚠️ **Red-flag title:** EY GDS **"Technology Consultant"** = ₹9.5L–₹12.5L across 1–7 yrs (n=79); AmbitionBox's own note is *36% below the IT Services & Consulting industry average*. Materially different job from Senior Consultant. Confirm title **and** rank before the HR call.

**Certs are noise.** Across all 2,275 open EY India reqs on 25 Aug 2026: `AZ-305` = 5, `AZ-400` = 2, **`AZ-204` = 0**, `Azure Certified` = 0. Zero of the eight hours.

---

## 3. Strategy — the revised bet

Eight hours cannot cover this JD. The plan is a bet, stated openly.

### The four bets

**Bet 1 — Weight follows the responsibility list, not the skills list.**
The skills block is a generic laundry list every EY tech JD carries. The **responsibilities** block is specific and was written for this role. Three of nine are CI/CD + IaC + GitOps. That's where Day 2 goes, in full.

**Bet 2 — Zero hours on DSA.**
Half of senior GDS reports have no coding round; when it happens it's HackerRank easy/medium. Your Blind75/NeetCode work in [../dsa/](../dsa/) and [../DSA_MASTER.md](../DSA_MASTER.md) clears that today. Three warm-up problems on the morning of, not before.

**Bet 3 — Platform framing beats tool depth.**
You will not out-Terraform someone who's written it for four years. You *can* out-frame them. "Reusable module with policy-as-code guardrails so teams can't provision a public storage account" beats reciting `for_each` semantics. Say the altitude thing, then show you know the mechanics underneath.

**Bet 4 — Grade negotiation is worth more than any technical hour.**
₹11L spread. Thirty minutes on Day 4 beats eight hours of anything else in expected value.

### What I'm deliberately NOT preparing

| Skipped | Why | If it comes up |
|---|---|---|
| **MuleSoft / Boomi / Camel** | Good-to-have; can't fake platform experience in 8 hrs | "Haven't worked in MuleSoft. I've built the same patterns — canonical mapping, connectors, DLQ, retry — in code and in Azure. Concepts port; DataWeave I'd pick up in a week." |
| **GraphQL depth** | Listed, rarely the job | One paragraph: schema/resolvers, N+1 + DataLoader, why it's hard to cache and rate-limit, when not to use it. |
| **Apigee / Kong** | APIM is the Azure answer | Know the one-line positioning of each. Nothing more. |
| **Power Automate** | Low-code, good-to-have | "Business-user-facing sibling of Logic Apps. I'd reach for Logic Apps Standard for anything an engineer owns." |
| **Jenkins / GitLab CI depth** | ADO + GitHub Actions is enough | "ADO and GitHub Actions in anger; Jenkins I can read and maintain." |
| **Deep AWS** | EY is a Microsoft shop | Memorise the Azure→AWS→GCP mapping table only. |
| **.NET / Java syntax** | JD accepts Python | Never apologise for Python. |
| **Certification content** | 0 of 2,275 reqs mention AZ-204 | — |

**Reversed from the earlier plan:** ArgoCD/Flux and Kubernetes/Helm were on this skip list. They are now core — responsibility 7 names them. Day 2 covers them properly.

### Your unfair advantage

The typical applicant for this req knows Terraform and Kubernetes and has never shipped an LLM system. You are the inverse, and **EY is spending a billion dollars on the thing you already do.**

- **EY + Microsoft, May 2026:** joint investment of "more than $1 billion" over five years to scale enterprise AI. Named stack: Azure, Microsoft Foundry, Microsoft Fabric, Copilot Studio, Power Platform. Copilot to 400,000+ EY employees.
- **EY Canvas:** a multiagent framework in the audit workflow hub on Azure + Foundry + Fabric, across **130,000 Assurance professionals and 160,000 audit engagements.** At-scale, not a pilot.
- EY GDS logged actual Senior Consultant interview questions on **cosine similarity** and **Transformer architecture**. The AI questions are live in this exact interview.

**The reframe:** an agent platform *is* an integration platform. Tool calling is API invocation. An MCP server is an API gateway for models. RAG ingestion is an ETL pipeline. Agent orchestration is workflow orchestration. Every integration story you don't have, you can tell through a system you actually built.

**Play it once, deliberately, in L2** — as the answer to "where does this role go" or "what would you bring beyond the JD." Not in L1; L1 wants to know you can ship a pipeline.

---

## 4. The 8-hour plan

**Passive reading is banned.** Every block ends in an *output* — spoken aloud, typed, or drawn. Recognition is not recall. If you only read, you'll recognise the answer in the room and still not be able to say it.

### Day 1 — Event-driven spine (2h 00m) · *JD responsibilities 1 & 4*

| Block | Time | Do | Output |
|---|---|---|---|
| 1.1 | 15m | **Resume archaeology.** Open your CV. List every technology on it. Circle what you can't defend for 3 minutes. | A written list of your own weak spots. Drives everything else. |
| 1.2 | 35m | [03](03-messaging-and-event-streaming.md) — Service Bus vs Event Grid vs Event Hub vs Storage Queue. **The most-asked Azure integration question.** | Draw the decision table from memory. Say the one-line discriminator for each of the four. |
| 1.3 | 25m | [03](03-messaging-and-event-streaming.md) — DLQ, peek-lock, sessions/ordering, retry with backoff + jitter, poison messages. | Say five distinct reasons a message dead-letters. Explain why jitter exists. |
| 1.4 | 25m | [03](03-messaging-and-event-streaming.md) — **batch-over-messaging** (JD responsibility 4) + claim-check + completion tracking. | Talk through the 2M-record nightly batch design out loud, 6 minutes, timed. |
| 1.5 | 10m | [03](03-messaging-and-event-streaming.md) — transactional outbox + idempotent consumers. | Say the outbox pattern in three sentences. |
| 1.6 | 10m | Pick your **two flagship projects.** Not three. | Write the 3-sentence version of each: what it did, what you owned, what number improved. |

**If you only do one thing:** 1.2.
**Cut first:** 1.5.

### Day 2 — The heavy block: CI/CD, IaC, K8s, GitOps (2h 00m) · *JD responsibilities 5, 6, 7*

Three of the nine responsibilities. Give it the whole day.

| Block | Time | Do | Output |
|---|---|---|---|
| 2.1 | 30m | [05](05-cicd-iac-and-gitops.md) — pipeline design, ADO vs GitHub Actions, **OIDC workload identity federation** for secretless auth, templates/reusable workflows as the platform play. | Say how a pipeline authenticates to Azure with no stored secret. Then say why a template beats a copied pipeline. |
| 2.2 | 25m | [05](05-cicd-iac-and-gitops.md) — **security scanning** (JD names it explicitly): SAST / SCA / container / IaC / secret scanning / DAST, what gates vs what reports. | Name a tool per category and say where it sits in the pipeline. |
| 2.3 | 30m | [05](05-cicd-iac-and-gitops.md) — Terraform: state, remote backend, locking, drift, modules, `for_each` vs `count`, policy-as-code. **Plus the EY-logged question "How do you check resources using Terraform?"** | Answer the EY-logged question in 60 seconds. Explain what's in the state file and why it's a credential. |
| 2.4 | 20m | [04](04-microservices-containers-kubernetes.md) — the EY-logged K8s/Docker set: HPA, Service objects, `EXPOSE` vs `--publish`, CrashLoopBackOff triage, probes. | All five out loud, 60 seconds each, timed. |
| 2.5 | 15m | [05](05-cicd-iac-and-gitops.md) — **GitOps**: pull vs push, ArgoCD Application/sync/selfHeal, Flux, secrets in GitOps, Flagger canary. | Say why pull beats push in one sentence — the credentials argument. |

**If you only do one thing:** 2.3. Terraform state is the single most-asked IaC question and EY logged it.
**Cut first:** 2.5 — but only after you can say the pull-vs-push sentence.

### Day 3 — APIs, gateways, auth, and the FS domain (2h 00m) · *JD responsibilities 2, 3, 8*

| Block | Time | Do | Output |
|---|---|---|---|
| 3.1 | 25m | [01](01-api-design-rest-soap-graphql-openapi.md) — idempotency, status codes, versioning, pagination, RFC 9457. | Design a 5-endpoint API out loud: verbs, codes, versioning, error shape. |
| 3.2 | 20m | [01](01-api-design-rest-soap-graphql-openapi.md) — **SOAP + SOAP-to-REST.** Legacy adapters are JD responsibility 2. | Answer "how would you expose a legacy SOAP service as REST" end to end, no notes. |
| 3.3 | 25m | [02](02-azure-integration-services.md) — **API gateway** concepts (JD responsibility 3): APIM policy pipeline, auth, throttling, versioning, monitoring. | Say the four policy sections in order. Explain revisions vs versions. |
| 3.4 | 20m | [06](06-auth-and-security.md) — `client_credentials`, PKCE, the JWT validation checklist, id_token vs access_token, managed identity. | Recite the JWT checklist. Say why an id_token is never an API access token. |
| 3.5 | 30m | [12](12-financial-services-integration.md) — FS vocabulary and the constraints that change architecture (audit trail, residency, separation of duties, exactly-once *effect*). | Rehearse the honest-framing line: no FS background, but these constraints are familiar — and here's how. |

**If you only do one thing:** 3.5. Domain vocabulary is the cheapest credibility you can buy, and you have none of it today.
**Cut first:** 3.2.

### Day 4 — Rehearsal only. No new material. (2h 00m)

EY's careers site states they score behavioural answers on three elements: **relevant experience, action taken, result.** STAR is the literal rubric. This day is not optional.

| Block | Time | Do | Output |
|---|---|---|---|
| 4.1 | 30m | [ANSWERS.md](ANSWERS.md) §A — "Tell me about yourself," "Why EY," "Why leaving." | Each **three times out loud, timed.** 90 seconds, not four minutes. |
| 4.2 | 30m | [ANSWERS.md](ANSWERS.md) §D — STAR stories. Fill in **your** numbers on six. | Six written skeletons, each ending in a metric. No metric = not a story. |
| 4.3 | 25m | [ANSWERS.md](ANSWERS.md) §E — the gap answer, in its **platform-engineer** form. | Say it until it's fluent and unapologetic. This question decides the offer. |
| 4.4 | 20m | [ANSWERS.md](ANSWERS.md) §F — grade + CTC. Pick your number and your floor. | Write down: target CTC, floor, target sub-grade, the exact sentence you'll say. |
| 4.5 | 15m | [11](11-rapid-fire-cheatsheet.md) — final scan list only. | Nothing new. Recognition pass. |

**If you only do one thing:** 4.3.
**Cut first:** 4.5.

---

## 5. Micro-slots — dead time

30–60 seconds each. Say them out loud or subvocalise.

1. Service Bus vs Event Grid vs Event Hub — one line each.
2. Five reasons a message dead-letters.
3. Why pull-based GitOps beats push — the credentials argument.
4. What's in the Terraform state file, and why it's a credential.
5. `EXPOSE` vs `--publish`.
6. How HPA computes desired replicas — and why KEDA is the right answer for a queue consumer.
7. Liveness vs readiness vs startup — and the cascading-restart trap.
8. SAST vs DAST vs SCA vs IaC scanning — one line each.
9. How a pipeline authenticates to Azure with no stored secret.
10. `client_credentials` vs `authorization_code + PKCE`.
11. The JWT validation checklist — eight items.
12. Idempotency: which verbs are idempotent, and how you make POST idempotent.
13. Exponential backoff with jitter — why the jitter.
14. The transactional outbox, in three sentences.
15. Exactly-once delivery is impossible; exactly-once *effect* is achievable — why.
16. Your 3-sentence project pitch. Both projects.

---

## 6. Interview day

Two rounds, same day. **Different interviews, different audiences.**

### L1 — technical (30–60 min, an engineer)

Wants: can this person build, deploy and debug an integration service.
- Resume walkthrough → architecture of your last project → protocol/platform questions → possibly one coding problem.
- **Commit to an answer, then refine.** A documented EY GDS candidate was accused of using outside help because their answers kept improving across follow-ups; the interviewer ended the call early. State the answer, *then* add nuance. Do not think out loud into a better answer.
- If you get code: brute force → optimise → complexity. Out loud.

### L2 — techno-managerial (Manager, Senior Manager, sometimes a Director)

Wants: can this person sit in front of a financial-services client.
- Scenario design, trade-off defence, conflict/deadline STAR, and "convince me" prompts. EY logged *"Convince me to adopt AWS for our company"* — persuasion is explicitly tested. **Qualify before you advocate.** That's the consulting instinct they're listening for.
- End every story with a number.
- This is where you spend your one deliberate GenAI card.

### HR / fitment

- CIS form may arrive the same day. **It is not an offer.** Keep every other process running.
- Confirm **title and rank** explicitly.
- Notice: modal is 60 days, not 90. Buyout exists but is discretionary and counselor-dependent — **get it in the offer letter in writing**, not verbally.

### Questions to ask

**L1:** Which requisition is this — the DE Cloud Integration Platform Engineer role, or the ACE/MuleSoft one? · Is the GitOps setup ArgoCD or Flux, and who owns the cluster? · What does the on-call model look like for integration services?

**L2:** **Which client and which unit is this req for?** *(Bench/redeployment is a live GDS employee complaint — thread ~July 2026. Some GDS positions carry a client round after EY's rounds.)* · Which industry group — Banking, Insurance, Asset Management? · Do I work directly with the client's engineers or through an onshore lead? · Where does EY.ai / the Canvas agent work touch the DE integration practice?

**HR:** What rank and sub-grade is this mapped to? · RTO expectation for this team specifically? *(GDS India commonly reported as 2 days/week, ~8–10 days a month; varies by service line.)* · Is this engagement US- or UK-shift aligned?

**Never ask:** hikes or promotion timelines in round one; WFH before an offer; anything answerable from ey.com.

---

## 7. When you don't know

Three steps, no apology, under 20 seconds:

1. **Name the adjacent thing you have done.** "I haven't run Flux. I've done pull-based reconciliation with ArgoCD's model in mind — Git as the source of truth, cluster reconciles toward it."
2. **State what you do know, concretely.** "My understanding is Flux splits it into GitRepository and Kustomization/HelmRelease controllers, with image automation as a separate controller."
3. **Ask a question that shows you understand the problem shape.** "Is the cluster multi-tenant? That's usually what decides ArgoCD over Flux."

Never bluff — EY interviewers follow up, and a collapsing answer costs more than the original gap. Never over-apologise either; one clause, then move.

**Never bluff financial-services experience.** You have none. The honest framing in [12](12-financial-services-integration.md) is stronger than a guess, because an FS interviewer will detect the guess in one follow-up.

---

## 8. File index

| File | Covers | Priority |
|---|---|---|
| [ANSWERS.md](ANSWERS.md) | Scripted answers to the questions they'll actually ask | ⭐⭐⭐ |
| [03](03-messaging-and-event-streaming.md) | Service Bus, Event Grid, Event Hub, Kafka, RabbitMQ, batch-over-messaging, patterns | ⭐⭐⭐ |
| [05](05-cicd-iac-and-gitops.md) | CI/CD, security scanning, Terraform, Bicep, ArgoCD/Flux, progressive delivery | ⭐⭐⭐ |
| [04](04-microservices-containers-kubernetes.md) | Docker, Kubernetes, Helm, KEDA, debugging drills | ⭐⭐⭐ |
| [01](01-api-design-rest-soap-graphql-openapi.md) | REST, SOAP + SOAP-to-REST, GraphQL, OpenAPI | ⭐⭐ |
| [06](06-auth-and-security.md) | OAuth2, OIDC, JWT, mTLS, API keys, OWASP API Top 10 | ⭐⭐ |
| [12](12-financial-services-integration.md) | FS domain vocabulary, compliance constraints, worked FS designs | ⭐⭐ |
| [02](02-azure-integration-services.md) | APIM, Logic Apps, Functions, Data Factory | ⭐⭐ |
| [08](08-system-design-integration.md) | 12 integration designs + a 35-minute framework | ⭐⭐ |
| [09](09-behavioral-ey-and-hr.md) | STAR bank, EY values, HR and negotiation | ⭐⭐ |
| [10](10-genai-to-integration-bridge.md) | Turning GenAI depth into the differentiator | ⭐⭐ |
| [07](07-python-for-integration-and-coding-round.md) | Integration-flavoured Python coding problems | ⭐ |
| [11](11-rapid-fire-cheatsheet.md) | One-liners, comparison tables, final scan | ⭐⭐⭐ (last hour) |

---

*Companion: [ANSWERS.md](ANSWERS.md) for the scripted answers. Original JD in [jd.txt](jd.txt).*
