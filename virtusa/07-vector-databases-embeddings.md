# Vector Databases, Embeddings & Semantic Search

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

| § | Section | Qs |
|---|---------|----|
| 1 | [Fundamentals & Embedding Models](#1-fundamentals--embedding-models) | Q1–Q6 |
| 2 | [Similarity Metrics & Normalization](#2-similarity-metrics--normalization) | Q7–Q9 |
| 3 | [ANN Algorithms In Depth](#3-ann-algorithms-in-depth) | Q10–Q17 |
| 4 | [Quantization, Memory & Build Time](#4-quantization-memory--build-time) | Q18–Q21 |
| 5 | [Filtering, Hybrid & Sparse](#5-filtering-hybrid--sparse) | Q22–Q26 |
| 6 | [Production Operations](#6-production-operations) | Q27–Q32 |
| 7 | [Product Deep-Dives](#7-product-deep-dives) | Q33–Q38 |
| 8 | [Evaluation, Cost & Sizing](#8-evaluation-cost--sizing) | Q39–Q42 |
| — | [Red Flags / Do NOT say](#red-flags--do-not-say) | — |
| — | [Rapid-Fire (last 10 min before you walk in)](#rapid-fire-last-10-min-before-you-walk-in) | 24 |

---

## 1. Fundamentals & Embedding Models

### Q1. What does a vector database do that Postgres or Mongo can't?
`[EASY]`

**Answer:** It indexes high-dimensional float arrays so you can retrieve the *approximate* nearest neighbours of a query vector in sub-linear time. A normal DB indexes for **exact equality / range / prefix** on scalars (B-tree, hash) — those structures collapse in high dimensions ("curse of dimensionality": at d=1536 every point is roughly equidistant, so space-partitioning trees like KD-tree degrade to full scan).

Three things a vector DB gives you:

| Capability | Why a normal DB struggles |
|---|---|
| ANN index (HNSW/IVF/DiskANN) | B-tree cannot order 1536-D space; brute force is O(N·d) |
| Distance-aware ranking (top-k by cosine/L2) | SQL can compute it but must scan every row |
| Vector-aware ops: quantization, filtered graph traversal, rescoring | Not in a generic storage engine |

**Gotcha:** Postgres *can* do this — `pgvector` bolts an HNSW index onto Postgres. So the honest answer is "a vector DB is a specialised index + serving layer, and you only need a dedicated one when scale, filtering complexity, or ops demands exceed what pgvector on your existing Postgres can do."

**Follow-up they will ask:** *"So when do you NOT need a vector DB?"* → Under ~100k vectors, an in-memory NumPy matrix or FAISS flat index rebuilt on deploy is faster, cheaper, and exact. Don't run infrastructure you don't need.

---

### Q2. What is an embedding? What does "1536 dimensions" actually mean?
`[EASY]`

**Answer:** An embedding is a fixed-length float vector produced by a neural encoder such that **semantic similarity ≈ geometric proximity**. 1536 dimensions = the model's output width; each dimension is a learned latent feature, individually uninterpretable. Only relative distances between vectors in the *same* model's space are meaningful.

Key properties to state out loud:
- **Same model, same version, same preprocessing** — vectors from two different models are not comparable, ever.
- Effectively deterministic for a given input (no sampling/temperature) — though hosted APIs can differ in the last few decimal places across calls because of batching/GPU float non-determinism, and providers can silently ship model updates, so pin versions and never assume bit-identical vectors.
- Bounded input: OpenAI embedding models take max **8,191 tokens**; BERT-based open models (BGE/E5 v1.5) usually **512 tokens** — anything longer is silently truncated, which is a classic silent-quality bug.
- Dimensions ≠ quality. `text-embedding-3-large` truncated to 256 dims still beats the older 1536-dim `ada-002` on MTEB.

---

### Q3. Which embedding model would you pick, and defend it.
`[MEDIUM]`

**Answer:** Default to **`text-embedding-3-small` at 1536 dims** for an Azure-OpenAI enterprise build: cheapest credible option ($0.02 / 1M tokens), 8k context, already available in Azure OpenAI so no extra vendor review. Move to **`text-embedding-3-large`** only if a golden-set eval shows a real recall lift; move to a **self-hosted BGE/E5** if data cannot leave the network or embedding volume makes API cost dominate.

| Model | Dims | Max tokens | Notes |
|---|---|---|---|
| `text-embedding-3-small` | 1536 (truncatable) | 8191 | ~$0.02/1M tok. Default choice. Available on Azure OpenAI. |
| `text-embedding-3-large` | 3072 (truncatable) | 8191 | ~$0.13/1M tok. Best OpenAI quality; 2× storage at full width. |
| `text-embedding-ada-002` | 1536 (fixed) | 8191 | Legacy. Worse and pricier than 3-small. Migrate off it. |
| Cohere `embed-english-v3.0` | 1024 | 512 | Native int8/binary output; `input_type` asymmetric prefixes. On Azure/AWS marketplaces. |
| `BAAI/bge-large-en-v1.5` | 1024 | 512 | Strong open model; needs a query instruction prefix. |
| `BAAI/bge-m3` | 1024 | 8192 | Multilingual + emits dense **and** sparse **and** ColBERT vectors — one model for hybrid. |
| `intfloat/multilingual-e5-large` | 1024 | 512 | Needs `"query: "` / `"passage: "` prefixes. Good for Indic + EN mix. |
| `Alibaba-NLP/gte-large-en-v1.5` | 1024 | 8192 | Long-context open model, no prefix needed. |
| `nomic-embed-text-v1.5` | 768 (Matryoshka) | 8192 | Open, task prefixes, truncatable. |

**Gotcha:** Cost of embedding is almost never the bottleneck at query time — you embed the corpus **once** and one short query per request. The recurring cost is *storage + RAM*, which scales with dimensions. That's the real reason to care about 768 vs 3072.

**Follow-up they will ask:** *"How would you actually decide?"* → Build a 200-query golden set from real user questions with labelled relevant chunks, then compare Recall@10 and nDCG@10 across 3 candidate models on the *same* chunks. Pick the cheapest model within 1–2 points of the best.

---

### Q4. Explain Matryoshka embeddings and the `dimensions` parameter.
`[MEDIUM]`

**Answer:** Matryoshka Representation Learning (MRL) trains the model so that the **first k dimensions of the vector are themselves a valid embedding**. So you can truncate 3072 → 512 and keep most of the quality, cutting storage/RAM by 6×. OpenAI's `text-embedding-3-*` models are MRL-trained and expose this via the `dimensions` API parameter.

**Code:**
```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment
# Azure equivalent (openai >= 1.x):
#   from openai import AzureOpenAI
#   client = AzureOpenAI(azure_endpoint="https://<res>.openai.azure.com",
#                        api_version="2024-10-21",
#                        azure_ad_token_provider=token_provider)  # or api_key=...
#   ...and on Azure `model=` is the *deployment* name, not the model name.

resp = client.embeddings.create(
    model="text-embedding-3-large",
    input=["quarterly revenue recognition policy"],
    dimensions=512,          # Matryoshka truncation, server-side + re-normalized
)
vec = resp.data[0].embedding
print(len(vec))              # 512
```

**Gotcha:** If you truncate **client-side** (`vec[:512]`) the vector is no longer unit-norm, so cosine and dot product diverge. Re-normalize:
```python
import numpy as np
v = np.asarray(vec[:512], dtype="float32")
v /= np.linalg.norm(v)
```
The API's `dimensions` parameter normalizes for you; manual slicing does not.

**Follow-up they will ask:** *"How far can you truncate?"* → Measure, don't guess. Typical published behaviour: 3-large at 256 dims still outperforms full 1536-dim ada-002. In my sizing I'd test 1536 → 768 → 512 and stop at the last one within ~1 point of Recall@10.

---

### Q5. Some models need instruction prefixes. What are they and what breaks if you skip them?
`[MEDIUM]`

**Answer:** E5, BGE, GTE-instruct and Nomic are trained with **asymmetric prefixes** that tell the model whether the text is a short query or a long passage. Skipping them costs real recall (commonly 3–8 points on Recall@10) because the query and passage land in slightly different regions of the space.

| Family | Query prefix | Document prefix |
|---|---|---|
| E5 (`e5-*`, `multilingual-e5-*`) | `"query: "` | `"passage: "` |
| BGE v1.5 (English) | `"Represent this sentence for searching relevant passages: "` | *(none)* |
| Nomic v1.5 | `"search_query: "` | `"search_document: "` |
| Cohere v3 | `input_type="search_query"` | `input_type="search_document"` |
| OpenAI `text-embedding-3-*` | *(none — symmetric)* | *(none)* |

**Code:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-large")
doc_vecs = model.encode([f"passage: {c}" for c in chunks], normalize_embeddings=True)
q_vec    = model.encode("query: what is the refund window?", normalize_embeddings=True)
```

**Gotcha:** The failure is *silent* — search still returns results, just worse ones. This is why every ingest job must record `embedding_model`, `model_version` and `prefix_scheme` in metadata, and why query-time embedding must go through the **same helper function** as ingest-time.

---

### Q6. Symmetric vs asymmetric search — why does it matter?
`[MEDIUM]`

**Answer:** *Symmetric* = both sides are the same kind of text (dedup, "find similar tickets"). *Asymmetric* = short question vs long passage (RAG). RAG is asymmetric, so use a model trained for retrieval with the right query/document treatment, rather than a general-purpose sentence-similarity model (`all-MiniLM-L6-v2` is the usual default people reach for; it is fine as a cheap baseline but is tuned for symmetric STS-style similarity and is beaten comfortably by BGE/E5/GTE on asymmetric retrieval benchmarks).

Practical consequences:
- Use **retrieval**-tuned models (BGE/E5/GTE/OpenAI-3) for RAG, not STS models.
- Consider **HyDE** (embed a hypothetical answer generated by the LLM instead of the raw question) to close the query/document asymmetry gap when queries are terse.
- Consider embedding a **chunk + its context header** (doc title, section path) on the document side, which pulls short chunks nearer to natural-language questions.

---

## 2. Similarity Metrics & Normalization

### Q7. Cosine vs dot product vs L2 — when do you use each?
`[MEDIUM]`

**Answer:** **Cosine** for text retrieval (default — it ignores magnitude, which for text encodes length/frequency artefacts rather than meaning). **Dot product** when the model is explicitly trained for it or when magnitude carries signal (some recsys / late-interaction models). **L2 (Euclidean)** for image/geometric embeddings and for models trained with an L2 objective.

The identity to have on the whiteboard:

```
cos(a,b) = (a·b) / (‖a‖ ‖b‖)

If ‖a‖ = ‖b‖ = 1  (unit-normalized):
    a·b        = cos(a,b)
    ‖a-b‖²     = 2 - 2·cos(a,b)
```

So **on normalized vectors, all three metrics produce the identical top-k ranking** — only the reported score differs. Dot product is then the cheapest (no sqrt, no divide), which is why FAISS `METRIC_INNER_PRODUCT` on normalized vectors is the standard fast path.

| Metric | Range | Use when | Cost |
|---|---|---|---|
| Cosine | [-1, 1] | Text, default | division per compare (or free if pre-normalized) |
| Dot / inner product | unbounded | Pre-normalized data; magnitude-aware models | cheapest |
| L2 / Euclidean | [0, ∞) | Image/geometric embeddings | sqrt (often skipped, ranks by L2²) |

**Follow-up they will ask:** *"Then why does every DB offer all three?"* → Because not everyone normalizes, and because index build (HNSW graph construction, IVF k-means) is metric-specific — the graph you build for L2 is not the graph you build for inner product.

---

### Q8. Do you have to normalize? What breaks if you don't?
`[MEDIUM]`

**Answer:** If you configure **dot product** on un-normalized vectors, long documents win regardless of relevance — magnitude dominates the score. If you configure **cosine**, normalization is done for you (or is a no-op), so nothing breaks but you pay a division per comparison.

Rules I follow:
1. Normalize once at ingest (`v /= ‖v‖`), store unit vectors, configure the index for **inner product / dot**. Fastest and safest.
2. OpenAI `text-embedding-*` returns **already unit-norm** vectors — verify with `np.linalg.norm(v) ≈ 1.0` rather than assuming.
3. Any client-side slicing (Matryoshka), averaging of chunk vectors, or arithmetic on vectors **destroys** unit norm. Re-normalize after.
4. Never mix normalized and un-normalized vectors in one index.

**Code:**
```python
import numpy as np

def l2_normalize(x: np.ndarray) -> np.ndarray:
    """Row-wise unit normalization, safe against zero vectors."""
    x = np.asarray(x, dtype="float32")
    if x.ndim == 1:
        x = x[None, :]
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    np.maximum(norms, 1e-12, out=norms)
    return x / norms
```

---

### Q9. Two unrelated sentences score 0.78 cosine. Is the model broken? Can I threshold on the score?
`[MEDIUM]`

**Answer:** Not broken — **absolute cosine values are model-specific and are not calibrated probabilities.** Embedding spaces are anisotropic: vectors occupy a narrow cone, so the baseline similarity between two *random* English sentences is model-dependent and often surprisingly high. Approximate, and worth measuring yourself rather than quoting:

| Model | Typical unrelated-pair cosine |
|---|---|
| `text-embedding-ada-002` | ~0.7–0.8 (notoriously compressed range) |
| `BAAI/bge-*-v1.5` | ~0.6–0.7 — BAAI documents that BGE's similarity distribution sits roughly in [0.6, 1] |
| `intfloat/e5-*` | ~0.7–0.8 with the correct prefixes |
| `text-embedding-3-small/large` | noticeably wider spread; unrelated pairs commonly land ~0.1–0.3 |

So a hard threshold like `score > 0.75` means "very relevant" on one model and "completely unrelated" on another. It will not transfer across models, and often not even across query types on the same model.

What to do instead:
- **Rank, don't threshold.** Take top-k, then filter with a *relative* rule (e.g. drop anything below `0.85 × top_score`).
- **Calibrate empirically** — sample 1,000 random query/chunk pairs, take the 99th percentile of the negative distribution, and use that as your floor. Re-calibrate on every model change.
- **Use a cross-encoder reranker** for a genuinely calibrated relevance score (BGE-reranker, Cohere Rerank, Azure AI Search semantic ranker) and threshold on *that*.

**Gotcha:** Hard-coding a cosine threshold and then swapping the embedding model is one of the most common silent RAG regressions in production. The threshold must be part of the model version bundle.

---

## 3. ANN Algorithms In Depth

### Q10. Why approximate at all? Show me exact top-k and its cost.
`[EASY]`

**Answer:** Exact (flat / brute-force) search is O(N·d) per query. At N=1M, d=1536 that's ~1.5 billion multiply-adds per query — roughly 100–500 ms single-threaded, ~6 GB scanned from RAM. ANN gets you 95–99% of the same results in 1–5 ms by touching only ~0.1% of the vectors. You trade **recall** for **latency and memory**.

Flat is still the right answer when N < ~50k, when you need 100% recall (compliance, dedup), or as the **ground-truth oracle** for measuring your ANN index's recall.

**Code — from-scratch cosine top-k (classic whiteboard ask):**
```python
import heapq
import numpy as np


def cosine_top_k_numpy(query: np.ndarray, matrix: np.ndarray, k: int = 5):
    """matrix: (N, d) rows already L2-normalized. query: (d,) normalized.
    Returns list[(index, score)] sorted desc. O(N*d) time, O(N) extra space."""
    scores = matrix @ query                      # (N,) dot == cosine when normalized
    k = min(k, scores.shape[0])
    idx = np.argpartition(-scores, k - 1)[:k]    # O(N) select, beats full O(N log N) sort
    idx = idx[np.argsort(-scores[idx])]          # sort only the k survivors
    return [(int(i), float(scores[i])) for i in idx]


def cosine_top_k_pure_python(query, docs, k=5):
    """No numpy. docs: list[list[float]] (not necessarily normalized).
    Min-heap of size k -> O(N*d + N log k)."""
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    qn = dot(query, query) ** 0.5 or 1e-12
    heap: list[tuple[float, int]] = []
    for i, d in enumerate(docs):
        dn = dot(d, d) ** 0.5 or 1e-12
        score = dot(query, d) / (qn * dn)
        if len(heap) < k:
            heapq.heappush(heap, (score, i))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, i))
    return [(i, s) for s, i in sorted(heap, reverse=True)]
```

**Gotcha:** Say "`np.argpartition` is O(N), a full `argsort` is O(N log N)" — interviewers listen for that.

---

### Q11. Explain HNSW as if I've never heard of it.
`[MEDIUM]`

**Answer:** HNSW = Hierarchical Navigable Small World. It's a **multi-layer proximity graph** — think skip-list generalised to metric space.

- Every vector is a node. Each node is assigned a maximum layer by an exponentially decaying random draw, so layer 0 holds all N nodes, layer 1 holds ~N/M, layer 2 ~N/M², etc.
- Each layer is a graph where nodes are linked to their approximate nearest neighbours.
- **Search:** start at the single entry point on the top layer, greedily walk to the neighbour closest to the query, descend a layer when you can't improve, repeat. At layer 0 run a best-first search keeping a candidate list of size `ef` and return the best k.
- Upper layers = long-range "highways" that get you into the right neighbourhood in a few hops; layer 0 = fine-grained local search.

Complexity: search visits **O(log N)** hops/nodes (empirical, not a proven worst-case bound — the greedy walk can still get stuck, which is why `ef` exists). In practice ~1 ms, and single-digit ms at high `ef`, for 1M × 768 at recall ≈0.95 single-threaded — see the measured table in Q15.

Why it won: highest recall-per-millisecond of any in-memory method, supports incremental inserts (no training step), and is simple to operate. Cost: it's a **RAM hog** and deletes are awkward.

---

### Q12. HNSW knobs: `M`, `ef_construction`, `ef_search`. What does each do to recall, latency and memory?
`[HARD]`

**Answer:**

| Knob | What it is | ↑ Recall | ↑ Query latency | ↑ Memory | ↑ Build time | Changeable after build? |
|---|---|---|---|---|---|---|
| `M` | Max bidirectional links per node per layer (layer 0 gets 2·M) | Yes, strongly | Slightly (more edges to scan) | **Yes, linearly** | Yes | **No — requires rebuild** |
| `ef_construction` | Candidate list size while inserting | Yes (better graph) | No | No | **Yes, strongly** | **No — requires rebuild** |
| `ef_search` | Candidate list size at query time | Yes, strongly | **Yes, roughly linearly** | No (transient) | No | **Yes — per query** |

Practical defaults and ranges:
- `M`: 16 is the standard default. 8–12 for low-dim (≤384) or memory-tight; 32–64 for high-dim (1536+) or when you need recall > 0.99. Above 64 you get diminishing returns and a memory blowout.
- `ef_construction`: 100–200 typical; 400+ for high-recall/high-dim. It is a *build-time-only* cost — spend here, it's free at query time.
- `ef_search`: must be ≥ k. Start at 64–128. **This is your production tuning dial** — you can raise it for a "high accuracy" query mode and lower it under load shedding, with no reindex.

Product defaults worth quoting: pgvector `m=16, ef_construction=64, hnsw.ef_search=40`; Qdrant `m=16, ef_construct=100`; Azure AI Search `m=4, efConstruction=400, efSearch=500`.

**Gotcha:** The classic production bug is `ef_search < k` (e.g. asking for top-50 with `ef=40`) — you get silently degraded or short result sets. Also: raising `M` after the fact does nothing; you must rebuild.

**Follow-up they will ask:** *"Recall is 0.82 and you need 0.95. What do you change first?"* → `ef_search` — it's free, instant, and reversible. Measure the latency cost. Only if latency blows past SLO do you rebuild with a higher `M`/`ef_construction`.

---

### Q13. Explain IVF and IVF-PQ. What are `nlist` and `nprobe`?
`[HARD]`

**Answer:** **IVF (Inverted File)** partitions the space with k-means into `nlist` Voronoi cells, each with a centroid. At query time you compare the query to the `nlist` centroids, pick the closest `nprobe` cells, and scan only the vectors inside them. You touch roughly `N · nprobe/nlist` vectors instead of N.

- `nlist` — number of clusters. Rule of thumb `4·√N` to `16·√N` (FAISS guidance: ~4096 for 1M, 65536 for 10M). Needs training data: budget **≥ 39 and ideally 100–256 training vectors per centroid**, or k-means produces garbage clusters.
- `nprobe` — cells scanned per query. This is the recall/latency dial, exactly like `ef_search`. `nprobe = nlist` degenerates to brute force. Typical 8–64.

**IVF-PQ** adds **Product Quantization** to compress the vectors inside each cell:
- Split the d-dim vector into `m` sub-vectors of length d/m (d must be divisible by m).
- Run k-means with 256 centroids in each sub-space → each sub-vector becomes 1 byte (`nbits=8`).
- A vector becomes **m bytes**. For d=1536, m=64 → 64 bytes vs 6,144 bytes = **96× compression**.
- Distances are computed with precomputed lookup tables (ADC — asymmetric distance computation), so it's fast as well as small.
- **OPQ** prepends a learned rotation that decorrelates dimensions before splitting — usually a couple of recall points for free.

| | HNSW | IVF-Flat | IVF-PQ |
|---|---|---|---|
| Needs training pass | No | Yes (k-means) | Yes (k-means + PQ codebooks) |
| Memory (1M × 1536) | ~6.3 GB | ~6.2 GB | ~0.07 GB at m=64 |
| Recall @ tuned | 0.95–0.99 | 0.95–0.99 | 0.7–0.9 (0.95+ with rescoring) |
| Incremental insert | Cheap | Cheap (drifts over time) | Cheap (drifts) |
| Best for | ≤ ~50M in RAM | Mid-size, cheap build | Huge N, RAM-constrained |

**Gotcha:** IVF quality **decays as you insert** — the centroids were fit on the original distribution. After significant drift or growth you must retrain. HNSW does not have this problem. That single fact is why most modern DBs default to HNSW.

---

### Q14. ScaNN, DiskANN, LSH — when would you reach for these?
`[HARD]`

**Answer:**

- **ScaNN (Google)** — partitioning + *anisotropic vector quantization*: the quantization loss is weighted to preserve the component of the error that is parallel to the vector, because that's what distorts the inner product for high-scoring neighbours. Then a reordering/rescoring stage on full vectors. Consistently top of ann-benchmarks for recall-per-QPS. Reach for it when you're on GCP (it powers Vertex AI Vector Search) or when you're running an offline benchmark and want the ceiling.
- **DiskANN / Vamana (Microsoft)** — a single flat graph designed so the neighbour lists live on **SSD** while a compressed (PQ) copy of the vectors stays in RAM to guide the traversal. Serves billions of vectors from one node at ~5–10 ms. Reach for it when the corpus doesn't fit in RAM and you refuse to shard. Shipped in **pgvectorscale (StreamingDiskANN)**, Azure Cosmos DB, and Milvus.
- **LSH (Locality-Sensitive Hashing)** — random hyperplane projections; vectors that hash to the same bucket are probably close. Historically important, but it needs many hash tables for decent recall and loses badly to graph methods on recall-per-byte. Still the right tool for **near-duplicate detection at scale** (MinHash/SimHash over Jaccard), not for semantic top-k.
- **Flat / brute force** — always your recall oracle, and genuinely optimal below ~50k vectors.

**Follow-up they will ask:** *"Which would you pick for 500M vectors on a budget?"* → DiskANN-style (pgvectorscale or Milvus DiskANN) with PQ in RAM and full vectors on NVMe, plus rescoring. Beats sharding 500M vectors of HNSW across a fleet of 64 GB nodes on cost by an order of magnitude.

---

### Q15. Give me the recall / latency / memory tradeoff, concretely.
`[HARD]`

**Answer:** Reference workload: **1M vectors × 768 dims, k=10, single node, in-memory, one thread.** Numbers are the right order of magnitude, not a benchmark.

| Index | Recall@10 | p50 latency | RAM | Build time | Note |
|---|---|---|---|---|---|
| Flat (exact) | 1.00 | ~80–150 ms | 3.1 GB | 0 | Oracle |
| HNSW M=8, ef=32 | ~0.85 | ~0.4 ms | 3.2 GB | ~3 min | Too lossy for RAG |
| HNSW M=16, ef=64 | ~0.94 | ~0.9 ms | 3.2 GB | ~6 min | **Sane default** |
| HNSW M=32, ef=128 | ~0.98 | ~2 ms | 3.4 GB | ~15 min | High-accuracy tier |
| HNSW M=32, ef=512 | ~0.995 | ~7 ms | 3.4 GB | ~15 min | Diminishing returns |
| IVF4096, nprobe=8 | ~0.85 | ~1.5 ms | 3.1 GB | ~2 min | Cheap build |
| IVF4096, nprobe=64 | ~0.97 | ~8 ms | 3.1 GB | ~2 min | |
| IVF4096, PQ96 | ~0.75 | ~0.6 ms | 0.1 GB | ~5 min | 32× smaller |
| IVF4096, PQ96 + rescore ×4 | ~0.93 | ~1.5 ms | 0.1 GB RAM + 3.1 GB SSD | ~5 min | Best $/recall |
| HNSW M=16 + int8 SQ + rescore | ~0.97 | ~0.7 ms | 0.9 GB | ~6 min | **Best all-round default** |

**How to tune methodically (say this — it's the real answer):**
1. Build a **flat index over a 100k sample** → ground truth for 500 real queries.
2. Fix the SLO first: "p95 retrieval ≤ 150 ms end-to-end, Recall@10 ≥ 0.95."
3. Sweep the *query-time* knob only (`ef_search` / `nprobe`), plot recall vs p95. Pick the knee.
4. If the knee misses the SLO, change a build-time knob (`M`, `ef_construction`, quantization) and re-sweep.
5. Re-run the sweep after any model change or 2× corpus growth.

**Gotcha:** Retrieval latency is usually **not** your bottleneck. Embedding the query (50–200 ms API call) and the LLM generation (1–5 s) dominate. Optimising HNSW from 3 ms to 1 ms while the LLM takes 3 s is theatre — say this and you sound senior.

---

### Q16. How do you measure your ANN index's recall in production?
`[MEDIUM]`

**Answer:** ANN recall is measured against **exact** search, not against human relevance labels — keep the two evaluations separate.

```python
import numpy as np


def ann_recall_at_k(ann_results: list[list[int]],
                    exact_results: list[list[int]],
                    k: int = 10) -> float:
    """Mean fraction of true top-k IDs that the ANN index also returned."""
    hits = [len(set(a[:k]) & set(e[:k])) / k
            for a, e in zip(ann_results, exact_results)]
    return float(np.mean(hits))
```

Procedure:
1. Sample 500–1000 **real** production queries (query distribution matters — synthetic queries overstate recall).
2. Compute exact top-k with a flat index over the *same* vectors (sample the corpus if the full flat scan is too slow — recall estimates on a 10% sample are usually within a point).
3. Report Recall@10 alongside p50/p95/p99 latency and QPS. Track it as a dashboard metric, not a one-off.
4. Re-measure after every reindex, quantization change, or corpus doubling.

**Follow-up they will ask:** *"What recall is good enough?"* → For RAG with a reranker downstream, 0.95 @ k=50 is plenty, because the reranker fixes ordering and you over-fetch anyway. For "find the exact clause in this contract" compliance workloads, you want 0.99+ or exact search over a pre-filtered subset.

---

### Q17. Pick an index for 100k / 10M / 1B vectors.
`[MEDIUM]`

**Answer:**

| Scale | Index | Why |
|---|---|---|
| < 50k | **Flat** (NumPy / FAISS `IndexFlatIP`) | Exact, ~ms, zero ops. Rebuild on deploy. |
| 50k – 1M | **HNSW** in pgvector or Qdrant | Fits in RAM easily, best recall/latency, no training |
| 1M – 50M | **HNSW + int8 scalar quantization + rescoring** | 4× RAM cut for ~1 recall point |
| 50M – 500M | **DiskANN (pgvectorscale/Milvus)** or **HNSW sharded** | RAM cost of pure HNSW becomes the dominant bill |
| > 500M | **IVF-PQ / DiskANN, sharded, with rescoring** | Only compressed representations are economical |

Cross-cutting: at every scale above ~1M, add a **reranker** on the top-50 rather than chasing the last recall points from the ANN index — it's cheaper and improves final answer quality more.

---

## 4. Quantization, Memory & Build Time

### Q18. How much RAM does 1M × 1536-dim cost? Show the formula.
`[MEDIUM]`

**Answer:**

```
raw_vectors_bytes = N × d × bytes_per_component

  bytes_per_component:  float32 = 4 | float16 = 2 | int8 = 1 | binary = 1/8

HNSW graph overhead ≈ N × (2·M × 4 bytes)          # layer-0 links, 4-byte node IDs
                     × ~1.05                        # upper layers add ~5%

total ≈ raw_vectors + graph + (ids + payload + tombstones)
```

Worked, N = 1,000,000, d = 1536, M = 16:

| Component | Math | Bytes |
|---|---|---|
| Vectors fp32 | 1e6 × 1536 × 4 | **6.14 GB** (5.72 GiB) |
| HNSW graph | 1e6 × 2×16 × 4 × 1.05 | 0.13 GB |
| IDs + minimal payload | 1e6 × ~200 B | 0.20 GB |
| **Total resident** | | **≈ 6.5 GB** |
| **Provision** | ×2 for build/compaction/OS/page-cache headroom | **≈ 13–16 GB node** |

Same corpus, other precisions: fp16 → 3.07 GB; int8 → 1.54 GB; binary → 0.19 GB. At 768 dims, halve all of it.

**Gotcha:** People quote the 6 GB and forget that (a) HNSW **build** transiently needs more than steady state, (b) deleted-but-not-compacted vectors still occupy RAM, and (c) if you also store the raw chunk text as payload in the same service, text often exceeds the vectors. Budget 2× and store text in Postgres/blob with only IDs in the vector store if RAM is tight.

**Follow-up they will ask:** *"Your node has 16 GB and the corpus just doubled — what do you do today?"* → Drop to 768 dims via Matryoshka (halves it) or turn on int8 scalar quantization with rescoring (quarters it). Both are reversible and neither requires new hardware.

---

### Q19. Scalar vs product vs binary quantization — compare them.
`[HARD]`

**Answer:**

| Type | How | Compression | Typical recall loss | Rescoring needed? |
|---|---|---|---|---|
| **Scalar (SQ8 / int8)** | Per-dimension linear map float32 → int8 using observed min/max (or a 0.99 quantile to clip outliers) | 4× | 0.5–2 pts | Optional, cheap |
| **Product (PQ)** | Split into m sub-vectors, k-means 256 centroids each → 1 byte per sub-vector | 8–96× | 5–20 pts | **Yes** |
| **Binary (BQ)** | Keep only the sign of each dimension → 1 bit; compare with Hamming distance (XOR + popcount) | 32× | 3–30 pts, **highly dimension-dependent** | **Yes, always** |
| **Matryoshka truncation** | Not quantization — just fewer dimensions | 2–6× | 1–3 pts | No |

Decision guide:
- **int8 SQ is the default win.** 4× less RAM for ~1 recall point. Turn it on almost always above 1M vectors.
- **Binary only on high-dimensional models.** At 1024–3072 dims (OpenAI 3-large, Cohere v3, BGE-M3) binary + rescoring holds ~95–98% of full-precision recall. At 384 dims it collapses — there isn't enough redundancy in the sign bits.
- **PQ when RAM is the binding constraint** and you can afford the rescoring pass from SSD.
- **Stack them:** Matryoshka 3072→1024, then binary = 96× smaller, then rescore against fp32 on disk. That's the modern billion-scale recipe.

**Gotcha:** Quantization is applied to the *stored* vectors; the **query** vector usually stays full-precision (asymmetric distance computation) because it costs nothing and preserves accuracy.

---

### Q20. Explain rescoring / oversampling. Why does it rescue quantization?
`[HARD]`

**Answer:** Two-stage retrieval: search the **compressed** index for `k × oversampling` candidates (fast, low-memory, slightly wrong ordering), then recompute **exact** distances for just those candidates against the full-precision vectors and return the true top-k. You get compressed-index memory with near-full-precision recall, because quantization mostly perturbs *ordering within the neighbourhood*, not *membership of the neighbourhood*.

Cost: for k=10, oversampling=4 you rescore 40 vectors = 40 × 1536 × 4 B = 245 KB read + 61k FLOPs. Negligible. The full-precision copy can live on SSD or in a separate cheap tier — it is only touched 40 times per query, not 1M.

**Code (Qdrant — the config knob is explicit):**
```python
from qdrant_client import models

search_params = models.SearchParams(
    hnsw_ef=128,
    quantization=models.QuantizationSearchParams(
        ignore=False,
        rescore=True,        # re-rank candidates against original vectors
        oversampling=3.0,    # fetch 3x limit from the quantized index first
    ),
)
```

Equivalents: FAISS `IndexRefineFlat` wrapper / `index.k_factor`; Azure AI Search `rerankWithOriginalVectors` + `defaultOversampling`; Elasticsearch `rescore_vector.oversample`.

**Follow-up they will ask:** *"What oversampling factor?"* → Start at 2–4 for int8, 3–5 for binary, and measure. It's a query-time knob so you can tune it without a reindex.

---

### Q21. How long does index build take, and how do you speed it up?
`[MEDIUM]`

**Answer:** HNSW build is **N sequential inserts, each costing an O(log N)-hop search**, so the headline term is **O(N · log N)** distance computations, with `ef_construction` and `M` as large multiplicative constants (each insert evaluates an `ef_construction`-sized candidate list and prunes to `M` links per layer). In practice ~5–20 minutes per million 768-dim vectors single-threaded, and it parallelises well across cores. IVF is much faster to build (one k-means pass on a *sample*, then a single assignment pass) but needs the training step.

Levers, in order of impact:
1. **Parallelism.** pgvector ≥ 0.6 does parallel HNSW build — set `max_parallel_maintenance_workers`. FAISS honours `faiss.omp_set_num_threads(n)`.
2. **Memory for the build.** In Postgres, if the graph doesn't fit in `maintenance_work_mem` the build spills to disk and gets *dramatically* slower. Set it to several GB for the build, then reset.
3. **Bulk-load first, index after.** Inserting 10M rows into an existing HNSW index is far slower than `COPY` then `CREATE INDEX`.
4. **Lower `ef_construction`** if build time is genuinely blocking — but this permanently caps recall, so it's the last lever.
5. **Build offline** on a big machine, ship the artefact (FAISS `write_index`, or a Postgres logical-replica/snapshot swap).

**Gotcha:** Your real bottleneck for a fresh corpus is usually **embedding generation**, not index build — see the sizing exercise in Q41, where API rate limits dominate everything else.

---

## 5. Filtering, Hybrid & Sparse

### Q22. Pre-filter vs post-filter vs filtered-HNSW. Explain all three.
`[HARD]`

**Answer:**

| Strategy | How | Good when | Fails when |
|---|---|---|---|
| **Post-filter** | ANN top-k, then drop rows failing the predicate | Filter is non-selective (>50% pass) | Selective filters — you return far fewer than k, or nothing |
| **Pre-filter (exact)** | Resolve the predicate to an ID set, brute-force only those vectors | Small result set (< ~10k IDs) | Large ID sets — degenerates to full scan |
| **Filtered ANN (filtered-HNSW / ACORN / iterative scan)** | Apply the predicate *during* graph traversal, with cardinality estimation choosing the plan | The general case | Very low-cardinality attributes with a disconnected subgraph |

The real engineering insight: **filtering breaks graph connectivity.** If only 1% of nodes pass the filter, the HNSW graph restricted to those nodes is a sparse, possibly disconnected subgraph — greedy traversal gets stranded in a local minimum and recall craters. Solutions the products actually ship:

- **Qdrant** — estimates filter cardinality from payload indexes, then picks: exact/full scan of the matching subset when it is small, otherwise filtered graph search using *extra links built per payload sub-group* so each tenant/category subgraph stays connected. The knob is `full_scan_threshold` (default `10000`, and note the unit is **kilobytes of vector data**, not a vector count — a common misreading).
- **Weaviate** — ACORN-style: traverse the unfiltered graph but expand through non-matching nodes without returning them, preserving connectivity.
- **pgvector ≥ 0.8** — `hnsw.iterative_scan` (`relaxed_order` or `strict_order`): keep pulling more from the index until enough rows survive the WHERE clause. This fixed pgvector's long-standing "LIMIT 10 with a filter returns 3 rows" problem.
- **Azure AI Search** — `vectorFilterMode: preFilter` (default) or `postFilter`, chosen per query.

**Follow-up they will ask:** *"Which do you use for per-user document ACLs?"* → Filtered ANN with a payload/keyword index on the ACL field, and a hard rule that the filter is applied **inside** the search, never in application code after the fact — otherwise you've built a data-leak bug.

---

### Q23. Why exactly does naive post-filtering break recall? Give numbers.
`[HARD]`

**Answer:** Because the ANN index is blind to the predicate, the fraction of your top-k that survives the filter equals the filter's selectivity.

Concrete: 10M chunks, filter `tenant_id = 'acme'` matching **0.1%** (10k chunks). Ask the index for top-100 and post-filter:

```
expected survivors = 100 × 0.001 = 0.1 documents
```

You return an empty result set ~90% of the time. The naive fix is over-fetching:

```
fetch_k = k / selectivity = 10 / 0.001 = 10,000 candidates
```

Now every query scans and sorts 10k results — latency goes from 2 ms to ~200 ms, and you're materialising and transferring 10k payloads. And you still have no guarantee, because the true matching chunks may sit outside the global top-10,000 by pure vector distance.

**Correct answers:** (1) filtered ANN with cardinality estimation, or (2) pre-filter to the 10k-ID set and brute-force it (10k × 1536 = ~15M multiply-adds and ~61 MB scanned — single-digit milliseconds on one core with SIMD, so genuinely fast at this size), or (3) physical partitioning so the tenant has its own namespace/collection and the filter disappears entirely.

**Gotcha:** State the rule: **the more selective the filter, the worse post-filtering is, and the better pre-filtering/partitioning gets.** Selectivity is the deciding variable, and the DB needs statistics to know it.

---

### Q24. How do you implement hybrid search? Write the fusion.
`[MEDIUM]`

**Answer:** Run BM25/keyword and dense vector search **in parallel**, then fuse the two ranked lists. Dense retrieval fails on exact identifiers, product codes, rare acronyms and names; BM25 fails on paraphrase. Hybrid typically buys 5–15 points of Recall@10 on enterprise corpora — it is the single highest-ROI retrieval upgrade after chunking.

Fuse with **Reciprocal Rank Fusion (RRF)** — rank-based, so it needs no score normalization across two incomparable scales:

```
RRF(d) = Σ_over_lists  1 / (k + rank_i(d))       # k = 60 by convention
```

**Code:**
```python
from collections import defaultdict


def rrf_fuse(rankings: list[list[str]], k: int = 60, top_n: int = 10
             ) -> list[tuple[str, float]]:
    """rankings: list of ranked doc-id lists (best first), one per retriever."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]


# dense_ids / bm25_ids: list[str] of doc ids, best-first, from each retriever
dense_ids = ["d7", "d2", "d9"]
bm25_ids  = ["d2", "d4", "d7"]
fused = rrf_fuse([dense_ids, bm25_ids])   # -> [('d2', 0.0325...), ('d7', 0.0323...), ...]
```

Alternative: **weighted score fusion** `α·norm(dense) + (1-α)·norm(bm25)` with per-query min-max normalization. More tunable, but brittle — scores are not comparable across queries, so α needs retuning whenever a model changes. Use RRF unless you have an eval loop to tune α.

**Follow-up they will ask:** *"Where does reranking fit?"* → Retrieve 50 via hybrid+RRF → cross-encoder rerank (Cohere Rerank / BGE-reranker / Azure semantic ranker) → keep top 5 for the LLM context. RRF fixes recall; the reranker fixes precision.

---

### Q25. What are sparse vectors and SPLADE? Why not just use BM25?
`[HARD]`

**Answer:** A sparse vector has one dimension per vocabulary term with mostly zeros — BM25 is effectively a hand-crafted sparse representation. **SPLADE** is a *learned* sparse representation: a BERT-style model predicts a weight for every wordpiece in the 30,522-token vocabulary, with a ReLU + log saturation `log(1 + ReLU(logit))` and a FLOPS regularizer that forces sparsity down to ~100–300 non-zeros per document.

Why it beats BM25: **learned term expansion**. A document about "notice period" gets non-zero weight on "resignation", "attrition", "exit" even though those words never appear — so you get semantic matching *while keeping exact-term matching and interpretability*, and it slots into an inverted index.

| | BM25 | SPLADE | Dense |
|---|---|---|---|
| Exact term match | Excellent | Excellent | Poor |
| Synonym / paraphrase | None | Good (learned expansion) | Excellent |
| Needs GPU to index | No | Yes | Yes |
| Interpretable | Yes | Yes (per-term weights) | No |
| Index type | Inverted | Inverted (sparse vectors) | ANN graph |

Serving: Qdrant native `sparse_vectors`, Pinecone sparse-dense, Elasticsearch **ELSER** (Elastic's own learned-sparse model), Milvus `SPARSE_INVERTED_INDEX`. **BGE-M3** conveniently emits dense + sparse + ColBERT vectors from one forward pass.

**Gotcha:** Don't pitch SPLADE as a free upgrade. It costs a GPU inference pass at ingest *and* at query time, and roughly triples index size vs BM25. On a services project the pragmatic call is BM25 + dense + RRF first; SPLADE only if the eval shows keyword recall is still the failure mode.

---

### Q26. How do you enforce per-user document access control in vector search?
`[MEDIUM]`

**Answer:** ACLs are a **filtering** problem, and the filter must be evaluated **inside** the retrieval engine, never in application code afterwards.

Pattern I use:
1. At ingest, denormalize the document's ACL into the vector payload: `allowed_groups: ["finance", "hr-admin"]` (group IDs, not user IDs — users churn, groups don't).
2. Index that field (Qdrant payload index / pgvector GIN on an array column / Azure AI Search filterable `Collection(Edm.String)`).
3. At query time, resolve the caller's groups from the validated JWT (**never** from a client-supplied parameter) and pass them as a filter: `allowed_groups ANY OF caller_groups`.
4. Over-fetch and re-check post-retrieval as a defence-in-depth assertion — but the primary enforcement is the filter.
5. Handle revocation: ACL changes must trigger a metadata update (most DBs support payload-only update without re-embedding — Qdrant `set_payload`, pgvector plain `UPDATE`).

**Gotcha:** The nastiest leak isn't retrieval — it's **caching**. A semantic cache or a shared summary index keyed only on query text will serve a finance user's answer to an intern. Cache keys must include the ACL scope.

---

## 6. Production Operations

### Q27. How do you do multi-tenancy in a vector store?
`[HARD]`

**Answer:** Three patterns; pick by tenant count and isolation requirement.

| Pattern | Isolation | Scales to | Cost | Use when |
|---|---|---|---|---|
| **Metadata filter** (one index, `tenant_id` payload + payload index) | Logical only | 10k+ tenants | Cheapest | Many small tenants, shared SLA |
| **Namespace / partition** (Pinecone namespaces, Qdrant tenant-keyed payload index, Weaviate multi-tenancy shards) | Physical partition, one deployment | 100k+ tenants | Low | The default for SaaS |
| **Separate index/collection per tenant** | Full | ~dozens–low hundreds | Expensive | Regulated tenants, per-tenant encryption keys, wildly different corpus sizes |

Key facts to state:
- **Do not create 10,000 HNSW indexes.** Each index carries fixed memory overhead, its own graph and its own entry point; thousands of them will exhaust RAM and file handles long before the vectors do.
- Namespaces/tenant-keyed indexes are the sweet spot: the engine stores each tenant's vectors **contiguously**, so a tenant-filtered search is effectively a small dedicated index. Qdrant does this by marking the field `is_tenant=True`; Weaviate gives each tenant its own shard and can offload idle tenants to cold storage.
- Watch the **noisy-neighbour** problem: one 50M-vector tenant in a shared index degrades everyone. Promote such a tenant to a dedicated collection.
- Deletion/right-to-be-forgotten is far easier with physical separation — drop a namespace vs. issue millions of filtered deletes.

**Follow-up they will ask:** *"500 enterprise tenants, strict data isolation in the contract — what do you do?"* → Tenant-keyed partitions inside one cluster for the shared tier, plus a dedicated collection (or a dedicated Azure AI Search index) for the handful of tenants whose contract demands physical isolation. Document which tier each tenant is on.

---

### Q28. Sharding and replication — how do they affect recall and latency?
`[MEDIUM]`

**Answer:**
- **Sharding** (split vectors across N nodes, usually by hash of ID): each shard runs its own ANN search for top-k, and a coordinator merges N×k results into the final top-k. Recall is *approximately preserved* — merging top-k from partitions is correct for exact search, and for ANN it's fine as long as each shard's own recall is high. The cost is **tail latency**: query time = the slowest shard, so p99 degrades as N grows (scatter-gather amplification). Shard for memory capacity, not for speed.
- **Replication** (copies of the same shard): scales **read QPS** linearly and gives HA. Doesn't help single-query latency. Writes must fan out to all replicas — with eventual consistency you get a **freshness lag** where a just-upserted doc is visible on one replica and not another.

Rules I apply:
- Shard when a single node's RAM can no longer hold the index (see Q18 math), not before.
- Keep a tenant's vectors on a single shard when you can (tenant-key sharding) — turns scatter-gather into a single-shard query.
- Size replicas from QPS: `replicas = ceil(peak_QPS / per_node_QPS × 1.5)` and always ≥ 2 for HA.

---

### Q29. What happens to an HNSW index under heavy upserts and deletes?
`[HARD]`

**Answer:** It degrades, in two distinct ways.

**Deletes:** you cannot cleanly remove a node from an HNSW graph — its neighbours' link lists point at it and removing it may disconnect the graph. So every engine uses **tombstones**: mark deleted, keep the node in the graph as a routing waypoint, filter it out of results. Consequences:
- Memory is not reclaimed until compaction.
- Searches waste `ef` budget on dead candidates → effective recall for the *live* set drops.
- With >20–30% tombstones, recall degradation becomes measurable — this is the trigger to rebuild/compact.

**Updates (upsert = delete + insert):** the new node is inserted using the *current* graph, which is fine, but a high-churn index slowly accumulates a worse topology than a fresh build. IVF is worse still — the k-means centroids were fit on the original distribution, so drift silently reduces recall with no tombstone signal at all.

What to do:
- Monitor deleted-vector ratio; run the engine's compaction (Qdrant optimizers, Milvus compaction, Postgres `VACUUM`) or schedule a periodic rebuild.
- For pgvector: deleted heap tuples remain referenced by the HNSW index until `VACUUM`; ensure autovacuum is tuned for high-churn tables (`autovacuum_vacuum_scale_factor` down to 0.02 on big tables).
- Prefer **immutable chunk IDs with a soft `is_current` flag** and a nightly compaction over in-place churn, if your write pattern allows.

**Gotcha:** Many teams monitor QPS and latency but never monitor recall. Recall decays silently under churn. Schedule the Q16 recall job weekly.

---

### Q30. You need to switch embedding models on a live system. Zero downtime. How?
`[HARD]`

**Answer:** **Blue/green with a version field and an alias flip.** Vectors from two models are in incompatible spaces — you can never mix them in one searchable index, and you cannot incrementally migrate a live index.

Steps:
1. **Version everything.** Every vector row already carries `embedding_model`, `model_version`, `dims`, `chunker_version`. If it doesn't, that's the first fix.
2. **Build green offline.** New collection/index `docs_v2` (or a new `embedding_v2 halfvec` column in Postgres). Backfill from the canonical chunk store — never re-derive chunks from source, or you're changing two variables at once.
3. **Dual-write** during backfill: every new/updated doc writes to both v1 and v2 so green never falls behind. Track a high-water mark to know when green has caught up.
4. **Evaluate** on the golden set: Recall@10, nDCG@10, and end-to-end answer quality on v1 vs v2. Do not ship on vibes; a "better" MTEB score can be worse on your corpus.
5. **Shadow traffic**: send 100% of real queries to both, log both result sets, diff them. Catches latency and empty-result regressions.
6. **Flip** via alias/config (feature flag, or `ALTER TABLE ... RENAME` / a `SEARCH_INDEX` env var). Roll out 5% → 50% → 100%.
7. **Keep v1 hot for 7 days** for instant rollback, then drop.

**Gotcha:** The query path must resolve the model from the *index's* metadata, not from a separate constant. If the app is pinned to `text-embedding-3-small` and someone flips the index to a 3-large build, you get a dimension mismatch error at best and garbage results at worst.

**Follow-up they will ask:** *"Cost of the re-embed?"* → Corpus tokens × price. 10M docs × 2,400 tokens = 24B tokens ≈ $480 with `text-embedding-3-small` at $0.02/1M. Use the provider's **batch API (≈50% discount, 24h SLA)** for a backfill — it's not latency-sensitive.

---

### Q31. "Embedding drift" — is that a real thing? How do you version embeddings?
`[MEDIUM]`

**Answer:** The model doesn't drift — it's deterministic. Three real things get called drift:

1. **Provider model change.** An unpinned model alias gets updated server-side and new vectors land in a slightly different space than your existing corpus. Defence: pin exact model + version (in Azure OpenAI, a **deployment** pinned to a specific model version), and alert on unexpected version strings in responses.
2. **Data drift.** The query or corpus distribution moves (new product line, new jargon) and the frozen model has never seen the vocabulary. Symptom: retrieval quality falls while the index is unchanged. Detect by tracking mean top-1 similarity and the "zero good results" rate over time.
3. **Pipeline drift.** Someone changes the chunker, strips headers differently, or drops the E5 prefix. This is the most common and the most preventable — pin it in metadata and assert on it in CI.

Metadata I attach to every vector:
```json
{
  "doc_id": "...", "chunk_id": "...", "chunk_index": 3,
  "embedding_model": "text-embedding-3-small",
  "azure_deployment": "emb-3-small-prod", "model_version": "1",
  "api_version": "2024-10-21", "dims": 1536, "normalized": true,
  "chunker_version": "v3-recursive-512-64",
  "source_uri": "...", "ingested_at": "2026-07-31T10:00:00Z",
  "allowed_groups": ["finance"]
}
```

---

### Q32. Backups, DR and consistency for a vector store.
`[MEDIUM]`

**Answer:** Treat the vector index as a **derived artefact, not the source of truth.**

- **Source of truth** = original documents (blob storage) + the chunk table (Postgres) with text, metadata and IDs. If the vector store burns down, you rebuild it. That reframing removes 90% of the DR anxiety.
- **RTO matters though** — rebuilding 50M vectors takes hours of API calls plus index build. So still take snapshots: Qdrant snapshots, Milvus backup tool, `pg_dump`/PITR for pgvector, service-native backup for Pinecone/Azure AI Search. Test the restore, not just the backup.
- **Consistency:** most vector DBs are eventually consistent for search after an upsert (indexing lag from milliseconds to seconds). If a user uploads a doc and immediately searches, they may not find it. Fix by either exposing an explicit `wait=true` flush on write (Qdrant supports this), or by showing "indexing…" in the UI. Don't promise read-your-writes unless the engine guarantees it.
- **Idempotency:** use deterministic chunk IDs (e.g. `uuid5(namespace, f"{doc_id}:{chunk_index}:{chunker_version}")`) so a re-run of a failed ingest upserts rather than duplicates. Duplicate chunks are a top-3 cause of "the LLM keeps repeating itself."

---

## 7. Product Deep-Dives

### Q33. Compare the vector DB options and tell me when you'd pick each.
`[MEDIUM]`

**Answer:** *(Pricing figures are order-of-magnitude and move constantly — quote them as "roughly" in the interview.)*

| Product | Type | Index | Filtering | Hybrid | Best fit / when to choose |
|---|---|---|---|---|---|
| **pgvector** | Postgres extension | ivfflat, HNSW | SQL WHERE (iterative scan in ≥0.8) | via `tsvector` + RRF in SQL | You already run Postgres and have < ~10M vectors. **Default first answer** — transactions, joins, one backup story. |
| **pgvectorscale** | pgvector add-on (Rust) | StreamingDiskANN + SBQ | label-based | inherits | pgvector that has outgrown RAM; want DiskANN economics without leaving Postgres |
| **Qdrant** | Dedicated (Rust) | HNSW (+SQ/PQ/BQ) | **Best-in-class filtered HNSW** | Native sparse + fusion | Heavy metadata filtering, multi-tenancy, self-host on K8s. My default dedicated pick. |
| **Pinecone** | Fully managed SaaS | proprietary (serverless) | metadata filters | sparse-dense | You want zero ops and will pay for it; no infra team |
| **Weaviate** | Dedicated (Go) | HNSW, flat, dynamic | ACORN filtering | Native BM25 + hybrid | Multi-tenant SaaS (per-tenant shards, cold offload); GraphQL fans |
| **Milvus / Zilliz** | Dedicated, distributed | 10+ incl. DiskANN, GPU CAGRA | yes | yes | Billion-scale, GPU indexing, you have a platform team. Heavy deps (etcd/object store/MQ). |
| **Chroma** | Embedded / light server | hnswlib | metadata | basic | Prototypes, notebooks, demos. **Not** a production answer. |
| **Redis (RediSearch)** | In-memory DB | FLAT, HNSW | tags/numeric | yes | You already run Redis; need sub-ms and also want it as a semantic cache |
| **Elasticsearch / OpenSearch** | Search engine | HNSW (int8/bbq options) | native, mature | **BM25 is native — best hybrid story** | You already run ELK; keyword search is a first-class requirement |
| **Azure AI Search** | Managed PaaS | HNSW, exhaustiveKNN | OData `$filter`, pre/post | RRF hybrid + **semantic ranker** | **Enterprise on Azure.** See Q38. |
| **FAISS** | Library, not a DB | Everything | none | none | Offline eval, research, embedded in your own service; you own persistence and CRUD |

**How to answer "which would you pick" in this interview:** "pgvector if we're already on Postgres and under ~10M vectors; **Azure AI Search** if the client is an Azure enterprise shop, because it comes with the semantic ranker, integrated vectorization, Entra ID RBAC and private endpoints their security team already approved; Qdrant if we need aggressive metadata filtering or multi-tenancy and are willing to self-host." That answer shows judgement rather than fandom.

---

### Q34. pgvector: show me the SQL. ivfflat vs hnsw, and the operators.
`[MEDIUM]`

**Answer:**

**Operators:**

| Operator | Distance | Matching index opclass |
|---|---|---|
| `<->` | L2 / Euclidean | `vector_l2_ops` |
| `<=>` | **Cosine distance** (1 - cosine similarity) | `vector_cosine_ops` |
| `<#>` | **Negative** inner product (negated so ASC = best) | `vector_ip_ops` |
| `<+>` | L1 / Manhattan (pgvector ≥ 0.7) | `vector_l1_ops` |

**SQL:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id            bigserial PRIMARY KEY,
    doc_id        text NOT NULL,
    tenant_id     text NOT NULL,
    content       text NOT NULL,
    embedding     vector(1536) NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- HNSW: better recall/latency, slower build, no training. Preferred.
CREATE INDEX chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);

-- IVFFlat alternative: fast build, smaller, but MUST be created AFTER data is loaded
-- (it trains centroids on existing rows) and degrades as data grows.
-- lists ≈ rows/1000 up to 1M rows, then sqrt(rows).
-- CREATE INDEX chunks_embedding_ivf
--     ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

CREATE INDEX chunks_tenant_idx ON chunks (tenant_id);

-- Query-time knobs (session-scoped)
SET hnsw.ef_search = 100;          -- default 40; must be >= LIMIT
SET hnsw.iterative_scan = relaxed_order;  -- pgvector >= 0.8: fixes under-returning with filters
-- SET ivfflat.probes = 20;        -- if using ivfflat

SELECT id, doc_id, content,
       1 - (embedding <=> $1) AS cosine_similarity
FROM   chunks
WHERE  tenant_id = $2
ORDER  BY embedding <=> $1          -- ASC: smaller cosine distance = more similar
LIMIT  10;
```

**Code (psycopg 3 + pgvector):**
```python
import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DSN = "postgresql://app:secret@localhost:5432/rag"

# NOTE: do NOT use autocommit=True here. `SET LOCAL` is transaction-scoped and is a
# no-op (with a warning) outside a transaction block. With autocommit off, psycopg3
# opens a transaction implicitly and the `with` block commits on clean exit.
with psycopg.connect(DSN) as conn:
    register_vector(conn)  # adapts numpy arrays <-> vector type

    # Bulk insert
    rows = [("doc-1", "acme", "Refunds are processed within 14 days.",
             np.random.rand(1536).astype("float32"))]
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO chunks (doc_id, tenant_id, content, embedding) "
            "VALUES (%s, %s, %s, %s)", rows)

    # Search
    q = np.random.rand(1536).astype("float32")
    q /= np.linalg.norm(q)
    with conn.cursor() as cur:
        cur.execute("SET LOCAL hnsw.ef_search = 100")  # per-transaction; reverts on commit
        cur.execute(
            """
            SELECT id, content, 1 - (embedding <=> %s) AS score
            FROM   chunks
            WHERE  tenant_id = %s
            ORDER  BY embedding <=> %s
            LIMIT  %s
            """,
            (q, "acme", q, 5),
        )
        for row in cur.fetchall():
            print(row)
```

**Gotcha:** `ORDER BY embedding <=> $1 LIMIT 10` uses the index. `ORDER BY 1 - (embedding <=> $1) DESC` does **not** — wrapping the operator in an expression defeats the index and you silently get a sequential scan. Always `EXPLAIN ANALYZE` and look for `Index Scan using ..._hnsw`.

**Limits to know:** `vector` supports up to 16,000 dims but HNSW/ivfflat indexes only up to **2,000 dims** — so full-width `text-embedding-3-large` (3072) can't be indexed as `vector`; use `halfvec` (fp16, indexable to 4,000 dims) or truncate via Matryoshka. That's a great specific detail to drop.

---

### Q35. When does Postgres/pgvector stop being enough?
`[HARD]`

**Answer:** Four signals, in the order they usually appear:

1. **RAM.** The HNSW index must be in `shared_buffers`/page cache to be fast. Once the index exceeds RAM you fall off a cliff (random SSD reads per graph hop). ~10M × 1536 fp32 ≈ 61 GB — that's the practical wall for a normal Postgres box.
2. **Index build/maintenance windows.** HNSW builds are long and `CREATE INDEX` (non-concurrent) locks writes. `CONCURRENTLY` helps but doubles the time.
3. **Write throughput.** Sustained high-rate upserts cause bloat + autovacuum pressure that competes with your OLTP workload on the same instance.
4. **Feature needs.** Native sparse vectors, per-query quantization/rescoring knobs, tenant-aware physical partitioning, multi-vector/ColBERT — pgvector doesn't do these.

Escalation ladder (do these in order, don't jump to a new vendor):
1. Reduce dimensions (Matryoshka 1536 → 768) — instant 2×.
2. `halfvec` (fp16) — another 2×, ~0 recall loss.
3. **pgvectorscale** — StreamingDiskANN + statistical binary quantization; keeps you in Postgres while moving the bulk to SSD.
4. Move the vector workload to a **read replica** so it stops competing with OLTP.
5. *Then* consider a dedicated store (Qdrant / Azure AI Search).

**Gotcha:** Never lose the argument for staying in Postgres too early. One backup story, one access-control story, real joins with your business tables, and transactional consistency between a chunk and its vector are worth a lot on an enterprise services project.

---

### Q36. Write FAISS code. What is FAISS good and bad at?
`[MEDIUM]`

**Answer:** FAISS is a **library**, not a database: no persistence semantics, no CRUD-with-durability, no metadata filtering, no auth, no network layer. It gives you the fastest, most configurable ANN implementations. Use it for offline evaluation, recall benchmarking, and embedding a small index inside your own service.

**Code:**
```python
import faiss                      # pip install faiss-cpu
import numpy as np

d, n = 1536, 200_000
rng = np.random.default_rng(0)
xb = rng.random((n, d), dtype="float32")
faiss.normalize_L2(xb)            # in-place; makes inner product == cosine

# ---------- 1. Exact baseline (ground truth for recall) ----------
flat = faiss.IndexFlatIP(d)
flat.add(xb)

# ---------- 2. HNSW: in-memory workhorse ----------
hnsw = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)  # M = 32
hnsw.hnsw.efConstruction = 200
hnsw.add(xb)                      # no training step needed
hnsw.hnsw.efSearch = 128          # query-time recall dial

# ---------- 3. IVF-PQ: compressed, needs training ----------
# OPQ64_256 = learned rotation to 256 dims with 64 sub-quantizers; PQ64 = 64 bytes/vector.
# nlist must suit the training set: FAISS warns below 39 training vectors per centroid,
# so at n=200k use nlist=1024 (~195/centroid), NOT 4096 (~49/centroid).
ivfpq = faiss.index_factory(d, "OPQ64_256,IVF1024,PQ64", faiss.METRIC_INNER_PRODUCT)
ivfpq.train(xb)                   # at 1M+ vectors, train on a sample and raise nlist to 4096
ivfpq.add(xb)
faiss.extract_index_ivf(ivfpq).nprobe = 32   # recall dial; downcast to reach the IVF layer

# ---------- 4. Stable external IDs ----------
ided = faiss.IndexIDMap2(faiss.IndexFlatIP(d))
ided.add_with_ids(xb[:1000], np.arange(1000, dtype="int64"))

# ---------- 5. Search + recall measurement ----------
xq = xb[:500]
_, truth = flat.search(xq, 10)
_, approx = hnsw.search(xq, 10)
recall = np.mean([len(set(a) & set(t)) / 10 for a, t in zip(approx, truth)])
print(f"HNSW recall@10 = {recall:.3f}")

# ---------- 6. Persistence ----------
faiss.write_index(hnsw, "/tmp/corpus.hnsw.faiss")
reloaded = faiss.read_index("/tmp/corpus.hnsw.faiss")
```

**Gotcha:** FAISS returns **positions**, not your document IDs, unless you wrap in `IndexIDMap2`. Keep a parallel `list[str]` or (better) a Postgres table mapping position → chunk. Also: `faiss.normalize_L2` mutates the array in place — pass a copy if you need the original.

**Follow-up they will ask:** *"Why not ship FAISS to production?"* → No filtering (kills ACLs and multi-tenancy), no durable incremental updates (you rebuild and swap the file), no replication. Fine as a rebuilt-on-deploy read-only index; not fine as a system of record.

---

### Q37. Write Qdrant client code with filtering and quantization.
`[MEDIUM]`

**Answer:**

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")  # or url=..., api_key=... for Cloud

# ---------- create collection: HNSW + int8 quantization ----------
# `recreate_collection()` is DEPRECATED in qdrant-client >= 1.9 (it silently drops data).
# Use delete_collection() + create_collection(), or guard with collection_exists().
if client.collection_exists("docs"):
    client.delete_collection("docs")

client.create_collection(
    collection_name="docs",
    vectors_config=models.VectorParams(
        size=1536,
        distance=models.Distance.COSINE,
        on_disk=True,           # originals memmapped from disk (needed for the rescore tier);
                                # without this the fp32 copy also stays resident in RAM
    ),
    # full_scan_threshold is in KILOBYTES of vector data, not a vector count.
    hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128, full_scan_threshold=10_000),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,      # clip outliers before mapping to int8
            always_ram=True,    # keep quantized vectors in RAM, originals on disk
        )
    ),
    on_disk_payload=True,
)

# Payload index makes the tenant filter cheap AND enables cardinality estimation.
client.create_payload_index(
    collection_name="docs",
    field_name="tenant_id",
    field_schema=models.PayloadSchemaType.KEYWORD,
    # For real multi-tenancy, use the tenant-keyed form instead so Qdrant stores each
    # tenant's points contiguously (see Q27):
    #   field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True)
)

# ---------- upsert ----------
client.upsert(
    collection_name="docs",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.01] * 1536,
            payload={"tenant_id": "acme", "doc_id": "policy-7", "lang": "en",
                     "text": "Refunds are processed within 14 days."},
        )
    ],
    wait=True,   # read-your-writes for this call
)

# ---------- filtered search with rescoring ----------
hits = client.query_points(
    collection_name="docs",
    query=[0.01] * 1536,
    limit=10,
    query_filter=models.Filter(
        must=[models.FieldCondition(key="tenant_id",
                                    match=models.MatchValue(value="acme"))],
        must_not=[models.FieldCondition(key="lang",
                                        match=models.MatchValue(value="de"))],
    ),
    search_params=models.SearchParams(
        hnsw_ef=128,
        quantization=models.QuantizationSearchParams(rescore=True, oversampling=3.0),
    ),
    with_payload=True,
).points

for h in hits:
    print(h.id, round(h.score, 4), h.payload["doc_id"])
```

**Gotcha:** `query_points` is the current API (client ≥ 1.10) and returns a `QueryResponse` — you must take `.points`; the older `client.search(...)` returned a bare list and is deprecated. Mention that you know both if the interviewer's codebase is older. For multi-tenancy at scale, create the tenant payload index with `is_tenant=True` so Qdrant stores each tenant's points contiguously.

---

### Q38. Azure AI Search — what does it give you and why do enterprises pick it?
`[MEDIUM]`

**Answer:** Because it is **one PaaS resource that covers keyword + vector + hybrid + reranking + ingestion**, already inside the customer's Azure security perimeter. On a Virtusa-style enterprise engagement that's usually decisive — the security review is already done.

What it actually provides:

| Feature | Detail |
|---|---|
| Vector search | HNSW (defaults `m=4, efConstruction=400, efSearch=500`) or `exhaustiveKnn`; cosine/dotProduct/euclidean; up to 3072 dims per vector field |
| Hybrid | Runs BM25 and vector in one request, fused with **RRF (k=60)** — no glue code |
| **Semantic ranker** | Microsoft-hosted cross-encoder that re-ranks up to **50** results; returns `@search.rerankerScore` (0–4) plus extractive captions and answers. This is the single biggest quality lever and you don't host a model. |
| Integrated vectorization | Skillset splits documents and calls your Azure OpenAI embedding deployment at index time **and** query time — no separate embedding service |
| Compression | Scalar + binary quantization with `rerankWithOriginalVectors` and `defaultOversampling` |
| Filtering | OData `$filter`; `vectorFilterMode: preFilter` (default) or `postFilter` — per query |
| Security | Entra ID RBAC, private endpoints, customer-managed keys, and **security trimming** via a filterable `allowed_groups` field |
| Ops | Indexers for Blob/SQL/Cosmos/SharePoint with change tracking; SLA-backed, no nodes to run |

**Code sketch (`azure-search-documents` ≥ 11.5):**
```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

# Preferred on an enterprise engagement: keyless auth via Entra ID RBAC.
# `pip install azure-identity`; the caller needs the "Search Index Data Reader" role.
from azure.identity import DefaultAzureCredential

client = SearchClient(endpoint="https://<svc>.search.windows.net",
                      index_name="docs",
                      credential=DefaultAzureCredential())
# Key-based fallback (dev/local only):
#   from azure.core.credentials import AzureKeyCredential
#   credential=AzureKeyCredential("<query-key>")

results = client.search(
    search_text="what is the refund window?",             # BM25 leg
    vector_queries=[VectorizedQuery(vector=query_vector,  # vector leg
                                    k_nearest_neighbors=50,
                                    fields="contentVector")],
    filter="tenant_id eq 'acme'",
    query_type="semantic",                                # enable semantic ranker
    semantic_configuration_name="default",
    top=5,
)
for r in results:
    print(r["@search.rerankerScore"], r["title"])
```

**Gotcha:** Know the ceilings — semantic ranker only reranks the top 50, so your first-stage retrieval must actually surface the right doc in that window. And storage/index quotas are per-SKU (Basic vs Standard S1/S2/S3), so capacity planning is a SKU decision, not a config change.

**Red flag to avoid:** don't say "Azure AI Search is just a wrapper over Elasticsearch." It isn't, and it's the kind of throwaway line that ends a good round.

---

## 8. Evaluation, Cost & Sizing

### Q39. How do you evaluate retrieval quality (not the LLM's answer)?
`[MEDIUM]`

**Answer:** Separate the two evaluations. Retrieval eval needs a **golden set**: 200–500 real questions, each labelled with the chunk IDs that actually contain the answer. Build it from real support tickets/user logs, and have SMEs label — LLM-generated question/answer pairs are a starting point, not a ground truth.

| Metric | What it answers | When it's the one to watch |
|---|---|---|
| **Recall@k** | Did the right chunk make it into the top-k at all? | The primary RAG metric — the LLM can't use what wasn't retrieved |
| **nDCG@10** | Is the ordering good, weighted toward the top? | When you have a reranker and graded relevance |
| **MRR** | How high is the first relevant hit? | Single-answer lookups |
| **Precision@k** | How much junk is in the context? | Context-window and cost pressure |
| **Hit rate** | Fraction of queries with ≥1 relevant hit | Executive-friendly headline |
| **ANN Recall vs exact** | Is the *index* losing results? (Q16) | Infra tuning — keep it separate from relevance |

Downstream (RAGAS-style, LLM-as-judge): context precision, context recall, faithfulness, answer relevancy. Useful, but noisy and expensive — gate releases on Recall@k, use the LLM-judge metrics as a trend.

Ship it as a **CI job**: golden set runs on every retrieval-config change; block the merge if Recall@10 drops more than 2 points.

---

### Q40. Model the cost of a vector search deployment.
`[MEDIUM]`

**Answer:** Four line items. *(Prices are approximate — say "roughly, and I'd verify current pricing.")*

1. **One-time embedding of the corpus:** `total_tokens × price/1M`. 24B tokens × $0.02/1M (`text-embedding-3-small`) ≈ **$480**. Halve it with the batch API.
2. **Ongoing embedding:** query embeddings (one short query ≈ 20 tokens — effectively free, ~$0.40 per million queries) + delta ingestion.
3. **Storage/serving** — the recurring cost, and it's a **RAM** cost:
   - Self-hosted: derive RAM from Q18, pick instances. 2× 64 GB memory-optimised nodes ≈ $700–900/month on-demand, ~40% less reserved.
   - Managed (Pinecone serverless ≈ $0.33/GB-month storage plus read/write units; Azure AI Search per-SKU per-hour) — simpler, more expensive at scale, cheaper below ~5M vectors once you price your own ops time.
4. **Reranking**, if used: ~$1–2 per 1,000 rerank requests for a hosted reranker, or a GPU you host.

**The lever nobody expects you to mention:** dimensions. Going 1536 → 768 via Matryoshka halves storage, halves RAM, halves the instance bill, and roughly halves distance-computation time — usually for ~1 point of recall. It's the highest-leverage cost decision in the whole system, and it's a one-line API change.

**Gotcha:** In a full RAG system, vector infra is typically **5–15%** of the bill; LLM generation tokens are the rest. Optimise retrieval for *quality* and the LLM for *cost*, not the other way round.

---

### Q41. Worked exercise: size a vector store for 10M documents.
`[HARD]`

**Answer:** State assumptions out loud first — that's the graded part.

**Assumptions:** 10M documents, avg 2,400 tokens each; chunk 512 tokens with 64 overlap (stride 448) → ~5.4 chunks/doc → **~54M vectors** (round to 50M). Peak 50 QPS, p95 retrieval SLO 150 ms, Recall@10 ≥ 0.95, ~1% of corpus changes daily.

**Step 1 — Embedding cost & time (usually the binding constraint):**
```
corpus tokens          = 10M × 2,400                = 24.0B
+ overlap (~14%)                                    ≈ 27.4B
cost @ $0.02/1M (3-small)                           ≈ $548   (~$274 via batch API)
```
Throughput is the real problem. At an Azure OpenAI deployment of **1M TPM**:
```
27.4B / 1M tokens-per-min = 27,400 min ≈ 19 days
```
→ Request a quota increase to 10M TPM (≈ 46 hours), or use the batch endpoint, or shard across regions. **Say this out loud** — most candidates only compute dollars and miss that rate limits set the schedule.

**Step 2 — Storage, at 50M vectors:**

| Config | Bytes/vector | Total vectors | + HNSW graph (M=16) | Fits on |
|---|---|---|---|---|
| fp32, 1536-d | 6,144 | **307 GB** | +6.4 GB | 5–6 × 64 GB nodes |
| fp32, 768-d (MRL) | 3,072 | 154 GB | +6.4 GB | 3 × 64 GB nodes |
| int8 SQ, 1536-d | 1,536 | 77 GB | +6.4 GB | 2 × 64 GB nodes |
| **int8 SQ, 768-d** | 768 | **38 GB** | +6.4 GB | **1 × 64 GB node + replica** |
| binary, 1536-d + fp32 rescore on SSD | 192 | 9.6 GB RAM | +6.4 GB | 1 × 32 GB node, 307 GB NVMe |

**Step 3 — Recommendation:** `text-embedding-3-small` truncated to **768 dims** (Matryoshka) + **int8 scalar quantization with rescoring ×3**, HNSW `M=16, ef_construction=128, ef_search=96`.
- RAM: 38 GB int8 vectors + 6.4 GB graph + ~5 GB payload/IDs ≈ **50 GB** → 2 × 64 GB nodes (one primary + one replica) with room to grow. Chunk **text** lives in Postgres, not the vector store — only IDs and filter fields in the payload.
- **Don't forget the rescoring tier:** oversampling ×3 re-ranks against the *original* fp32 vectors, so those 154 GB (50M × 768 × 4 B) must still exist — on local NVMe, not RAM. In Qdrant that's `always_ram=True` on the quantized copy with the originals `on_disk`. A candidate who quotes only the 38 GB has under-provisioned the box.
- QPS: a single node serves several hundred QPS at this size; 50 QPS peak is comfortable, and the replica covers HA and read scaling.
- Latency budget: vector search ~5–15 ms, rerank top-50 ~50 ms, query embedding ~60 ms → **p95 ≈ 130 ms**, inside SLO.
- Freshness: 1% daily = 500k vectors/day = ~6 upserts/sec — trivial. Schedule compaction weekly and a recall check (Q16) weekly.
- Validation plan: build a flat index on a 500k sample, 500-query golden set, sweep `ef_search` ∈ {48, 96, 192} and oversampling ∈ {1, 3, 5}, pick the knee.

**Follow-up they will ask:** *"Now make it 10× bigger."* → 500M vectors: switch to DiskANN (pgvectorscale or Milvus) or binary quantization + SSD rescoring, and shard by tenant so most queries stay single-shard. Don't scale HNSW-in-RAM to 500M — the instance bill grows faster than the value.

---

### Q42. Retrieval quality dropped in production. Triage it.
`[MEDIUM]`

**Answer:** Work outside-in, and check the cheap things first.

| Symptom | Likely cause | Check |
|---|---|---|
| Empty or short result sets | Post-filter with a selective filter; `ef_search < k`; iterative scan off | Log pre-filter candidate count vs returned count |
| Everything looks vaguely relevant, nothing is right | Chunks too large; query/document asymmetry | Inspect retrieved chunks by hand — 20 queries, 10 minutes, most bugs surface |
| Exact IDs / product codes not found | Pure dense retrieval | Add BM25 + RRF (Q24) |
| Gradual decay over weeks | Tombstone accumulation, IVF centroid drift | Deleted-ratio metric; run recall job (Q16); compact |
| Sudden step change | Model/deployment version changed; chunker deployed; prefix dropped | Diff `model_version` / `chunker_version` in metadata against last-known-good |
| One tenant is bad, others fine | Filter cardinality / noisy neighbour | Per-tenant recall breakdown |
| Duplicated content in answers | Non-idempotent ingest creating duplicate chunks | `SELECT content, count(*) ... GROUP BY HAVING count(*) > 1` |
| Latency spike, recall fine | Over-fetching for post-filter; payload bloat; cold page cache | p99 by stage; `with_payload` size |

**The one-line rule:** *log the retrieved chunk IDs and scores for every request.* Without that you cannot debug RAG at all, and it costs almost nothing.

---

## Red Flags / Do NOT say

- ❌ "More dimensions means better quality." → Wrong. `text-embedding-3-large` truncated to 256 dims beats full 1536-dim `ada-002`.
- ❌ "I'd use cosine similarity > 0.8 as the relevance cutoff." → Uncalibrated and model-specific (Q9).
- ❌ "We just use Chroma in production." → Signals prototype-only experience. Say what you'd use *for production* and why.
- ❌ "Vector DBs replace SQL databases." → They're an index. The documents still live somewhere transactional.
- ❌ "FAISS is a vector database." → It's a library: no filtering, no auth, no durable CRUD.
- ❌ "HNSW recall is 100%." → It's approximate by definition; quote a measured number instead.
- ❌ "We can just re-embed with the new model incrementally." → Mixed embedding spaces are broken results. Blue/green or nothing (Q30).
- ❌ Mentioning `openai.Embedding.create` or `from langchain.embeddings import OpenAIEmbeddings` — both are legacy. Current: `client.embeddings.create(...)` and `from langchain_openai import OpenAIEmbeddings`.
- ❌ Naming a product without a tradeoff. Every "I'd use X" must be followed by "because… and the cost is…".

---

## Rapid-Fire (last 10 min before you walk in)

1. **`text-embedding-3-small` dims / max tokens / price?** → 1536 (truncatable), 8191 tokens, ~$0.02 per 1M tokens.
2. **`text-embedding-3-large` dims?** → 3072, truncatable via the `dimensions` parameter.
3. **Matryoshka in one line?** → Model trained so the first k dims are a valid embedding; truncate for cheap storage.
4. **Cosine vs dot on normalized vectors?** → Identical ranking; dot is cheaper (no divide).
5. **`‖a-b‖²` in terms of cosine (unit vectors)?** → `2 - 2·cos(a,b)`.
6. **HNSW `M`?** → Links per node per layer (layer 0 gets 2M). ↑recall, ↑memory linearly. Rebuild to change.
7. **HNSW `ef_construction`?** → Build-time candidate list. ↑graph quality, ↑build time only. Free at query time.
8. **HNSW `ef_search`?** → Query-time candidate list. The live recall/latency dial. Must be ≥ k.
9. **IVF `nlist` / `nprobe`?** → Number of k-means cells / cells scanned per query. `nprobe` is the recall dial.
10. **`nlist` rule of thumb?** → 4·√N to 16·√N; ~4096 at 1M, ~65536 at 10M.
11. **PQ compression for d=1536, m=64?** → 64 bytes vs 6,144 bytes = 96×.
12. **RAM for 1M × 1536 float32?** → 6.14 GB, plus ~0.13 GB HNSW graph at M=16. Provision ~2×.
13. **int8 scalar quantization?** → 4× smaller, ~1 recall point, turn it on above 1M vectors.
14. **Binary quantization caveat?** → 32× smaller but needs rescoring, and only works on high-dim (1024+) models.
15. **Rescoring / oversampling?** → Fetch k×N from the compressed index, re-rank against full-precision vectors.
16. **Why post-filtering breaks?** → Survivors ≈ k × selectivity. 0.1% filter on top-100 returns 0.1 docs.
17. **RRF formula and constant?** → `Σ 1/(60 + rank)`; rank-based so no score normalization needed.
18. **SPLADE?** → Learned sparse vectors with term expansion over the BERT vocab; served in an inverted index.
19. **pgvector operators?** → `<->` L2, `<=>` cosine distance, `<#>` negative inner product, `<+>` L1.
20. **pgvector index dim limit?** → HNSW/ivfflat cap at 2,000 dims for `vector`; use `halfvec` (4,000) or truncate.
21. **pgvector 0.8 headline feature?** → `hnsw.iterative_scan` — fixes under-returning results with WHERE filters.
22. **Azure AI Search semantic ranker limit?** → Reranks the top 50 results; returns `@search.rerankerScore` 0–4.
23. **HNSW deletes?** → Tombstones; graph keeps the node as a waypoint. Compact above ~20–30% deleted.
24. **Zero-downtime model swap?** → Blue/green index + dual-write + golden-set eval + alias flip + keep old 7 days.

---

*If you only memorise three things from this file: the memory formula (Q18), what the three HNSW knobs do (Q12), and why post-filtering breaks recall (Q23). Those three come up in almost every vector-DB interview.*
