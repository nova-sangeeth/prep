# Microservices, Docker, Kubernetes & Helm

> EY GDS — API & Integration Developer (Senior / Senior Consultant) — prep pack file 04

**What this file buys you:** EY's own logged DevOps questions are `Explain the Docker expose and publish commands`, `How does HPA work in Kubernetes?`, `What are the objects in a Kubernetes service?` — command-level, not essay-level. The JD pairs "Microservices and Containers (Docker, Kubernetes, Helm)" with AKS + GitOps. This file gives you the sayable answer, the real YAML/CLI, and the failure-mode drills, calibrated so a Python/FastAPI dev can answer every one of them without ever having run a production cluster.

**If you only have 45 minutes:** read §2 (Dockerfile), §9 (probes/QoS), §11 (KEDA), §13 (debugging drills — memorise the command sequences), §16 (traps), §18 (rapid fire).

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [Docker: images, layers, union FS](#1-docker-images-layers-and-the-union-filesystem) | Q1–Q5 |
| 2 | [Docker: the production Dockerfile](#2-docker-the-production-dockerfile) | Q6–Q12 |
| 3 | [Docker: runtime, signals, PID 1](#3-docker-runtime-signals-and-pid-1) | Q13–Q17 |
| 4 | [Registry, scanning, tagging, ACR](#4-registry-scanning-tagging-acr) | Q18–Q22 |
| 5 | [docker-compose for local integration dev](#5-docker-compose-for-local-integration-dev) | Q23–Q24 |
| 6 | [Kubernetes architecture & the reconcile loop](#6-kubernetes-architecture-and-the-reconcile-loop) | Q25–Q29 |
| 7 | [Workload objects](#7-workload-objects-pod--replicaset--deployment--statefulset--daemonset--job) | Q30–Q36 |
| 8 | [Service, Ingress, Gateway API](#8-service-ingress-and-gateway-api) | Q37–Q43 |
| 9 | [Resources, QoS, probes, disruption](#9-resources-qos-probes-and-disruption) | Q44–Q51 |
| 10 | [Config, Secrets, identity, RBAC](#10-config-secrets-identity-and-rbac) | Q52–Q57 |
| 11 | [Autoscaling: HPA, VPA, CA, KEDA](#11-autoscaling-hpa-vpa-cluster-autoscaler-keda) | Q58–Q63 |
| 12 | [Scheduling & networking policy](#12-scheduling-and-network-policy) | Q64–Q69 |
| 13 | [AKS specifics](#13-aks-specifics-cni-workload-identity-agic-container-apps) | Q70–Q76 |
| 14 | [Debugging drills](#14-debugging-drills-the-round-2-favourite) | D1–D6 |
| 15 | [Helm](#15-helm) | Q77–Q88 |
| 16 | [Microservices architecture](#16-microservices-architecture) | Q89–Q101 |
| 17 | [Interviewer traps](#17-interviewer-traps) | 12 |
| 18 | [30-second whiteboard versions](#18-30-second-whiteboard-versions) | 3 |
| 19 | [Rapid fire](#19-rapid-fire-40) | 40 |

---

## 1. Docker: images, layers and the union filesystem

### Q1. What actually is a Docker image?
`[EASY]`

**Answer:** An image is an ordered stack of read-only filesystem layers plus a JSON config blob, addressed by a content digest. Each layer is a tar of the *changes* one build instruction made. At runtime the container runtime unions those layers with an overlay driver and adds one thin writable layer on top — that writable layer is the only thing that dies when the container dies.

The manifest is what a registry actually stores: a JSON document listing the config digest and each layer digest. `docker pull` fetches the manifest first, then only the layer blobs it does not already have locally — that is why the second pull of a similar image is nearly instant.

```bash
docker image inspect ghcr.io/org/orders-api:1.4.2 --format '{{json .RootFS.Layers}}' | python -m json.tool
docker history ghcr.io/org/orders-api:1.4.2 --no-trunc   # layer-by-layer size + the instruction that made it
```

**If they push back — "which storage driver?"** — `overlay2` on modern Linux. It merges `lowerdir` (the read-only layers) and `upperdir` (the container's writable layer) into a `merged` mount. Writing to a file that lives in a lower layer triggers **copy-up**: the whole file is copied into the upper layer first. That is why writing to a 2 GB file inside a container is slow the first time and why databases want a volume, not the container filesystem.

---

### Q2. Why does deleting a file in a later layer not shrink the image?
`[MEDIUM]`

**Answer:** Layers are additive and immutable. A deletion is recorded as a **whiteout file** (`.wh.<name>`) in the newer layer that hides the file from the union view — the bytes are still sitting in the older layer and still ship in the image and still get pulled. Classic failure: `RUN wget bigfile && ... && rm bigfile` as three separate `RUN` lines leaves `bigfile` in the image forever.

```dockerfile
# BAD — 400 MB still in the image
RUN apt-get update
RUN apt-get install -y build-essential
RUN rm -rf /var/lib/apt/lists/*

# GOOD — one layer, the cleanup happens before the layer is sealed
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
```

**If they push back — "how do you find the fat layer?"** — `docker history --no-trunc <image>` gives per-layer size against the instruction that created it, or use `dive` for an interactive view. The real fix in 2026 is a multi-stage build so the fat layer never enters the final stage at all.

---

### Q3. Explain the build cache and how you order a Dockerfile to keep `pip install` cached.
`[MEDIUM]` — *high frequency for a Python candidate*

**Answer:** BuildKit caches per instruction. The cache key for `RUN` is the literal command string plus the parent layer's digest; for `COPY`/`ADD` it is the checksum of the copied file contents plus the parent digest. The moment one instruction misses, every instruction after it is rebuilt. So the rule is: **order instructions from least-frequently-changing to most-frequently-changing**, and copy the dependency manifest separately from the source.

```dockerfile
WORKDIR /app
COPY requirements.txt .          # changes maybe monthly
RUN pip install -r requirements.txt
COPY ./app ./app                 # changes every commit — must be AFTER pip install
```

If you `COPY . .` before `pip install`, every source edit invalidates the dependency layer and you reinstall the whole wheel set on every build. On a RAG service with `torch`/`numpy` pinned that is the difference between a 12-second and a 6-minute build.

**If they push back — "what about a shared pip cache?"** — BuildKit cache mounts. The wheels survive across builds without landing in a layer:

```dockerfile
# syntax=docker/dockerfile:1.7
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

And in CI where each runner is fresh, add registry-backed cache: `docker buildx build --cache-to type=registry,ref=myacr.azurecr.io/orders-api:buildcache,mode=max --cache-from type=registry,ref=myacr.azurecr.io/orders-api:buildcache`.

---

### Q4. `COPY` vs `ADD` — when do you use each?
`[EASY]` — *EY-adjacent; pairs with the logged EXPOSE/publish question*

**Answer:** Use `COPY` for essentially everything. `ADD` does two extra magic things: if the source is a **local tar archive it is auto-extracted** into the destination, and if the source is a **remote URL or a Git repository it is fetched/cloned**. That implicit behaviour is exactly what you do not want in a reproducible build, and a remote `ADD` also silently pins nothing.

```dockerfile
COPY --chown=10001:10001 ./app ./app      # explicit, checksummed, cacheable
COPY --link /opt/venv /opt/venv           # independent layer, not invalidated by earlier changes

# only legitimate ADD use: you actually want tar extraction
ADD rootfs.tar.gz /
# instead of: ADD https://example.com/x.tgz /tmp/   -> use RUN curl + verified checksum
```

**If they push back — "what does `--link` do?"** — it writes the copied content as its own independent layer that is not invalidated when earlier layers change, so rebasing onto a new base image does not force a re-copy. Good for the `COPY --from=builder /opt/venv` line.

---

### Q5. What is `.dockerignore` and why does it matter beyond image size?
`[EASY]`

**Answer:** It excludes paths from the **build context** — the tarball the CLI ships to the daemon/builder before the first instruction runs. Without it you upload `.git`, `.venv`, `__pycache__`, local `.env` files and test fixtures on every build. Three consequences: slow builds, secrets leaking into an image via a careless `COPY . .`, and cache thrash because a changed `.pyc` changes the context checksum.

```gitignore
# .dockerignore
.git
.gitignore
.venv
venv/
__pycache__/
**/*.pyc
.pytest_cache/
.mypy_cache/
.env
.env.*
*.md
tests/
.github/
Dockerfile
docker-compose*.yml
```

**If they push back — "you excluded `tests/` — how do you run tests in CI then?"** — a dedicated `test` stage in the multi-stage build with its own `COPY tests ./tests`, invoked as `docker build --target test .`. The default target still ships without them.

---

## 2. Docker: the production Dockerfile

### Q6. Show me a production Dockerfile for a FastAPI service.
`[MEDIUM]` — *memorise this; it is the single most likely "show me code" moment in this file*

**Answer:** Multi-stage: a builder stage with the compiler toolchain that produces a virtualenv, and a slim runtime stage that copies only the venv and the source, runs as a non-root numeric UID, has a healthcheck, and uses exec-form `ENTRYPOINT` so uvicorn is PID 1 and receives `SIGTERM`.

```dockerfile
# syntax=docker/dockerfile:1.7
# ---------- stage 1: build wheels into a venv ----------
FROM python:3.12-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install -r requirements.txt

# ---------- stage 2: test (built only with --target test) ----------
FROM builder AS test
COPY ./app ./app
COPY ./tests ./tests
RUN /opt/venv/bin/pip install pytest pytest-asyncio httpx \
 && /opt/venv/bin/python -m pytest -q

# ---------- stage 3: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv

WORKDIR /app
COPY --chown=10001:10001 ./app ./app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
```

Four things a senior interviewer is listening for in that file: the **venv copy** (not `pip install --user`, not site-packages surgery), the **numeric UID** in `USER`, `EXPOSE` present but understood as metadata, and **exec-form** ENTRYPOINT/CMD.

**If they push back — "why a venv and not just install into the system Python?"** — copying `/opt/venv` is a single self-contained directory with a stable path, so `COPY --from` is one clean layer and `PATH` is the only runtime wiring. Copying `/usr/local/lib/python3.12/site-packages` also works but you then have to remember `/usr/local/bin` for console scripts, and you inherit whatever the base image put there.

---

### Q7. Multi-stage builds — what problem do they actually solve?
`[EASY]`

**Answer:** They let you keep the build toolchain out of the shipped artifact. Compilers, headers, `git`, npm caches and test dependencies exist only in an earlier stage; the final stage copies just the built artifact. You get a smaller image (faster pulls, faster pod starts) and a much smaller attack surface, which is the part that matters to a Big-4 client security review — no `gcc` in the container means no trivial in-container compile.

Concrete for Python: `psycopg2`, `cryptography`, `lxml`, `orjson` may need `build-essential` to compile if no wheel matches. That toolchain is ~250–400 MB. Multi-stage drops it entirely.

**If they push back — "how much smaller, really?"** — for a typical FastAPI + SQLAlchemy + httpx service: `python:3.12` single-stage ≈ 1.0–1.1 GB; `python:3.12-slim` multi-stage ≈ 180–220 MB. Don't quote a number you haven't measured on your own image — say "roughly 5x on my services, measure with `docker images`."

---

### Q8. `python:3.12`, `-slim`, `alpine`, or distroless — pick one and defend it.
`[HARD]` — *the musl trap*

**Answer:** **`-slim` (Debian bookworm, glibc)** for almost every Python service. Alpine uses **musl** libc, not glibc, so the huge ecosystem of `manylinux` binary wheels on PyPI does not match — pip falls back to building from source, which needs a compiler and can turn a 30-second install into many minutes. Since **PEP 656** there is a `musllinux` wheel tag and popular packages (numpy, pandas, matplotlib) do publish musl wheels, but coverage is still thinner than manylinux, so on Alpine you are one obscure dependency away from a source build.

| Base | libc | Size (approx) | Shell/pkg mgr | Use it when |
|---|---|---|---|---|
| `python:3.12` | glibc | ~1.0 GB | yes | never in prod |
| `python:3.12-slim-bookworm` | glibc | ~130 MB base | yes (`apt`) | **default** |
| `python:3.12-alpine` | musl | ~50 MB base | yes (`apk`) | pure-Python deps only, and you've verified the wheel set |
| `gcr.io/distroless/python3-debian12` | glibc | ~50 MB | **no shell** | hardened prod, once your debugging story is `kubectl debug` |

Second Alpine gotcha beyond wheels: musl's allocator and its **default 128 KB thread stack** behave differently under heavy threading, and DNS resolution differs from glibc (musl historically queries A and AAAA in parallel and does not honour `search` domain fallbacks identically) — which bites in Kubernetes where `ndots:5` is the default.

**If they push back — "distroless has no shell, how do you debug?"** — `kubectl debug -it <pod> --image=busybox:1.36 --target=<container> --share-processes`. That attaches an **ephemeral container** in the same process and network namespace, so you get a shell next to the app without a shell inside the app image. That is the correct 2026 answer and it is what makes distroless viable.

---

### Q9. `EXPOSE` vs `-p / --publish`.
`[EASY]` — **EY logged this verbatim on their DevOps role**

**Answer:** `EXPOSE 8000` is **documentation/metadata only** — it records in the image config which port the process listens on. It opens nothing and maps nothing. `-p 8080:8000` (or `--publish`) is the runtime flag that actually creates the host-to-container port mapping via the daemon's proxy/iptables rules. You can publish a port that was never `EXPOSE`d, and an `EXPOSE`d port is unreachable from the host until you publish it.

```bash
docker run -d --name api -p 8080:8000 orders-api:1.4.2   # host 8080 -> container 8000
docker run -d --name api -P orders-api:1.4.2             # -P publishes ALL EXPOSEd ports to random high host ports
docker port api                                          # show the actual mapping
```

Two useful consequences: `-P` (capital) is the only thing that consumes `EXPOSE`, and containers on the same user-defined bridge network reach each other on the container port directly by DNS name — no publish needed. In Kubernetes, `containerPort` in the pod spec is the same kind of metadata: kube-proxy/CNI routes to the pod IP regardless.

**If they push back — "so is `EXPOSE` useless?"** — no: `-P` uses it, Compose's `depends_on`/healthcheck tooling reads it, and image scanners and reviewers use it as the declared contract. It is documentation with two consumers.

---

### Q10. `CMD` vs `ENTRYPOINT`, and exec form vs shell form.
`[MEDIUM]` — *the PID 1 question is hiding behind this one*

**Answer:** `ENTRYPOINT` is the executable; `CMD` supplies default arguments that a `docker run` argument list overrides. Exec form (`["a","b"]`) runs the binary directly as PID 1. Shell form (`a b`) wraps it in `/bin/sh -c`, so **`sh` becomes PID 1** and does not forward signals — your process never sees `SIGTERM` and gets `SIGKILL`ed at the end of the grace period instead of shutting down cleanly.

The interaction matrix (from the Dockerfile reference — worth knowing cold):

| | No ENTRYPOINT | `ENTRYPOINT exec_entry p1` (shell) | `ENTRYPOINT ["exec_entry","p1"]` (exec) |
|---|---|---|---|
| No CMD | error, not allowed | `/bin/sh -c exec_entry p1` | `exec_entry p1` |
| `CMD ["exec_cmd","p1"]` | `exec_cmd p1` | `/bin/sh -c exec_entry p1` | `exec_entry p1 exec_cmd p1` |
| `CMD exec_cmd p1` (shell) | `/bin/sh -c exec_cmd p1` | `/bin/sh -c exec_entry p1` | `exec_entry p1 /bin/sh -c exec_cmd p1` |

Note row 2: **a shell-form ENTRYPOINT swallows CMD entirely.** Also: setting `ENTRYPOINT` in your Dockerfile resets any `CMD` inherited from the base image to empty.

```dockerfile
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# docker run img app.worker:celery_app   -> overrides CMD, keeps uvicorn
# docker run --entrypoint /bin/sh img -c 'env | sort'  -> override the entrypoint for a one-off
```

**If they push back — "I need env var expansion in the command."** — either use an exec-form wrapper that does its own expansion, or `ENTRYPOINT ["/bin/sh","-c","exec uvicorn app.main:app --port ${PORT:-8000}"]`. The `exec` keyword is the important bit: it replaces the shell process so your app becomes PID 1 anyway.

---

### Q11. What does `HEALTHCHECK` do and how does it relate to Kubernetes probes?
`[MEDIUM]`

**Answer:** `HEALTHCHECK` makes the Docker daemon run a command inside the container on an interval and mark the container `starting` / `healthy` / `unhealthy`. Exit **0 = healthy, 1 = unhealthy, 2 = reserved (do not use)**. Defaults are `--interval=30s`, `--timeout=30s`, `--start-period=0s`, `--retries=3` (`--start-interval=5s` exists on modern engines — *verify against your engine version*). It takes `retries` consecutive failures to flip to `unhealthy`.

The critical point for this JD: **Kubernetes ignores `HEALTHCHECK` entirely.** kubelet only runs the `livenessProbe` / `readinessProbe` / `startupProbe` from the pod spec. So `HEALTHCHECK` is for Compose/local dev/Swarm and for `depends_on: condition: service_healthy`; the K8s answer is probes. Keep both, but never tell an interviewer that `HEALTHCHECK` protects a pod.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python","-c","import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=2).status==200 else 1)"]
```
```bash
docker inspect --format '{{.State.Health.Status}} {{len .State.Health.Log}}' api
```

**If they push back — "why `python -c` instead of curl?"** — a slim/distroless image has no curl and you should not install one just for a healthcheck. The interpreter is already there; use it.

---

### Q12. Why run as non-root, and how do you actually do it?
`[MEDIUM]`

**Answer:** Root in the container is root in the host user namespace unless userns-remap is on, so a container escape or a writable host mount becomes a host compromise. Non-root also blocks the whole class of "attacker installs a package inside the container" moves. Do it with a **numeric UID** in `USER` so Kubernetes' `runAsNonRoot: true` admission check can verify it without resolving `/etc/passwd`.

```dockerfile
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app
COPY --chown=10001:10001 ./app ./app
USER 10001:10001
```
```yaml
# the K8s half — pair them, or the image hardening is decorative
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  seccompProfile: { type: RuntimeDefault }
  capabilities: { drop: ["ALL"] }
```

**If they push back — "`readOnlyRootFilesystem: true` broke my app."** — mount `emptyDir` at the paths that genuinely need writes (`/tmp`, and `/app/.cache` if a library insists), and set `TMPDIR`. For Python specifically, `PYTHONDONTWRITEBYTECODE=1` removes the `.pyc` write attempt that otherwise fails on a read-only rootfs.

**If they push back — "why can't I bind port 80 then?"** — ports below 1024 need `CAP_NET_BIND_SERVICE`. Don't grant it; listen on 8000 and let the Service/Ingress map 80/443 to it.

---

## 3. Docker: runtime, signals and PID 1

### Q13. Why does PID 1 signal handling matter for a rolling deployment?
`[HARD]`

**Answer:** On `kubectl delete`/rollout, kubelet sends `SIGTERM` to PID 1, waits `terminationGracePeriodSeconds` (**default 30**), then `SIGKILL`s. Linux gives PID 1 special treatment: **default signal dispositions are not installed for PID 1**, so a process that does not explicitly install a handler simply ignores `SIGTERM`. If your PID 1 is `/bin/sh -c uvicorn ...`, the shell ignores it and never forwards it, so uvicorn keeps serving until the SIGKILL — every in-flight request is severed and long RAG/LLM calls get truncated.

Exec form fixes the common case because uvicorn/gunicorn do install handlers. Add a graceful shutdown hook so drain is deliberate:

```python
# app/main.py
import asyncio
import contextlib
import logging

import httpx
from fastapi import FastAPI

log = logging.getLogger("orders")

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=10.0)
    yield
    # runs on SIGTERM -> uvicorn stops accepting, then unwinds lifespan
    log.info("draining")
    await asyncio.sleep(0)          # let in-flight tasks finish their current await
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
```
```yaml
terminationGracePeriodSeconds: 45
lifecycle:
  preStop:
    exec:
      command: ["sleep", "5"]   # let endpoint removal propagate to kube-proxy/ingress before we stop accepting
```

**If they push back — "what if my process spawns children and leaves zombies?"** — PID 1 also inherits orphans and must `wait()` on them. Either set `shareProcessNamespace`/use an init: `docker run --init` injects `tini`, and in Kubernetes you either make your app reap properly or add a tiny init as the entrypoint. Celery/gunicorn masters already reap; a `bash` wrapper does not.

---

### Q14. Volumes vs bind mounts vs tmpfs.
`[EASY]`

**Answer:** A **named volume** is Docker-managed storage under `/var/lib/docker/volumes`, portable and the right default for data. A **bind mount** maps an arbitrary host path in — great for live-reloading source in dev, a security and portability liability in prod. **tmpfs** is memory-backed and never touches disk, for secrets and scratch.

```bash
docker volume create pgdata
docker run -d --name pg -v pgdata:/var/lib/postgresql/data postgres:16
docker run -d --name api -v "$PWD/app:/app/app:ro" orders-api:dev        # bind, read-only
docker run -d --name api --tmpfs /tmp:rw,noexec,nosuid,size=64m orders-api:1.4.2
```

**If they push back — "K8s equivalents?"** — volume → `PersistentVolumeClaim`; bind mount → `hostPath` (avoid; it defeats scheduling and is a known escape vector); tmpfs → `emptyDir: { medium: Memory }` (and note that memory-backed emptyDir counts against the container's memory limit, so it can cause an OOMKill).

---

### Q15. Which network drivers exist and which do you use?
`[EASY]`

**Answer:** `bridge` (default, per-host isolated network), `host` (container shares the host network namespace — no isolation, no port mapping, lowest latency), `none` (no networking), plus **user-defined bridge** networks and `overlay` for multi-host Swarm. Always create a user-defined bridge for a multi-container app: it gives you **embedded DNS resolution by container name**, which the default bridge does not.

```bash
docker network create --driver bridge intdev
docker run -d --name pg --network intdev postgres:16
docker run -d --name api --network intdev -e DB_HOST=pg -p 8000:8000 orders-api:1.4.2
# api resolves "pg" via Docker's 127.0.0.11 embedded DNS
```

**If they push back — "how does a container reach the host?"** — `host.docker.internal` on Docker Desktop; on Linux, `--add-host=host.docker.internal:host-gateway`.

---

### Q16. How do you pass secrets into a build without baking them into the image?
`[MEDIUM]`

**Answer:** Never `ARG`/`ENV` a secret — `ARG` values are visible in `docker history` and `ENV` persists into the running container's environment. Use BuildKit **secret mounts**, which expose the file only for that one `RUN` and never create a layer.

```dockerfile
# syntax=docker/dockerfile:1.7
RUN --mount=type=secret,id=piptoken \
    pip install --index-url "https://$(cat /run/secrets/piptoken)@pkgs.dev.azure.com/org/_packaging/feed/pypi/simple/" -r requirements.txt
```
```bash
docker buildx build --secret id=piptoken,env=AZ_ARTIFACTS_PAT -t orders-api:1.4.2 .
```

At **runtime**, secrets come from the platform, not the image: Key Vault via the Secrets Store CSI driver + workload identity (see §10), never a baked `.env`.

**If they push back — "what about SSH keys for a private git dependency?"** — `RUN --mount=type=ssh` plus `docker buildx build --ssh default`.

---

### Q17. What is the difference between `docker stop`, `docker kill` and `docker rm -f`?
`[EASY]`

**Answer:** `docker stop` sends `SIGTERM`, waits (default 10 s, `-t` to change), then `SIGKILL`. `docker kill` sends `SIGKILL` immediately (or `-s` a chosen signal). `docker rm -f` kills and removes the container record. In Kubernetes the analogue is the `terminationGracePeriodSeconds` window — same shape, default 30 s instead of 10 s.

**If they push back — "why does my container take exactly 10 seconds to stop?"** — that is the tell that your PID 1 is ignoring `SIGTERM`. Fix the entrypoint form, don't raise the timeout.

---

## 4. Registry, scanning, tagging, ACR

### Q18. How do you tag images, and why is `:latest` a production incident waiting to happen?
`[MEDIUM]`

**Answer:** Tags are mutable pointers; digests are immutable. `:latest` means "whatever was pushed last", so two pods of the same Deployment can be running different code, a rollback is undefined, and `imagePullPolicy: Always` (which is the implicit default when the tag *is* `latest`) turns every pod start into a registry round-trip. Tag with something traceable and never reuse a tag.

Scheme I'd defend: `<semver>-<gitsha>` for humans, and **deploy by digest** for machines.

```bash
TAG="1.4.2-$(git rev-parse --short=12 HEAD)"
docker buildx build -t myacr.azurecr.io/orders-api:$TAG \
                    -t myacr.azurecr.io/orders-api:1.4 --push .

# resolve to an immutable digest and deploy THAT
DIGEST=$(az acr manifest show-metadata -r myacr -n orders-api:$TAG --query digest -o tsv)
kubectl set image deploy/orders-api api=myacr.azurecr.io/orders-api@$DIGEST
```
```bash
# lock the registry so a tag can never be overwritten
az acr repository update --name myacr --repository orders-api --write-enabled true
az acr repository update --name myacr --image orders-api:1.4.2 --write-enabled false --delete-enabled false
```

**If they push back — "GitOps makes this easier?"** — yes: the digest lands in the Git manifest, so the cluster state is provably the state in the repo, and ArgoCD/Flux image automation writes the new digest as a commit. That is the whole point of GitOps and it is a listed good-to-have on this JD.

---

### Q19. How do you scan an image, and where in the pipeline?
`[MEDIUM]`

**Answer:** Trivy in CI, failing the build on HIGH/CRITICAL with a fixed version available, plus a scheduled re-scan of already-published images because new CVEs land against images you built months ago. Scan the **filesystem** early (fast feedback on dependencies) and the **image** after build.

```bash
# fail the build only on fixable HIGH/CRITICAL
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 \
  --format sarif --output trivy.sarif myacr.azurecr.io/orders-api:1.4.2

# dependency-level scan straight off the repo, no build needed
trivy fs --scanners vuln,secret,misconfig --exit-code 1 .

# generate an SBOM for the client's supply-chain requirement
trivy image --format cyclonedx --output sbom.json myacr.azurecr.io/orders-api:1.4.2
```
```yaml
# GitHub Actions fragment
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myacr.azurecr.io/orders-api:${{ github.sha }}
    severity: HIGH,CRITICAL
    ignore-unfixed: true
    exit-code: '1'
```

**If they push back — "the base image has 40 CVEs and none are fixable."** — that is why `--ignore-unfixed` exists for the gate, plus a `.trivyignore` with an expiry date and a ticket per entry. The durable fix is a smaller base (slim → distroless) and a scheduled base-image bump job, not suppression.

---

### Q20. Azure Container Registry — which SKU and why?
`[MEDIUM]`

**Answer:** **Premium** for anything client-facing, because three things only exist there: **geo-replication**, **private endpoints / Private Link**, and **customer-managed keys**. Basic and Standard are functionally identical to Premium on the data-plane API; they differ on included storage, throughput and enterprise features.

| | Basic | Standard | Premium |
|---|---|---|---|
| Included storage | 10 GiB | 100 GiB | 500 GiB |
| Storage limit | 40 TiB | 40 TiB | 100 TiB |
| Webhooks | 2 | 10 | 500 |
| Geo-replication | — | — | **yes** |
| Private endpoints | — | — | **yes** (200) |
| Content trust / CMK | — | — | **yes** |
| Anonymous pull | — | yes | yes |
| Artifact cache rules | — | yes | yes |
| DataplaneRead per registry | 10,000 r/m | 10,000 r/m | **20,000 r/m** |
| DataplaneWrite per registry | 2,000 r/m | 2,000 r/m | **4,000 r/m** |

Max image layer size is 195 GiB and max manifest size 4 MiB on every tier. Rate limits are enforced with a **token bucket**, so a burst is absorbed but a sustained overrun returns **HTTP 429 with a `Retry-After` header** whose value counts down rather than staying fixed.

**If they push back — "our AKS node pool scaling out to 200 nodes gets throttled pulling."** — that is the classic thundering herd. Fixes in order: geo-replicate so pulls hit a local replica; enable **artifact streaming** (Premium) so pods start before the whole image lands; shrink the image; stagger the rollout with `maxSurge`; and honour `Retry-After` with exponential backoff and jitter.

---

### Q21. What are ACR Tasks and when would you use one?
`[EASY]`

**Answer:** Server-side builds inside ACR — no build agent, and they can trigger on a Git commit, on a **base image update**, or on a schedule. The base-image trigger is the genuinely useful one: when `python:3.12-slim` gets a security patch, ACR rebuilds every dependent image automatically, which is exactly the "we patch CVEs without a human" story a Big-4 client audit asks for.

```bash
az acr task create --registry myacr --name orders-api-build \
  --image orders-api:{{.Run.ShortCommit}} \
  --context https://github.com/org/orders-api.git#main \
  --file Dockerfile \
  --git-access-token "$GH_PAT" \
  --base-image-trigger-type Runtime \
  --commit-trigger-enabled true

az acr task run --registry myacr --name orders-api-build
az acr task logs --registry myacr --name orders-api-build
```

**If they push back — "why not just Azure DevOps / GitHub Actions?"** — you usually should, for the test/scan/deploy chain. ACR Tasks earns its place for the base-image-update rebuild and for multi-arch builds without configuring buildx runners.

---

### Q22. How does geo-replication work and what does it change for you?
`[MEDIUM]`

**Answer:** One registry resource, one login server name, replicas in multiple regions. Azure Traffic Manager routes a pull to the nearest replica, and pushes to the home region replicate out asynchronously. You keep one name (`myacr.azurecr.io`) and one set of RBAC. Storage is billed **per replica** — the shown storage usage is for the home region, multiply by replica count.

```bash
az acr replication create --registry myacr --location southeastasia
az acr replication list --registry myacr -o table
```

**If they push back — "so a pod in a new region can never pull a stale image?"** — it can, briefly: replication is async, so a deploy that fires immediately after a push in another region can hit a replica that does not have the manifest yet and gets a `MANIFEST_UNKNOWN`. Mitigation is to gate the deploy on `az acr manifest show` succeeding in the target region, or accept `imagePullBackOff` + retry.

---

## 5. docker-compose for local integration dev

### Q23. Show a Compose file you'd actually use for local integration development.
`[MEDIUM]`

**Answer:** For an integration service the local stack is: the API, a database, and a local stand-in for the broker. I use `depends_on: condition: service_healthy` so the API does not start before Postgres accepts connections, and a bind mount plus `--reload` for the source.

```yaml
# compose.yaml  (Compose v2 — no top-level "version:" key any more)
name: orders-local

services:
  api:
    build:
      context: .
      target: builder          # dev image keeps the toolchain
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://app:app@db:5432/orders
      SERVICEBUS_EMULATOR: "amqp://guest:guest@broker:5672/"
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel:4317
    volumes:
      - ./app:/app/app:ro
    depends_on:
      db:      { condition: service_healthy }
      broker:  { condition: service_healthy }
    networks: [intdev]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: orders
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d orders"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    volumes: [pgdata:/var/lib/postgresql/data]
    networks: [intdev]

  broker:
    image: rabbitmq:3.13-management-alpine
    ports: ["5672:5672", "15672:15672"]
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks: [intdev]

  otel:
    image: otel/opentelemetry-collector-contrib:0.104.0
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes: ["./otel-config.yaml:/etc/otelcol/config.yaml:ro"]
    networks: [intdev]

volumes:
  pgdata:

networks:
  intdev:
    driver: bridge
```
```bash
docker compose up -d --build
docker compose logs -f api
docker compose exec api python -m pytest -q
docker compose down -v          # -v also drops the named volume
```

**If they push back — "Azure Service Bus has no emulator, so what do you actually test locally?"** — you test your *handler* against a broker-shaped interface. RabbitMQ or the Azure Service Bus emulator container covers the AMQP path; the Azure-specific semantics (sessions, duplicate detection, transfer DLQ) get an integration test against a real dev namespace in CI, not on a laptop. Say that explicitly — it shows you know where the emulator stops being honest. See [Messaging & Event Streaming](03-messaging-and-event-streaming.md).

---

### Q24. Compose vs Kubernetes — when do you stop using Compose?
`[EASY]`

**Answer:** Compose is a local developer-loop tool. You stop the moment you need any of: horizontal scaling driven by a metric, rolling updates with health gating, secret injection from a vault, multi-node scheduling, or a real ingress with TLS. Do **not** try to make Compose a deployment target and do not use `kompose` output as production manifests — it produces a literal translation with no probes, no resources, no PDB, no ServiceAccount.

**If they push back — "our client runs Compose in prod on a VM."** — that happens; the honest framing is that it's fine for a single-node non-HA workload with a documented restart policy, and the migration path is Container Apps before AKS because it removes the cluster-ops burden entirely (see Q76).

---

## 6. Kubernetes architecture and the reconcile loop

### Q25. Walk me through the Kubernetes control plane.
`[MEDIUM]` — *near-certain opener if you claim K8s*

**Answer:** Control plane: **kube-apiserver** is the only component that talks to etcd and is the single front door — everything else is a client of it. **etcd** is the consistent key-value store holding all cluster state. **kube-scheduler** watches for pods with no `nodeName` and binds them to a node. **kube-controller-manager** runs the built-in controllers (Deployment, ReplicaSet, Node, Job, endpoints…). **cloud-controller-manager** owns the cloud-specific bits (load balancers, routes, node lifecycle).

On every node: **kubelet** watches for pods bound to its node and drives the container runtime via CRI to make them real, and reports status back. **kube-proxy** programs iptables/IPVS (or is replaced by eBPF in Cilium) so ClusterIP virtual IPs resolve to pod IPs. **CNI plugin** gives each pod its IP and wires the veth. **CoreDNS** runs as a normal Deployment and serves cluster DNS.

The mental model to say out loud: **everything is a level-triggered reconciliation loop.** A controller watches desired state in the API server, observes actual state, and takes one step to close the gap — then loops. Nothing is imperative and nothing is push-based; that is why `kubectl apply` returns instantly and why "it eventually converged" is normal rather than a bug.

**If they push back — "what happens when you `kubectl apply` a Deployment?"** — kubectl POSTs to the apiserver → authn (cert/OIDC) → authz (RBAC) → admission (mutating webhooks e.g. the workload-identity webhook, then validating webhooks e.g. Gatekeeper/Kyverno) → persisted to etcd. The Deployment controller sees a new Deployment, creates a ReplicaSet. The ReplicaSet controller creates Pods. The scheduler binds each Pod to a node. That node's kubelet pulls the image and starts containers via CRI. The endpoints/EndpointSlice controller adds the pod IP to the Service once the readiness probe passes. kube-proxy programs the rules. **That chain is the single best answer in this whole file — it demonstrates you understand the system, not the commands.**

---

### Q26. What is a Pod and why is it not just "a container"?
`[EASY]`

**Answer:** A Pod is the smallest schedulable unit: one or more containers that share a **network namespace** (same IP, same localhost, same port space) and can share volumes. They are always co-scheduled on one node and share a lifecycle. The multi-container case is the sidecar/ambassador/adapter set — a service mesh proxy, a log shipper, a Key Vault CSI mount, an OTel collector.

Pods are **mortal and never reused**: a "restarted" pod is a new pod with a new IP. That is why you address a Service, not a pod.

**If they push back — "how do sidecars start in the right order?"** — since Kubernetes 1.29 (GA in 1.33) native sidecars are `initContainers` with `restartPolicy: Always`: they start before the app containers, keep running alongside, and are torn down last. That fixes the two ancient bugs — the app container racing a not-yet-ready proxy, and a Job never completing because the sidecar never exits.

```yaml
spec:
  initContainers:
    - name: otel-agent
      image: otel/opentelemetry-collector-contrib:0.104.0
      restartPolicy: Always          # <- makes it a native sidecar
  containers:
    - name: api
      image: myacr.azurecr.io/orders-api:1.4.2
```

---

### Q27. Explain namespaces, ResourceQuota and LimitRange.
`[EASY]`

**Answer:** A **Namespace** is a scope for names and a boundary for RBAC, quota and (with NetworkPolicy) traffic — it is not a security boundary on its own. **ResourceQuota** caps the aggregate the namespace may consume. **LimitRange** sets per-container defaults and min/max, which is what stops a dev shipping a pod with no requests at all.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: team-quota, namespace: integration }
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "100"
    count/deployments.apps: "30"
    persistentvolumeclaims: "10"
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: integration }
spec:
  limits:
    - type: Container
      default:        { cpu: 500m, memory: 512Mi }   # becomes the limit if unset
      defaultRequest: { cpu: 100m, memory: 128Mi }   # becomes the request if unset
      max:            { cpu: "4",  memory: 8Gi }
      min:            { cpu: 10m,  memory: 32Mi }
```

**If they push back — "gotcha with ResourceQuota?"** — the moment a namespace has a quota on `requests.cpu`/`limits.memory`, **every** pod in it must specify those fields or creation is rejected. Pair it with a LimitRange or you break every existing deployment the day you add the quota.

---

### Q28. What is the difference between a controller and an operator?
`[MEDIUM]`

**Answer:** A controller is any reconcile loop watching a resource. An **operator** is a controller for a **CRD** that encodes domain operational knowledge — "how to safely upgrade this stateful system." Strimzi for Kafka is the canonical one an integration dev cares about: it owns the `Kafka`, `KafkaTopic` and `KafkaUser` CRDs and handles broker rolling restarts, rack awareness and partition reassignment so you never do it by hand.

**If they push back — "would you run Kafka on Kubernetes?"** — for a client I'd default to Azure Event Hubs' Kafka-compatible endpoint and skip the operational burden entirely; that is also the answer EY's Azure-first posture wants. Self-hosted Strimzi on AKS is justifiable when the client needs Kafka-native features Event Hubs doesn't expose (Kafka Streams state stores, Connect with specific plugins, compacted topics with custom retention) or has a data-residency constraint.

---

### Q29. What is `kubectl apply` vs `create` vs `replace`, and what is server-side apply?
`[MEDIUM]`

**Answer:** `create` fails if the object exists. `replace` overwrites the whole object and loses fields you didn't send. `apply` does a three-way merge between your manifest, the live object, and the last-applied config, so it is the only declarative one. **Server-side apply** (`kubectl apply --server-side`) moves that merge into the apiserver and tracks **field ownership** per manager, which is what makes multiple controllers (you + HPA + a mutating webhook) able to own different fields of the same object without fighting.

```bash
kubectl apply --server-side --field-manager=argocd -f k8s/
kubectl diff -f k8s/                       # what would change, before you change it
kubectl apply --server-side --force-conflicts -f k8s/   # take ownership from another manager
```

**If they push back — "why does my replica count keep flapping?"** — you have `replicas:` in Git *and* an HPA. Remove `replicas` from the manifest (or set Argo to ignore that field with `ignoreDifferences`), otherwise every sync resets the count the HPA just changed.

---

## 7. Workload objects: Pod / ReplicaSet / Deployment / StatefulSet / DaemonSet / Job

### Q30. Deployment rolling update — explain `maxSurge` and `maxUnavailable`.
`[MEDIUM]`

**Answer:** During a `RollingUpdate` the Deployment controller creates a new ReplicaSet and shifts replicas across. **`maxSurge` (default 25%)** is how many pods above `replicas` may exist at once; **`maxUnavailable` (default 25%)** is how many below `replicas` may be unavailable at once. Both accept a count or a percentage; percentages round surge up and unavailable down. Other defaults worth knowing: `progressDeadlineSeconds` **600**, `revisionHistoryLimit` **10**, `minReadySeconds` **0**.

For a stateless API where capacity matters, I use `maxUnavailable: 0` + `maxSurge: 1` (or 25%) so you never dip below full capacity — at the cost of needing headroom for one extra pod.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: integration
spec:
  replicas: 4
  revisionHistoryLimit: 5
  minReadySeconds: 10
  progressDeadlineSeconds: 300
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: { app: orders-api }
  template:
    metadata:
      labels: { app: orders-api }
    spec:
      terminationGracePeriodSeconds: 45
      containers:
        - name: api
          image: myacr.azurecr.io/orders-api@sha256:0000000000000000000000000000000000000000000000000000000000000000
          ports: [{ containerPort: 8000, name: http }]
```
```bash
kubectl rollout status deploy/orders-api -n integration --timeout=5m
kubectl rollout history deploy/orders-api -n integration
kubectl rollout undo deploy/orders-api -n integration --to-revision=3
kubectl rollout restart deploy/orders-api -n integration   # re-roll without changing the spec
```

**If they push back — "`maxUnavailable: 0` and `maxSurge: 0` together?"** — rejected: the rollout could never make progress. At least one must be non-zero.

**If they push back — "how does a rollback actually work?"** — the old ReplicaSet is retained (that's what `revisionHistoryLimit` bounds) and `rollout undo` just scales it back up. If you set `revisionHistoryLimit: 0` you have no rollback target.

---

### Q31. Deployment vs StatefulSet — and why would an integration developer ever need a StatefulSet?
`[MEDIUM]`

**Answer:** A Deployment's pods are interchangeable: random name suffix, random start order, shared or no storage. A **StatefulSet** gives **stable ordinal identity** (`kafka-0`, `kafka-1`), **stable per-pod DNS** via a headless Service, **stable per-pod PersistentVolumeClaims** created from `volumeClaimTemplates`, and **ordered, one-at-a-time** create/update/delete.

Why an integration dev cares: **Kafka, ZooKeeper/KRaft controllers, and any broker with per-node on-disk state.** A Kafka broker's identity *is* its data — broker 2 must come back as broker 2 with broker 2's log segments, or the partition replicas it leads are lost. That is precisely what a StatefulSet provides and a Deployment cannot.

```yaml
apiVersion: v1
kind: Service
metadata: { name: kafka-headless, namespace: streaming }
spec:
  clusterIP: None                      # headless -> DNS returns pod IPs, not a VIP
  selector: { app: kafka }
  ports: [{ name: broker, port: 9092 }]
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: kafka, namespace: streaming }
spec:
  serviceName: kafka-headless
  replicas: 3
  podManagementPolicy: OrderedReady    # Parallel if you don't need ordering
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                     # canary a StatefulSet by raising this
  selector:
    matchLabels: { app: kafka }
  template:
    metadata:
      labels: { app: kafka }
    spec:
      terminationGracePeriodSeconds: 120
      containers:
        - name: kafka
          image: quay.io/strimzi/kafka:0.43.0-kafka-3.8.0
          ports: [{ containerPort: 9092, name: broker }]
          volumeMounts: [{ name: data, mountPath: /var/lib/kafka/data }]
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: managed-csi-premium
        resources: { requests: { storage: 200Gi } }
```
Each pod resolves as `kafka-0.kafka-headless.streaming.svc.cluster.local`.

**If they push back — "what happens to the PVCs when you delete the StatefulSet?"** — by default they are **retained** deliberately, so scaling down doesn't destroy data. Since 1.27 `persistentVolumeClaimRetentionPolicy` lets you set `whenDeleted`/`whenScaled` to `Delete` if you actually want cleanup.

---

### Q32. DaemonSet — what runs as one?
`[EASY]`

**Answer:** One pod per node (optionally a node subset via `nodeSelector`/affinity), automatically added when a node joins. Node-scoped agents: CNI plugins, `kube-proxy`, log shippers (Fluent Bit), node metrics exporters, the **Secrets Store CSI driver**, and the Azure Key Vault provider. As an app developer you rarely write one; as someone deploying to a client cluster you must recognise them because they consume node capacity that your pods then can't have.

**If they push back — "how do you get a DaemonSet onto a tainted control-plane node?"** — add a matching `toleration`, and usually `priorityClassName: system-node-critical` so it isn't the thing evicted under pressure.

---

### Q33. Job and CronJob — what are the fields that actually matter?
`[MEDIUM]`

**Answer:** For a `Job`: `completions` (how many successful pods constitute done), `parallelism` (how many at once), `backoffLimit` (**default 6** retries before the Job is failed), `activeDeadlineSeconds` (hard wall-clock cap), and `ttlSecondsAfterFinished` (auto-cleanup). For a `CronJob`: `schedule`, `concurrencyPolicy` (`Allow` default / `Forbid` / `Replace`), `startingDeadlineSeconds`, and `successfulJobsHistoryLimit` / `failedJobsHistoryLimit` (defaults **3** and **1**).

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: reconcile-erp-orders, namespace: integration }
spec:
  schedule: "*/15 * * * *"
  timeZone: "Asia/Kolkata"          # 1.27+ — do not rely on the node's TZ
  concurrencyPolicy: Forbid         # never two reconciles at once
  startingDeadlineSeconds: 120
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 3
      activeDeadlineSeconds: 600
      ttlSecondsAfterFinished: 3600
      template:
        spec:
          restartPolicy: Never
          serviceAccountName: orders-sa
          containers:
            - name: reconcile
              image: myacr.azurecr.io/orders-api:1.4.2
              command: ["python", "-m", "app.jobs.reconcile"]
              resources:
                requests: { cpu: 200m, memory: 256Mi }
                limits:   { memory: 512Mi }
```

**If they push back — "what if the controller was down at the scheduled time?"** — CronJob counts missed schedules; if more than 100 are missed it stops scheduling and records an event. `startingDeadlineSeconds` bounds how late a run may start — set it, or a controller outage produces a thundering herd of catch-up jobs.

---

### Q34. `restartPolicy` — what are the values and where do they apply?
`[EASY]`

**Answer:** `Always` (default, and the only value allowed for pods managed by a Deployment/StatefulSet/DaemonSet), `OnFailure`, `Never`. It is a **pod-level** field applied to containers by kubelet. Jobs use `OnFailure` or `Never` — never `Always`, or the Job can never complete.

**If they push back — "what's the backoff?"** — kubelet restarts with exponential backoff starting at **100 ms**, doubling (200 ms, 400 ms, 800 ms…) capped at **5 minutes**, and the counter resets after the container has run successfully for **10 minutes**. When the backoff is in effect the pod shows `CrashLoopBackOff` — which is a *state description, not an error*: the error is whatever made the container exit.

---

### Q35. How does a Deployment know which pods are its own?
`[EASY]`

**Answer:** Label selectors. `spec.selector.matchLabels` must match `spec.template.metadata.labels`. The selector is **immutable after creation** on apps/v1 — changing it requires deleting and recreating the Deployment, which is one of the more annoying real-world gotchas when someone renames an app label.

**If they push back — "what if two Deployments have overlapping selectors?"** — they fight: both ReplicaSets adopt the same pods and continuously scale each other's away. Kubernetes does not prevent it. Always include a unique `app.kubernetes.io/name` + `app.kubernetes.io/instance` pair; Helm's `_helpers.tpl` selector labels exist precisely for this.

---

### Q36. What are the recommended labels?
`[EASY]`

**Answer:** The `app.kubernetes.io/*` set: `name`, `instance`, `version`, `component`, `part-of`, `managed-by`. Selector labels must be a **stable subset** — `name` + `instance` only. Never put `version` in the selector, or every image bump orphans the old ReplicaSet.

```yaml
labels:
  app.kubernetes.io/name: orders-api
  app.kubernetes.io/instance: orders-api-prod
  app.kubernetes.io/version: "1.4.2"
  app.kubernetes.io/component: api
  app.kubernetes.io/part-of: order-platform
  app.kubernetes.io/managed-by: Helm
```

---

## 8. Service, Ingress and Gateway API

### Q37. What are the objects in a Kubernetes service?
`[EASY]` `EY-logged` — *asked verbatim in a real EY GDS round*

**Answer:** Two readings, and I'd give both in twenty seconds. If they mean **the Service types**, there are four `spec.type` values — `ClusterIP` (default, internal VIP), `NodePort` (a port 30000–32767 on every node), `LoadBalancer` (provisions a cloud load balancer, and implicitly creates the NodePort and ClusterIP under it), `ExternalName` (no proxying at all, just a CNAME to an external DNS name) — plus the special case of a **headless** Service, `clusterIP: None`, which has no VIP and returns pod IPs directly. If they mean **which API objects make a Service work**, it's the `Service` itself, the `EndpointSlice` objects the control plane generates from the selector, the ClusterIP allocated out of the service CIDR, the CoreDNS record, and — on top, for L7 — `Ingress` + `IngressClass` or the Gateway API kinds.

| Type | What it gives you | When I actually use it |
|---|---|---|
| `ClusterIP` | Stable virtual IP + DNS name, cluster-internal only | Default for every microservice-to-microservice call. Nearly everything. |
| `NodePort` | Same, plus a static port on every node's IP | Rarely on purpose — it's a building block under `LoadBalancer`, or a stopgap in a bare-metal/lab cluster |
| `LoadBalancer` | Cloud LB with an external IP (on AKS, an Azure Load Balancer, `Standard` SKU) | Exactly **one** per cluster in practice — the ingress controller's Service. Not per app: one public IP per app is how you get a hundred-IP bill and a hundred certificates |
| `ExternalName` | CNAME to `foo.bank.internal` | Aliasing an out-of-cluster dependency (on-prem SOAP endpoint, managed Postgres) so app config says `payments-legacy.integration.svc.cluster.local` and the target can move without a redeploy |
| headless (`clusterIP: None`) | No VIP; DNS returns one A record per ready pod | StatefulSets (per-pod identity), client-side load balancing for gRPC/Kafka, anything that must address individual replicas |

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orders-api
  namespace: integration
  labels:
    app.kubernetes.io/name: orders-api
spec:
  type: ClusterIP
  selector:                       # matches POD labels, not the Deployment
    app.kubernetes.io/name: orders-api
    app.kubernetes.io/instance: orders-api-prod
  ports:
    - name: http                  # name it: Gateway API and monitoring both reference port names
      port: 80                    # the port the VIP listens on
      targetPort: http            # the containerPort NAME on the pod — survives a port change
      protocol: TCP
  sessionAffinity: None
```

**If they push back — "what's `port` vs `targetPort` vs `nodePort`?"** — `port` is on the Service VIP, `targetPort` is on the pod (a number or a named `containerPort`), `nodePort` is on every node's IP. Use a *named* `targetPort` so moving the app from 8000 to 8080 is a Deployment-only change.

---

### Q38. How does a Service actually find its Pods, and what programs the data path?
`[MEDIUM]` — *the follow-up to the EY-logged question; know this chain cold*

**Answer:** By **label selector**, and nothing else — there is no reference from a Service to a Deployment. The EndpointSlice controller watches pods whose labels match `spec.selector`, and writes their IPs into `EndpointSlice` objects. `kube-proxy` on every node watches those EndpointSlices and programs the kernel — iptables/nftables/IPVS rules — so that a packet to the ClusterIP is DNAT'd to one of the backend pod IPs. The Kubernetes docs put it plainly: *"EndpointSlices act as the source of truth for kube-proxy when it comes to how to route internal traffic."*

The chain, in the order you should say it: **pod labels → selector → EndpointSlice → kube-proxy → kernel DNAT rule.**

- EndpointSlices hold **100 endpoints each by default**; that's tunable via the kube-controller-manager flag `--max-endpoints-per-slice` **up to a maximum of 1000**. (The older singular `Endpoints` object is why a 5000-pod Service used to melt the API server — every pod change rewrote one huge object to every node.)
- Each endpoint carries three conditions: **`ready`** (serving and not terminating), **`serving`** (maps to the pod's `Ready` condition, and stays meaningful during termination), **`terminating`** (set once the pod has a deletion timestamp). Proxies normally ignore terminating endpoints but may fall back to `serving && terminating` ones if *all* remaining endpoints are terminating — that's the safety valve that keeps a Service from black-holing during a full rollout.
- kube-proxy modes: **`iptables`** (the long-time default; a chain of rules with probabilistic jumps), **`ipvs`** (kernel hash table, better at large scale — **deprecated as of Kubernetes v1.35**), **`nftables`** (the modern Linux mode, much better rule-update performance at scale), and **`kernelspace`** on Windows.

```bash
# the exact debug sequence when "the service doesn't work"
kubectl -n integration get svc orders-api -o wide
kubectl -n integration get endpointslices -l kubernetes.io/service-name=orders-api -o yaml
kubectl -n integration get pods --show-labels -l app.kubernetes.io/name=orders-api
# from inside the cluster, bypass DNS and hit the VIP directly:
kubectl -n integration run curl --rm -it --restart=Never --image=curlimages/curl:8.10.1 -- \
  curl -sv http://orders-api.integration.svc.cluster.local/healthz
```

**Empty EndpointSlice = one of exactly three things:** (1) the selector doesn't match the pod labels (typo, or you matched the Deployment's labels instead of the pod template's), (2) the pods exist but are **not Ready** — readiness probe failing, so they're excluded, (3) `targetPort` points at a port nothing is listening on. That triage order is what an interviewer is fishing for.

**If they push back — "session affinity?"** — `sessionAffinity: ClientIP` makes kube-proxy pin a source IP to the same backend, with `sessionAffinityConfig.clientIP.timeoutSeconds` defaulting to **10800 (3 hours)**. It's a blunt instrument: it's L3, so everything behind one corporate NAT gateway is "one client", and it defeats even load spreading. For a bank's internal traffic I'd rather make the service stateless and keep session state in Redis; sticky sessions at L7 (cookie affinity on the ingress) are at least per-browser.

---

### Q39. What is the difference between a Service and a Deployment?
`[EASY]` — *the distinction candidates blur; interviewers use it as a sincerity check*

**Answer:** They solve orthogonal problems and neither references the other. A **Deployment** is a lifecycle controller: it owns "N replicas of this pod template exist, and here is how to replace them safely." A **Service** is a network identity: a stable name, a stable virtual IP, and load balancing across whatever pods currently match a label selector. They only meet because both mention the same labels. You can have a Deployment with no Service (a Kafka consumer, a worker — nothing dials in), and a Service with no Deployment (fronting a StatefulSet, or an `ExternalName` alias to an on-prem SOAP endpoint).

The consequences of them being decoupled are the interesting part:

- **Delete the Deployment, the Service survives** with zero endpoints. DNS still resolves; connections to the ClusterIP just fail. That's why "DNS resolves but I get connection refused" almost always means *no ready endpoints*, not a DNS problem.
- **One Service can front two Deployments.** That is the entire mechanism behind a poor-man's canary: `orders-api-stable` and `orders-api-canary` Deployments both carry `app.kubernetes.io/name: orders-api`, the Service selects only on that key, and traffic splits by replica ratio. (Precise percentage splits need Gateway API `HTTPRoute` weights or a service mesh — see Q43.)
- **One pod can be in several Services** — e.g. a `-headless` Service for peer discovery plus a normal ClusterIP Service for clients.
- The Deployment's `spec.selector` is **immutable**; the Service's selector is **mutable**. Flipping a Service's selector from `version: v1` to `version: v2` is an instantaneous, zero-deploy blue/green cutover — a genuinely useful trick, and a good thing to volunteer.

**If they push back — "so what does the Deployment do about networking?"** — nothing. It sets pod labels and container ports. Every networking decision lives in Service, Ingress/Gateway, and NetworkPolicy objects.

---

### Q40. Explain Kubernetes DNS naming, and when you'd use a headless Service.
`[MEDIUM]`

**Answer:** CoreDNS publishes every Service as `<service>.<namespace>.svc.cluster.local`, resolving to the ClusterIP. Inside the same namespace the short name `orders-api` works because of the pod's DNS search path; across namespaces you need at least `orders-api.integration`. A **headless** Service — `clusterIP: None` — skips the VIP entirely: CoreDNS returns one A record per **ready** pod, so the client does its own load balancing. I use it for StatefulSets (each pod gets `pod-0.svc-name.ns.svc.cluster.local`), and for gRPC or Kafka clients that want to hold long-lived connections to every backend rather than being pinned to one by a kernel-level VIP.

```
orders-api.integration.svc.cluster.local     -> 10.0.134.22          (ClusterIP)
kafka-0.kafka-headless.streaming.svc.cluster.local -> 10.244.3.17    (a specific pod)
_http._tcp.orders-api.integration.svc.cluster.local -> SRV: port 80, target orders-api...
```

**The gRPC reason this matters.** A ClusterIP Service load-balances *connections*, not *requests*. gRPC/HTTP-2 multiplexes everything down one TCP connection, so a gRPC client behind a ClusterIP pins itself to one pod forever and your other nine replicas idle. Fix: headless Service plus a client-side round-robin resolver (`dns:///orders-grpc.integration.svc.cluster.local` with `round_robin`), or terminate gRPC at an L7 proxy. This is a strong thing to raise unprompted — it's the classic "we scaled out and throughput didn't change" incident.

**The `ndots:5` tax — a real latency finding for a Python service.** Kubernetes injects `options ndots:5` into `/etc/resolv.conf`. Any hostname with fewer than 5 dots is tried against every entry in the search path *first*. `api.contoso.com` therefore generates four failed lookups (`api.contoso.com.integration.svc.cluster.local`, `.svc.cluster.local`, `.cluster.local`, then the node's domain) before the real one. On an `httpx.AsyncClient` doing 500 rps to an external SaaS that is 2000 wasted DNS queries a second.

```yaml
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"          # or use a fully-qualified name with a trailing dot in code
```
In Python: `httpx.AsyncClient(base_url="https://api.contoso.com./v1")` — the trailing dot makes it absolute and skips the search path entirely.

**If they push back — "what does `ExternalName` actually do?"** — nothing but return a CNAME; there's no proxying, no health checking, no TLS handling. Two gotchas: it can't rewrite the `Host` header (so the target must accept the real hostname's certificate), and a client that pins SNI will present the external name. For an on-prem SOAP endpoint I'd usually rather run a real egress proxy so I get logging, mTLS and retries — see [Auth](06-auth-and-security.md).

---

### Q41. What is the difference between an Ingress resource and an Ingress controller?
`[MEDIUM]` — *extremely commonly confused; get this crisp*

**Answer:** The `Ingress` object is **inert configuration data** — a declarative L7 routing table stored in etcd. The **Ingress controller** is a running workload (a Deployment of nginx, Traefik, Envoy, or AGIC) that watches Ingress objects and programs an actual proxy to match. The Kubernetes docs are blunt about it: *"An Ingress controller is required to satisfy an Ingress. Only creating an Ingress resource has no effect."* So a cluster with no controller installed will happily accept your Ingress YAML, report no error, and route nothing — which is exactly the confusion the question is testing.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orders-api
  namespace: integration
spec:
  ingressClassName: nginx          # WHICH controller picks this up; omit and you rely on a default class
  tls:
    - hosts: ["orders.contoso-bank.com"]
      secretName: orders-tls       # Secret of type kubernetes.io/tls, keys tls.crt and tls.key
  rules:
    - host: orders.contoso-bank.com          # host-based routing
      http:
        paths:
          - path: /api/v1/orders             # path-based routing
            pathType: Prefix
            backend:
              service:
                name: orders-api
                port:
                  name: http
          - path: /api/v1/orders/health
            pathType: Exact
            backend:
              service:
                name: orders-api
                port:
                  number: 80
  defaultBackend:                            # anything matching no rule
    service:
      name: notfound-svc
      port: { number: 80 }
```

- **`pathType` has exactly three values.** `Exact` — matches the URL path exactly, case-sensitive. `Prefix` — matches on `/`-split path *elements*, so `/api/v1` matches `/api/v1/orders` but **not** `/api/v1foo`. `ImplementationSpecific` — the controller decides, and for nginx that historically means regex. Always write `Prefix` or `Exact`; `ImplementationSpecific` is how a routing rule stops being portable.
- **TLS termination** happens at the controller. `spec.tls[].secretName` points at a `kubernetes.io/tls` Secret carrying `tls.crt` and `tls.key`; the hostname in `tls.hosts` must match the SNI the client sends. In a bank, the cert normally comes from Key Vault via the Secrets Store CSI driver or cert-manager, not from a human running `kubectl create secret` — see [Auth](06-auth-and-security.md).
- **`IngressClass`** is the object that maps a class name to a controller. Without `ingressClassName` you're depending on whichever IngressClass carries `ingressclass.kubernetes.io/is-default-class: "true"` — a shared-cluster landmine. On a multi-tenant platform, always set it explicitly.

**nginx vs AGIC on AKS** — the real trade-off:

| | ingress-nginx | AGIC (Application Gateway Ingress Controller) |
|---|---|---|
| Where the proxy runs | **In-cluster** pods; consumes node CPU/memory; you own its scaling and its CVEs | **Outside** the cluster — an Azure Application Gateway (`Standard_v2`/`WAF_v2`); AGIC is only a controller pod translating Ingress → ARM |
| Data path | Client → Azure LB → nginx pod → pod IP | Client → App Gateway → **pod IP directly** ("doesn't require NodePort or KubeProxy services") |
| WAF | Bolt on ModSecurity yourself | Native Azure WAF policy — usually the deciding factor for a regulated client |
| Reconcile speed | Sub-second, in-process | An ARM control-plane call; slower, and rate-limited |
| Sharp edge | You must patch it | *"By default, AGIC assumes full ownership of the Application Gateway it's linked to. AGIC overwrites all existing Application Gateway configuration that isn't defined in Kubernetes Ingress resources."* Point an AGIC at a shared, hand-built App Gateway and it will delete the listeners. |

Say the AGIC ownership warning out loud if AKS comes up — it's an operational scar, not a doc fact, and it lands.

**If they push back — "which would you pick for a bank?"** — Application Gateway (or **Application Gateway for Containers**, which is the newer Kubernetes-native offering with a dedicated data plane, driven by the **ALB Controller**, and Microsoft now recommends it over AGIC for new work). The reasoning is compliance, not preference: WAF, TLS policy and public IP all sit in an Azure resource that Security already governs with Azure Policy, rather than in a pod my team patches. The cost is slower reconcile and a control plane outside the GitOps loop.

---

### Q42. Ingress annotations — why do you call them a design smell?
`[HARD]` — *a platform-engineer differentiator*

**Answer:** Because everything the Ingress spec can't express — rewrites, timeouts, body size, rate limits, mTLS, canary weights, CORS — has to be smuggled in as a controller-specific **string** in `metadata.annotations`. Those strings are untyped, unvalidated, and silently ignored when you typo them; they can't be RBAC'd separately from the rest of the object; they don't compose (two annotations that both want to rewrite the path just fight); and they make the manifest completely non-portable — moving from nginx to AGIC means rewriting every one of them. It's configuration-as-magic-string, which is the opposite of a paved road.

```yaml
metadata:
  annotations:
    # every one of these is nginx-only, and none is validated by the API server
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/proxy-body-size: "25m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/limit-rps: "50"
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
    cert-manager.io/cluster-issuer: letsencrypt-prod
```

Historically this was also a **security** problem, not just an aesthetic one: annotation values get interpolated into a generated nginx config, which is why ingress-nginx has a track record of config-injection CVEs and why modern versions ship `--enable-annotation-validation` and restrict `configuration-snippet` by default. A field an app team can set that becomes a line in a proxy's config file is an escape hatch out of the cluster's security model.

**The platform-engineer answer — what I'd actually build:**

1. **App teams never author raw Ingress.** They fill in a values file for a Helm library chart; the chart emits the annotations. One place to change nginx→AGIC, one place to fix a CVE-driven syntax change. ([CI/CD & GitOps](05-cicd-iac-and-gitops.md) covers the library-chart pattern.)
2. **Admission policy blocks the escape hatch.** A Kyverno/Gatekeeper rule denies `configuration-snippet`, `server-snippet` and `auth-url` annotations outside the platform namespace, and denies an Ingress with no `ingressClassName`.
3. **Migrate the recurring ones to Gateway API**, where timeouts, rewrites and weights are *typed spec fields* that the API server validates — Q43.

**If they push back — "so are annotations always wrong?"** — no. `cert-manager.io/cluster-issuer` is a legitimate cross-controller hint, and one-off annotations are fine for a single team's single app. The smell is when the same six annotations are copy-pasted into thirty repos: that's a missing platform abstraction, and it's a signal I'd act on.

---

### Q43. What is the Gateway API and why does it exist? Explain the role split.
`[HARD]` — *the best platform-engineering signal in this whole section*

**Answer:** Gateway API is the successor to Ingress: a set of CRDs, `gateway.networking.k8s.io`, that turn everything Ingress pushed into annotations into typed, validated spec fields — and, crucially, split the configuration across three objects owned by three different roles, so the platform team and the application team can each own their half without editing the same YAML file. Ingress fails on exactly two axes: annotations don't compose or validate, and there is **no role separation** — one object holds the TLS certificate, the hostname, the WAF binding and the app's routing rules, so either app teams can edit the cert or the platform team becomes a ticket queue for every route change. `GatewayClass`, `Gateway`, `HTTPRoute` and `GRPCRoute` are all **stable at `v1`** — the v1.0 GA release was 31 October 2023, GRPCRoute joined the Standard channel in v1.1 (May 2024).

| Kind | Owned by | Analogy |
|---|---|---|
| `GatewayClass` | **Infrastructure provider** (Azure, the cloud vendor, or the cluster's networking team) | Like a `StorageClass` — "this class of load balancer is available and this controller implements it" |
| `Gateway` | **Cluster operator / platform team** — you | The actual listener: public IP, ports, TLS certs, WAF policy, and **which namespaces may attach routes** |
| `HTTPRoute` / `GRPCRoute` | **Application developer** — the product team, in their own namespace | Just their paths, headers, weights, timeouts, retries |

```yaml
# --- PLATFORM TEAM owns this. Lives in namespace `gateway-infra`. -----------
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: shared-external
  namespace: gateway-infra
spec:
  gatewayClassName: azure-alb-external        # or `nginx`, `istio`, `envoy-gateway`
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "*.contoso-bank.com"
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: wildcard-contoso-bank-tls
      allowedRoutes:                          # THE GUARDRAIL: who may attach
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "external"      # platform labels the namespace; app teams cannot
        kinds:
          - kind: HTTPRoute
---
# --- APPLICATION TEAM owns this. Lives in THEIR namespace. -------------------
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: orders-api
  namespace: integration
spec:
  parentRefs:
    - name: shared-external
      namespace: gateway-infra
      sectionName: https
  hostnames: ["orders.contoso-bank.com"]
  rules:
    - matches:
        - path: { type: PathPrefix, value: /api/v1/orders }
          headers:
            - name: x-tenant-tier
              value: premium
      timeouts:
        request: 30s                          # a TYPED FIELD, not an annotation string
        backendRequest: 10s
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            set:
              - name: X-Forwarded-Prefix
                value: /api/v1/orders
      backendRefs:                            # canary as a first-class weighted split
        - name: orders-api-stable
          port: 80
          weight: 90
        - name: orders-api-canary
          port: 80
          weight: 10
```

Three points worth making unprompted:

- **The `allowedRoutes` selector is the whole platform story.** The platform team owns the public IP, the wildcard certificate and the WAF; an app team attaches a route by having a labelled namespace and never touches the cert. That is a guardrail, not a review gate — it scales to fifty teams without a ticket queue.
- **Cross-namespace references require an explicit `ReferenceGrant`** in the *target* namespace. An HTTPRoute in `team-a` cannot point `backendRefs` at a Service in `team-b` unless `team-b` publishes a grant. Ingress had no equivalent — it was trust-by-default.
- **It's CRDs, not built-in.** You install the bundle (Standard channel for GA kinds, Experimental for the rest) and a controller that implements it — on AKS, the **ALB Controller** for Application Gateway for Containers, which implements Gateway API **v1.5** and also supports `GRPCRoute` and `ReferenceGrant`. Istio, Envoy Gateway, Traefik and ingress-nginx's successor all implement it too, which is the portability payoff.

**If they push back — "would you migrate everything tomorrow?"** — no. I'd stand up the Gateway alongside the existing Ingress controller, move new services onto `HTTPRoute` first, and migrate existing ones only when they next need something Ingress can't express cleanly — a weighted canary, a header match, a per-route timeout. Both APIs can front the same Services simultaneously, so there's no big-bang. What I would do immediately is stop letting new services add snippet annotations.

---

## 9. Resources, QoS, probes and disruption

### Q44. `requests` vs `limits` — what does each one actually do?
`[MEDIUM]` — *asked in almost every K8s round; most answers are vague*

**Answer:** They act at completely different layers. A **request** is a scheduling contract: the kube-scheduler only places the pod on a node whose *unallocated* capacity covers the sum of requests, and it also becomes the CPU weight the kernel uses to share contended CPU. A **limit** is a runtime ceiling the kernel enforces, and the two resources behave differently at the ceiling — **CPU is throttled** (compressible), **memory is OOM-killed** (incompressible). The docs are explicit: *"a `cpu` limit is a hard limit the kernel enforces"*, whereas *"`memory` limits are enforced by the kernel with out of memory (OOM) kills… A container may use more memory than its `memory` limit, but if it does, it may get killed."*

```yaml
resources:
  requests:
    cpu: "250m"        # scheduler reserves this; cgroup cpu.weight is derived from it
    memory: "512Mi"    # scheduler reserves this; NOT enforced at runtime
  limits:
    memory: "512Mi"    # cgroup memory.max -> exceed it and the kernel kills the process
    # cpu limit deliberately omitted here -- see Q46
```

Facts to have ready:

- **The scheduler never looks at limits.** It sums requests against the node's **Allocatable**, which is `capacity − kube-reserved − system-reserved − eviction-threshold`. That's why a 4-vCPU node does not have 4000m of schedulable CPU.
- **Memory requests are not enforced at all.** A container requesting 512Mi with a 2Gi limit will happily sit at 1.9Gi; nothing objects until the *node* runs short, at which point the kubelet evicts the pods most over their requests first.
- **Setting neither is the worst option** — it makes the pod `BestEffort` (Q45), first to be evicted, and invisible to the scheduler's bin-packing so the node gets oversubscribed.
- **Overcommit is measurable:** `kubectl describe node aks-user-12345678-vmss000003` prints "Allocated resources" with requests and limits as a percentage of allocatable. Limits summing over 100% is normal and fine; **requests** over ~90% means the next pod won't schedule.

```bash
# what is actually reserved vs what is actually used
kubectl describe node <node> | sed -n '/Allocated resources/,/Events/p'
kubectl top pods -n integration --sort-by=memory
# every container in a namespace with no limits set:
kubectl -n integration get pods -o json | python -c "
import json,sys
for p in json.load(sys.stdin)['items']:
    for c in p['spec']['containers']:
        if not c.get('resources', {}).get('limits'):
            print(p['metadata']['name'], c['name'])
"
```

**If they push back — "how do you enforce that teams set them?"** — `LimitRange` in the namespace gives a `default` (applied as a limit when none is set) and a `defaultRequest`, plus `min`/`max` bounds, so an unannotated pod can't be BestEffort. `ResourceQuota` caps the namespace total and — usefully — once a quota on `requests.cpu` exists, a pod with **no** request is *rejected*, not defaulted. Then a Kyverno policy in audit mode reports who's relying on the defaults. That's the paved-road version.

---

### Q45. What are the QoS classes and how do they affect eviction?
`[MEDIUM]`

**Answer:** Three classes, assigned by the kubelet from what you set, not by you directly. **Guaranteed**: every container has both a CPU and a memory request *and* limit, and for each resource limit **equals** request. **Burstable**: not Guaranteed, but at least one container has some CPU or memory request or limit. **BestEffort**: no CPU or memory requests or limits anywhere in the pod. Under node memory pressure the kubelet evicts **BestEffort first, then Burstable, then Guaranteed last**, and within a class it ranks by how far a pod exceeds its requests and by pod priority. The class is fixed at creation — an in-place resize that would change the QoS class is rejected by admission.

| Class | Condition | Eviction | `oom_score_adj` |
|---|---|---|---|
| `Guaranteed` | requests == limits, for **both** CPU and memory, on **every** container | Last | Lowest — hardest for the kernel OOM killer to pick |
| `Burstable` | Some request/limit set, but not matching | Second — worst offenders vs. their requests go first | Middle, computed from the memory request |
| `BestEffort` | Nothing set at all | **First** | Highest — the kernel's first victim |

Two things that catch people:

- **PodDisruptionBudgets are ignored during node-pressure eviction.** The docs state it outright. A PDB protects you from `kubectl drain`, not from a node running out of memory. So "we have a PDB" is not an availability answer for OOM.
- **Guaranteed is not a free win.** requests == limits means you pay for peak all the time and lose all burst headroom, and on CPU it means a hard quota (Q46). I reserve Guaranteed for the things whose restart is genuinely expensive — a stateful broker, a long-running batch consumer mid-transaction.

**What I'd actually set for an integration microservice:** Burstable, with **`memory.request == memory.limit`** (so memory is effectively guaranteed and the pod isn't evicted for drifting over its request) and a **CPU request but no CPU limit** on latency-sensitive services. That gets you predictable memory behaviour and burstable CPU.

**If they push back — "check the class of a running pod?"** — `kubectl get pod orders-api-7d4f -o jsonpath='{.status.qosClass}'`, or `kubectl get pods -o custom-columns='NAME:.metadata.name,QOS:.status.qosClass'` across the namespace to find the BestEffort stragglers.

---

### Q46. Why are CPU limits contentious? Explain CPU throttling.
`[HARD]` — *senior-level; very few candidates can explain the CFS mechanism*

**Answer:** Because a CPU limit is not "you may use one core" — it's a **quota per fixed window**. The kernel's CFS bandwidth controller gives the cgroup `limit × period` of CPU time each period, where the period defaults to **100 ms** (the kubelet's `--cpu-cfs-quota-period` default). A container with `limits.cpu: "1"` gets 100 ms of CPU time per 100 ms window *summed across all its threads*. If four threads run concurrently, that budget is gone in 25 ms and every thread is **hard-stopped for the remaining 75 ms** — even though the node is idle. That shows up as p99 latency spikes at 20% average CPU utilisation, which is the single most confusing performance symptom in Kubernetes.

The measurement that proves it, and the one to quote:

```promql
# fraction of CFS periods in which the container was throttled -- anything sustained above ~0 is real
rate(container_cpu_cfs_throttled_periods_total{namespace="integration"}[5m])
  / rate(container_cpu_cfs_periods_total{namespace="integration"}[5m])
```

```bash
# straight from the cgroup, inside the pod (cgroup v2)
kubectl -n integration exec orders-api-7d4f -- cat /sys/fs/cgroup/cpu.max     # e.g. "100000 100000" = 1 CPU
kubectl -n integration exec orders-api-7d4f -- cat /sys/fs/cgroup/cpu.stat    # nr_throttled, throttled_usec
```

**The argument for omitting CPU limits:** CPU is compressible. If the node is contended, the kernel already shares it *proportionally to requests* — that's what `cpu.weight` is for. A limit adds nothing under contention and actively hurts when the node is idle, because it refuses free capacity. **The argument for keeping them:** without limits, capacity planning is non-deterministic, a runaway thread can starve its neighbours' latency (weights only bind under contention, and getting there takes time), and in a shared multi-tenant cluster you cannot bill or reason about a tenant's ceiling. **My position, sayable in one line:** always set CPU requests; set CPU limits by default at the namespace `LimitRange` for general workloads, and grant a documented exemption to latency-sensitive services, monitored via the throttling ratio above. That is a platform decision with a guardrail, not a per-app opinion.

**The Python-specific trap — say this, it's concrete and it's yours.** `os.cpu_count()` and `multiprocessing.cpu_count()` report the **node's** CPU count, not the cgroup quota. The Gunicorn documentation's `workers = 2 * cpu + 1` formula therefore spawns 33 Uvicorn workers on a 16-vCPU node for a pod limited to 1 CPU — 33 processes fighting over 100 ms of quota per 100 ms, each with its own copy of your model/config memory. Compute workers from the limit, injected via the downward API:

```yaml
env:
  - name: CPU_LIMIT_MILLICORES
    valueFrom:
      resourceFieldRef:
        containerName: api
        resource: limits.cpu
        divisor: 1m
```
```python
# app/workers.py
import math
import os

def worker_count() -> int:
    """Workers from the cgroup budget, never from the node's core count."""
    millicores = int(os.getenv("CPU_LIMIT_MILLICORES", "0"))
    if millicores:                      # limit is set -> respect it
        cores = max(1, millicores // 1000)
    else:                               # no limit -> fall back to the request, then to 1
        cores = max(1, math.floor((os.cpu_count() or 1) / 4))
    return min(2 * cores + 1, 8)        # cap: each worker costs memory too
```
For an async FastAPI service the honest answer is usually **1 worker per pod and scale with replicas** — the event loop is single-threaded, so extra workers per pod buy nothing a second replica wouldn't buy more observably.

**If they push back — "can you change the period?"** — yes: `--cpu-cfs-quota-period` (needs the `CustomCPUCFSQuotaPeriod` feature gate for non-default values), and on AKS via custom node configuration (`"cpuCfsQuotaPeriod": "200ms"`, or `"cpuCfsQuota": false` to disable enforcement entirely for a node pool). A shorter period smooths the stalls at the cost of more scheduler overhead. I'd treat it as a last resort after fixing thread counts.

---

### Q47. A container exits with code 137. Walk me through it.
`[MEDIUM]` — *a favourite because it separates memorisers from debuggers*

**Answer:** 137 is `128 + 9` — the process was killed by **SIGKILL**. Two distinct causes produce it, and the first thing I do is work out which. If `kubectl describe pod` shows `Last State: Terminated, Reason: OOMKilled`, the container's cgroup hit `memory.max` and the kernel OOM killer took it. If the reason is `Error` and it happened during a rollout or a drain, it's the *grace period* expiring — the container ignored SIGTERM for `terminationGracePeriodSeconds` and the kubelet escalated to SIGKILL. Related: **143 is `128 + 15`**, a clean SIGTERM exit, which is what a well-behaved container shows on a normal rollout.

```bash
kubectl -n integration describe pod orders-api-7d4f | sed -n '/Last State/,/Ready/p'
kubectl -n integration get pod orders-api-7d4f \
  -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}{"\t"}{.status.containerStatuses[0].lastState.terminated.exitCode}{"\n"}'
kubectl -n integration get events --field-selector involvedObject.name=orders-api-7d4f --sort-by=.lastTimestamp
kubectl -n integration logs orders-api-7d4f --previous     # the PREVIOUS container's logs -- the ones that matter
```

**The distinction that gets missed:** an OOMKill on the *container's own limit* kills only that container and the kubelet restarts it in place — `RESTARTS` climbs, the pod stays `Running`. An OOM caused by **node** memory pressure produces a kubelet **eviction**: the pod goes `Failed` with reason `Evicted` and is rescheduled elsewhere. Same underlying resource, different object-level symptom, different fix (limit too low vs. node too small / requests too optimistic).

**Python-flavoured causes, in the order I'd check them:**
1. **Real growth** — an unbounded in-memory cache, an accumulating list, a `pandas`/`pyarrow` load of a whole file. Confirm with `tracemalloc` or `memray` in a staging run before touching the limit.
2. **A spike the limit doesn't cover** — deserialising a 200 MB batch payload triples RSS transiently. Memory limits are enforced *reactively*, so the pod survives most days and dies on the big-file day.
3. **Too many workers.** Every Gunicorn/Uvicorn worker is a full process. `workers × per-worker RSS` must fit under the limit — see Q46.
4. **CPython does not always return freed memory to the OS.** RSS plateaus at the high-water mark, so a limit tuned to steady state and a limit tuned to peak are different numbers. Set the limit from the observed peak with headroom, not the average.
5. **The wrong denominator** — a library reading `/proc/meminfo` (the node) instead of the cgroup, and sizing a buffer pool off 64 GB inside a 512Mi container.

**If they push back — "how do you pick the number?"** — from data, not from a round number: `max_over_time(container_memory_working_set_bytes{container="api"}[14d])` plus roughly 25–30% headroom, then re-check after each release. Note it must be **working set**, not RSS — the working set is what the kubelet actually compares against the limit for eviction. And I'd set request == limit for memory so the pod is not evicted for exceeding a lower request.

---

### Q48. Liveness, readiness and startup probes — what's the difference, and what's the classic mistake?
`[HARD]` — *the highest-value question in this file; expect it, and expect the follow-up*

**Answer:** Three questions, three different consequences. **Liveness** asks *"is this process wedged?"* — on failure the kubelet **restarts the container**. **Readiness** asks *"can I serve traffic right now?"* — on failure the pod is **removed from the Service's endpoints** but keeps running. **Startup** asks *"has it finished booting?"* — while it's running, liveness and readiness are suspended entirely. **The classic mistake is putting a downstream dependency check in the liveness probe.** If `/healthz` pings the database or Service Bus, then the moment that dependency has a thirty-second blip, *every replica fails liveness simultaneously*, the kubelet kills them all, they restart into the same still-broken dependency, and you get `CrashLoopBackOff` across the fleet — plus a reconnect storm that often prevents the dependency recovering. You have converted a partial degradation into a total, self-sustaining outage. Restarting a process never fixes someone else's database. **Dependency checks belong in readiness.**

The rule as one line: **liveness checks only in-process state; readiness checks whether *this* pod can usefully serve a request right now.**

```python
# app/health.py  -- FastAPI. Three endpoints, three different jobs.
import asyncio
import time

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db import engine          # your AsyncEngine

router = APIRouter()

_boot_complete = False          # flipped by the startup lifespan handler
_shutting_down = False          # flipped by the SIGTERM handler (see Q51)
_loop_watchdog = time.monotonic()
_dep_cache: tuple[float, bool] = (0.0, False)


async def heartbeat() -> None:
    """Started as a background task in the lifespan handler.
    Proves the event loop is still scheduling work."""
    global _loop_watchdog
    while True:
        _loop_watchdog = time.monotonic()
        await asyncio.sleep(1)


async def _db_ok_cached(ttl_seconds: float) -> bool:
    """One dependency check per ttl, shared by every probe hit."""
    global _dep_cache
    checked_at, ok = _dep_cache
    now = time.monotonic()
    if now - checked_at < ttl_seconds:
        return ok
    try:
        async with engine.connect() as conn:          # SQLAlchemy async engine
            await conn.execute(text("SELECT 1"))
        ok = True
    except Exception:
        ok = False
    _dep_cache = (now, ok)
    return ok


@router.get("/livez", include_in_schema=False)
async def livez() -> Response:
    # IN-PROCESS ONLY. No database. No Service Bus. No outbound HTTP.
    # A blocked event loop is the one thing a restart genuinely fixes.
    if time.monotonic() - _loop_watchdog > 30:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(status_code=status.HTTP_200_OK)


@router.get("/readyz", include_in_schema=False)
async def readyz() -> Response:
    # Dependency checks live HERE, and only for dependencies without which
    # this pod cannot serve ANY request. Cached, so 10 replicas x 1s does not
    # become 10 rps of health traffic against the database.
    if _shutting_down or not _boot_complete:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if not await _db_ok_cached(ttl_seconds=5):
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(status_code=status.HTTP_200_OK)


@router.get("/startupz", include_in_schema=False)
async def startupz() -> Response:
    # Has the slow work finished -- schema migration check, warm cache,
    # config pulled from App Configuration, connection pool primed.
    return Response(
        status_code=status.HTTP_200_OK if _boot_complete
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
```

```yaml
containers:
  - name: api
    image: myacr.azurecr.io/orders-api:1.4.2
    ports:
      - name: http
        containerPort: 8000
    startupProbe:                    # boot budget: 30 x 10s = 300s
      httpGet: { path: /startupz, port: http }
      periodSeconds: 10
      failureThreshold: 30
    livenessProbe:                   # detection: 3 x 10s = 30s once running
      httpGet: { path: /livez, port: http }
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 3
    readinessProbe:
      httpGet: { path: /readyz, port: http }
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2            # drop out of the LB fast
      successThreshold: 1
```

**The readiness version of the same trap, which is the follow-up they'll ask.** Readiness on a *shared* dependency also drains every replica at once — the Service ends up with zero endpoints and you get connection refused instead of a degraded response. So readiness should return 503 only when this pod genuinely cannot serve *anything*. If the service has a read path that works from cache while the write path is down, stay ready and fail the write requests with a proper 503 on that route. "Fail the request, not the pod" is the principle.

**If they push back — "does a worker with no HTTP server need probes?"** — yes, and it needs different ones. A Kafka/Service Bus consumer has no traffic to gate, so readiness is near-meaningless, but liveness matters a lot: the classic wedge is a consumer whose poll loop has stopped while the process is still alive. I liveness-check a heartbeat file the consume loop touches every iteration — `exec: ["python", "-c", "import sys,time,os; sys.exit(0 if time.time()-os.path.getmtime('/tmp/hb') < 90 else 1)"]` — which detects a stalled loop that a TCP or HTTP check would never see. See [Messaging](03-messaging-and-event-streaming.md).

---

### Q49. How do you tune probes, and when do you need a startup probe?
`[MEDIUM]`

**Answer:** Four knobs, and you should know the defaults because they're aggressive. `initialDelaySeconds` **defaults to 0**, `periodSeconds` to **10**, `timeoutSeconds` to **1**, `successThreshold` to **1**, `failureThreshold` to **3**. Worst-case time to detect a wedged container is roughly `initialDelaySeconds + periodSeconds × failureThreshold`. A slow-starting app needs a **startup probe**, not a long liveness `initialDelaySeconds`, because the startup probe lets you decouple the two budgets: a generous boot window *and* a tight detection loop once running. With only a liveness probe you must pick one number that is both, so you either crash-loop a slow booter or take five minutes to notice a hung one.

| Field | Default | What to actually set, and why |
|---|---|---|
| `initialDelaySeconds` | `0` | Leave at 0 **if** you have a startup probe. Without one, set it above worst-case boot or the kubelet kills the container mid-startup — the cause of most mysterious `CrashLoopBackOff` on first deploy |
| `periodSeconds` | `10` | Liveness 10s; readiness 5s (you want to leave the LB quickly, and rejoin quickly) |
| `timeoutSeconds` | **`1`** | **Raise it.** A 1-second timeout against a Python service whose event loop is briefly busy produces phantom liveness failures under load — a restart *caused by* load, right when you least want it. 3–5s |
| `successThreshold` | `1` | **Must be 1** for liveness and startup — the API server rejects anything else. Only readiness may raise it (to damp a flapping backend) |
| `failureThreshold` | `3` | Liveness 3 (be slow to kill). Readiness 2 (be quick to drain). Startup: `failureThreshold × periodSeconds` = your total boot budget |

**Why a startup probe wins.** Set `failureThreshold: 30, periodSeconds: 10` and the container gets 300 seconds to boot — but the moment `/startupz` returns 200, liveness takes over with a 30-second detection window. You also get *early* failure detection: if the app dies at second 12, the startup probe's next check fails and eventually restarts it, whereas `initialDelaySeconds: 300` on liveness means the kubelet ignores a dead process for five minutes. Slow-boot cases that are real for this candidate profile: warming an embedding or vector index, `alembic upgrade head` at startup, pulling config from App Configuration, or JIT-compiling on first request.

**Handlers, and their costs:** `httpGet` (cheapest and most informative — prefer it), `tcpSocket` (only proves something is listening; a deadlocked app still accepts TCP, so it is a *weak* liveness signal), `exec` (**forks a process every single period** — on 200 pods at 5-second intervals that's meaningful node CPU, and it's the probe type most likely to be the thing causing your node pressure), and `grpc` (native, no need to ship `grpc_health_probe` in the image).

**Two things people get wrong:**
- **Probes never go through the Service.** The kubelet on the node dials the **pod IP** directly. So a probe failure is never a Service/DNS problem — and, conversely, a default-deny `NetworkPolicy` that blocks node→pod traffic can break probes on some CNIs.
- **Probe traffic is real traffic.** `/readyz` hitting the database every 5 seconds across 20 replicas is 4 queries a second of pure overhead. Cache the dependency check result with a short TTL, as in Q48.

**If they push back — "how does this interact with a rolling update?"** — directly. The Deployment considers a new pod "available" only after readiness passes plus `minReadySeconds`, and `maxUnavailable`/`maxSurge` gate the next batch on that. A readiness probe that is too optimistic makes a rolling update roll bad pods out at full speed; one that is too slow makes `progressDeadlineSeconds` (default 600) trip and the rollout report failure. Covered in Q30.

---

### Q50. What is a PodDisruptionBudget, and what does it not protect you from?
`[MEDIUM]`

**Answer:** A PDB caps how many pods of a set may be taken down **voluntarily** at once — it's the object that makes `kubectl drain` and AKS node-image upgrades wait instead of stampeding. You set either `minAvailable` or `maxUnavailable`, never both. What it does **not** cover is involuntary disruption: hardware failure, a kernel panic, a network partition, a node running out of resources. The docs list those explicitly as unavoidable, and node-pressure eviction ignores PDBs entirely. So a PDB is a *maintenance* safety net, not an availability guarantee — the availability guarantee comes from replica count, `topologySpreadConstraints` across zones, and PDB together.

| Voluntary (PDB applies) | Involuntary (PDB does nothing) |
|---|---|
| Draining a node for repair or upgrade | Hardware failure of the machine backing the node |
| Draining to scale the cluster down | Kernel panic |
| Evicting a pod to make room for something else | Node disappears due to a network partition |
| Deleting the Deployment, or updating its pod template | Eviction because the node is out of resources |
| Directly deleting a pod (by accident) | Cloud provider/hypervisor losing the VM |

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: orders-api
  namespace: integration
spec:
  maxUnavailable: 1                    # prefer this to minAvailable -- it tracks replica changes
  unhealthyPodEvictionPolicy: AlwaysAllow   # let a drain remove already-broken pods
  selector:
    matchLabels:
      app.kubernetes.io/name: orders-api
      app.kubernetes.io/instance: orders-api-prod
```

- **`maxUnavailable` over `minAvailable`.** `minAvailable: 2` on a Deployment you later scale to 2 blocks every drain forever. `maxUnavailable: 1` keeps meaning the same thing at 3 replicas or 30. The docs recommend it for exactly this reason.
- **`maxUnavailable: 0` (or `minAvailable: 100%`) blocks drains permanently.** This is a genuine production incident pattern: an AKS node-image upgrade hangs for hours with no obvious error because a single-replica app has an absolute PDB. If a workload truly cannot tolerate disruption, run more than one replica; don't express it as a PDB that no maintenance can satisfy.
- **`unhealthyPodEvictionPolicy: AlwaysAllow`** — the docs recommend setting it: *"It is recommended to set `AlwaysAllow` Unhealthy Pod Eviction Policy to your PodDisruptionBudgets to support eviction of misbehaving applications during a node drain."* Under the default `IfHealthyBudget`, pods that are already not-Ready count against the budget, so a crash-looping app can wedge a node drain — a broken pod blocking maintenance is the worst of both worlds.
- **PDBs only gate the Eviction API.** `kubectl delete pod` bypasses them completely; so does the kubelet under node pressure.

```bash
kubectl -n integration get pdb                       # ALLOWED DISRUPTIONS is the column that matters
kubectl drain aks-user-12345678-vmss000003 --ignore-daemonsets --delete-emptydir-data --timeout=600s
```
If `ALLOWED DISRUPTIONS` is `0`, the drain will block — check it *before* you start a node pool upgrade, not during. On a platform team I'd ship the PDB inside the golden Helm chart so every service gets a sane one by default and no app team has to remember. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

**If they push back — "PDB vs `maxUnavailable` on the Deployment?"** — different actors. The Deployment's `maxUnavailable` governs *the Deployment controller's own* rollout. The PDB governs *everyone else* — node drains, the cluster autoscaler consolidating nodes, an operator. You need both, and they should agree: a PDB of `maxUnavailable: 1` alongside a rollout `maxUnavailable: 25%` on 8 replicas means a drain during a rollout can be more disruptive than either alone.

---

### Q51. Explain `terminationGracePeriodSeconds` and the `preStop` hook — how do you drain a message consumer cleanly?
`[HARD]` — *ties containers to messaging; strong finish to this section*

**Answer:** When a pod is deleted, two things happen **in parallel, not in sequence**: the control plane marks the endpoint terminating and removes it from EndpointSlices — which every kube-proxy on every node must then converge on — while the kubelet immediately runs the `preStop` hook and then sends **SIGTERM** to PID 1. The `terminationGracePeriodSeconds` clock (**default 30**) starts at deletion and `preStop` time counts against it; when it expires, SIGKILL. The race is the problem: pods routinely receive SIGTERM *before* the last kube-proxy has removed the DNAT rule, so traffic keeps arriving at a process that has already begun shutting down — which is why rolling updates produce a scatter of 502s. The fix is a `preStop` sleep: keep serving for 5–15 seconds while the data plane converges, *then* let SIGTERM land.

```yaml
spec:
  terminationGracePeriodSeconds: 120     # must exceed preStop + longest in-flight unit of work
  containers:
    - name: consumer
      image: myacr.azurecr.io/orders-consumer:1.4.2
      lifecycle:
        preStop:
          exec:
            # keep serving while every kube-proxy drops this pod from its rules.
            # Needs `sleep` in the image -- on distroless use the container's own
            # binary, e.g. command: ["/app/bin/drain", "--seconds=15"]
            command: ["/bin/sh", "-c", "sleep 15"]
```

**The ordering, said out loud in an interview:**
1. `DELETE` on the pod → `deletionTimestamp` set, pod enters `Terminating`, grace clock starts.
2. **In parallel:** endpoints controller marks the endpoint `terminating` → EndpointSlice updated → each kube-proxy reprograms its node. *Eventually consistent, and no one waits for it.*
3. **In parallel:** kubelet runs `preStop` (blocking), then sends SIGTERM to PID 1.
4. App drains; container exits → pod removed.
5. Grace period expires first → **SIGKILL**, exit code 137 (Q47).

**Draining a message consumer is a different problem from draining an HTTP server** — nothing is going to stop *sending* you messages just because you left a load balancer, because there is no load balancer. The broker keeps handing work to a link that is still open. So the shutdown sequence has to be app-side:

```python
# app/consumer.py -- Azure Service Bus consumer with a correct SIGTERM drain.
import asyncio
import logging
import signal

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusReceiveMode

from app.handlers import handle    # async def handle(msg) -> None, must be idempotent

log = logging.getLogger(__name__)
_shutdown = asyncio.Event()


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    # SIGTERM from the kubelet; SIGINT for local runs.
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown.set)


async def run(namespace: str, queue: str) -> None:
    _install_signal_handlers(asyncio.get_running_loop())
    credential = DefaultAzureCredential()          # workload identity -- see file 06
    async with ServiceBusClient(namespace, credential) as client:
        receiver = client.get_queue_receiver(
            queue_name=queue,
            receive_mode=ServiceBusReceiveMode.PEEK_LOCK,   # never RECEIVE_AND_DELETE for money
            max_wait_time=5,                                # bounded, so shutdown is responsive
            prefetch_count=0,                               # do not prefetch: anything sitting
        )                                                   # in the client buffer at SIGKILL is
                                                            # stalled until its lock expires
        async with receiver:
            while not _shutdown.is_set():
                batch = await receiver.receive_messages(max_message_count=10, max_wait_time=5)
                for msg in batch:
                    try:
                        await handle(msg)
                        await receiver.complete_message(msg)     # settle BEFORE we exit
                    except Exception:
                        log.exception("handler failed, abandoning for redelivery")
                        await receiver.abandon_message(msg)
            log.info("SIGTERM received: loop drained, in-flight settled, closing receiver")
```

Three rules that follow, and they're the reusable part:

- **`terminationGracePeriodSeconds` must exceed `preStop` + the longest single unit of work.** A consumer whose worst-case message takes 90 seconds cannot live with the 30-second default: the kubelet SIGKILLs it mid-transaction, the message's lock eventually expires and it is redelivered — which is fine only if the handler is genuinely idempotent. Set 120s, and make the handler idempotent anyway. See [Messaging](03-messaging-and-event-streaming.md).
- **Set `prefetch_count: 0`** (or drop it low) on anything you intend to drain gracefully. Prefetched messages sitting in a client buffer at SIGKILL are dead time until their locks expire — the deeper the prefetch, the longer the redelivery stall.
- **PID 1 must actually receive the signal.** If the entrypoint is a shell (`CMD python app.py` in shell form), the shell is PID 1, it does not forward SIGTERM, and your handler never runs — the pod always dies by SIGKILL at the grace period and every rollout takes exactly 120 seconds. Use exec-form `CMD ["python", "-m", "app.consumer"]` or `tini`. This is the connection back to Q13.

**If they push back — "how long do rollouts take then?"** — worst case `replicas / maxUnavailable × grace period`, which is why a 120-second grace period on a 30-replica consumer is a 20-minute rollout at `maxUnavailable: 1`. The answer is to raise `maxSurge`/`maxUnavailable` for a consumer (there's no LB to protect — the broker redistributes), or use a rollout strategy that respects it in Argo Rollouts. That trade-off, and how a GitOps controller reports a rollout still in progress, is in [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

---

## 10. Config, Secrets, identity and RBAC

### Q52. How do you get configuration into a container, and what happens when the config changes?
`[MEDIUM]`

> **Answer:** Two shapes — environment variables from a ConfigMap, or the ConfigMap projected as files into a volume. The difference that matters operationally is reload: **environment variables are resolved once at container start and never update**, so a ConfigMap edit does nothing until the pod restarts. Mounted files *do* eventually update in place, but only if the app re-reads them, and never for a `subPath` mount. So I pick deliberately: env vars for things that are genuinely immutable for the life of the pod, files for anything I want to change without a redeploy.

The numbers and the exact rules, from the Kubernetes docs:

| | Env var (`envFrom` / `valueFrom.configMapKeyRef`) | Volume mount | `subPath` mount |
|---|---|---|---|
| Updates on ConfigMap change | **Never** — requires pod restart | Yes, eventually | **Never** |
| Propagation delay | n/a | kubelet sync period + cache propagation delay (tunable via kubelet's `configMapAndSecretChangeDetectionStrategy`) | n/a |
| Suits | ports, log level at boot, feature flags you're willing to roll for | endpoint maps, XSLT, WSDL, cert bundles, routing tables | nothing — avoid it if you want reloads |

Size cap on both ConfigMap and Secret is **1 MiB**. That is a real constraint for integration work: a large WSDL or a big country/BIC mapping table does not belong in a ConfigMap, it belongs in blob storage fetched at startup or baked into the image.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-api-config
  namespace: integration
immutable: true                       # available since v1.19
data:
  LOG_LEVEL: "INFO"
  SERVICE_BUS_NAMESPACE: "eygds-orders-sb"
  routing.yaml: |
    routes:
      - source: SAP_ECC
        target: payments-adapter
        transform: sap_idoc_to_iso20022
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: orders-api, namespace: integration }
spec:
  selector: { matchLabels: { app.kubernetes.io/name: orders-api } }
  template:
    metadata:
      labels: { app.kubernetes.io/name: orders-api }
      annotations:
        # forces a rolling restart whenever the ConfigMap content changes (Helm)
        checksum/config: "{{ include (print $.Template.BasePath \"/configmap.yaml\") . | sha256sum }}"
    spec:
      containers:
        - name: api
          image: myacr.azurecr.io/orders-api:1.4.2
          envFrom:
            - configMapRef: { name: orders-api-config }   # scalar keys become env vars
          volumeMounts:
            - name: routing
              mountPath: /etc/orders/routing        # NOT subPath — subPath never updates
              readOnly: true
      volumes:
        - name: routing
          configMap:
            name: orders-api-config
            items: [{ key: routing.yaml, path: routing.yaml }]
```

**Immutable ConfigMaps** (`immutable: true`) do two things: they block accidental edits, and they let kubelet stop watching the object, which materially cuts API-server load on a large cluster. The trade is that you can no longer edit it — you create `orders-api-config-v2` and roll the Deployment. On the paved road that is a feature, not a cost: config becomes versioned and rollback-able the same way images are.

**The twelve-factor position and where it breaks.** Factor III says config lives in the environment, and it is right about the *principle* — no per-environment config baked into the artefact. It is wrong about the *mechanism* in Kubernetes for three reasons: env vars cannot be rotated without a restart; they cannot carry structured or large values; and they leak — `kubectl describe pod` shows them, they appear in crash dumps, they are inherited by every child process, and anything that can read `/proc/<pid>/environ` in the container can read them. So the platform rule I'd set is: **env vars for non-secret, non-rotating scalars; files for structured config; and never a secret in an env var** — that last one is Q53.

**If they push back — "how do you make the app actually pick up a changed file?"** — three options, in order of preference. (1) Roll the Deployment; that is a `checksum/config` annotation in the chart and it is what most teams should do, because a config change gets the same canary and rollback path as a code change. (2) A SIGHUP handler or a `watchdog`/inotify watcher in the app that re-reads and swaps an in-memory config object under a lock. (3) Reload on every request — fine for a `LOG_LEVEL` read, wrong for anything that costs a parse. For a FastAPI service I'd do (1) for correctness and add (2) only for a genuinely hot-reloadable knob like log level.

---

### Q53. A Kubernetes Secret is encrypted, right?
`[MEDIUM]` — **the trap; expect it, and expect them to nod along if you get it wrong**

> **Answer:** No — and this is the single most common misconception about Kubernetes. A Secret is **base64-encoded, not encrypted**. Base64 is an encoding, it is reversible with one command and no key. By default it sits in plaintext in etcd, and anyone with `get secrets` in the namespace can read it — including, indirectly, **anyone who can create a Pod in that namespace**, because they can just mount it. The real answers are encryption at rest with a KMS provider, tight RBAC, and better still not putting the secret in Kubernetes at all — mount it straight from Key Vault with the Secrets Store CSI driver.

The Kubernetes docs say it plainly: *"Kubernetes Secrets are, by default, stored unencrypted in the API server's underlying data store (etcd). Anyone with API access can retrieve or modify a Secret, and so can anyone with access to etcd. Additionally, anyone who is authorized to create a Pod in a namespace can use that access to read any Secret in that namespace; this includes indirect access such as the ability to create a Deployment."*

```bash
# this is the whole "encryption"
kubectl get secret sb-conn -n integration -o jsonpath='{.data.connectionString}' | base64 -d
```

Four layers, and I'd name all four:

1. **Encryption at rest with a KMS provider.** The API server encrypts Secret resources before writing to etcd, using a data-encryption key wrapped by a key you own in a KMS. On AKS that is the Key Vault KMS integration: `az aks update --enable-azure-keyvault-kms --azure-keyvault-kms-key-id $KEY_ID --azure-keyvault-kms-key-vault-network-access Public`, with a user-assigned managed identity holding **Key Vault Crypto User** on the vault. Note the legacy KMS experience caps at **2,000 secrets per cluster**; KMS v2 is not subject to that limit, and for new clusters on **1.33+** Microsoft points you at the newer KMS data-encryption experience with automatic key rotation. Two gotchas worth saying out loud: it does not work with a system-assigned identity (chicken-and-egg on cluster creation), and after enabling or rotating you must rewrite every existing Secret — `kubectl get secrets --all-namespaces -o json | kubectl replace -f -` — or the old ones stay unencrypted.
2. **RBAC least privilege on `secrets`** — Q56/Q57.
3. **Restrict which containers see it** — mount into one container, not `envFrom` across the pod.
4. **Don't store it in Kubernetes.** Secrets Store CSI driver or External Secrets Operator — Q54.

**If they push back — "so is encryption at rest pointless if RBAC is the real hole?"** — no, they defend different attackers. Encryption at rest defends the **etcd snapshot**: the backup blob, the disk, the support engineer with node access. RBAC defends the **API path**. A financial-services auditor will ask for both, and will also ask who can read the KMS key — which is why the Key Vault key gets its own access review, and why `purge protection` and `soft delete` must be on. Deleting that key makes every secret in the cluster permanently unrecoverable.

**If they push back — "what about Secret rotation?"** — a Kubernetes Secret has no rotation story of its own. Mounted Secret volumes do get updated when the object changes, on the same kubelet-sync path as ConfigMaps, but *the app still has to re-read the file*, and Secrets consumed as env vars never update. That is the argument for the CSI driver, which has an actual rotation loop.

---

### Q54. Then how do you get an Azure Key Vault secret into a pod properly?
`[HARD]` — *the answer that separates a platform engineer from an app developer*

> **Answer:** The Secrets Store CSI driver with the Azure Key Vault provider. The pod declares a `SecretProviderClass` naming the vault and the objects, the driver mounts them as files into the pod at start, authenticates with workload identity, and a rotation loop refreshes the mounted content on an interval — default **2 minutes** on AKS, and off by default until you enable it. The secret never becomes a Kubernetes Secret unless I explicitly ask it to, which means it is never sitting in etcd for a namespace reader to grab.

On AKS this is an add-on, not a Helm chart you maintain:

```bash
az aks enable-addons --addons azure-keyvault-secrets-provider \
  --name myAKSCluster --resource-group myResourceGroup

# turn ON rotation (it is disabled by default) and set the poll interval
az aks update --name myAKSCluster --resource-group myResourceGroup \
  --enable-secret-rotation --rotation-poll-interval 2m

az aks show -g myResourceGroup -n myAKSCluster --query addonProfiles.azureKeyvaultSecretsProvider
# -> { "config": { "enableSecretRotation": "false", "rotationPollInterval": "2m" }, ... }
```

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: payments-kv
  namespace: integration
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: "11111111-2222-3333-4444-555555555555"   # UAMI client id (workload identity)
    keyvaultName: "kv-eygds-payments"
    tenantId: "aaaabbbb-cccc-dddd-eeee-ffff00001111"
    objects: |
      array:
        - |
          objectName: sap-adapter-client-secret
          objectType: secret
        - |
          objectName: iso20022-signing-cert
          objectType: certificate
  # OPTIONAL: also mirror into a real K8s Secret, for things that can only read env vars
  secretObjects:
    - secretName: payments-legacy-env
      type: Opaque
      data:
        - objectName: sap-adapter-client-secret
          key: SAP_CLIENT_SECRET
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: payments-adapter, namespace: integration }
spec:
  selector: { matchLabels: { app.kubernetes.io/name: payments-adapter } }
  template:
    metadata:
      labels:
        app.kubernetes.io/name: payments-adapter
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: payments-adapter-sa
      containers:
        - name: adapter
          image: myacr.azurecr.io/payments-adapter:2.1.0
          volumeMounts:
            - name: kv
              mountPath: /mnt/secrets-store    # files: /mnt/secrets-store/sap-adapter-client-secret
              readOnly: true
      volumes:
        - name: kv
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes:
              secretProviderClass: payments-kv
```

Three facts about `secretObjects` that people get wrong, and that are worth saying because they sound like operational scars:
- **The sync only happens once a pod actually mounts the volume.** You cannot create a `SecretProviderClass` and expect the Kubernetes Secret to appear on its own. The upstream docs say it directly: *"The secrets will only sync once you start a pod mounting the secrets."*
- **When the last pod consuming it is deleted, the synced Kubernetes Secret is deleted too.** That surprises people during a scale-to-zero or a namespace drain.
- The moment you sync to a Kubernetes Secret you are back in etcd, so treat it as a compatibility shim for a legacy component that can only read env vars — not the default.

Also: rotation does **not** reach a `subPath` mount. That is a Kubernetes limitation, not a driver bug, and it is the same rule as Q52.

**External Secrets Operator** is the other credible answer, and the one to reach for in a multi-cloud or multi-vendor estate. It is a controller, not a CSI driver: a `SecretStore`/`ClusterSecretStore` holds the connection to the provider (Key Vault, AWS Secrets Manager, HashiCorp Vault, GCP SM), and an `ExternalSecret` declares what to fetch and materialises it as a native Kubernetes Secret on a `refreshInterval`. `refreshPolicy` is `Periodic` by default, `CreatedOnce` fetches once, `OnChange` re-syncs only when the `ExternalSecret` spec changes; setting `refreshInterval: 0` also means fetch-once.

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata: { name: payments-adapter, namespace: integration }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: azure-kv, kind: ClusterSecretStore }
  target:
    name: payments-adapter-secret
    creationPolicy: Owner
  data:
    - secretKey: SAP_CLIENT_SECRET
      remoteRef: { key: sap-adapter-client-secret }
```

| | Secrets Store CSI driver | External Secrets Operator |
|---|---|---|
| Where the secret lands | file in the pod (K8s Secret optional) | a real Kubernetes Secret, always |
| Blast radius | pod-scoped | namespace-scoped (etcd) |
| Rotation | poll loop refreshes mounted files (2m default on AKS) | `refreshInterval` re-syncs the Secret |
| Works with env vars | only via `secretObjects` | natively |
| Multi-provider | Azure/AWS/GCP/Vault providers | broad, provider-agnostic CRDs |
| My default on AKS | **yes** | when a team genuinely needs a Secret object or multi-cloud |

**If they push back — "the file changed, does my app see it?"** — the *file* changes; your open file handle does not. The driver updates the mounted content, but a Python process that read the secret once at import time keeps the old value forever. Either re-read the file per use (cheap — it's a local tmpfs read), or use a credential object that re-reads on refresh. This is exactly the same class of bug as Q52's reload problem, and it is the thing that makes "rotation is enabled" a false comfort.

---

### Q55. How does a pod get an Azure token with no secret at all?
`[HARD]` — *the single highest-value answer in this section*

> **Answer:** Microsoft Entra Workload ID. There is no secret anywhere. Kubernetes projects a short-lived, audience-scoped OIDC token for the pod's ServiceAccount onto a volume; the AKS cluster publishes an OIDC discovery document; a **federated identity credential** on a user-assigned managed identity says "trust tokens from *this* issuer, with subject `system:serviceaccount:<namespace>:<name>`"; and the Azure SDK swaps that projected token for an Entra access token. The pod's identity is its ServiceAccount, and the trust is a signature check, not a shared secret.

Four objects, and you should be able to name them in order:

1. **Cluster:** OIDC issuer enabled — `az aks update -g rg -n cluster --enable-oidc-issuer --enable-workload-identity`. That publishes `{IssuerURL}/.well-known/openid-configuration` and `{IssuerURL}/openid/v1/jwks`, which is how Entra fetches the public signing keys.
2. **ServiceAccount:** annotated with the managed identity's client ID.
3. **Federated identity credential** on the user-assigned managed identity: issuer = the cluster's OIDC URL, subject = `system:serviceaccount:<ns>:<sa>`, audience = **`api://AzureADTokenExchange`**.
4. **Pod:** labelled `azure.workload.identity/use: "true"`, which is what makes the mutating webhook act. Without the label the webhook does nothing and the pod fails on restart — Microsoft made this a *fail-closed* requirement deliberately.

```bash
export RG=rg-eygds-int CLUSTER=aks-eygds-int NS=integration SA=payments-adapter-sa
export UAMI=id-payments-adapter

az identity create -g $RG -n $UAMI
export CLIENT_ID=$(az identity show -g $RG -n $UAMI --query clientId -o tsv)
export ISSUER=$(az aks show -g $RG -n $CLUSTER --query oidcIssuerProfile.issuerUrl -o tsv)

kubectl create serviceaccount $SA -n $NS
kubectl annotate serviceaccount $SA -n $NS azure.workload.identity/client-id=$CLIENT_ID

az identity federated-credential create \
  --name fic-$NS-$SA \
  --identity-name $UAMI \
  --resource-group $RG \
  --issuer "$ISSUER" \
  --subject "system:serviceaccount:${NS}:${SA}" \
  --audience api://AzureADTokenExchange

# then grant the UAMI a *data-plane* role, not Contributor
az role assignment create --assignee $CLIENT_ID \
  --role "Azure Service Bus Data Sender" \
  --scope "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.ServiceBus/namespaces/eygds-payments-sb/queues/payments-outbound"
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payments-adapter-sa
  namespace: integration
  annotations:
    azure.workload.identity/client-id: "11111111-2222-3333-4444-555555555555"
    # optional; default 3600, supported range 3600-86400
    azure.workload.identity/service-account-token-expiration: "3600"
```

What the mutating webhook injects when it sees the label: a projected `serviceAccountToken` volume and four environment variables — `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_AUTHORITY_HOST`, and `AZURE_FEDERATED_TOKEN_FILE` pointing at the projected token file. `DefaultAzureCredential` reads exactly those, so **the application code contains no Azure-specific wiring at all**:

```python
from azure.identity.aio import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

FQNS = "eygds-payments-sb.servicebus.windows.net"

async def publish(payload: str) -> None:
    # WorkloadIdentityCredential is picked up from AZURE_FEDERATED_TOKEN_FILE et al.
    credential = DefaultAzureCredential()
    async with credential:
        async with ServiceBusClient(FQNS, credential) as client:
            sender = client.get_queue_sender(queue_name="payments-outbound")
            async with sender:
                await sender.send_messages(ServiceBusMessage(payload))
```

Minimum `azure-identity` for Python is **1.13.0** — below that there is no `WorkloadIdentityCredential` and `DefaultAzureCredential` silently falls through to something else. One more scope gotcha worth knowing: with `WorkloadIdentityCredential` you pass v2-format scopes like `https://management.azure.com/.default`, not the bare resource URI that IMDS-based managed identity accepted.

**Azure AD Pod Identity is dead — say it clearly.** The open-source project was **deprecated on 24 October 2022** and **archived in September 2023**; the AKS managed add-on was patched and supported only **through September 2025**, explicitly to give people time to migrate. Its design was the problem, not just its age: NMI ran as a DaemonSet intercepting IMDS calls at the node level, which meant identity was assigned to the underlying VM scale set and a pod that could reach `169.254.169.254` could potentially get an identity it wasn't entitled to. Workload identity replaces node-level interception with a per-pod, per-audience, signed OIDC token. If a client is still on pod identity, that is a migration ticket, and Microsoft ships a migration sidecar that proxies IMDS calls to OIDC as a bridge.

**If they push back — "what are the limits?"** — **20 federated identity credentials per managed identity**, which is the number that bites when one identity is shared across many namespaces or many clusters; propagation of a newly created FIC takes a few seconds; virtual nodes are not supported. Also: the projected Kubernetes token and the Entra access token expire on different clocks — the SA token defaults to 1 hour, Entra tokens last 24 hours — and if you change a ServiceAccount annotation you must restart the pod for it to take effect.

**If they push back — "how do you debug 'AADSTS70021: No matching federated identity record found'?"** — decode the projected token and compare three fields against the FIC: `iss` must equal the cluster's OIDC issuer URL exactly (trailing slash included), `sub` must be `system:serviceaccount:<ns>:<sa>` character-for-character, `aud` must be `api://AzureADTokenExchange`. Ninety percent of the time it is a namespace typo in the subject, or the pod is running under `default` because `serviceAccountName` was omitted.

```bash
kubectl exec -n integration deploy/payments-adapter -- \
  cat /var/run/secrets/azure/tokens/azure-identity-token 2>/dev/null \
  || kubectl exec -n integration deploy/payments-adapter -- printenv AZURE_FEDERATED_TOKEN_FILE
kubectl get sa payments-adapter-sa -n integration -o yaml   # is the client-id annotation there?
az identity federated-credential list --identity-name id-payments-adapter -g rg-eygds-int -o table
```

Cluster-level enablement and the AKS-side networking detail live in [§13 AKS specifics](#13-aks-specifics-cni-workload-identity-agic-container-apps); the OIDC/OAuth2 mechanics of the token exchange itself are in [Auth](06-auth-and-security.md).

---

### Q56. Explain Kubernetes RBAC.
`[MEDIUM]`

> **Answer:** Four object types and one join. **Role** and **ClusterRole** are pure permission sets — a list of rules, each rule being `apiGroups` × `resources` × `verbs`. **RoleBinding** and **ClusterRoleBinding** attach a role to subjects: users, groups, or ServiceAccounts. The only difference between the namespaced and cluster-scoped variants is *scope*: a Role is confined to one namespace, a ClusterRole can also cover cluster-scoped resources like nodes and non-resource URLs like `/healthz`. RBAC is purely additive — there are no deny rules — so the whole discipline is about not granting things in the first place.

The join that people forget: **a RoleBinding may reference a ClusterRole**, and when it does the ClusterRole's permissions are scoped down to that RoleBinding's namespace. That is the pattern for the paved road — define the permission set *once*, cluster-wide, and bind it per namespace.

```yaml
# one reusable definition
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: platform-integration-operator }
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "configmaps", "events"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/exec", "pods/portforward"]
    verbs: ["create"]                       # note: this is a WRITE on a subresource
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments/scale"]
    verbs: ["update", "patch"]
  - apiGroups: ["keda.sh"]
    resources: ["scaledobjects", "scaledjobs"]
    verbs: ["get", "list", "watch"]
---
# bound per namespace, scoped to that namespace only
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: integration-operators, namespace: integration }
subjects:
  - kind: Group
    name: "aad-group-objectid-or-name"      # AKS + Entra: the group OID is the subject
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: platform-integration-operator
  apiGroup: rbac.authorization.k8s.io
```

Things worth knowing cold:

- **`roleRef` is immutable.** You cannot repoint a binding at a different role — the API rejects it and you must delete and recreate. That is deliberate: it means granting someone `update` on a binding lets them manage *subjects* without silently swapping in a more powerful role.
- **Verbs are not just CRUD.** `get`/`list`/`watch`/`create`/`update`/`patch`/`delete`/`deletecollection`, plus verbs on subresources: `pods/log` (get), `pods/exec` (create), `deployments/scale` (update), `serviceaccounts/token` (create). `list` implies you get the full objects, not just names — so `list secrets` is `read all secrets`.
- **Aggregated ClusterRoles.** A ClusterRole with an `aggregationRule` has its `rules` field filled in by the controller from every ClusterRole matching the selector. The built-ins use labels `rbac.authorization.k8s.io/aggregate-to-admin`, `-to-edit`, `-to-view`. This is how you extend `edit` to cover a CRD without editing a built-in object:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: keda-edit-aggregation
  labels:
    rbac.authorization.k8s.io/aggregate-to-edit: "true"
rules:
  - apiGroups: ["keda.sh"]
    resources: ["scaledobjects", "scaledjobs", "triggerauthentications"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

- **The default user-facing ClusterRoles:** `cluster-admin` (everything), `admin` (namespace admin including RBAC within the namespace), `edit` (read/write most objects, but **not** RBAC objects), `view` (read-only, and **`view` deliberately cannot read Secrets**). If someone asks "what's wrong with just giving the team `edit`?", the answer is that `edit` can create pods, and a pod can mount any Secret in the namespace.
- **Escalation prevention:** you cannot create or update a Role granting permissions you do not already hold, unless you have the `escalate` verb on roles. Same rule for bindings via `bind`. This is why a namespace `admin` cannot bootstrap themselves to `cluster-admin`.

**If they push back — "how do you check what a principal can actually do?"** — `kubectl auth can-i`, including the impersonation form, which is the one to know:

```bash
kubectl auth can-i --list -n integration
kubectl auth can-i create pods -n integration \
  --as=system:serviceaccount:integration:payments-adapter-sa
kubectl auth can-i get secrets -n integration --as=system:serviceaccount:integration:cicd-deployer
# who can read secrets here?
kubectl get rolebindings,clusterrolebindings -A -o json \
  | jq -r '.items[] | select(.roleRef.name|test("admin|edit|secret")) | "\(.kind)\t\(.metadata.namespace // "-")\t\(.metadata.name)\t\(.roleRef.name)"'
```

---

### Q57. Design the RBAC for the CI/CD identity that deploys to the cluster.
`[HARD]` — *platform-engineer framing; pairs with [CI/CD & GitOps](05-cicd-iac-and-gitops.md)*

> **Answer:** My first answer is that the CI identity should not have cluster write access at all — with GitOps, CI's only privilege is *push to a Git repository*, and Argo CD reconciles from there. Where a client insists on push-based deploys, the deployer gets a per-namespace ServiceAccount bound to a narrow Role: write on Deployments, Services, ConfigMaps and the rollout subresources, and explicitly **no** `get`/`list` on Secrets, no `create` on RBAC objects, no cluster-scoped verbs. And it is one identity per namespace per environment, federated to the pipeline via OIDC, so there is no kubeconfig or SA token to steal.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: cicd-deployer, namespace: integration }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role                                  # Role, not ClusterRole — one namespace
metadata: { name: cicd-deployer, namespace: integration }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]   # no delete
  - apiGroups: ["apps"]
    resources: ["deployments/status", "deployments/scale"]
    verbs: ["get", "update", "patch"]
  - apiGroups: [""]
    resources: ["services", "configmaps", "serviceaccounts"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events"]
    verbs: ["get", "list", "watch"]         # so the pipeline can print a failing rollout
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["keda.sh"]
    resources: ["scaledobjects", "scaledjobs", "triggerauthentications"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses", "networkpolicies"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  # DELIBERATELY ABSENT: secrets, roles, rolebindings, pods/exec, namespaces, anything cluster-scoped
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: cicd-deployer, namespace: integration }
subjects:
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: integration
roleRef:
  kind: Role
  name: cicd-deployer
  apiGroup: rbac.authorization.k8s.io
```

The reasoning I'd give out loud, because this is where they're testing judgement rather than YAML:

- **No `secrets` verbs.** A deployer that cannot read Secrets cannot exfiltrate credentials if the pipeline is compromised. Secrets come from Key Vault via the CSI driver (Q54), so the deployer never needs them.
- **No `create` on `roles`/`rolebindings`.** Otherwise the deployer can grant itself anything, and privilege-escalation prevention won't save you once the binding exists in a namespace it already admins.
- **No `pods/exec`.** `exec` into a running pod is a shell inside your workload with its identity. It belongs to break-glass, audited, time-boxed — not to a pipeline.
- **No `delete` on workloads.** A pipeline should roll forward; deletion is a human decision with a change record. This one is negotiable and I'd raise it as a policy question rather than a hill.
- **Namespaced, per environment.** The prod deployer identity cannot touch UAT and vice versa. Cheap to do, and it is the control an FS auditor actually asks to see evidence of.
- **Federated, not a stored token.** In Azure DevOps or GitHub Actions, the pipeline authenticates to Entra by OIDC federation, and Entra ID/AKS RBAC maps that to a cluster identity — no long-lived ServiceAccount token in a variable group. Since 1.24 ServiceAccount tokens aren't auto-created as Secrets anyway; a manually minted one is a permanent credential in etcd and should be avoided.

**If they push back — "prove it's least privilege"** — I'd wire it into the pipeline itself, so drift shows up as a failing build rather than an audit finding:

```bash
set -euo pipefail
SA=system:serviceaccount:integration:cicd-deployer
for forbidden in "get secrets" "create rolebindings" "create pods/exec" "delete deployments"; do
  if kubectl auth can-i $forbidden -n integration --as="$SA" --quiet; then
    echo "RBAC REGRESSION: deployer can '$forbidden'" >&2; exit 1
  fi
done
kubectl auth can-i patch deployments -n integration --as="$SA" --quiet   # must succeed
```

**If they push back — "and with Argo CD, where does the privilege go?"** — it moves to the Argo CD application controller's ServiceAccount, which does hold broad rights, but it is a single, auditable, in-cluster identity that only ever applies what is in Git. Human access is then governed by Argo's own AppProject restrictions (allowed destinations, allowed resource kinds) plus Entra SSO. That is the real security argument for GitOps, over and above the reproducibility one — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

---

## 11. Autoscaling: HPA, VPA, Cluster Autoscaler, KEDA

### Q58. How does HPA work in Kubernetes?
`[MEDIUM]` — **`EY-logged`** *(asked verbatim in a real EY GDS interview)*

> **Answer:** The HorizontalPodAutoscaler is a control loop in kube-controller-manager that runs every **15 seconds** by default. Each pass it reads the current metric for the pods of a scale target, compares it to the target you configured, and computes `desiredReplicas = ceil[currentReplicas × (currentMetricValue / desiredMetricValue)]`. If the ratio is within a **10% tolerance** it does nothing; otherwise it writes the new replica count to the target's `scale` subresource, and the Deployment controller does the rest. For CPU and memory the metrics come from **metrics-server** over the `metrics.k8s.io` API; for anything else, from `custom.metrics.k8s.io` or `external.metrics.k8s.io`.

Walk it as a loop, because that is the answer they want:

1. **Fetch.** HPA queries the metrics API for every pod matching the target's selector. metrics-server aggregates kubelet's `/metrics/resource` data at a **15-second resolution**. It is not installed by default upstream — AKS ships it — and it is explicitly *only* for autoscaling, not a monitoring source.
2. **Compute.** The ratio formula above. For `Resource` metrics with `type: Utilization`, "current value" is the mean of (pod usage ÷ pod **request**) across ready pods — which is why **an HPA on CPU utilisation is meaningless if the container has no CPU request**. That is the single most common HPA misconfiguration.
3. **Filter.** Pods being deleted are ignored. Failed pods are discarded. Pods with **missing metrics** are set aside and treated conservatively: assumed to be at 100% of target when scaling *down*, 0% when scaling *up*, so uncertainty never causes an aggressive move. Not-yet-ready pods are assumed to consume 0% when scaling up, which damps the scale-up while new pods are still warming (`--horizontal-pod-autoscaler-initial-readiness-delay`, default **30s**; `--horizontal-pod-autoscaler-cpu-initialization-period`, default **5m**).
4. **Stabilise.** Before acting, the controller applies the stabilisation window and the scaling policies (Q59).
5. **Act.** `PATCH` the `scale` subresource. HPA never creates or deletes pods itself — it only sets `spec.replicas`.

```bash
kubectl get hpa orders-api -n integration
kubectl describe hpa orders-api -n integration    # the Events + Conditions block is the debugging gold
kubectl top pods -n integration                   # proves metrics-server is answering at all
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/integration/pods" | jq '.items[0]'
```

`describe` conditions you should recognise: `AbleToScale=False` (waiting on a stabilisation window), `ScalingActive=False` with `FailedGetResourceMetric` (metrics-server down, or **no resource requests set**), `ScalingLimited=True` (pinned at min or max).

**If they push back — "which API version, and why does it matter?"** — `autoscaling/v2`. `v1` only supports CPU and has no `behavior` field, so no stabilisation tuning, no multiple metrics. If someone shows me an `autoscaling/v1` HPA in 2026 that is a modernisation ticket.

**If they push back — "what if you specify several metrics?"** — HPA computes a desired replica count for *each* metric independently and takes the **maximum**. So adding a metric can only ever make it scale up more eagerly, never less.

---

### Q59. Tune an HPA for an API that gets sharp traffic spikes and explain every field.
`[HARD]`

> **Answer:** The defaults are asymmetric on purpose — scale up fast, scale down slowly — and for a spiky API I make them more so. Default `scaleUp` has a zero-second stabilisation window and lets you either double the replicas or add 4 pods every 15 seconds, whichever is larger. Default `scaleDown` has a **300-second** stabilisation window and allows 100% removal per 15 seconds after it. I keep the aggressive scale-up and I make scale-down much gentler, because a wrong scale-down on a spiky service is a user-visible latency incident and a wrong scale-up is a few rupees of compute.

The documented defaults, which is the thing to have memorised:

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
      - { type: Percent, value: 100, periodSeconds: 15 }
  scaleUp:
    stabilizationWindowSeconds: 0
    policies:
      - { type: Percent, value: 100, periodSeconds: 15 }
      - { type: Pods,    value: 4,   periodSeconds: 15 }
    selectPolicy: Max
```

`stabilizationWindowSeconds` maxes out at **3600**; `periodSeconds` must be greater than 0 and at most **1800**.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders-api, namespace: integration }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders-api
  minReplicas: 3
  maxReplicas: 40
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 65 }
    - type: Pods                                  # per-pod custom metric via Prometheus Adapter
      pods:
        metric: { name: http_requests_in_flight }
        target: { type: AverageValue, averageValue: "25" }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0               # react immediately
      selectPolicy: Max
      policies:
        - { type: Percent, value: 100, periodSeconds: 15 }
        - { type: Pods,    value: 8,   periodSeconds: 15 }
    scaleDown:
      stabilizationWindowSeconds: 600             # 10 min of "it really is quiet now"
      selectPolicy: Min
      policies:
        - { type: Percent, value: 20, periodSeconds: 60 }   # shed at most 20% per minute
        - { type: Pods,    value: 2,  periodSeconds: 60 }
```

How the window actually behaves: for scale-down, the controller looks at all desired-replica recommendations computed over the last `stabilizationWindowSeconds` and picks the **highest** of them. So one quiet 15-second sample cannot shrink the fleet — it has to stay quiet for the whole window. `selectPolicy: Min` on scale-down then takes the *least aggressive* of the listed policies. `selectPolicy: Disabled` on a direction switches that direction off entirely, which is how you get an HPA that only ever grows (useful during a controlled migration).

**Why 65% and not 80%:** utilisation is measured against the request, and a pod at 80% of request under a spike has no headroom for the 30–60 seconds it takes to schedule, pull and warm a replacement. The target should be set so that the fleet can absorb the spike *while* the new pods are coming up. For a Python service with a slow import graph, measure your actual cold-start and work backwards.

**If they push back — "in-flight requests instead of CPU — where does that metric come from?"** — Prometheus Adapter (or Azure Monitor managed Prometheus + KEDA's prometheus scaler) registers `custom.metrics.k8s.io`, translating a PromQL query into a per-pod metric HPA can read. For a FastAPI app that is a `prometheus_client.Gauge` incremented in middleware, scraped by Prometheus. The `Object` and `External` metric types cover the same idea for a non-pod source — but for a queue-driven consumer, KEDA is the better tool (Q62).

**If they push back — "how do you stop it flapping between two values?"** — the 10% tolerance plus the stabilisation window handle most of it. If it still oscillates, the usual cause is that the pod's own metric changes as a *result* of scaling in a nonlinear way — the classic being memory, where a JVM or a Python process with a big cache never gives memory back, so `averageUtilization` on memory ratchets one way. That is why HPA on memory is a trap and CPU or an application-level metric is the right signal.

---

### Q60. What is the Vertical Pod Autoscaler, and can you run it alongside HPA?
`[MEDIUM]`

> **Answer:** VPA right-sizes a pod rather than counting pods — it observes actual CPU and memory usage over time and sets the container's **requests** to what the workload really needs. Three components: the **recommender** (watches usage history and OOM events, produces recommendations), the **updater** (evicts pods whose requests are wrong), and the **admission controller** (a mutating webhook that stamps the recommended requests onto pods as they are created). And no — **you should not run VPA and HPA against the same CPU or memory metric**; Microsoft's own AKS documentation says so outright. They fight: HPA scales replicas because utilisation-against-request is high, VPA raises the request, which drops utilisation, which makes HPA scale back in.

`updateMode` values:

| Mode | Behaviour |
|---|---|
| `Off` | Recommendations only, nothing is changed. **Start here, always.** |
| `Initial` | Requests set at pod creation only; running pods untouched. |
| `Recreate` | Evicts and recreates pods when the recommendation drifts, respecting PodDisruptionBudgets. |
| `InPlaceOrRecreate` | Resizes in place where the cluster supports it, falling back to eviction. AKS **1.34+**. |
| `Auto` | **Deprecated since VPA 1.4.0** (AKS 1.34+) — currently just an alias for `Recreate`. |

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata: { name: reconcile-job, namespace: integration }
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reconcile-job
  updatePolicy:
    updateMode: "Off"                 # recommendation mode while we learn the workload
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        minAllowed: { cpu: 100m, memory: 128Mi }
        maxAllowed: { cpu: "2",  memory: 4Gi }
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsOnly
```

```bash
kubectl describe vpa reconcile-job -n integration    # Target / Lower Bound / Upper Bound per container
```

The legitimate combination is **VPA on memory, HPA on CPU or a custom metric** — different signals, no feedback loop. On AKS the other real constraints: the recommender keeps only **eight days** of history, it is validated to about **1,000 pods per cluster** under VPA objects, JVM workloads are unsupported (the JVM's memory reporting hides the real working set), and VPA can happily recommend more than any node can provide, so pair it with a `LimitRange` or `maxAllowed`.

Where VPA earns its place on an integration platform is not the API tier at all — it is the **batch and reconciliation jobs**, the things that run on a CronJob every fifteen minutes and were sized once, in 2023, by guessing. Run VPA in `Off` mode across the namespace for two weeks and you have a data-driven right-sizing exercise with a cost number attached, which is a very easy conversation to have with a client.

**If they push back — "so how do you right-size the API tier?"** — the same recommender output, applied by a human at review time: read `kubectl describe vpa`, put the target into the Helm values, ship it through the normal pipeline. Recommendation-as-advice, not recommendation-as-automation. That keeps the request value in Git where the [GitOps](05-cicd-iac-and-gitops.md) flow can see it.

---

### Q61. Cluster Autoscaler versus HPA — and what stops a node from being removed?
`[MEDIUM]`

> **Answer:** HPA changes the number of **pods**; the Cluster Autoscaler changes the number of **nodes**. They are complementary and normally both on. CA's scale-up trigger is not CPU pressure — it watches for **pods that are Pending because no node can satisfy their requests**, then adds a node to a node pool. Scale-down is the reverse: a node that has been underutilised for long enough and whose pods can be rescheduled elsewhere gets drained and deleted. On AKS the CA runs in the managed control plane and is tuned through a **cluster-wide autoscaler profile** — you cannot set it per node pool.

The defaults on AKS, which are worth knowing because they explain most "why isn't it scaling?" tickets:

| Setting | Default |
|---|---|
| `scan-interval` | 10 seconds |
| `scale-down-delay-after-add` | 10 minutes |
| `scale-down-unneeded-time` | 10 minutes |
| `scale-down-unready-time` | 20 minutes |
| `scale-down-utilization-threshold` | 0.5 |
| `max-graceful-termination-sec` | 600 seconds |
| `max-node-provision-time` | 15 minutes |
| `expander` | `random` |
| `skip-nodes-with-local-storage` | `false` |
| `skip-nodes-with-system-pods` | `true` |
| `max-empty-bulk-delete` | 10 nodes |
| `ok-total-unready-count` / `max-total-unready-percentage` | 3 nodes / 45% |

```bash
az aks update -g rg-eygds-int -n aks-eygds-int \
  --cluster-autoscaler-profile scan-interval=20s,scale-down-delay-after-add=10m,scale-down-unneeded-time=5m,expander=least-waste,balance-similar-node-groups=true
kubectl get configmap -n kube-system cluster-autoscaler-status -o yaml
kubectl get events --field-selector source=cluster-autoscaler,reason=NotTriggerScaleUp
```

**What blocks a scale-down** — this is the part they're really asking:
- A pod **not backed by a controller** (a bare Pod) — CA won't evict something nothing will recreate.
- A **PodDisruptionBudget** that would be violated (see §9).
- Pods using **local storage** — `emptyDir` or `hostPath` — unless `skip-nodes-with-local-storage=false`.
- **kube-system** pods without a PDB, because `skip-nodes-with-system-pods` defaults to `true`.
- Node selectors or anti-affinity that cannot be honoured anywhere else.
- The explicit opt-out annotation `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"`.

**What blocks a scale-up:** the node pool is at `--max-count`; subnet IP exhaustion (a real one with Azure CNI, where every pod takes a VNet IP); regional core quota; PersistentVolume zone affinity conflicts; restrictive pod topology spread constraints that CA's scheduling simulation cannot satisfy; and pods with a `PriorityClass` below **-10**, which never trigger a scale-up because that band is reserved for overprovisioning placeholder pods. After repeated failures the node pool enters an exponential backoff that can last **up to 30 minutes**, and the only way to clear it is to disable and re-enable autoscaling on the pool.

**AKS node pool design that I'd actually recommend:**
- A **system** node pool with the taint `CriticalAddonsOnly=true:NoSchedule` for CoreDNS, metrics-server, the CSI drivers and KEDA; user workloads on separate **user** pools. This stops a runaway consumer from starving cluster DNS.
- **One node pool per availability zone** plus `balance-similar-node-groups=true` if you use zone-aware scheduling, because CA itself is not zone-aware — zone placement is done by the underlying VM scale set.
- Long-running APIs and bursty batch consumers in **different pools**, selected by affinity or the `priority` expander, so a batch burst doesn't evict the API tier.
- **Spot node pools** for KEDA-driven batch consumers with a priority expander preferring spot, since a reconciliation job that can be retried is exactly the workload spot was built for.
- Never manually resize the VM scale set behind an autoscaled pool, and never turn on the scale set's own autoscaler alongside CA.

**If they push back — "cluster autoscaler vs Karpenter / Node Auto Provisioning?"** — same job, different model: instead of scaling fixed node pools, NAP (AKS's Karpenter-based node auto-provisioning) picks a VM size to fit the pending pods. Better bin-packing and less node-pool design work; less predictable and a newer operational story. On a client cluster I'd default to CA with well-designed pools unless workload shapes are genuinely unpredictable.

---

### Q62. Your Service Bus queue is 200,000 messages deep and the consumers are at 4% CPU. What scales them?
`[HARD]` — *the integration-engineer answer; this is the one to land*

> **Answer:** Nothing, if the HPA is on CPU — and that is the whole point. A consumer blocked on I/O burns almost no CPU: it is asleep in an `await` waiting on a network receive, then it makes a downstream call and waits again. CPU utilisation reflects the cost of *processing* a message, not the *volume of work waiting*. The correct signal is queue depth, and the correct tool is **KEDA**, which scales on Service Bus active message count, Kafka consumer lag, or any of ~70 event sources — and scales **to zero** when the queue is empty, which HPA cannot do.

Why CPU fails here, stated precisely enough to survive a follow-up: HPA's target is a *utilisation* of a resource the pod is consuming. An async consumer's throughput is bounded by concurrency and downstream latency, not by CPU. Ten thousand queued messages and one queued message produce identical CPU. Worse, if you did set a low CPU target to compensate, the scale-out would be driven by processing *cost* — so an expensive message type would scale you out while a cheap backlog of a hundred thousand would not.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payments-consumer-sa
  namespace: integration
  annotations:
    azure.workload.identity/client-id: "11111111-2222-3333-4444-555555555555"
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: servicebus-workload-identity
  namespace: integration
spec:
  podIdentity:
    provider: azure-workload
    # which user-assigned managed identity KEDA federates to when polling the queue.
    # omit to fall back to the client-id annotation on the ServiceAccount.
    identityId: "11111111-2222-3333-4444-555555555555"
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: payments-consumer
  namespace: integration
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payments-consumer
  pollingInterval: 15          # default 30s — how often KEDA asks Service Bus
  cooldownPeriod: 300          # default 300s — wait after last trigger before going to 0
  minReplicaCount: 0           # scale to zero: no messages, no pods, no cost
  maxReplicaCount: 30
  fallback:
    failureThreshold: 3        # if the scaler errors 3x in a row...
    replicas: 3                # ...hold at 3 rather than collapsing to 0
  advanced:
    restoreToOriginalReplicaCount: false
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
          policies:
            - { type: Percent, value: 25, periodSeconds: 60 }
  triggers:
    - type: azure-servicebus
      metadata:
        namespace: eygds-payments-sb        # namespace NAME (not FQDN) — required for identity auth
        queueName: payments-inbound
        messageCount: "20"                  # target messages PER REPLICA (scaler default is 5)
        activationMessageCount: "0"         # >0 messages wakes it from zero
      authenticationRef:
        name: servicebus-workload-identity
```

Read `messageCount: "20"` as *"each replica should be responsible for about 20 queued messages"*: 200,000 active messages ÷ 20 = 10,000 desired, clamped by `maxReplicaCount` to 30. That clamp is deliberate — the real bottleneck downstream is the SAP adapter's connection pool, and scaling consumers past it just converts a queue backlog into downstream timeouts. **Sizing `maxReplicaCount` is a downstream-capacity decision, not a queue-depth decision**, and saying that in the interview is worth more than any YAML.

Two thresholds, not one, and people always conflate them: `activationMessageCount` decides **0 → 1** (KEDA's own decision), while `messageCount` decides **1 → N** (delegated to the HPA it creates). If you want the consumer to stay asleep until at least 100 messages accumulate, that is `activationMessageCount: "100"`, not `messageCount`.

For the identity to work end to end: the AKS cluster has the OIDC issuer and workload identity enabled (Q55); the KEDA operator is installed with `--set podIdentity.azureWorkload.enabled=true --set podIdentity.azureWorkload.clientId=<id> --set podIdentity.azureWorkload.tenantId=<tid>`, which puts the right label and annotation on the KEDA operator's ServiceAccount; a federated credential exists for `system:serviceaccount:keda:keda-operator`; and the managed identity holds **Azure Service Bus Data Receiver** on the queue so it can read runtime properties. The consumer pods separately use their own workload identity to actually receive messages. Two identities, two grants — that separation is what lets the scaler be read-only.

**If they push back — "what does KEDA count, exactly?"** — the queue's **active** message count. Not scheduled messages, not dead-lettered ones. A DLQ that is filling up will not scale anything, which is correct behaviour but means you need a **separate alert on DLQ depth** — see [Messaging](03-messaging-and-event-streaming.md). If you deliberately want a drain worker for the DLQ, that is a second ScaledObject targeting the `.../$deadletterqueue` path.

**If they push back — "does scale-to-zero lose messages?"** — no. Service Bus is the durable buffer; the consumers are stateless. What it *does* cost you is cold start: the first message after an idle period waits for a pod to be scheduled, image pulled (cached on the node if you're lucky), and the Python process to import. Budget 5–20 seconds, and if the SLA can't absorb that, `minReplicaCount: 1` is the correct trade, not an argument against KEDA.

---

### Q63. ScaledObject or ScaledJob, and what is KEDA actually doing under the covers?
`[HARD]`

> **Answer:** For long-running consumers you use a **ScaledObject**, and KEDA does *not* replace the HPA — it creates and manages one, named `keda-hpa-{scaledobject-name}`, and feeds it through the External Metrics API from KEDA's own metrics adapter. KEDA owns exactly one thing the HPA cannot do: the **0 ↔ 1** transition, which it performs directly on the Deployment. Everything from 1 to N is a normal HPA doing the normal formula from Q58. For work that is naturally one-message-one-execution — a long batch reconciliation, a file transformation that must not be interrupted mid-flight — you use a **ScaledJob**, which creates a Kubernetes Job per unit of work instead of scaling a Deployment.

```bash
kubectl get scaledobject,hpa -n integration
# NAME                                  SCALETARGETKIND  READY  ACTIVE
# scaledobject.keda.sh/payments-consumer apps/v1.Deployment True  True
# NAME                                       REFERENCE                    TARGETS
# horizontalpodautoscaler.../keda-hpa-payments-consumer  Deployment/...   1200/20 (avg)
kubectl describe scaledobject payments-consumer -n integration
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/integration" | jq
```

That architecture has a consequence worth volunteering: **you must not put a plain HPA on the same Deployment as a ScaledObject.** Two controllers writing `spec.replicas` fight, and the symptom is a replica count that oscillates on a 15-second beat. If you need custom scale-down behaviour, put it in `advanced.horizontalPodAutoscalerConfig.behavior` on the ScaledObject, as in Q62.

**ScaledObject vs ScaledJob:**

| | ScaledObject | ScaledJob |
|---|---|---|
| Target | Deployment / StatefulSet / any `/scale` CRD | creates `batch/v1` Jobs |
| Underlying mechanism | manages an HPA | creates Jobs directly, no HPA |
| Right for | continuous consumers, APIs | long or non-interruptible per-message work |
| Interruption | a pod may be killed mid-message on scale-down | a Job runs to completion |
| Key defaults | `pollingInterval` 30s, `cooldownPeriod` 300s, `minReplicaCount` 0, `maxReplicaCount` 100 | `pollingInterval` 30s, `maxReplicaCount` 100, `successfulJobsHistoryLimit` 100, `failedJobsHistoryLimit` 100, `scalingStrategy.strategy` `default` |

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata: { name: statement-reconciliation, namespace: integration }
spec:
  jobTargetRef:
    parallelism: 1
    completions: 1
    backoffLimit: 2
    activeDeadlineSeconds: 3600
    template:
      metadata:
        labels: { azure.workload.identity/use: "true" }
      spec:
        serviceAccountName: reconciliation-sa
        restartPolicy: Never
        containers:
          - name: reconcile
            image: myacr.azurecr.io/reconciliation:3.0.1
            command: ["python", "-m", "app.jobs.reconcile_one"]
            resources:
              requests: { cpu: 500m, memory: 1Gi }
              limits:   { memory: 2Gi }
  pollingInterval: 30
  maxReplicaCount: 20
  successfulJobsHistoryLimit: 20
  failedJobsHistoryLimit: 50
  scalingStrategy:
    strategy: "accurate"          # accounts for running jobs; better for long-running work
  triggers:
    - type: azure-servicebus
      metadata:
        namespace: eygds-payments-sb
        queueName: reconciliation-requests
        messageCount: "1"          # one job per message
      authenticationRef:
        name: servicebus-workload-identity
```

**The Kafka variant**, since the JD names Kafka first — same shape, different trigger, and one crucial extra rule:

```yaml
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: eygds-kafka.servicebus.windows.net:9093
        consumerGroup: settlement-processor
        topic: trades.settled.v1
        lagThreshold: "50"              # scaler default is 10
        activationLagThreshold: "0"
        offsetResetPolicy: latest
        excludePersistentLag: "false"
      authenticationRef:
        name: kafka-sasl-auth
```

The rule: **replicas are capped at the topic's partition count**, because a consumer group cannot have more active consumers than partitions — the extras sit idle holding no assignment. KEDA enforces this by default. You can override it with `allowIdleConsumers: "true"` but you almost never should; the correct fix for "I need more throughput than partitions allow" is more partitions, which is a topic-design decision. `excludePersistentLag: "true"` is the escape hatch for a poison partition whose lag never moves and would otherwise pin you at max replicas forever. Details of consumer groups, partitions and rebalancing are in [Messaging](03-messaging-and-event-streaming.md).

**TriggerAuthentication** is the object that keeps credentials out of every ScaledObject. It supports `podIdentity` (as in Q62 — no secret at all, the right answer on AKS), `secretTargetRef` (pointing at a Kubernetes Secret key), `env` (from the target's env), and `azureKeyVault` (fetched directly from Key Vault). There is also a `ClusterTriggerAuthentication` for a shared, cluster-scoped credential — which is the paved-road version: the platform team defines one `ClusterTriggerAuthentication` per messaging namespace and application teams reference it by name and never see a connection string.

**If they push back — "which trigger would you use to scale on something that isn't a queue?"** — the same mechanism generalises: the `cron` scaler for known business-hours load (pre-warm the settlement consumers at 07:45 IST before the batch window), `prometheus` for any PromQL expression, `azure-monitor` for an Azure metric, `postgresql` for an outbox table's row count. That last one is the neat one for integration work — a transactional outbox with an unpublished-row count is a perfectly good scaling trigger, and it ties the scaling signal to the exact thing you care about.

**If they push back — "how do you troubleshoot a ScaledObject that says READY=False?"** — in order: `kubectl describe scaledobject` for the condition message; `kubectl logs -n keda deploy/keda-operator` for the scaler's actual error (auth failures show up here, not on the ScaledObject); confirm the external metric resolves via `kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/<ns>"`; then check the Azure side — the federated credential subject, and whether the identity has **Data Receiver** on the queue. A `403` in the operator log with `READY=False` is almost always a missing role assignment, and a `404` is almost always a `namespace` value written as an FQDN instead of a bare namespace name.

## 12. Scheduling and network policy

### Q64. Walk me through what happens between `kubectl apply` and the pod actually running — and what makes a pod stay `Pending`.
`[MEDIUM]`

> The scheduler watches for pods whose `spec.nodeName` is empty and runs two phases over the nodes: **filter**, which throws away every node the pod cannot possibly run on, and **score**, which ranks the survivors. The winner gets a `Binding` written back to the API server, and the kubelet on that node pulls the image and starts the containers. `Pending` means the filter phase left zero feasible nodes — so the answer is always in `kubectl describe pod`, in the `FailedScheduling` event, which tells you exactly which predicate rejected how many nodes.

**Filter** (does it fit at all): free **requests** on the node for CPU/memory/ephemeral-storage, `nodeSelector`/`nodeAffinity` match, taints tolerated, host ports free, volume topology (a zonal managed disk pins the pod to that zone), pod affinity/anti-affinity satisfiable, `topologySpreadConstraints` with `DoNotSchedule` not violated, `maxPods` on the node not reached.

**Score** (which of the survivors is best): `NodeResourcesFit` with the default `LeastAllocated` strategy (spread load), `ImageLocality` (node already has the image layers), `InterPodAffinity` weights, `PodTopologySpread`, `TaintToleration`. On large clusters the scheduler deliberately scores only a sample of feasible nodes (`percentageOfNodesToScore`, adaptive by default) to bound scheduling latency.

The realistic `Pending` causes, in the order I check them:

| Symptom in the event | Real cause |
|---|---|
| `Insufficient cpu` / `Insufficient memory` | Sum of **requests** already on the node, not usage. Allocatable < Capacity because of kube-reserved/system-reserved and DaemonSets. |
| `node(s) didn't match Pod's node affinity/selector` | Label typo, or the node pool with that label is scaled to 0 and the autoscaler can't grow it. |
| `node(s) had untolerated taint {...}` | Spot pool, `CriticalAddonsOnly`, or a node stuck `NotReady`. |
| `node(s) had volume node affinity conflict` | Zonal disk in zone 1, only zone 2/3 nodes have room. |
| `node(s) didn't match pod topology spread constraints` | `maxSkew` with `DoNotSchedule` and a zone is full. |
| `pod has unbound immediate PersistentVolumeClaims` | No matching StorageClass / no capacity. |
| Nothing at all, event is old | Cluster autoscaler hit `max-count`, vCPU quota, or regional capacity. |

```bash
kubectl describe pod orders-api-7d9c4-abcde -n integration | sed -n '/Events/,$p'
kubectl get events -n integration --field-selector reason=FailedScheduling --sort-by=.lastTimestamp
kubectl describe node aks-apppool-41287654-vmss000002 | sed -n '/Allocated resources/,$p'
kubectl get pod orders-api-7d9c4-abcde -n integration -o jsonpath='{.status.conditions[?(@.type=="PodScheduled")].message}{"\n"}'
```

**If they push back — "the node clearly has free memory, why is it Pending?"** — because scheduling is done against **requests**, not live usage. A node with 8 Gi allocatable and 7.5 Gi of requests is full to the scheduler even if actual usage is 2 Gi. That is also the argument for setting honest requests: over-requesting wastes half the cluster, under-requesting gets you OOMKilled and evicted under pressure (see §9).

---

### Q65. `nodeSelector` vs node affinity, and when do you actually need pod affinity or anti-affinity?
`[MEDIUM]`

> `nodeSelector` is the primitive version — an exact label match, all terms AND-ed, no way to express "prefer". Node affinity replaces it and adds two things that matter: `requiredDuringSchedulingIgnoredDuringExecution`, which is a hard filter, and `preferredDuringSchedulingIgnoredDuringExecution`, which is a weighted (1–100) scoring hint. Pod affinity and anti-affinity are different — they place pods relative to *other pods* over a `topologyKey`, and the everyday use is anti-affinity to stop all replicas of one API landing in one zone or on one node.

`IgnoredDuringExecution` in both names is the honest part of the API: these rules are evaluated **at scheduling time only**. Relabel the node afterwards and nothing moves.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: integration
spec:
  replicas: 6
  selector:
    matchLabels: { app.kubernetes.io/name: orders-api }
  template:
    metadata:
      labels:
        app.kubernetes.io/name: orders-api
        app.kubernetes.io/instance: orders-api-prod
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:                    # terms are OR-ed
              - matchExpressions:                 # expressions inside a term are AND-ed
                  - key: kubernetes.io/os
                    operator: In
                    values: ["linux"]
                  - key: workload
                    operator: In
                    values: ["integration"]
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 80
              preference:
                matchExpressions:
                  - key: topology.kubernetes.io/zone
                    operator: In
                    values: ["southindia-1"]      # co-locate with the primary Service Bus namespace
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels: { app.kubernetes.io/name: orders-api }
      containers:
        - name: api
          image: myacr.azurecr.io/orders-api:1.4.2
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits:   { memory: 512Mi }
```

`topologyKey` is the whole point of (anti-)affinity: `kubernetes.io/hostname` means "one per node", `topology.kubernetes.io/zone` means "one per zone". Operators available: `In`, `NotIn`, `Exists`, `DoesNotExist`, and `Gt`/`Lt` for node affinity only.

**If they push back — "why preferred and not required anti-affinity?"** — `requiredDuringScheduling` anti-affinity over `kubernetes.io/hostname` with 6 replicas and 4 nodes leaves 2 replicas `Pending` forever, and it blocks rolling updates because the surge pod cannot be placed. Required anti-affinity is for things that genuinely must not share a failure domain (a 3-node quorum). For "spread my API replicas", use `preferred` — or better, `topologySpreadConstraints` (Q66), which is cheaper for the scheduler and expresses the intent exactly.

---

### Q66. Explain `topologySpreadConstraints` and `maxSkew`. Why prefer it over anti-affinity?
`[HARD]` — *the zone-spreading question; very common when the interviewer says "three availability zones"*

> `topologySpreadConstraints` says "keep the number of my pods per domain within `maxSkew` of the emptiest domain", where a domain is defined by `topologyKey`. Anti-affinity can only say "at most one per domain"; spread constraints say "roughly even across domains", which is what you actually want for 6 replicas over 3 zones. And it scales — anti-affinity forces the scheduler to compare the incoming pod against every existing pod in every candidate domain, which gets expensive on a big cluster.

**Skew** = (matching pods in this domain) − (global minimum across eligible domains). With `whenUnsatisfiable: DoNotSchedule`, a placement that pushes the skew above `maxSkew` is rejected and the pod goes `Pending`. With `ScheduleAnyway`, it is a scoring preference only. Zones holding 2, 2, 1 pods with `maxSkew: 1` is legal; adding the next pod to a "2" zone would make it 3 vs a global minimum of 1, skew 2 — rejected.

```yaml
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule          # hard: never let one zone hold the extra replicas
          minDomains: 3                             # stable since 1.30; only valid with DoNotSchedule
          matchLabelKeys: ["pod-template-hash"]     # only count pods of THIS ReplicaSet
          nodeAffinityPolicy: Honor                 # default (null == Honor)
          nodeTaintsPolicy: Ignore                  # default (null == Ignore)
          labelSelector:
            matchLabels: { app.kubernetes.io/name: orders-api }
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway         # soft: prefer node spread, never block a rollout
          labelSelector:
            matchLabels: { app.kubernetes.io/name: orders-api }
```

Field notes worth having: `minDomains` went stable in **1.30** — without it, if only one zone has ready nodes, the global minimum is computed over one domain and everything piles into it; `matchLabelKeys` (beta and on by default since **1.27**) is what stops the old ReplicaSet's pods from counting against the new one during a rollout; `nodeAffinityPolicy` and `nodeTaintsPolicy` went GA in **1.33**, defaulting to `Honor` and `Ignore` respectively.

Platform-engineer framing: the zone constraint plus a PDB (see §9) go in the golden Helm chart's `_helpers.tpl`, not in each team's values file. Teams get zone spreading whether or not they know what a topology key is.

**If they push back — "what if a whole zone goes down?"** — with `DoNotSchedule` the replacement pods stay `Pending` rather than crowding into the surviving zones, which is exactly wrong during an outage. Pair the hard zone constraint with a soft hostname constraint, or use `ScheduleAnyway` on the zone constraint for workloads where availability beats perfect balance. That trade-off — availability vs. balance during a zone failure — is the answer they are fishing for.

---

### Q67. Taints and tolerations — the three effects, and how does AKS use them?
`[MEDIUM]`

> Taints go on nodes and repel pods; tolerations go on pods and let them ignore a specific taint. Three effects: `NoSchedule` blocks new pods, `PreferNoSchedule` is the soft version, and `NoExecute` also evicts pods that are already running and don't tolerate it. The key subtlety is that a toleration is permission, not attraction — it lets a pod land on a tainted node, it does not pull it there. To dedicate a pool you need both: a taint on the nodes and a `nodeSelector`/affinity on the pods.

```yaml
      tolerations:
        - key: "kubernetes.azure.com/scalesetpriority"
          operator: "Equal"
          value: "spot"
          effect: "NoSchedule"
        - key: "node.kubernetes.io/unreachable"      # override the admission-added default
          operator: "Exists"
          effect: "NoExecute"
          tolerationSeconds: 30
      nodeSelector:
        kubernetes.azure.com/scalesetpriority: spot  # toleration alone would NOT pull it here
```

Built-in node-condition taints applied by the control plane: `node.kubernetes.io/not-ready` and `node.kubernetes.io/unreachable` (both `NoExecute`), plus `memory-pressure`, `disk-pressure`, `pid-pressure`, `unschedulable`, `network-unavailable` (all `NoSchedule`). The `DefaultTolerationSeconds` admission controller silently adds a **300 second** toleration for the two `NoExecute` ones to every pod — which is why a pod on a dead node takes about five minutes to be recreated elsewhere unless you override it.

AKS uses taints as its own control surface:

| Taint / label | Where | Why |
|---|---|---|
| `CriticalAddonsOnly=true:NoSchedule` | Dedicated system node pool | Keeps CoreDNS, metrics-server and add-ons away from your app pods (`--node-taints` on `az aks nodepool add --mode System`). |
| `kubernetes.azure.com/scalesetpriority=spot:NoSchedule` + label `...scalesetpriority: spot` | Spot pools | Only workloads that explicitly tolerate eviction land there. |
| `kubernetes.azure.com/mode: system` (label) | System pools | AKS *prefers* system pods here; it does not force them. |

**If they push back — "how fast does a workload move when a node dies?"** — the node controller marks the node `NotReady`, applies `node.kubernetes.io/not-ready:NoExecute`, and the default 300 s toleration keeps the pod bound for five minutes before eviction. For a latency-critical consumer I drop `tolerationSeconds` to 30 in the golden chart — but not lower, or a transient kubelet heartbeat blip starts churning pods across the cluster.

---

### Q68. What are PriorityClasses and preemption, and would you use them on a shared integration cluster?
`[HARD]`

> A PriorityClass maps a name to an integer; pods reference it and the scheduler orders its queue by that integer. If a high-priority pod cannot be scheduled, the scheduler looks for a node where evicting lower-priority pods would make room, sets `nominatedNodeName`, evicts them with their normal graceful termination, and schedules the pod. On a shared platform I do use it, but with exactly three tiers and a `ResourceQuota` guarding them — otherwise every team labels its own workload critical and priority becomes noise.

Reserved values: `system-node-critical` = **2000001000**, `system-cluster-critical` = **2000000000**. User-defined classes are capped at **1000000000**, names can't start with `system-`, and only one class may set `globalDefault: true` (pods with no class get priority 0 otherwise). `preemptionPolicy: Never` (stable since 1.24) gives a pod queue priority without letting it evict anyone — the right setting for batch that should jump the queue but never kill a live API.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: platform-critical }
value: 1000000
globalDefault: false
description: "Ingress controllers, cert-manager, KEDA, log shippers."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: business-critical }
value: 100000
globalDefault: false
description: "Payment and settlement APIs and their queue consumers."
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata: { name: batch-nonpreempting }
value: 1000
preemptionPolicy: Never
globalDefault: false
description: "Overnight reconciliation jobs on the spot pool."
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: restrict-business-critical, namespace: integration }
spec:
  hard: { "pods": "40" }
  scopeSelector:
    matchExpressions:
      - operator: In
        scopeName: PriorityClass
        values: ["business-critical"]
```

That `ResourceQuota` with a `PriorityClass` scope is the governance half of the answer and almost nobody mentions it: without it, priority is a self-declared field and the tier collapses.

**If they push back — "does preemption respect PodDisruptionBudgets?"** — best effort only. The scheduler prefers victims whose PDB would not be violated, but if no such victim set exists it preempts anyway and the PDB is violated. PDBs protect against voluntary disruption (drains, upgrades); preemption is not fully bound by them, and neither is a node dying.

---

### Q69. A pod in namespace A can reach a pod in namespace B by default. How do you lock that down for a bank?
`[HARD]` — *the segmentation question; expect it in any financial-services round*

> Kubernetes networking is flat and **default-allow** — every pod can reach every other pod and every external endpoint, across namespaces, and nothing logs it. `NetworkPolicy` is the fix: a namespaced allow-list, selected by pod labels. Two things surprise people. First, a pod is only isolated once *some* policy selects it — policies are purely additive, there is no deny rule and no ordering. Second, the `NetworkPolicy` object is inert unless the CNI enforces it: on AKS that means Cilium, Azure NPM or Calico, and if you never enabled one, `kubectl apply` succeeds and nothing is blocked. The baseline I ship is default-deny ingress **and** egress per namespace, plus explicit allows.

**Enforcement on AKS.** Cilium is the current recommendation (eBPF data plane, plus FQDN and L7 policy beyond the upstream spec) and is enabled with `--network-dataplane cilium`; Azure NPM (`--network-policy azure`) is iptables/ipsets-based and is being retired — **30 September 2026** for Windows nodes and **30 September 2028** for Linux, with NPM on Linux additionally unsupported beyond 250 nodes / 20,000 pods; Calico (`--network-policy calico`) remains for Windows and legacy clusters. It is no longer create-time-only — `az aks update --network-policy azure|calico|none` works on an existing cluster, but it **reimages every node pool simultaneously**, so it is a maintenance-window change.

```bash
az aks create -g rg-integration -n aks-integration-prod \
  --network-plugin azure --network-plugin-mode overlay \
  --network-dataplane cilium --tier standard --generate-ssh-keys
```

The baseline, in three objects per namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: integration }
spec:
  podSelector: {}                       # every pod in the namespace
  policyTypes: [Ingress, Egress]        # no rules == deny everything in both directions
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns-egress, namespace: integration }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels: { kubernetes.io/metadata.name: kube-system }
          podSelector:
            matchLabels: { k8s-app: kube-dns }
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: orders-api-allows, namespace: integration }
spec:
  podSelector:
    matchLabels: { app.kubernetes.io/name: orders-api }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: { kubernetes.io/metadata.name: ingress-nginx }
      ports: [{ protocol: TCP, port: 8000 }]
  egress:
    - to:                                        # Service Bus / SQL reached via private endpoints
        - ipBlock:
            cidr: 10.42.8.0/24
      ports: [{ protocol: TCP, port: 5671 }, { protocol: TCP, port: 1433 }]
    - to:                                        # the legacy SOAP host on-premises
        - ipBlock:
            cidr: 172.20.14.7/32
      ports: [{ protocol: TCP, port: 8443 }]
```

Traps to state before they ask:

- **`podSelector` + `namespaceSelector` in the same `from` element are AND-ed** ("pods labelled `role=client` *in* namespaces labelled `user=alice`"); as two separate list items they are OR-ed. This is the single most common NetworkPolicy bug.
- **Default-deny egress breaks DNS first.** Nothing resolves, everything looks like a hung connection, and the app logs say "name resolution failure". Ship the DNS policy in the same chart as the deny.
- **No FQDN, no L7, no deny rules** in the upstream API. Egress to `*.servicebus.windows.net` is not expressible — you allow the private endpoint CIDR, or you use Cilium FQDN policy, or you send egress through Azure Firewall via a UDR.
- **LoadBalancer traffic is SNAT/DNAT-rewritten** before policies see it, so `ipBlock` on ingress from the internet is unreliable — use `spec.loadBalancerSourceRanges` on the Service, which is applied earlier.

**If they push back — "isn't that what a service mesh is for?"** — they solve different halves. NetworkPolicy is L3/L4 reachability enforced in the node data plane; a mesh gives every workload a cryptographic identity and mTLS on the wire. In Istio you set `PeerAuthentication` to `STRICT` for mesh-wide mTLS and `AuthorizationPolicy` for identity- and L7-aware rules (`GET /v1/payments` from `orders-api` only). For a regulated client I run both: NetworkPolicy is the coarse segmentation an auditor can read, mTLS is the encryption-in-transit and identity control, and neither trusts the pod IP.

**If they push back — "sidecar or ambient mode?"** — sidecar injects an Envoy per pod: full L7 anywhere, but a pod restart to inject, per-pod CPU/memory overhead, and every mesh upgrade is a fleet-wide restart. Ambient splits it — a per-node `ztunnel` DaemonSet does L4 mTLS with no pod restarts, and you add waypoint proxies only for the namespaces that need L7. Ambient is the direction of travel, but note for AKS specifically: **the managed AKS Istio add-on does not support ambient mode yet** — it is sidecar-only — so on AKS today it is sidecar via the add-on, or self-managed Istio/Linkerd which the add-on also refuses to coexist with.

---

## 13. AKS specifics: CNI, workload identity, AGIC, Container Apps

### Q70. Azure CNI, kubenet, or Azure CNI Overlay — which one and why?
`[HARD]` — *the AKS networking question; the IP-address answer is what separates a platform engineer from an app developer*

> Three IP-address-management models. **kubenet** gives pods addresses from a private range outside the VNet and needs route tables on the cluster subnet — it caps at 400 nodes and it is retired on **31 March 2028**. **Flat Azure CNI** gives every pod a real VNet IP: directly routable, but it eats the subnet alive. **Azure CNI Overlay** gives nodes VNet IPs and carves a **/24 per node** out of a private pod CIDR that lives outside the VNet, scaling to 5,000 nodes and 250 pods per node with VM-grade pod-to-pod performance. In an enterprise hub-and-spoke where the network team hands you a /24 and will not hand you another, Overlay is the answer, and it is now the AKS default when you don't specify `--network-plugin`.

The arithmetic is the whole argument, and it is a good whiteboard moment:

- Flat Azure CNI with `maxPods=30`: each node reserves **31** VNet IPs (node + 30 pods). A `/24` has 251 usable addresses → **8 nodes**, before you leave headroom for upgrade surge.
- Azure CNI Overlay: each node consumes **1** VNet IP; the same `/24` carries ~250 nodes, and pods come from `10.244.0.0/16` (the default `--pod-cidr`), which may even be reused across independent clusters in the same VNet.

| | Azure CNI Overlay | Azure CNI (flat / node subnet) | kubenet (legacy) |
|---|---|---|---|
| Pod IP source | Private pod CIDR, `/24` per node | Cluster/pod subnet in the VNet | Private range + UDRs |
| Max nodes | 5,000 | Subnet-bound | **400** |
| Max pods/node | 250 (default 250 for Overlay; 30 for flat CNI, 110 for kubenet via CLI) | 250 | 250 |
| Pod reachable from outside | No — SNAT to node IP | Yes, directly | No |
| Route table maintenance | None | None | Required |
| Status | Default, recommended | Use when pods must be directly addressable | Retired 31 Mar 2028 |

```bash
az aks create -g rg-integration -n aks-integration-prod \
  --network-plugin azure --network-plugin-mode overlay \
  --pod-cidr 192.168.0.0/16 --service-cidr 10.42.0.0/16 --dns-service-ip 10.42.0.10 \
  --vnet-subnet-id "$SUBNET_ID" --network-dataplane cilium \
  --tier standard --zones 1 2 3 --generate-ssh-keys
```

The trade-off that matters for financial-services integration: with Overlay, **pod egress is SNAT'd to the node IP**, so when the client's firewall or a partner's allow-list is per-source-IP, you allow-list the node subnet (or, better, a fixed NAT Gateway public IP), never pod IPs. And the pod CIDR must not overlap anything reachable over peering, ExpressRoute or VPN — an on-prem host inside your pod CIDR simply becomes unreachable from the cluster. If something outside genuinely must dial a pod directly, that is the case for **Azure CNI Pod Subnet** (flat, pods on their own dedicated subnet), not for going back to node-subnet CNI.

**If they push back — "we're on kubenet today, how do you migrate?"** — `az aks update` onto Azure CNI Overlay; it reimages every node pool, so it is a maintenance-window operation, and it is a one-way door: on Linux-only Overlay clusters the pod CIDR can later be **expanded** to a larger containing superset, but never shrunk or replaced.

---

### Q71. How would you lay out node pools for an integration platform on AKS?
`[MEDIUM]`

> At minimum three pools. A dedicated **system** pool tainted `CriticalAddonsOnly=true:NoSchedule` so CoreDNS and the add-ons never fight my workloads; a zone-spread **user** pool for the APIs and the always-on queue consumers; and a **spot** pool, tainted and labelled, for batch and reconciliation jobs that can be evicted. Node pools are the unit of taint, label, VM size, zone, `maxPods` and Kubernetes version, so the pool layout *is* the scheduling policy.

| Pool | Mode | Sizing | Taints / labels | Runs |
|---|---|---|---|---|
| `syspool` | System | 3 × D4s_v5, zones 1–3 | `CriticalAddonsOnly=true:NoSchedule` | CoreDNS, metrics-server, CSI drivers, ingress controller |
| `apppool` | User | autoscale 3–20, zones 1–3 | `workload=integration` | REST APIs, Service Bus/Kafka consumers |
| `batchpool` | User, **Spot** | autoscale 0–10 | `kubernetes.azure.com/scalesetpriority=spot:NoSchedule` | Nightly reconciliation, replay jobs |

Hard facts to quote: system pools need **at least 2 nodes** (3 recommended), must be Linux, need a VM SKU of at least **4 vCPU and 4 GB**, no B-series, and **cannot be Spot**; a cluster must always have at least one system pool. Limits: **1,000 nodes per node pool**, **100 node pools per cluster**, **5,000 nodes per cluster** on VMSS + Standard LB, and **300 load-balanced Services per cluster** — that last one is the reason you use one ingress rather than a `LoadBalancer` Service per API.

```bash
az aks nodepool add -g rg-integration --cluster-name aks-integration-prod -n batchpool \
  --priority Spot --eviction-policy Delete --spot-max-price -1 \
  --enable-cluster-autoscaler --min-count 0 --max-count 10 \
  --node-vm-size Standard_D8s_v5 --max-pods 50 --mode User --zones 1 2 3
```

`--spot-max-price -1` means "never evict me on price, only on capacity", `Delete` (the default) removes evicted nodes rather than leaving them deallocated against your quota, and `priority`/`eviction-policy` are immutable after creation. Also immutable per pool: `maxPods` — to change it you add a new pool and drain the old one, which is exactly why `maxPods` belongs in the platform's Terraform module and not in a ticket.

**If they push back — "what happens when a spot node is evicted mid-batch?"** — nothing graceful. The pod dies with the node, so spot workloads must be restartable and idempotent: consumers that checkpoint (Service Bus lock renewal / Kafka offset commit after processing — see [Messaging](03-messaging-and-event-streaming.md)), Jobs with a `backoffLimit`, and no expectation that a PDB saves you. PDBs bound *voluntary* disruption; eviction and node death are involuntary. Also keep the autoscaler on the spot pool, or after one eviction wave the pool sits at zero until a human notices.

---

### Q72. How does a pod get an Azure token — for Key Vault or Service Bus — without a secret in the cluster?
`[HARD]` — *pairs with [Auth](06-auth-and-security.md); near-certain in an Azure integration interview*

> Microsoft Entra Workload ID. The cluster publishes an OIDC issuer; the pod gets a short-lived, audience-scoped ServiceAccount token projected into its filesystem; the Azure SDK exchanges that token at the Entra v2 token endpoint for an access token, because a **federated identity credential** on a user-assigned managed identity trusts that issuer plus the subject `system:serviceaccount:<namespace>:<serviceaccount>`. No client secret exists anywhere — not in a Kubernetes Secret, not in Key Vault, not in the pipeline. The old **pod-managed identity** approach is dead: the open-source project was deprecated in October 2022 and archived in 2023, and the AKS managed add-on was only patched through September 2025.

```bash
az aks update -g rg-integration -n aks-integration-prod \
  --enable-oidc-issuer --enable-workload-identity

ISSUER=$(az aks show -g rg-integration -n aks-integration-prod \
  --query oidcIssuerProfile.issuerUrl -o tsv)

az identity create -g rg-integration -n id-orders-api
CLIENT_ID=$(az identity show -g rg-integration -n id-orders-api --query clientId -o tsv)

az identity federated-credential create \
  --name fic-orders-api --identity-name id-orders-api -g rg-integration \
  --issuer "$ISSUER" \
  --subject "system:serviceaccount:integration:orders-sa" \
  --audience api://AzureADTokenExchange
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-sa
  namespace: integration
  annotations:
    azure.workload.identity/client-id: "00000000-0000-0000-0000-000000000000"
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: orders-api, namespace: integration }
spec:
  selector:
    matchLabels: { app.kubernetes.io/name: orders-api }
  template:
    metadata:
      labels:
        app.kubernetes.io/name: orders-api
        azure.workload.identity/use: "true"   # REQUIRED, or the webhook skips the pod
    spec:
      serviceAccountName: orders-sa
      containers:
        - name: api
          image: myacr.azurecr.io/orders-api:1.4.2
```

The mutating webhook injects `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_AUTHORITY_HOST` and `AZURE_FEDERATED_TOKEN_FILE` plus the projected token volume. Application code changes to nothing:

```python
from azure.identity.aio import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient

credential = DefaultAzureCredential()          # picks WorkloadIdentityCredential from the env vars
client = ServiceBusClient(
    fully_qualified_namespace="sb-integration-prod.servicebus.windows.net",
    credential=credential,
)

async def publish(payload: bytes) -> None:
    async with client:
        sender = client.get_queue_sender(queue_name="orders-inbound")
        async with sender:
            from azure.servicebus import ServiceBusMessage
            await sender.send_messages(ServiceBusMessage(payload))
```

Numbers they may probe: the projected SA token defaults to **3600 seconds** and is configurable **3600–86400** via `azure.workload.identity/service-account-token-expiration`; the Entra access token it buys lasts 24 hours; minimum `azure-identity` for Python is **1.13.0**; and there is a hard limit of **20 federated identity credentials per managed identity**.

**If they push back — "20 FICs won't cover 40 microservices"** — correct, and that is a design signal, not a blocker. One managed identity per bounded context (one per team or per data domain), with several ServiceAccounts federated to it, rather than one identity per deployment. Azure RBAC is then scoped per identity — `Azure Service Bus Data Sender` on one queue, not `Contributor` on the namespace.

---

### Q73. AGIC or nginx ingress on AKS — which do you pick?
`[MEDIUM]`

> nginx (or the AKS app routing add-on) when I want cheap, portable, in-cluster L7 with the full annotation surface, and when the team is comfortable owning it. AGIC when the enterprise already terminates at an Azure Application Gateway with WAF_v2 — AGIC turns Ingress objects into Application Gateway config and the gateway talks straight to pod IPs, skipping the in-cluster proxy hop and the second load balancer. For anything new, though, Microsoft now points you at **Application Gateway for Containers**, which is the ground-up rebuild: ALB Controller in-cluster, Azure-managed data plane, and both the Ingress API and Gateway API (v1.5) instead of a wall of annotations.

Facts that show you have run it:

- AGIC works **only** with `Standard_v2` and `WAF_v2` Application Gateway SKUs.
- **One AGIC add-on per cluster, targeting one Application Gateway.** More than that means the Helm deployment, not the add-on.
- **AGIC assumes full ownership** of the gateway it is attached to and overwrites listeners, rules and backend pools that are not expressed as Ingress objects. Export the ARM template before you enable it. `ProhibitedTargets` (co-existing with hand-managed config) exists only in the Helm flavour.
- With Azure CNI Overlay you need AGIC **v1.9.1+**, the Application Gateway subnet must be a `/24` or smaller and delegated to `Microsoft.Network/applicationGateways`, and the gateway VNet cannot be peered from another region.
- Application Gateway for Containers adds WAF, mTLS to frontend and/or backend, header/URL rewrite, gRPC, traffic splitting, and least-request/ring-hash load balancing.

Financial-services framing: the WAF, the TLS policy and the central certificate are usually non-negotiable controls, and they belong at the Azure-managed edge — which is the real argument for AGIC/AGC over nginx, not raw performance. Token validation and quota still sit in front of that at APIM ([Azure integration services](02-azure-integration-services.md), [Auth](06-auth-and-security.md)).

**If they push back — "why not one `LoadBalancer` Service per API?"** — a public IP and a frontend rule per API, a hard cap of **300 load-balanced Services per cluster**, no host/path routing, no shared WAF, and certificate management smeared across every team. Ingress is one entry point, one cert story, one WAF, one place to put rate limits.

---

### Q74. It's a private cluster in a bank. What can you *not* control, and how do you reach the API server?
`[MEDIUM]`

> The control plane is AKS-managed and lives in Microsoft's subscription: no SSH to the masters, no custom `kube-apiserver` flags, no direct etcd access, no etcd backup you can take yourself. What I control is node pools, networking, RBAC, add-ons, admission (via Azure Policy/Gatekeeper) and the version. In a private cluster the API server is exposed through a Private Link private endpoint in my VNet with a `privatelink.<region>.azmk8s.io` private DNS zone, so `kubectl` only works from a connected network — peered VNet, VPN, ExpressRoute or Bastion — and `az aks command invoke` is the escape hatch when there is no network path at all.

```bash
az aks create -g rg-integration -n aks-integration-prod \
  --enable-private-cluster --private-dns-zone system --disable-public-fqdn \
  --assign-identity "$UAMI_ID" --load-balancer-sku standard \
  --network-plugin azure --network-plugin-mode overlay --generate-ssh-keys

# no network path? run through the Azure control plane instead of the data path
az aks command invoke -g rg-integration -n aks-integration-prod \
  --command "kubectl get pods -n integration -o wide"
```

Consequences worth naming before they ask:

- **IP authorized ranges (`--api-server-authorized-ip-ranges`) apply only to a public API server** — they are the cheaper alternative to a private cluster, not an addition to it.
- **Azure DevOps Microsoft-hosted agents cannot reach a private cluster.** You need self-hosted / scale-set agents inside the VNet — which is exactly why GitOps pull-based delivery (Flux/Argo running *inside* the cluster) fits private clusters better than push-based deploys ([CI/CD & GitOps](05-cicd-iac-and-gitops.md)).
- **ACR needs Private Link too**, or image pulls fail on a locked-down cluster.
- Deleting or editing the private endpoint in your subnet breaks the cluster.
- Because you cannot back up etcd, **the Git repo is the disaster-recovery plan** for cluster state, plus Velero for PVs.

Tier choice, since a bank will ask about the SLA: **Free** has no financially backed SLA and is recommended below 10 nodes; **Standard** gives **99.95%** API server availability with availability zones (99.9% without) and scales to 5,000 nodes; **Premium** adds 24-month Long Term Support for a Kubernetes version. Production integration platform = Standard minimum, Premium if the client's change-freeze calendar makes annual minor upgrades unrealistic.

**If they push back — "how do you prove who did what on the cluster?"** — Entra ID authentication with Azure RBAC (no local accounts: `--disable-local-accounts`), plus diagnostic settings streaming the `kube-audit` and `kube-audit-admin` categories to Log Analytics with the retention the client's policy requires. `kube-audit-admin` drops the read events and is usually the one you keep long-term for cost reasons.

---

### Q75. How do you upgrade a production AKS cluster without an outage?
`[HARD]` — *the operational-runbook question; JD item 9 in disguise*

> Two independent tracks. Kubernetes version: AKS supports **N, N-1 and N-2** with a 12-month support window per GA minor, you cannot skip a minor version on a non-LTS cluster, and the control plane goes first — since 1.28 it may run up to three minors ahead of the node pools, so I upgrade the control plane, validate, then roll node pools one at a time. Node OS image: a separate, weekly track, driven by the node OS auto-upgrade channel. The guardrails that make it non-disruptive are `max-surge`, PDBs, a drain timeout that matches my longest-running consumer, and a maintenance window.

```bash
# 0. pre-flight: deprecated APIs in the live cluster (beta APIs are off by default from 1.30)
kubent

# 1. what's available
az aks get-upgrades -g rg-integration -n aks-integration-prod -o table

# 2. control plane only, validate workloads against the new API server
az aks upgrade -g rg-integration -n aks-integration-prod \
  --kubernetes-version 1.34.1 --control-plane-only

# 3. node pools, one at a time, with production surge settings
az aks nodepool update -g rg-integration --cluster-name aks-integration-prod -n apppool \
  --max-surge 33% --drain-timeout 45 --node-soak-duration 5

az aks nodepool upgrade -g rg-integration --cluster-name aks-integration-prod -n apppool \
  --kubernetes-version 1.34.1
```

The defaults you should know cold, because they are the difference between a 20-minute and a 4-hour upgrade:

| Setting | Default | Production |
|---|---|---|
| `--max-surge` | **1 node** | **33%** (Microsoft's own recommendation) |
| `--max-unavailable` | **0** (and not settable on system pools) | leave at 0 unless you have no spare quota |
| `--drain-timeout` | **30 minutes** (range 5 min – 24 h) | match your longest in-flight message/batch |
| `--node-soak-duration` | **0 minutes** (max 30) | 0–5, longer just delays finding problems |

Surge costs quota: five pools of four nodes at 50% surge needs headroom for ten extra VMs *and* their IPs — which is another reason for CNI Overlay (Q70). Node OS channels are `None`, `Unmanaged`, `SecurityPatch` and `NodeImage`; **`NodeImage` is the default for new Standard clusters** and ships an AKS-tested VHD with security *and* bug fixes weekly, while `SecurityPatch` ships security-only fixes faster and often live-patches without a reimage. Cluster auto-upgrade channels are `none`, `patch`, `stable`, `rapid`, `node-image` — and setting the cluster channel to `node-image` pins the node OS channel to `NodeImage`. Pair either with a planned-maintenance window (`aksManagedAutoUpgradeSchedule` / `aksManagedNodeOSUpgradeSchedule`) of at least four hours.

**If they push back — "the upgrade stalled halfway"** — almost always a drain that cannot complete: a PDB written as `minAvailable: 3` on a 3-replica Deployment makes every eviction a violation, so the node never drains, the drain timeout expires and the upgrade stops (a subsequent `PUT` resumes it). The fix is `maxUnavailable: 1` in the PDB and enough replicas, plus `terminationGracePeriodSeconds` long enough for in-flight work — see §9 and §3 on signal handling.

---

### Q76. When would you put an integration workload on Azure Container Apps instead of AKS?
`[HARD]` — *very likely in the L2 techno-managerial round; they are testing judgement, not trivia*

> Container Apps is managed Kubernetes with the Kubernetes API taken away — KEDA, Dapr and Envoy are built in, you get revisions and traffic splitting, scale-to-zero, managed TLS ingress and event-driven Jobs, and there is no cluster, no node pool, no upgrade calendar and no CNI decision. My rule: if the workload is a stateless HTTP API or a queue/topic consumer, and I don't need cluster-level primitives, Container Apps wins on total cost of ownership — for a five-service integration layer, AKS is mostly platform work I'd be doing for its own sake. I move to AKS the moment I need the Kubernetes API itself: operators and CRDs, DaemonSets, a service mesh, StatefulSets, node-level control, or a shared multi-tenant platform with namespaces, quotas and GitOps for many teams.

**Container Apps if** — stateless HTTP APIs and adapters; event-driven consumers that should idle at zero overnight; scheduled or event-driven **Jobs** (the JD's "batch jobs using event streaming" maps onto Container Apps Jobs with a KEDA `ScaledJob`); a small team with no cluster operations budget; Dapr pub/sub or state building blocks; you want revisions and percentage traffic splitting without installing anything.

**AKS if** — you need CRDs/operators (Strimzi for Kafka, cert-manager, Argo CD/Flux, KEDA you control the version of); DaemonSets for node-level agents that a client's security policy mandates; Istio/Linkerd mTLS; StatefulSets with per-pod stable identity and volumes; GPUs, spot pools, taints, specific VM SKUs or node-level compliance controls; a request that legitimately runs longer than four minutes; one shared platform serving many teams with namespace-level isolation and quotas.

Limits that decide it, with numbers:

| | Azure Container Apps |
|---|---|
| Per-replica size (Consumption) | **0.25–4 vCPU, 0.5–8 GiB** (Dedicated D-series to 32 vCPU/128 GiB, E-series to 256 GiB, allocated per node) |
| Replicas | min default **0**, max default **10**, configurable up to **1,000** |
| HTTP scale rule | default **10** concurrent requests per replica |
| KEDA behaviour | poll **30 s**, cooldown **300 s**, scale-down stabilization **300 s**, scale-up steps 1 → 4 → 8 → 16 → 32 |
| **HTTP request timeout** | **240 seconds — hard.** A slow SOAP call or a long batch must become a Job, not a request. |
| Ingress | Envoy-managed, TLS 1.2/1.3 terminated at the edge, HTTP/1.1 + HTTP/2, gRPC, WebSocket, internal or external, max **5 extra TCP ports** |
| Kubernetes API | **Not exposed.** No `kubectl`, no CRDs, no DaemonSets. |
| Scale to zero | Consumption yes; the preview **Flexible** profile does not |

```bash
az containerapp create -g rg-integration -n orders-consumer \
  --environment cae-integration-prod \
  --image myacr.azurecr.io/orders-consumer:1.4.2 \
  --min-replicas 0 --max-replicas 30 \
  --user-assigned "$UAMI_ID" \
  --scale-rule-name sb-orders --scale-rule-type azure-servicebus \
  --scale-rule-metadata "queueName=orders-inbound" \
                        "namespace=sb-integration-prod" \
                        "messageCount=20" \
  --scale-rule-identity "$UAMI_ID"
```

That is the same KEDA scaler you would write as a `ScaledObject` on AKS (§11), minus the cluster. Note `--scale-rule-identity`: managed identity for the scaler, so no connection string ever lands in a secret.

**If they push back — "doesn't running both fragment your platform?"** — only if the paved road isn't shared. Same Terraform/Bicep module library, same ACR with the same scanning gate, same managed-identity-and-RBAC model, same Log Analytics workspace and dashboards, same pipeline template with the deploy step swapped. What must not be duplicated is the *decision*: I'd publish the rule above as the platform's guidance so teams don't relitigate it per service — which is also the honest answer to "how do you run a platform, not a project" ([System Design](08-system-design-integration.md), [CI/CD & GitOps](05-cicd-iac-and-gitops.md)).

**If they push back — "and the EY-logged HPA question in this context?"** — `[EY-logged]` *"How does HPA work in Kubernetes?"* usually gets a follow-up about what happens when there is no room for the new replica. On AKS the honest chain is HPA → pod `Pending` → cluster autoscaler adds a node (Q64, §11). On Container Apps there is no such chain to explain, because scaling replicas and scaling infrastructure are the same operation — and saying that out loud is a good way to show you understand both.


## 14. Debugging drills: the round-2 favourite

L2 stops asking *what is a Deployment* and starts asking **"a pod is in CrashLoopBackOff — walk me through what you type."** They are listening for a *sequence* with a reason attached to each command, not a list of commands. Six drills below cover ~90% of what actually happens. Memorise the sequences; the prose is there so you can say why.

**The 60-second triage you run before any drill** — every incident starts here:

```bash
NS=payments
kubectl -n $NS get pods -o wide                                  # STATUS + RESTARTS + node + AGE
kubectl -n $NS get events --sort-by=.lastTimestamp | tail -40    # what the cluster just did and why
kubectl -n $NS get deploy,rs,svc,endpointslice                   # desired vs ready vs routable
kubectl -n $NS rollout status deploy/payments-adapter --timeout=30s
kubectl top pods -n $NS --containers                             # needs metrics-server; on AKS it's there
```

`STATUS` names the *state machine position*, not the fault. `Pending` = scheduler hasn't placed it. `ContainerCreating` = placed, kubelet is pulling/mounting. `CreateContainerConfigError` = a referenced ConfigMap/Secret **key** is missing. `ErrImagePull`/`ImagePullBackOff` = registry. `CrashLoopBackOff` = it started and died, repeatedly. `OOMKilled` = the kernel killed it. `Evicted` = the node ran out of something. `Terminating` for minutes = a finalizer or a container ignoring SIGTERM.

---

### D1. `CrashLoopBackOff` — the pod restarts forever

**Symptom:** `payments-adapter-7c9f8d6b4-x2k9p   0/1   CrashLoopBackOff   7   9m`

> **Spoken answer:** CrashLoopBackOff isn't the error — it's kubelet's backoff state after the container exited repeatedly. I go straight to two things: the **last exit code** from `kubectl describe`, and `kubectl logs --previous`, because the container running right now may have produced no output yet. The exit code splits the problem in half: 137 means something SIGKILLed it — almost always the OOM killer or a liveness probe — while exit 1 means my own application raised and died, and the traceback is in the previous container's logs.

```bash
POD=payments-adapter-7c9f8d6b4-x2k9p

# 1. exit code, reason, restart count, probe config, mounted refs, and the event tail — one command
kubectl -n payments describe pod $POD

# 2. the ONLY logs that matter: the container that already died
kubectl -n payments logs $POD --previous --tail=200
kubectl -n payments logs $POD --previous --all-containers   # init + sidecars too

# 3. machine-readable version of what describe showed you
kubectl -n payments get pod $POD -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.lastState.terminated.exitCode}{"\t"}{.lastState.terminated.reason}{"\n"}{end}'

# 4. did the whole ReplicaSet do this, or just this pod? (one pod = node/data; all pods = code/config)
kubectl -n payments get pods -l app.kubernetes.io/name=payments-adapter \
  -o custom-columns='NAME:.metadata.name,NODE:.spec.nodeName,RESTARTS:.status.containerStatuses[0].restartCount'

# 5. cluster-side narrative
kubectl -n payments get events --field-selector involvedObject.name=$POD --sort-by=.lastTimestamp
```

**Read the exit code first:**

| Exit | Meaning | What to do |
|---|---|---|
| `0` | Process returned cleanly — but `restartPolicy: Always` restarts it anyway | Your entrypoint isn't a long-running server. `CMD ["python","app.py"]` where `app.py` just sets up and returns. |
| `1` | Unhandled application exception | `logs --previous` has the traceback. Usually config: missing env var, bad DSN, Pydantic `ValidationError` on settings at import time. |
| `126` | Command found but not executable | `chmod +x entrypoint.sh`, or CRLF line endings on the shebang line. |
| `127` | Command not found | Typo in `command:`, or the binary doesn't exist in a distroless/alpine base. |
| `137` | `128+9` SIGKILL | **OOMKilled**, or the liveness probe failed and kubelet killed it, or SIGTERM was ignored past `terminationGracePeriodSeconds`. |
| `139` | `128+11` SIGSEGV | Native extension mismatch — a manylinux wheel on musl (alpine), or a `grpcio`/`pyarrow` built for the wrong glibc. |
| `143` | `128+15` SIGTERM | Graceful shutdown requested — normal during a rollout, a bug if it's on loop. |

**Likely causes, ranked:**

1. **App raised at startup** (exit 1). Settings validation, a DB URL that resolves in dev and not in prod, a missing Key Vault reference. The traceback is in `--previous`.
2. **OOMKilled** (exit 137, `Reason: OOMKilled` under `Last State` in describe). Go to **D4**.
3. **Liveness probe killing a healthy slow starter.** The app needs 45 s to warm a connection pool or load an ONNX/embedding model; `livenessProbe` has `initialDelaySeconds: 10, failureThreshold: 3, periodSeconds: 10` → killed at ~40 s, forever. `describe` shows `Liveness probe failed:` events *followed by* `Killing container`. This one is invisible in logs because the app never logs an error — it was murdered mid-boot.
4. **Missing ConfigMap/Secret key.** If the *object* is missing you get `CreateContainerConfigError`, not CrashLoop — the container never runs. If the object exists but the app requires a key that isn't in it, you get exit 1. `kubectl -n payments describe pod $POD | grep -A3 Environment` and `kubectl -n payments get cm payments-adapter-config -o yaml`.
5. **Bad `command`/`args`** (126/127) — overriding the image's ENTRYPOINT in the chart and getting the path wrong.
6. **Dependency down at boot and the app calls `sys.exit(1)`** rather than retrying. Fix the app: an integration service must start and report *not ready*, not refuse to start.

**The integration-specific classic — the liveness probe that checks the database.** Someone points `livenessProbe` at `/health`, and `/health` runs `SELECT 1`. A 40-second Azure SQL failover or a Service Bus throttling blip makes the probe fail on **every pod simultaneously**. Kubelet kills all of them at once. They restart into a dependency that is still recovering, so they fail again — and a 40-second dependency blip becomes a 15-minute total outage of your own service, with a cold connection pool and a cold cache on the other side. This is a genuinely great answer to give unprompted.

> **The rule:** **liveness answers "is this process wedged and unrecoverable?" and must depend on nothing external. Readiness answers "should I get traffic this second?" and may check dependencies. Startup guards slow boots so liveness never sees a booting pod.**

```yaml
# The fix, in the golden chart so nobody can get it wrong (see §15 Q86)
startupProbe:                       # up to 120s to boot; liveness does not run until this passes
  httpGet: { path: /livez, port: http }
  periodSeconds: 5
  failureThreshold: 24
livenessProbe:                      # process-only. No DB, no broker, no HTTP call out.
  httpGet: { path: /livez, port: http }
  periodSeconds: 20
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:                     # may check dependencies — failing here removes it from Endpoints
  httpGet: { path: /readyz, port: http }
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
```

```python
# app/health.py — the split, in FastAPI
from fastapi import APIRouter, Response, status
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text

router = APIRouter()
_ready = {"warm": False}          # flipped True by the startup task when pools are built

@router.get("/livez", status_code=status.HTTP_200_OK)
async def livez() -> dict[str, str]:
    """Liveness: proves the event loop is scheduling. Touches nothing external, ever."""
    return {"status": "alive"}

@router.get("/readyz")
async def readyz(response: Response, engine: AsyncEngine) -> dict[str, object]:
    """Readiness: may check dependencies. Failing here drops the pod from the Service."""
    checks: dict[str, bool] = {"warm": _ready["warm"]}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception:
        checks["db"] = False
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"checks": checks}
```

**If they push back — "but then a broken DB means you serve traffic to a dead service"** — Yes, and that is the correct trade. With readiness on the DB, *every* pod leaves the EndpointSlice at once, the Service has zero backends, and the ingress returns 503 with no application telemetry at all — you have converted a partial failure into a total one and blinded yourself. I keep the pod in rotation, return `503` with a `Retry-After` from the handler, emit the failure as a metric, and let the circuit breaker and the client's retry policy do their job. Readiness on a shared dependency is only correct when failing readiness routes traffic *somewhere that works* — a second region behind Front Door — not when it just empties the pool.

**If they push back — "how do you stop this recurring?"** — It's a chart-level fix, not a per-service one: the golden chart hard-codes `/livez` for liveness and does not expose a value that lets a team point liveness at anything else. That is the platform answer.

---

### D2. `ImagePullBackOff` — the image never arrives

**Symptom:** `0/1  ImagePullBackOff` (or `ErrImagePull` on the first attempt — `ImagePullBackOff` is kubelet backing off after it).

> **Spoken answer:** `describe pod` prints the registry's own error string in the events, and that string alone tells me which of four things it is: the tag doesn't exist, we aren't authenticated, we're authenticated but not authorised, or we can't reach the registry at all. On AKS the authorisation case is almost always the `AcrPull` role missing on the **kubelet** managed identity — `az aks check-acr` confirms it in one command.

```bash
# 1. the registry's verbatim error is in the events
kubectl -n payments describe pod $POD | sed -n '/Events:/,$p'

# 2. what exactly are we asking for? (typos in a --set image.tag land here)
kubectl -n payments get pod $POD -o jsonpath='{range .spec.containers[*]}{.image}{"\n"}{end}'

# 3. does that tag/digest exist at all?
az acr repository show-tags -n eyintacr --repository integration/payments-adapter -o table
az acr manifest list-metadata -r eyintacr -n integration/payments-adapter --query "[].{tag:tags[0],digest:digest}" -o table

# 4. can this cluster pull from that registry? (this is the one command to remember)
az aks check-acr --name aks-int-prod --resource-group rg-int-prod --acr eyintacr.azurecr.io

# 5. non-Azure registry: is a pull secret actually attached, and is it valid?
kubectl -n payments get sa payments-adapter -o jsonpath='{.imagePullSecrets}'
kubectl -n payments get secret partner-registry -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d
```

**Error string → cause:**

| Event text | Cause | Fix |
|---|---|---|
| `manifest unknown` / `not found` | Tag/digest doesn't exist. CI pushed `1.4.2-rc3`, the chart asks for `1.4.2`. Or a retention policy garbage-collected an untagged digest you were pinning. | Fix the tag; enable a retention lock on promoted digests. |
| `unauthorized: authentication required` (401) | No credentials presented at all — no `imagePullSecrets`, or they're on the wrong ServiceAccount / wrong namespace. | Attach the secret to the SA the pod actually uses. |
| `denied` / `403 Forbidden` | Authenticated but not authorised — `AcrPull` not assigned to the kubelet identity. | `--attach-acr` or the Terraform role assignment below. |
| `dial tcp ... i/o timeout` | Network. ACR behind Private Link with no private DNS zone link, an egress NetworkPolicy, a firewall, or an HTTP proxy without the ACR REST **and** data endpoints in `noProxy`. | See **D6** and the proxy note. |
| `x509: certificate signed by unknown authority` | Corporate TLS interception; the node trust store lacks the CA. | Ship the CA bundle to the nodes (a DaemonSet or node image customisation). |

**The AKS fix.** `az aks update --attach-acr` is not magic — per Microsoft's docs it assigns the built-in **`AcrPull`** role to the **kubelet managed identity** (the agent-pool identity, *not* the cluster control-plane identity). That's why it needs Owner/User Access Administrator to run, and why in a bank you almost never run it — you declare it:

```bash
# imperative, for a lab
az aks update -n aks-int-prod -g rg-int-prod --attach-acr eyintacr
az aks update -n aks-int-prod -g rg-int-prod --detach-acr eyintacr
```

```hcl
# infra/acr_pull.tf — the platform way. This is the whole of "--attach-acr".
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}
```

**Private / partner registry (no Azure identity available):**

```bash
kubectl -n payments create secret docker-registry partner-registry \
  --docker-server=registry.partner.example.com \
  --docker-username=svc-ey-integration \
  --docker-password="$REGISTRY_PAT"

# attach to the ServiceAccount so every pod using it inherits the secret —
# better than repeating imagePullSecrets in every Deployment
kubectl -n payments patch serviceaccount payments-adapter \
  -p '{"imagePullSecrets":[{"name":"partner-registry"}]}'
```

**If they push back — "the role assignment exists and it still 403s"** — Two real causes. First, propagation: if `AcrPull` was granted to an **Entra group** and the kubelet identity was added to that group, Microsoft documents a latency issue — the token kubelet already holds doesn't carry the new group membership. The documented workaround is a bring-your-own kubelet identity that is in the group *before* the cluster is created. Second, **ABAC-enabled ACR**: for registries in "RBAC Registry + ABAC Repository Permissions" mode, `az aks --attach-acr` is explicitly unsupported and `AcrPull` is the wrong role — you assign **`Container Registry Repository Reader`** by hand.

**If they push back — "why did it work yesterday?"** — Almost always a mutable tag. Someone re-pushed `:latest` or `:1.4`, or a cleanup task pruned the digest. Promote by digest, not tag ([CI/CD & GitOps](05-cicd-iac-and-gitops.md)), and note that `imagePullPolicy` defaults to `Always` when the tag is `:latest` or absent and `IfNotPresent` otherwise — which is why a re-pushed fixed tag can be live on new nodes and stale on old ones at the same time.

---

### D3. `Pending` — the pod is never scheduled

**Symptom:** `payments-adapter-7c9f8d6b4-x2k9p   0/1   Pending   0   6m` with no node assigned.

> **Spoken answer:** Pending means the scheduler hasn't placed it, and the scheduler tells you exactly why — `describe pod` contains a line like `0/6 nodes are available: 3 Insufficient cpu, 3 node(s) had untolerated taint`. That string is the entire diagnosis; I read it, and only then do I look at the cluster autoscaler to see whether it tried to add a node and why it declined.

```bash
# 1. the scheduler's verdict, verbatim
kubectl -n payments describe pod $POD | sed -n '/Events:/,$p'

# 2. is there actually room? NOTE: scheduling is on REQUESTS, not usage
kubectl describe node aks-user-12345678-vmss000003 | sed -n '/Allocated resources/,$p'
kubectl top nodes                                     # usage — deliberately a different number
kubectl get nodes -L agentpool,topology.kubernetes.io/zone,kubernetes.azure.com/scalesetpriority

# 3. taints and labels on every node, in one line each
kubectl get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key,POOL:.metadata.labels.agentpool'

# 4. storage
kubectl -n payments get pvc
kubectl -n payments describe pvc payments-adapter-data
kubectl get storageclass

# 5. did the autoscaler try?
kubectl -n kube-system get configmap cluster-autoscaler-status -o yaml
kubectl -n kube-system logs -l app=cluster-autoscaler --tail=100 | grep -i 'scale.up\|no.scale'
```

**Ranked, by the message the scheduler prints:**

| Scheduler message | Cause | Fix |
|---|---|---|
| `Insufficient cpu` / `Insufficient memory` | Sum of **requests** on the node exceeds allocatable. A node at 5% actual CPU can still be full. | Right-size requests (**D4**), or scale the pool. |
| `node(s) didn't match Pod's node affinity/selector` | `nodeSelector: { agentpool: integration }` and no pool carries that label. Typo, or the pool was renamed. | Compare `kubectl get nodes --show-labels` with the selector. |
| `node(s) had untolerated taint {kubernetes.azure.com/scalesetpriority: spot}` | Spot node pool; workloads need a matching toleration **and** `nodeAffinity`. | Add the toleration, or target the on-demand pool. |
| `pod has unbound immediate PersistentVolumeClaims` | PVC is Pending: no StorageClass, wrong `storageClassName`, or a **zone mismatch** — an Azure zonal disk can only attach to a node in its own zone. | Use `volumeBindingMode: WaitForFirstConsumer` so the PV is created where the pod lands. |
| `node(s) didn't have free ports for the requested pod ports` | `hostPort` collision. | Drop `hostPort`; use a Service. |
| `Too many pods` | Per-node pod cap reached. On AKS this depends on the network plugin and pool config — don't quote a number, read it: `kubectl get nodes -o jsonpath='{.items[*].status.allocatable.pods}'`. | New pool with a higher `--max-pods` (it's immutable on an existing pool). |
| `didn't match pod anti-affinity rules` | `requiredDuringScheduling` anti-affinity with `topologyKey: kubernetes.io/hostname` and replicas > nodes. | Use `preferredDuringScheduling`, or add nodes. |

**When the cluster autoscaler doesn't help.** CA only scales up when it can prove a *simulated* new node of that pool's SKU would let the pod schedule. It refuses when: the pod's requests exceed the largest SKU in any eligible pool (logs `pod didn't trigger scale-up: ... Insufficient cpu`); the pool is at `--max-count`; the pod's `nodeSelector`/taints match no pool; the subscription is at its regional vCPU quota (the scale set fails and CA back-offs that pool for ~5 minutes); or the PVC pins a zone with no capacity. Its own status is the source of truth:

```bash
kubectl -n kube-system get configmap cluster-autoscaler-status -o jsonpath='{.data}' | head -60
az aks nodepool show -g rg-int-prod --cluster-name aks-int-prod -n integration \
  --query '{min:minCount,max:maxCount,count:count,auto:enableAutoScaling}'
```

**If they push back — "the pod is Pending but the node has plenty of free memory"** — Then it isn't a memory problem; it's a *requests accounting* problem or a constraint problem. Scheduling compares `sum(requests)` against `allocatable`, and `allocatable` is capacity minus kube-reserved, system-reserved and eviction thresholds — on a small AKS SKU that's a meaningful slice. Also check for a namespace `ResourceQuota` (the pod may be rejected by admission rather than scheduling — that shows on the ReplicaSet, `kubectl -n payments describe rs`) and for a `PriorityClass` that lets higher-priority pods preempt yours in a loop.

---

### D4. `OOMKilled` — the kernel killed the container

**Symptom:** `describe` shows `Last State: Terminated / Reason: OOMKilled / Exit Code: 137`.

> **Spoken answer:** Exit 137 with `Reason: OOMKilled` means the container hit its own cgroup memory limit and the kernel killed the biggest process in it. The only question that matters next is whether the limit is too low or the process leaks, and the way I tell them apart is the shape of the curve: a leak climbs monotonically over the pod's whole lifetime and gets killed on a clock, while an undersized limit gets killed within seconds of a *specific* operation — a large batch, a 20 MB SOAP envelope, a model load.

```bash
# 1. confirm it was the cgroup OOM killer, not an eviction
kubectl -n payments describe pod $POD | grep -A6 'Last State'
kubectl -n payments get pod $POD -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}'

# 2. distinguish container OOM from NODE memory pressure eviction — different fix
kubectl get events -A --field-selector reason=Evicted --sort-by=.lastTimestamp | tail
kubectl describe node aks-user-12345678-vmss000003 | grep -i 'MemoryPressure\|OutOfMemory'

# 3. what does the container actually use, right now
kubectl top pod -n payments --containers
kubectl -n payments exec -it $POD -c api -- cat /sys/fs/cgroup/memory.max        # cgroup v2
kubectl -n payments exec -it $POD -c api -- cat /sys/fs/cgroup/memory.current
kubectl -n payments exec -it $POD -c api -- cat /sys/fs/cgroup/memory.peak       # if available
# cgroup v1 nodes: /sys/fs/cgroup/memory/memory.limit_in_bytes and memory.max_usage_in_bytes

# 4. what the platform says over time — the curve is the diagnosis
#    PromQL: container_memory_working_set_bytes{namespace="payments",container="api"}
#    KQL (Container Insights) — working set per container over 24h:
#    Perf
#    | where ObjectName == "K8SContainer" and CounterName == "memoryWorkingSetBytes"
#    | where InstanceName contains "payments-adapter"
#    | summarize p50=percentile(CounterValue,50), p99=percentile(CounterValue,99)
#              by bin(TimeGenerated, 5m), InstanceName
#    | render timechart
```

| Signal | Reading |
|---|---|
| `Reason: OOMKilled` on the **container** | The container's own cgroup limit. Fix `limits.memory` or the code. |
| Pod `Reason: Evicted`, `The node was low on resource: memory` | The **node** ran out; kubelet evicted the lowest-QoS pod. Fix `requests.memory` (that's what protects you) and node sizing. |
| Killed within seconds, always at the same operation | Limit too low for one unit of work. |
| Sawtooth that climbs across hours, killed on a schedule | Real leak, or unbounded caching / an unbounded in-memory queue. |
| Only the pods on one node | That node is over-committed or has a noisy neighbour. |

**How you actually size it** (say this — most candidates hand-wave):

1. Load-test with realistic payloads (k6/Locust) for at least an hour, including your largest legitimate message, and record `container_memory_working_set_bytes` — not RSS, working set is what kubelet compares against the limit.
2. `requests.memory` = observed steady-state (~p50–p75). This is what the scheduler reserves and what protects you from node-pressure eviction.
3. `limits.memory` = p99 × 1.5, with a floor of "peak working set while processing one largest unit of work". Requests and limits equal ⇒ **Guaranteed** QoS ⇒ last to be evicted; that's what I use for anything holding in-flight financial messages.
4. **Always set `limits.memory`** — memory is incompressible, so a container with no limit takes the node down instead of itself. **Rarely set `limits.cpu`** on a latency-sensitive service — CFS throttling adds tail latency even when the node is idle; use `requests.cpu` to get your share.
5. Re-derive it from production quarterly. A limit set in year one and never revisited is how you find out about the leak.

**Python specifics worth saying:**

```python
# app/runtime.py — worker count from the CGROUP quota, not the node's CPU count.
# os.cpu_count() reports the NODE's cores; a 500m-limited container that spawns
# 32 gunicorn workers will OOM and throttle at the same time.
import os
from pathlib import Path

def cgroup_cpu_limit(default: float | None = None) -> float:
    v2 = Path("/sys/fs/cgroup/cpu.max")
    if v2.exists():
        quota, period = v2.read_text().split()
        if quota != "max":
            return int(quota) / int(period)
    v1q, v1p = Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"), Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    if v1q.exists() and v1p.exists():
        q = int(v1q.read_text())
        if q > 0:
            return q / int(v1p.read_text())
    return default if default is not None else float(os.cpu_count() or 1)

WORKERS = max(1, min(8, int(cgroup_cpu_limit(1.0) * 2) + 1))
```

Also: set `MALLOC_ARENA_MAX=2` for glibc arena bloat under threaded workers; run gunicorn/uvicorn with `--max-requests 2000 --max-requests-jitter 200` so a slow leak recycles workers instead of tripping the limit; and remember that streaming a large SOAP/XML payload with `lxml.etree.fromstring` materialises the whole tree — use `iterparse` for anything unbounded ([APIs](01-api-design-rest-soap-graphql-openapi.md)).

**If they push back — "so just raise the limit"** — Only after I know which curve I'm looking at. Raising the limit on a real leak converts a 20-minute crash cycle into a 6-hour one, which is worse: it fails at 3 a.m. instead of during the load test, and it now takes a bigger node. Raising it is the right answer when the workload legitimately needs the memory — and then I raise `requests` too, or the pod stays Burstable and gets evicted under node pressure anyway.

---

### D5. 502 / 504 through the ingress

**Symptom:** the app is `Running` and `1/1 Ready`, but callers get `502 Bad Gateway` or `504 Gateway Time-out` at the ingress.

> **Spoken answer:** The code tells you which half of the path is broken. 503 means the Service has no ready endpoints at all. 502 means the ingress reached something and got a refused or broken connection — wrong port, wrong protocol, or the backend died mid-request. 504 means it reached the right place and the backend didn't answer inside the proxy's own timeout. So I check EndpointSlices first, then curl the Service from inside the cluster to bisect ingress-vs-service, then look at the timeout ladder.

```bash
# 1. does the Service have ready backends? (503 lives here)
kubectl -n payments get endpointslice -l kubernetes.io/service-name=payments-adapter -o wide
kubectl -n payments get svc payments-adapter -o yaml | sed -n '/ports:/,/selector:/p'

# 2. does the Service selector actually match the pod labels? (silent, very common)
kubectl -n payments get svc payments-adapter -o jsonpath='{.spec.selector}{"\n"}'
kubectl -n payments get pods --show-labels -l app.kubernetes.io/name=payments-adapter

# 3. bisect: talk to the Service from inside the cluster, bypassing the ingress
kubectl -n payments run curl --rm -it --restart=Never --image=curlimages/curl:8.11.1 -- \
  curl -sS -o /dev/null -w '%{http_code} %{time_total}s\n' \
  http://payments-adapter.payments.svc.cluster.local:8080/readyz

# 4. bisect further: talk to ONE pod, bypassing the Service
kubectl -n payments port-forward pod/$POD 18080:8080 &
curl -sv http://127.0.0.1:18080/readyz

# 5. what does the ingress controller itself say?
kubectl -n payments describe ingress payments-adapter
kubectl -n ingress-nginx logs -l app.kubernetes.io/name=ingress-nginx --tail=200 \
  | grep -E ' (50[0234]) ' | tail -20
kubectl -n ingress-nginx exec deploy/ingress-nginx-controller -- \
  /nginx-ingress-controller --version
```

**Ranked, by status code:**

| Code | Cause | Check / fix |
|---|---|---|
| **503** | Zero ready endpoints. Readiness failing, or a rollout drained everything because `maxUnavailable` was too aggressive with no PDB, or the Service selector matches nothing. | `get endpointslice` shows an empty `addresses`. This is a **D1** problem wearing a 5xx costume. |
| **502** | `targetPort` names a port nothing listens on, or names a port by name that the container never declared. | `svc.spec.ports[].targetPort` must equal a `containerPort` (or its name). |
| **502** | **The app bound to `127.0.0.1`.** The single most common one for a FastAPI/Flask dev. | `uvicorn app.main:app --host 0.0.0.0 --port 8080`. `0.0.0.0`, always, in a container. |
| **502** | Protocol mismatch — backend speaks TLS or gRPC, the ingress is sending plain HTTP/1.1. | `nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"` or `"GRPC"`. |
| **502** | Backend closed the connection mid-request — a worker was OOMKilled or the keepalive idle timeout on the app is *shorter* than nginx's upstream keepalive, so nginx reuses a socket the app just closed. | Make the app's keepalive **longer** than the proxy's (`--timeout-keep-alive 75` for uvicorn against nginx's `keep-alive: 75`). |
| **504** | Backend slower than the proxy read timeout. ingress-nginx defaults: `proxy-connect-timeout` **5 s**, `proxy-read-timeout` **60 s**, `proxy-send-timeout` **60 s**. A slow ERP or SOAP call blows straight through 60 s. | Raise per-Ingress by annotation, never globally. |
| **413** | Body over `proxy-body-size`, default **`1m`**. A 5 MB SOAP envelope or a bulk NAV file fails here, not at your app. | `nginx.ingress.kubernetes.io/proxy-body-size: "16m"`. |
| **TLS errors** | Cert SAN doesn't match the host, or the `Certificate` never became Ready. | `kubectl get certificate,certificaterequest,order,challenge -A` and `kubectl -n payments describe ingress` for the `tls.secretName`. |

```yaml
# Per-ingress overrides — the only correct scope for a slow legacy backend
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payments-adapter
  namespace: payments
  annotations:
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
    nginx.ingress.kubernetes.io/proxy-next-upstream: "error timeout"   # NOT non_idempotent
spec:
  ingressClassName: nginx
  tls:
    - hosts: ["payments.int.ey.example.com"]
      secretName: payments-adapter-tls
  rules:
    - host: payments.int.ey.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: payments-adapter
                port: { number: 8080 }
```

**The timeout ladder — say this, it is the senior signal.** Client → Front Door → APIM → ingress → Service → your app → the ERP. **Each layer's timeout must be shorter than the layer above it.** If APIM gives up at 60 s while nginx is still waiting at 120 s and your app is still waiting on the ERP at 180 s, the caller retries, you now run the same non-idempotent posting twice, and no layer's logs contain the whole story. Pick the ladder deliberately — e.g. ERP 25 s, app 30 s, ingress 40 s, APIM 50 s, client 60 s — and pair it with an idempotency key ([APIs](01-api-design-rest-soap-graphql-openapi.md), [System Design](08-system-design-integration.md), [FS](12-financial-services-integration.md)).

**If they push back — "you're on AGIC/Application Gateway, not nginx"** — Same taxonomy, different knobs: the timeout lives in the HTTP setting (`appgw.ingress.kubernetes.io/request-timeout`), 502 usually means the App Gateway health probe marks the backend pool unhealthy — check the **Backend health** blade, which will say `Unhealthy` with the probe's actual response — and AGIC in the default mode routes to **pod IPs directly**, so a NetworkPolicy that blocks the App Gateway subnet produces exactly this symptom while in-cluster curl succeeds.

---

### D6. DNS failures and mysteriously slow external calls

**Symptom:** intermittent `Name or service not known` / `Temporary failure in name resolution`, or external calls to Service Bus / an ERP that are fine locally and take 200 ms extra in the cluster.

> **Spoken answer:** I confirm it from inside the pod's own network namespace with an ephemeral debug container, then check CoreDNS itself, then check the two classics: `ndots:5`, which makes every non-FQDN external lookup do three failed searches before it tries the real name, and an egress NetworkPolicy that forgot to allow UDP and TCP 53 to kube-dns — which breaks *everything* the moment the policy lands, so it correlates with a deploy, not with load.

```bash
# 1. inside the failing pod's netns, with real tools, without changing the image
kubectl -n payments debug -it $POD --image=nicolaka/netshoot:v0.13 --target=api -- bash
#   ...then, inside:
#   cat /etc/resolv.conf
#   dig +search +stats sb-int-prod.servicebus.windows.net
#   dig +noall +answer sb-int-prod.servicebus.windows.net.      # trailing dot = absolute, no search
#   nslookup payments-adapter.payments.svc.cluster.local
#   getent hosts login.microsoftonline.com
#   curl -sv --max-time 5 https://sb-int-prod.servicebus.windows.net/

# 1b. if --target isn't supported / you need the app's filesystem too
kubectl -n payments debug $POD -it --copy-to=payments-debug --share-processes --image=nicolaka/netshoot:v0.13
kubectl -n payments delete pod payments-debug        # ALWAYS clean up the copy

# 2. is CoreDNS healthy and are there enough replicas?
kubectl -n kube-system get pods -l k8s-app=kube-dns -o wide
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=200 | grep -iE 'error|SERVFAIL|i/o timeout'
kubectl -n kube-system get cm coredns coredns-custom -o yaml
kubectl -n kube-system top pods -l k8s-app=kube-dns

# 3. is a NetworkPolicy in the way?
kubectl -n payments get networkpolicy
kubectl -n payments describe networkpolicy default-deny-egress

# 4. node-level debugging when it's only one node
kubectl debug node/aks-user-12345678-vmss000003 -it --image=nicolaka/netshoot:v0.13
```

**Cause 1 — the `ndots` trap (the one they want).** Kubernetes gives every pod this `/etc/resolv.conf`:

```text
nameserver 10.0.0.10
search payments.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`ndots:5` means: *if the name has fewer than 5 dots, try each search domain first, and only then try the name as given.* `sb-int-prod.servicebus.windows.net` has 3 dots, so the resolver issues:

1. `sb-int-prod.servicebus.windows.net.payments.svc.cluster.local` → NXDOMAIN
2. `sb-int-prod.servicebus.windows.net.svc.cluster.local` → NXDOMAIN
3. `sb-int-prod.servicebus.windows.net.cluster.local` → NXDOMAIN
4. `sb-int-prod.servicebus.windows.net` → answer

Four name attempts, each typically issuing **both A and AAAA** — up to eight queries for one lookup. At 500 rps of outbound calls that is thousands of wasted CoreDNS queries per second; the symptom is p99 latency spikes and intermittent `i/o timeout` under load, never at low load. Three fixes, in order of preference:

```yaml
# (a) best: per-pod ndots. Cluster-internal short names still work; external names go direct.
spec:
  dnsConfig:
    options:
      - { name: ndots, value: "2" }
      - { name: single-request-reopen }      # glibc: don't share a socket for the A/AAAA pair
```

```python
# (b) use absolute names (trailing dot) for external hosts — zero search-domain attempts
SERVICE_BUS_FQDN = "sb-int-prod.servicebus.windows.net."
```

(c) enable **NodeLocal DNSCache** so lookups hit a per-node cache over TCP to CoreDNS instead of a UDP round trip across the cluster. And in Python, reuse one long-lived `httpx.AsyncClient` / `aiohttp.ClientSession` — a fresh client per request re-resolves DNS and re-does the TLS handshake every time, which multiplies this problem by your request rate.

**Cause 2 — NetworkPolicy blocking egress to kube-dns.** The moment you apply a `default-deny` egress policy, DNS dies for the whole namespace unless you explicitly allow it. Always ship the DNS allowance in the same PR as the deny:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: payments
spec:
  podSelector: {}
  policyTypes: [Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: payments
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system   # auto-applied label, 1.21+
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }                    # TCP 53 too — truncated responses retry over TCP
```

Forgetting **TCP 53** is the subtle version of this bug: everything works until a response exceeds 512 bytes, is truncated, and the resolver retries over TCP into a dropped packet. Symptom: only *some* hostnames fail.

**Cause 3 — CoreDNS itself.** Under-replicated CoreDNS (it's autoscaled proportionally to cluster size on AKS, which lags a sudden pod-count jump), a CoreDNS pod co-scheduled on a saturated node, or an upstream problem — CoreDNS forwards anything it doesn't own via `forward . /etc/resolv.conf` to the node's resolver, so a broken Private DNS Zone link for `privatelink.servicebus.windows.net` shows up as *your* DNS failing. Check the Corefile, then resolve the same name from the node.

**If they push back — "how do you prove it's DNS and not the network?"** — Split the two explicitly: `getent hosts <name>` exercises resolution only; `curl --resolve <name>:443:<ip> https://<name>/` exercises connectivity with resolution bypassed. If `getent` is slow/failing and `--resolve` works, it's DNS. If both fail, it's routing, NSG, private endpoint, or a firewall — go look at Azure, not CoreDNS.

**If they push back — "the pod has no shell, it's distroless"** — that's exactly why `kubectl debug` exists. `kubectl debug -it $POD --image=nicolaka/netshoot --target=api` attaches an **ephemeral container** to the *running* pod, sharing its network namespace (and, with `--target`, its process namespace), without a restart and without adding tools to your production image. This is the single most useful modern kubectl command and very few candidates mention it.

---
## 15. Helm

JD responsibility 7 names Helm explicitly, next to GitOps. For a **platform** engineer Helm is not "the thing that installs my app" — it is the artefact through which the platform team ships opinions: probes that can't be pointed at a database, security contexts that can't be turned off, KEDA scaling and OpenTelemetry already wired. §15 Q86 is the answer that separates a Helm *user* from a Helm *owner*. Helm-under-ArgoCD, the deploy pipeline and chart scanning live in [CI/CD & GitOps](05-cicd-iac-and-gitops.md); this section is the mechanism.

> **Version note for 2026:** Helm 4.0 shipped in late 2025; **Helm 3 bug fixes end 8 July 2026 and security fixes end 11 November 2026**, so "when are you moving to Helm 4?" is a live question. Helm 4 needs no release migration — the release storage format is identical and Chart `apiVersion: v2` charts work unchanged — but new releases use **server-side apply** (releases created under Helm 3 stay on client-side apply), Helm 3 **plugins must be ported**, and `--wait` changed shape (Q82). Know this; most candidates won't.

---

### Q77. Walk me through the structure of a Helm chart.
`[EASY]` `[NEAR-CERTAIN OPENER]`

> **Answer:** A chart is a directory with a `Chart.yaml` describing the chart, a `values.yaml` of defaults, a `templates/` directory of Go-templated Kubernetes manifests, and a `charts/` directory holding dependencies. Helm renders `templates/` against the merged values to produce plain YAML, then applies it to the cluster and records the result as a **release** — a versioned, rollback-able object stored in a Secret in the target namespace. The mental model I use is that a chart is `pydantic` for YAML: a schema, a set of values, and a render step.

```text
charts/integration-service/
├── Chart.yaml            # name, version, appVersion, dependencies, kubeVersion  (REQUIRED)
├── Chart.lock            # resolved dependency digests — commit this
├── values.yaml           # documented defaults for every value the chart supports
├── values.schema.json    # JSON Schema; `helm lint`/`install` validate values against it
├── README.md             # generated by helm-docs from values.yaml comments
├── .helmignore           # like .dockerignore — keeps junk out of the packaged .tgz
├── charts/               # subcharts, populated by `helm dependency update`
├── crds/                 # CRDs installed BEFORE templates, never templated, never upgraded
└── templates/
    ├── _helpers.tpl      # named templates; files starting with _ render no manifest
    ├── NOTES.txt         # templated post-install message shown to the operator
    ├── deployment.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── pdb.yaml
    ├── networkpolicy.yaml
    └── tests/
        └── test-connection.yaml   # annotated helm.sh/hook: test — run by `helm test`
```

```yaml
# Chart.yaml — only apiVersion, name and version are REQUIRED
apiVersion: v2                     # v2 = Helm 3/4. v1 = Helm 2-era; dependencies lived in requirements.yaml
name: integration-service
description: EY DE golden chart for an integration service (HTTP adapter and/or queue consumer)
type: application                  # application | library
version: 3.4.1                     # SemVer 2, the CHART's version — bump on any chart change
appVersion: "1.4.2"                # the APP's version — quoted, need not be SemVer
kubeVersion: ">=1.29.0-0"          # install fails on an older API server
home: https://tech.ey.example.com/platform/integration-service
maintainers:
  - name: DE Integration Platform Guild
    email: de-integration-platform@ey.example.com
annotations:
  artifacthub.io/changes: |
    - kind: security
      description: readOnlyRootFilesystem now defaults to true
```

Two fields people confuse constantly: **`version` is the chart's version, `appVersion` is the software's version.** Fixing a typo in a template bumps `version` and not `appVersion`. Shipping a new image bumps `appVersion` (and `version`, because the chart changed).

**If they push back — "what's the `crds/` directory for?"** — CRDs in `crds/` are installed before any template renders and are **never templated and never upgraded or deleted by Helm** — deliberately, because deleting a CRD deletes every custom resource in the cluster. So chart-managed CRD upgrades are a manual `kubectl apply` step, which is precisely why platform teams install CRD-bearing components (KEDA, cert-manager, Gateway API) as their own ArgoCD applications rather than as subcharts of an app chart.

---

### Q78. `values.yaml`, `-f`, `--set` — what wins?
`[MEDIUM]` `[HIGH FREQUENCY]`

> **Answer:** Least specific to most specific: the chart's own `values.yaml`, then a parent chart's values overriding a subchart's, then user-supplied `-f` files applied left to right so the **right-most file wins**, then `--set` on top of everything. The trap that actually bites in production is that `helm upgrade` does **not** carry forward the values you passed last time — it computes values from the chart defaults plus what you pass on *this* invocation — so a pipeline that deploys with a bare `--set image.digest=...` silently reverts every other override.

**Precedence, most specific last:**

1. The chart's `values.yaml`
2. A **parent** chart's `values.yaml` (parent beats subchart; `global:` flows down to every subchart)
3. `-f/--values` files, merged **left to right — the last file specified wins**
4. `--set` / `--set-json` / `--set-string` / `--set-file` / `--set-literal`

Merging is a **deep merge for maps and a wholesale replace for lists** — you cannot append one element to a list from a values file. That's why well-designed charts take `extraEnv`, `extraVolumes`, `tolerations` as full lists the caller replaces, and why a chart with a list of "default" sidecars is a chart nobody can extend.

```bash
# left to right; prod.yaml beats base.yaml, --set beats both
helm upgrade --install payments-adapter oci://eyintacr.azurecr.io/helm/integration-service \
  --version 3.4.1 \
  --namespace payments \
  -f values/base.yaml \
  -f values/prod.yaml \
  --set image.digest="sha256:8c1f...ab" \
  --set-string podAnnotations."deploy\.ey\.com/build"="20260826.4" \
  --set-file config.certificateChain=./certs/erp-chain.pem \
  --set-json 'resources={"requests":{"cpu":"200m","memory":"512Mi"},"limits":{"memory":"1Gi"}}'
```

Note the escaping: `--set` treats `.` as a path separator and `,` as a separator between pairs, so any key or value containing them must be backslash-escaped. `--set-string` forces a string — without it `--set image.tag=1.40` becomes the float `1.4` and you deploy the wrong image. That class of bug is the reason CI should use `-f` files, not long `--set` chains.

**The upgrade-values trap and its three flags:**

| Flag | Behaviour |
|---|---|
| *(none)* | Chart defaults + the values supplied on this invocation. Previously supplied overrides are **gone**. |
| `--reuse-values` | Merge the previous release's values, then layer this invocation's `-f`/`--set` on top. Breaks when a new chart version introduces a value the stored values don't have. |
| `--reset-values` | Force chart defaults, ignore everything stored. |
| `--reset-then-reuse-values` | Helm **3.14+**: reset to the *new* chart's defaults, then re-apply the previously stored user overrides, then this invocation's flags. Usually what people actually meant. `--reset-values`/`--reuse-values` take precedence over it. |

**The platform rule:** CI always passes the **complete** `-f values/<env>.yaml` from Git on every deploy, and uses `--set` only for the image digest and build metadata. Then the release is a pure function of the repo, `--reuse-values` never enters the conversation, and GitOps drift detection has something true to compare against.

**If they push back — "how do you stop a team passing nonsense values?"** — `values.schema.json`. Helm validates values against it on `install`, `upgrade`, `lint` and `template`, so a bad value fails at authoring time with a readable message instead of producing YAML the API server rejects:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["image", "platform"],
  "properties": {
    "image": {
      "type": "object",
      "required": ["repository", "digest"],
      "properties": {
        "repository": { "type": "string", "pattern": "^eyintacr\\.azurecr\\.io/" },
        "digest":     { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
        "tag":        { "type": "string", "not": { "const": "latest" } }
      }
    },
    "platform": {
      "type": "object",
      "required": ["costCentre", "dataClassification"],
      "properties": {
        "costCentre":         { "type": "string", "pattern": "^CC-[0-9]{6}$" },
        "dataClassification": { "enum": ["public", "internal", "confidential", "restricted"] }
      }
    },
    "replicaCount": { "type": "integer", "minimum": 2 }
  }
}
```

That schema enforces four platform policies — images only from our ACR, pinned by digest, never `:latest`, always tagged with a cost centre and a data classification, never a single replica in a chart used for prod — before a single manifest is rendered.

---

### Q79. What is the templating language, and what are the idioms you actually use?
`[MEDIUM]`

> **Answer:** Go's `text/template` plus the **sprig** function library, plus a handful Helm adds itself — `include`, `required`, `tpl`, `lookup`, `toYaml`, `.Files`. The three idioms that carry 90% of real charts are `toYaml | nindent` for injecting an arbitrary values block into a manifest, `required` for making a value mandatory with a human error message, and whitespace control with `{{-` and `-}}` so the rendered YAML is still valid YAML.

```yaml
# templates/deployment.yaml — the idioms, in context
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "int.fullname" . }}
  labels: {{- include "int.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels: {{- include "int.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        # roll pods automatically when the ConfigMap changes — Helm will not do this for you
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels: {{- include "int.labels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "int.serviceAccountName" . }}
      securityContext: {{- include "int.podSecurityContext" . | nindent 8 }}
      containers:
        - name: api
          image: "{{ .Values.image.repository }}@{{ required "image.digest is mandatory — promote by digest, never by tag" .Values.image.digest }}"
          imagePullPolicy: {{ .Values.image.pullPolicy | default "IfNotPresent" }}
          ports:
            - { name: http, containerPort: {{ .Values.service.targetPort | int }}, protocol: TCP }
          env:
            - name: OTEL_SERVICE_NAME
              value: {{ include "int.fullname" . | quote }}
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: {{ printf "service.namespace=%s,deployment.environment=%s" .Release.Namespace .Values.platform.environment | quote }}
            {{- range $k, $v := .Values.env }}
            - name: {{ $k }}
              value: {{ $v | quote }}
            {{- end }}
            {{- with .Values.extraEnv }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
          resources: {{- toYaml .Values.resources | nindent 12 }}
```

| Idiom | What it does / why |
|---|---|
| `{{- ` / ` -}}` | Chomp whitespace **left** / **right** of the action. Without them you get blank lines and broken indentation. |
| `nindent N` | `indent N` plus a leading newline. Correct after `key:` — `toYaml \| indent` on the same line produces invalid YAML. |
| `toYaml .Values.resources` | Serialise an arbitrary values subtree as YAML — how a chart accepts a block it doesn't model field by field. |
| `include "name" .` | Call a named template **and return a string**, so it can be piped. `template` is a statement and cannot be piped — that's why real charts use `include` everywhere. |
| `required "msg" .Values.x` | Fail the render with `msg` if `x` is null/empty. The way you make a value mandatory. |
| `default "v" .Values.x` | Fallback. Note `default` treats `false` and `0` as empty — use `if hasKey` for booleans. |
| `quote` / `squote` | Force a string. `enabled: {{ .Values.on }}` renders `yes` → YAML 1.1 boolean chaos; `\| quote` fixes it. |
| `tpl (.Values.raw) .` | Render a string *from values* as a template — lets a values file contain `{{ .Release.Name }}`. |
| `lookup "v1" "Secret" ns name` | Read live cluster state during render (empty on `helm template`/dry-run — never make correctness depend on it). |
| `.Files.Get "config/erp.xml"` | Embed a non-template file from the chart, e.g. a WSDL or an XSLT into a ConfigMap. |
| `sha256sum`, `b64enc`, `trunc 63`, `trimSuffix "-"` | sprig. `trunc 63 \| trimSuffix "-"` is mandatory on names — 63 is the label/name limit and truncation can leave a trailing dash, which is invalid. |
| `genSignedCert`, `randAlphaNum` | sprig crypto/random — **avoid**: they regenerate on every upgrade and silently rotate your secret. Use `lookup` to preserve, or cert-manager/Key Vault. |

**If they push back — "why does my `checksum/config` annotation matter?"** — Helm updates a ConfigMap in place; nothing about that restarts the pods consuming it, so a config change appears to deploy successfully and changes nothing. Hashing the rendered ConfigMap into a pod annotation changes the pod template, which triggers a rolling update. Every serious chart has that line, and its absence is a great thing to spot in a review.

---

### Q80. What is `_helpers.tpl` and why `include` rather than `template`?
`[MEDIUM]`

> **Answer:** Any file in `templates/` whose name starts with an underscore renders no manifest, so `_helpers.tpl` is where named templates live — `define`/`end` blocks for names, label sets, security contexts, anything repeated. You call them with `include` rather than `template` because `include` **returns a string** and can therefore be piped into `nindent`, `sha256sum` or `quote`; `template` is a statement that writes directly to output and cannot be piped, which makes correct indentation impossible.

```yaml
{{/* templates/_helpers.tpl */}}

{{/*
Chart name, overridable, truncated to the 63-char DNS label limit.
trimSuffix "-" because truncation can leave a trailing dash, which is invalid.
*/}}
{{- define "int.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "int.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Selector labels: MUST be a stable subset. Never include version here — the selector
     is immutable on apps/v1 and a version label in it orphans every ReplicaSet. */}}
{{- define "int.selectorLabels" -}}
app.kubernetes.io/name: {{ include "int.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "int.labels" -}}
{{ include "int.selectorLabels" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/version: {{ .Chart.AppVersion | default .Chart.Version | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ .Values.platform.domain | default "integration" }}
ey.com/cost-centre: {{ required "platform.costCentre is mandatory — it drives chargeback and the Azure Policy tag check" .Values.platform.costCentre | quote }}
ey.com/data-classification: {{ .Values.platform.dataClassification | default "internal" | quote }}
{{- end -}}

{{- define "int.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "int.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
```

Two scoping rules that trip people up. First, **inside `define` the dot is whatever the caller passed**, not the root — `include "int.labels" .` passes the current scope, and if you're inside a `range` or a `with`, `.` is the loop item and `.Values` no longer exists. Use `$` for the root context: `include "int.labels" $`. Second, **named templates share one global namespace across the chart and every subchart**, which is why every helper is prefixed (`int.`) — two charts both defining `fullname` will silently collide and the last one loaded wins.

**If they push back — "when do helpers become a library chart?"** — the moment a second chart wants them. See Q86.

---

### Q81. What are the built-in objects?
`[MEDIUM]`

> **Answer:** `.Values` is the merged values tree, `.Release` describes this install (`.Name`, `.Namespace`, `.Revision`, `.IsInstall`, `.IsUpgrade`, `.Service`), `.Chart` is the parsed `Chart.yaml` (`.Name`, `.Version`, `.AppVersion`), and `.Capabilities` describes the target cluster — `.KubeVersion` and `.APIVersions.Has` — which is how a chart supports two Kubernetes versions from one template. `.Files`, `.Template` and `.Subcharts` round it out.

| Object | Key fields | Typical use |
|---|---|---|
| `.Values` | the merged tree | everything |
| `.Release` | `Name`, `Namespace`, `Revision`, `IsInstall`, `IsUpgrade`, `Service` | naming, `IsInstall` guards on hooks, `Revision` in annotations |
| `.Chart` | `Name`, `Version`, `AppVersion`, `Annotations` | labels, provenance |
| `.Capabilities` | `KubeVersion`, `KubeVersion.Minor`, `APIVersions.Has "..."`, `HelmVersion` | conditional API versions |
| `.Files` | `Get`, `GetBytes`, `Glob`, `AsConfig`, `AsSecrets`, `Lines` | embedding a WSDL/XSLT/`logging.yaml` into a ConfigMap |
| `.Template` | `Name`, `BasePath` | the `checksum/config` idiom in Q79 |
| `.Subcharts` | subchart contexts by name | rare; usually a smell |

```yaml
{{- if .Capabilities.APIVersions.Has "autoscaling/v2" }}
apiVersion: autoscaling/v2
{{- else }}
apiVersion: autoscaling/v2beta2
{{- end }}
kind: HorizontalPodAutoscaler
---
{{- if .Capabilities.APIVersions.Has "policy/v1/PodDisruptionBudget" }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "int.fullname" . }}
spec:
  minAvailable: {{ .Values.pdb.minAvailable | default 1 }}
  selector:
    matchLabels: {{- include "int.selectorLabels" . | nindent 6 }}
{{- end }}
```

```yaml
# templates/configmap.yaml — .Files for a legacy contract shipped inside the chart
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "int.fullname" . }}-contracts
data:
{{ (.Files.Glob "contracts/*.{wsdl,xsd,xslt}").AsConfig | indent 2 }}
```

**If they push back — "is `.Capabilities` reliable under `helm template`?"** — No, and that matters. `helm template` runs with no cluster connection, so `.Capabilities.APIVersions` contains only Helm's built-in default list unless you pass `--api-versions` / `--kube-version` explicitly. Same for `lookup`, which returns empty. So a CI job that renders and scans charts must pass `--kube-version 1.31 --api-versions autoscaling/v2 --api-versions keda.sh/v1alpha1`, or it validates a manifest nobody will ever deploy. ArgoCD has the same issue and exposes `spec.source.helm.apiVersions` for it.

---

### Q82. What does `helm upgrade --install --atomic --wait --timeout` actually do, and why does `--atomic` matter?
`[MEDIUM]` `[HIGH VALUE — this is the deploy command they'll ask about]`

> **Answer:** `--install` makes the command idempotent — it installs if the release doesn't exist, upgrades if it does — so the same line works in CI on first deploy and on the thousandth. `--wait` makes Helm block until the resources report ready instead of returning the moment the API server accepts the manifests. And `--atomic` is the one that matters: it implies `--wait`, and if the release doesn't become ready inside `--timeout`, Helm automatically rolls back to the previous revision. Without it, a failed deploy leaves you half-upgraded with a green pipeline, because `kubectl apply` succeeding says nothing about whether the pods started.

```bash
helm upgrade --install payments-adapter \
  oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
  --namespace payments --create-namespace \
  -f values/base.yaml -f values/prod.yaml \
  --set image.digest="$IMAGE_DIGEST" \
  --atomic \
  --timeout 8m \
  --cleanup-on-fail \
  --history-max 20 \
  --wait-for-jobs
```

| Flag | Effect | Default |
|---|---|---|
| `--install` | upgrade-or-install; idempotent | off |
| `--wait` | block until resources are ready, up to `--timeout` | off in Helm 3 (see the version note below) |
| `--wait-for-jobs` | also wait for `Job`s to complete — needed if a hook runs a migration | off |
| `--atomic` | on failure, roll back to the previous revision. **Sets `--wait` automatically.** | off |
| `--timeout` | time to wait for any individual Kubernetes operation | **`5m0s`** |
| `--cleanup-on-fail` | delete resources newly created by a failed upgrade | off |
| `--history-max` | revisions retained per release; `0` = unlimited | **`10`** |
| `--dry-run` | `none` \| `client` \| `server` — `server` sends it to the API server for real admission/validation | **`none`** |
| `--force` | replace rather than patch (delete + recreate). Causes downtime; last resort for immutable-field errors. | off |

**Why `--atomic` is non-negotiable in a pipeline.** Without it the sequence is: Helm applies the new manifests, the API server accepts them, Helm exits 0, the pipeline goes green — and then the new pods CrashLoopBackOff. The Deployment's rolling update stalls with `maxUnavailable` old pods gone, you're serving at reduced capacity, and nobody knows because the deploy "succeeded". With `--atomic --timeout 8m`, Helm waits, sees the rollout never reaches ready, rolls back to revision N-1, and exits non-zero. The pipeline fails, the previous version is serving, and the on-call engineer reads a real error. **One flag converts a silent partial outage into a clean automatic recovery.**

Three caveats to state before they raise them:

- `--atomic` needs a `--timeout` **longer than your slowest legitimate rollout** — `maxSurge`/`maxUnavailable` × `startupProbe` budget × replicas. Set it too short and you roll back healthy deploys. 5 minutes (the default) is often too short for a 20-replica service with a 2-minute startup probe.
- The rollback is itself a Helm operation that can fail, most often on immutable fields. `--cleanup-on-fail` reduces the debris.
- **`--atomic` does not undo side effects.** If a `pre-upgrade` hook already ran a forward-only database migration, rolling the manifests back leaves the old code against the new schema. That is why migrations must be backwards-compatible expand/contract, never destructive in the same release ([System Design](08-system-design-integration.md)).

> **Helm 4 note:** `--wait` became a strategy flag. `--wait` alone now selects **`watcher`**, which tracks readiness with **kstatus** — the same library Flux and Argo use — and the default when the flag is omitted is **`hookOnly`**, which reproduces Helm 3's no-`--wait` behaviour so existing pipelines keep working. `legacy` gives the exact old implementation. If you inherit a pipeline and upgrade the Helm binary, this and the plugin change are the two things to check.

**If they push back — "isn't ArgoCD doing this for you?"** — Under GitOps you generally don't run `helm upgrade` at all: Argo runs `helm template` itself and applies the output, so `--atomic` has no meaning. The equivalents are `syncPolicy.retry`, `selfHeal`, and a **sync window plus a health check**; automatic rollback is `argocd app rollback` or, better, reverting the Git commit — because in GitOps Git is the rollback mechanism. Details in [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

---

### Q83. Where does Helm keep release state, and how do you roll back?
`[MEDIUM]` `[EY-adjacent — pairs with their release-management questions]`

> **Answer:** Helm 3 has no Tiller — release state lives in the cluster as a **Secret per revision in the release's namespace**, named `sh.helm.release.v1.<release>.v<n>`, containing a gzipped, base64-encoded record of the rendered manifests plus the supplied values. `helm history` lists the revisions and `helm rollback <release> <revision>` re-applies a stored one as a *new, higher* revision — it never rewrites history.

```bash
helm -n payments list -a                          # -a includes failed/pending releases
helm -n payments history payments-adapter
# REVISION  UPDATED       STATUS      CHART                      APP VERSION  DESCRIPTION
# 12        2026-08-24..  superseded  integration-service-3.4.0  1.4.1        Upgrade complete
# 13        2026-08-26..  failed      integration-service-3.4.1  1.4.2        Upgrade "payments-adapter" failed: timed out
# 14        2026-08-26..  deployed    integration-service-3.4.0  1.4.1        Rollback to 12

helm -n payments get values   payments-adapter --revision 13     # exactly what was passed
helm -n payments get values   payments-adapter --revision 13 --all  # incl. chart defaults
helm -n payments get manifest payments-adapter --revision 13     # exactly what was applied
helm -n payments get notes    payments-adapter
helm -n payments get hooks    payments-adapter

helm -n payments rollback payments-adapter 12 --wait --timeout 8m
helm -n payments status payments-adapter --show-resources

kubectl -n payments get secret -l owner=helm,name=payments-adapter
```

Practical consequences to mention:

- **The state is namespaced and in-cluster.** Delete the namespace and you delete the release history; a DR plan that only backs up Git still needs the Secrets, or a documented "reinstall from Git" runbook — which in GitOps you have by definition.
- **`--history-max` defaults to 10** and old revisions are pruned. Rolling back to a revision from six months ago is not possible; rolling back by re-deploying the chart version from Git always is. That's the reliable path.
- **A `failed` release is still the current revision.** A subsequent `helm upgrade` may refuse with `another operation (install/upgrade/rollback) is in progress` if a previous run was killed mid-flight — the release is stuck `pending-upgrade`. The fix is `helm rollback <release>` to the last good revision, and if the Secret itself is wedged, delete the `pending` revision Secret and re-run. Know this; it happens to every pipeline eventually.
- **Rollback restores manifests, not data.** Same caveat as Q82.

**If they push back — "how do you know what changed before you upgrade?"** — the `helm-diff` plugin, and it belongs in the pipeline as a manual-approval artefact for prod:

```bash
helm plugin install https://github.com/databus23/helm-diff
helm -n payments diff upgrade payments-adapter \
  oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1 \
  -f values/prod.yaml --set image.digest="$IMAGE_DIGEST" \
  --context 3 --detailed-exitcode      # exit 2 = there is a diff
```

`--detailed-exitcode` returning 2 is how you gate: no diff, skip the deploy; diff, post it to the change ticket and require approval. Note that Helm 3 plugins need porting for Helm 4.

---
### Q84. Explain Helm hooks and hook weights.
`[MEDIUM]`

> **Answer:** A hook is an ordinary Kubernetes manifest in `templates/` carrying the `helm.sh/hook` annotation, which takes it out of the normal release flow and runs it at a defined point instead — `pre-install`, `post-upgrade`, `pre-rollback` and so on. Helm applies all hooks for a phase, waits for them to reach a ready/complete state, then continues. Ordering inside a phase comes from `helm.sh/hook-weight`, a **string** integer sorted **ascending**, defaulting to **0**, so negative weights run first.

**The nine hooks:** `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `post-delete`, `pre-rollback`, `post-rollback`, `test`.

**`helm.sh/hook-delete-policy`** — three values: `before-hook-creation` (**the default**: delete the previous hook resource before creating the new one), `hook-succeeded`, `hook-failed`. You almost always want `hook-succeeded,hook-failed` on a Job so successful runs clean up but a failure leaves the pod behind for you to read the logs from.

```yaml
# templates/hooks/db-migrate.yaml — expand/contract schema migration before the new code lands
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "int.fullname" . }}-migrate-{{ .Release.Revision }}
  labels: {{- include "int.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"                       # STRING. Lower runs first.
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 1
  activeDeadlineSeconds: 900
  template:
    metadata:
      labels: {{- include "int.selectorLabels" . | nindent 8 }}
    spec:
      restartPolicy: Never
      serviceAccountName: {{ include "int.serviceAccountName" . }}
      securityContext: {{- include "int.podSecurityContext" . | nindent 8 }}
      containers:
        - name: migrate
          image: "{{ .Values.image.repository }}@{{ .Values.image.digest }}"
          command: ["alembic", "upgrade", "head"]
          securityContext: {{- include "int.containerSecurityContext" . | nindent 12 }}
          envFrom:
            - secretRef: { name: {{ include "int.fullname" . }}-db }
          resources:
            requests: { cpu: 100m, memory: 256Mi }
            limits:   { memory: 512Mi }
---
# templates/tests/test-connection.yaml — run by `helm test <release>`, not by install
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "int.fullname" . }}-smoke"
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  containers:
    - name: smoke
      image: curlimages/curl:8.11.1
      args:
        - "-sSf"
        - "--max-time"
        - "10"
        - "http://{{ include "int.fullname" . }}:{{ .Values.service.port }}/readyz"
```

**Three things people get wrong, and stating them is the senior signal:**

1. **Hook resources are not tracked as part of the release.** Helm's docs are explicit: what a hook creates is not managed by the release, so `helm uninstall` will not remove it unless a delete policy or a `ttlSecondsAfterFinished` handles it. Orphaned migration Jobs accumulating in a namespace for two years is a real thing you find in client clusters.
2. **`--wait` on the release does not wait for hooks by default** — you need `--wait-for-jobs` if a hook Job must complete before Helm proceeds past the phase for *your* readiness accounting.
3. **A hook Job's name must change per revision or `before-hook-creation` fights an immutable `Job.spec`.** Including `{{ .Release.Revision }}` in the name (as above) is the simplest fix; a `generateName`-style hash also works.

**If they push back — "why not just run the migration in an initContainer?"** — Because an initContainer runs **once per pod**, so with 6 replicas you get 6 concurrent `alembic upgrade head` runs racing for the same advisory lock, and it runs again on every pod restart and every scale-up. A `pre-upgrade` hook runs **once per release**, which is the actual semantic you want. The initContainer pattern is right for *waiting* on a dependency, not for *changing* one.

**If they push back — "how do hooks work under ArgoCD?"** — Argo does not execute Helm hooks as Helm would; it converts the common ones into its own **sync phases**, mapping `pre-install`/`pre-upgrade` to `PreSync`, `post-install`/`post-upgrade` to `PostSync`, and `test` to `argocd.argoproj.io/hook: Skip` unless you say otherwise. For a chart that must work both ways, the safe pattern is to annotate with **both** `helm.sh/hook` and `argocd.argoproj.io/hook`.

---

### Q85. Dependencies, subcharts, `condition`, `tags`, `alias` and `global`.
`[MEDIUM]`

> **Answer:** Dependencies are declared in `Chart.yaml` and materialised into `charts/` by `helm dependency update`, which also writes `Chart.lock` with resolved versions — commit the lock, not the `.tgz`. `condition` switches a subchart on or off from a boolean values path; `tags` switch a **group** of subcharts together; `alias` lets you include the same chart twice under different names with different values; and `global:` is the one values namespace that flows down into every subchart.

```yaml
# Chart.yaml
dependencies:
  - name: integration-lib                      # the golden library chart — always on
    version: "2.1.0"
    repository: "oci://eyintacr.azurecr.io/helm"

  - name: keda-scaledobjects
    version: "1.2.0"
    repository: "oci://eyintacr.azurecr.io/helm"
    condition: scaling.keda.enabled            # a boolean path in THIS chart's values
    tags: [autoscaling]

  - name: redis
    alias: idempotency-store                   # same chart, two instances, different values
    version: "20.6.2"
    repository: "oci://eyintacr.azurecr.io/helm-mirror"   # mirrored into our ACR, not upstream
    condition: idempotencyStore.enabled

  - name: common-observability
    version: "1.0.4"
    repository: "oci://eyintacr.azurecr.io/helm"
    tags: [observability]
    import-values:
      - child:  otel.collectorEndpoint         # child-parent form: lift a child value up
        parent: otel.endpoint
```

```yaml
# values.yaml — how the caller drives all of it
global:                                        # visible as .Values.global.* in EVERY subchart
  imageRegistry: eyintacr.azurecr.io
  environment: prod
  otelCollector: otel-collector.observability.svc.cluster.local:4317

tags:                                          # switch whole groups at once
  autoscaling: true
  observability: true

scaling:
  keda:
    enabled: true

idempotencyStore:
  enabled: true

idempotency-store:                             # NOTE: keyed by the ALIAS, not by "redis"
  architecture: standalone
  auth:
    existingSecret: idempotency-redis
```

Rules worth stating precisely:

- **A subchart's values are scoped under the subchart's name (or alias) in the parent's values**, and the parent's values win over the subchart's own `values.yaml`. Inside the subchart the prefix disappears — the subchart sees `.Values.architecture`, not `.Values.idempotency-store.architecture`.
- **Globals flow down only.** A subchart cannot write into the parent's values; a parent's `global` beats a subchart's `global`.
- **`condition` beats `tags`.** If a chart has both and the condition path exists, the condition decides; the condition is checked first and `tags` only apply when no valid condition path is present. `tags` are OR — any true tag enables the chart.
- **`import-values`** comes in two forms: the `exports` form (`import-values: ["data"]`, pulling from the child's `exports.data` block) and the `child`/`parent` form above, which maps an arbitrary child path onto a parent path.
- `helm dependency update` refreshes `charts/` and `Chart.lock`; `helm dependency build` installs exactly what the lock pins. **CI must use `build`**, or a dependency drifts between your test render and your prod deploy.

**If they push back — "umbrella chart of ten microservices: good idea?"** — No. It couples ten independent release cadences into one, so any deploy of service C is a deploy of A through J, one bad template fails the whole umbrella, and the blast radius of a rollback is ten services. Umbrella charts are right for *one deployable unit with its own dependencies* — a service plus its Redis plus its ScaledObject. Ten microservices are ten releases, orchestrated by ten ArgoCD Applications, generated from one ApplicationSet ([CI/CD & GitOps](05-cicd-iac-and-gitops.md)).

---

### Q86. What is a library chart — and how would you design a golden chart for a platform team?
`[HARD]` `[THE PLATFORM QUESTION IN THIS SECTION — prepare this one properly]`

> **Answer:** A library chart is a chart with `type: library`: it renders no resources of its own and cannot be installed, it only exports named templates for other charts to `include`. That's the mechanism behind what I'd actually build for EY — a **golden chart** the platform team owns that encodes the probe split, resource defaults, security context, KEDA scaling and OpenTelemetry wiring, so onboarding a new integration service is about twenty lines of values instead of a new architecture. The point isn't reuse for its own sake — it's that the compliant configuration becomes the *default*, and the non-compliant one becomes hard to express.

**The shape:**

```text
platform-charts/
├── integration-lib/                 # type: library — the opinions
│   ├── Chart.yaml
│   └── templates/
│       ├── _labels.tpl
│       ├── _security.tpl
│       ├── _probes.tpl
│       ├── _observability.tpl
│       ├── _deployment.tpl          # a whole Deployment as one named template
│       └── _scaledobject.tpl
└── integration-service/             # type: application — the thin wrapper teams install
    ├── Chart.yaml                   # depends on integration-lib
    ├── values.yaml                  # documented defaults
    ├── values.schema.json           # the guardrails from Q78
    └── templates/
        ├── deployment.yaml          # {{- include "int.deployment" . -}}
        ├── service.yaml
        ├── serviceaccount.yaml
        ├── scaledobject.yaml
        ├── pdb.yaml
        └── networkpolicy.yaml
```

```yaml
# integration-lib/Chart.yaml
apiVersion: v2
name: integration-lib
description: EY DE integration platform library — probes, security context, labels, KEDA, OTel
type: library                        # cannot be installed; renders nothing on its own
version: 2.1.0
```

```yaml
{{/* integration-lib/templates/_security.tpl — not overridable by design */}}
{{- define "int.podSecurityContext" -}}
runAsNonRoot: true
runAsUser: 10001
runAsGroup: 10001
fsGroup: 10001
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "int.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
privileged: false
capabilities:
  drop: ["ALL"]
{{- end -}}
```

```yaml
{{/*
integration-lib/templates/_probes.tpl
The D1 lesson, encoded. /livez is hard-coded for liveness: there is deliberately NO value
that lets a team point liveness at a dependency.
*/}}
{{- define "int.probes" -}}
startupProbe:
  httpGet:
    path: /livez
    port: http
  periodSeconds: 5
  failureThreshold: {{ div (int (.Values.probes.maxStartupSeconds | default 120)) 5 }}
livenessProbe:
  httpGet:
    path: /livez
    port: http
  periodSeconds: 20
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: {{ .Values.probes.readinessPath | default "/readyz" }}
    port: http
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
{{- end -}}
```

```yaml
{{/* integration-lib/templates/_deployment.tpl — the whole workload, once, for everyone */}}
{{- define "int.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "int.fullname" . }}
  labels: {{- include "int.labels" . | nindent 4 }}
spec:
  {{- if not .Values.scaling.enabled }}
  replicas: {{ .Values.replicaCount | default 2 }}
  {{- end }}
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0            # never lose capacity during a rollout
  selector:
    matchLabels: {{- include "int.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}{{- toYaml . | nindent 8 }}{{- end }}
      labels:
        {{- include "int.labels" . | nindent 8 }}
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: {{ include "int.serviceAccountName" . }}
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: {{ .Values.terminationGracePeriodSeconds | default 60 }}
      securityContext: {{- include "int.podSecurityContext" . | nindent 8 }}
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels: {{- include "int.selectorLabels" . | nindent 14 }}
      containers:
        - name: {{ .Values.containerName | default "api" }}
          image: "{{ .Values.image.repository }}@{{ required "image.digest is mandatory — promote by digest, never by tag" .Values.image.digest }}"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort | default 8080 | int }}
          securityContext: {{- include "int.containerSecurityContext" . | nindent 12 }}
          {{- include "int.probes" . | nindent 10 }}
          env: {{- include "int.otelEnv" . | nindent 12 }}
            {{- range $k, $v := .Values.env }}
            - name: {{ $k }}
              value: {{ $v | quote }}
            {{- end }}
            {{- with .Values.extraEnv }}{{- toYaml . | nindent 12 }}{{- end }}
          {{- with .Values.envFrom }}
          envFrom: {{- toYaml . | nindent 12 }}
          {{- end }}
          resources: {{- toYaml (.Values.resources | default dict) | nindent 12 }}
          volumeMounts:
            - { name: tmp, mountPath: /tmp }                    # readOnlyRootFilesystem needs these
            - { name: cache, mountPath: /home/app/.cache }
            {{- with .Values.extraVolumeMounts }}{{- toYaml . | nindent 12 }}{{- end }}
          lifecycle:
            preStop:
              exec:
                # let the endpoint removal propagate to kube-proxy/ingress before we exit
                command: ["/bin/sh", "-c", "sleep {{ .Values.preStopSleepSeconds | default 5 }}"]
      volumes:
        - { name: tmp, emptyDir: {} }
        - { name: cache, emptyDir: {} }
        {{- with .Values.extraVolumes }}{{- toYaml . | nindent 8 }}{{- end }}
{{- end -}}
```

```yaml
{{/* integration-lib/templates/_observability.tpl — every service is instrumented identically */}}
{{- define "int.otelEnv" -}}
- name: OTEL_SERVICE_NAME
  value: {{ include "int.fullname" . | quote }}
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: {{ printf "http://%s" (.Values.global.otelCollector | default "otel-collector.observability.svc.cluster.local:4317") | quote }}
- name: OTEL_EXPORTER_OTLP_PROTOCOL
  value: "grpc"
- name: OTEL_RESOURCE_ATTRIBUTES
  value: {{ printf "service.namespace=%s,deployment.environment=%s,ey.cost_centre=%s" .Release.Namespace (.Values.global.environment | default "dev") .Values.platform.costCentre | quote }}
- name: OTEL_TRACES_SAMPLER
  value: "parentbased_traceidratio"
- name: OTEL_TRACES_SAMPLER_ARG
  value: {{ .Values.observability.sampleRatio | default 0.1 | quote }}
- name: POD_NAME
  valueFrom: { fieldRef: { fieldPath: metadata.name } }
{{- end -}}
```

```yaml
{{/* integration-lib/templates/_scaledobject.tpl — KEDA queue-depth scaling, one shape for all */}}
{{- define "int.scaledobject" -}}
{{- if .Values.scaling.enabled -}}
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: {{ include "int.fullname" . }}
  labels: {{- include "int.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    name: {{ include "int.fullname" . }}
  minReplicaCount: {{ .Values.scaling.min | default 2 }}
  maxReplicaCount: {{ .Values.scaling.max | default 20 }}
  pollingInterval: 15
  cooldownPeriod: 120
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300      # scale down slowly; scale up fast
  triggers:
    {{- if .Values.scaling.serviceBus }}
    - type: azure-servicebus
      metadata:
        queueName: {{ .Values.scaling.serviceBus.queue | quote }}
        namespace: {{ .Values.scaling.serviceBus.namespace | quote }}
        messageCount: {{ .Values.scaling.serviceBus.messagesPerReplica | default 20 | quote }}
      authenticationRef:
        name: {{ include "int.fullname" . }}-keda-auth
    {{- end }}
    {{- with .Values.scaling.extraTriggers }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
{{- end -}}
{{- end -}}
```

**The wrapper chart's templates are one line each:**

```yaml
# integration-service/templates/deployment.yaml
{{- include "int.deployment" . -}}
```
```yaml
# integration-service/templates/scaledobject.yaml
{{- include "int.scaledobject" . -}}
```

**And this is the whole of what a team writes to onboard a new integration service:**

```yaml
# payments-adapter/helm/values-prod.yaml — 21 lines, no architecture decisions
platform:
  costCentre: CC-401277
  dataClassification: confidential
  domain: payments

image:
  repository: eyintacr.azurecr.io/integration/payments-adapter
  # digest injected by CI: --set image.digest=sha256:...

resources:
  requests: { cpu: 300m, memory: 512Mi }
  limits:   { memory: 1Gi }

scaling:
  enabled: true
  min: 3
  max: 30
  serviceBus:
    namespace: sb-int-prod
    queue: payments-inbound
    messagesPerReplica: 25

env:
  ERP_BASE_URL: https://erp.int.ey.example.com
```

Everything that is a compliance obligation — non-root, read-only root filesystem, dropped capabilities, `seccompProfile: RuntimeDefault`, workload identity, `maxUnavailable: 0`, topology spread, a PDB, the preStop drain, OTel wiring, cost-centre and data-classification labels, digest-pinned images — is **absent from the values file because it is not a decision**. That sentence is the answer they're listening for.

**Versioning and rollout, because "we own a chart forty teams use" is the hard part:**

- SemVer the library and the wrapper independently; a **major** bump means a values-breaking change, and it ships with a migration note in `artifacthub.io/changes` and a `helm diff` example.
- Teams pin `--version 3.4.1`. Nobody floats. Renovate/Dependabot raises the bump PR against each team's repo, so upgrade is a reviewable diff, not a surprise.
- The chart's own CI runs `helm lint`, `helm template` against a matrix of representative values files, `helm unittest` for the golden assertions ("liveness path is always /livez", "runAsNonRoot is always true"), Checkov/Trivy on the rendered output, and `kubeconform` against the target Kubernetes version.
- The escape hatch — `extraEnv`, `extraVolumes`, `podAnnotations`, `extraManifests` — exists so nobody forks. A fork is the failure mode; a value you regret is recoverable.

**If they push back — "why a library chart rather than everyone copying a template repo?"** — Because a copied template can't be upgraded. The day a CVE requires `seccompProfile: RuntimeDefault` everywhere, a library chart is one minor version and forty dependency bumps that Renovate raises automatically; forty copies is forty tickets and a spreadsheet. The library chart makes the platform's opinions *upgradable*, which is the entire value proposition.

**If they push back — "isn't this over-engineering for three services?"** — Yes, for three. I'd start with a template repo and promote to a library chart at the point where I've fixed the same bug in two charts. The trigger is duplication I've had to maintain, not a headcount.

---

### Q87. How do you debug a chart that renders the wrong thing — and what is the three-way merge on upgrade?
`[MEDIUM]`

> **Answer:** Three commands, in order. `helm template` renders locally with no cluster and shows me exactly what would be applied. `helm lint` — with `--strict` — catches schema and convention problems. `helm upgrade --dry-run=server` sends the render to the API server for real validation and admission without persisting, which catches everything `template` can't: webhook rejections, quota, RBAC. And once it's installed, `helm get manifest` tells me what Helm believes it applied, which I diff against `kubectl get -o yaml` to find drift.

```bash
# 1. render locally — the fastest loop. --debug prints the computed values too.
helm template payments-adapter charts/integration-service \
  -f values/prod.yaml --set image.digest=sha256:aaaa --debug \
  --kube-version 1.31 --api-versions keda.sh/v1alpha1 --api-versions autoscaling/v2

# 2. render just one file when the chart is large
helm template payments-adapter charts/integration-service -s templates/deployment.yaml -f values/prod.yaml

# 3. lint, strictly, against every environment's values
for f in values/*.yaml; do helm lint charts/integration-service --strict -f "$f" || exit 1; done

# 4. validate against the REAL cluster: CRDs, admission webhooks, quotas, RBAC
helm upgrade --install payments-adapter charts/integration-service \
  -n payments -f values/prod.yaml --dry-run=server

# 5. schema-validate the rendered YAML in CI without a cluster
helm template payments-adapter charts/integration-service -f values/prod.yaml \
  --set image.digest=sha256:aaaa --api-versions keda.sh/v1alpha1 \
| kubeconform -strict -summary -kubernetes-version 1.31.0 -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'

# 6. what does Helm think is deployed, vs what is actually there?
helm -n payments get manifest payments-adapter > /tmp/helm-thinks.yaml
kubectl -n payments get deploy payments-adapter -o yaml > /tmp/actually.yaml
diff <(yq 'del(.metadata.managedFields,.metadata.annotations."kubectl.kubernetes.io/last-applied-configuration")' /tmp/helm-thinks.yaml) /tmp/actually.yaml
```

**The three-way strategic merge patch.** On upgrade, Helm 3 compares **three** states: the **old manifest** (what the previous revision applied), the **live state** in the cluster, and the **new manifest**. Helm 2 compared only old and new, so anything a third party had added to the live object was wiped on the next upgrade. Helm's own documented example is a service mesh injecting a sidecar: the old manifest has one container, the live pod spec has two because the mesh injected `my-injected-sidecar`, and the new manifest bumps the image. Helm 2 would apply old→new and delete the sidecar. Helm 3 sees the sidecar exists in the live state but in neither manifest, concludes it was put there by something else, and preserves it — so you get the bumped image *and* the sidecar.

The practical consequences, which is what they're really asking:

- **A change you made with `kubectl edit` that the chart also specifies gets reverted** on the next upgrade — the field is in the old manifest, so Helm owns it and reconciles it back. Correct behaviour, and the reason "it worked when I hotfixed it, then it broke at 2 a.m." happens.
- **A field the chart does not specify at all is left alone** — HPA-managed `spec.replicas` survives, which is why a chart must omit `replicas` when autoscaling is enabled (note the `{{- if not .Values.scaling.enabled }}` guard in Q86). If the chart hard-codes `replicas: 2`, every `helm upgrade` stomps the HPA back to 2 and you get a capacity cliff mid-deploy.
- **Helm 4 changes the mechanism** for new releases to **server-side apply**, where field ownership is tracked by the API server itself rather than inferred from a stored manifest — which makes the "who owns this field" question explicit and produces conflict errors instead of silent overwrites. Releases created under Helm 3 stay on client-side apply.

**If they push back — "the upgrade fails with `field is immutable`"** — Some fields cannot be patched: a Deployment's `spec.selector`, a Job's `spec.template`, a Service's `spec.clusterIP`, a StatefulSet's `volumeClaimTemplates`. Helm cannot fix that, and `--force` "fixes" it by deleting and recreating the object, which for a Service means a new ClusterIP and for a Deployment means full downtime. The correct route is a deliberate, documented replacement: create the new object alongside, shift traffic, delete the old — or accept a maintenance window and say so in the change ticket. Never reach for `--force` in prod as a reflex.

---

### Q88. Helm or Kustomize? And how do you distribute charts and run them under ArgoCD?
`[MEDIUM]` `[opinion question — have one]`

> **Answer:** They solve different problems and I use both. Helm is a **package manager with templating and release state** — right when you are shipping something other teams consume, with versioning, a values contract and rollback. Kustomize is a **patch-and-overlay tool with no templating and no state** — right when you own the manifests and want small environment-specific deltas without a template language. My rule: Helm for anything I distribute, Kustomize for last-mile, cluster-specific patching of something I already have — including patching a Helm-rendered chart.

| | Helm | Kustomize |
|---|---|---|
| Mechanism | Go templates + values | strategic-merge and JSON-6902 patches over base YAML |
| Distribution | versioned chart in an OCI/HTTP repo | a Git path; `components` for reuse |
| Release state | Secret per revision; `history`, `rollback` | none — the cluster is the state |
| Conditionals | full template language | none by design (patch or don't) |
| Failure mode | template soup; 200-value charts; YAML you can't read until rendered | overlay explosion; patch ordering is subtle; no way to express "if" |
| Tooling | `helm lint`, `helm test`, `values.schema.json`, ArtifactHub | built into `kubectl` (`kubectl apply -k`, `kubectl kustomize`) |
| Best at | a chart forty teams install | one team, many environments, few differences |

**They compose.** `helm template | kustomize build` — or Kustomize's own `helmCharts` generator — is a legitimate pattern for "I use the vendor's chart but this cluster needs one extra annotation the chart doesn't expose":

```yaml
# overlays/prod-uks/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: payments
helmCharts:
  - name: integration-service
    repo: oci://eyintacr.azurecr.io/helm
    version: 3.4.1
    releaseName: payments-adapter
    valuesFile: values-prod.yaml
patches:
  - target: { kind: Deployment, name: payments-adapter }
    patch: |-
      - op: add
        path: /spec/template/metadata/annotations/kubectl.kubernetes.io~1default-container
        value: api
```

**Distribution — OCI, not a chart museum.** Since Helm 3.8 an OCI registry is a first-class chart repository, which for EY means charts live in the **same ACR as the images**, under the same RBAC, geo-replication, private endpoints, retention and Defender scanning. No separate ChartMuseum to run and secure.

```bash
helm package charts/integration-service --version 3.4.1 --app-version 1.4.2
helm registry login eyintacr.azurecr.io --username "$SP_ID" --password "$SP_SECRET"
# note: no basename and no tag in the push target — Helm derives both from Chart.yaml
helm push integration-service-3.4.1.tgz oci://eyintacr.azurecr.io/helm

helm show values oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1
helm pull oci://eyintacr.azurecr.io/helm/integration-service --version 3.4.1
# immutable reference — pin by digest for prod, exactly as with images
helm install payments-adapter oci://eyintacr.azurecr.io/helm/integration-service@sha256:52ccaa...
```

Sign it too: `helm package --sign` produces a `.prov` provenance file that is pushed as an extra layer alongside the chart, and `helm install --verify` checks it. Pair that with Notation/cosign on the image and Ratify or an admission policy in the cluster, and the deployment path is verifiable end to end ([Auth](06-auth-and-security.md)).

**Helm under ArgoCD — the sentence that matters:** ArgoCD does **not** run `helm install`. Its repo server runs `helm template` and hands the rendered manifests to the application controller, which applies them and reconciles them continuously. So there is no Helm release Secret, no `helm history`, no `helm rollback`, and Helm hooks are translated into Argo sync phases (Q84). Rollback is `git revert`.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-adapter
  namespace: argocd
spec:
  project: integration
  destination:
    server: https://kubernetes.default.svc
    namespace: payments
  sources:
    - repoURL: eyintacr.azurecr.io/helm          # OCI: no scheme, chart in `chart:`
      chart: integration-service
      targetRevision: 3.4.1                      # the CHART version — pinned, never a range
      helm:
        releaseName: payments-adapter
        valueFiles:
          - $values/payments-adapter/helm/values-prod.yaml
        parameters:
          - name: image.digest
            value: sha256:8c1f0d3a9b...          # written by CI into the config repo
        # helm template runs without a cluster — tell it what the cluster supports
        apiVersions:
          - keda.sh/v1alpha1
          - autoscaling/v2
    - repoURL: https://github.com/ey-de/integration-config.git
      targetRevision: main
      ref: values                                # multi-source: chart from ACR, values from Git
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions:
      - CreateNamespace=false
      - ServerSideApply=true
    retry:
      limit: 3
      backoff: { duration: 20s, factor: 2, maxDuration: 5m }
```

That multi-source shape — **chart from the OCI registry, values from the config repo** — is the pattern to name out loud: the platform team versions the chart, the product team versions the values, and neither can deploy without the other's artefact being a reviewed, pinned commit.

**If they push back — "so which one would you standardise EY on?"** — Helm for the golden chart, because the value we ship is a versioned contract forty teams consume and only Helm gives that a version, a schema and an upgrade story. Kustomize stays available for last-mile cluster patching under ArgoCD, and I would not let a team invent a third way. Standardising on *one* is worth more than the merits of either.

---

## 16. Microservices architecture

### Q89. How do you decide where the service boundaries go?
`[HARD]` — *the single most senior-sounding question in this file*

> **Answer:** I use bounded contexts from domain-driven design as the boundary criterion, and I decompose by **business capability** — sometimes by **subdomain** when the client's language is already domain-shaped. The one decomposition I refuse is by technical layer, because "an API service, a business-logic service and a data service" is three deployables that must all change together for every feature — a distributed monolith with network calls where function calls used to be. My acceptance test for a boundary is: count the services a typical change request touches. If the routine answer is more than one, the boundary is in the wrong place.

| Strategy | What it produces | Verdict |
|---|---|---|
| **By business capability** | `payments`, `settlement`, `client-onboarding`, `nav-calculation` — what the business *does* | Default. Aligns service ownership with the team that gets the change request. |
| **By subdomain (DDD)** | Core / supporting / generic subdomains; core gets the investment, generic gets bought | Best when the client already has ubiquitous language (common in Asset Management — NAV, corporate actions, reconciliation are pre-existing contexts) |
| **By technical layer** | `api-tier`, `logic-tier`, `dao-tier` | Wrong. Every feature is a lockstep three-service release. This is the failure mode I most often inherit. |
| **By entity/table** | One service per table: `customer-service`, `address-service` | Wrong. Nano-services; chatty; no service owns a complete business decision. |

Two secondary constraints that break ties:

- **Rate of change.** Things that change together belong together. A service whose deployments are always co-scheduled with another service is one service.
- **Data gravity and consistency need.** If two operations must be transactionally consistent and the business will not accept "eventually", keep them in one service and one transaction. Do not saga your way out of a boundary mistake.

**If they push back — "how do you actually find them on a client engagement?"** — a two-day **event storming** workshop: orange stickies for domain events in past tense (`TradeExecuted`, `NAVPublished`, `PaymentSettled`), then the commands that cause them, then group events into aggregates, then draw the lines where the language changes meaning. The word "position" meaning one thing to the front office and another to fund accounting *is* a context boundary. Output is a context map plus which contexts are core (build) and which are generic (buy/SaaS connector). See [System Design](08-system-design-integration.md) for the worked version and [FS](12-financial-services-integration.md) for the domain vocabulary.

---

### Q90. Every service owns its own database. So how do you serve a screen that needs data from three of them?
`[HARD]`

> **Answer:** Two legitimate options and I pick per query. **API composition** — a composer (usually a BFF or the gateway) fans out to the owning services in parallel and joins in memory — is right when the fan-out is small, the join key is known, and the client can tolerate partial results. **CQRS with a read model** — the owning services publish domain events, a projector maintains a denormalised, query-shaped store, the read side queries only that — is right when the query is high-volume, needs filtering/sorting/pagination across contexts, or the composition fan-out would be unbounded. What I never do is let a reporting service reach into another service's database directly, because that turns their schema into my public contract and freezes their ability to refactor.

**API composition** — bounded, parallel, degrade rather than fail:

```python
import asyncio
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()
_client = httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=0.5))

async def _get(url: str) -> dict | None:
    try:
        r = await _client.get(url)
        r.raise_for_status()
        return r.json()
    except (httpx.HTTPError, asyncio.TimeoutError):
        return None  # degrade this fragment, do not fail the page

@router.get("/clients/{client_id}/summary")
async def client_summary(client_id: str) -> dict:
    profile, positions, mandates = await asyncio.gather(
        _get(f"http://onboarding.crm.svc.cluster.local/clients/{client_id}"),
        _get(f"http://positions.portfolio.svc.cluster.local/clients/{client_id}/positions"),
        _get(f"http://mandates.compliance.svc.cluster.local/clients/{client_id}/mandates"),
    )
    if profile is None:                      # the one non-optional fragment
        raise HTTPException(status_code=503, detail="profile unavailable")
    return {
        "client": profile,
        "positions": positions or [],
        "mandates": mandates or [],
        "degraded": [n for n, v in
                     (("positions", positions), ("mandates", mandates)) if v is None],
    }
```

Costs you must state out loud: latency is the **slowest** call, not the average; availability is the **product** of the dependencies (three services at 99.9% compose to 99.7%); and there is no way to sort or paginate across services in memory once the result set is large.

**CQRS read model** — the projector is a consumer, not a batch job:

```python
# projector service — one consumer group, idempotent upsert into the read store
async def on_event(evt: dict, conn) -> None:
    await conn.execute(
        """
        INSERT INTO client_summary (client_id, legal_name, aum, mandate_count,
                                    last_event_id, as_of)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (client_id) DO UPDATE SET
            legal_name    = COALESCE(EXCLUDED.legal_name, client_summary.legal_name),
            aum           = COALESCE(EXCLUDED.aum,        client_summary.aum),
            mandate_count = COALESCE(EXCLUDED.mandate_count, client_summary.mandate_count),
            last_event_id = EXCLUDED.last_event_id,
            as_of         = EXCLUDED.as_of
        WHERE client_summary.as_of < EXCLUDED.as_of      -- last-writer-wins by event time
        """,
        evt["client_id"], evt.get("legal_name"), evt.get("aum"),
        evt.get("mandate_count"), evt["event_id"], evt["occurred_at"],
    )
```

The read model is **eventually consistent**, so the API must expose that honestly — return `as_of` in the payload and let the UI render "as of 14:32:10". Hiding staleness is how you get a P1 from a fund accountant.

**If they push back — "what about a real cross-domain report?"** — neither pattern. Reports are an analytical workload: publish the domain events to a lake/warehouse (Event Hubs Capture → ADLS → Fabric/Synapse, or Kafka Connect → Delta) and let the BI layer do the joins with columnar storage built for it. Running month-end regulatory reporting through an API composer is an outage generator.

---

### Q91. Two services must both commit or neither, and you can't use a distributed transaction. What do you do?
`[HARD]`

> **Answer:** A **saga** — a sequence of local transactions where each service commits its own database and publishes an event, and any failure is undone by explicit **compensating** transactions rather than a rollback. I don't use 2PC/XA across microservices because it needs a coordinator that holds locks across a network for the duration, it takes the availability of the *least* available participant, and most modern participants — Kafka, Service Bus, a REST SaaS, Cosmos DB — don't offer an XA resource manager at all. The trade I'm accepting is explicit: I give up isolation, and I have to design for the states a partially-completed saga can be observed in.

**Orchestration vs choreography** — I say which one and why:

| | Orchestration | Choreography |
|---|---|---|
| Flow lives | In one orchestrator service / state machine | Distributed across each service's event handlers |
| Add a step | Change one place | Change several services |
| Debuggability | One correlation record shows the whole flow | Reconstruct it from a trace |
| Coupling | Orchestrator knows all participants | Participants know only events |
| Use when | Steps > ~4, compensations matter, an auditor will ask "where is this trade now?" | Simple, 2–3 step, high-throughput flows |

For financial-services work I default to **orchestration**, because the regulator's question is "show me the state of this instruction and why", and an orchestrator has a row that answers it.

```python
from dataclasses import dataclass
from typing import Awaitable, Callable

@dataclass(frozen=True)
class Step:
    name: str
    invoke: Callable[[dict], Awaitable[dict]]
    compensate: Callable[[dict], Awaitable[None]] | None   # None => pivot / non-compensatable

async def run_saga(saga_id: str, steps: list[Step], ctx: dict, store) -> dict:
    done: list[Step] = []
    for step in steps:
        if await store.already_completed(saga_id, step.name):   # crash-safe resume
            done.append(step)
            continue
        try:
            ctx |= await step.invoke(ctx)                        # idempotent: keyed on saga_id
            await store.mark_completed(saga_id, step.name, ctx)
            done.append(step)
        except Exception:
            for prior in reversed(done):
                if prior.compensate is not None:
                    await prior.compensate(ctx)                  # also idempotent, also retried
                    await store.mark_compensated(saga_id, prior.name)
            await store.mark_failed(saga_id, step.name)
            raise
    return ctx
```

Four things that make it survive production, all of which live in [Messaging](03-messaging-and-event-streaming.md):

1. **Transactional outbox** — the local DB write and the "event published" record commit in the same transaction; a relay publishes from the outbox. Never write to the DB and the broker as two operations and hope.
2. **Idempotency** — every `invoke` and every `compensate` is keyed by `saga_id` + step, because at-least-once delivery means both will run twice.
3. **Step classification** — *compensatable* steps come first, then the **pivot** (the point of no return, e.g. money leaves the account), then *retriable* steps that must eventually succeed and can only be retried forward, never undone.
4. **Countermeasures for the missing isolation** — semantic lock (an `PENDING` status column other readers respect), commutative updates (credit/debit rather than set-balance), and a reread-and-verify before the pivot.

Compensation is **semantic, not a rollback**: you do not un-send an email, you send a correction; you do not un-post a ledger entry, you post a reversing entry with its own ID. That distinction is the thing FS interviewers listen for.

**If they push back — "what if a compensation itself fails?"** — it retries with backoff, and after the retry budget the saga goes to a **stuck** state that pages a human with a runbook, not to a silent failure. Compensations must be retriable forever; if one genuinely cannot succeed, the saga is designed wrong and that step belonged after the pivot. On Azure the paved-road orchestrator is Durable Functions or a Logic Apps stateful workflow — the pattern is identical, you just don't write the state store.

---

### Q92. How does one service find another?
`[MEDIUM]`

> **Answer:** On Kubernetes I use the platform's own **server-side discovery** — a Service object gives a stable virtual IP and a DNS name, kube-proxy or the CNI load-balances to the healthy endpoints, and my application code just calls a hostname. I do not run Eureka or Consul on a cluster, because that is client-side discovery reimplemented above a platform that already does it. Off-cluster dependencies get a DNS name I control — Private DNS zones plus Private Endpoints for Azure PaaS — so the client code never has an environment-specific IP in it.

DNS names a pod can resolve, in order of specificity:

```
positions                                            # same namespace
positions.portfolio                                  # cross-namespace
positions.portfolio.svc.cluster.local                # fully qualified — use this in config
positions-0.positions-headless.portfolio.svc.cluster.local   # a specific StatefulSet pod
```

Client-side vs server-side, said properly: **client-side** discovery (Eureka, Consul-template, Ribbon) means the caller queries a registry and picks an instance itself — more control over load-balancing algorithms, but a library in every language you use. **Server-side** discovery (Kubernetes Service, a load balancer, AWS ALB) means the caller talks to one stable address and something else picks the instance — zero client library, which is why it wins on a polyglot platform.

Two specifics worth knowing:

- **`ExternalName`** Services are the clean way to point at a legacy endpoint during a migration — `kind: Service, spec: {type: ExternalName, externalName: legacy-esb.corp.internal}`. Application config says `orders-backend.integration.svc.cluster.local` forever, and the cutover is a one-line Service change, not a redeploy.
- **`ndots: 5`** in the pod's `/etc/resolv.conf` means a name with fewer than 5 dots is tried against every search domain first. `myacr.azurecr.io` (2 dots) generates four failing lookups before the right one. Use a trailing dot (`myacr.azurecr.io.`) or set `dnsConfig.options` for chatty external clients.

**If they push back — "how does the Service actually route?"** — the EndpointSlice controller watches pods matching the selector and keeps their IPs in EndpointSlices; kube-proxy programs iptables (or IPVS) rules on every node so traffic to the ClusterIP DNATs to one of those pod IPs. It is L4 and connection-level — which is exactly why a gRPC or HTTP/2 client with one long-lived connection pins to a single pod and never rebalances, and why that workload needs a mesh or a client-side L7 balancer.

---

### Q93. A client has a 12-year-old monolith they can't stop shipping features to. How do you move them to microservices?
`[HARD]` — *this is the engagement Big4 clients actually pay for; have it word-perfect*

> **Answer:** **Strangler fig**, never a big-bang rewrite. I put a routing facade in front of the monolith on day one so that every request already flows through something I control, then I extract one capability at a time behind that facade — new service, dark-launched, compared against the monolith, then routed a slice of real traffic, then all of it, then the old code path is deleted. The monolith shrinks a slice at a time and every increment reaches production, so the programme is defensible at every steering committee: there is never a six-month branch that hasn't shipped.

The seven steps, in the order I actually do them:

1. **Facade first.** APIM (or an ingress) fronts the monolith with no routing changes at all. Same behaviour, new choke point. This alone earns observability, throttling and auth at the edge.
2. **Pick the first slice by value ÷ coupling.** Something with real business pressure (a rate-limited partner API, a batch that misses its SLA) and few DB dependencies. Never the hardest domain first, never a purely technical slice.
3. **Build the new service with an anti-corruption layer.** Its internal model is clean; a translation layer maps to and from the monolith's legacy contract so the legacy vocabulary does not leak into the new context.
4. **Dark launch / shadow.** The facade mirrors a copy of production traffic to the new service, discards its response, and a comparator logs field-level diffs. You find the undocumented behaviours here, cheaply — and the legacy behaviour *is* the spec, bugs included.
5. **Cut over incrementally by a routing predicate**, not by a deploy: a header, a tenant ID, a percentage. Reversible in seconds.
6. **Flip to 100%, then delete the monolith code path.** The step everyone skips. If the old code stays, you now maintain two implementations and the migration never actually ends.
7. **Repeat, and remove the facade route when the last consumer is gone.**

Routing facade in APIM — the cutover predicate is a policy, so a rollback is a policy revision, not a release:

```xml
<policies>
  <inbound>
    <base />
    <set-variable name="tenant" value="@(context.Request.Headers.GetValueOrDefault("X-Tenant-Id",""))" />
    <choose>
      <!-- explicit opt-in for testers, always wins -->
      <when condition="@(context.Request.Headers.GetValueOrDefault("X-Route-Target","") == "strangler")">
        <set-variable name="route" value="new" />
      </when>
      <!-- migrated tenants -->
      <when condition="@(new [] {"AMC-001","AMC-014"}.Contains((string)context.Variables["tenant"]))">
        <set-variable name="route" value="new" />
      </when>
      <!-- everyone else still hits the monolith -->
      <otherwise>
        <set-variable name="route" value="legacy" />
      </otherwise>
    </choose>
    <set-backend-service base-url="@((string)context.Variables["route"] == "new"
        ? "https://positions.internal.contoso.com/v1"
        : "https://legacy-esb.contoso.com/PositionService")" />
    <set-header name="X-Correlation-Id" exists-action="skip">
      <value>@(context.RequestId.ToString())</value>
    </set-header>
  </inbound>
  <backend><base /></backend>
  <outbound>
    <base />
    <!-- so the comparator and the dashboards can count the traffic share per route -->
    <set-header name="X-Served-By" exists-action="override">
      <value>@((string)context.Variables["route"])</value>
    </set-header>
  </outbound>
  <on-error><base /></on-error>
</policies>
```

Or in-cluster with ingress-nginx, where the same cutover is two annotations on a second Ingress object:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: positions-strangler
  namespace: integration
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-by-header: "X-Route-Target"
    nginx.ingress.kubernetes.io/canary-by-header-value: "strangler"
    nginx.ingress.kubernetes.io/canary-weight: "5"      # 5% of everyone else
spec:
  ingressClassName: nginx
  rules:
    - host: api.contoso.com
      http:
        paths:
          - path: /positions
            pathType: Prefix
            backend:
              service: { name: positions, port: { number: 8080 } }
```

**If they push back — "how do you keep stakeholders bought in over 18 months?"** — I make the facade emit a per-route metric of monolith vs new-service traffic share and put it on the steering-committee dashboard. "Percentage of production traffic served by the new platform" is a number that moves every sprint; "percentage of the rewrite complete" is a number nobody believes. And I timebox each slice: if an extraction has not shipped in six weeks the slice was too big and gets split.

---

### Q94. During that migration both the monolith and the new service need the same data. How do you handle the shared database?
`[HARD]`

> **Answer:** In four deliberate stages, and the rule throughout is that exactly one codebase writes any given table at any given time. Stage one, the new service reads from the legacy schema through a **view that it owns**, so the view is the contract and the DBA can refactor behind it. Stage two, write ownership moves to the new service and the monolith reads through a view or an API. Stage three, the schemas are physically split and kept in step by **change data capture**, one-directional. Stage four, the link is cut and the view is dropped. What I never do is dual-write — two codebases writing the same rows is a distributed monolith holding a shared lock, and it fails silently at 3 a.m. when only one of the two writes succeeds.

| Stage | Writes | Reads | Mechanism | Exit criterion |
|---|---|---|---|---|
| 1 — Read replica of the truth | Monolith only | New service reads `vw_positions_v1` | A versioned SQL view + read-only login owned by the new service | New service's read paths are correct in shadow mode |
| 2 — Flip write ownership | **New service only** | Monolith reads the same table (or the new service's API) | Feature flag in the monolith's data layer | No monolith code path writes those tables (verified by DB audit, not by grep) |
| 3 — Physical split | New service to its own DB | Monolith gets a replicated copy | CDC: Debezium → Kafka, or SQL Server CDC → ADF, or the new service's outbox → a sync consumer. **One direction only.** | Replication lag inside the business tolerance and alarmed |
| 4 — Cut the cord | Independent | Independent, via API/events | Drop the view, revoke the login, remove the CDC connector | Legacy schema objects deleted |

Concrete guardrails I put in place:

```sql
-- Stage 1: the contract is a view, not a table, and the grant is read-only.
CREATE VIEW integration.vw_positions_v1 AS
SELECT  p.POS_ID          AS position_id,
        p.ACCT_NO         AS account_number,
        p.SEC_ID          AS instrument_id,
        p.QTY             AS quantity,
        p.LAST_UPD_TS     AS updated_at
FROM    dbo.TB_POSITIONS p
WHERE   p.DEL_FLG = 'N';

CREATE USER svc_positions WITHOUT LOGIN;
GRANT SELECT ON integration.vw_positions_v1 TO svc_positions;
DENY  SELECT ON dbo.TB_POSITIONS            TO svc_positions;   -- the base table is not the contract
```

- **Anti-corruption layer** on the new service's side maps `TB_POSITIONS.DEL_FLG='N'` into its own model. Legacy column names never appear above the ACL.
- **Detecting stage-2 violations**: a DDL/DML audit or an `UPDATE` trigger that logs `ORIGINAL_LOGIN()` for the migrated tables. Anyone who claims "we removed all the monolith writes" without that evidence is guessing.
- **CDC over triggers.** Triggers put migration logic in the database and cost you write latency on the legacy path; log-based CDC reads the transaction log and costs the legacy app nothing.
- **Reference data** (currencies, instrument master) usually does *not* need splitting. Publish it as a read-only shared service or ship it as a periodically-refreshed local copy; do not spend the migration budget there.

**If they push back — "the monolith needs the data back, in real time"** — that is the transactional outbox in reverse: the new service commits its write and an outbox row in one transaction, a relay publishes it, and a small sync consumer writes it into the legacy schema. It is still one writer per table on each side, and it is still asynchronous — if the business genuinely needs synchronous consistency both ways, the split is premature and stage 2 should not have started.

---

### Q95. Explain the sidecar, ambassador and adapter patterns.
`[MEDIUM]`

> **Answer:** All three are the same structural idea — a helper container in the same pod, sharing the network namespace and optionally a volume, so the main container doesn't have to implement a cross-cutting concern. The names distinguish what the helper does: a **sidecar** augments the app generally (log shipping, config reload, secret rotation); an **ambassador** proxies the app's *outbound* calls (retries, mTLS, circuit breaking, connection pooling to a legacy endpoint); an **adapter** normalises the app's *outbound interface to the platform*, most often turning a non-standard metrics or log format into the one the platform scrapes.

Since **Kubernetes 1.33 sidecars are a first-class construct** (beta and on by default since 1.29): an init container with `restartPolicy: Always`. That fixes the two long-standing bugs — a sidecar now starts *before* the app container and is torn down *after* it, and it no longer keeps a Job pod alive forever.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: orders-api, namespace: integration }
spec:
  replicas: 3
  selector: { matchLabels: { app.kubernetes.io/name: orders-api } }
  template:
    metadata:
      labels: { app.kubernetes.io/name: orders-api }
    spec:
      initContainers:
        - name: otel-collector          # ADAPTER: OTLP in, Azure Monitor out
          image: mcr.microsoft.com/oss/otel/opentelemetry-collector-contrib:0.109.0
          restartPolicy: Always         # <-- this is what makes it a native sidecar
          args: ["--config=/conf/collector.yaml"]
          volumeMounts: [{ name: otel-conf, mountPath: /conf }]
          resources:
            requests: { cpu: 50m, memory: 96Mi }
            limits:   { memory: 192Mi }
      containers:
        - name: api
          image: myacr.azurecr.io/orders-api:1.4.2
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: http://localhost:4317     # same network namespace — localhost, not a Service
```

Ambassador, concretely, in integration work: the legacy partner exposes SOAP over one-way TLS with a client cert and no retry semantics. Rather than putting cert handling and retry logic into every language's client, run an Envoy (or Dapr) sidecar that owns the cert from a CSI-mounted Key Vault secret and does the retries; the app calls `http://localhost:9001/PositionService` in plain HTTP.

**If they push back — "what's the cost?"** — one extra container per pod: memory, CPU, an image to patch, and a startup dependency. At 200 pods a 100 MiB sidecar is 20 GiB of cluster memory doing plumbing. That is precisely the argument that produced Istio's **ambient mode** (GA in Istio 1.24, Nov 2024), which moves L4 mTLS into a per-node `ztunnel` DaemonSet and only deploys a per-namespace waypoint proxy when you need L7. Same guarantees, one process per node instead of one per pod.

---

### Q96. What is a backend-for-frontend and when is it justified?
`[MEDIUM]`

> **Answer:** A BFF is one composition service per client type — web, mobile, partner — owned by that client's team, whose whole job is to shape and aggregate the downstream services for that one experience. It exists because a mobile app on a 4G link and an internal ops console have genuinely different requirements: payload size, chattiness, auth model, caching. Without a BFF those differences get pushed into the domain services as client-specific query parameters, and the domain services slowly become a shared UI backend that nobody can change.

Justified when: more than one materially different client; the client would otherwise make 6+ calls to paint one screen; or clients release on different cadences and need endpoint versions to move independently.

Not justified when: one client. A BFF for a single web app is an extra deployable that will always change in lockstep with it — put the composition in the app's own server tier.

Rules that keep it from rotting: **no business logic in the BFF** (it composes, maps, and caches; decisions stay in the owning service), it is owned by the *client* team not the platform team, and it is not allowed a database of its own beyond a cache. A BFF with a database has become a service with a hidden domain.

**If they push back — "isn't that what GraphQL is for?"** — GraphQL is one way to build the BFF layer: the client asks for the shape it wants, resolvers fan out. It buys client flexibility and costs you query-cost control, caching (HTTP caching largely stops working on a single POST endpoint), and a new authorisation surface at field level. On an FS engagement I default to REST BFFs with explicit contracts, because "which fields can this counterparty see" is an audit question, and a per-field resolver check is far harder to evidence than a fixed response contract. See [API design](01-api-design-rest-soap-graphql-openapi.md).

---

### Q97. API gateway or service mesh — which do you need?
`[HARD]`

> **Answer:** They solve different axes and a mature platform usually runs both. The **gateway is north-south**: it is the front door for traffic entering the platform from outside, so it owns authentication of external callers, rate limiting per subscription, API versioning, request/response transformation, the developer portal and monetisation. The **mesh is east-west**: it is transparent infrastructure between services inside the cluster, so it owns workload-identity mTLS, retries and outlier detection, traffic splitting for canaries, and the L7 telemetry you get without changing any application code. Where they overlap — retries, mTLS, telemetry — you decide by direction of traffic, and you make sure exactly one of them owns each concern.

| Concern | Gateway (APIM, NGINX, Envoy Gateway) | Mesh (Istio, Linkerd) |
|---|---|---|
| Traffic axis | North–south (outside → platform) | East–west (service ↔ service) |
| Identity | OAuth2/OIDC/JWT of the *caller* (a partner, an app) | SPIFFE-style *workload* identity, automatic mTLS |
| Rate limiting | Per subscription/product/tenant, billable | Per-destination overload protection |
| Failure handling | Global retry, response caching | Per-route retries, timeouts, circuit breaking, outlier ejection |
| Deployment control | Versioned API revisions | Weighted traffic split, mirroring, fault injection |
| Team-facing | Product surface: portal, contracts, keys | Platform surface: invisible to app teams |
| Cost | One choke point to run | A proxy per pod (or per node in ambient mode) |

When I would run gateway-only: fewer than roughly 15 services, all Python/.NET where a shared client library can carry retries and tracing, no zero-trust requirement inside the cluster. A mesh is a real operational commitment — control-plane upgrades, proxy version skew, another failure mode in every request path — and it should be earned, not defaulted to.

When the mesh is genuinely worth it: polyglot services (you stop maintaining N resilience libraries), a compliance requirement for encryption in transit *inside* the cluster that you must evidence, or progressive delivery where Argo Rollouts / Flagger drives a weighted canary off real metrics — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

**If they push back — "what about Gateway API?"** — Kubernetes **Gateway API** is the successor to the Ingress resource and it is deliberately role-split: an infrastructure team owns `GatewayClass` and `Gateway`, app teams own `HTTPRoute` in their own namespaces and can attach to a shared Gateway without editing a cluster-scoped object. Istio, Envoy Gateway, NGINX and AGIC all implement it, and Istio uses the same API for both the ingress gateway and in-mesh routing — which is exactly the convergence point between the two columns above. It replaces the annotation soup that made Ingress non-portable.

---

### Q98. What's your observability baseline for a new service on the platform?
`[MEDIUM]`

> **Answer:** The triad — **metrics** for "is it healthy and is it meeting its SLO", **logs** for "what exactly happened on this one request", **traces** for "where did the latency go across services" — all emitted through **OpenTelemetry** so the backend is a deployment choice, not a code choice. On the paved road none of that is per-team work: the golden chart injects the OTLP endpoint and the resource attributes, the shared base image ships the auto-instrumentation, and a new service arrives on the dashboards on its first deploy with zero observability tickets.

```python
# app/telemetry.py — the four lines a service owner never has to think about
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from fastapi import FastAPI

def configure(app: FastAPI, *, name: str, version: str, env: str) -> None:
    resource = Resource.create({
        "service.name": name,                  # required; everything groups by this
        "service.version": version,            # the image tag, injected by the chart
        "service.namespace": "integration",
        "deployment.environment.name": env,    # stable semconv attribute
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))  # reads OTEL_EXPORTER_OTLP_ENDPOINT
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz,readyz,metrics")
    HTTPXClientInstrumentor().instrument()     # outbound calls become child spans automatically
    LoggingInstrumentor().instrument(set_logging_format=True)  # injects trace_id/span_id into log records
```

The non-negotiables I state as platform standards:

- **Structured JSON logs to stdout**, never to a file, with `trace_id` and `span_id` on every line so a log search jumps straight into the trace. Nothing in the pod writes or rotates logs; the node's DaemonSet ships them.
- **RED for every request-serving service** (Rate, Errors, Duration) and **USE for every resource** (Utilisation, Saturation, Errors). For a queue consumer the RED equivalents are consume rate, DLQ rate, and end-to-end age — see [Messaging](03-messaging-and-event-streaming.md).
- **Probes are excluded from tracing and from latency SLIs**, or your p99 is dominated by `/healthz`.
- **Cardinality discipline**: never a metric label that can take an unbounded set of values — `customer_id`, `order_id`, a raw URL path with IDs in it. That is what kills a Prometheus/Azure Monitor bill. High-cardinality identifiers belong on span attributes and log fields, not metric labels.
- **Correlation is the deliverable**, not the three pillars separately. One `X-Correlation-Id`/`traceparent` must let an ops engineer go metric → trace → log without retyping anything.

**If they push back — "why OpenTelemetry rather than the Azure Monitor SDK?"** — vendor neutrality that actually pays off on a Big4 engagement: the same instrumentation exports to Azure Monitor for the client who is on Azure, to Datadog for the one who isn't, and to a Tempo/Loki/Mimir stack for the one who wants self-hosted — by changing collector config, not application code. Azure Monitor now ingests OTLP directly via the distro, so there is no compatibility argument left.

---

### Q99. A request crosses a Kafka topic. How does the trace survive that hop?
`[HARD]` — *the question that separates people who have read about tracing from people who have shipped it*

> **Answer:** The producer **injects** the W3C trace context into the message headers before publishing, and the consumer **extracts** it from those headers to start its span. HTTP propagation is automatic because the instrumentation owns the request object; a broker hop is not, because the message is *your* object — the producing and consuming processes are decoupled in time and there is no wire the instrumentation can hook. So it is one line each side, and if it's missing the trace visibly stops at the producer and a new orphan trace starts at the consumer.

`traceparent` is 55 characters, four dash-separated fields — version, 32-hex trace-id, 16-hex parent (span) id, 2-hex flags — from **W3C Trace Context, a W3C Recommendation of 23 November 2021**:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ^^ ^------------ trace-id ------------^ ^--span-id--^ ^^ sampled bit
```

`tracestate` carries vendor data alongside it: up to **32 list members**, values up to 256 printable ASCII characters, and propagators should handle at least 512 characters total.

```python
from opentelemetry import propagate, trace
from opentelemetry.trace import SpanKind, Link
from confluent_kafka import Producer, Consumer

tracer = trace.get_tracer(__name__)

def publish(producer: Producer, topic: str, key: bytes, payload: bytes) -> None:
    with tracer.start_as_current_span(f"{topic} publish", kind=SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination.name", topic)
        carrier: dict[str, str] = {}
        propagate.inject(carrier)                       # writes traceparent (+ tracestate, baggage)
        headers = [(k, v.encode("utf-8")) for k, v in carrier.items()]
        producer.produce(topic, key=key, value=payload, headers=headers)

def consume_one(consumer: Consumer) -> None:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        return
    carrier = {k: (v.decode("utf-8") if isinstance(v, bytes) else v)
               for k, v in (msg.headers() or [])}
    ctx = propagate.extract(carrier)                    # rebuilds the remote SpanContext
    with tracer.start_as_current_span(
        f"{msg.topic()} process", context=ctx, kind=SpanKind.CONSUMER
    ) as span:
        span.set_attribute("messaging.kafka.offset", msg.offset())
        span.set_attribute("messaging.kafka.partition", msg.partition())
        handle(msg.value())
```

Two subtleties a senior answer includes:

- **Batches need span links, not a parent.** A span can have exactly one parent, so when one `poll()` returns 500 records from 500 different traces you cannot parent the batch span to all of them. The OpenTelemetry messaging conventions therefore use **span links** as the default correlation mechanism between producer and consumer, with parent-child reserved for the single-message case:
  ```python
  links = [Link(trace.get_current_span(propagate.extract(c)).get_span_context())
           for c in carriers]
  with tracer.start_as_current_span("orders batch process",
                                    kind=SpanKind.CONSUMER, links=links):
      ...
  ```
- **Azure Service Bus does the same thing under a different property name.** The Azure SDKs write the trace context into the `Diagnostic-Id` application property, and Microsoft's own docs state the protocol is based on W3C Trace-Context and that `Diagnostic-Id` uses the `traceparent` format. If you hand-build messages (a Logic App, a legacy .NET publisher) you must set it yourself or the trace breaks at the queue. Same applies to an Event Grid CloudEvent — put it in the `traceparent` extension attribute.

**If they push back — "the message sat in the queue for four hours, doesn't that wreck the trace?"** — yes, and that is why the consumer's work is a *linked* span in its own trace rather than a child span inside a four-hour-long parent. Long-latency async hops are correlated, not nested; the queue wait itself is a metric (message age / `messaging.message.queued_duration`), not a span duration. Getting that distinction right is what stops a trace UI from showing a "four-hour request".

---

### Q100. You can't keep 100% of traces. What's your sampling strategy?
`[MEDIUM]`

> **Answer:** Head sampling for volume control and tail sampling for the traces that matter. Head sampling decides at the root span using a deterministic hash of the trace ID, so every service in the trace makes the same decision and you never get a half-sampled trace — that's `parentbased_traceidratio` at something like 5–10% for the noisy paths. But head sampling throws away errors at the same rate as successes, so I put an OpenTelemetry Collector in front of the backend running **tail sampling**: buffer the spans of a trace, and after the decision window keep 100% of traces that contain an error or exceed a latency threshold, plus a small probabilistic slice of the healthy ones.

The OTel SDK default is `parentbased_always_on` — 100%, which is fine in dev and a bill in prod. Set it via environment (injected by the chart, never hard-coded):

```yaml
env:
  - { name: OTEL_TRACES_SAMPLER,     value: "parentbased_traceidratio" }
  - { name: OTEL_TRACES_SAMPLER_ARG, value: "0.1" }         # 10% of root traces
  - { name: OTEL_PROPAGATORS,        value: "tracecontext,baggage" }   # this is also the default
```

Collector-side tail sampling — the config that keeps every failure:

```yaml
processors:
  tail_sampling:
    decision_wait: 10s          # buffer a trace this long before deciding (default 30s)
    num_traces: 50000           # in-memory trace cap (this is the default)
    expected_new_traces_per_sec: 2000
    policies:
      - name: all-errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces
        type: latency
        latency: { threshold_ms: 2000 }
      - name: settlement-flow-always      # business-critical path, keep everything
        type: string_attribute
        string_attribute: { key: messaging.destination.name, values: [settlement-instructions] }
      - name: baseline
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }
exporters:
  azuremonitor: {}
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling, batch]
      exporters: [azuremonitor]
```

The two costs of tail sampling you must name before they do: the collector has to hold **every span of a trace in memory until the decision window expires**, so it needs real memory and a `memory_limiter`; and all spans of one trace must reach the **same** collector instance, which means a load-balancing exporter keyed on trace ID in front of a collector pool, not a round-robin Service.

**If they push back — "doesn't sampling break your SLOs?"** — no, because SLOs are computed from **metrics, which are never sampled**. Request counts, error counts and latency histograms are 100% complete and cheap because they're pre-aggregated. Traces are for diagnosis after a metric has told you something is wrong. Anyone computing an error rate by counting sampled traces has built a lying dashboard.

---

### Q101. When should you *not* do microservices?
`[HARD]` — *answer this confidently; hedging here reads as inexperience*

> **Answer:** Most of the time, honestly. Microservices buy you independent deployability and independent scaling, and you pay for them in network failure modes, eventual consistency, distributed debugging and a platform team. If a client doesn't need the thing being bought, they still pay the price. I'd start with a well-modularised monolith and extract services when a specific, named pressure appears — and I'd say that to a client even when a microservices programme is the bigger engagement, because the alternative is a distributed monolith, which is strictly worse than the monolith they started with.

The four disqualifiers, in the order I check them:

1. **Team size and topology.** If one team owns everything, independent deployability buys nothing — you have coordination inside a standup already. The rough threshold is when you have enough people that a single deployment pipeline is a queue: roughly three or more stream-aligned teams. Below that, service boundaries just add ceremony. And Conway's law is not advice, it's a prediction: you will ship your org chart, so if the org isn't split by capability the services won't be either.
2. **Deployment and operational maturity.** Microservices raise the floor on everything else: you need automated CI/CD per service, IaC, centralised logging, distributed tracing, on-call with runbooks, and a container platform someone owns. If a client's current release is a manual Friday-night change window, giving them 30 services multiplies that pain by 30. Fix the deployment pipeline first — that is the prerequisite, not a parallel workstream.
3. **An unclear domain model.** Service boundaries are extremely expensive to move — a wrong boundary becomes a network call, a data migration and a versioned contract. In a green-field product where the domain is still being discovered, you cannot know where the boundaries are yet. Build the modular monolith with hard internal module boundaries (separate schemas, no cross-module table access, communication through in-process interfaces), learn where the seams actually are from a year of change requests, then extract along seams you've observed rather than seams you've guessed.
4. **No independent scaling or availability requirement.** If every component scales together and no component has a different availability target, the split earns nothing operationally.

**The line I actually say:** *"A distributed monolith is worse than a monolith on every axis. You've kept the lockstep releases, the shared database and the coupled domain model — and you've added network latency, partial failure, serialization, service discovery and a distributed debugging problem. The monolith at least had a stack trace."*

**If they push back — "so you're against microservices?"** — no, I'm against them as a default. The signals I *do* act on: one component needs to scale 50× independently of everything else; two parts of the system have genuinely different availability or compliance requirements (a public-facing quote API next to a batch NAV engine); teams are blocking each other's releases; or a component needs a different runtime entirely. Each of those is a reason to extract *that one thing* — which is the strangler fig in Q93, not a rewrite. Modular monolith first, extract on evidence, and keep the module boundaries clean enough that extraction is a refactor rather than an archaeology project.

---

## 17. Interviewer traps

Twelve places where the plausible answer is the wrong one. Each is phrased as the interviewer hears it.

**Trap 1 — the liveness probe that checks the database.**
*Most candidates say:* "Liveness hits `/health`, which verifies the database, cache and downstream API are reachable."
*The correct answer is:* liveness must check **only whether this process is wedged**, because a failing liveness probe **kills the container**. If liveness checks a shared dependency, one database blip restarts every pod in the fleet simultaneously — you converted a degraded dependency into a total outage, and the restart storm keeps the dependency down. Dependency checks belong in **readiness** (take me out of the load balancer, keep me alive) and in `/health/detail` for humans. My liveness endpoint returns 200 unconditionally unless an internal invariant is broken — a deadlocked event loop, an unrecoverable thread pool.

**Trap 2 — `:latest`.**
*Most candidates say:* "We deploy `myapp:latest` and Kubernetes pulls the new image."
*The correct answer is:* `latest` is a mutable tag, so two pods of the same Deployment can be running different code, and `kubectl rollout undo` rolls back to a manifest that resolves to the *same* mutable tag — you cannot actually roll back. It also silently changes `imagePullPolicy` behaviour: the default is `IfNotPresent`, except that a tag of `latest` (or no tag) defaults to `Always`. Deploy an immutable tag — ideally the digest, `myacr.azurecr.io/orders-api@sha256:…` — set by CI from the commit SHA. In GitOps that digest is what's in Git, and that's what makes the repo the real state of production.

**Trap 3 — "Secrets are encrypted."**
*Most candidates say:* "Sensitive values go in a Kubernetes Secret because Secrets are encrypted."
*The correct answer is:* they are **base64-encoded, not encrypted**. The Kubernetes docs are explicit: Secrets are by default stored **unencrypted** in etcd, anyone with API access or etcd access can read them, and anyone who can create a Pod in a namespace can read every Secret in that namespace — including indirectly, by creating a Deployment. You need at minimum encryption-at-rest via an `EncryptionConfiguration` (on AKS, KMS etcd encryption backed by Key Vault), tight RBAC on `get/list secrets`, and preferably no long-lived secret in the cluster at all — Workload Identity for Azure resources and the Secrets Store CSI driver for the rest.

**Trap 4 — no resource requests.**
*Most candidates say:* "We didn't set requests, we let it use what it needs."
*The correct answer is:* the **request is what the scheduler uses to place the pod**, so no request means the scheduler thinks the pod is free and packs it onto any node — then the node runs out of memory and the kubelet starts evicting. It also puts the pod in the `BestEffort` QoS class, which is the **first** thing killed under node pressure. Set requests from observed p95 usage; set a memory **limit** equal to the request for anything you care about (`Guaranteed` QoS, evicted last); set requests and limits on every container including sidecars, and enforce it with a `LimitRange` plus a policy engine so an unset request never merges.

**Trap 5 — CPU limits everywhere.**
*Most candidates say:* "We set CPU limits on everything so noisy neighbours can't hurt us."
*The correct answer is:* CPU is compressible and the limit is enforced by **CFS quota throttling** — when the container exhausts its quota inside the 100 ms period it is stopped until the next period, which shows up as sawtooth p99 latency on a service that is nowhere near its average limit. Requests already give you scheduling fairness and a guaranteed share under contention. My default is: **memory request = memory limit** (memory is incompressible; without a limit you take the node down), **CPU request set, CPU limit omitted** for latency-sensitive services, with limits only where you must cap a genuinely abusive batch workload. Diagnose it with `container_cpu_cfs_throttled_periods_total / container_cpu_cfs_periods_total`.

**Trap 6 — HPA on CPU for a queue consumer.**
*Most candidates say:* "The consumer autoscales on CPU at 70%."
*The correct answer is:* a consumer that is blocked waiting on a broker and on I/O has flat, low CPU whether the queue holds 10 messages or 10 million — CPU is not correlated with the thing you care about. Scale on **queue depth or consumer lag** with KEDA: `azure-servicebus` on `messageCount`, or `kafka` on `lagThreshold`. It also gets you **scale-to-zero**, which HPA alone cannot do (HPA's floor is `minReplicas: 1`). And remember the hard ceiling: for Kafka, useful parallelism stops at the partition count, so scaling to 50 replicas on a 12-partition topic gives you 38 idle pods holding no assignments. See [Messaging](03-messaging-and-event-streaming.md).

**Trap 7 — no PodDisruptionBudget.**
*Most candidates say:* "We run three replicas, so a node drain is fine."
*The correct answer is:* without a PDB, a **voluntary** disruption — a node drain during an AKS node-image upgrade, a cluster-autoscaler scale-down, a `kubectl drain` — can evict all three at once, because the eviction API has nothing telling it otherwise. A PDB is the only thing that makes the drain *wait*.
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: orders-api, namespace: integration }
spec:
  minAvailable: 2                      # or maxUnavailable: 1
  selector: { matchLabels: { app.kubernetes.io/name: orders-api } }
```
The inverse trap is just as bad: `minAvailable` equal to `replicas` means **no** pod can ever be evicted, and the node upgrade hangs forever. And a PDB does nothing for *involuntary* disruption — a node dying — that's what `topologySpreadConstraints` across zones is for.

**Trap 8 — no graceful shutdown on a consumer.**
*Most candidates say:* "Kubernetes sends SIGTERM and the pod exits cleanly."
*The correct answer is:* only if your process actually handles SIGTERM, and only if it finishes inside `terminationGracePeriodSeconds` (default **30**), after which it is SIGKILLed mid-message. For a queue consumer the correct shutdown is: on SIGTERM, **stop fetching new messages**, finish the in-flight ones, commit offsets / complete the messages, close the broker connection, then exit. A consumer killed mid-flight either loses the message (if it pre-committed) or redelivers it (if it didn't) — so the handler must be idempotent regardless. Set the grace period longer than your longest single message handler, and note that a shell-form `CMD` gives you `/bin/sh` as PID 1, which does not forward SIGTERM to your Python process at all.

**Trap 9 — `kubectl apply` from CI called GitOps.**
*Most candidates say:* "Our pipeline runs `kubectl apply -f` after the build, so we do GitOps."
*The correct answer is:* that's **CIOps** — push-based imperative deployment. GitOps has four properties none of which that has: the desired state is **declarative** and lives in Git; Git is the **single source of truth**; an in-cluster agent (Argo CD, Flux) **pulls** and applies it; and it **continuously reconciles**, so manual drift is detected and reverted. The practical differences: with `kubectl apply` from CI, someone who runs `kubectl edit` in prod stays edited forever and nobody knows; the CI runner needs cluster-admin credentials stored outside the cluster; and there is no answer to "what is running in prod right now" other than querying the cluster. With GitOps, the answer is a Git SHA. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

**Trap 10 — a Deployment for something that needs identity.**
*Most candidates say:* "It's a stateless container, so a Deployment."
*The correct answer is:* ask whether anything depends on *which* replica it is. Deployment pods get random name suffixes, are interchangeable, start and terminate in arbitrary order, and share a Service VIP. If the workload needs a **stable network identity** (a broker peer, a leader-elected coordinator, anything another system connects to by name), **stable per-pod storage** (a PVC that follows pod-3 across reschedules), or **ordered** rollout/scale-down, it needs a **StatefulSet** with a headless Service. The integration-shaped version of this trap: a scheduled job that must run exactly once cluster-wide is neither — that's a `CronJob` with `concurrencyPolicy: Forbid`, or a leader-elected singleton, not a Deployment with `replicas: 1` (which briefly runs two during a rolling update).

**Trap 11 — NetworkPolicy without an enforcing CNI.**
*Most candidates say:* "We applied default-deny NetworkPolicies, so the namespace is locked down."
*The correct answer is:* the API server **accepts and stores a NetworkPolicy regardless of whether anything enforces it**. The Kubernetes docs say it plainly: creating a NetworkPolicy without a controller that implements it has no effect, and POSTing it has no effect unless your networking solution supports network policy. So a `kubectl get netpol` that returns your policies is **not** evidence of enforcement. On AKS, network policy is **off unless you enable it**: `--network-policy azure|calico|cilium` at create time (or via `az aks update`). Microsoft now recommends **Cilium**; Azure NPM is retiring — 30 Sep 2026 for Windows nodes, 30 Sep 2028 for Linux. Evidence of enforcement is a test: two pods, apply the policy, prove the connection times out.

**Trap 12 — Ingress resource vs Ingress controller.**
*Most candidates say:* "I created an Ingress, so traffic will route."
*The correct answer is:* the **Ingress resource is only a routing rule** — a piece of declarative data. Nothing routes until an **Ingress controller** (ingress-nginx, AGIC, Traefik, Envoy Gateway) is running in the cluster, watching Ingress objects and programming an actual data plane. A cluster with no controller accepts the Ingress and gives you an object with an empty `.status.loadBalancer` forever. Corollary: `ingressClassName` decides *which* controller picks it up, so with two controllers installed, omitting it means either both claim it or neither does. Same shape as trap 11 and it's worth saying so out loud — *"Kubernetes is a declarative API; a resource with no controller behind it is a wish, not a behaviour"* — that one sentence tends to end the round well.

---

## 18. 30-second whiteboard versions

Literal scripts. Say them at this length, then stop and let them ask.

### (a) CrashLoopBackOff triage

> "CrashLoopBackOff isn't an error, it's a state — the kubelet is backing off restarts, starting at 100 milliseconds and doubling up to a 5-minute cap. So I ignore the phrase and go find the actual exit.
>
> First, `kubectl describe pod`: I read `Last State` for the **exit code** and `Reason`, and the Events at the bottom. Exit code 137 with reason OOMKilled means the memory limit was too low — bump the limit or fix the leak. Exit code 1 or 2 means the application itself threw. 127 means the command isn't in the image — usually a wrong ENTRYPOINT path or a missing shell in a distroless base.
>
> Second, `kubectl logs <pod> --previous` — the crashed container's logs, not the one that's currently starting. That's where the stack trace is.
>
> If the logs are empty it's failing before the app starts, so it's config or permissions: a Secret or ConfigMap that doesn't exist yet, a mount the non-root UID can't read, or a readiness endpoint on the wrong port. `kubectl get events --sort-by=.lastTimestamp -n <ns>` catches the mount and image-pull failures.
>
> Then I reproduce without the crash loop: `kubectl debug` an ephemeral container into the pod, or run the image with the entrypoint overridden. And I check whether it's actually a liveness probe *killing* a healthy process — if the probe's `initialDelaySeconds` is shorter than the app's startup time, it kills the container mid-boot forever. That's what `startupProbe` exists for."

Commands, in the order spoken:
```bash
kubectl describe pod orders-api-7d9f -n integration | sed -n '/Last State/,/Events/p'
kubectl logs orders-api-7d9f -n integration --previous --tail=200
kubectl get events -n integration --sort-by=.lastTimestamp | tail -30
kubectl debug -it orders-api-7d9f -n integration --image=busybox:1.36 --target=api
kubectl run tmp --rm -it --image=myacr.azurecr.io/orders-api:1.4.2 --command -- sh
```

### (b) How you autoscale an integration consumer

> "The mistake is scaling a consumer on CPU. A consumer blocked on a broker receive has flat CPU whether the queue is empty or has a million messages, so CPU tells you nothing about backlog. I scale on the backlog itself.
>
> I use KEDA. It runs a scaler that polls the queue — Service Bus `messageCount`, or Kafka consumer-group lag — and it creates and drives an HPA for me, so I get the standard autoscaling machinery with a queue-shaped metric. The trigger says something like: one replica per 500 messages of backlog, minimum zero, maximum twenty.
>
> Scale-to-zero is the reason I use KEDA rather than a raw HPA — HPA's floor is one replica, KEDA's ScaledObject can go to zero and wake on the first message, which matters a lot for the overnight batch queues that are idle 20 hours a day.
>
> Two ceilings I set deliberately. `maxReplicaCount` is bounded by the downstream, not the queue — if the consumer writes to a legacy SQL box that dies past 30 connections, scaling to 100 pods just moves the outage. And on Kafka, parallelism stops at the partition count: more consumers than partitions means idle pods holding no assignments.
>
> Then graceful shutdown, because scale-down evicts pods mid-message: SIGTERM stops the fetch loop, in-flight messages finish and complete, and the grace period is longer than the longest handler."

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: settlement-consumer, namespace: integration }
spec:
  scaleTargetRef: { name: settlement-consumer }
  minReplicaCount: 0
  maxReplicaCount: 20                 # bounded by the downstream, not the queue
  pollingInterval: 15
  cooldownPeriod: 300
  triggers:
    - type: azure-servicebus
      metadata:
        queueName: settlement-instructions
        messageCount: "500"           # target backlog per replica
        namespace: contoso-sb-prod
      authenticationRef: { name: sb-workload-identity }
```

### (c) The golden-chart platform story

> "The problem on a client platform isn't writing Kubernetes manifests — it's that thirty teams each write their own, slightly differently, and none of them have a PodDisruptionBudget or resource requests. So we don't ask teams to write manifests at all.
>
> We publish one **golden library chart** to the internal OCI registry, versioned semantically. It renders the whole standard shape from about fifteen lines of values: Deployment, Service, ServiceAccount with Workload Identity annotation, HPA or KEDA ScaledObject, PDB, NetworkPolicy, topology spread across zones, probes, resource requests, the OTLP endpoint and the standard labels. A service team's chart is a `Chart.yaml` that depends on it and a `values.yaml`.
>
> The guardrails are enforced twice — shift left and admission. In CI, `helm template` piped into a policy check, so a chart missing requests or running as root fails the PR. In the cluster, the same policies as a Kyverno or Gatekeeper admission policy, so nothing gets in around the pipeline. Same rules, two places, because CI is advisory and admission is authoritative.
>
> Delivery is GitOps: CI builds the image, signs it, scans it, and opens a PR that bumps a digest in the environment repo. Argo CD reconciles. Nobody has cluster credentials, prod state is a Git SHA, and drift reverts itself.
>
> The number I'd quote to a client is time-to-first-deploy for a new service — days of copy-pasted YAML down to about an hour — and the fact that raising the platform baseline is one chart version bump plus a dependency PR across every service, not thirty tickets."

---

## 19. Rapid fire (40)

Forty one-liners across the whole file. Cover the answer, say it, check.

| # | Question | Answer |
|---|---|---|
| 1 | **`EXPOSE` vs `-p/--publish`?** `EY-logged` | `EXPOSE` is documentation/metadata in the image — it publishes nothing. `-p 8080:80` actually maps a host port to a container port at runtime. `-P` publishes every `EXPOSE`d port to a random high host port. In Kubernetes both are irrelevant: `containerPort` is also informational and the Service does the mapping. |
| 2 | **How does HPA work?** `EY-logged` | A controller loop (default every **15s**) reads a metric per pod, computes `desiredReplicas = ceil(currentReplicas × currentMetric / targetMetric)`, and skips the change if the ratio is within the default **0.1** tolerance. Scale-down has a default **300s** stabilization window; the default policies allow 100% or 4 pods per 15s. |
| 3 | **What are the objects in a Kubernetes Service?** `EY-logged` | Types: `ClusterIP` (default, internal VIP), `NodePort` (a port in **30000–32767** on every node), `LoadBalancer` (cloud LB → NodePort → pods), `ExternalName` (a CNAME, no proxying). Plus **headless** (`clusterIP: None`, DNS returns pod IPs) and the backing **EndpointSlice** objects. |
| 4 | **`kubectl apply` vs `create`?** | `create` is imperative and fails if the object exists; `apply` is declarative, creates or patches, and records intent (client-side in the last-applied annotation, or field ownership with server-side apply). |
| 5 | **Deployment vs StatefulSet?** | Deployment = interchangeable pods, random names, parallel ordering. StatefulSet = stable ordinal names, stable per-pod PVCs via `volumeClaimTemplates`, ordered rollout, headless Service for per-pod DNS. |
| 6 | **What is a ReplicaSet for?** | It keeps N pods running. You don't write one — a Deployment creates one per pod-template revision, which is what makes `rollout undo` work. |
| 7 | **`maxSurge` and `maxUnavailable` defaults?** | Both **25%** for a RollingUpdate Deployment. `maxUnavailable: 0` gives a strictly additive rollout (needs spare capacity); both zero is invalid. |
| 8 | **Liveness vs readiness vs startup?** | Liveness failing **restarts** the container; readiness failing **removes it from Service endpoints**; startup **suspends the other two** until the app has booted, which is how you support slow starts without a lax liveness threshold. |
| 9 | **What are the QoS classes?** | `Guaranteed` (every container has requests == limits for cpu and memory), `Burstable` (requests set, below limits), `BestEffort` (nothing set). Eviction order under node pressure is BestEffort → Burstable → Guaranteed. |
| 10 | **Exit code 137?** | 128 + 9 = SIGKILL. Almost always OOMKilled (check `Last State: Reason`) or a SIGTERM that outlived the grace period. |
| 11 | **Default `terminationGracePeriodSeconds`?** | **30**. SIGTERM, then SIGKILL after that. Raise it above your longest in-flight handler for consumers. |
| 12 | **What runs first, `preStop` or SIGTERM?** | `preStop` — it runs to completion *before* SIGTERM is sent, and it consumes the same grace period. Use it for a sleep so the endpoint removal propagates before the process stops accepting. |
| 13 | **ConfigMap vs Secret?** | Same API shape; Secret is base64, has type metadata, is not written to disk on the node in plaintext outside tmpfs, and is what RBAC and audit tooling watch. Neither is encrypted at rest by default. |
| 14 | **Does a ConfigMap change restart the pod?** | No. Mounted-volume keys update in place (eventually, via kubelet sync); `envFrom` values do **not** update at all. Force a rollout with a checksum annotation on the pod template. |
| 15 | **What is Workload Identity on AKS?** | The pod's ServiceAccount is federated to a Microsoft Entra app/managed identity via OIDC; the SDK exchanges a projected SA token for an Entra token. No secret in the cluster, and it replaces the deprecated pod-identity model. |
| 16 | **Role vs ClusterRole?** | Role is namespaced; ClusterRole is cluster-wide and also the only way to grant on cluster-scoped resources (nodes, PVs) or across all namespaces. A ClusterRole bound with a **RoleBinding** applies only inside that namespace — the reusable-permission-set trick. |
| 17 | **HPA vs VPA vs Cluster Autoscaler?** | HPA changes replica *count*; VPA changes per-pod *requests/limits* (and evicts to apply them); Cluster Autoscaler changes *node count* when pods are unschedulable. Don't run HPA and VPA on the same CPU metric. |
| 18 | **Why KEDA over HPA?** | Event-source-shaped metrics (queue depth, consumer lag, cron) and **scale-to-zero**. KEDA creates and manages the HPA underneath. |
| 19 | **What is a PodDisruptionBudget?** | A floor on availability during **voluntary** disruptions — drains and evictions block rather than violate it. It does nothing for node failure. |
| 20 | **taints/tolerations vs nodeSelector vs affinity?** | Taints repel pods from nodes (node-side, opt-out); tolerations let a pod ignore a taint; `nodeSelector`/`nodeAffinity` attract pods to nodes (pod-side, opt-in); `podAntiAffinity` spreads pods apart from each other. |
| 21 | **`topologySpreadConstraints` in one line?** | Even distribution of a pod set across a topology key (zone, node) with `maxSkew`, and `whenUnsatisfiable: DoNotSchedule` vs `ScheduleAnyway` decides whether it's a hard rule. |
| 22 | **Does a NetworkPolicy work by default?** | No — it needs a CNI that enforces it; the API accepts it either way. On AKS, enable Cilium/Azure NPM/Calico explicitly. |
| 23 | **Default NetworkPolicy behaviour?** | Pods are non-isolated: all ingress and egress allowed. The moment any policy selects a pod, that *direction* becomes deny-by-default and only listed traffic is allowed. |
| 24 | **Ingress vs Gateway API?** | Ingress is one object with vendor annotations; Gateway API splits it by role — infra team owns `GatewayClass`/`Gateway`, app teams own namespaced `HTTPRoute`s — and moves the annotations into typed fields. |
| 25 | **What is a headless Service for?** | `clusterIP: None` — DNS returns pod IPs instead of a VIP. Used for StatefulSet per-pod DNS and for clients that want to do their own load balancing (gRPC, brokers). |
| 26 | **`kubectl rollout` commands worth knowing?** | `status` (waits for completion — use it as the CI gate), `history`, `undo --to-revision=N`, `restart` (bumps a pod-template annotation to force new pods without changing the image). |
| 27 | **What does Helm actually store in the cluster?** | A release **Secret** per revision (type `helm.sh/release.v1`), holding a gzipped, base64-encoded manifest and values. That's what `helm rollback` reads. |
| 28 | **`helm upgrade --install --atomic --wait`?** | `--install` creates if absent; `--wait` blocks until resources are ready; `--atomic` implies `--wait` and **rolls back automatically** on failure. Set `--timeout` to something longer than your slowest probe. |
| 29 | **Helm library chart vs subchart?** | A **library** chart (`type: library`) ships only reusable named templates and installs nothing itself — the mechanism behind a golden chart. A subchart is a real chart pulled in as a dependency and deployed with the parent. |
| 30 | **Why is `helm template` in CI?** | It renders offline so you can run policy checks (kubeconform, Kyverno CLI, conftest) on the actual YAML before merge, and it's how GitOps repos get rendered manifests. |
| 31 | **Docker `CMD` vs `ENTRYPOINT`?** | `ENTRYPOINT` is the executable; `CMD` is the default arguments to it (and is fully replaced by anything you pass on `docker run`). Always use **exec form** (`["python","-m","app"]`) so your process is PID 1 and receives signals. |
| 32 | **Multi-stage build in one sentence?** | Build toolchain and dev dependencies live in an earlier stage; the final stage copies only the artefact, so compilers, headers and build secrets never ship. |
| 33 | **How do you avoid baking a secret into an image?** | BuildKit secret mounts: `RUN --mount=type=secret,id=pip_token …`, or a short-lived token via `--build-arg` in a *discarded* stage. Never `ENV`/`ARG` in the final stage — both are visible in `docker history`. |
| 34 | **Where do you scan images?** | Three places: on PR (Trivy/Grype on the built image, fail on fixable HIGH/CRITICAL), in the registry (ACR/Defender continuous rescan, because new CVEs land against old images), and at admission (signature + policy verification). |
| 35 | **Distributed transaction across services?** | Don't — saga of local transactions plus compensations, driven by an outbox, with idempotent steps. 2PC needs a lock-holding coordinator and most modern participants don't offer one. |
| 36 | **Choreography or orchestration?** | Choreography for 2–3 step, high-throughput, loosely coupled flows. Orchestration once there are more steps, real compensations, or an auditor who will ask "where is this instruction now". |
| 37 | **Database-per-service — how do you query across?** | API composition (parallel fan-out, small and bounded) or a CQRS read model fed by events (high-volume, filter/sort/paginate). Never read another service's tables directly. |
| 38 | **Strangler fig in one sentence?** | Put a routing facade in front of the legacy system, move one capability at a time behind it with a reversible routing predicate, and delete the old code path each time — never a big-bang rewrite. |
| 39 | **API gateway vs service mesh?** | Gateway = north-south, external caller auth, throttling, versioning, developer portal. Mesh = east-west, workload-identity mTLS, retries, traffic splitting, L7 telemetry with no code change. Most platforms run both. |
| 40 | **How does a trace survive a queue hop?** | The producer injects `traceparent` into message headers (Service Bus SDKs use the `Diagnostic-Id` application property in the same W3C format) and the consumer extracts it. Batches use **span links**, not a parent, because a span can only have one parent. |
