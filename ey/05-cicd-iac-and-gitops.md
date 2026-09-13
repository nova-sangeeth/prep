# CI/CD, Infrastructure-as-Code & GitOps — the heaviest block in this JD

> EY GDS — **DE-Cloud Integration Platform Engineer** (Digital Engineering, Financial Services) — prep pack file 05

**What this file buys you in the interview:** three of the nine JD responsibilities live here — build CI/CD pipelines *including security scanning and release management* (#5), provision cloud infra with IaC (#6), and deploy on Kubernetes with **Helm and GitOps workflows, ArgoCD/Flux** (#7). GitOps moved out of "good to have" and into the responsibility list, which means it is no longer skippable. EY's own logged DevOps questions — *"How do you check resources using Terraform?"*, *"What is the difference between Git Pull and Git Fetch?"*, *"How does HPA work in Kubernetes?"* — sit exactly on this surface. This file is the single highest-value technical read in the pack after messaging.

**The framing that wins this interview:** the title says **Platform** Engineer. Every answer is about the **paved road** — a pipeline template the security guild owns and every product team must `extends:`, a golden Helm chart, a versioned Terraform module registry, policy-as-code guardrails, self-service. Never *"I wrote a pipeline for my app."* Always *"I built the thing forty teams consume, and the guardrails that mean they cannot ship an unsigned image or a publicly-exposed Service Bus namespace."*

**Bridge from your stack:** a CI/CD pipeline is a DAG of idempotent steps with retry and artifact passing — that is LangGraph with a filesystem instead of a state dict. Terraform's plan/apply is a **reconciliation loop**: read desired state (HCL), read actual state (provider API), diff, converge. ArgoCD is the same loop running continuously inside the cluster instead of once inside a runner. A Helm chart is `pydantic` for YAML — a schema plus values plus rendering. Say these out loud; they land.

**If you only have 60 minutes:** §4 (secretless pipelines — the modern answer), §5 (security scanning — a whole JD bullet), §9.4–9.6 (Terraform state, for_each, checking resources), §11 (ArgoCD pull model), §13 (secrets in GitOps), §15.4 (draining a consumer), §17 (whiteboard), §18 (traps).

---

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [The paved road: what a platform engineer actually builds](#1-the-paved-road-what-a-platform-engineer-actually-builds) | Q1–Q3 |
| 2 | [CI/CD principles: build once, promote everywhere](#2-cicd-principles-build-once-promote-everywhere) | Q4–Q9 |
| 3 | [Agents, runners, caching, artifact feeds](#3-agents-runners-caching-artifact-feeds) | Q10–Q13 |
| 4 | [Secrets in pipelines — OIDC workload identity federation](#4-secrets-in-pipelines--oidc-workload-identity-federation) | Q14–Q17 |
| 5 | [Security scanning — the whole JD bullet](#5-security-scanning--the-whole-jd-bullet) | Q18–Q25 |
| 6 | [Azure DevOps Pipelines](#6-azure-devops-pipelines) | Q26–Q33 |
| 7 | [GitHub Actions](#7-github-actions) | Q34–Q40 |
| 8 | [Jenkins and GitLab CI — enough to be credible](#8-jenkins-and-gitlab-ci--enough-to-be-credible) | Q41–Q44 |
| 9 | [Terraform](#9-terraform) | Q45–Q59 |
| 10 | [Bicep, ARM, Pulumi, CloudFormation](#10-bicep-arm-pulumi-cloudformation) | Q60–Q66 |
| 11 | [GitOps and ArgoCD](#11-gitops-and-argocd) | Q67–Q76 |
| 12 | [Flux, and the honest ArgoCD-vs-Flux answer](#12-flux-and-the-honest-argocd-vs-flux-answer) | Q77–Q80 |
| 13 | [Secrets in GitOps](#13-secrets-in-gitops) | Q81–Q83 |
| 14 | [Progressive delivery: Flagger and Argo Rollouts](#14-progressive-delivery-flagger-and-argo-rollouts) | Q84–Q87 |
| 15 | [Deployment strategies for stateful integration workloads](#15-deployment-strategies-for-stateful-integration-workloads) | Q88–Q93 |
| 16 | [CI/CD security & compliance for financial services](#16-cicd-security--compliance-for-financial-services) | Q94–Q99 |
| 17 | [30-second whiteboard versions](#17-30-second-whiteboard-versions) | 3 |
| 18 | [Interviewer traps](#18-interviewer-traps) | 12 |
| 19 | [Rapid fire](#19-rapid-fire) | 60 |

Sibling files: [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md) · [API Design](01-api-design-rest-soap-graphql-openapi.md) · [Azure Integration Services](02-azure-integration-services.md) · [Messaging & Event Streaming](03-messaging-and-event-streaming.md) · [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md) · [Auth & Security](06-auth-and-security.md) · [System Design](08-system-design-integration.md) · [Financial Services Integration](12-financial-services-integration.md)

**Docker, Kubernetes objects, probes, HPA/KEDA and Helm fundamentals are in [file 04](04-microservices-containers-kubernetes.md)** — this file assumes them and does not repeat them. Here, Helm appears only as *platform IP* (the golden chart) and as a deployment mechanism.

---

## 1. The paved road: what a platform engineer actually builds

### Q1. What does an Integration Platform Engineer build that an integration developer doesn't?
`[MEDIUM]` `[THE FRAMING QUESTION — expect it as the opener in L2]`

**Answer:** An integration developer ships one adapter. A platform engineer ships the **paved road that forty adapters travel on** — and the guardrails that make the wrong thing hard. Concretely that's five artefacts: a versioned **pipeline template** the security guild owns and every product pipeline must `extends:`; a **golden Helm chart** with probes, PDB, resource requests, NetworkPolicy and OpenTelemetry already wired; a **private Terraform module registry** so "I need a Service Bus namespace" is six lines of HCL, not sixty; **policy-as-code** that fails the plan when someone tries to ship a public-facing namespace into a prod subscription; and **self-service** — a template repo plus a `backstage`-style scaffolder so a new integration service is live in an hour without a ticket.

The measure of the job is not "my pipeline works." It's **how many teams got a compliant deployment without talking to me**, and **how many non-compliant deployments were impossible rather than merely discouraged.**

```text
                       PRODUCT TEAM OWNS                PLATFORM TEAM OWNS
  ┌──────────────────────────────────┐  ┌────────────────────────────────────────┐
  │ app/  (FastAPI, handlers)        │  │ platform-templates/                    │
  │ tests/                           │  │   templates/secure-pipeline.yml  v3.2.0│
  │ helm/values-{dev,uat,prod}.yaml  │  │ platform-modules/                      │
  │ azure-pipelines.yml  (12 lines,  │  │   modules/integration-service/   v2.4.0│
  │   extends: the platform template)│  │ charts/integration-service/      v3.4.1│
  │ infra/main.tf  (module call)     │  │ policy/  (Rego, Checkov, Azure Policy) │
  └──────────────────────────────────┘  │ gitops-config/  (ArgoCD AppProjects)   │
                                         └────────────────────────────────────────┘
        can change freely                     changes go through the guild,
        inside the guardrails                 versioned, with a migration note
```

**If they push back — "Isn't that just adding bureaucracy?"** — It's the opposite: it removes the review. Because the security controls live *inside* the template rather than in a checklist a human enforces at a gate, a team that extends the template needs no security review to ship. The bureaucracy is what you get when every team writes its own pipeline and an architect has to read all forty. I version the templates and publish a changelog, so teams pin (`ref: refs/tags/v3.2.0`) and upgrade on their own schedule — that's the difference between a platform and a mandate.

---

### Q2. A team says "your golden chart doesn't do what I need." What do you do?
`[MEDIUM]` `[senior signal — this is the real job]`

**Answer:** Three options in order. **One:** if the need is general, I add it to the chart behind a value with a safe default — the chart gets better for everyone. **Two:** if it's genuinely one-off, the chart supports an escape hatch — `extraManifests`, `podAnnotations`, a `values` passthrough — so they don't fork. **Three:** if they still need to leave the road, they can, but they inherit the compliance obligations the road was carrying: they own the scanning gates, the SBOM, the audit evidence. I write that down as an exception with an expiry date.

The failure mode I actively watch for is a chart that has grown 200 values because I said yes to everything. At that point the abstraction has leaked and the chart is harder than raw manifests. When I see that, I split — two charts (stateless HTTP adapter, queue consumer) beats one chart with a `mode:` switch.

**If they push back — "How do you stop the chart becoming a monster?"** — I measure it: number of values, and how many are set by more than three teams. A value only two teams use is a candidate for the escape hatch instead. And I put a `values.schema.json` on the chart so `helm lint` rejects nonsense at authoring time rather than at deploy time.

---

### Q3. How do you get forty teams to actually adopt the paved road?
`[MEDIUM]` `[EY-consulting-shaped]`

**Answer:** Make it the fastest path, then make it the only compliant path, in that order. First I make the road demonstrably cheaper — a new service scaffolded and deploying to dev in under an hour, versus a week of copy-paste. Then I attach the things people can't get any other way: the prod subscription only accepts deployments from a service connection that a **required template check** protects, the ACR only permits signed images, and Azure Policy denies resources without the mandated tags. Adoption stops being a persuasion problem.

The order matters. If you lead with the mandate before the road is good, you get shadow pipelines and everyone hates the platform team.

**If they push back — "What's your migration story for legacy pipelines?"** — Strangler pattern, same as any legacy migration. New services must use the road from day one. Existing pipelines get a deadline tied to a control that's coming anyway (e.g. "on 1 March the prod service connection requires the template"), plus a scripted migration for the 80% case and hands-on help for the awkward 20%. I never do a big-bang cutover of forty pipelines on one weekend.

---

## 2. CI/CD principles: build once, promote everywhere

### Q4. Explain "build once, deploy everywhere" and why it matters.
`[EASY]` `[NEAR-CERTAIN]`

**Answer:** You build the artefact exactly once, at the first stage, and then the *same bytes* are promoted through dev, test, UAT and prod. Nothing is rebuilt per environment. Everything that differs between environments is injected at deploy time as configuration or as a mounted secret — never baked in. The reason is falsifiability: if you rebuild per environment, the thing you tested in UAT is not the thing that reaches prod, and every UAT sign-off is worthless.

The mechanical version of this rule: **promote by immutable digest, never by tag.** A tag is a mutable pointer; `sha256:...` is the artefact.

```bash
# CI, once
IMAGE=eyintacr.azurecr.io/integration/payments-adapter
docker buildx build --provenance=true --sbom=true -t "$IMAGE:$BUILD_ID" --push .

# resolve the digest and carry THAT forward — this is the promoted identity
DIGEST=$(az acr manifest show-metadata --name "$IMAGE:$BUILD_ID" --query digest -o tsv)
echo "##vso[task.setvariable variable=imageDigest;isOutput=true]$DIGEST"

# every later stage deploys the digest, never the tag
helm upgrade --install payments-adapter oci://eyintacr.azurecr.io/helm/integration-service \
  --version 3.4.1 \
  --set image.repository="$IMAGE" \
  --set image.digest="$DIGEST" \
  --namespace payments --atomic --timeout 5m
```

Lock the registry so a tag physically cannot be overwritten (see [file 04 §4](04-microservices-containers-kubernetes.md) for `az acr repository update --write-enabled false` and lock semantics).

**If they push back — "What about environment-specific dependencies?"** — Then the artefact is wrong. If the prod build needs a different wheel, that difference belongs in configuration or in a feature flag, not in the build. The one legitimate exception is architecture (linux/amd64 vs arm64), and the answer there is a multi-arch manifest built once — still one artefact identity.

---

### Q5. Trunk-based development or GitFlow — which does a delivery team actually run, and why?
`[MEDIUM]` `[opinion question; have an opinion]`

**Answer:** Trunk-based, with short-lived branches and a protected `main`, for anything continuously deployed. GitFlow's `develop` + `release/*` + `hotfix/*` machinery exists to solve a problem — coordinating a versioned release of software you ship to customers who install it — that a cloud integration platform does not have. On a delivery team the cost of GitFlow is long-lived branches, painful merges, and a "release branch" that quietly becomes a second `main`.

But be honest about the exception: **a client with a hard change-advisory-board process and a fixed monthly release train sometimes genuinely needs a release branch**, because "what is in the November release" must be a stable, auditable set. That's a real FS constraint, and the answer there is trunk-based development plus **release branches cut from `main` at code freeze**, plus feature flags so unfinished work can sit in `main` disabled. You get one integration point, not two.

| | Trunk-based | GitFlow |
|---|---|---|
| Branch lifetime | hours to 2 days | weeks |
| Where integration pain lands | continuously, small | at release, large |
| Hotfix | commit to main, promote | branch from `master`, merge to two places |
| Fits | continuous deployment, platform work | boxed/versioned product releases |
| The FS compromise | trunk + release branch at freeze + feature flags | — |

**If they push back — "How do you keep main deployable with everyone committing to it?"** — Branch protection with required status checks (the full CI gate, not a subset), required review, linear history, and **feature flags for anything that spans more than a day**. Plus the deploy pipeline gates on the same checks, so a green `main` means deployable by construction. Merge queues if commit rate makes CI-on-merge racy.

---

### Q6. Describe environment promotion with approvals and gates.
`[MEDIUM]` `[near-certain in an FS context]`

**Answer:** One pipeline, one artefact, N stages, and the *difference between environments is who or what must say yes*. Dev is fully automatic on merge to `main`. Test is automatic but gated on integration and contract tests passing. UAT requires an approval from the business analyst who owns the flow. Prod requires two approvals from a group that excludes the person who triggered the run — four-eyes — plus a change-record check and a deployment window.

The distinction I'd draw explicitly is **approvals (a human says yes) versus checks (a machine says yes)**. Machines should do as much as possible: branch control, artefact policy evaluation, business-hours window, an "is there an approved ServiceNow change" REST call. Humans should only be asked the questions machines can't answer.

```text
  merge to main
      │
      ▼
  [build once] ──► artefact + SBOM + signature + digest, immutable
      │
      ▼
  dev      auto                       (checks: none beyond CI gate)
      │
      ▼
  test     auto                       (checks: contract tests, API fuzz vs OpenAPI)
      │
      ▼
  uat      approval: BA owner         (checks: branch control = refs/heads/main)
      │                                        artefact policy = signed + no CRITICAL CVE
      ▼
  prod     approval: 2 of release-managers, requester excluded
                                      (checks: business hours 06:00–09:00 Mon–Thu,
                                               exclusive lock,
                                               ServiceNow change is Approved,
                                               required template = platform v3.x)
```

Azure DevOps calls these **Environment checks**: Approvals, Branch control, Business hours, Evaluate artifact, Exclusive lock, Invoke REST API, Invoke Azure Function, Required template, ServiceNow change management. GitHub Actions calls the equivalent **Environments** with required reviewers, wait timers and deployment branch policies. Name them; it shows you've operated this, not just read about it.

**If they push back — "What about emergency changes at 3am?"** — A documented break-glass path that is *auditable, not silent*: a separate pipeline with a single approver from the on-call rota, which fires an automatic incident record and a Teams notification to the control owner, and which cannot skip the security gates — only the human approvals. Emergency should change *who approves*, never *what is checked*. Then a retrospective within 48 hours that either normalises the change or reverts it.

---

### Q7. What does "shift left" mean concretely in a pipeline?
`[EASY]`

**Answer:** Move each check to the earliest point at which it can possibly fail, because feedback cost rises about an order of magnitude per stage. Format and lint run in a pre-commit hook, on the developer's machine, in under a second. Unit tests and SAST run on the PR. Dependency and secret scanning run on the PR. Contract tests and IaC policy run on the PR — a `terraform plan` posted as a PR comment is shift-left for infrastructure. Image scanning runs at build. DAST and API fuzzing run against the deployed test environment. Only load and chaos testing legitimately live late.

```yaml
# .pre-commit-config.yaml — the cheapest gate there is
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml", "-r", "app"]
        additional_dependencies: ["bandit[toml]"]
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_checkov
        args: ["--args=--quiet --compact"]
```

**If they push back — "Pre-commit hooks can be bypassed with `--no-verify`."** — Correct, which is why every pre-commit hook is *also* a required PR check. The hook is a convenience so you find out in one second instead of four minutes; the PR check is the control. Never rely on a client-side hook as a security boundary.

---

### Q8. What is artifact immutability and how do you enforce it?
`[MEDIUM]`

**Answer:** Once published, an artefact's content can never change under the same identity. Enforced at three layers: **naming** — promote by digest, never by a floating tag; **registry configuration** — ACR repository set to `--write-enabled false` for released repos, or a lock on the specific tag, so a push cannot overwrite; and **verification** — the image is signed with cosign at build and admission control in the cluster refuses anything unsigned, so even an overwritten tag fails to run.

```bash
# make a released tag physically immutable in ACR
az acr repository update \
  --name eyintacr --repository integration/payments-adapter \
  --write-enabled false

# sign keylessly with the pipeline's OIDC identity, then attest the SBOM
IMG="eyintacr.azurecr.io/integration/payments-adapter@${DIGEST}"
cosign sign --yes "$IMG"
syft "$IMG" -o cyclonedx-json=sbom.cdx.json
cosign attest --yes --predicate sbom.cdx.json --type cyclonedx "$IMG"

# verify — this is what admission control runs
cosign verify "$IMG" \
  --certificate-identity-regexp '^https://github\.com/eygds/platform-workflows/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

**If they push back — "Why sign if the registry is private?"** — Because "private" is a network control and signing is an integrity control, and they fail differently. A compromised build agent or a mis-scoped push credential puts a bad image inside the private registry; the signature is what tells the cluster the image came from *the pipeline*, on *a protected branch*, and nowhere else. In an FS audit that provenance chain is the artefact you're asked for, not the firewall rule.

---

### Q9. Continuous Delivery vs Continuous Deployment — and which one is honest for an FS client?
`[EASY]` `[trap: candidates use them interchangeably]`

**Answer:** Continuous **Delivery** means every commit that passes the pipeline is *releasable* — the artefact is built, tested, signed and sitting in a registry, and a human decision releases it. Continuous **Deployment** removes the human: green pipeline goes to production automatically.

For a bank or an insurer, the honest answer is continuous delivery to prod and continuous deployment to everything below it. Not because the technology can't do it, but because the change-management control requires a named approver and a change record, and because the blast radius of a payment integration is regulatory, not just financial. What I push for is that the human decision is the *only* manual step — no manual test sign-off, no manual config edit, no manual smoke test. The deploy itself is one click and thirty seconds.

**If they push back — "So you're saying CD is impossible in a bank?"** — No. I'm saying full continuous deployment is a maturity end-state that needs progressive delivery underneath it: automated canary analysis with metric-based rollback, feature flags, and a proven mean-time-to-restore. Once you can show the auditor "a bad change is automatically rolled back in ninety seconds and here are the last twenty times that happened", the argument for a human gate weakens a lot. I'd sequence it: automate the gates, prove rollback, then negotiate the gate away.

---

## 3. Agents, runners, caching, artifact feeds

### Q10. Microsoft-hosted vs self-hosted agents — when do you *need* self-hosted?
`[MEDIUM]` `[FS-specific — very likely]`

**Answer:** You need self-hosted the moment the pipeline must reach something that is not on the public internet — a private AKS API server, a Service Bus namespace behind Private Link, an on-prem SQL or SAP over ExpressRoute, a private Azure DevOps artifact feed, a Key Vault with public network access disabled. That is the normal state of affairs at a financial-services client, so in practice most of my prod-touching stages run on self-hosted agents in a VNet, and only the build-and-test stages run hosted.

Microsoft is explicit about this: *"You can't use private connections such as ExpressRoute or VPN to connect Microsoft-hosted agents to your corporate network. The traffic between Microsoft-hosted agents and your servers will be over public network."* And Microsoft-hosted agents can't be targeted by service tags — the only option is allow-listing the whole regional IP range from the weekly `ServiceTags_Public` JSON, which is a very large surface to open for a bank.

The verified hosted-agent numbers, worth quoting:

| Fact (Microsoft-hosted, Azure Pipelines) | Value |
|---|---|
| Hardware | Standard_DS2_v2 — 2 vCPU, 7 GB RAM, 14 GB SSD |
| Free disk for your job | **10 GB** ("no space left on device" is almost always this) |
| Free tier, private project | 1 parallel job, **60 min per job**, 1,800 min (30 h)/month |
| Paid parallel job | no monthly cap, **360 min (6 h) per job** |
| Linux cgroup | 6 GB physical / 13 GB total memory |
| VM lifetime | fresh VM per job, discarded after |
| CIS hardening | **not** CIS-hardened — use self-hosted / scale-set / Managed DevOps Pools if required |

GitHub-hosted runners: **6 hours per job**, self-hosted runners **5 days per job**, and a workflow run caps at **35 days**.

The three self-hosted flavours worth naming: plain VMs (you patch them), **VM scale-set agents** (Azure scales the pool, images are yours), and **Managed DevOps Pools** (Microsoft manages the scaling, you supply the image and the VNet). For an FS client I'd propose Managed DevOps Pools or scale-set agents over pet VMs, because ephemeral agents remove the "what did the last build leave behind" class of problem.

**If they push back — "Self-hosted agents are a security risk though."** — They are, and the mitigation is standard: **ephemeral** agents (one job then destroyed), no inbound ports (the agent polls out), a dedicated low-privilege identity per pool, network-segmented so the build pool cannot reach prod data, and never run untrusted code — a fork PR — on a self-hosted agent that sits inside the corporate network. Hosted agents are the *safer* place for untrusted code; that's the trade you're managing.

---

### Q11. How do you make a Python build fast? Talk about caching.
`[MEDIUM]`

**Answer:** Three caches, and they solve different things. **Dependency cache** keyed on the lockfile hash — restore `~/.cache/pip` (or `uv`'s cache) so `pip install` is a copy, not a download. **Docker layer cache** — order the Dockerfile so requirements are copied and installed before app code, and use BuildKit's registry-backed cache so the cache survives a fresh agent. **Test caching** — `pytest --lf` locally, but in CI the win is parallelism (`pytest -n auto`) plus splitting slow integration tests into their own job that runs concurrently.

The rule that matters: **cache key must include the lockfile, restore key must not.** Exact hit = fast; partial hit = warm start; no key relationship = a cache that silently serves stale wheels.

```yaml
# Azure DevOps
- task: Cache@2
  displayName: Cache pip wheels
  inputs:
    key: 'pip | "$(Agent.OS)" | requirements.txt | requirements-dev.txt'
    restoreKeys: |
      pip | "$(Agent.OS)"
    path: $(Pipeline.Workspace)/.cache/pip
```

```yaml
# GitHub Actions — setup-python does the keying for you
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: pip
    cache-dependency-path: |
      requirements.txt
      requirements-dev.txt
```

```dockerfile
# syntax=docker/dockerfile:1.7
# BuildKit cache mount: pip's cache persists across builds without entering a layer
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt
COPY app/ ./app/
```

```bash
# registry-backed layer cache so a fresh ephemeral agent still gets a warm build
docker buildx build \
  --cache-from type=registry,ref=eyintacr.azurecr.io/cache/payments-adapter \
  --cache-to   type=registry,ref=eyintacr.azurecr.io/cache/payments-adapter,mode=max \
  --tag "$IMAGE:$BUILD_ID" --push .
```

GitHub Actions cache storage is **10 GB per repository** across all plans, evicted least-recently-used — so a cache-everything strategy quietly evicts the cache that mattered.

**If they push back — "Is caching ever wrong?"** — Yes, twice. First, never cache anything you're about to security-scan by content: a cached SCA result hides a new advisory published since the cache was written, so the advisory database always refreshes. Second, a cache is an untrusted input — a PR from a fork must not be able to poison the cache the default branch reads. GitHub scopes caches by branch with restricted fallback for exactly this reason; keep it that way.

---

### Q12. What is an artifact feed and why not just push to PyPI?
`[EASY]`

**Answer:** An artifact feed is a private package registry — Azure Artifacts, GitHub Packages, JFrog, Nexus — that does three jobs: hosts your internal shared libraries, **proxies** the public index so a build still works when PyPI has an outage or a package is yanked, and gives you a control point where you can block a package by policy. For a bank, the upstream-proxy behaviour is often the point: builds must be reproducible and must not depend on a third party's availability.

```ini
# pip.conf — one index, which is the feed; the feed proxies PyPI upstream
[global]
index-url = https://pkgs.dev.azure.com/eygds/Platform/_packaging/integration-platform/pypi/simple/
```

The named trap here is **dependency confusion**: if pip sees both your private feed and public PyPI as separate indexes, a public package with your internal name and a higher version wins. The fix is exactly what's above — **one** `index-url` that proxies upstream, never `extra-index-url` alongside it — plus reserving your internal package names publicly.

**If they push back — "How do you handle a package with a known CVE that has no fix?"** — Document it as an accepted risk with an owner and an expiry date in the ignore file, add a compensating control if one exists (network policy, input validation), and set an alert on the advisory so the day a fix ships the exception is removed. Never a permanent blanket ignore, and never a global `--severity CRITICAL`-only downgrade to make the build green.

---

### Q13. `git pull` vs `git fetch` — and why does a pipeline care?
`[EASY]` `[EY-LOGGED QUESTION — asked verbatim]`

**Answer:** `git fetch` downloads new objects and updates your remote-tracking refs (`origin/main`) and touches nothing in your working tree. `git pull` is `git fetch` followed by an integration of the fetched commits into your current branch — `merge` by default, `rebase` with `--rebase`. So fetch is read-only and always safe; pull mutates your branch and can conflict.

Why a pipeline cares: CI never runs `git pull`. It does a **detached-HEAD checkout of an exact commit SHA**, usually shallow (`--depth=1`), because the build must be reproducible from an identity, not from "whatever the branch is right now." If your pipeline needs history — for `git describe`, for a changelog, for SonarQube's blame data, or for gitleaks scanning the full history — you explicitly ask for it (`fetchDepth: 0` in Azure DevOps, `fetch-depth: 0` in `actions/checkout`), and that is a deliberate, slower choice.

```bash
git fetch origin                      # safe: updates origin/main only
git log --oneline HEAD..origin/main   # see what would land, before landing it
git pull --rebase origin main         # fetch + rebase local commits on top
git pull --ff-only origin main        # refuse to create a merge commit; fail instead
```

**If they push back — "What's `git pull --ff-only` for?"** — It's the safe default for a shared branch: it fails loudly if your local branch has diverged instead of silently manufacturing a merge commit. On a trunk-based team I'd set `git config --global pull.ff only` and let people choose `--rebase` deliberately. It's the same instinct as `terraform plan` before `apply` — make the surprising outcome an error, not a side effect.

---

## 4. Secrets in pipelines — OIDC workload identity federation

### Q14. Where do secrets live in your pipelines?
`[MEDIUM]` `[NEAR-CERTAIN — and the modern answer is "nowhere"]`

**Answer:** The correct 2026 answer is that a pipeline should have **no long-lived cloud credential at all.** Never a secret in YAML, never in the repo, and — the part most candidates miss — ideally not even in a variable group, because a service principal secret in a variable group is still a secret someone has to rotate and someone could exfiltrate. The pattern is **OIDC workload identity federation**: the CI system mints a short-lived signed JWT describing *this repo, this branch, this environment*; Entra ID trusts that issuer for a specific subject and exchanges it for an access token. There is no stored credential to steal or rotate.

For the residual secrets that genuinely aren't cloud identities — a partner SFTP password, a legacy SOAP API key — they live in **Key Vault**, and the pipeline reads them at runtime with the federated identity. In Azure DevOps that's a variable group **linked to Key Vault**, so the value is never persisted in the pipeline definition, only referenced.

The hierarchy, worst to best, said in one breath: hardcoded in YAML → pipeline variable marked secret → variable group → **variable group linked to Key Vault** → **workload identity federation, no secret at all**.

**If they push back — "What if the client can't do OIDC yet?"** — Then it's a Key Vault-linked variable group with a service principal whose secret has a 90-day maximum lifetime, an automated rotation runbook, and a Defender alert on the app registration's credential add events. And I put the OIDC migration on the roadmap with a date, because "we'll rotate diligently" is a promise no organisation keeps for three years.

---

### Q15. Set up an Azure DevOps service connection with workload identity federation. What actually happens?
`[HARD]` `[strong senior differentiator]`

**Answer:** You create an Azure Resource Manager service connection with credential type **Workload identity federation**, either **automatic** (Azure DevOps creates the app registration and the federated credential for you) or **manual** (you paste the Issuer and Subject Identifier that Azure DevOps generates into a federated credential on an app registration or a user-assigned managed identity). At run time, the pipeline task requests a token from Azure DevOps; Azure DevOps issues a JWT whose subject encodes the org, project and service connection name; Entra ID validates it against the federated credential and returns an access token scoped to whatever RBAC that identity holds.

Two current facts worth knowing because they show recency: you can now federate to a **user-assigned managed identity**, not only an app registration — which is the better choice when you can't create service principals in the tenant. And the **Azure DevOps issuer `https://vstoken.dev.azure.com` is deprecated and retires on 1 July 2027**; new connections default to the Microsoft Entra issuer `https://login.microsoftonline.com/`, and existing ones should be *converted*, not replaced.

```yaml
# Terraform through a WIF service connection — no ARM_CLIENT_SECRET anywhere
- task: AzureCLI@2
  displayName: terraform plan (non-prod)
  inputs:
    azureSubscription: sc-wif-integration-nonprod   # WIF service connection
    scriptType: bash
    scriptLocation: inlineScript
    addSpnToEnvironment: true                       # exposes $servicePrincipalId, $idToken, $tenantId
    inlineScript: |
      set -euo pipefail
      export ARM_USE_OIDC=true
      export ARM_USE_AZUREAD=true                   # data-plane auth to the state blob via Entra ID
      export ARM_CLIENT_ID="$servicePrincipalId"
      export ARM_OIDC_TOKEN="$idToken"
      export ARM_TENANT_ID="$tenantId"
      export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"

      terraform -chdir=infra/envs/nonprod init -input=false
      terraform -chdir=infra/envs/nonprod plan -input=false -lock-timeout=5m -out=tfplan
      terraform -chdir=infra/envs/nonprod show -json tfplan > "$(Build.ArtifactStagingDirectory)/tfplan.json"
```

**Permissions you need on both sides** — and naming this is what separates someone who's done it from someone who's read about it: in Azure DevOps, *Service connection administrator* or endpoint administrator on the connection; in Azure, *Managed Identity Federated Credential Contributor* (or Managed Identity Contributor) on a UAMI, or **Owner** on the app registration; plus the role assignment (e.g. Contributor) on the target subscription or resource group. Those are three different approvals from possibly three different people, which is why the setup ticket takes a week at a bank.

**If they push back — "How do you scope it so a dev branch can't deploy to prod?"** — The federated credential's **subject** is the control. In Azure DevOps the subject is derived from org/project/service-connection, so you get one identity per service connection and you restrict which pipelines may use it (never tick *Grant access permission to all pipelines*) plus an environment-level branch-control check. In GitHub Actions the subject is far more expressive — you federate on `repo:eygds/payments-adapter:environment:prod`, so a token minted from a feature branch literally does not match the trust and Entra ID refuses it. That is a cryptographic boundary, not a policy one.

---

### Q16. Same thing in GitHub Actions — show me the OIDC flow.
`[MEDIUM]` `[HIGH-VALUE — memorise the permissions block]`

**Answer:** Three moving parts. The workflow requests an OIDC token by granting `id-token: write`. `azure/login@v2` exchanges it at Entra ID for an access token using only *public* identifiers — client id, tenant id, subscription id — which are `vars`, not secrets. Entra ID accepts it because the app registration has a federated credential whose issuer is `https://token.actions.githubusercontent.com` and whose subject matches the run.

The verified subject formats, which is what you'll be asked to bind on:

| Trigger | `sub` claim |
|---|---|
| Branch | `repo:ORG/REPO:ref:refs/heads/BRANCH-NAME` |
| Tag | `repo:ORG/REPO:ref:refs/tags/TAG-NAME` |
| Environment | `repo:ORG/REPO:environment:ENVIRONMENT-NAME` |
| Pull request | `repo:ORG/REPO:pull_request` |
| Reusable workflow | matched via the `job_workflow_ref` claim |

The token is short-lived — the documented example expires in **900 seconds** — and is valid for a single job.

```yaml
name: deploy-prod
on:
  push:
    tags: ['v*']

permissions:
  contents: read          # least privilege: start from nothing and add

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: prod     # required reviewers + the sub claim we federate on
    permissions:
      id-token: write     # <- mint the OIDC JWT
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Azure login (federated — no client secret exists)
        uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy
        run: |
          set -euo pipefail
          az account show -o table
          az aks get-credentials --resource-group rg-int-prod --name aks-int-prod --overwrite-existing
          helm upgrade --install payments-adapter \
            oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
            --set image.digest="${{ needs.build.outputs.digest }}" \
            --namespace payments --atomic --timeout 5m
```

```bash
# the Entra ID side: bind the trust to the ENVIRONMENT, not the branch
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "gh-payments-adapter-prod",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:eygds/payments-adapter:environment:prod",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

**If they push back — "Isn't `pull_request` a dangerous subject to federate?"** — Extremely, and I never federate it for a write-capable identity. `repo:ORG/REPO:pull_request` matches *any* PR, including one opened from a fork by a stranger. The only thing I'd ever bind to it is a read-only identity for `terraform plan`, and even then `pull_request_target` and fork PRs need separate handling. Write identities bind to `environment:prod`, which forces the run through the environment's required reviewers before the token is even minted.

---

### Q17. What is the `permissions` block in GitHub Actions and what's the default?
`[MEDIUM]` `[trap question]`

**Answer:** `GITHUB_TOKEN` is a per-run installation token, and `permissions:` sets its scopes. The safe pattern is to declare `permissions: {}` or `contents: read` at workflow level — which drops everything — and then grant the minimum per job: `id-token: write` only on the job that logs into Azure, `packages: write` only on the job that pushes, `pull-requests: write` only on the job that posts the plan comment. Setting `permissions` at workflow level **replaces** the default entirely rather than adding to it, which is what makes it useful.

Two limits worth having: `GITHUB_TOKEN` is rate-limited to **1,000 API requests per hour per repository** (15,000 on Enterprise Cloud), and it expires when the job finishes.

**If they push back — "Why not just use a PAT?"** — Because a PAT is a long-lived, user-scoped, org-wide credential that outlives the person who created it and is invisible in the audit trail as anything other than that user. `GITHUB_TOKEN` is scoped to the repository and the run, expires automatically, and shows in logs as the workflow. If I genuinely need cross-repo access I use a **GitHub App** installation token, scoped to the specific repos, minted per run — never a PAT in a secret.

---

## 5. Security scanning — the whole JD bullet

> Responsibility #5 names "automated testing, **security scanning**, and release management" explicitly. In an FS interview this is not a bullet, it's a five-minute conversation. Know the categories, one named tool each, where it runs, and what you gate on.

### Q18. Walk me through every security scan in your pipeline and where each one runs.
`[HARD]` `[THE question for this JD — rehearse this out loud]`

**Answer:** Seven categories, and the discipline is knowing *where* each runs and *what you block on*, because a pipeline that blocks on everything gets disabled within a month.

| Category | Tool (Python/Azure stack) | Runs | Gate |
|---|---|---|---|
| **Secret scanning** | gitleaks + GitHub secret scanning with **push protection** | pre-commit, PR, and push | **Block always.** Zero tolerance — a leaked credential is already leaked. |
| **SAST** | Bandit (Python), CodeQL, SonarQube | PR, on changed files | Block on new HIGH; existing findings tracked, not blocking |
| **SCA / dependencies** | pip-audit, Dependabot, Snyk, OWASP Dependency-Check | PR + nightly on `main` | Block on HIGH/CRITICAL **with a fix available**; report the rest |
| **IaC scanning** | Checkov, Trivy `config`, Bicep linter, Terrascan | PR, on the plan JSON | Block on the org's hard rules (public network, no encryption, no tags) |
| **Container image** | Trivy, Defender for Containers, ACR scanning | after build, before push | Block on HIGH/CRITICAL fixable; base-image age is a separate report |
| **DAST + API fuzz** | OWASP ZAP baseline, **schemathesis** against the OpenAPI spec | against deployed test env | Report, with a small blocking subset (auth bypass, 500s) |
| **Supply chain** | Syft/CycloneDX SBOM, cosign signing, SLSA provenance | at publish | Block on *missing* signature/SBOM (a control, not a finding) |

The nightly re-scan of `main` matters more than most people think: a dependency that was clean when you built it is not clean forever, and CVE-2021-44228 landed on a Friday. A pipeline that only scans at build time tells you nothing about what is running in prod today.

**If they push back — "Which of those would you drop if the build takes too long?"** — None. I'd move them rather than drop them: secret scanning and SAST stay on the PR because they're fast and their findings are cheap to fix early; SCA and image scanning move to a job that runs in parallel with tests rather than after them; DAST and the full ZAP scan move to a nightly against the test environment, with only a fast baseline on the PR. Total wall-clock, not total work, is what people actually complain about.

---

### Q19. Show me the real pipeline steps for each scanner.
`[HARD]`

```yaml
# ── SECRET SCANNING ──────────────────────────────────────────────────────────
- script: |
    set -euo pipefail
    gitleaks detect --source . --redact --no-banner \
      --report-format sarif --report-path "$(Build.ArtifactStagingDirectory)/gitleaks.sarif" \
      --exit-code 1
  displayName: 'Secrets: gitleaks (blocking)'
  # full-history scan requires fetchDepth: 0 on the checkout step
```

```yaml
# ── SAST (Python) ────────────────────────────────────────────────────────────
- script: |
    set -euo pipefail
    # -ll = report MEDIUM severity and above; -ii = MEDIUM confidence and above
    bandit -r app -ll -ii -f json -o "$(Build.ArtifactStagingDirectory)/bandit.json"
  displayName: 'SAST: bandit (blocking on medium+)'

# SonarQube — the task major version tracks the extension installed in your org
- task: SonarQubePrepare@6
  inputs:
    SonarQube: sonarqube-service-connection
    scannerMode: CLI
    configMode: manual
    cliProjectKey: eygds_payments-adapter
    extraProperties: |
      sonar.python.version=3.12
      sonar.sources=app
      sonar.tests=tests
      sonar.python.coverage.reportPaths=coverage.xml
- task: SonarQubeAnalyze@6
- task: SonarQubePublish@6
  inputs:
    pollingTimeoutSec: '300'
```

```yaml
# ── SCA / DEPENDENCIES ───────────────────────────────────────────────────────
- script: |
    set -euo pipefail
    pip install pip-audit
    # --strict fails the run if any dependency cannot be resolved/audited at all
    pip-audit -r requirements.txt --strict \
      --format json --output "$(Build.ArtifactStagingDirectory)/pip-audit.json"
  displayName: 'SCA: pip-audit (blocking)'
```

```yaml
# ── IaC SCANNING ─────────────────────────────────────────────────────────────
- script: |
    set -euo pipefail
    pip install checkov
    checkov -d infra/terraform --framework terraform \
      --quiet --compact \
      --output cli --output junitxml \
      --output-file-path console,"$(Build.ArtifactStagingDirectory)/checkov.xml" \
      --skip-check CKV_AZURE_35   # documented exception, owner + expiry in EXCEPTIONS.md
  displayName: 'IaC: checkov (blocking)'

# Custom org rules that Checkov does not ship — OPA against the plan JSON
- script: |
    set -euo pipefail
    conftest test --policy policy/terraform "$(Build.ArtifactStagingDirectory)/tfplan.json"
  displayName: 'IaC: OPA/conftest against the plan (blocking)'
```

```yaml
# ── CONTAINER IMAGE ──────────────────────────────────────────────────────────
- script: |
    set -euo pipefail
    trivy image \
      --exit-code 1 \
      --severity HIGH,CRITICAL \
      --ignore-unfixed \
      --format sarif -o "$(Build.ArtifactStagingDirectory)/trivy.sarif" \
      "$(acrLoginServer)/$(imageRepo):$(tag)"
  displayName: 'Image: trivy (blocking on fixable HIGH/CRITICAL)'
```

```yaml
# ── DAST / API-SPEC FUZZING (against the deployed test env) ──────────────────
- script: |
    set -euo pipefail
    pip install schemathesis
    schemathesis run https://payments-adapter.test.internal.ey.net/openapi.json \
      --checks all \
      -H "Authorization: Bearer $(TEST_TOKEN)"
  displayName: 'API fuzz: schemathesis against the OpenAPI contract'

- script: |
    set -euo pipefail
    docker run --rm -v "$(pwd):/zap/wrk:rw" ghcr.io/zaproxy/zaproxy:stable \
      zap-api-scan.py \
        -t https://payments-adapter.test.internal.ey.net/openapi.json \
        -f openapi -r zap-report.html
  displayName: 'DAST: OWASP ZAP API scan (report only)'
```

```yaml
# ── SUPPLY CHAIN: SBOM + SIGN + ATTEST ───────────────────────────────────────
- task: AzureCLI@2
  displayName: 'Supply chain: SBOM, sign, attest'
  inputs:
    azureSubscription: sc-wif-acr-push
    scriptType: bash
    scriptLocation: inlineScript
    inlineScript: |
      set -euo pipefail
      az acr login --name $(acrName)
      IMG="$(acrLoginServer)/$(imageRepo)@$(imageDigest)"
      syft "$IMG" -o cyclonedx-json=sbom.cdx.json
      cosign sign --yes "$IMG"
      cosign attest --yes --predicate sbom.cdx.json --type cyclonedx "$IMG"
```

**Verified flag notes:** Trivy's `--severity` default is `UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL`, its default `--format` is `table` and default `--scanners` is `vuln,secret`; `--ignore-unfixed` is shorthand for `--ignore-status affected,will_not_fix,fix_deferred,end_of_life`; `--exit-code` sets the exit code "when any security issues are found". Ignore entries go in `.trivyignore` / `.trivyignore.yaml` via `--ignorefile`, or as a Rego policy via `--ignore-policy`.

---

### Q20. Bandit says my `subprocess` call is a HIGH. It's fine. Now what?
`[MEDIUM]` `[the false-positive question — this is where scanning becomes theatre]`

**Answer:** I suppress it **narrowly, in code, with a reason, at the line** — never with a global severity downgrade and never by turning the check off org-wide. The suppression is a code review artefact: the reviewer sees the `# nosec` and the justification in the same diff as the code.

```python
import shlex
import subprocess  # nosec B404 - required for the SAP RFC CLI shim; no shell, fixed argv

ALLOWED_TRANSACTIONS = frozenset({"ZPAY001", "ZPAY002"})


def run_sap_shim(transaction: str, payload_path: str) -> str:
    """Invoke the vendor CLI. Argv is fixed; the only variable is allow-listed."""
    if transaction not in ALLOWED_TRANSACTIONS:
        raise ValueError(f"transaction not allow-listed: {transaction!r}")

    # nosec B603 - shell=False, argv is a list, transaction is allow-listed above
    result = subprocess.run(  # noqa: S603
        ["/opt/sap/bin/rfc-shim", "--transaction", transaction, "--input", payload_path],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        shell=False,
    )
    return result.stdout


def _never_do_this(user_input: str) -> None:
    # This is what the scanner is actually looking for and it is correct to flag it.
    subprocess.run(f"/opt/sap/bin/rfc-shim {shlex.quote(user_input)}", shell=True, check=True)
```

The governance layer around suppressions: every ignore file entry carries **an owner, a justification and an expiry date**, they live in a file the security guild reviews quarterly, and a CI job fails when an entry is past its expiry. That converts "we ignored it" from an untracked liability into a managed exception with a date.

```yaml
# .trivyignore.yaml — an exception is a dated decision, not a deletion
vulnerabilities:
  - id: CVE-2024-99999
    paths: ["usr/lib/python3.12/site-packages/legacy_soap_client"]
    statement: "No fix upstream. Not reachable: parser is only invoked on partner
                payloads that APIM schema-validates first. Compensating control:
                APIM validate-content policy on the ingress API."
    expired_at: 2026-11-30
```

**If they push back — "How do you stop the ignore file becoming a dumping ground?"** — Three things. A hard cap on the number of open exceptions per service, published on the platform dashboard. Expiry enforcement in CI. And I report the *trend* rather than the count to leadership — exceptions opened vs closed per month — because a flat count hides a slow leak. If a team is above the cap they can still ship, but their next exception needs the security guild's signature, which makes the cost visible to the person creating it.

---

### Q21. What do you gate the build on versus only report?
`[MEDIUM]`

**Answer:** Gate on things that are **new, actionable, and high-impact**. Report on things that are pre-existing, unfixable, or advisory. The precise rule I use: block if the finding is HIGH or CRITICAL **and** a fix exists **and** it was introduced by this change. Everything else raises a ticket with an SLA — CRITICAL 7 days, HIGH 30 days — and shows on a dashboard the team owns.

The reason for the "introduced by this change" clause is that turning on scanning against a five-year-old codebase produces 4,000 findings, and a gate that fails on all of them gets bypassed on day two. So you **baseline**: snapshot the existing findings as accepted-with-SLA, gate strictly on the delta, and burn the baseline down on a schedule. Sonar calls this "new code" quality gates; the same idea works with any tool.

Two things are gated unconditionally regardless of severity, because they're controls rather than findings: **a detected secret**, and **a missing signature or SBOM**.

**If they push back — "The team says the gate blocks them constantly."** — Then either the gate is wrong or the base image is. I'd look at what's actually failing: if it's the same three OS-level CVEs in the base image every week, the fix is a hardened, weekly-rebuilt golden base image the platform team owns — which removes the finding for every team at once. That's the platform answer. Tuning the threshold down is the answer that looks like progress and isn't.

---

### Q22. What is an SBOM and why does a bank care?
`[MEDIUM]` `[FS-relevant]`

**Answer:** A Software Bill of Materials is a machine-readable inventory of every component in an artefact — package, version, licence, and ideally the hash — in a standard format, CycloneDX or SPDX. A bank cares because of the Log4Shell question: *"is this component anywhere in our estate, and where?"* Without SBOMs that took organisations weeks. With SBOMs stored per released artefact it's a query. It's also increasingly a contractual and regulatory expectation for third-party software.

The operationally important part: an SBOM is only useful if it's generated **from the built artefact, not from the lockfile**, and if it's **attached to the artefact** rather than to a build log that ages out. Hence `syft <image>` (scans the image layers, catches OS packages your lockfile never mentioned) and `cosign attest` (stores it in the registry alongside the image, signed).

```bash
# generate from the image, not the repo — catches OS packages too
syft eyintacr.azurecr.io/integration/payments-adapter@sha256:abc... \
  -o cyclonedx-json=sbom.cdx.json

# attach it to the image, signed, in the registry
cosign attest --yes --predicate sbom.cdx.json --type cyclonedx \
  eyintacr.azurecr.io/integration/payments-adapter@sha256:abc...

# months later: "are we exposed to this CVE?" — scan the stored SBOM, not the estate
grype sbom:./sbom.cdx.json
```

**If they push back — "What's SLSA and do you need it?"** — SLSA (Supply-chain Levels for Software Artifacts) is a framework of build-integrity levels. The practical content is **provenance**: a signed statement of which source commit, which builder, and which parameters produced this artefact. `docker buildx --provenance=true` and GitHub's artifact attestations generate it. For an FS client I'd target the level where builds run on ephemeral, hosted infrastructure and provenance is generated and verified at admission — that's a meaningful control. Chasing the top level (fully hermetic, reproducible builds) is usually not proportionate for integration middleware.

---

### Q23. How is IaC scanning different from application SAST?
`[MEDIUM]`

**Answer:** Different failure model. SAST looks for a defect in code that *could* be exploited at runtime. IaC scanning looks for a **misconfiguration that is the vulnerability** — a storage account with public blob access, a Service Bus namespace with SAS enabled, an NSG with 0.0.0.0/0 on 22, a database without encryption at rest. There's no exploit chain to argue about; the resource is wrong the moment it exists.

Two practical consequences. First, you can scan **the plan, not just the source** — `terraform show -json tfplan > tfplan.json` and run Checkov or Conftest against the resolved values, which catches things a source scan can't see because they came from a variable or a module default. Second, IaC scanning has a runtime twin: **Azure Policy** at the subscription/management-group level. Scanning catches it in the PR; Azure Policy catches it if someone clicks it in the portal. You want both, because scanning is only a control if IaC is the only way in.

```rego
# policy/terraform/guardrails.rego — org rules Checkov doesn't ship
package terraform.guardrails

import rego.v1

deny contains msg if {
    rc := input.resource_changes[_]
    rc.type == "azurerm_servicebus_namespace"
    rc.change.after.local_auth_enabled == true
    msg := sprintf("%s: SAS/local auth must be disabled — use Entra ID + RBAC", [rc.address])
}

deny contains msg if {
    rc := input.resource_changes[_]
    rc.type == "azurerm_servicebus_namespace"
    input.variables.env.value == "prod"
    rc.change.after.public_network_access_enabled == true
    msg := sprintf("%s: prod namespaces must be Private Link only", [rc.address])
}

deny contains msg if {
    rc := input.resource_changes[_]
    "create" in rc.change.actions
    required := {"workload", "environment", "cost_centre", "data_classification"}
    missing := required - {k | rc.change.after.tags[k]}
    count(missing) > 0
    msg := sprintf("%s: missing mandatory tags %v", [rc.address, missing])
}
```

```bash
conftest test --policy policy/terraform tfplan.json
```

**If they push back — "Why OPA when Checkov already has 1,000 rules?"** — Checkov covers the industry-standard rules brilliantly and I use it. OPA covers *my client's* rules — naming conventions, mandatory tags tied to their cost model, "prod resources must be in UK South for data residency", "no resource may be created outside a module from the approved registry". Those are the rules an auditor actually asks about, and no off-the-shelf tool ships them.

---

### Q24. Where does Microsoft Defender fit?
`[EASY]`

**Answer:** Defender for Cloud is the runtime and posture half; the pipeline scanners are the pre-deployment half. **Defender for Containers** scans images in ACR on push and continuously re-scans, and gives you runtime threat detection on AKS nodes and workloads. **Microsoft Defender for Cloud DevOps security** (formerly Defender for DevOps) connects to Azure DevOps and GitHub and surfaces the pipeline's own findings — IaC misconfigurations, exposed secrets — in the same Defender console as the runtime findings, so a security analyst sees one list.

The value is the join: Defender can tell you *this running container has a critical CVE, here is the image, here is the pipeline that built it, here is the commit*. That closes the loop from a runtime alert back to a code fix, which is the thing that's usually missing.

**If they push back — "So can you drop Trivy?"** — No, and for a specific reason: ACR/Defender scanning happens *after* the push. Trivy in the pipeline happens *before*. If I only scan post-push, a vulnerable image is already in the registry and someone can pull it, and my gate is a notification rather than a block. Trivy blocks; Defender covers drift, new CVEs against already-published images, and the runtime layer that Trivy can't see.

---

### Q25. How do you scan a Helm chart or Kubernetes manifests?
`[MEDIUM]`

**Answer:** Render first, then scan — because the security-relevant fields (`runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities.drop`, resource limits, `hostNetwork`) live in values and templates, and a scanner reading the template source sees `{{ .Values.securityContext }}` and learns nothing.

```bash
# render with the values that will actually be used, then scan the output
helm template payments-adapter charts/integration-service \
  --values charts/integration-service/values.yaml \
  --values apps/payments-adapter/values-prod.yaml \
  > /tmp/rendered.yaml

trivy config /tmp/rendered.yaml --severity HIGH,CRITICAL --exit-code 1
checkov -f /tmp/rendered.yaml --framework kubernetes --quiet --compact

# schema-validate against the target cluster's API version — catches removed APIs
kubeconform -strict -kubernetes-version 1.30.0 -summary /tmp/rendered.yaml
```

The runtime twin here is **Pod Security Admission** (enforce `restricted` on the namespace) plus a policy engine — Kyverno or Gatekeeper — that refuses an unsigned image or a pod without resource limits. Same principle as IaC: scan blocks the PR, admission blocks the cluster.

**If they push back — "What if a team deploys with `kubectl apply` and bypasses the chart?"** — In a GitOps cluster they can't: humans don't have write access to the cluster, ArgoCD does, and ArgoCD only applies what's in Git. That's one of the strongest arguments for GitOps in a regulated environment and it's the answer I'd lead with — see §11. Where direct access still exists, admission control is the backstop, because it doesn't care how the manifest arrived.

---

## 6. Azure DevOps Pipelines

### Q26. Explain the YAML pipeline object model.
`[EASY]` `[NEAR-CERTAIN]`

**Answer:** Four nested levels plus triggers. **Stages** are the promotion boundary and the unit of approval. **Jobs** are the unit of scheduling — each job gets its own agent and its own workspace, so jobs are isolated and can run in parallel. **Steps** are tasks or scripts and run sequentially on one agent, sharing the filesystem. Wrapping them: `trigger` (CI, on push), `pr` (validation builds), `pool` (which agents), `variables`, and `resources` (other repos, pipelines, container images).

The mental model that avoids most mistakes: **anything shared between jobs must be published as an artifact or an output variable**, because jobs do not share a disk. Steps share a disk; jobs never do.

```yaml
trigger:                       # CI trigger
  branches: { include: [main] }
  paths: { exclude: [docs/*, README.md] }

pr:                            # PR validation
  branches: { include: [main] }

resources:
  repositories:
    - repository: platform     # the governance template lives elsewhere
      type: git
      name: Platform/platform-templates
      ref: refs/tags/v3.2.0    # pinned; a moving ref is an unreviewed change

variables:
  - group: platform-common     # linked to Key Vault — no secret literals here
  - name: acrName
    value: eyintacr

stages:
  - stage: build
    jobs:
      - job: compile
        pool: { vmImage: ubuntu-latest }
        steps:
          - script: echo "steps share a filesystem"
```

**If they push back — "What's the difference between a `task:` and a `script:`?"** — `script:` is sugar for the `CmdLine`/`Bash` task — it runs shell. A `task:` is a versioned, packaged unit with typed inputs (`AzureCLI@2`, `UsePythonVersion@0`), and the `@N` is the *major* version, which Microsoft can update within. For anything security-relevant I prefer tasks over scripts, because a task handles credential injection and masking properly, whereas a script that echoes a variable can leak it into logs.

---

### Q27. What are templates, and what does `extends` do that `template` doesn't?
`[HARD]` `[THE PLATFORM-ENGINEERING ANSWER — rehearse it]`

**Answer:** A plain template is *inclusion* — a pipeline pulls in steps or a job from a shared file, and it can pull in anything else too. `extends` is *inversion of control*: the pipeline declares "my entire definition is this template, here are my parameters", and the template decides what runs. The pipeline can only inject what the template's parameters allow — typically a `stepList` for the build steps. It cannot add a stage, change the pool, or skip the scanning.

That distinction is the whole governance story, because Azure DevOps has a **required template check** you can attach to an environment or a service connection: the deployment is refused unless the pipeline extends an approved template. So the security guild owns the scanning stages, the sign step and the approval structure; product teams own their build steps; and the platform can prove to an auditor that *every* production deployment ran the mandated controls.

```yaml
# platform-templates/templates/secure-pipeline.yml   (owned by the security guild)
parameters:
  - name: serviceName
    type: string
  - name: pythonVersion
    type: string
    default: '3.12'
  - name: buildSteps           # the ONLY thing a product team injects
    type: stepList
    default: []
  - name: prodEnvironment
    type: string
  - name: severityGate
    type: string
    default: 'HIGH,CRITICAL'
    values: ['CRITICAL', 'HIGH,CRITICAL']

stages:
  - stage: build_and_scan
    displayName: Build, test, scan
    jobs:
      - job: build
        pool: { vmImage: ubuntu-latest }
        steps:
          - checkout: self
            fetchDepth: 0      # gitleaks needs history

          - task: UsePythonVersion@0
            inputs: { versionSpec: '${{ parameters.pythonVersion }}' }

          # product team's steps land here, sandwiched between platform controls
          - ${{ parameters.buildSteps }}

          - template: steps/security-scan.yml
            parameters:
              severityGate: ${{ parameters.severityGate }}

          - template: steps/sign-and-attest.yml
            parameters:
              serviceName: ${{ parameters.serviceName }}

  - stage: deploy_prod
    dependsOn: build_and_scan
    condition: succeeded()
    jobs:
      - deployment: deploy
        environment: ${{ parameters.prodEnvironment }}
        pool: { name: fs-selfhosted-linux }
        strategy:
          runOnce:
            deploy:
              steps:
                - template: steps/helm-deploy.yml
                  parameters: { serviceName: ${{ parameters.serviceName }} }
```

```yaml
# payments-adapter/azure-pipelines.yml   (the whole product-team pipeline)
trigger:
  branches: { include: [main] }

resources:
  repositories:
    - repository: platform
      type: git
      name: Platform/platform-templates
      ref: refs/tags/v3.2.0

extends:
  template: templates/secure-pipeline.yml@platform
  parameters:
    serviceName: payments-adapter
    prodEnvironment: aks-prod.payments
    buildSteps:
      - script: |
          set -euo pipefail
          pip install -r requirements.txt -r requirements-dev.txt
          pytest tests/unit --junitxml=junit.xml --cov=app --cov-report=xml:coverage.xml
        displayName: Unit tests
```

**If they push back — "Can't a team just not extend the template?"** — They can write whatever pipeline they like, and it will build fine. What it cannot do is deploy: the prod environment carries a **required template** check naming `templates/secure-pipeline.yml@platform`, and the ACR push service connection carries the same check. So the enforcement point is the *credential*, not the pipeline file — which is the right place, because it's the thing they can't self-serve around.

---

### Q28. What is a `deployment` job and how does it differ from a `job`?
`[MEDIUM]`

**Answer:** A `deployment` job targets an **environment**, which gives you three things a plain job doesn't: the environment's checks and approvals gate it automatically; Azure DevOps records deployment history per environment (what version is in UAT right now, and who put it there); and you get **strategies** — `runOnce`, `rolling`, `canary` — with lifecycle hooks (`preDeploy`, `deploy`, `routeTraffic`, `postRouteTraffic`, `on: success | failure`). A deployment job also checks out nothing by default, so you add `checkout: self` explicitly when you need the repo.

```yaml
- stage: deploy_prod
  dependsOn: build_and_scan
  jobs:
    - deployment: helm_deploy
      displayName: Helm deploy to AKS prod
      environment: aks-prod.payments        # environment.resourceName
      pool:
        name: fs-selfhosted-linux           # private AKS API server -> self-hosted
      strategy:
        runOnce:
          preDeploy:
            steps:
              - download: current
                artifact: manifests
          deploy:
            steps:
              - task: AzureCLI@2
                displayName: helm upgrade
                inputs:
                  azureSubscription: sc-wif-aks-prod
                  scriptType: bash
                  scriptLocation: inlineScript
                  inlineScript: |
                    set -euo pipefail
                    az aks get-credentials -g rg-int-prod -n aks-int-prod --overwrite-existing
                    kubelogin convert-kubeconfig -l workloadidentity
                    helm upgrade --install payments-adapter \
                      oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
                      --namespace payments \
                      --set image.repository=eyintacr.azurecr.io/integration/payments-adapter \
                      --set image.digest=$(build.outputs.imageDigest) \
                      --atomic --timeout 5m --wait
          routeTraffic:
            steps:
              - script: ./scripts/smoke-test.sh https://payments.internal.ey.net
                displayName: Smoke test before declaring success
          on:
            failure:
              steps:
                - script: helm rollback payments-adapter --namespace payments
                  displayName: Rollback
```

Note `--atomic --timeout 5m`: Helm rolls back automatically if the release doesn't become ready. That is your first line of defence and it costs one flag.

**If they push back — "Why not use the Kubernetes environment resource and `manifest` tasks?"** — You can, and for a push-based ADO deployment it gives you the nice per-environment pod view. I generally don't, for two reasons: it wants cluster credentials in the pipeline, which is exactly what GitOps removes; and `KubernetesManifest@1` with `strategy: canary` reimplements what Argo Rollouts or Flagger do better with real metric analysis. If the client is on GitOps, the ADO pipeline's last act is a commit to the config repo, not a `kubectl apply` — see §11.

---

### Q29. Give me the complete multi-stage pipeline for a Python integration service.
`[HARD]` `[the "show me a real pipeline" ask]`

```yaml
# azure-pipelines.yml — full pipeline, expanded (in practice this lives behind `extends`)
name: $(Date:yyyyMMdd)$(Rev:.r)

trigger:
  branches: { include: [main] }
  paths: { exclude: [docs/*, '**/*.md'] }

pr:
  branches: { include: [main] }

variables:
  - group: platform-common            # Key Vault-linked; no secret literals
  - name: acrName
    value: eyintacr
  - name: acrLoginServer
    value: eyintacr.azurecr.io
  - name: imageRepo
    value: integration/payments-adapter
  - name: tag
    value: $(Build.BuildNumber)-$(Build.SourceVersion)

stages:

  # ── 1. BUILD, TEST, SCAN ───────────────────────────────────────────────────
  - stage: build_and_scan
    displayName: Build, test, scan
    jobs:
      - job: test
        displayName: Unit + contract tests, SAST, SCA
        pool: { vmImage: ubuntu-latest }
        steps:
          - checkout: self
            fetchDepth: 0

          - task: UsePythonVersion@0
            inputs: { versionSpec: '3.12' }

          - task: Cache@2
            inputs:
              key: 'pip | "$(Agent.OS)" | requirements.txt | requirements-dev.txt'
              restoreKeys: 'pip | "$(Agent.OS)"'
              path: $(Pipeline.Workspace)/.cache/pip

          - script: |
              set -euo pipefail
              python -m pip install --upgrade pip
              pip install -r requirements.txt -r requirements-dev.txt
            displayName: Install dependencies
            env: { PIP_CACHE_DIR: $(Pipeline.Workspace)/.cache/pip }

          - script: |
              set -euo pipefail
              ruff check app tests
              mypy app
            displayName: Lint + type check

          - script: |
              set -euo pipefail
              pytest tests/unit -n auto \
                --junitxml=junit-unit.xml \
                --cov=app --cov-report=xml:coverage.xml --cov-fail-under=80
            displayName: Unit tests

          - script: |
              set -euo pipefail
              uvicorn app.main:app --host 127.0.0.1 --port 8000 &
              APP_PID=$!
              trap 'kill $APP_PID' EXIT
              for _ in $(seq 1 30); do
                curl -sf http://127.0.0.1:8000/healthz && break
                sleep 1
              done
              pytest tests/contract --junitxml=junit-contract.xml
              schemathesis run http://127.0.0.1:8000/openapi.json --checks all
            displayName: Contract tests + OpenAPI fuzz

          - script: gitleaks detect --source . --redact --no-banner --exit-code 1
            displayName: 'Secrets: gitleaks'

          - script: bandit -r app -ll -ii -f json -o bandit.json
            displayName: 'SAST: bandit'

          - script: |
              set -euo pipefail
              pip install pip-audit
              pip-audit -r requirements.txt --strict --format json --output pip-audit.json
            displayName: 'SCA: pip-audit'

          - task: PublishTestResults@2
            condition: succeededOrFailed()
            inputs:
              testResultsFiles: 'junit-*.xml'
              testRunTitle: 'payments-adapter $(Build.BuildNumber)'

          - task: PublishCodeCoverageResults@2
            condition: succeededOrFailed()
            inputs: { summaryFileLocation: coverage.xml }

      - job: image
        displayName: Build image, scan, sign, push
        dependsOn: test
        pool: { vmImage: ubuntu-latest }
        steps:
          - checkout: self

          - script: |
              set -euo pipefail
              docker buildx create --use --name builder
              docker buildx build \
                --provenance=true --sbom=true \
                --cache-from type=registry,ref=$(acrLoginServer)/cache/payments-adapter \
                --cache-to   type=registry,ref=$(acrLoginServer)/cache/payments-adapter,mode=max \
                --load -t $(acrLoginServer)/$(imageRepo):$(tag) .
            displayName: docker buildx build

          - script: |
              set -euo pipefail
              trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed \
                --format sarif -o trivy.sarif \
                $(acrLoginServer)/$(imageRepo):$(tag)
            displayName: 'Image scan: trivy (blocking)'

          - task: AzureCLI@2
            name: push
            displayName: Push, sign, attest SBOM
            inputs:
              azureSubscription: sc-wif-acr-push
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail
                az acr login --name $(acrName)
                docker push $(acrLoginServer)/$(imageRepo):$(tag)

                DIGEST=$(az acr manifest show-metadata \
                  --name $(acrLoginServer)/$(imageRepo):$(tag) --query digest -o tsv)
                IMG="$(acrLoginServer)/$(imageRepo)@${DIGEST}"

                syft "$IMG" -o cyclonedx-json=sbom.cdx.json
                cosign sign --yes "$IMG"
                cosign attest --yes --predicate sbom.cdx.json --type cyclonedx "$IMG"

                echo "##vso[task.setvariable variable=imageDigest;isOutput=true]${DIGEST}"

  # ── 2. INFRASTRUCTURE: PLAN (always) / APPLY (gated) ───────────────────────
  - stage: infra_plan
    displayName: Terraform plan
    dependsOn: build_and_scan
    jobs:
      - job: plan
        pool: { name: fs-selfhosted-linux }     # state account is Private Link only
        steps:
          - checkout: self
          - task: AzureCLI@2
            displayName: init + validate + plan
            inputs:
              azureSubscription: sc-wif-integration-prod
              scriptType: bash
              scriptLocation: inlineScript
              addSpnToEnvironment: true
              inlineScript: |
                set -euo pipefail
                export ARM_USE_OIDC=true ARM_USE_AZUREAD=true
                export ARM_CLIENT_ID="$servicePrincipalId"
                export ARM_OIDC_TOKEN="$idToken"
                export ARM_TENANT_ID="$tenantId"
                export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"

                cd infra/envs/prod
                terraform init -input=false
                terraform fmt -check -recursive
                terraform validate
                terraform plan -input=false -lock-timeout=5m -out=tfplan
                terraform show -json tfplan > tfplan.json
                terraform show -no-color tfplan > plan.txt

          - script: |
              set -euo pipefail
              pip install checkov
              checkov -f infra/envs/prod/tfplan.json --framework terraform_plan --quiet --compact
              conftest test --policy policy/terraform infra/envs/prod/tfplan.json
            displayName: 'IaC policy: checkov + OPA (blocking)'

          - publish: infra/envs/prod/tfplan
            artifact: tfplan

  - stage: infra_apply
    displayName: Terraform apply (approval-gated)
    dependsOn: infra_plan
    jobs:
      - deployment: apply
        environment: infra-prod        # approvals + business hours + ServiceNow check
        pool: { name: fs-selfhosted-linux }
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - download: current
                  artifact: tfplan
                - task: AzureCLI@2
                  displayName: terraform apply (the saved plan, not a fresh one)
                  inputs:
                    azureSubscription: sc-wif-integration-prod
                    scriptType: bash
                    scriptLocation: inlineScript
                    addSpnToEnvironment: true
                    inlineScript: |
                      set -euo pipefail
                      export ARM_USE_OIDC=true ARM_USE_AZUREAD=true
                      export ARM_CLIENT_ID="$servicePrincipalId"
                      export ARM_OIDC_TOKEN="$idToken"
                      export ARM_TENANT_ID="$tenantId"
                      export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
                      cd infra/envs/prod
                      terraform init -input=false
                      terraform apply -input=false -auto-approve \
                        "$(Pipeline.Workspace)/tfplan/tfplan"

  # ── 3. APPLICATION DEPLOY ──────────────────────────────────────────────────
  - stage: deploy_prod
    displayName: Deploy to AKS
    dependsOn: [build_and_scan, infra_apply]
    condition: succeeded()
    variables:
      imageDigest: $[ stageDependencies.build_and_scan.image.outputs['push.imageDigest'] ]
    jobs:
      - deployment: helm
        environment: aks-prod.payments
        pool: { name: fs-selfhosted-linux }
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - task: AzureCLI@2
                  displayName: helm upgrade --atomic
                  inputs:
                    azureSubscription: sc-wif-aks-prod
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      set -euo pipefail
                      az aks get-credentials -g rg-int-prod -n aks-int-prod --overwrite-existing
                      kubelogin convert-kubeconfig -l workloadidentity
                      helm upgrade --install payments-adapter \
                        oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
                        --namespace payments \
                        --values apps/payments-adapter/values-prod.yaml \
                        --set image.digest="$(imageDigest)" \
                        --atomic --timeout 5m --wait
```

Two details worth pointing at while you talk through it: `terraform apply` consumes **the saved plan file**, not a freshly-computed one, so the thing the approver looked at is the thing that runs; and the cross-stage output variable syntax `$[ stageDependencies.<stage>.<job>.outputs['<step>.<var>'] ]` is how the digest survives a stage boundary.

**If they push back — "Why is Terraform in the same pipeline as the app?"** — In this example it's for readability. In practice I separate them: infrastructure has a different change cadence, a different approver and a different blast radius from application code, so it gets its own repo and pipeline. Coupling them means a routine app deploy requires an infrastructure approval, which is how you teach people to rubber-stamp approvals. The join between them is a published contract — outputs from the infra state consumed as inputs to the app deploy.

---

### Q30. What are variable groups, and how do you link one to Key Vault?
`[EASY]`

**Answer:** A variable group is a named set of variables in the Library, shared across pipelines, with its own permissions. Linking it to Key Vault means the *values* stay in Key Vault and Azure DevOps holds only the reference — at run time the pipeline fetches them with the service connection's identity. That gives you Key Vault's audit log of every secret read, its rotation, its soft-delete, and one place to revoke.

```yaml
variables:
  - group: payments-adapter-prod   # linked to kv-eyint-prod via a WIF service connection
  - name: nonSecretThing
    value: 'fine in YAML'

steps:
  - script: |
      set -euo pipefail
      # secrets are NOT auto-mapped into the env for script steps — map explicitly
      curl -sS -H "X-API-Key: ${PARTNER_API_KEY}" https://partner.example.com/v1/ping
    env:
      PARTNER_API_KEY: $(partner-api-key)   # secret variable, masked in logs
```

**If they push back — "Secrets get masked in logs anyway, so what's the risk?"** — Masking is best-effort string replacement, and it's easy to defeat accidentally: base64 the value, split it across lines, write it to a file the next task uploads as an artifact. Masking is a safety net, not a control. The control is that the secret exists in exactly one place with an audit log, is short-lived, and ideally doesn't exist at all because you used workload identity federation instead.

---

### Q31. `dependsOn` and `condition` — how do you express "deploy only from main, only if tests passed"?
`[MEDIUM]`

**Answer:** `dependsOn` builds the DAG; `condition` decides whether the node runs when its dependencies complete. The key gotcha is that **specifying any `condition` replaces the implicit `succeeded()`**, so a condition that only checks the branch will run the stage even after a failure. You must AND them.

```yaml
- stage: deploy_prod
  dependsOn: [build_and_scan, infra_apply]
  # WRONG: this deploys even if build_and_scan failed
  # condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')
  condition: >-
    and(
      succeeded(),
      eq(variables['Build.SourceBranch'], 'refs/heads/main'),
      ne(variables['Build.Reason'], 'PullRequest')
    )
```

Also worth knowing: `dependsOn: []` makes a stage or job start immediately in parallel with everything else, which is how you fan out scans; and `succeededOrFailed()` vs `always()` differ on cancellation — `always()` runs even when the run is cancelled, which is what you want for a cleanup step that tears down a test environment.

**If they push back — "How do you deploy the same commit to two regions in parallel?"** — Two deployment jobs in one stage with no `dependsOn` between them, each targeting its own environment, both consuming the same `imageDigest` output. If the client wants sequential region rollout with a soak, that's two stages with the second depending on the first and a `pause`/manual validation job between — or, better, hand it to Argo Rollouts and let the metric analysis decide.

---

### Q32. What is a service connection and how do you stop it being over-privileged?
`[MEDIUM]`

**Answer:** A service connection is a stored identity plus endpoint definition that pipelines use to reach something outside Azure DevOps — a subscription, ACR, a Kubernetes cluster, SonarQube. The over-privilege failure is always the same shape: one Contributor-on-the-whole-subscription connection shared by every pipeline, with *Grant access permission to all pipelines* ticked.

The fix is four rules. **One connection per environment per purpose** — separate `sc-wif-acr-push` from `sc-wif-aks-prod` from `sc-wif-integration-prod`. **Least privilege RBAC** scoped to a resource group, not a subscription, with a custom role where the built-ins are too broad. **Never grant to all pipelines** — authorise each pipeline explicitly. And **workload identity federation** so there's no secret behind it at all.

**If they push back — "Contributor is convenient though — what would you actually scope down?"** — The two that matter most in an integration platform: the deploy identity does not need `Microsoft.Authorization/roleAssignments/write` (that's how a Contributor escalates to Owner), and the app deploy identity does not need write on the state storage account. I'd start from Contributor-minus-role-assignments on the workload resource group, then split the Terraform identity (which *does* need to create role assignments, so it gets **User Access Administrator** scoped to that one resource group and nothing else) from the app deploy identity, which needs almost nothing.

---

### Q33. Azure DevOps or GitHub Actions — which would you recommend to a client?
`[MEDIUM]` `[opinion question; EY logged "Convince me to adopt AWS" — persuasion is tested]`

**Answer:** For a large financial-services enterprise today I'd usually land on **Azure DevOps for the release plane and GitHub for the code plane**, and I'd say so explicitly rather than pretending one wins outright. Azure DevOps has the governance primitives that survive an audit: environments with typed checks, the required-template check, exclusive locks, ServiceNow change integration, and per-service-connection authorisation. GitHub Actions has the better developer experience, the richer marketplace, far more expressive OIDC subject claims, and it's where Microsoft's investment is going.

The decision criteria I'd actually put to the client: where does the code already live; is there a hard four-eyes/change-management requirement that ADO's checks satisfy out of the box; do you need self-hosted runners in a VNet (both do it, ADO's pool model is more mature); and what's the five-year direction — GitHub Enterprise plus Actions is where the platform is heading, so a greenfield programme starting today I'd put on GitHub.

| | Azure DevOps Pipelines | GitHub Actions |
|---|---|---|
| Governance | environments + checks (required template, exclusive lock, ServiceNow, business hours) | environments + required reviewers, wait timer, branch policies, rulesets |
| Reuse | templates + `extends` (inversion of control) | reusable workflows + composite actions (call, not extends) |
| OIDC | service connection with WIF; subject = org/project/connection | subject includes repo, ref, environment, `job_workflow_ref` — much finer |
| Job limits | 60 min free / **360 min** paid (MS-hosted) | **6 h** (GitHub-hosted), 5 days (self-hosted) |
| Marketplace | smaller, more curated | very large, and that's a supply-chain surface |
| Best at | regulated release management | developer velocity, open ecosystem |

**If they push back — "Pick one. Now defend it."** — GitHub Actions, for a new build. The governance gap has closed far enough — environments, rulesets, OIDC with environment-scoped subjects, artifact attestations, and required workflows — while the ecosystem and the talent pool have not. The one condition I'd attach: pin every third-party action to a **commit SHA**, not a tag, and mirror the ones you depend on. That's the real risk with Actions, and it's manageable. If the client's audit function has already certified Azure DevOps and has a working ServiceNow integration, I would not spend the programme's political capital moving it — that's a migration with no business outcome.

---

## 7. GitHub Actions

### Q34. Walk me through the workflow syntax.
`[EASY]`

**Answer:** A workflow is a YAML file in `.github/workflows/`. It has `on` (events — `push`, `pull_request`, `workflow_dispatch`, `schedule`, `workflow_call`), `permissions` (the `GITHUB_TOKEN` scopes), `concurrency`, and `jobs`. Each job declares `runs-on`, optional `needs` for the DAG, optional `strategy.matrix`, its own `permissions` and `environment`, and a list of `steps` that are either `uses:` (an action) or `run:` (shell). Jobs are isolated VMs; steps share one.

The three things that most distinguish a competent workflow from a naive one: an explicit `permissions` block, `concurrency` to cancel superseded PR runs, and third-party actions pinned to a SHA.

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, uat, prod]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/unit --junitxml=junit-${{ matrix.python }}.xml
```

Note `cancel-in-progress` is conditional: cancelling superseded PR runs saves minutes, but cancelling a superseded `main` deploy mid-flight is how you get a half-applied change.

**If they push back — "Why pin to a SHA instead of `@v4`?"** — Because a tag is mutable. Whoever controls the action's repository can move `v4` to new code, and that code runs on your runner with your `GITHUB_TOKEN` and your OIDC token. There have been real incidents of exactly this. A SHA is immutable, and Dependabot updates SHA pins for you with a diff you review. For `actions/*` published by GitHub the risk is lower, but for anything third-party a SHA pin is table stakes.

---

### Q35. Reusable workflows vs composite actions — when do you use each?
`[HARD]` `[the platform-engineering answer for GitHub]`

**Answer:** A **composite action** packages a sequence of *steps* and gets inlined into a caller's job — it shares that job's runner, filesystem and permissions. A **reusable workflow** is called with `uses:` at the *job* level: it brings its own jobs, its own runners, its own `permissions`, and can itself contain multiple jobs, environments and matrices.

So: composite action for a chunk of steps you repeat inside jobs — "set up Python, restore cache, install deps". Reusable workflow for the whole delivery pipeline you want forty repos to share — because only the reusable workflow can own the job structure, the environment gates and the permission boundaries, which is where the governance lives.

The verified limits: you can chain **a maximum of ten levels** (the caller plus up to nine reusable workflows), loops are prohibited, `secrets: inherit` passes the caller's secrets implicitly, and **environment secrets cannot be passed via `workflow_call`** because it doesn't support the `environment` keyword.

```yaml
# eygds/platform-workflows/.github/workflows/integration-service.yml  (platform-owned)
name: integration-service
on:
  workflow_call:
    inputs:
      service-name:   { required: true,  type: string }
      python-version: { required: false, type: string, default: '3.12' }
      acr-name:       { required: true,  type: string }
      deploy-environment: { required: true, type: string }
    secrets:
      SONAR_TOKEN: { required: false }
    outputs:
      image-digest:
        description: Immutable digest of the published image
        value: ${{ jobs.image.outputs.digest }}

permissions: {}

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check app tests && mypy app
      - run: pytest tests/unit -n auto --cov=app --cov-report=xml --cov-fail-under=80
      - run: bandit -r app -ll -ii
      - run: pip install pip-audit && pip-audit -r requirements.txt --strict
      - uses: gitleaks/gitleaks-action@v2
        env: { GITLEAKS_ENABLE_UPLOAD_ARTIFACT: 'false' }

  image:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write          # OIDC to Azure AND keyless cosign
      packages: read
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: ACR login
        run: az acr login --name ${{ inputs.acr-name }}

      - uses: docker/setup-buildx-action@v3

      - name: Build (load locally so we can scan before publishing)
        run: |
          set -euo pipefail
          docker buildx build --load \
            --provenance=true --sbom=true \
            -t ${{ inputs.acr-name }}.azurecr.io/integration/${{ inputs.service-name }}:${{ github.sha }} .

      - name: Trivy (blocking)
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: ${{ inputs.acr-name }}.azurecr.io/integration/${{ inputs.service-name }}:${{ github.sha }}
          exit-code: '1'
          severity: 'HIGH,CRITICAL'
          ignore-unfixed: true
          format: 'sarif'
          output: 'trivy.sarif'

      - name: Push, sign, attest
        id: push
        run: |
          set -euo pipefail
          IMAGE=${{ inputs.acr-name }}.azurecr.io/integration/${{ inputs.service-name }}
          docker push "$IMAGE:${{ github.sha }}"
          DIGEST=$(az acr manifest show-metadata --name "$IMAGE:${{ github.sha }}" --query digest -o tsv)
          syft "$IMAGE@$DIGEST" -o cyclonedx-json=sbom.cdx.json
          cosign sign --yes "$IMAGE@$DIGEST"
          cosign attest --yes --predicate sbom.cdx.json --type cyclonedx "$IMAGE@$DIGEST"
          echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"

  deploy:
    needs: image
    runs-on: [self-hosted, linux, vnet]   # private AKS API server
    environment: ${{ inputs.deploy-environment }}   # required reviewers live here
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - name: Helm deploy
        run: |
          set -euo pipefail
          az aks get-credentials -g rg-int-prod -n aks-int-prod --overwrite-existing
          kubelogin convert-kubeconfig -l workloadidentity
          helm upgrade --install ${{ inputs.service-name }} \
            oci://${{ inputs.acr-name }}.azurecr.io/helm/integration-service --version 3.4.1 \
            --namespace payments \
            --values apps/${{ inputs.service-name }}/values-${{ inputs.deploy-environment }}.yaml \
            --set image.digest=${{ needs.image.outputs.digest }} \
            --atomic --timeout 5m --wait
```

```yaml
# eygds/payments-adapter/.github/workflows/ci.yml  — the whole product-team workflow
name: payments-adapter
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  delivery:
    uses: eygds/platform-workflows/.github/workflows/integration-service.yml@v3.2.0
    permissions:
      contents: read
      id-token: write
      packages: read
    with:
      service-name: payments-adapter
      acr-name: eyintacr
      deploy-environment: prod
    secrets: inherit
```

**If they push back — "GitHub has no `extends`, so how do you enforce it?"** — Two mechanisms. **Required workflows** (org-level rulesets) force a specific workflow to run on every PR in the selected repos, and it can't be edited by the repo. And the harder boundary: federate the deploy identity's trust on `job_workflow_ref`, so Entra ID only issues a token when the job came from `eygds/platform-workflows/.github/workflows/integration-service.yml`. A team can write any workflow they like; only the platform's workflow can get a prod token. That's cryptographic enforcement, which is stronger than ADO's required-template check.

---

### Q36. What's a matrix build and when does it bite you?
`[EASY]`

**Answer:** `strategy.matrix` fans one job definition into N parallel jobs over a cartesian product of variables — Python versions, OSes, target regions. `include` adds specific combinations, `exclude` removes them, `fail-fast: false` keeps the rest running when one fails, and `max-parallel` throttles.

Where it bites: the cap is **256 jobs per workflow run**, and concurrency is limited by plan (Free 20, Team 60, Enterprise 500 concurrent jobs) — so a 3×4×5 matrix on a busy org queues rather than parallelises. The subtler bite is when matrix jobs share a mutable resource: two matrix legs both pushing `:latest`, or both running `terraform apply` against the same state, will race. Matrix is for *independent* work.

**If they push back — "How do you get an output from a matrix job?"** — You largely can't, cleanly: with a matrix, a workflow-level output reflects the last successfully-completing leg that set a value, which is nondeterministic. The correct pattern is for each leg to upload a uniquely-named artifact, and a following job with `needs:` to download all of them and aggregate. I'd never depend on matrix job outputs for something like a digest.

---

### Q37. Explain `environment` in GitHub Actions.
`[MEDIUM]`

**Answer:** An environment is a named deployment target carrying protection rules — required reviewers, a wait timer, deployment branch/tag policies — plus environment-scoped secrets and variables. A job that declares `environment: prod` pauses before it starts until the rules pass, and only then can it read that environment's secrets and mint an OIDC token whose `sub` is `repo:ORG/REPO:environment:prod`.

That last part is the one to emphasise: the environment isn't just a UI gate, it changes the *identity* of the job. Federate prod access on the environment subject and a job that skipped the environment simply cannot authenticate.

**If they push back — "Required reviewers can approve their own PR's deployment."** — By default a reviewer can approve their own run, and for four-eyes you have to prevent that. GitHub has a "prevent self-review" setting on environments; enable it. Combine with a CODEOWNERS-based review requirement on the config and a deployment branch policy restricted to `main`, so the person merging and the person approving the deployment are different humans with an audit record of both.

---

### Q38. `needs`, `if`, and job outputs — show me a conditional deploy.
`[MEDIUM]`

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      app-changed:   ${{ steps.filter.outputs.app }}
      infra-changed: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            app:
              - 'app/**'
              - 'requirements*.txt'
              - 'Dockerfile'
            infra:
              - 'infra/**'

  build:
    needs: detect
    if: needs.detect.outputs.app-changed == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "building"

  terraform:
    needs: detect
    if: needs.detect.outputs.infra-changed == 'true'
    runs-on: [self-hosted, linux, vnet]
    steps:
      - run: echo "planning"

  deploy:
    needs: [build, terraform]
    # both upstreams may be SKIPPED; !failure() && !cancelled() lets that through
    if: >-
      github.ref == 'refs/heads/main'
      && !failure() && !cancelled()
    runs-on: [self-hosted, linux, vnet]
    environment: prod
    steps:
      - run: echo "deploying"
```

The trap embedded there: a job whose `needs` were **skipped** is itself skipped by default. `always()` is too broad because it also runs after a cancellation. `!failure() && !cancelled()` is the expression that means "proceed unless something actually went wrong."

**If they push back — "Why not just always run everything?"** — On a monorepo with twenty services, always-run turns a one-line README change into forty minutes of compute and forty deployments, each with its own small chance of failing. Path filtering keeps the signal honest. The caveat is that path filters must be conservative: if a shared library changes, everything downstream of it must rebuild, so I keep the filters coarse rather than clever.

---

### Q39. How do you post a `terraform plan` into the PR?
`[MEDIUM]` `[very common real-world ask]`

```yaml
name: terraform-plan
on:
  pull_request:
    paths: ['infra/**']

permissions:
  contents: read

jobs:
  plan:
    runs-on: [self-hosted, linux, vnet]
    permissions:
      contents: read
      id-token: write          # OIDC to a READ-ONLY Azure identity
      pull-requests: write     # only this job may comment
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.8
          terraform_wrapper: false

      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_PLAN_CLIENT_ID }}   # Reader + state blob read
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: Plan
        id: plan
        env:
          ARM_USE_OIDC: 'true'
          ARM_USE_AZUREAD: 'true'
          ARM_CLIENT_ID: ${{ vars.AZURE_PLAN_CLIENT_ID }}
          ARM_TENANT_ID: ${{ vars.AZURE_TENANT_ID }}
          ARM_SUBSCRIPTION_ID: ${{ vars.AZURE_SUBSCRIPTION_ID }}
        run: |
          set -euo pipefail
          cd infra/envs/nonprod
          terraform init -input=false
          terraform plan -input=false -lock-timeout=5m -no-color -out=tfplan | tee plan.txt
          terraform show -json tfplan > tfplan.json
          {
            echo 'summary<<TFEOF'
            grep -E '^(Plan:|No changes)' plan.txt || echo 'Plan: (see details)'
            echo TFEOF
          } >> "$GITHUB_OUTPUT"

      - name: Policy check
        run: conftest test --policy ../../../policy/terraform infra/envs/nonprod/tfplan.json

      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('infra/envs/nonprod/plan.txt', 'utf8');
            const clipped = plan.length > 60000 ? plan.slice(0, 60000) + '\n...truncated...' : plan;
            const body = `### Terraform plan — nonprod\n\n${{ toJSON(steps.plan.outputs.summary) }}\n\n<details><summary>Full plan</summary>\n\n\`\`\`hcl\n${clipped}\n\`\`\`\n\n</details>`;
            const { data: comments } = await github.rest.issues.listComments({
              ...context.repo, issue_number: context.issue.number,
            });
            const mine = comments.find(c => c.user.type === 'Bot' && c.body.startsWith('### Terraform plan — nonprod'));
            if (mine) {
              await github.rest.issues.updateComment({ ...context.repo, comment_id: mine.id, body });
            } else {
              await github.rest.issues.createComment({ ...context.repo, issue_number: context.issue.number, body });
            }
```

The identity used for plan is **read-only**. That's the whole security design of plan-in-PR: a plan needs to read the world and the state, nothing more, so a malicious PR that manages to influence the plan step still can't change anything.

**If they push back — "What about Atlantis or Terraform Cloud?"** — Atlantis is a self-hosted server that listens to PR webhooks, runs plan, comments, and applies on `atlantis apply` — it centralises the runner and the state locking so you don't hand every repo an apply identity. Terraform Cloud/HCP Terraform adds hosted state, a private module registry, run tasks and **Sentinel** policy. Both are good; the reason I'd often not use them at an EY client is that they add a vendor and a network path into a locked-down environment, and Azure DevOps environments plus a storage-account backend plus Conftest gives you 90% of it with nothing new to onboard. If the estate has more than about fifty Terraform workspaces, the calculus flips and HCP Terraform's registry and run-task model earns its keep.

---

### Q40. What's the `GITHUB_TOKEN` and what can it not do?
`[EASY]`

**Answer:** It's an installation access token minted per workflow run, scoped to the repository, expiring when the run ends, with permissions set by the `permissions` block. It can do most repo-level API work — comment, create a check run, push to the repo if granted `contents: write`.

What it **cannot** do, and this catches people: a push made with `GITHUB_TOKEN` **does not trigger further workflows** (deliberate, to prevent infinite loops); it can't reach other repositories; and it can't do org-level administration. When you genuinely need a commit to trigger downstream workflows — a GitOps bump commit is the classic case — you use a GitHub App installation token or a fine-grained PAT stored as a secret, and you accept that as a deliberate, scoped exception.

**If they push back — "So how do you do a GitOps image bump from CI?"** — Either push to the config repo with a GitHub App token scoped to that one repo (so ArgoCD, not a workflow, picks it up — no downstream workflow needed, so the restriction doesn't bite), or better, don't push from CI at all: let **Flux's image automation controllers** or **Argo CD Image Updater** watch the registry and write the commit themselves. That removes the write credential from CI entirely, which is the more defensible design. See §11.

---

## 8. Jenkins and GitLab CI — enough to be credible

> Be honest about depth here. The line that works: *"Azure DevOps and GitHub Actions in anger; Jenkins and GitLab CI I can read, maintain and migrate off."* Then prove the "read and maintain" with the detail below.

### Q41. Declarative vs scripted Jenkinsfile — what's the difference?
`[MEDIUM]`

**Answer:** **Scripted** is raw Groovy — a `node { }` block where you write imperative code. Maximum power, no structure, and the pipeline becomes a program only its author understands. **Declarative** wraps it in a `pipeline { }` schema with fixed sections — `agent`, `stages`, `steps`, `post`, `options`, `environment`, `when`, `input` — which is validatable, restartable-from-stage, and readable. Declarative is the default for anything new; you drop into `script { }` blocks for the rare imperative bit.

```groovy
// Jenkinsfile — declarative
@Library('integration-platform@v3.2.0') _     // the shared library IS the paved road

pipeline {
    agent none
    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        timestamps()
    }
    environment {
        IMAGE = 'eyintacr.azurecr.io/integration/payments-adapter'
        TAG   = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(8)}"
    }
    stages {
        stage('Build & test') {
            agent { docker { image 'python:3.12-slim'; args '-u root' } }
            steps {
                sh '''
                    set -euo pipefail
                    pip install -r requirements.txt -r requirements-dev.txt
                    pytest tests/unit --junitxml=junit.xml --cov=app --cov-report=xml
                    bandit -r app -ll -ii -f json -o bandit.json
                    pip-audit -r requirements.txt --strict --format json --output pip-audit.json
                '''
            }
            post {
                always {
                    junit 'junit.xml'
                    archiveArtifacts artifacts: 'bandit.json,pip-audit.json', fingerprint: true
                }
            }
        }

        stage('Image') {
            agent { label 'docker-linux' }
            steps {
                script {
                    // shared library step: build + trivy + push + cosign, one call
                    integrationImage.buildScanPush(image: env.IMAGE, tag: env.TAG,
                                                   severityGate: 'HIGH,CRITICAL')
                }
            }
        }

        stage('Deploy prod') {
            when { branch 'main' }
            agent { label 'docker-linux' }
            input {
                message 'Deploy payments-adapter to production?'
                ok 'Deploy'
                submitter 'release-managers'          // four-eyes, by AD group
            }
            steps {
                withCredentials([azureServicePrincipal('sp-aks-prod')]) {
                    sh '''
                        set -euo pipefail
                        az login --service-principal -u "$AZURE_CLIENT_ID" \
                                 -p "$AZURE_CLIENT_SECRET" -t "$AZURE_TENANT_ID"
                        az aks get-credentials -g rg-int-prod -n aks-int-prod --overwrite-existing
                        helm upgrade --install payments-adapter \
                          oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
                          --namespace payments --set image.tag="$TAG" \
                          --atomic --timeout 5m --wait
                    '''
                }
            }
        }
    }
    post {
        failure {
            emailext to: 'integration-oncall@ey.com',
                     subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                     body: "${env.BUILD_URL}"
        }
    }
}
```

**Shared libraries** are Jenkins' answer to templates — a Git repo with `vars/integrationImage.groovy` defining a global step, loaded with `@Library`. That's the platform-engineering hook: the security controls live in the library, the Jenkinsfile calls one step. Jenkins can't *force* it the way ADO's required template can, so you enforce it with credential scoping — only the library's step knows the ACR push credential — plus a Jenkinsfile linting job.

**If they push back — "Why do teams migrate off Jenkins?"** — Four reasons, in the order clients say them: plugin sprawl and the upgrade fragility that comes with it (a Jenkins upgrade breaks three plugins and a weekend); the controller is a stateful pet that needs backups, patching and its own DR story; Groovy sandbox and script-approval friction; and the fact that a self-managed controller with hundreds of plugins is a genuinely large attack surface for something that holds every deployment credential in the estate. What Jenkins still wins on: it runs anywhere, including air-gapped, and it can do things a hosted YAML system can't. I wouldn't rip it out on principle — I'd migrate the pipelines that fit a hosted model and leave the exotic ones.

---

### Q42. Show me a GitLab CI pipeline.
`[MEDIUM]`

```yaml
# .gitlab-ci.yml
stages: [test, scan, package, deploy]

default:
  image: python:3.12-slim
  interruptible: true
  retry:
    max: 2
    when: [runner_system_failure, stuck_or_timeout_failure]

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  IMAGE: "$CI_REGISTRY_IMAGE/payments-adapter"

cache:
  key:
    files: [requirements.txt, requirements-dev.txt]
  paths: [.cache/pip]

.python: &python
  before_script:
    - pip install -r requirements.txt -r requirements-dev.txt

unit:
  <<: *python
  stage: test
  script:
    - pytest tests/unit --junitxml=report.xml --cov=app --cov-report=xml:coverage.xml
  artifacts:
    when: always
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

sast:
  <<: *python
  stage: scan
  needs: []                       # DAG: start immediately, don't wait for `test`
  script:
    - bandit -r app -ll -ii -f json -o bandit.json
    - pip-audit -r requirements.txt --strict
  artifacts:
    paths: [bandit.json]

package:
  stage: package
  image: docker:27-cli
  services: [docker:27-dind]
  needs: [unit]
  script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
    - docker build -t "$IMAGE:$CI_COMMIT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHA"

container_scan:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  needs: [package]
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed "$IMAGE:$CI_COMMIT_SHA"

deploy_prod:
  stage: deploy
  image: alpine/helm:3.16.2
  needs: [container_scan]
  environment:
    name: production
    url: https://payments.internal.ey.net
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
      when: manual                # the four-eyes gate
      allow_failure: false
    - when: never
  script:
    - helm upgrade --install payments-adapter oci://eyintacr.azurecr.io/helm/integration-service
        --version 3.4.1 --namespace payments
        --set image.tag="$CI_COMMIT_SHA" --atomic --timeout 5m --wait
```

The two things to name: `rules:` replaced the older `only/except` and is far more expressive (`if`, `changes`, `exists`, `when: manual`), and `needs:` turns the stage list into a **DAG** so a scan job doesn't wait for an unrelated stage to finish. GitLab's reuse primitives are `extends:`, YAML anchors, and `include:` (local, project, remote, or template) — `include` from a central compliance project is GitLab's equivalent of the governance template, and **compliance pipelines** can force it.

**If they push back — "GitLab CI vs GitHub Actions?"** — GitLab is one integrated product — SCM, CI, registry, package registry, security dashboards, environments — which is a real advantage for a mid-size client who doesn't want to assemble four tools. GitHub Actions has the bigger ecosystem and the better OIDC story. For an EY financial-services engagement, the deciding factor is usually what the client already runs and what their security team has already assessed, not which YAML dialect is nicer.

---

### Q43. Translate the same concept across all four tools.
`[EASY]` `[worth memorising as a table — it makes you sound tool-agnostic]`

| Concept | Azure DevOps | GitHub Actions | GitLab CI | Jenkins |
|---|---|---|---|---|
| Pipeline file | `azure-pipelines.yml` | `.github/workflows/*.yml` | `.gitlab-ci.yml` | `Jenkinsfile` |
| Grouping | stage → job → step | job → step | stage → job → script | stage → steps |
| Parallel DAG | `dependsOn` | `needs` | `needs` | `parallel { }` |
| Reuse | template + `extends` | reusable workflow / composite action | `include` + `extends` | shared library |
| Where it runs | pool / agent | `runs-on` | runner tag | `agent { label }` |
| Gate | environment checks | environment protection rules | `when: manual` + protected env | `input` directive |
| Secrets | variable group → Key Vault | secrets / OIDC | CI/CD variables (masked, protected) | credentials plugin |
| Artefacts | `publish` / `download` | upload/download-artifact | `artifacts:` | `archiveArtifacts` |
| Matrix | `strategy: matrix` | `strategy.matrix` | `parallel: matrix` | `matrix { }` |

---

### Q44. A client has pipelines in all four. What do you do?
`[MEDIUM]` `[EY-consulting-shaped]`

**Answer:** I don't start with the tools. I start by writing down what the *controls* are — every production deployment is scanned, signed, four-eyes approved, and auditable — because those must hold in all four regardless of what we consolidate. Then I implement them in each tool as a shared template/library, so compliance is achieved before any migration begins. Only then do I look at consolidation, and I'd sequence it by pain: the tool with the most operational cost and the least strategic fit goes first, and I'd expect to leave at least one behind because some team has a genuine reason.

The consulting framing: consolidation is a cost programme, not a compliance programme. Don't sell it as security, because the moment you do, you've committed to a two-year migration to get something you could have had in six weeks.

**If they push back — "Give me the six-week version."** — One shared scanning and signing step implemented four ways, called from every pipeline; a single artefact registry (ACR) that all four push to, with tag immutability and signature-required policy; and admission control in the clusters that refuses anything unsigned. That last one is the lever: whatever the pipeline is, if it can't produce a signed image from a protected branch, nothing runs. You get the control without touching the pipelines.

---

## 9. Terraform

### Q45. What is Terraform and what is the core workflow?
`[EASY]` `[NEAR-CERTAIN opener]`

**Answer:** Terraform is a declarative, provider-based infrastructure-as-code tool: you write the desired state in HCL, Terraform reads the actual state through a provider's API, diffs the two against a recorded state file, and produces a plan of creates, updates, replacements and destroys. The loop is `init` (download providers and configure the backend), `validate`, `plan`, `apply`, and `destroy`. It's cloud-agnostic in the sense that one language and one workflow drive 4,000+ providers — not in the sense that a configuration is portable between clouds, which it isn't.

The single most important property to name: **the plan is a first-class artefact.** You can review it, gate on it, run policy against it, and apply exactly it. That's what makes Terraform auditable in a way that a `az cli` script never is.

```bash
terraform init -input=false            # providers + backend
terraform fmt -recursive               # canonical formatting
terraform validate                     # syntax + type checking, no API calls
terraform plan -out=tfplan             # save the plan as a file
terraform show -json tfplan > p.json   # machine-readable, for policy
terraform apply tfplan                 # apply exactly what was reviewed
```

**If they push back — "Is Terraform still open source?"** — HashiCorp moved Terraform to the Business Source License in August 2023, which is why the **OpenTofu** fork exists under the Linux Foundation. For a client, the practical questions are: are you a HashiCorp competitor (almost no one is, so BSL doesn't bite), and do you want the fork's governance. I'd default to Terraform for the provider ecosystem and HCP integration, and I'd flag OpenTofu as a viable drop-in if the client's open-source policy requires it. Knowing this exists is a recency signal.

---

### Q46. Providers, resources, data sources, variables, locals, outputs — what's each for?
`[EASY]`

**Answer:** A **provider** is the plugin that talks to an API and must be pinned. A **resource** is something Terraform creates and owns. A **data source** reads something Terraform does *not* own — that's the important distinction, and it's how you consume a platform-team-owned VNet or Log Analytics workspace without taking responsibility for it. **Variables** are inputs with types, defaults and validation. **Locals** are named expressions, computed once, for readability. **Outputs** are the module's public interface.

```hcl
# versions.tf — pin everything. A floating provider is an unreviewed change.
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"     # azurerm 5.x is current as of Aug 2026; upgrade deliberately
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  # azurerm v4+ requires subscription_id explicitly or via ARM_SUBSCRIPTION_ID
  subscription_id = var.subscription_id
  storage_use_azuread = true
}

# data source: the platform team owns this VNet; we only read it
data "azurerm_subnet" "integration" {
  name                 = "snet-integration"
  virtual_network_name = var.vnet_name
  resource_group_name  = var.network_resource_group_name
}

locals {
  name_prefix = "${var.workload}-${var.env}"
  base_tags = merge(var.tags, {
    workload            = var.workload
    environment         = var.env
    managed_by          = "terraform"
    cost_centre         = var.cost_centre
    data_classification = var.data_classification
  })
}

output "service_bus_namespace_id" {
  description = "Consumed by the application deploy pipeline."
  value       = azurerm_servicebus_namespace.this.id
}

output "managed_identity_client_id" {
  description = "Set as AZURE_CLIENT_ID in the workload."
  value       = azurerm_user_assigned_identity.app.client_id
}
```

**If they push back — "When should something be a data source rather than a resource?"** — Ownership, not convenience. If another team's Terraform (or ClickOps, or an Azure Landing Zone deployment) creates and lifecycle-manages it, it's a data source for me. The failure mode of getting this wrong is severe: two configurations both declaring the same resource will fight, each `apply` reverting the other's changes. If I need to *reference* something in the same state that I do own, I reference the resource directly, not through a data source — a data source there introduces an unnecessary read and can create a dependency cycle.

---

### Q47. Show me a real reusable module.
`[HARD]` `[the platform IP question]`

**Answer:** A module is a directory of `.tf` files with typed inputs and documented outputs, versioned and consumed by tag. The platform value is that "I need an integration service" becomes a ten-line call that already encodes managed identity, RBAC, no SAS keys, mandatory tags and private networking — so the compliant path is also the shortest one.

```hcl
# platform-modules/modules/integration-service/variables.tf
variable "workload" {
  description = "Short workload name, e.g. payments-adapter."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,22}$", var.workload))
    error_message = "workload must be lowercase alphanumeric with hyphens, 3-23 chars."
  }
}

variable "env" {
  description = "Environment."
  type        = string
  validation {
    condition     = contains(["dev", "test", "uat", "prod"], var.env)
    error_message = "env must be one of: dev, test, uat, prod."
  }
}

variable "location" {
  description = "Azure region. UK South for FS data-residency workloads."
  type        = string
  default     = "uksouth"
}

variable "resource_group_name" { type = string }
variable "log_analytics_workspace_id" { type = string }
variable "infrastructure_subnet_id" { type = string }
variable "acr_id" { type = string }
variable "acr_login_server" { type = string }
variable "image" {
  description = "Fully qualified image reference, digest-pinned."
  type        = string
}

variable "sb_sku" {
  type    = string
  default = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.sb_sku)
    error_message = "sb_sku must be Standard or Premium. Basic has no topics."
  }
}

variable "sb_capacity" {
  description = "Premium messaging units. Ignored for Standard."
  type        = number
  default     = 1
}

variable "queues" {
  description = "Queue name => settings. Defaults encode the platform's opinions."
  type = map(object({
    max_delivery_count                      = optional(number, 10)
    lock_duration                           = optional(string, "PT1M")
    default_message_ttl                     = optional(string, "P14D")
    requires_session                        = optional(bool, false)
    requires_duplicate_detection            = optional(bool, true)
    duplicate_detection_history_time_window = optional(string, "PT10M")
    max_size_in_megabytes                   = optional(number, 1024)
  }))
  default = {}
}

variable "receive_queues" {
  description = "Subset of queues the app may receive from."
  type        = list(string)
  default     = []
}

variable "send_queues" {
  description = "Subset of queues the app may send to."
  type        = list(string)
  default     = []
}

variable "min_replicas" {
  type    = number
  default = 1
}

variable "max_replicas" {
  type    = number
  default = 10
}
variable "cost_centre" { type = string }
variable "data_classification" {
  type = string
  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
    error_message = "data_classification must be public, internal, confidential or restricted."
  }
}
variable "tags" {
  type    = map(string)
  default = {}
}
```

```hcl
# platform-modules/modules/integration-service/main.tf
locals {
  name_prefix = "${var.workload}-${var.env}"
  is_prod     = var.env == "prod"
  base_tags = merge(var.tags, {
    workload            = var.workload
    environment         = var.env
    managed_by          = "terraform"
    cost_centre         = var.cost_centre
    data_classification = var.data_classification
  })
}

resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${local.name_prefix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = local.base_tags
}

resource "azurerm_servicebus_namespace" "this" {
  name                = "sbns-${local.name_prefix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sb_sku

  capacity                     = var.sb_sku == "Premium" ? var.sb_capacity : 0
  premium_messaging_partitions = var.sb_sku == "Premium" ? 1 : 0

  local_auth_enabled            = false     # no SAS keys, ever — Entra ID + RBAC only
  minimum_tls_version           = "1.2"
  public_network_access_enabled = !local.is_prod

  tags = local.base_tags
}

resource "azurerm_servicebus_queue" "this" {
  for_each = var.queues

  name         = each.key
  namespace_id = azurerm_servicebus_namespace.this.id

  max_delivery_count                      = each.value.max_delivery_count
  lock_duration                           = each.value.lock_duration
  default_message_ttl                     = each.value.default_message_ttl
  requires_session                        = each.value.requires_session
  requires_duplicate_detection            = each.value.requires_duplicate_detection
  duplicate_detection_history_time_window = each.value.duplicate_detection_history_time_window
  max_size_in_megabytes                   = each.value.max_size_in_megabytes

  dead_lettering_on_message_expiration = true   # platform opinion: never silently drop
}

resource "azurerm_container_app_environment" "this" {
  name                           = "cae-${local.name_prefix}"
  resource_group_name            = var.resource_group_name
  location                       = var.location
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  infrastructure_subnet_id       = var.infrastructure_subnet_id
  internal_load_balancer_enabled = local.is_prod
  tags                           = local.base_tags
}

resource "azurerm_container_app" "this" {
  name                         = "ca-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = local.base_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = var.acr_login_server
    identity = azurerm_user_assigned_identity.app.id
  }

  ingress {
    external_enabled = false
    target_port      = 8000
    transport        = "http"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.workload
      image  = var.image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "SERVICEBUS_FQDN"
        value = "${azurerm_servicebus_namespace.this.name}.servicebus.windows.net"
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }
      env {
        name  = "OTEL_SERVICE_NAME"
        value = var.workload
      }

      liveness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/healthz"
      }
      readiness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/readyz"
      }
    }
  }

  lifecycle {
    # Terraform owns the infrastructure; the delivery pipeline owns the image tag.
    # Without this, every terraform apply reverts the app to the last-planned image.
    ignore_changes = [template[0].container[0].image]
  }
}

resource "azurerm_role_assignment" "sb_receiver" {
  for_each = toset(var.receive_queues)

  scope                = azurerm_servicebus_queue.this[each.value].id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "sb_sender" {
  for_each = toset(var.send_queues)

  scope                = azurerm_servicebus_queue.this[each.value].id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}
```

```hcl
# infra/envs/prod/backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-uks"
    storage_account_name = "sttfstateeyint001"
    container_name       = "tfstate"
    key                  = "integration/payments-adapter/prod.tfstate"
    use_azuread_auth     = true    # Entra ID for the data plane, no storage keys
    use_oidc             = true    # federated, no client secret
  }
}
```

```hcl
# infra/envs/prod/main.tf — what a product team actually writes
module "payments_adapter" {
  source = "git::https://dev.azure.com/eygds/Platform/_git/platform-modules//modules/integration-service?ref=v2.4.0"

  workload            = "payments-adapter"
  env                 = "prod"
  location            = "uksouth"
  resource_group_name = "rg-int-prod-uks"
  cost_centre         = "FS-BCM-4471"
  data_classification = "confidential"

  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.platform.id
  infrastructure_subnet_id   = data.azurerm_subnet.integration.id
  acr_id                     = data.azurerm_container_registry.platform.id
  acr_login_server           = data.azurerm_container_registry.platform.login_server
  image                      = "eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b..."

  sb_sku = "Premium"
  queues = {
    "payments-in"  = { requires_session = true, max_delivery_count = 10 }
    "payments-out" = { max_delivery_count = 5, default_message_ttl = "P7D" }
  }
  receive_queues = ["payments-in"]
  send_queues    = ["payments-out"]

  min_replicas = 2
  max_replicas = 20
}
```

**If they push back — "Why not just use the Azure Verified Modules?"** — I do, underneath. Azure Verified Modules (`Azure/avm-res-servicebus-namespace/azurerm` on the registry, `br/public:avm/res/service-bus/namespace:<version>` in Bicep) are Microsoft-maintained resource modules with a consistent interface — they save me writing the resource plumbing. But an AVM is a *resource* module: it gives you a well-formed Service Bus namespace, not an opinion about whether SAS should be disabled or which tags are mandatory at this client. My module is a **pattern** module that composes AVMs and encodes the client's policy. That layering — AVM for resources, my module for the pattern — is the answer that shows you understand the distinction.

---

### Q48. Explain Terraform state. What's in it and why does it matter?
`[HARD]` `[EY-adjacent, very likely]`

**Answer:** State is Terraform's record of the mapping between your configuration and real resources — resource addresses, provider IDs, attribute values, and dependency metadata. It exists because Terraform must know that `azurerm_servicebus_namespace.this` corresponds to *that specific* Azure resource ID, and because it needs the previous attribute values to compute a diff and to order destroys correctly.

Three consequences that matter operationally. **One: state is the source of truth for ownership.** Delete a resource from your config and Terraform destroys it, because state says you own it. **Two: state must be remote, shared and locked** — a local `terraform.tfstate` means two engineers can apply simultaneously and corrupt each other. **Three, and this is the one candidates miss: state contains secrets in plaintext.** Any attribute Terraform read — a generated password, a connection string, a storage key — is in the state file in clear, regardless of whether the output is marked `sensitive`. `sensitive` only hides it from CLI output.

What follows from #3, concretely: the state storage account is treated as a **production secret store**. Private endpoint only, no public network access, Entra ID auth (no storage account keys), infrastructure encryption, soft delete plus versioning, an immutability policy for the audit trail, and RBAC granting *Storage Blob Data Contributor* to exactly the deployment identities and nobody else — not "the platform team", not a group with thirty people in it.

```hcl
# the state account is itself Terraform-managed, in a bootstrap state
resource "azurerm_storage_account" "tfstate" {
  name                            = "sttfstateeyint001"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = "uksouth"
  account_tier                    = "Standard"
  account_replication_type        = "GRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false    # force Entra ID auth
  public_network_access_enabled   = false    # private endpoint only
  allow_nested_items_to_be_public = false
  infrastructure_encryption_enabled = true

  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 90 }
    container_delete_retention_policy { days = 90 }
  }
}
```

```bash
# azurerm backend locking is native: a blob lease. If a run dies mid-apply:
terraform force-unlock 8f3c2a91-...   # ONLY after confirming no apply is running
```

**If they push back — "How do you stop a developer reading secrets out of state?"** — Nobody gets standing read access to the state container. Plans run through the pipeline with a federated identity; if an engineer needs to run a plan locally they get just-in-time access through PIM with an approval and a time limit, and that read is in the storage account's diagnostic log. Beyond access control, I minimise what's in state: generate secrets in Key Vault (`azurerm_key_vault_secret` with a `random_password` still lands in state, so prefer Key Vault-native generation or a `ephemeral` resource on Terraform 1.10+), and reference secrets by Key Vault URI rather than by value wherever the resource supports it.

---

### Q49. `count` vs `for_each` — why is `for_each` safer?
`[MEDIUM]` `[classic, and there's a precise answer]`

**Answer:** `count` addresses instances by **integer index** — `azurerm_servicebus_queue.this[0]`. `for_each` addresses them by **string key** — `azurerm_servicebus_queue.this["payments-in"]`. The difference bites when the collection changes: remove the first element of a `count` list and every subsequent index shifts by one, so Terraform plans to destroy and recreate every resource after the removed one. With `for_each`, removing a key affects exactly that key.

For a Service Bus queue that is a nuisance. For a queue with messages in it, or a database, it's an outage.

```hcl
# DANGEROUS: removing "b" from the list recreates everything after it
variable "queue_names" {
  type    = list(string)
  default = ["a", "b", "c"]
}
resource "azurerm_servicebus_queue" "bad" {
  count        = length(var.queue_names)
  name         = var.queue_names[count.index]
  namespace_id = azurerm_servicebus_namespace.this.id
}

# SAFE: keyed by name; removing "b" touches only "b"
resource "azurerm_servicebus_queue" "good" {
  for_each     = toset(var.queue_names)
  name         = each.value
  namespace_id = azurerm_servicebus_namespace.this.id
}
```

Use `count` for exactly one thing: a **conditional single resource**, `count = var.enable_private_endpoint ? 1 : 0`. Everything else is `for_each`. (Terraform 1.x doesn't have a first-class `if`, so `count` is the idiom.)

**If they push back — "I already have a `count`-based module in production. Now what?"** — `moved` blocks, which let you refactor addresses without destroying anything. Terraform reads them at plan time and rewrites the state mapping, and the plan should show zero changes. That's the check: if a `moved` refactor produces any create or destroy, you got an address wrong.

```hcl
moved {
  from = azurerm_servicebus_queue.bad[0]
  to   = azurerm_servicebus_queue.good["payments-in"]
}
moved {
  from = azurerm_servicebus_queue.bad[1]
  to   = azurerm_servicebus_queue.good["payments-out"]
}
```

---

### Q50. **"How do you check resources using Terraform?"**
`[MEDIUM]` `[EY-LOGGED QUESTION — asked verbatim. Answer all three readings.]`

**Answer:** The question is ambiguous, so I'd answer all three readings in about forty seconds. **Checking what *will* change:** `terraform plan`, ideally saved with `-out` and rendered as `terraform show -json` so a policy engine can read it. **Checking what Terraform currently *manages*:** `terraform state list` to enumerate addresses, `terraform state show <address>` for one resource's recorded attributes, and `terraform output` for the module's declared interface. **Checking whether reality still *matches*:** `terraform plan -refresh-only`, which reconciles state against the live API and shows drift without proposing any configuration change — that's the drift-detection command.

```bash
# 1. what will change
terraform plan -out=tfplan
terraform show -no-color tfplan          # human-readable
terraform show -json tfplan | jq '.resource_changes[]
    | select(.change.actions[] | . == "delete" or . == "replace")
    | {address, actions: .change.actions}'   # the destroys, surfaced explicitly

# 2. what is managed right now
terraform state list
terraform state list | grep servicebus
terraform state show 'module.payments_adapter.azurerm_servicebus_namespace.this'
terraform output -json

# 3. has reality drifted from state?
terraform plan -refresh-only              # detect only, change nothing
terraform apply -refresh-only             # accept reality into state, no infra change

# 4. static checks, no cloud calls
terraform validate
terraform fmt -check -recursive
terraform providers                       # provider dependency tree
terraform graph | dot -Tsvg > graph.svg   # dependency graph

# 5. interactive inspection of state + expressions
terraform console
> module.payments_adapter.service_bus_namespace_id
```

There's also a genuinely-named `check` block (Terraform 1.5+) for continuous **assertions** that run on every plan and apply and warn rather than fail — good for post-deploy health verification:

```hcl
check "service_bus_reachable" {
  data "http" "health" {
    url = "https://${var.workload}-${var.env}.internal.ey.net/readyz"
  }
  assert {
    condition     = data.http.health.status_code == 200
    error_message = "Readiness endpoint did not return 200 after apply."
  }
}
```

**If they push back — "How would you detect drift across a hundred workspaces?"** — A scheduled pipeline per workspace running `terraform plan -detailed-exitcode`, which returns **0** for no changes, **1** for error, **2** for changes present. Exit code 2 on a nightly refresh-only run means someone changed something outside Terraform; that raises a ticket with the plan attached, and Azure Activity Log tells me who. Then I fix the cause, not just the drift — usually it's a standing Contributor role assignment that should have been PIM-eligible. HCP Terraform has drift detection built in if the client is on it.

---

### Q51. Workspaces vs directory-per-environment — pick one.
`[MEDIUM]` `[opinion question]`

**Answer:** Directory-per-environment, for real environments. CLI workspaces give you multiple states from *one configuration*, which sounds elegant until you need prod to differ from dev in a way that isn't a variable — a different SKU tier is fine, but a Private Endpoint that only exists in prod, a different subscription, a different provider alias, or a resource that simply doesn't exist below prod means `count = terraform.workspace == "prod" ? 1 : 0` scattered through the code. That's a configuration that no longer reads as a description of any single environment.

Directory-per-env costs you some duplication — which you fix with a shared module, not with a workspace — and buys you: separate state with separate RBAC, separate backend keys, separate pipelines with separate approvals, the ability to pin a different module version per environment while you roll out a change, and a `prod/` directory whose contents an auditor can read as "this is production".

| | Directory-per-env | CLI workspaces |
|---|---|---|
| State isolation | separate backend key, separate RBAC | same backend, different key prefix |
| Env can differ structurally | yes, naturally | only via conditionals |
| Different subscription/tenant | trivial | awkward |
| Blast radius of a mistake | one env | easy to `apply` against the wrong workspace |
| Duplication | some, solved by modules | none |
| Good for | environments | short-lived parallel copies (per-PR, per-feature) |

Workspaces are genuinely good for **ephemeral** copies — a per-pull-request environment torn down on merge. That's the use case they fit.

**If they push back — "What about Terragrunt?"** — Terragrunt is a wrapper that solves exactly the duplication that directory-per-env creates: DRY backend configuration, `dependency` blocks that wire one stack's outputs into another's inputs, and `run-all` across a tree. It's genuinely useful at scale — dozens of stacks across many accounts. The cost is a second tool, a second DSL, and a hiring constraint. My rule: below about ten stacks, plain Terraform with a small amount of generated backend config; above that, evaluate Terragrunt seriously. Note also that Terraform 1.5+'s `import` blocks and 1.10's `ephemeral` values have absorbed a couple of Terragrunt's reasons to exist.

---

### Q52. Why is `-target` a smell?
`[MEDIUM]` `[trap-adjacent]`

**Answer:** `terraform apply -target=...` applies a subgraph and deliberately skips the rest of the dependency graph, so the resulting state is *partially converged* — Terraform's own docs describe it as intended for exceptional recovery, not routine use. The state that comes out doesn't correspond to any complete plan, and the next full apply may surprise you.

Two legitimate uses: recovering from a bug or a provider error where one resource is wedged, and breaking a genuine chicken-and-egg cycle during bootstrap. Both are one-off, both get written down in the incident record.

If a team is reaching for `-target` regularly, the actual problem is that the state is too big. The fix is decomposition: split the monolith into a networking stack, a platform stack and a per-service stack, joined by `terraform_remote_state` data sources or, better, by explicit inputs so the coupling is visible.

**If they push back — "But a full plan on our 800-resource state takes twenty minutes."** — That's the symptom, and `-target` treats the symptom. The cause is state granularity. Split it, and each apply refreshes 60 resources instead of 800. Secondary levers: `-refresh=false` when you've just refreshed and know nothing changed externally, `-parallelism` tuning, and provider-level caching. But splitting the state is the real fix and it also shrinks your blast radius, which is the argument that gets it prioritised.

---

### Q53. `lifecycle`, `depends_on`, and provisioners.
`[MEDIUM]`

**Answer:** `lifecycle` has four meta-arguments that each solve a specific problem. `create_before_destroy` for zero-downtime replacement of something with a dependent. `prevent_destroy` as a tripwire on stateful resources — it makes the plan **fail** rather than proceed. `ignore_changes` for attributes another system legitimately owns, the canonical case being the container image that the delivery pipeline updates. And `replace_triggered_by` to force replacement when a referenced resource changes.

`depends_on` is for **hidden** dependencies only — where A must exist before B but B's configuration doesn't reference A. Terraform infers everything else from references, and an unnecessary `depends_on` just serialises your graph and slows the apply.

```hcl
resource "azurerm_servicebus_namespace" "this" {
  # ...
  lifecycle {
    prevent_destroy = true          # a destroy plan fails; deliberate removal needs a code change
  }
}

resource "azurerm_container_app" "this" {
  # ...
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [template[0].container[0].image]
  }

  # hidden dependency: the app authenticates via RBAC that isn't referenced here
  depends_on = [azurerm_role_assignment.sb_receiver]
}
```

**Provisioners** (`local-exec`, `remote-exec`, `file`) are the documented last resort. They break the model: they're not part of the plan, they aren't idempotent, they can't be reasoned about, and a failed provisioner marks the resource **tainted** so the next apply destroys and recreates it. The one I'll accept is `local-exec` in a `when = destroy` block for a genuine cleanup that has no API. Everything else has a better home — a `cloud-init`/custom script extension, a container image, an Ansible run, or a Function triggered by an Event Grid resource-creation event.

**If they push back — "What's the RBAC eventual-consistency problem?"** — Very real and worth naming: `azurerm_role_assignment` returns success before the assignment has propagated, so a resource created immediately after may get a 403. `depends_on` doesn't help because Terraform already thinks it's done. The pragmatic fixes are a `time_sleep` resource between them, retry logic in the application's startup, or — best — designing so the app tolerates a transient 403 on first call and retries, since that's also true at runtime.

---

### Q54. What's `terraform import` for, and how has it changed?
`[MEDIUM]`

**Answer:** `import` brings an existing, unmanaged resource under Terraform's control by writing it into state. It's how you adopt ClickOps'd infrastructure, or infrastructure created by another team, without destroying and recreating it — which is the only acceptable option for a production Service Bus namespace with live traffic.

The important change: since Terraform 1.5 there's a declarative **`import` block**, so an import is a reviewable, planned, version-controlled change rather than an out-of-band CLI command someone ran once and didn't tell anyone about. And 1.5 added `-generate-config-out` to scaffold the HCL for you.

```hcl
# import.tf — reviewable in a PR, visible in the plan, then deleted after apply
import {
  to = module.payments_adapter.azurerm_servicebus_namespace.this
  id = "/subscriptions/aaaa.../resourceGroups/rg-int-prod-uks/providers/Microsoft.ServiceBus/namespaces/sbns-payments-adapter-prod"
}
```

```bash
# scaffold the configuration from the live resource, then hand-tidy it
terraform plan -generate-config-out=generated.tf
terraform plan     # MUST show "No changes" before you apply anything
terraform apply
```

The discipline: **an import is done when the plan is clean.** If the plan wants to change something after import, your HCL doesn't match reality and applying it will mutate a live resource. That's the moment to stop.

**If they push back — "How do you import a hundred resources?"** — Generate the import blocks. Query Azure Resource Graph for the resource IDs, template them into `import.tf` with a script, run `plan -generate-config-out`, then spend the real effort on reconciling the generated HCL down to the module call it should have been. The import is mechanical; making it *maintainable* is the work. I'd also do it in tranches by resource type, each its own PR, so a bad import affects one type.

---

### Q55. Policy-as-code for Terraform — Sentinel, OPA, Checkov: which and why?
`[MEDIUM]`

**Answer:** They occupy different points. **Checkov** is a rule library — hundreds of pre-built checks mapped to CIS and standards benchmarks, zero authoring effort, runs on source or on the plan JSON. **OPA/Conftest** is a general policy engine with Rego, where I write the client's own rules against the plan JSON — it's open, runs anywhere, and I'd default to it for custom policy. **Sentinel** is HashiCorp's policy engine, only available in HCP Terraform / Terraform Enterprise, with the advantage of first-class enforcement levels (`advisory`, `soft-mandatory` which an admin can override with a recorded reason, `hard-mandatory`) integrated into the run workflow.

My default stack: Checkov for the standard benchmark, OPA/Conftest for client-specific rules, both against `tfplan.json`, both blocking in the PR. Sentinel only if the client is already on HCP Terraform — its soft-mandatory-with-override model is genuinely nice for FS because the override is itself an audit record.

And the layer underneath all three: **Azure Policy**, which enforces at the resource-manager level regardless of how the resource was created. Scanning is a pipeline control; Azure Policy is a platform control. An auditor will want both, and will ask what happens when someone uses the portal.

**If they push back — "Isn't Azure Policy enough on its own?"** — It's the stronger control but the worse experience: it fails at *deploy* time with a policy error, after the engineer has written the code, opened the PR, got it reviewed and run the apply. Checkov and OPA fail in the PR in ninety seconds with a line number. Same rules, two enforcement points: one for developer feedback, one for actual enforcement. I'd generate both from a single source of truth where possible so they can't drift apart.

---

### Q56. How do you structure Terraform repos for a client with many teams?
`[MEDIUM]`

**Answer:** Three layers, and they map to three different change cadences and three different approvers.

```text
platform-modules/            (platform team; tagged releases; semver)
  modules/
    integration-service/     v2.4.0
    apim-api/                v1.9.2
    private-endpoint/        v3.0.1
  .github/workflows/test.yml  -> terraform test + checkov + example applies

landing-zone/                (cloud platform team; rare, high-blast-radius changes)
  envs/{nonprod,prod}/       vnets, hub firewall, Log Analytics, ACR, policy assignments

payments-adapter/            (product team; frequent, low-blast-radius changes)
  infra/envs/{dev,uat,prod}/ module calls only; ~40 lines each
  app/ tests/ Dockerfile
  azure-pipelines.yml        extends the platform template
```

Key rules: product teams may only call modules from the registry — enforced by an OPA rule that fails a plan containing a `resource` block outside an approved module source. Module changes are semver-tagged and consumers pin. Landing zone outputs are consumed by product stacks as data sources or via a published `terraform_remote_state`, never by hardcoding IDs. And every module ships with `terraform test` files plus an `examples/` directory that CI actually applies and destroys.

```hcl
# platform-modules/modules/integration-service/tests/defaults.tftest.hcl
variables {
  workload            = "test-svc"
  env                 = "dev"
  resource_group_name = "rg-module-test"
  cost_centre         = "TEST-0000"
  data_classification = "internal"
  # ... remaining required inputs
}

run "sas_auth_is_disabled_by_default" {
  command = plan

  assert {
    condition     = azurerm_servicebus_namespace.this.local_auth_enabled == false
    error_message = "Platform policy: SAS/local auth must be disabled."
  }
}

run "prod_disables_public_network_access" {
  command = plan
  variables { env = "prod" }

  assert {
    condition     = azurerm_servicebus_namespace.this.public_network_access_enabled == false
    error_message = "Prod namespaces must be Private Link only."
  }
}
```

**If they push back — "Monorepo or polyrepo for the modules?"** — Monorepo for the modules, because they share test tooling and are released together, and the `//modules/x?ref=tag` source syntax lets consumers pin a single tag across the set. Polyrepo for the product stacks, because each has a different owner and a different approval chain. The one thing I would not do is a monorepo containing both modules and every team's environments — then a module change and forty environment changes share a PR history and nobody can tell what shipped.

---

### Q57. How do you handle a Terraform apply that fails halfway?
`[MEDIUM]` `[operational credibility]`

**Answer:** Terraform is not transactional — resources created before the failure stay created and are recorded in state. So the recovery is: read the error, fix the cause, and re-run `plan` and `apply`, because Terraform is convergent and will only do the remaining work. What you must **not** do is delete the state or start hand-fixing in the portal.

The specific cases worth naming. If the run died without writing state (agent killed, network drop), the **lock may still be held** — verify no apply is running, then `terraform force-unlock <ID>`. If a resource was created but Terraform lost track of it, you'll get an "already exists" error on the next apply; the fix is `import`, not a portal delete. If a resource is in a broken state at the provider, `terraform taint` (or, current syntax, `terraform apply -replace=<address>`) forces recreation on the next apply.

```bash
terraform force-unlock 8f3c2a91-4d5e-...      # only after confirming no run is live
terraform apply -replace='module.x.azurerm_container_app.this'   # replaces taint
terraform state rm 'module.x.azurerm_role_assignment.stale'      # forget, don't destroy
```

**If they push back — "What if apply fails in prod at 2am mid-change-window?"** — The runbook decision is roll-forward or roll-back, and for infrastructure it's almost always **roll forward**, because `terraform apply` of the previous commit is itself a destructive operation that may delete something the failed run created and something else now depends on. So: stop, assess whether the partially-applied state is *serving traffic correctly* — often it is, because the failure was on a resource nothing depends on yet — and if so, fix in the morning under normal change control. Only roll back if the partial state is actively broken. That decision, and who makes it, belongs in the runbook before the change window, not during it.

---

### Q58. What is drift and how do you deal with it?
`[MEDIUM]`

**Answer:** Drift is any divergence between the state file and reality — someone changed a setting in the portal, an autoscaler resized something, or a support engineer applied a hotfix. Detection is `terraform plan -refresh-only` on a schedule with `-detailed-exitcode`; exit code 2 means drift exists.

Then a decision per instance, not a blanket policy. If the change was **wrong**, `terraform apply` reverts it and you fix the access that allowed it. If the change was **right but out-of-process**, you codify it: update the HCL to match, and the next plan is clean. If the attribute is **legitimately owned elsewhere** — the container image, an autoscaler's replica count — you add it to `ignore_changes` so it stops being reported as drift, because a drift report that's 90% noise gets ignored.

The root-cause fix is almost always access: nobody should have standing write access to production resources outside the pipeline. PIM-eligible, just-in-time, approval-required, time-boxed. Drift is usually a symptom of a permissions model, not of careless engineers.

**If they push back — "Does GitOps solve drift?"** — For Kubernetes, yes, and much better: ArgoCD's `selfHeal` reverts the cluster continuously, in seconds, without a scheduled job. For Azure resources, Terraform has no equivalent daemon — the nearest things are HCP Terraform's continuous drift detection, Azure Policy with `deployIfNotExists` remediation for specific settings, and **deployment stacks' deny settings** in the Bicep world, which actually prevent the change rather than reverting it. That asymmetry — Kubernetes has a real reconciler, ARM doesn't — is worth naming because it's a genuine architectural difference and it's the reason GitOps caught on where cluster workloads are concerned.

---

### Q59. Terraform vs the cloud-native tools — one sentence each on the trade.
`[EASY]`

**Answer:** Terraform is the answer when the estate is multi-cloud, or when it spans things ARM doesn't reach — Entra ID app registrations, GitHub repos, Datadog monitors, Kubernetes resources, Snowflake. Bicep/ARM is the answer when the estate is Azure-only and the client values zero-day support for new Azure features, no state file to protect, and Microsoft support on the tool itself. Pulumi is the answer when the team's centre of gravity is genuinely software engineering and they'll get real value from loops, types and unit tests in a general-purpose language. CloudFormation is the AWS-only equivalent of ARM, and CDK is its Pulumi.

Full comparison and the "which for an EY client" argument is in §10.

---

## 10. Bicep, ARM, Pulumi, CloudFormation

### Q60. What is Bicep and how does it relate to ARM?
`[EASY]` `[near-certain if you say "Azure"]`

**Answer:** Bicep is a domain-specific language that **transpiles to ARM JSON**. It is not a separate deployment engine — the thing that runs is still an ARM template against the Azure Resource Manager API, so Bicep has exactly ARM's capabilities and exactly ARM's limits. What it removes is ARM JSON's ergonomics: no `"[concat(...)]"` string expressions, real types and IntelliSense, modules that are just other Bicep files, automatic dependency inference from symbolic references, and about a 60% reduction in line count.

The three practical consequences: **no state file** (ARM is the state — Azure knows what exists), **day-zero support for new Azure resources** because it's the same API surface Microsoft ships against, and **Microsoft support** on the tool. The cost is that it is Azure-only, and it has no plan/apply cycle in the Terraform sense — `what-if` is close but is a preview computed by ARM, not a saved artefact you apply.

**If they push back — "So Bicep has no state — how does it know what to delete?"** — By default it doesn't, and that's the honest weakness. An incremental-mode deployment only adds and updates; remove a resource from the template and it stays in Azure. `complete` mode deletes anything in the resource group that isn't in the template, which is powerful and terrifying. The modern answer is **deployment stacks** (§Q64), which give you an explicit managed-resource list and an `actionOnUnmanage` behaviour — that's ARM finally getting the equivalent of Terraform's ownership model.

---

### Q61. Show me the same integration service in Bicep.
`[HARD]`

```bicep
// main.bicep — resource-group scope
targetScope = 'resourceGroup'

@description('Short workload name, e.g. payments-adapter.')
@minLength(3)
@maxLength(23)
param workload string

@allowed(['dev', 'test', 'uat', 'prod'])
param env string

param location string = resourceGroup().location

@allowed(['Standard', 'Premium'])
param serviceBusSku string = 'Standard'

@description('Premium messaging units. Ignored for Standard.')
@allowed([1, 2, 4, 8, 16])
param serviceBusCapacity int = 1

param queues array = [
  { name: 'payments-in',  requiresSession: true,  maxDeliveryCount: 10, ttl: 'P14D' }
  { name: 'payments-out', requiresSession: false, maxDeliveryCount: 5,  ttl: 'P7D'  }
]

param logAnalyticsWorkspaceName string
param infrastructureSubnetId string
param acrLoginServer string
param acrName string
param acrResourceGroupName string

@description('Digest-pinned image reference.')
param containerImage string

param costCentre string

@allowed(['public', 'internal', 'confidential', 'restricted'])
param dataClassification string

@secure()
@description('Only for a legacy backend that genuinely cannot use managed identity.')
param legacyPartnerApiKey string = ''

var namePrefix = '${workload}-${env}'
var isProd = env == 'prod'

// Built-in role definition GUIDs (verified against Microsoft Learn built-in roles)
var sbDataReceiverRoleId = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0' // Azure Service Bus Data Receiver
var sbDataSenderRoleId   = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39' // Azure Service Bus Data Sender

var tags = {
  workload: workload
  environment: env
  managedBy: 'bicep'
  costCentre: costCentre
  dataClassification: dataClassification
}

// the `existing` keyword: reference something this template does not own
resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${namePrefix}'
  location: location
  tags: tags
}

resource sbns 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: 'sbns-${namePrefix}'
  location: location
  tags: tags
  sku: {
    name: serviceBusSku
    tier: serviceBusSku
    capacity: serviceBusSku == 'Premium' ? serviceBusCapacity : null
  }
  properties: {
    disableLocalAuth: true                                  // no SAS keys, ever
    minimumTlsVersion: '1.2'
    publicNetworkAccess: isProd ? 'Disabled' : 'Enabled'
    zoneRedundant: serviceBusSku == 'Premium' && isProd
  }
}

resource sbQueues 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = [for q in queues: {
  parent: sbns
  name: q.name
  properties: {
    requiresSession: q.requiresSession
    maxDeliveryCount: q.maxDeliveryCount
    defaultMessageTimeToLive: q.ttl
    lockDuration: 'PT1M'
    deadLetteringOnMessageExpiration: true
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    maxSizeInMegabytes: 1024
  }
}]

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${namePrefix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: infrastructureSubnetId
      internal: isProd
    }
    zoneRedundant: isProd
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-${namePrefix}'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
        traffic: [
          { latestRevision: true, weight: 100 }
        ]
      }
      registries: [
        { server: acrLoginServer, identity: uami.id }
      ]
    }
    template: {
      containers: [
        {
          name: workload
          image: containerImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'SERVICEBUS_FQDN', value: '${sbns.name}.servicebus.windows.net' }
            { name: 'AZURE_CLIENT_ID', value: uami.properties.clientId }
            { name: 'OTEL_SERVICE_NAME', value: workload }
          ]
          probes: [
            { type: 'Liveness',  httpGet: { path: '/healthz', port: 8000 }, periodSeconds: 10 }
            { type: 'Readiness', httpGet: { path: '/readyz',  port: 8000 }, periodSeconds: 5  }
          ]
        }
      ]
      scale: {
        minReplicas: isProd ? 2 : 1
        maxReplicas: isProd ? 20 : 5
      }
    }
  }
}

// queue-scoped RBAC — least privilege, not namespace-wide
resource sbReceive 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (q, i) in queues: {
  name: guid(sbQueues[i].id, uami.id, sbDataReceiverRoleId)
  scope: sbQueues[i]
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', sbDataReceiverRoleId)
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}]

// cross-resource-group role assignment must go through a module
module acrPull 'modules/acr-pull.bicep' = {
  name: 'acrPull-${namePrefix}'
  scope: resourceGroup(acrResourceGroupName)
  params: {
    acrName: acrName
    principalId: uami.properties.principalId
  }
}

output serviceBusNamespaceId string = sbns.id
output managedIdentityClientId string = uami.properties.clientId
output containerAppFqdn string = app.properties.configuration.ingress.fqdn
```

```bicep
// modules/acr-pull.bicep
param acrName string
param principalId string

var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, principalId, acrPullRoleId)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
```

```bicep
// prod.bicepparam — typed parameters, and Key Vault by reference not by value
using './main.bicep'

param workload = 'payments-adapter'
param env = 'prod'
param serviceBusSku = 'Premium'
param serviceBusCapacity = 1
param logAnalyticsWorkspaceName = 'log-platform-prod-uks'
param infrastructureSubnetId = '/subscriptions/aaaa.../resourceGroups/rg-net-prod-uks/providers/Microsoft.Network/virtualNetworks/vnet-int-prod/subnets/snet-aca-infra'
param acrLoginServer = 'eyintacr.azurecr.io'
param acrName = 'eyintacr'
param acrResourceGroupName = 'rg-platform-prod-uks'
param containerImage = 'eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e...'
param costCentre = 'FS-BCM-4471'
param dataClassification = 'confidential'

// the secret is fetched at deployment time; the value never enters the repo
param legacyPartnerApiKey = az.getSecret(
  'aaaa0a0a-bb1b-cc2c-dd3d-eeeeee4e4e4e',
  'rg-platform-prod-uks',
  'kv-eyint-prod',
  'legacy-partner-api-key'
)
```

```bash
# preview before deploying — the closest thing Bicep has to `terraform plan`
az deployment group what-if \
  --resource-group rg-int-prod-uks \
  --template-file main.bicep \
  --parameters prod.bicepparam \
  --result-format FullResourcePayload

az deployment group create \
  --resource-group rg-int-prod-uks \
  --template-file main.bicep \
  --parameters prod.bicepparam \
  --name "payments-adapter-$(date +%Y%m%d%H%M%S)"
```

**If they push back — "`what-if` isn't as good as `terraform plan`, is it?"** — No, and I'd say so plainly. `what-if` is computed server-side by ARM and it has known noisy properties — it reports changes to attributes that aren't really changing because the provider doesn't return them, and there's no saved artefact you can hand to an approver and then apply *exactly*. That gap is real and it's the single strongest technical argument for Terraform in an environment where the plan is an audit artefact. Deployment stacks close part of it by making ownership explicit, but the plan-as-artefact property is still Terraform's.

---

### Q62. What's the Bicep module and scope model?
`[MEDIUM]`

**Answer:** A Bicep module is just another `.bicep` file invoked with a `module` block, and its most important property is that it can target a **different scope** — a different resource group, subscription or management group — via the `scope:` argument. That is how you do the things a single-scope template can't: assign a role on a registry in another resource group, create the resource group itself from a subscription-scope deployment, or assign policy at a management group.

The four `targetScope` values are `resourceGroup` (default), `subscription`, `managementGroup` and `tenant`. A subscription-scope template is how you create resource groups; a management-group-scope template is how you assign policy across subscriptions.

```bicep
targetScope = 'subscription'

param env string
param location string = 'uksouth'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-int-${env}-uks'
  location: location
  tags: { environment: env, managedBy: 'bicep' }
}

module workload 'main.bicep' = {
  name: 'integration-${env}'
  scope: rg                       // deploy the RG-scope template into the RG we just made
  params: {
    workload: 'payments-adapter'
    env: env
    // ...
  }
}
```

Also worth naming: `az bicep decompile main.json` converts an existing ARM template to Bicep (the migration path — it produces ugly output that needs hand-tidying, so treat it as a starting point); `bicep lint` / the `bicepconfig.json` linter rules run in CI; and **Azure Verified Modules** are the Microsoft-maintained public registry, referenced as `br/public:avm/res/service-bus/namespace:0.9.1`.

**If they push back — "Bicep modules have no versioning, unlike Terraform."** — They do, via a **private module registry** backed by ACR: `az bicep publish --file main.bicep --target br:eyintacr.azurecr.io/bicep/integration-service:v2.4.0`, consumed as `module x 'br:eyintacr.azurecr.io/bicep/integration-service:v2.4.0' = {...}`. Same semver discipline as Terraform modules, and you get ACR's RBAC and geo-replication for free. Local path modules are fine inside one repo; anything shared across teams goes in the registry.

---

### Q63. What are secure parameters and where do they go wrong?
`[MEDIUM]` `[trap]`

**Answer:** `@secure()` on a `string` or `object` parameter tells ARM not to log the value in deployment history or return it in outputs. What it does **not** do is protect the value anywhere else: a secure parameter passed into a resource that echoes it, or referenced in an `output`, leaks — and ARM will actually refuse an output that references a secure parameter, which is the guardrail working.

The failure modes: putting the value in a `.bicepparam` or `parameters.json` file in the repo (that's just a secret in Git with extra steps); passing it on a command line where it lands in shell history and CI logs; and the subtle one, using a secure parameter's value in a `name` or a `guid()` expression where it ends up in the deployment name.

The correct pattern is a Key Vault reference so the value never transits your repo or your pipeline variables at all:

```bicep
// in a .bicepparam
param legacyPartnerApiKey = az.getSecret('<subId>', '<rg>', 'kv-eyint-prod', 'legacy-partner-api-key')
```

```json
// classic parameters.json equivalent — the KeyVault reference form
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "legacyPartnerApiKey": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/aaaa.../resourceGroups/rg-platform-prod-uks/providers/Microsoft.KeyVault/vaults/kv-eyint-prod"
        },
        "secretName": "legacy-partner-api-key"
      }
    }
  }
}
```

For this to work the Key Vault needs `enabledForTemplateDeployment: true` (or the equivalent RBAC), and the identity running the deployment needs *Key Vault Secrets User*.

**If they push back — "How do you prove no secret is in the repo?"** — Three layers, and they're cheap: gitleaks in pre-commit and as a blocking PR check; GitHub secret scanning with **push protection** so the push is rejected before the secret ever lands in history; and a custom CI rule that fails when any `.bicepparam` or `parameters.json` supplies a literal value for a parameter declared `@secure()` in the template. That third one is the specific control for this failure and almost nobody has it.

---

### Q64. What are deployment stacks and why do they matter?
`[HARD]` `[recency signal]`

**Answer:** A deployment stack is an Azure resource (`Microsoft.Resources/deploymentStacks`) that manages a set of resources as one unit. It gives ARM the two things it always lacked versus Terraform: an explicit **managed resource list**, so removing a resource from the template can actually delete it; and **deny settings**, which create a deny-assignment preventing anyone — including an Owner — from modifying or deleting the managed resources outside the stack.

That second property is genuinely interesting for financial services. It's not drift *detection*, it's drift *prevention* at the control plane, which is stronger than anything Terraform offers on Azure.

The parameters to know: `actionOnUnmanage` is `deleteAll`, `deleteResources` or `detachAll` (default detach); `denySettingsMode` is `none`, `denyDelete` or `denyWriteAndDelete`, with `denySettingsApplyToChildScopes`, up to **200** excluded actions and a hard maximum of **five** excluded principals — which is why you exclude an Entra **group** (the CI/CD workload identity, the break-glass admins) rather than individual principals. Stacks can live at resource group, subscription or management group scope, and the recommended pattern is to put the stack at the *parent* scope so developers with write access to the resource group can't edit the stack or its deny assignment. Requires Azure CLI 2.61.0+ or Az PowerShell 12.0.0+.

```bash
# create/update — the same command does both
az stack group create \
  --name payments-adapter-prod \
  --resource-group rg-int-prod-uks \
  --template-file main.bicep \
  --parameters prod.bicepparam \
  --action-on-unmanage deleteResources \
  --deny-settings-mode denyWriteAndDelete \
  --deny-settings-apply-to-child-scopes \
  --deny-settings-excluded-principals "$CICD_IDENTITY_OBJECT_ID $BREAKGLASS_GROUP_OBJECT_ID"

# what does the stack currently manage?
az stack group show --name payments-adapter-prod \
  --resource-group rg-int-prod-uks --output json

# tear down cleanly, including the resources
az stack group delete --name payments-adapter-prod \
  --resource-group rg-int-prod-uks --action-on-unmanage deleteAll
```

Two operational gotchas worth having ready: the deny setting applies only to **control-plane** operations, so it stops someone deleting a Key Vault but not someone reading a secret out of it; and it applies only to **explicitly declared** resources, so an AKS cluster's implicitly-created VMs in the node resource group are not covered.

**If they push back — "Does this make Terraform unnecessary on Azure?"** — For an Azure-only estate it closes the biggest gap, yes. What it doesn't give you is the plan-as-reviewable-artefact, a single tool across Entra ID/GitHub/Datadog/Kubernetes, or portability if the client acquires an AWS-based business — which in financial services happens. So I'd frame it as: deployment stacks make Bicep a genuinely defensible choice for an Azure-only client in 2026, which was not true two years ago.

---

### Q65. Terraform vs Bicep vs ARM vs Pulumi — and which for an EY client?
`[HARD]` `[argue both sides; EY logged "Convince me to adopt AWS" — persuasion is graded]`

| | Terraform | Bicep | ARM JSON | Pulumi |
|---|---|---|---|---|
| Language | HCL (declarative DSL) | DSL → ARM | JSON | Python/TS/Go/C# |
| Clouds | ~everything, 4,000+ providers | Azure only | Azure only | ~everything |
| State | your own remote state, must be protected | none (ARM is state) | none | Pulumi Cloud or self-managed |
| Preview | `plan`, saved and applied exactly | `what-if` (server-side, noisier, not applied as an artefact) | `what-if` | `preview` |
| Delete on removal | yes, by default | no (unless complete mode / deployment stacks) | same | yes |
| New Azure features | provider lag, days–weeks | day zero | day zero | provider lag |
| Drift prevention | detection only | **deployment stacks deny settings** | — | detection only |
| Modules | registry, semver, `moved` blocks | modules + ACR private registry + AVM | linked templates | packages |
| Testing | `terraform test`, Terratest | `bicep test` (preview), what-if in CI | — | real unit tests, any framework |
| Licence | BSL (OpenTofu is the MPL fork) | MIT, Microsoft-supported | — | Apache 2 |
| Skills market | very large | Azure-specific, growing | shrinking | small |

**The answer for an EY client, argued both ways.** *For Bicep:* EY is a Microsoft shop with a $1B joint AI investment and a named Azure/Foundry/Fabric stack; the client is often Azure-only; Bicep has no state file to secure — which removes an entire class of audit finding — and deployment stacks now give you ownership and drift prevention; and Microsoft supports it, which matters to a risk function. *For Terraform:* the estate is almost never purely Azure once you count Entra ID app registrations, the GitHub org, the Datadog or Splunk config, and any acquired business; the plan is a reviewable artefact you can attach to a change record, which Bicep genuinely cannot match; and the skills market is far larger, which is a delivery-risk argument a partner understands.

**Where I'd land, and I'd say it as a decision not a preference:** Terraform as the default for anything spanning more than ARM, and Bicep where the team is Azure-native and wants zero state to protect. What I would *not* do is run both for the same resources — the failure mode I've seen is Terraform and Bicep both claiming a resource group, each apply reverting the other's changes. Pick one per boundary and write the boundary down.

**If they push back — "Just pick one. You're consulting; commit."** — Terraform. The deciding factor is that the plan is a saved, reviewable, policy-checkable artefact and the same tool covers Entra ID and Kubernetes, which is where an integration platform's identity and workload configuration actually lives. I'd accept Bicep instantly if the client already has a Bicep estate and a working deployment-stacks pattern — migrating working IaC for tool-preference reasons is value-destroying.

---

### Q66. CloudFormation — enough to not be caught out.
`[EASY]` `[the JD names it]`

**Answer:** CloudFormation is AWS's native IaC: YAML or JSON templates, deployed as a **stack**, with **change sets** as the preview mechanism (the `terraform plan` analogue), **StackSets** for multi-account/multi-region rollout, **drift detection** built in, and rollback-on-failure by default. **CDK** generates CloudFormation from TypeScript/Python — it's the Pulumi-shaped option in the AWS world. **SAM** is the serverless-focused superset.

The mapping that matters if they probe: CloudFormation stack ≈ ARM deployment / deployment stack; change set ≈ `what-if` / `plan`; StackSets ≈ Azure Policy `deployIfNotExists` plus management-group-scope templates; `!Ref`/`!GetAtt` ≈ Bicep symbolic references; stack outputs and exports ≈ ARM outputs.

The JD naming CloudFormation and EKS/GKE alongside AKS means "don't assume Azure-only", not "we need an AWS expert". The credible line: *"I lead with Azure because that's the estate I've worked in, and I can hold the AWS conversation — CloudFormation change sets and StackSets, EKS with IRSA instead of workload identity, Secrets Manager instead of Key Vault. If the engagement is AWS I'd expect a few weeks to be genuinely productive, and Terraform ports across both."*

**If they push back — "Convince me to adopt AWS."** *(EY logged this exact question at Senior Analyst level.)* — The honest persuasive case: breadth and maturity of the managed-service catalogue, especially in data and event streaming — MSK, Kinesis, EventBridge — where you have more purpose-built choices than Azure gives you; a larger third-party ecosystem and integration surface; and a bigger engineering talent pool. Then the discipline of the consultant: I'd close by naming the counter-argument, because a partner is grading judgement not enthusiasm — for an organisation already on Microsoft 365, Entra ID and Power Platform, the identity and licensing gravity of Azure usually outweighs those advantages, and the right answer is often "AWS for the data platform, Azure for the enterprise integration layer, one identity plane across both."

---

## 11. GitOps and ArgoCD

### Q67. What is GitOps and why is pull safer than push?
`[MEDIUM]` `[NOW A CORE JD RESPONSIBILITY — expect it]`

**Answer:** GitOps is four principles: the desired state is **declarative**; it is **versioned and immutable** in Git; changes are **pulled automatically** by an agent; and that agent **continuously reconciles** actual state toward desired state. The last one is what distinguishes GitOps from "we keep our YAML in Git" — the agent doesn't just apply on change, it fights drift forever.

Pull is safer than push for one decisive reason: **no cluster credentials leave the cluster.** In a push model, CI holds a kubeconfig with write access to production; anyone who compromises the CI system, or a workflow that a malicious PR can influence, owns the cluster. In a pull model the agent runs *inside* the cluster, reads Git and the registry outbound, and CI has no cluster access at all. For a bank with a private AKS API server, that also removes the need for a VNet-joined runner just to deploy.

```text
  PUSH (CI deploys)                        PULL (GitOps)
  ─────────────────                        ─────────────
  CI runner ──kubeconfig──► API server     CI ──► builds image, commits tag to config repo
     ▲                                                        │
     │ holds prod credentials                                 ▼ (agent polls, outbound only)
     │ needs network path into the VNet     ArgoCD/Flux in-cluster ──► API server
     │ drift invisible until next deploy    continuous reconcile, selfHeal, drift auto-reverted
```

The other three benefits, in order of how much an FS client cares: **the audit trail is the Git history** — every production change is a signed commit with an author, a reviewer and a timestamp, which is exactly what a change auditor asks for; **rollback is `git revert`**, so it's the same mechanism as deploy and it's already tested; and **drift is impossible to sustain** because the reconciler reverts it.

**If they push back — "What's the downside of GitOps?"** — Three real ones. Secrets need a separate solution because you can't commit them (§13). Debugging gains a layer — "why isn't my change live" now has answers in Git, in the agent's sync status, and in the cluster. And you need discipline about **what** is in Git: if CI writes an image tag back to the config repo on every build, your config repo history is 95% bot commits and the audit value degrades. I'd use an image automation controller writing to a dedicated file, or better, digest-pinned promotion PRs that a human merges.

---

### Q68. Walk me through ArgoCD's architecture.
`[MEDIUM]` `[near-certain if GitOps comes up]`

**Answer:** Four components. The **API server** is the stateless gRPC/REST front end — the UI, the CLI, authentication, RBAC and the app management API; it scales horizontally. The **repository server** clones Git repos and *generates manifests* — it runs `helm template`, `kustomize build` or a config-management plugin, and caches the result. The **application controller** is the reconciler: it compares the desired manifests from the repo server against live cluster state, reports Synced/OutOfSync and Healthy/Degraded, and executes syncs. **Redis** is a disposable cache for manifests and app state — losing it costs performance, not correctness.

The verified knobs, which is where you show you've operated it: the controller's polling interval is `timeout.reconciliation`, **default 3 minutes**, with `timeout.reconciliation.jitter` to spread the refresh spike; the controller has two work queues sized by `--status-processors` (default **20**) and `--operation-processors` (default **10**); the repo server's config-management-tool timeout is `ARGOCD_EXEC_TIMEOUT`, **default 90 seconds**, with `--parallelismlimit` to stop concurrent manifest generation OOM-killing it; `--repo-cache-expiration` defaults to **24 hours**; and `ARGOCD_CONTROLLER_REPLICAS` enables cluster sharding for large installs.

```bash
# the diagnostic sequence for "my app isn't syncing"
argocd app get payments-adapter-prod
argocd app diff payments-adapter-prod          # desired vs live, the actual answer
argocd app history payments-adapter-prod
argocd app sync payments-adapter-prod --dry-run
kubectl logs -n argocd deploy/argocd-repo-server --tail=100        # manifest generation
kubectl logs -n argocd statefulset/argocd-application-controller   # reconciliation
```

**If they push back — "Three minutes is slow. How do you make it react instantly?"** — A **webhook** from the Git provider to the ArgoCD API server, which triggers an immediate refresh of the affected applications. The 3-minute poll then becomes the safety net for missed webhooks rather than the primary path. In production I configure both, because a webhook you rely on and don't monitor is a silent failure waiting to happen.

---

### Q69. Show me a real ArgoCD Application.
`[MEDIUM]`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-adapter-prod
  namespace: argocd
  finalizers:
    # ensures deleting the Application also removes the resources it created
    - resources-finalizer.argocd.argoproj.io
spec:
  project: fs-integration-prod

  # multi-source: the chart lives in ACR, the values live in the config repo
  sources:
    - repoURL: eyintacr.azurecr.io/helm
      chart: integration-service
      targetRevision: 3.4.1              # pinned chart version, never a range
      helm:
        releaseName: payments-adapter
        valueFiles:
          - $values/apps/payments-adapter/values-prod.yaml
    - repoURL: https://dev.azure.com/eygds/Platform/_git/gitops-config
      targetRevision: main
      ref: values

  destination:
    server: https://prod-aks-abc123.privatelink.uksouth.azmk8s.io:443
    namespace: payments

  syncPolicy:
    automated:
      prune: false        # PROD: never auto-delete. Removal is a deliberate manual sync.
      selfHeal: true      # revert manual cluster edits automatically
      allowEmpty: false   # an empty manifest set is a bug, not an instruction to delete everything
    syncOptions:
      - CreateNamespace=false      # the namespace is platform-owned, with quotas and NetworkPolicy
      - ApplyOutOfSyncOnly=true    # don't re-apply unchanged resources
      - ServerSideApply=true       # avoids the last-applied-configuration annotation size limit
      - PruneLast=true             # delete removed resources only after the new ones are healthy
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 15s
        factor: 2
        maxDuration: 5m

  revisionHistoryLimit: 20

  ignoreDifferences:
    # HPA owns replicas; without this the app is permanently OutOfSync
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
    # the CA injector owns this field
    - group: admissionregistration.k8s.io
      kind: ValidatingWebhookConfiguration
      jqPathExpressions:
        - '.webhooks[]?.clientConfig.caBundle'
```

Three things to point at while you talk: `prune: false` in prod is a deliberate choice — auto-prune plus a bad merge deletes production; `selfHeal: true` is the drift control and it's the thing that makes GitOps a *control* rather than a convenience; and `ignoreDifferences` for `/spec/replicas` is the single most common real-world ArgoCD issue, because HPA and Git both want to own that field.

**If they push back — "Why `prune: false` in prod but presumably `true` in dev?"** — Because the cost of the two mistakes is asymmetric. In dev, leftover resources cost money and confusion, so auto-prune is right. In prod, an accidental deletion — a bad merge, a mis-templated ApplicationSet, a Git revert that goes further back than intended — is an outage. So prod prunes on an explicit manual sync where a human sees the list of resources ArgoCD is about to delete. `PruneLast=true` and `PrunePropagationPolicy=foreground` reduce the damage further when you do prune.

---

### Q70. What is App-of-Apps, and how does ApplicationSet differ?
`[HARD]`

**Answer:** **App-of-Apps** is a bootstrap pattern: one ArgoCD Application whose Git path contains *other* Application manifests. Sync the root and it creates all the children. It's how you bring up a cluster from nothing — one `kubectl apply` of the root app installs ingress, cert-manager, external-secrets, the monitoring stack and every workload.

**ApplicationSet** is a controller with a CRD that **generates** Applications from a template plus a generator, so you don't hand-write one Application per service per environment. Nine generator types: **List** (fixed key/value elements), **Cluster** (one app per registered cluster), **Git** (from files or directory structure in a repo), **Matrix** (cartesian of two generators), **Merge** (overlay generators, later overriding earlier), **SCM Provider** (discover repos in a GitHub/GitLab org), **Pull Request** (an ephemeral env per open PR), **Cluster Decision Resource**, and **Plugin** (RPC to your own service).

The platform-engineering point: App-of-Apps is how you bootstrap; ApplicationSet is how you scale. Forty services × four environments is 160 Applications, and nobody hand-writes those.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: integration-services
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]   # fail loudly on a typo, don't render empty
  syncPolicy:
    preserveResourcesOnDeletion: true       # deleting the ApplicationSet must not delete prod
  generators:
    - matrix:
        generators:
          # one config file per service in the config repo
          - git:
              repoURL: https://dev.azure.com/eygds/Platform/_git/gitops-config
              revision: main
              files:
                - path: "apps/*/config.yaml"
          # crossed with the environment list
          - list:
              elements:
                - env: dev
                  cluster: https://dev-aks.privatelink.uksouth.azmk8s.io:443
                  autoPrune: "true"
                  project: fs-integration-nonprod
                - env: prod
                  cluster: https://prod-aks.privatelink.uksouth.azmk8s.io:443
                  autoPrune: "false"
                  project: fs-integration-prod
  template:
    metadata:
      name: '{{.workload}}-{{.env}}'
      labels:
        workload: '{{.workload}}'
        environment: '{{.env}}'
    spec:
      project: '{{.project}}'
      sources:
        - repoURL: eyintacr.azurecr.io/helm
          chart: integration-service
          targetRevision: '{{.chartVersion}}'
          helm:
            releaseName: '{{.workload}}'
            valueFiles:
              - $values/apps/{{.workload}}/values-{{.env}}.yaml
        - repoURL: https://dev.azure.com/eygds/Platform/_git/gitops-config
          targetRevision: main
          ref: values
      destination:
        server: '{{.cluster}}'
        namespace: '{{.namespace}}'
      syncPolicy:
        automated:
          prune: '{{.autoPrune}}'
          selfHeal: true
        syncOptions:
          - ServerSideApply=true
```

```yaml
# gitops-config/apps/payments-adapter/config.yaml — what a product team owns
workload: payments-adapter
namespace: payments
chartVersion: "3.4.1"
```

**If they push back — "What's the blast radius of a bad ApplicationSet?"** — Enormous, and that's the honest risk: one bad template renders 160 broken Applications at once. Three mitigations I'd always have: `goTemplateOptions: ["missingkey=error"]` so a typo fails rendering instead of producing an empty and destructive value; `preserveResourcesOnDeletion: true` so deleting the ApplicationSet doesn't cascade into deleting workloads; and the ApplicationSet manifest itself under normal PR review with a CI job that runs the generator in dry-run and diffs the resulting Application list. Treat the ApplicationSet as the highest-privilege file in the repo, because it is.

---

### Q71. Sync policies, waves and hooks — how do you order a deployment?
`[HARD]`

**Answer:** Argo CD orders a sync in three nested levels. **Phases** first: `PreSync` → `Sync` → `PostSync`, with `SyncFail` on failure and `PostDelete` on app deletion (plus `PreDelete` and `Skip`). Within a phase, **waves** — the `argocd.argoproj.io/sync-wave` annotation, an integer that **defaults to 0** and may be negative. Within a wave, Argo CD orders by kind (namespaces before things in them) and then by name.

Two verified details worth quoting: Argo CD waits **2 seconds between waves** (configurable via `ARGOCD_SYNC_WAVE_DELAY`) so other controllers can react before it assesses health; and it only processes resources that are out-of-sync or unhealthy, advancing wave by wave and stopping if a wave doesn't become healthy.

For an integration workload the ordering that matters is: **schema/queue infrastructure before consumers**, and **database migrations before the code that needs them**.

```yaml
# wave -2: the namespace-scoped prerequisites
apiVersion: v1
kind: ConfigMap
metadata:
  name: payments-config
  annotations:
    argocd.argoproj.io/sync-wave: "-2"
---
# wave -1: secrets materialised from Key Vault before anything mounts them
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: partner-api-key
  annotations:
    argocd.argoproj.io/sync-wave: "-1"
spec:
  refreshInterval: 1h
  secretStoreRef: { name: azure-kv, kind: SecretStore }
  target: { name: partner-api-key, creationPolicy: Owner }
  data:
    - secretKey: apiKey
      remoteRef: { key: legacy-partner-api-key }
---
# PreSync hook: schema migration runs to completion BEFORE the new pods start
apiVersion: batch/v1
kind: Job
metadata:
  name: payments-db-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
    argocd.argoproj.io/sync-wave: "-1"
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 600
  template:
    spec:
      restartPolicy: Never
      serviceAccountName: payments-adapter
      containers:
        - name: migrate
          image: eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
          command: ["alembic", "upgrade", "head"]
          env:
            - name: AZURE_CLIENT_ID
              valueFrom:
                configMapKeyRef: { name: payments-config, key: azureClientId }
---
# wave 0 (default): the workload
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-adapter
---
# PostSync hook: smoke test. Fails -> the sync is marked failed.
apiVersion: batch/v1
kind: Job
metadata:
  name: payments-smoke-test
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: smoke
          image: eyintacr.azurecr.io/platform/smoke-runner:1.4.0
          args: ["--base-url", "http://payments-adapter.payments.svc:8000", "--suite", "payments"]
```

**If they push back — "What if the PreSync migration fails?"** — The sync stops at the PreSync phase and the workload is never updated, which is exactly right: the old code keeps running against the old schema. Then `SyncFail` hooks run for alerting or cleanup. The deeper discipline is that migrations must be **expand-only and backward-compatible** — add the column, don't rename it — so that even a successful migration leaves the currently-running old code working. That constraint is what makes rollback possible at all, and it's the same rule as the message-schema rule in §15.

---

### Q72. What is ArgoCD's health assessment and why does it matter?
`[MEDIUM]`

**Answer:** Argo CD tracks two orthogonal statuses. **Sync status** is "does the cluster match Git" — Synced or OutOfSync. **Health status** is "is the resource actually working" — Healthy, Progressing, Degraded, Suspended, Missing, Unknown. It ships built-in health checks for the standard kinds (a Deployment is Healthy when its updated replicas are available; a Service of type LoadBalancer is Healthy when it has an ingress IP) and you can write **custom Lua health checks** for CRDs.

Why it matters: sync alone tells you the YAML was applied, which is nearly worthless as a deployment signal. `--wait` on health, or a PostSync smoke test gated on health, is what makes "the deployment succeeded" mean something. It's also what progressive delivery hooks into.

```yaml
# argocd-cm ConfigMap — a custom health check for a CRD Argo doesn't know
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations.health.flagger.app_Canary: |
    hs = {}
    if obj.status ~= nil and obj.status.phase ~= nil then
      if obj.status.phase == "Succeeded" or obj.status.phase == "Initialized" then
        hs.status = "Healthy"
        hs.message = obj.status.phase
      elseif obj.status.phase == "Failed" then
        hs.status = "Degraded"
        hs.message = "Canary analysis failed; rolled back"
      else
        hs.status = "Progressing"
        hs.message = obj.status.phase
      end
      return hs
    end
    hs.status = "Progressing"
    hs.message = "Waiting for Canary status"
    return hs
```

**If they push back — "How do you alert on this?"** — Argo CD Notifications, subscribing to triggers like `on-sync-failed`, `on-health-degraded` and `on-sync-status-unknown`, with a Teams or PagerDuty provider. The one I care most about in an FS context is **`on-health-degraded` for prod applications**, because it catches the case where a sync succeeded and the workload then failed — which a CI-based deploy would have reported as green and walked away from. Argo CD also exports Prometheus metrics (`argocd_app_info` with sync and health labels), so the durable alert is a Prometheus rule on "app has been OutOfSync for more than 15 minutes", which catches both stuck syncs and unreverted drift.

---

### Q73. How do you do multi-cluster and multi-tenancy in ArgoCD?
`[HARD]` `[FS-relevant: segregation is an audit requirement]`

**Answer:** **Multi-cluster:** one Argo CD instance registers N clusters (`argocd cluster add`), and each Application's `destination.server` picks one. The alternative is an Argo CD per cluster. For financial services I usually argue for **one Argo CD per environment tier** — a non-prod instance managing dev/test/UAT clusters, and a separate prod instance — because a single instance managing prod holds prod credentials and becomes a crown-jewel target, and because environment segregation is usually an explicit control the auditor tests.

**Multi-tenancy** is the **AppProject**. A project constrains which repos an app may source from, which cluster/namespace pairs it may deploy to, which resource kinds it may create, and who may do what to it. Without projects, any team with Argo CD access can deploy anything anywhere — Argo CD's default project is `default` and it allows everything, which is the single most common misconfiguration.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: fs-integration-prod
  namespace: argocd
spec:
  description: Financial-services integration workloads, production

  sourceRepos:
    - https://dev.azure.com/eygds/Platform/_git/gitops-config
    - eyintacr.azurecr.io/helm

  destinations:
    - server: https://prod-aks.privatelink.uksouth.azmk8s.io:443
      namespace: payments
    - server: https://prod-aks.privatelink.uksouth.azmk8s.io:443
      namespace: settlement

  # this project may not create cluster-scoped resources at all
  clusterResourceWhitelist: []

  # and may not create these even inside its namespaces
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota
    - group: ''
      kind: LimitRange
    - group: networking.k8s.io
      kind: NetworkPolicy
    - group: rbac.authorization.k8s.io
      kind: ClusterRoleBinding

  roles:
    - name: release-manager
      description: May sync, may not edit the Application spec
      policies:
        - p, proj:fs-integration-prod:release-manager, applications, sync, fs-integration-prod/*, allow
        - p, proj:fs-integration-prod:release-manager, applications, get, fs-integration-prod/*, allow
      groups:
        - EY-GDS-Integration-ReleaseManagers      # Entra ID group via OIDC/Dex
    - name: developer
      description: Read-only in production
      policies:
        - p, proj:fs-integration-prod:developer, applications, get, fs-integration-prod/*, allow
      groups:
        - EY-GDS-Integration-Developers

  # no deploys during the settlement window or the market-open peak
  syncWindows:
    - kind: deny
      schedule: '0 7 * * 1-5'
      duration: 4h
      timeZone: Europe/London
      applications: ['*']
      manualSync: false          # not even a manual sync during the window
    - kind: allow
      schedule: '0 20 * * 1-4'
      duration: 3h
      timeZone: Europe/London
      applications: ['*']
```

The `namespaceResourceBlacklist` above is the platform boundary made concrete: ResourceQuota, LimitRange and NetworkPolicy are platform-owned, so a product team's Application literally cannot widen its own quota or open its own network policy.

**If they push back — "Sync windows sound like they'd block an emergency fix."** — They would, deliberately, and that's why the break-glass path is a *different* project with a different window policy and a different approver group, not a flag on this one. A deny window with `manualSync: false` is a real control an auditor can test; a window you can click past is theatre. The break-glass project's use is alerted on and reviewed.

---

### Q74. How does the image tag get into Git? Who commits it?
`[HARD]` `[the question that exposes whether you've really done GitOps]`

**Answer:** Three options, and the choice says a lot about the client's control posture. **One: CI commits.** The build pipeline updates the values file and pushes. Simple, and everyone starts here — but it puts a write credential to the config repo in CI, and it fills the repo history with bot commits. **Two: an image automation controller.** Flux's `ImageRepository`/`ImagePolicy`/`ImageUpdateAutomation`, or Argo CD Image Updater, watches the registry and writes the commit itself — CI never touches the config repo at all, which is the cleanest separation. **Three: a promotion PR.** The pipeline opens a pull request against the config repo; a human merges it. Slowest, and the only one that satisfies a strict four-eyes-on-production-change control.

For financial services I'd typically run **automated for dev and test, promotion PR for UAT and prod.** That gives velocity where it's cheap and an auditable human decision where it's required — and the PR *is* the change record.

```yaml
# Flux image automation: the controller writes the commit, not CI
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: payments-adapter
  namespace: flux-system
spec:
  image: eyintacr.azurecr.io/integration/payments-adapter
  interval: 5m
  provider: azure          # workload identity to ACR, no registry secret
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: payments-adapter
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: payments-adapter
  filterTags:
    pattern: '^main-[a-f0-9]+-(?P<ts>[0-9]+)$'
    extract: '$ts'
  policy:
    numerical:
      order: asc
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: dev-image-automation
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-config
  git:
    checkout:
      ref: { branch: main }
    commit:
      author:
        name: flux-image-automation
        email: flux@ey.com
      messageTemplate: |
        chore(dev): update {{range .Changed.Changes}}{{.OldValue}} -> {{.NewValue}}{{end}}
    push:
      branch: main
  update:
    path: ./clusters/dev
    strategy: Setters
```

```yaml
# the values file carries a setter marker the controller rewrites in place
image:
  repository: eyintacr.azurecr.io/integration/payments-adapter
  tag: main-9f2c1b4-1756089600 # {"$imagepolicy": "flux-system:payments-adapter:tag"}
```

**If they push back — "Why not just have ArgoCD track the `latest` tag?"** — Because that breaks every property GitOps exists to provide. Git no longer describes what's running, so you can't tell what version is in prod from the repo, `git revert` doesn't roll back, and the audit trail is gone. It also breaks reproducibility — redeploying the same commit six months later gets a different image. Track an immutable tag or, better, a digest, and let something explicitly update it.

---

### Q75. Argo CD RBAC and SSO — how do you wire it to the client's identity?
`[MEDIUM]`

**Answer:** Argo CD supports OIDC directly or via the bundled **Dex** connector. For an Azure client I'd point it at Entra ID as an OIDC provider, map Entra group object IDs into Argo CD's RBAC policy, and disable the local `admin` account entirely (`admin.enabled: false` in `argocd-cm`) so there is no shared credential. RBAC is Casbin-style policy lines in `argocd-rbac-cm`: `p, <subject>, <resource>, <action>, <object>, allow|deny`.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly          # deny-by-default posture
  scopes: '[groups, email]'
  policy.csv: |
    p, role:platform-admin, applications, *, */*, allow
    p, role:platform-admin, clusters, *, *, allow
    p, role:platform-admin, repositories, *, *, allow
    p, role:platform-admin, projects, *, *, allow

    p, role:integration-release, applications, sync, fs-integration-prod/*, allow
    p, role:integration-release, applications, action/*, fs-integration-prod/*, deny
    p, role:integration-release, applications, delete, */*, deny

    p, role:integration-dev, applications, *, fs-integration-nonprod/*, allow
    p, role:integration-dev, applications, get, fs-integration-prod/*, allow
    p, role:integration-dev, applications, sync, fs-integration-prod/*, deny

    g, 8f3c2a91-1111-2222-3333-444455556666, role:platform-admin     # Entra group objectId
    g, 7e2b1c80-aaaa-bbbb-cccc-ddddeeeeffff, role:integration-release
    g, 6d1a0b7f-9999-8888-7777-666655554444, role:integration-dev
```

Note the explicit `deny` lines: in Casbin, deny wins over allow, so an explicit deny on `applications, sync` for prod is a hard boundary even if a broader allow exists elsewhere.

**If they push back — "Isn't this a second RBAC system to maintain alongside Kubernetes RBAC?"** — Yes, and that's a genuine cost. They serve different purposes: Kubernetes RBAC controls what the *Argo CD service account* can do in the cluster (and it should be scoped per project where possible, not cluster-admin), while Argo CD RBAC controls what *humans* can do through Argo CD. I'd keep both minimal and drive both from the same Entra groups so there's one place to manage membership. The mitigating factor is that once GitOps is in place, humans need very little direct Kubernetes RBAC at all — read-only for debugging is usually enough.

---

### Q76. What does Argo CD *not* solve?
`[MEDIUM]` `[senior honesty signal]`

**Answer:** Four things. **Secrets** — you cannot commit them, so you need a separate mechanism (§13). **Infrastructure outside Kubernetes** — Argo CD reconciles Kubernetes resources; your Service Bus namespace and APIM instance still need Terraform or Bicep, unless you adopt Crossplane or ASO to represent them as CRDs, which is a significant commitment. **Progressive delivery** — Argo CD syncs, it doesn't do metric-based canary analysis; that's Argo Rollouts or Flagger (§14). And **ordering across applications** — sync waves order resources within one Application, not across a fleet; cross-app ordering needs App-of-Apps waves or an explicit dependency mechanism.

The fifth one people forget: **Argo CD does not review your change.** If a bad manifest is merged, Argo CD will faithfully and immediately deploy it everywhere it applies. GitOps moves the control point to the PR, so branch protection, CODEOWNERS and the CI checks on the config repo are now production controls, and they need to be treated with the same seriousness as the application repo's.

**If they push back — "Would you use Crossplane to manage Azure resources through Argo CD?"** — I'd be cautious. The appeal is one control plane and one reconciliation model for everything, with continuous drift correction on cloud resources — which Terraform genuinely lacks. The costs are real: you take a dependency on provider CRDs that lag the Azure API, your cluster becomes a single point of failure for infrastructure, and the operational model is unfamiliar to most client platform teams. For a client with a mature Kubernetes practice and many identical environments, it's a serious option. For a typical FS integration engagement I'd keep Terraform for cloud infrastructure and Argo CD for cluster workloads, and be clear about the seam between them.

---

## 12. Flux, and the honest ArgoCD-vs-Flux answer

### Q77. What are Flux's components and CRDs?
`[MEDIUM]`

**Answer:** Flux is a set of composable controllers — the **GitOps Toolkit** — rather than one application. **Source controller** owns `GitRepository`, `OCIRepository`, `HelmRepository`, `HelmChart`, `Bucket`; it fetches and verifies sources and exposes them as artefacts. **Kustomize controller** owns `Kustomization` and applies manifests. **Helm controller** owns `HelmRelease` and drives Helm installs/upgrades with remediation. **Notification controller** owns `Provider`, `Alert` and `Receiver` — outbound alerts and inbound webhooks. **Image automation controllers** own `ImageRepository`, `ImagePolicy` and `ImageUpdateAutomation`.

The design consequence: every Flux object is a small Kubernetes resource with an `interval`, its own `status` and conditions, and its own reconciler. There is no server, no UI and no database — Flux's state is Kubernetes' state. That's the philosophical difference from Argo CD.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: gitops-config
  namespace: flux-system
spec:
  interval: 1m
  url: https://dev.azure.com/eygds/Platform/_git/gitops-config
  ref:
    branch: main
  secretRef:
    name: azdo-git-credentials
  # commits must be signed by a key in this ConfigMap — supply-chain control on Git itself
  verify:
    mode: HEAD
    secretRef:
      name: gitops-signing-keys
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: payments-prod
  namespace: flux-system
spec:
  interval: 10m
  retryInterval: 1m
  timeout: 5m
  path: ./clusters/prod/payments
  prune: true
  wait: true                      # block until all applied resources are healthy
  sourceRef:
    kind: GitRepository
    name: gitops-config
  targetNamespace: payments
  serviceAccountName: flux-payments      # multi-tenancy: impersonate a scoped SA
  dependsOn:
    - name: infra-controllers            # cross-Kustomization ordering
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: payments-adapter
      namespace: payments
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: integration-service
  namespace: flux-system
spec:
  interval: 5m
  url: oci://eyintacr.azurecr.io/helm/integration-service
  ref:
    semver: '>=3.4.0 <4.0.0'
  provider: azure                 # workload identity, no registry secret
  verify:
    provider: cosign              # refuse an unsigned chart
    matchOIDCIdentity:
      - issuer: '^https://token\.actions\.githubusercontent\.com$'
        subject: '^https://github\.com/eygds/platform-charts/.*$'
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: payments-adapter
  namespace: payments
spec:
  interval: 10m
  chartRef:
    kind: OCIRepository
    name: integration-service
    namespace: flux-system
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
      remediateLastFailure: true   # roll back automatically on a failed upgrade
  driftDetection:
    mode: enabled                  # Helm's own drift correction
  values:
    image:
      repository: eyintacr.azurecr.io/integration/payments-adapter
      digest: sha256:9f2c1b4e...
    replicaCount: 3
```

**If they push back — "How do you debug Flux without a UI?"** — `flux get all -A` for the whole picture, `flux get kustomizations --watch`, then `flux events --for HelmRelease/payments-adapter -n payments` for the timeline, and `kubectl describe` on the object for conditions. `flux trace` answers "which Kustomization and which Git commit produced this Deployment", which is the question you actually have at 3am. There's also a Flux UI (Weave GitOps) if the client wants one, but I'd argue the absence of a UI is partly the point — if you need a UI to know what's deployed, Git isn't really your source of truth.

---

### Q78. Argo CD or Flux? Give me the honest comparison.
`[HARD]` `[opinion question — commit, then nuance]`

**Answer:** **Argo CD** if humans need to see and drive deployments — a strong UI, an application-centric model, per-application RBAC, sync windows, and a CLI operators like. **Flux** if the platform team wants composable controllers, a smaller footprint, no server to run and secure, and deep integration with Kubernetes-native tooling. Both are CNCF Graduated, both are production-grade, and the choice is more about the operating model than about capability.

For a financial-services engagement I'd usually land on **Argo CD**, and the deciding reasons are operational rather than technical: the UI is what makes a support analyst or a release manager able to answer "what's in prod and did it deploy cleanly" without cluster access, sync windows model a change freeze directly, and AppProjects give you the tenancy boundary an auditor wants to see. Flux's multi-tenancy via service-account impersonation is arguably cleaner in principle, but it's harder to demonstrate to a non-engineer.

| | Argo CD | Flux |
|---|---|---|
| Model | central application controller + API server | composable controllers, no server |
| UI | first-class, a real product | none built in (Weave GitOps is separate) |
| Tenancy | AppProject: repos, destinations, kinds, roles | namespace + `serviceAccountName` impersonation |
| Helm | renders via `helm template`, then applies | real `helm` releases via helm-controller |
| Image automation | Argo CD Image Updater (separate component) | first-class controllers |
| Multi-cluster | one instance manages many clusters | typically one Flux per cluster |
| Change freeze | `syncWindows` on the AppProject | `spec.suspend` / suspend the Kustomization |
| Progressive delivery | Argo Rollouts (same family) | Flagger (same family) |
| Footprint | heavier (server, Redis, repo server) | lighter |
| Best for | operator-facing, regulated, multi-team | platform-native, composable, automation-first |

**If they push back — "Can you run both?"** — Technically yes, and I've seen it where Flux bootstraps the cluster's platform layer and Argo CD manages application workloads. I'd avoid it. Two reconcilers means two places to look when something doesn't deploy, two RBAC models, and the genuine risk of both claiming the same resource and fighting. Pick one per cluster and write down which.

---

### Q79. How does Flux handle Helm differently from Argo CD?
`[MEDIUM]` `[a real technical difference worth knowing]`

**Answer:** Argo CD by default **renders** the chart (`helm template`) and applies the resulting manifests directly — so there is no Helm release object in the cluster, `helm list` shows nothing, and Argo CD's own history is the release history. Flux's helm-controller performs a **real Helm install/upgrade**, so there's a genuine Helm release secret, `helm list` works, `helm rollback` works, and chart hooks run as Helm hooks.

That matters in two situations. If a chart depends on Helm lifecycle hooks or on `.Release.IsUpgrade`, Argo CD's templating approach can behave differently. And if the client's operations team already knows `helm list` and `helm history`, Flux fits their muscle memory. Conversely, Argo CD's approach means every resource is directly visible and diffable in the UI, with no Helm state to get stuck — no more `another operation in progress` errors.

**If they push back — "Which do you prefer?"** — Argo CD's rendering model, for a specific reason: the diff. When a chart upgrade would change 40 resources, Argo CD shows me exactly which fields on which objects, before I sync. Helm's own diff story requires a plugin and isn't integrated into the deployment gate. In a regulated environment, "show the approver precisely what will change" is worth more than Helm release semantics.

---

### Q80. How do you bootstrap a cluster with GitOps?
`[MEDIUM]`

**Answer:** The bootstrap problem is "who installs the installer". Flux answers it directly with `flux bootstrap`, which installs the controllers *and* commits their own manifests to Git, so Flux thereafter manages itself. Argo CD's equivalent is to install it (Helm or manifests, ideally from Terraform), then apply a root App-of-Apps whose first child is Argo CD itself — self-management from that point on.

The layered order that matters for an integration platform:

```text
  Terraform            -> AKS cluster, node pools, ACR, Key Vault, VNet, workload identity
      │
      ▼
  Terraform (helm provider or a bootstrap job)
                       -> install Argo CD, apply the root Application
      │
      ▼
  root Application     -> wave -3: cert-manager, external-secrets, CSI driver
     (App-of-Apps)        wave -2: ingress-nginx / AGIC, Gateway API CRDs
                          wave -1: kube-prometheus-stack, OpenTelemetry Collector, Flagger
                          wave  0: ApplicationSet -> every integration workload
```

```bash
# Flux equivalent, one command, and Flux commits its own manifests
flux bootstrap git \
  --url=https://dev.azure.com/eygds/Platform/_git/gitops-config \
  --branch=main \
  --path=clusters/prod \
  --token-auth \
  --components-extra=image-reflector-controller,image-automation-controller
```

**If they push back — "Isn't installing Argo CD from Terraform a chicken-and-egg violation?"** — It's a deliberate boundary, not a violation. Terraform owns everything up to and including "a cluster with Argo CD running and pointed at a repo"; Argo CD owns everything inside the cluster from there. The alternative — Argo CD managing its own installation from zero — has no bootstrap path. What I *do* insist on is that Terraform's Argo CD install is minimal (the Helm release and the root Application, nothing else), so that the Terraform state doesn't slowly become a second, competing source of truth for cluster contents.

---

## 13. Secrets in GitOps

### Q81. You can't commit secrets to Git. So how do secrets reach a GitOps-managed workload?
`[HARD]` `[EVERYONE ASKS THIS — have the four options and a pick]`

**Answer:** Four approaches, and they differ on where the trust boundary sits. **Sealed Secrets** encrypts the secret with a cluster-specific public key so the ciphertext is safe to commit; the controller in the cluster holds the private key and decrypts. **SOPS** encrypts values in a YAML file using a KMS key (Azure Key Vault key, age, PGP); Flux's kustomize-controller decrypts inline. **External Secrets Operator** doesn't put the secret in Git at all — Git holds a *reference*, and the operator fetches from Key Vault and materialises a Kubernetes Secret. **Key Vault CSI driver** mounts the secret into the pod as a file at runtime, optionally syncing to a Kubernetes Secret.

The distinction I'd draw for an interviewer: the first two put **encrypted secret material in Git**; the last two put **only a pointer in Git**. For financial services I pick a pointer approach, because it keeps Key Vault as the single system of record — one rotation mechanism, one access log, one revocation point — and because "the encrypted secret is in Git forever, and today's crypto is not forever" is an argument a risk function finds persuasive.

| | Sealed Secrets | SOPS | External Secrets Operator | Key Vault CSI driver |
|---|---|---|---|---|
| What's in Git | ciphertext | ciphertext | a reference | a reference |
| Source of truth | Git | Git | Key Vault | Key Vault |
| Rotation | re-seal + commit + sync | re-encrypt + commit | automatic on `refreshInterval` | on `rotationPollInterval` |
| Revocation | must find and remove the commit | same | revoke in Key Vault, done | revoke in Key Vault, done |
| Creates a K8s Secret | yes | yes | yes | only with `secretObjects` sync |
| Works with | any GitOps tool | Flux native; Argo via a plugin | any | any (CSI volume) |
| Auth to backend | n/a | workload identity to KV key | workload identity | workload identity |
| FS verdict | avoid for prod | acceptable | **preferred** | good when you can mount a file |

**If they push back — "What's actually wrong with Sealed Secrets?"** — Three things, and they compound. The ciphertext is in Git permanently, so a future key compromise or crypto break is retroactive across all history. Rotation means a commit, so secret rotation and code review are now the same workflow, which is wrong. And the sealing key is cluster-specific, so disaster recovery into a new cluster means re-sealing every secret — which people discover during the DR test. It's a fine tool for a small team; it doesn't survive an FS audit.

---

### Q82. Show me External Secrets Operator and the Key Vault CSI driver.
`[MEDIUM]`

```yaml
# ── External Secrets Operator: Git holds a reference, ESO fetches from Key Vault ──
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-kv
  namespace: payments
spec:
  provider:
    azurekv:
      authType: WorkloadIdentity          # federated; no client secret in the cluster
      vaultUrl: https://kv-eyint-prod.vault.azure.net
      serviceAccountRef:
        name: payments-adapter
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: partner-credentials
  namespace: payments
spec:
  refreshInterval: 1h                     # rotation propagates without a deploy
  secretStoreRef:
    name: azure-kv
    kind: SecretStore
  target:
    name: partner-credentials
    creationPolicy: Owner                 # ESO owns the Secret; deleting the ES deletes it
    template:
      type: Opaque
      data:
        # compose a connection string from two vault secrets
        SFTP_URL: "sftp://{{ .sftpUser }}:{{ .sftpPassword }}@partner.example.com:22"
  data:
    - secretKey: sftpUser
      remoteRef:
        key: partner-sftp-user
    - secretKey: sftpPassword
      remoteRef:
        key: partner-sftp-password
```

```yaml
# ── Key Vault CSI driver: mount as a file, optionally sync to a Secret ──
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: payments-kv
  namespace: payments
spec:
  provider: azure
  parameters:
    clientID: 00001111-aaaa-2222-bbbb-3333cccc4444   # the workload identity's client ID
    usePodIdentity: 'false'
    useVMManagedIdentity: 'false'
    keyvaultName: kv-eyint-prod
    tenantId: aaaabbbb-0000-1111-2222-ccccddddeeee
    objects: |
      array:
        - |
          objectName: legacy-partner-api-key
          objectType: secret
        - |
          objectName: mtls-client-cert
          objectType: cert
  secretObjects:                     # optional: also project into a K8s Secret
    - secretName: partner-api-key
      type: Opaque
      data:
        - objectName: legacy-partner-api-key
          key: apiKey
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-adapter
  namespace: payments
spec:
  replicas: 3
  selector:
    matchLabels: { app: payments-adapter }
  template:
    metadata:
      labels:
        app: payments-adapter
        azure.workload.identity/use: 'true'
    spec:
      serviceAccountName: payments-adapter
      containers:
        - name: app
          image: eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
          volumeMounts:
            - name: kv
              mountPath: /mnt/secrets-store
              readOnly: true
      volumes:
        - name: kv
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes:
              secretProviderClass: payments-kv
```

Verified AKS details worth quoting: the add-on is enabled with `az aks enable-addons --addons azure-keyvault-secrets-provider`; it creates a managed identity named `azurekeyvaultsecretsprovider-xxxxx` in the `MC_` node resource group; autorotation is **disabled by default** with `enableSecretRotation: false` and a `rotationPollInterval` of **2m**; and if you restrict ingress to the cluster, ports **9808** and **8095** must be open. The identity needs *Key Vault Secrets User* for secrets and *Key Vault Certificate User* for certificates.

**If they push back — "A rotated secret is in the mounted file — does my app pick it up?"** — Not automatically, and this is the trap. With rotation enabled the file content is updated, but your process already read it at startup. Worse, the documented limitation: a container using a Secret or ConfigMap as a **`subPath` volume mount never receives updates at all** — that's a Kubernetes limitation, not an AKS one. So either the app watches the file and reloads (my preference — it's twenty lines), or you use a controller like Reloader to restart the Deployment when the projected Secret changes. Either way it's an explicit design decision, not something you get for free.

---

### Q83. Which do you pick for a financial-services client, and why?
`[MEDIUM]`

**Answer:** **External Secrets Operator with Key Vault and workload identity**, as the default. The reasoning is the audit story: Key Vault is the single system of record, so there is one place where a secret is created, one access log showing every read with an identity and a timestamp, one rotation mechanism, and one revoke. Nothing sensitive is in Git in any form, so a Git repo compromise is not a secret compromise. And the workload's identity is federated, so there's no bootstrap secret either.

I'd add the **Key Vault CSI driver** alongside it for the specific cases where a file is the right shape — an mTLS client certificate and key, an SSH key for a partner SFTP — because mounting a cert file avoids base64-in-a-Secret gymnastics and keeps the private key off the etcd datastore.

And the control that makes it real: **Kubernetes Secrets encrypted at rest with a customer-managed key in Key Vault (KMS etcd encryption on AKS)**, plus RBAC so that no human has `get secrets` in the prod namespace. Otherwise you've moved the secret from Git into etcd, where anyone with namespace read can `kubectl get secret -o yaml`.

**If they push back — "What about HashiCorp Vault?"** — Genuinely better if the client already runs it or needs what it uniquely does: dynamic short-lived database credentials, its own PKI issuing short-lived certificates, transit encryption as a service. Those are real capabilities Key Vault doesn't match. The cost is that you're now operating a stateful, HA, seal/unseal-managed cluster with its own DR story — and at a Microsoft-centric client, Key Vault is already approved, already integrated with Entra ID, and already in the auditor's model. I'd propose Vault when dynamic credentials are a stated requirement, and Key Vault otherwise. ESO speaks to both, so the choice isn't load-bearing on the Kubernetes side.

---

## 14. Progressive delivery: Flagger and Argo Rollouts

### Q84. What is progressive delivery and what does it need underneath?
`[MEDIUM]`

**Answer:** Progressive delivery is automated, metric-driven release: instead of a human watching a dashboard after a deploy, a controller shifts a small slice of traffic to the new version, evaluates objective metrics against thresholds for a fixed period, and either advances the traffic weight or rolls back — with no human in the loop.

What it needs underneath is the part candidates miss. **Traffic splitting** — something that can send 10% of requests to a different backend: a service mesh (Istio, Linkerd, App Mesh, Kuma), the Gateway API, or an ingress controller that supports weighting (NGINX, Contour, Traefik, Gloo, APISIX, Skipper). **A metrics source** — Prometheus, Datadog, App Insights — with meaningful SLI queries. And **enough traffic** that 10% of it is statistically meaningful in a five-minute window; a service handling twelve requests an hour cannot be canaried on error rate.

Blue/green is the exception: Flagger's docs are explicit that **for blue/green no service mesh or ingress controller is required** — plain Kubernetes networking suffices, because you're switching a selector rather than splitting traffic.

**If they push back — "Our integration service is a queue consumer with no HTTP traffic. Can you canary it?"** — Not with traffic weights, because there's no request path to split. What you can do is a **capacity-based canary**: run one canary replica alongside N stable replicas, and because they're competing consumers on the same queue, the canary naturally receives roughly 1/(N+1) of the messages. Then analyse *consumer* metrics — dead-letter rate, message processing duration, abandon/completion ratio — and scale it up or kill it. Flagger can drive that with a custom `MetricTemplate`. It's a genuinely different shape from HTTP canary and knowing that distinction is a senior signal.

---

### Q85. Show me a Flagger Canary for an integration service.
`[HARD]`

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: payments-adapter
  namespace: payments
spec:
  provider: istio
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payments-adapter
  autoscalerRef:
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    name: payments-adapter
  progressDeadlineSeconds: 600      # give up and roll back if not progressing

  service:
    port: 8000
    targetPort: 8000
    gateways:
      - istio-system/internal-gateway
    hosts:
      - payments.internal.ey.net
    trafficPolicy:
      tls:
        mode: ISTIO_MUTUAL          # mTLS between mesh workloads

  analysis:
    interval: 1m                    # evaluate every minute
    threshold: 5                    # 5 failed checks -> rollback
    maxWeight: 50                   # never exceed 50% before promotion
    stepWeight: 10                  # 10% -> 20% -> ... -> 50% -> promote

    metrics:
      - name: request-success-rate  # built-in Istio metric
        thresholdRange:
          min: 99
        interval: 1m
      - name: request-duration      # built-in: P99 latency in ms
        thresholdRange:
          max: 500
        interval: 1m
      - name: servicebus-deadletter-rate
        templateRef:
          name: sb-deadletter
          namespace: payments
        thresholdRange:
          max: 0.1                  # messages/sec into the DLQ
        interval: 1m

    webhooks:
      - name: contract-conformance
        type: pre-rollout           # runs BEFORE any traffic is shifted
        url: http://flagger-loadtester.payments/
        timeout: 120s
        metadata:
          type: bash
          cmd: "schemathesis run http://payments-adapter-canary.payments:8000/openapi.json --checks all"
      - name: load-test
        type: rollout               # runs during each analysis interval
        url: http://flagger-loadtester.payments/
        timeout: 30s
        metadata:
          cmd: "hey -z 1m -q 20 -c 4 http://payments-adapter-canary.payments:8000/healthz"
      - name: notify-oncall
        type: rollback
        url: http://flagger-loadtester.payments/
        timeout: 15s
        metadata:
          type: bash
          cmd: "curl -sS -X POST -d 'payments-adapter canary rolled back' $ONCALL_WEBHOOK"
---
apiVersion: flagger.app/v1beta1
kind: MetricTemplate
metadata:
  name: sb-deadletter
  namespace: payments
spec:
  provider:
    type: prometheus
    address: http://prometheus.monitoring:9090
  query: |
    sum(
      rate(servicebus_deadletter_messages_total{
        namespace="{{ namespace }}",
        queue="payments-in",
        version="{{ target }}"
      }[{{ interval }}])
    )
```

Flagger rolls back when metrics fall outside `thresholdRange`, when pod health checks fail, when a webhook returns non-2xx, or when `progressDeadlineSeconds` elapses without progress — and the failed-check count reaching `threshold` is what triggers it. Flagger supports canary, A/B testing (header/cookie routing), blue/green, blue/green with mirroring (shadow traffic), and canary with session affinity.

**If they push back — "How long does a full canary take, and is that acceptable in a change window?"** — With `interval: 1m`, `stepWeight: 10` and `maxWeight: 50` it's five successful intervals plus promotion — roughly 6–8 minutes, plus the pre-rollout webhook. That fits a change window fine. What doesn't fit is the naive version people reach for first: `interval: 5m`, `stepWeight: 5`, `maxWeight: 100`, which is an hour and a half. I'd tune `interval` to be at least long enough for the metric to be meaningful — for a P99 latency query, at least a couple of scrape intervals — and no longer.

---

### Q86. Argo Rollouts — how does it differ from Flagger?
`[MEDIUM]`

**Answer:** Both do metric-analysed progressive delivery; they differ in shape. **Argo Rollouts replaces the Deployment** with a `Rollout` CRD that owns the ReplicaSets and expresses the release as an explicit list of `steps` — setWeight, pause, analysis, in whatever order you write. **Flagger keeps your Deployment** and drives it from the outside, generating primary/canary Deployments and Services, with the progression expressed declaratively as interval/stepWeight/maxWeight rather than as a step list.

Practically: Argo Rollouts gives you finer manual control (a `pause` with no duration waits for a human `kubectl argo rollouts promote`), integrates with the Argo CD UI, and its explicit steps read like a runbook. Flagger is less invasive — your Deployment stays a Deployment — and its automation is more opinionated. If the client is on Argo CD, use Argo Rollouts; if on Flux, use Flagger. They're from the same families for a reason.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payments-adapter
  namespace: payments
spec:
  replicas: 6
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: payments-adapter
  strategy:
    canary:
      canaryService: payments-adapter-canary
      stableService: payments-adapter-stable
      trafficRouting:
        istio:
          virtualService:
            name: payments-adapter
            routes: [primary]
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2               # start analysing from the 20% step
        args:
          - name: service-name
            value: payments-adapter-canary.payments.svc.cluster.local
      steps:
        - setWeight: 10
        - pause: { duration: 5m }
        - setWeight: 20
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: {}                   # no duration = wait for a human promote
        - setWeight: 100
  template:
    metadata:
      labels:
        app: payments-adapter
    spec:
      serviceAccountName: payments-adapter
      terminationGracePeriodSeconds: 90
      containers:
        - name: app
          image: eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
          ports:
            - containerPort: 8000
          readinessProbe:
            httpGet: { path: /readyz, port: 8000 }
          resources:
            requests: { cpu: 200m, memory: 256Mi }
            limits:   { memory: 512Mi }
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: payments
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      count: 5
      successCondition: result[0] >= 0.99
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(istio_requests_total{
              destination_service=~"{{args.service-name}}", response_code!~"5.."
            }[1m]))
            /
            sum(rate(istio_requests_total{
              destination_service=~"{{args.service-name}}"
            }[1m]))
```

```bash
kubectl argo rollouts get rollout payments-adapter -n payments --watch
kubectl argo rollouts promote payments-adapter -n payments
kubectl argo rollouts abort  payments-adapter -n payments     # immediate rollback to stable
kubectl argo rollouts undo   payments-adapter -n payments --to-revision=3
```

**If they push back — "Does GitOps conflict with progressive delivery? Argo CD wants the cluster to match Git, but Rollouts is deliberately mid-flight."** — Excellent question and it's the real integration issue. It works because the *desired* state in Git is the `Rollout` object, not the ReplicaSets — Argo CD reconciles the Rollout spec, and the Rollout controller owns the ReplicaSets and traffic weights underneath. You do need Argo CD to understand Rollout health, which it does natively for Argo Rollouts, and for Flagger you add the Lua health check from §Q72 so a canary in progress reads as *Progressing* rather than *Degraded*. Without that, Argo CD reports a healthy canary as degraded and people learn to ignore the status.

---

### Q87. What metrics do you actually canary an integration service on?
`[MEDIUM]` `[integration-specific — this differentiates you]`

**Answer:** Not just HTTP error rate, because for an integration service the interesting failures are asynchronous and downstream. I'd analyse four families. **Request health** — success rate and P99 latency, if there's a synchronous path. **Consumer health** — messages completed per second, abandon rate, and the one that matters most, **dead-letter rate**, because a canary that parses messages incorrectly will silently DLQ them while returning 200s on its health endpoint. **Downstream health** — error rate and latency of the calls the service makes *outbound* to SAP or the partner API, since a bad canary often breaks the backend contract rather than its own. And **lag** — queue depth or consumer lag trend, which catches a canary that is correct but slower.

The rule I'd state: **canary on the metric that would page you**, not on the metric that's easy to query. For a payments adapter that's dead-letter rate and settlement-file completeness, not CPU.

```promql
# dead-letter rate attributable to the canary version — the one that matters
sum(rate(servicebus_deadletter_total{queue="payments-in", version="canary"}[2m]))

# outbound dependency error rate from the canary
sum(rate(http_client_requests_total{
  source_version="canary", target="sap-erp", status=~"5.."
}[2m]))
/
sum(rate(http_client_requests_total{source_version="canary", target="sap-erp"}[2m]))

# is the canary keeping up? completion rate per replica vs stable
sum(rate(messages_completed_total{version="canary"}[2m])) / count(up{version="canary"})
  <
sum(rate(messages_completed_total{version="stable"}[2m])) / count(up{version="stable"}) * 0.8
```

**If they push back — "Dead-letter rate has a lag — a poison message takes `maxDeliveryCount` retries before it DLQs. Doesn't that make it useless as a canary signal?"** — Sharp, and correct. With `maxDeliveryCount: 10` and a 60-second lock duration, a message the canary can't parse takes up to ten minutes to reach the DLQ, by which point the canary may have been promoted. So I pair it with a **leading indicator** — the *abandon* rate, or an explicit `message_processing_failed_total` counter the application emits on the first failure — and use the DLQ rate as the slower confirming signal. This is exactly why you instrument the application for canary analysis rather than relying only on infrastructure metrics.

---

## 15. Deployment strategies for stateful integration workloads

### Q88. Name the deployment strategies and when each is right.
`[EASY]` `[near-certain]`

**Answer:** Seven, and they trade downtime against cost against confidence.

| Strategy | Mechanism | Downtime | Cost | Use when |
|---|---|---|---|---|
| **Recreate** | kill all old, start all new | yes | 1× | old and new genuinely cannot coexist — an exclusive DB lock, a single-writer file consumer |
| **Rolling** | replace N at a time | no | ~1.1× | the default for stateless HTTP; versions must be compatible |
| **Blue/green** | two full environments, switch the router | no | 2× | instant rollback matters more than cost; DB schema is compatible both ways |
| **Canary** | small % of traffic, measure, advance | no | ~1.1× | you have traffic volume and meaningful metrics |
| **A/B** | route by header/cookie/user attribute | no | ~1.1× | testing a behaviour change on a cohort, not a safety check |
| **Shadow / mirror** | duplicate real traffic to the new version, discard responses | no | 2× | validating a rewrite against production traffic with zero user risk |
| **Feature flag** | one binary, behaviour toggled at runtime | no | 1× | decoupling deploy from release; the only way to "roll back" in seconds |

The one to be precise about, because interviewers test it: **canary and A/B are not the same thing.** Canary splits traffic randomly to answer "is this version safe". A/B splits deterministically by user attribute to answer "which version performs better commercially". Different question, different routing, different analysis.

**If they push back — "Which does Kubernetes give you natively?"** — Only Recreate and RollingUpdate, as `Deployment.spec.strategy`. Blue/green is achievable by hand with two Deployments and flipping a Service selector. Canary with real traffic weights needs a mesh or a weighting-capable ingress, plus a controller to drive it — which is exactly why Flagger and Argo Rollouts exist. Saying that clearly is a good signal, because a lot of people claim "Kubernetes does canary" when what they mean is "I ran two replica sets and hoped".

---

### Q89. Now the hard version: how do you do a rolling update of a **queue consumer with in-flight messages**?
`[HARD]` `[THE integration question — this is where you separate yourself]`

**Answer:** The core problem is that a rolling update sends SIGTERM to a pod that is holding messages under lock. If the process dies without settling them, the broker redelivers after the lock expires — so at best you get duplicate processing and a latency spike, and at worst, if the work isn't idempotent, you get double payments.

The fix has four parts and they must all be present. **One: handle SIGTERM** — stop *pulling* new messages immediately, finish the ones in hand, settle them, then exit. **Two: set `terminationGracePeriodSeconds` longer than your worst-case single-message processing time** — the Kubernetes default is **30 seconds**, and if your handler can take 60, the default guarantees you get SIGKILLed mid-message. **Three: make the consumer idempotent anyway**, because a node can be lost without any grace period at all. **Four: cap `maxUnavailable`** so you never drain more consumers than the remaining ones can cover.

```python
# app/consumer.py — a Service Bus consumer that drains cleanly on SIGTERM
import asyncio
import logging
import os
import signal

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import ServiceBusClient

LOG = logging.getLogger("consumer")

FQDN = os.environ["SERVICEBUS_FQDN"]
QUEUE = os.environ["SERVICEBUS_QUEUE"]
MAX_WAIT = int(os.getenv("RECEIVE_MAX_WAIT_SECONDS", "5"))
BATCH = int(os.getenv("RECEIVE_BATCH_SIZE", "10"))

_shutdown = asyncio.Event()


def _request_shutdown(signum: int) -> None:
    """Stop pulling NEW work. Messages already in hand are finished first."""
    LOG.info("received %s: draining, will not fetch more", signal.Signals(signum).name)
    _shutdown.set()


async def handle(msg: ServiceBusReceivedMessage) -> None:
    """Idempotent by construction: keyed on the business id, not on delivery."""
    body = b"".join(msg.body).decode("utf-8")
    LOG.info("processing message_id=%s seq=%s", msg.message_id, msg.sequence_number)
    await asyncio.sleep(0)  # replace with the real handler
    del body


async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _request_shutdown, sig)

    credential = DefaultAzureCredential()
    try:
        async with ServiceBusClient(FQDN, credential) as client:
            receiver = client.get_queue_receiver(queue_name=QUEUE, max_wait_time=MAX_WAIT)
            async with receiver:
                while not _shutdown.is_set():
                    batch = await receiver.receive_messages(
                        max_message_count=BATCH, max_wait_time=MAX_WAIT
                    )
                    for msg in batch:
                        try:
                            await handle(msg)
                            await receiver.complete_message(msg)
                        except Exception:
                            LOG.exception(
                                "handler failed message_id=%s; abandoning for redelivery",
                                msg.message_id,
                            )
                            await receiver.abandon_message(msg)
                LOG.info("shutdown requested; receive loop exited cleanly")
    finally:
        await credential.close()
    LOG.info("drained")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-consumer
  namespace: payments
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0        # never lose consumer capacity during the roll
  selector:
    matchLabels: { app: payments-consumer }
  template:
    metadata:
      labels:
        app: payments-consumer
        azure.workload.identity/use: 'true'
    spec:
      serviceAccountName: payments-adapter
      # MUST exceed worst-case single-message processing time + settle time.
      # Kubernetes default is 30s; ours is 120s because the SAP call can take 90s.
      terminationGracePeriodSeconds: 120
      containers:
        - name: consumer
          image: eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
          command: ["python", "-m", "app.consumer"]   # exec form: PID 1 gets SIGTERM
          lifecycle:
            preStop:
              exec:
                # only needed if the pod ALSO serves HTTP: lets endpoint removal
                # propagate before the process starts refusing connections
                command: ["sh", "-c", "sleep 5"]
          resources:
            requests: { cpu: 200m, memory: 256Mi }
            limits:   { memory: 512Mi }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: payments-consumer
  namespace: payments
spec:
  minAvailable: 4              # node drains and cluster upgrades respect this too
  selector:
    matchLabels: { app: payments-consumer }
```

Two details that make this a senior answer: `command:` in **exec form** so the Python process is PID 1 and actually receives SIGTERM (shell form wraps it in `/bin/sh -c`, which does not forward signals — see [file 04 §3](04-microservices-containers-kubernetes.md)); and `maxUnavailable: 0` with `maxSurge: 1`, because for a consumer, capacity lost during a roll turns into queue depth and eventually into a breached SLA.

**If they push back — "What if the grace period expires anyway?"** — Then the kubelet sends SIGKILL, the process dies holding locks, and the broker redelivers after the lock duration expires — 60 seconds by default on Service Bus, up to 5 minutes maximum, or until `maxDeliveryCount` is hit. That's why the fourth requirement is non-negotiable: the handler is idempotent, keyed on the business identifier, with a dedupe table or Service Bus duplicate detection. Graceful shutdown reduces the frequency of redelivery; idempotency is what makes redelivery *safe*. Never rely on graceful shutdown alone — a node can be lost with no grace period at all.

---

### Q90. Explain the pod termination sequence precisely.
`[HARD]`

**Answer:** When a pod is deleted, two things happen **concurrently**, and that concurrency is the source of most deployment errors. On one path, the pod is marked Terminating and removed from all Service Endpoints/EndpointSlices, which then has to propagate to kube-proxy on every node and to any ingress controller or mesh sidecar. On the other path, the kubelet runs the `preStop` hook if there is one, then sends **SIGTERM** to PID 1 of each container, then waits up to `terminationGracePeriodSeconds` (**default 30**), then sends **SIGKILL**.

The race: endpoint removal is eventually consistent across the cluster, so for a short window after SIGTERM, some proxies still route traffic to a pod that has begun shutting down. That's what causes the "a few 502s on every deploy" symptom nobody can explain.

```text
  kubectl delete pod / rollout replaces it
        │
        ├─────────────► API server marks pod Terminating
        │                     │
        │                     ▼
        │               removed from EndpointSlice
        │                     │  (propagates to kube-proxy on every node,
        │                     │   to ingress, to mesh sidecars — NOT instant)
        │                     ▼
        │               traffic stops arriving  ◄── this can lag SIGTERM
        │
        └─────────────► kubelet: preStop hook (if any) runs to completion
                              │
                              ▼
                        SIGTERM to PID 1
                              │  ... grace period counts down (default 30s) ...
                              │  (the preStop hook's duration is INSIDE the grace period)
                              ▼
                        SIGKILL if still alive
```

Two consequences to state. **For an HTTP server**, add a `preStop: sleep 5` so endpoint removal wins the race, then let SIGTERM start a graceful shutdown — uvicorn/gunicorn will finish in-flight requests. **For a queue consumer**, `preStop` is not needed (nothing is routing to it), but the grace period must cover the worst-case message. And note the preStop hook's execution time is *deducted from* the grace period — it does not extend it.

**If they push back — "Why not just make the readiness probe fail instead of a preStop sleep?"** — Because failing readiness has exactly the same propagation delay as endpoint removal — the probe result must be observed, the endpoint updated, and the update distributed. It's the same race, not a fix for it. The `preStop` sleep works because it delays SIGTERM itself, giving the eventual consistency time to converge while the pod is still fully serving. It's crude, and it's the pattern the Kubernetes community actually converged on.

---

### Q91. Blue/green for a queue consumer — does it even make sense?
`[HARD]`

**Answer:** Not in the HTTP sense, because there is no router to flip. But there are two things that do work. **Consumer-group blue/green** works on Kafka or Event Hubs, where green joins as a *separate consumer group* reading from the same partitions — it processes everything independently, you compare its outputs against blue's, and cutover means stopping blue and pointing downstream at green's output. That's genuinely blue/green and it's how you validate a rewrite. **Broker-level blue/green** works on Service Bus with a topic: add a second subscription for green, let both process, and use a filter or a downstream switch to decide whose output counts.

The critical caveat: **this only works if processing is side-effect-free or the side effects are separable.** If both blue and green post to SAP, you've double-posted. So in practice green either writes to a shadow destination, or runs in a mode where the write is stubbed and only the transformation output is compared. That's shadow/mirror deployment more than blue/green, and it's the right tool for validating an integration rewrite.

```yaml
# Service Bus topic: green gets its own subscription, output goes to a shadow queue
# (Terraform sketch — see §9 for the full module)
resource "azurerm_servicebus_subscription" "green_shadow" {
  name               = "payments-green-shadow"
  topic_id           = azurerm_servicebus_topic.payments.id
  max_delivery_count = 10
}
```

```python
# the green consumer runs with side effects redirected, and diffs against blue
WRITE_MODE = os.getenv("WRITE_MODE", "live")   # "live" | "shadow"

async def emit(result: dict[str, object]) -> None:
    if WRITE_MODE == "shadow":
        await shadow_store.put(result)          # blob/table for later comparison
    else:
        await sap_client.post_document(result)  # the real side effect
```

**If they push back — "Isn't that just a lot of machinery to avoid a rolling update?"** — For a routine change, yes, and I'd do a rolling update. This is for the case that actually justifies it: replacing an entire legacy adapter, or a canonical-model change where you need evidence that the new implementation produces byte-identical output on a week of real production traffic. In financial services that evidence is often a precondition for the change board's approval, so the machinery buys you the approval, not just the safety.

---

### Q92. The message-schema rule: what is it and why does it govern deployment order?
`[HARD]` `[the single most valuable rule in this section]`

**Answer:** **A schema change ships one full release ahead of the code that requires it.** Concretely: release N makes the consumer *tolerate* the new field — reads it if present, defaults it if absent — and changes nothing about what producers emit. Release N+1 makes the producer start emitting it. Release N+2, optionally, removes the tolerance.

The reason is that during any rolling update, and for the entire time messages sit in a queue, **old and new versions coexist**. A message produced by a new pod may be consumed by an old pod. A message sitting in a queue for two days will be consumed by whatever is running when it's picked up — which might be two releases later. So producer and consumer are never atomically upgraded, and any change that requires them to be is an outage.

This is the same discipline as expand/contract database migration, applied to the wire format: **expand, migrate, contract**, with a release boundary between each.

```python
# app/contracts.py — a consumer that tolerates both the old and the new shape
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentInstructionV1(BaseModel):
    """Wire contract. Additive changes only within a major version."""

    model_config = ConfigDict(extra="ignore")   # forward compatible: ignore unknown fields

    schema_version: Literal[1] = 1
    payment_id: str
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    value_date: date

    # ADDED in release N. Optional with a default, so release N-1 messages still parse
    # and release N-1 CODE ignores it. Becomes required (no default) no earlier than N+2.
    settlement_account: str | None = None

    @property
    def effective_settlement_account(self) -> str:
        # the tolerance: derive the old behaviour when the new field is absent
        return self.settlement_account or _legacy_account_for(self.currency)


def _legacy_account_for(currency: str) -> str:
    return {"GBP": "GB-DEFAULT-01", "EUR": "EU-DEFAULT-01"}.get(currency, "XX-DEFAULT-01")
```

```text
  Release N     consumer tolerates settlement_account (optional, defaulted)
                producer unchanged                          <- deploy consumers FIRST
  Release N+1   producer emits settlement_account
                consumer unchanged                          <- deploy producers SECOND
  Release N+2   consumer requires settlement_account, tolerance removed
                (only after the queue's max message TTL has elapsed since N+1)
```

That last parenthesis is the detail people miss: you cannot remove the tolerance until every message written before N+1 has expired or been consumed. If the queue's `defaultMessageTimeToLive` is `P14D`, release N+2 is at least fourteen days after N+1.

**If they push back — "What if I need a breaking change?"** — Then it isn't a schema change, it's a **new schema**: a new message type, or a new topic/queue, with both running in parallel. Producers dual-write for a period, consumers of the old type are migrated one at a time, and the old path is decommissioned when its traffic reaches zero — which you verify with a metric, not with an assumption. It's more work, and it's the only way that doesn't require a synchronised deployment of systems owned by different teams. More on contract versioning in [API Design](01-api-design-rest-soap-graphql-openapi.md) and [Messaging](03-messaging-and-event-streaming.md).

---

### Q93. How do you deploy a batch job that runs through the messaging layer?
`[MEDIUM]` `[JD responsibility #4 — "Implement Batch Jobs using event streaming"]`

**Answer:** The deployment question for a batch workload is different from a service: the risk isn't downtime, it's **deploying mid-run**. A nightly job that processes 400,000 settlement records must not be replaced halfway through, because you'd either duplicate or drop a slice.

So three rules. **One: the job is a `Job`/`CronJob`, not a Deployment**, and a new image version affects the *next* run, not the current one — that's automatic and it's why the shape matters. **Two: use a leader or a lock** if the batch is driven by a long-lived consumer rather than a scheduled job, so a rolling update can't leave two coordinators active. **Three: make the unit of work a message, not the whole batch** — the "batch job over event streaming" pattern is exactly this: a control message fans out into N work messages, each independently retryable and idempotent, so a deploy mid-run costs you at most the in-flight messages, which redeliver.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: settlement-fanout
  namespace: payments
spec:
  schedule: "0 2 * * 1-5"          # 02:00, weekdays
  timeZone: Europe/London
  concurrencyPolicy: Forbid         # never two runs at once
  startingDeadlineSeconds: 600      # if the controller was down, skip rather than pile up
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 14
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600
      template:
        metadata:
          labels:
            azure.workload.identity/use: 'true'
        spec:
          restartPolicy: Never
          serviceAccountName: payments-adapter
          terminationGracePeriodSeconds: 60
          containers:
            - name: fanout
              image: eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
              command: ["python", "-m", "app.batch.settlement_fanout"]
              env:
                - name: BATCH_DATE
                  value: "auto"
```

The workers that consume the fanned-out messages are a normal Deployment, scaled by **KEDA** on queue depth (see [file 04 §11](04-microservices-containers-kubernetes.md)), and they follow §Q89's drain rules. That combination — CronJob to fan out, KEDA-scaled consumers to do the work — is exactly what the JD's oddly-worded "Batch Jobs using event streaming" means, and it's the direct replacement for cron-and-a-shared-drive.

**If they push back — "How do you know the batch completed?"** — Not by the CronJob's exit code, because the fanout job succeeds the moment it has enqueued the work. You need an explicit completion signal: a run record with an expected count written at fanout, incremented by each worker (idempotently, keyed on the work item id), and a reconciliation check — a second scheduled job, or a Durable Functions monitor — that alerts when the count hasn't reached the expected total by an SLA time. That reconciliation job *is* the control an FS auditor asks about, because "the file was processed" needs evidence, not an assumption.

---

## 16. CI/CD security & compliance for financial services

> Everything in this section is what turns a working pipeline into one that survives an audit. Domain context and the regulatory vocabulary are in [Financial Services Integration](12-financial-services-integration.md).

### Q94. What is separation of duties in a CI/CD context, and how do you implement it?
`[HARD]` `[FS-critical]`

**Answer:** Separation of duties means no single individual can unilaterally move a change into production. In a pipeline that decomposes into three concrete controls. **The author cannot approve** — branch protection requires a review from someone else, and the production environment's approver group excludes the person who triggered the run. **The approver cannot alter what they approved** — this is why the pipeline applies a *saved* Terraform plan and deploys a *digest-pinned* image, so approval binds to an immutable artefact. **Nobody has standing production write access outside the pipeline** — human access to prod resources is PIM-eligible, just-in-time, approval-gated and time-boxed, and in a GitOps cluster nobody has cluster write at all.

The thing that makes it real rather than declared: the identity that deploys is not an identity any human can assume. It's a federated workload identity bound to a specific pipeline and environment. An engineer cannot borrow it.

```text
  Control                          Implementation                                Evidence for the auditor
  ─────────────────────────────    ──────────────────────────────────────────    ────────────────────────────
  Author ≠ reviewer                branch protection, required reviewers,        PR record: author, reviewers,
                                   CODEOWNERS on infra/ and gitops-config/       timestamps, approving commit SHA
  Author ≠ deployment approver     ADO environment approvals with the            environment approval log
                                   requester excluded / GH prevent-self-review
  Approved artefact is immutable   digest-pinned image, saved tfplan,            image digest + cosign signature
                                   cosign signature verified at admission        + admission decision log
  No standing prod access          PIM-eligible only, GitOps = no cluster        PIM activation records with
                                   write for humans                              justification and approver
  All changes via pipeline         prod service connection restricted to         service connection auth list;
                                   template-checked pipelines; Azure Policy      Azure Activity Log by principal
  Emergency path is auditable      separate break-glass pipeline, single         break-glass run + auto-raised
                                   approver, auto-incident, 48h review           incident + post-review record
```

**If they push back — "The team is four people. Separation of duties is impossible."** — It's harder, not impossible, and I'd say what actually changes. Author-and-approver separation still works with four people. What breaks is having a distinct release manager role. The compensating controls I'd propose: mandatory two-person review on anything touching `infra/` or the GitOps config, automated gates doing as much as possible so human judgement is needed less often, and a **detective** control to substitute for the missing preventive one — a daily automated report of every production change with its approver, reviewed by someone outside the team, usually the service owner. Auditors accept compensating controls when you name them as such and evidence them.

---

### Q95. How do you evidence "who deployed what, when" to an auditor?
`[MEDIUM]` `[FS-critical]`

**Answer:** I'd give them a chain, not a log, because the question behind the question is "can you prove this specific production binary came from reviewed source". The chain is: **running image digest** → **cosign signature and provenance attestation**, which names the workflow, the repo and the commit → **the commit** in Git with its author and reviewers → **the PR** with its approval record → **the pipeline run** with its approvers and timestamps → **the deployment record** (Argo CD's sync history or the ADO environment's deployment history) → **the Azure Activity Log** entry showing which identity made the change.

Each link is independently verifiable, and none of it depends on anyone having written a change document by hand.

```bash
# 1. what digest is actually running in prod?
kubectl get pods -n payments -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'

# 2. verify the signature and read the provenance — which workflow, which commit?
IMG=eyintacr.azurecr.io/integration/payments-adapter@sha256:9f2c1b4e
cosign verify "$IMG" \
  --certificate-identity-regexp '^https://github\.com/eygds/platform-workflows/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

cosign verify-attestation "$IMG" --type slsaprovenance \
  --certificate-identity-regexp '^https://github\.com/eygds/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  | jq -r '.payload' | base64 -d | jq '.predicate.invocation.configSource'

# 3. the SBOM that was attested at build time
cosign download attestation "$IMG" | jq -r '.payload' | base64 -d | jq '.predicate.components | length'

# 4. GitOps deployment history — who synced, from which revision, when
argocd app history payments-adapter-prod
kubectl -n payments get rollout payments-adapter -o jsonpath='{.status.currentPodHash}'

# 5. Azure control-plane changes by principal, for the change window
az monitor activity-log list \
  --resource-group rg-int-prod-uks \
  --start-time 2026-08-20T00:00:00Z --end-time 2026-08-21T00:00:00Z \
  --query "[?authorization.action!='Microsoft.Resources/deployments/read'].{time:eventTimestamp, action:authorization.action, caller:caller, status:status.value}" \
  -o table
```

**If they push back — "How long do you retain that evidence?"** — Whatever the client's records-retention policy says, which in financial services is commonly seven years for anything touching a regulated process, and I'd confirm rather than assume. Practically that means: pipeline run logs exported to a Log Analytics workspace or immutable blob storage with a retention lock, because Azure DevOps and GitHub both age out run history far sooner than seven years; the Git repository itself preserved and backed up; ACR configured so released image tags cannot be deleted, with a lifecycle policy that exempts them; and the Activity Log exported to storage, since its native retention is 90 days. That last one catches people out — the Activity Log is not a long-term audit store by default.

---

### Q96. How does a pipeline integrate with change management / a CAB?
`[MEDIUM]` `[FS-specific]`

**Answer:** The goal is to make the change record a *gate the pipeline reads*, not a document someone writes afterwards. Azure DevOps has a native **ServiceNow change management** check on environments: the deployment waits until a linked change request is in an approved state, and the pipeline can create the change request automatically, update it with the deployment result, and close it. GitHub Actions does the same thing with a REST call to ServiceNow in a gate job, or via the ServiceNow DevOps integration.

The pattern that works: the pipeline **creates** a standard change from a pre-approved template, populated with the artefact digest, the commit range, the test results and the rollback plan; the CAB has already approved that *template* (a "standard change" in ITIL terms), so routine deployments need no meeting; and only changes that fall outside the template — a schema change, a new external dependency — get escalated to a normal change with a CAB review.

That distinction is the consulting value: **get the routine deployment classified as a standard change**, and you've removed the weekly CAB from the critical path without removing the control.

```yaml
# ADO: a REST-API check on the environment that verifies the change is approved
# (configured as an Invoke REST API check on the environment, shown here as its call)
- task: PowerShell@2
  displayName: Verify ServiceNow change is approved
  inputs:
    targetType: inline
    script: |
      $ErrorActionPreference = 'Stop'
      $number = "$(changeRequestNumber)"
      $uri = "https://eyclient.service-now.com/api/now/table/change_request?sysparm_query=number=$number"
      $resp = Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $env:SNOW_TOKEN" }
      $state = $resp.result[0].state
      if ($state -ne '-1' -and $state -ne 'scheduled') {
        throw "Change $number is in state '$state'; deployment blocked."
      }
      Write-Host "Change $number approved and scheduled."
  env:
    SNOW_TOKEN: $(servicenow-token)
```

**If they push back — "The client's CAB meets weekly. That kills your deployment frequency."** — Which is exactly the argument for standard changes, and I'd make it with evidence rather than opinion. I'd bring three months of data: change volume, change failure rate, and mean time to restore for pipeline-deployed changes versus manually-deployed ones. The case writes itself when automated deployments have a lower failure rate and a faster restore — because at that point the weekly CAB is *increasing* risk by batching changes together, which is the opposite of what it's for. That's a conversation with the change manager, not with the engineers, and it's where the consulting part of this job actually lives.

---

### Q97. What does environment segregation mean beyond "different resource groups"?
`[MEDIUM]`

**Answer:** Segregation is about what an attacker or a mistake in one environment can reach in another, and resource groups are a naming convention, not a boundary. Real segregation is: **separate subscriptions** for prod and non-prod, so an RBAC mistake or a runaway script is contained by a subscription boundary; **separate Entra ID app registrations and managed identities** with no shared credentials; **separate networks** with no route between non-prod and prod VNets, enforced by NSGs and route tables rather than by convention; **separate Key Vaults**, so a non-prod compromise yields no prod secrets; **separate clusters** or, at minimum, separate node pools with taints and NetworkPolicy; and **no production data in non-prod** — masked, synthetic, or tokenised.

That last one is the control most often violated and most often tested. A UAT environment full of real customer payment records is a data-protection incident waiting to happen and it's usually justified as "we need realistic test data". The answer is a data-masking pipeline, not a copy.

**If they push back — "What about the pipeline itself? It touches both."** — It must not, with the same identity. Separate service connections per environment, each federated to a different identity, each authorised only to the pipelines that need it, and — the control that closes the loop — the prod service connection is bound to a **branch control check** so only `refs/heads/main` can use it. The pipeline definition can span environments; the credentials never do. And the self-hosted agent pools are separate too, because a compromised non-prod agent must not be able to reach the prod VNet.

---

### Q98. How do you handle data residency in a deployment pipeline?
`[MEDIUM]` `[FS-specific — EY clients are multi-jurisdiction]`

**Answer:** Three layers, and the pipeline is only the first. **Preventive in code:** an OPA/Checkov rule that fails the plan if any resource's location is outside the permitted region set for that workload's classification. **Preventive at the platform:** an Azure Policy assignment at the management-group level with `allowedLocations`, so the resource cannot be created regardless of how it's deployed. **Detective:** a scheduled Resource Graph query that reports any resource outside the permitted regions, because policy exemptions get granted and then forgotten.

The subtleties that catch people: some Azure services have a **global** control plane or store metadata outside your chosen region; Microsoft-hosted **macOS agents always run in the US** regardless of your organisation's location, which Microsoft explicitly warns about for data sovereignty; and geo-replication and paired-region failover can move data to a region you didn't nominate. All three need to be checked per service, not assumed.

```rego
package terraform.residency

import rego.v1

permitted := {
    "restricted":   {"uksouth", "ukwest"},
    "confidential": {"uksouth", "ukwest", "northeurope"},
    "internal":     {"uksouth", "ukwest", "northeurope", "westeurope"},
}

deny contains msg if {
    rc := input.resource_changes[_]
    loc := rc.change.after.location
    class := rc.change.after.tags.data_classification
    allowed := permitted[class]
    not allowed[loc]
    msg := sprintf(
        "%s: location %q is not permitted for data_classification %q (allowed: %v)",
        [rc.address, loc, class, allowed],
    )
}
```

**If they push back — "What about the CI runner itself — does the build touch regulated data?"** — Usually not, but I'd verify rather than assert, because test fixtures are the leak. If any test uses production-derived data, the runner is in scope and must run in-region — which means self-hosted agents in the correct region, not Microsoft-hosted ones whose exact region within the geography isn't guaranteed. The cleaner fix is to make the fixtures synthetic so the question doesn't arise, and I'd push for that first because it also fixes the non-prod data problem from §Q97.

---

### Q99. Give me the auditor's five questions and your answers.
`[HARD]` `[the summary drill — rehearse this]`

**Answer:**

**1. "Show me that this binary in production came from reviewed source."** The image digest, the cosign signature verifying it was built by a named workflow on a protected branch, the provenance attestation naming the commit, the PR with its reviewers, and the admission policy that refuses anything unsigned. The chain in §Q95.

**2. "Show me who approved this change and that they weren't the author."** The environment approval record, with the requester excluded from the approver group by configuration, plus the PR approval record with CODEOWNERS. Two independent records, both timestamped.

**3. "Show me that your security controls actually ran on this change."** The pipeline run for that commit, with the scanning stages and their results; the required-template check on the production service connection proving the mandated stages could not have been skipped; and the exception register for anything suppressed, with its owner and expiry.

**4. "Show me nobody can change production outside this process."** No standing write access — PIM-eligible with approval and time limits, evidenced by activation records; GitOps means no human has cluster write; Azure Policy denies non-compliant resources regardless of origin; and the Activity Log filtered by principal shows only pipeline identities making changes in the window.

**5. "Show me you can restore it."** The rollback procedure, the last time it was exercised (not "we could" — a date), the retained artefacts proving the previous version is still deployable, and the runbook. `git revert` plus an Argo CD sync, or `helm rollback`, or applying the previous digest — and the DR test record.

**If they push back — "What if you can't answer one of them?"** — Then I say so, name the gap, and give a remediation date — because the fastest way to lose an audit is to bluff and be caught. In practice the one most teams fail is #5: everyone has a rollback procedure and almost nobody has exercised it in the last quarter. That's a cheap fix — a scheduled game-day where you roll back a real service in UAT and record it — and it converts a finding into evidence.

---

## 17. 30-second whiteboard versions

Three diagrams. Draw them while you talk; do not read them.

### 17.1 The paved road — build once, promote everywhere, secretless

```text
 PR opened
   │  pre-commit already ran ruff/bandit/gitleaks locally
   ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │ CI  (hosted agent — no prod access, no secrets, OIDC only)          │
 │  lint → unit → contract+OpenAPI fuzz → gitleaks → bandit → pip-audit│
 │  build image → trivy (BLOCK on fixable HIGH/CRIT) → push            │
 │  syft SBOM → cosign sign + attest        ══► ARTEFACT = sha256:...  │
 └────────────────────────────────────────────────────────────────────┘
   │                                         (immutable from here on)
   ▼
 ┌──────────┐   ┌──────────┐   ┌──────────────────┐   ┌────────────────┐
 │   dev    │──►│   test   │──►│      uat         │──►│      prod      │
 │  auto    │   │  auto    │   │ approve: BA      │   │ approve: 2 RMs │
 │          │   │          │   │ check: branch    │   │ checks: window │
 │          │   │          │   │                  │   │  + ServiceNow  │
 │          │   │          │   │                  │   │  + req template│
 └──────────┘   └──────────┘   └──────────────────┘   └────────────────┘
        SAME DIGEST at every stage. Config differs; the artefact never does.

 Identity:  no secret anywhere. GH: id-token:write → sub=repo:ORG/REPO:environment:prod
            ADO: WIF service connection → Entra federated credential
 Infra:     terraform plan (saved) → checkov + OPA → approval → apply THAT plan
```

**Say while drawing:** *"Build once at the top. From there the digest is the identity, and every gate is attached to that digest. The pipeline holds no cloud credential at all — it mints a fifteen-minute OIDC token bound to the environment. The approver approves an artefact and a saved plan, not an intention."*

---

### 17.2 GitOps: why pull beats push

```text
      PUSH                                    PULL  (GitOps)
 ┌──────────────┐                     ┌──────────────┐      ┌──────────────┐
 │  CI runner   │                     │  CI runner   │      │  config repo │
 │              │                     │              │      │  (Git)       │
 │ kubeconfig ──┼──write──► API       │ build+sign ──┼─────►│ PR: bump      │
 │ prod creds   │           server    │ NO cluster   │      │ digest        │
 │ VNet path    │                     │ creds at all │      └───────┬──────┘
 └──────────────┘                     └──────────────┘              │
   compromise CI                                                    │ pull (outbound)
   = own prod                          ┌─────────────────────────────▼─────────┐
   drift invisible                     │  AKS cluster                          │
   until next deploy                   │   ArgoCD: reconcile every 3 min       │
                                       │           + webhook for instant       │
                                       │   selfHeal: true  → drift reverted    │
                                       │   prune: false    → no auto-delete    │
                                       │   AppProject: repos/dests/kinds/RBAC  │
                                       │   syncWindow: deny 07:00-11:00 Mon-Fri│
                                       └───────────────────────────────────────┘
   Audit trail  = git log (signed commits, PR approvals)
   Rollback     = git revert  (same mechanism as deploy, already tested)
   Drift        = impossible to sustain; the reconciler reverts it in ≤3 min
```

**Say while drawing:** *"The decisive property is that no cluster credential leaves the cluster. CI can't reach production; it can only propose a commit. Everything else — audit trail, rollback, drift correction — falls out of that one design choice."*

---

### 17.3 Draining a consumer during a rolling update

```text
  rollout starts:  maxSurge: 1, maxUnavailable: 0     (never lose capacity)

  pod-old                                     pod-new
    │                                            │ starts, readiness passes
    │◄── removed from EndpointSlice ─────────────┤ (propagation is NOT instant)
    │                                            │
    ├─ preStop: sleep 5   (only if it serves HTTP — lets endpoints converge)
    │
    ├─ SIGTERM ──► _shutdown.set()
    │              stop FETCHING new messages
    │              finish the batch in hand
    │              complete_message() each one
    │              exit 0
    │
    │  ... terminationGracePeriodSeconds: 120  (default is 30 — TOO SHORT
    │      if a single message can take 90s through SAP) ...
    │
    └─ SIGKILL if still alive  ──► locks lost ──► broker redelivers after
                                    lock duration ──► IDEMPOTENCY saves you

  Non-negotiables:
   1. exec-form command  → the Python process is PID 1 and gets SIGTERM
   2. grace period > worst-case single-message time
   3. idempotent handler, keyed on the business id      ← the only real guarantee
   4. PodDisruptionBudget so node drains respect it too
   5. schema change ships ONE RELEASE AHEAD of the code that needs it
```

**Say while drawing:** *"Graceful shutdown reduces how often you redeliver. Idempotency is what makes redelivery safe. You need both, and if you only get one, take idempotency — a node can vanish with no grace period at all."*

---

## 18. Interviewer traps

**TRAP 1 — "Where do you store your pipeline secrets?"**
*Wrong:* "In pipeline variables, marked secret." That's answering a 2018 question.
*Right:* "Ideally nowhere. Workload identity federation means the pipeline mints a short-lived OIDC token — fifteen minutes on GitHub — and there is no stored credential to rotate or steal. Residual non-identity secrets go in Key Vault, referenced by a linked variable group, never persisted in the pipeline." Then name the deprecation: Azure DevOps' `vstoken.dev.azure.com` issuer retires 1 July 2027; new connections use the Entra issuer.

**TRAP 2 — "Terraform state — where does it live?"**
*Wrong:* "In a storage account with a lock." Correct but incomplete, and it misses the finding.
*Right:* Lead with the risk: **state contains secrets in plaintext**, regardless of `sensitive` markings. So the state account is a production secret store — private endpoint only, `shared_access_key_enabled = false`, Entra ID auth, versioning plus 90-day soft delete, and Storage Blob Data Contributor granted to the deployment identities only. Locking is a native blob lease. Then mention `force-unlock` and when it's safe.

**TRAP 3 — "How do you do canary in Kubernetes?"**
*Wrong:* "Set `maxSurge` and roll out slowly." That's a rolling update, not a canary.
*Right:* "Kubernetes natively gives you Recreate and RollingUpdate only. A real canary needs traffic splitting — a mesh or a weighting-capable ingress — plus a controller that analyses metrics and decides: Flagger or Argo Rollouts. And for a queue consumer there's no traffic to split, so you do a capacity-based canary and analyse dead-letter and abandon rates instead."

**TRAP 4 — "Does GitOps mean you keep your YAML in Git?"**
*Wrong:* "Yes."
*Right:* "That's necessary but not sufficient. The defining property is **continuous reconciliation** by an in-cluster agent that pulls — so no cluster credential lives in CI, and drift is reverted automatically rather than discovered at the next deploy. `kubectl apply` from a pipeline against YAML in Git is push-based CI/CD, not GitOps."

**TRAP 5 — "`count` or `for_each`?"**
*Wrong:* "Either — `count` is simpler."
*Right:* "`for_each` for collections, always, because `count` addresses by index: remove an element and everything after it shifts, so Terraform plans to destroy and recreate all of them. On a queue with messages in it that's an outage. `count` is only for a conditional single resource — `count = var.enabled ? 1 : 0`. And if you already have `count` in production, refactor with `moved` blocks and verify the plan shows zero changes."

**TRAP 6 — "Security scanning — you'd block the build on all HIGH and CRITICAL findings, right?"**
*Wrong:* "Yes, zero tolerance." A gate that fails on 4,000 pre-existing findings gets disabled in week two.
*Right:* "Block on findings that are new, HIGH/CRITICAL, **and fixable**. Baseline the pre-existing set as accepted-with-SLA and burn it down. Two things I block on unconditionally because they're controls not findings: a detected secret, and a missing signature or SBOM. And every exception carries an owner and an expiry that CI enforces."

**TRAP 7 — "Your image scan is clean at build. Are you covered?"**
*Wrong:* "Yes, we scan every build."
*Right:* "No. A dependency that was clean on Tuesday isn't clean forever — Log4Shell landed against images that had already passed. So a nightly re-scan of what's actually deployed, driven off the stored SBOMs, plus Defender for Containers doing continuous registry and runtime scanning. Build-time scanning tells you about the past."

**TRAP 8 — "Bicep or Terraform — which is better?"**
*Wrong:* Picking one and dismissing the other. This is a judgement question, not a preference question.
*Right:* Argue both, then commit. Bicep: no state to protect, day-zero Azure support, Microsoft-supported, and **deployment stacks** now give ownership semantics and deny settings — genuine drift *prevention*, which Terraform can't do on Azure. Terraform: the plan is a saved reviewable artefact, one tool covers Entra ID, GitHub and Kubernetes too, bigger skills market. "I'd default to Terraform, and switch to Bicep without hesitation for an Azure-only client who already has a working Bicep estate — migrating working IaC for tool preference destroys value."

**TRAP 9 — "How long is `terminationGracePeriodSeconds` by default?"**
*Wrong:* Guessing, or not knowing it's a problem.
*Right:* "**30 seconds**, and for a queue consumer that's usually wrong. If a single message can take 90 seconds through SAP, the default guarantees a SIGKILL mid-message, lost locks and redelivery. Set it above worst-case single-message time, use exec form so the process is PID 1 and actually receives SIGTERM, and make the handler idempotent anyway because a node can be lost with no grace period at all."

**TRAP 10 — "Just give the pipeline Contributor on the subscription — it's simpler."**
*Wrong:* Agreeing, or objecting vaguely on "least privilege" grounds.
*Right:* Be specific: "Contributor includes `Microsoft.Authorization/roleAssignments/write`, which is a direct path from Contributor to Owner — the pipeline can grant itself anything. I'd scope to the resource group, use Contributor-minus-role-assignments for the app deploy identity, and split out a separate Terraform identity that gets User Access Administrator on that one resource group because it genuinely does need to create role assignments. Two identities, two blast radii."

**TRAP 11 — "You've added the field to the message schema. Deploy it."**
*Wrong:* Deploying producer and consumer together.
*Right:* "Consumers first, one release ahead. Release N teaches the consumer to tolerate the field — optional with a default. Release N+1 makes the producer emit it. Release N+2 removes the tolerance, and no earlier than the queue's message TTL after N+1, because a message written before N+1 may still be sitting in the queue. Producer and consumer are never atomically upgraded — during any roll, and for the whole time messages sit in a queue, both versions coexist."

**TRAP 12 — "Self-hosted agents are just about cost, right?"**
*Wrong:* "Yes, they're cheaper at scale."
*Right:* "Cost is a side effect. The reason is reachability: Microsoft states you can't use ExpressRoute or VPN with Microsoft-hosted agents, and they can't be targeted by service tags — only by allow-listing a whole regional IP range. At a bank, the state storage account, the AKS API server and Key Vault are all Private Link only, so prod-touching stages *must* be self-hosted. And I'd make them ephemeral scale-set or Managed DevOps Pool agents, never pets, and never run fork PRs on them."

---

## 19. Rapid fire

| # | Q | A |
|---|---|---|
| 1 | `git fetch` vs `git pull`? | fetch updates remote-tracking refs only; pull = fetch + merge/rebase into your branch. CI never pulls — it checks out an exact SHA. |
| 2 | Build once, promote everywhere — why? | The artefact you tested must be the artefact that ships. Promote by digest, never by tag. |
| 3 | Trunk-based or GitFlow for a delivery team? | Trunk-based + short branches + feature flags. Add a release branch at code freeze only if a fixed release train is a hard client constraint. |
| 4 | Microsoft-hosted agent free disk? | 10 GB. Hardware: Standard_DS2_v2, 2 vCPU / 7 GB RAM / 14 GB SSD. |
| 5 | MS-hosted job timeout? | 60 min on the free tier (1,800 min/month); 360 min (6 h) with paid parallel jobs. |
| 6 | GitHub Actions job timeout? | 6 h GitHub-hosted, 5 days self-hosted; a workflow run caps at 35 days. |
| 7 | GH Actions matrix cap? | 256 jobs per workflow run. |
| 8 | GH Actions cache size? | 10 GB per repository, LRU eviction. |
| 9 | Reusable workflow nesting? | 10 levels total — caller plus up to 9 reusable workflows. Loops prohibited. |
| 10 | Permission needed for OIDC in Actions? | `permissions: id-token: write`. Token lifetime ~900 s, single job. |
| 11 | GH OIDC subject for an environment? | `repo:ORG/REPO:environment:ENVIRONMENT-NAME`. Branch: `repo:ORG/REPO:ref:refs/heads/BRANCH`. |
| 12 | Why federate on `environment:` not `ref:`? | The environment's required reviewers gate token issuance. A feature branch literally cannot mint a prod token. |
| 13 | ADO `extends` vs `template`? | `template` includes; `extends` inverts control — the template owns the pipeline and the "required template" check enforces it. |
| 14 | ADO deployment job vs job? | Targets an environment: checks/approvals, deployment history, and strategies (runOnce/rolling/canary) with lifecycle hooks. |
| 15 | ADO WIF issuer deprecation? | `https://vstoken.dev.azure.com` retires 1 July 2027; new connections use `https://login.microsoftonline.com/`. Convert, don't replace. |
| 16 | Trivy flag to fail the build? | `--exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed`. Default severity is all five levels; default format `table`. |
| 17 | Bandit medium-and-above? | `bandit -r app -ll -ii` (`-ll` = severity, `-ii` = confidence). Suppress narrowly with `# nosec Bxxx - reason`. |
| 18 | SCA for Python? | `pip-audit -r requirements.txt --strict`, plus Dependabot/Snyk. Nightly on `main`, not just at build. |
| 19 | IaC scanning tools? | Checkov (rule library), Trivy `config`, tfsec, Terrascan, Bicep linter; OPA/Conftest for client-specific rules against `tfplan.json`. |
| 20 | What's an SBOM for? | Answering "are we exposed to this CVE and where" as a query, not a fire drill. `syft` from the image, `cosign attest` to attach it. |
| 21 | Terraform state contains what? | Resource IDs, attributes, dependencies — **and secrets in plaintext**. Treat the state account as a production secret store. |
| 22 | azurerm backend locking? | Native blob lease. `terraform force-unlock <ID>` only after confirming no apply is running. |
| 23 | `count` vs `for_each`? | `for_each` — keyed by string, so removing one element doesn't shift the rest. `count` only for `? 1 : 0`. |
| 24 | Refactor addresses without destroying? | `moved` blocks. The plan must show zero changes. |
| 25 | How do you check resources in Terraform? | `plan` (will change), `state list`/`state show`/`output` (is managed), `plan -refresh-only` (has drifted). `-detailed-exitcode` returns 2 when changes exist. |
| 26 | Why is `-target` a smell? | It applies a subgraph, leaving state partially converged. Real fix for slow plans is splitting the state, not targeting. |
| 27 | Workspaces or directory-per-env? | Directory-per-env for real environments (separate state, RBAC, pipelines). Workspaces for ephemeral per-PR copies. |
| 28 | `prevent_destroy` vs `ignore_changes`? | `prevent_destroy` makes a destroy plan fail; `ignore_changes` cedes an attribute to another owner — canonically the image tag. |
| 29 | Import an existing resource? | `import` blocks (TF 1.5+), reviewable in a PR, with `plan -generate-config-out`. Done when the plan is clean. |
| 30 | Bicep vs ARM? | Bicep is a DSL that transpiles to ARM JSON — same engine, same limits, ~60% fewer lines, symbolic references, real modules. |
| 31 | Bicep's `existing` keyword? | References a resource this template doesn't own, so you can read its properties or scope a role assignment to it. |
| 32 | Deployment stacks — the two features? | An explicit managed-resource list (`actionOnUnmanage`: deleteAll/deleteResources/detachAll) and deny settings (none/denyDelete/denyWriteAndDelete). Max **5** excluded principals — exclude a group. |
| 33 | Bicep secret in a param file? | Never a literal. `az.getSecret(subId, rg, kv, name)` in `.bicepparam`, or a Key Vault `reference` in parameters.json. |
| 34 | Four GitOps principles? | Declarative; versioned and immutable; pulled automatically; continuously reconciled. |
| 35 | Why is pull safer than push? | No cluster credential leaves the cluster. Compromising CI doesn't compromise prod, and no VNet path to a private API server is needed. |
| 36 | Argo CD components? | API server, repo server (manifest generation), application controller (reconcile), Redis (cache). Reconcile default 3 min. |
| 37 | Argo CD sync-wave default and delay? | Wave 0 (negatives allowed); **2 seconds** between waves, `ARGOCD_SYNC_WAVE_DELAY`. Phases: PreSync → Sync → PostSync, plus SyncFail/PostDelete. |
| 38 | Why `prune: false` in prod? | Asymmetric cost: leftover resources are a nuisance, an accidental delete is an outage. Prune on a manual sync where a human sees the list. |
| 39 | Most common Argo CD OutOfSync cause? | HPA owns `/spec/replicas` and Git also declares it. Fix with `ignoreDifferences`. |
| 40 | ApplicationSet generators? | List, Cluster, Git, Matrix, Merge, SCM Provider, Pull Request, Cluster Decision Resource, Plugin. |
| 41 | Flux's five controller groups? | source (GitRepository/OCIRepository/HelmRepository/Bucket), kustomize (Kustomization), helm (HelmRelease), notification (Provider/Alert/Receiver), image automation (ImageRepository/ImagePolicy/ImageUpdateAutomation). |
| 42 | Argo CD vs Flux, one line? | Argo CD when humans need a UI, projects and sync windows; Flux when the platform wants composable controllers and no server. Both CNCF Graduated. |
| 43 | Helm difference between them? | Argo CD renders (`helm template`) and applies; Flux does a real Helm release, so `helm list`/`rollback` work. |
| 44 | Secrets in GitOps — the four options? | Sealed Secrets, SOPS (ciphertext in Git); External Secrets Operator, Key Vault CSI driver (pointer in Git). Prefer a pointer for FS. |
| 45 | Why not Sealed Secrets in prod? | Ciphertext lives in Git forever; rotation becomes a commit; the sealing key is cluster-specific, so DR means re-sealing everything. |
| 46 | AKS Key Vault CSI rotation defaults? | Add-on `azure-keyvault-secrets-provider`; `enableSecretRotation: false`, `rotationPollInterval: 2m`. A `subPath` mount never gets updates. |
| 47 | What does progressive delivery need underneath? | Traffic splitting (mesh, Gateway API, or a weighting ingress), a metrics source, and enough traffic for the sample to mean something. Blue/green needs none of it. |
| 48 | Flagger canary knobs? | `interval`, `threshold` (failed checks before rollback), `maxWeight`, `stepWeight`, `iterations`, `metrics`, `webhooks`, `progressDeadlineSeconds`. |
| 49 | Argo Rollouts vs Flagger? | Rollouts replaces the Deployment with explicit `steps`; Flagger drives your existing Deployment declaratively. Match the GitOps tool you already run. |
| 50 | Canary a queue consumer? | No traffic to split — run one canary replica among N as a competing consumer and analyse DLQ rate, abandon rate and processing duration. |
| 51 | Leading vs lagging canary signal for a consumer? | DLQ rate lags by up to `maxDeliveryCount × lockDuration`. Pair it with abandon rate or an explicit first-failure counter. |
| 52 | `terminationGracePeriodSeconds` default? | 30 seconds. The preStop hook runs **inside** it, not in addition to it. |
| 53 | Why does exec form matter? | Shell form wraps in `/bin/sh -c`, which doesn't forward signals — the app never sees SIGTERM and is SIGKILLed at the grace period. |
| 54 | `maxSurge`/`maxUnavailable` for a consumer? | `maxSurge: 1, maxUnavailable: 0` — never lose consumer capacity, because lost capacity becomes queue depth becomes a breached SLA. |
| 55 | The message-schema rule? | A schema change ships one release ahead of the code that requires it. Expand, migrate, contract — with a release boundary between each. |
| 56 | Batch over event streaming? | CronJob fans out a control message into N work messages; KEDA-scaled consumers do the work; a reconciliation job verifies the expected count by an SLA time. |
| 57 | Separation of duties in a pipeline? | Author ≠ reviewer ≠ approver; the approved artefact is immutable (digest + saved plan); no standing prod write access; the deploy identity is one no human can assume. |
| 58 | Evidence chain for an auditor? | digest → cosign signature + provenance → commit → PR approvals → pipeline run → sync/deployment history → Activity Log. |
| 59 | Activity Log retention gotcha? | 90 days by default. Export to Log Analytics or immutable storage if the retention requirement is years. |
| 60 | Standard change vs normal change? | Get routine deployments classified as a pre-approved standard change; escalate only schema changes and new dependencies to the CAB. Removes the weekly meeting from the critical path without removing the control. |

---

## Where to go next

- **Messaging semantics behind the drain and the schema rule** → [Messaging & Event Streaming](03-messaging-and-event-streaming.md)
- **Kubernetes objects, probes, HPA/KEDA, Helm fundamentals** → [Microservices, Containers & Kubernetes](04-microservices-containers-kubernetes.md)
- **APIM, Logic Apps, Functions — what you're actually deploying** → [Azure Integration Services](02-azure-integration-services.md)
- **OAuth2/OIDC/mTLS, workload identity in depth** → [Auth & Security](06-auth-and-security.md)
- **The end-to-end designs these pipelines ship** → [System Design](08-system-design-integration.md)
- **Regulatory vocabulary, payment/market-data patterns** → [Financial Services Integration](12-financial-services-integration.md)
- **The 8-hour plan and the grade negotiation** → [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md)
