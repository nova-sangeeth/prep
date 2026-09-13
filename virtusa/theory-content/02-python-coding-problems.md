# Python Coding Problems — Whiteboard & Machine Round

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

Every snippet below was executed on CPython 3.10/3.11 before it went into this file. Only `numpy` and `pydantic v2` are non-stdlib.

## Table of Contents

| # | Section | Contents |
|---|---------|----------|
| 0 | [How this round runs](#0-how-this-round-runs-read-first) | Paper-coding protocol, what they score |
| 1 | [Blind-75 hit list](#1-blind-75-hit-list-they-actually-ask) | 12 classics, one-line approach + O(), links to `../dsa/` |
| 2 | [Pythonic / idiom problems (Q1–Q16)](#2-pythonic--idiom-problems) | flatten, batch, LRU, TTL memo, retry, rate limiters, singleton, context managers |
| 3 | [Text & GenAI problems (Q17–Q27)](#3-text--genai-flavoured-problems) | chunkers, cosine, top-k vectors, MMR, partial JSON, SSE, PII, Levenshtein, MinHash |
| 4 | [Concurrency (Q28–Q32)](#4-concurrency) | bounded async pool, producer/consumer, per-host rate limit, thread-safe counter, to_thread |
| 5 | [OOP design on paper (Q33–Q37)](#5-oop-design-on-paper) | TTL KV store, tool registry, LFU, agent memory, resilient client |
| 6 | [Rapid-Fire](#rapid-fire-last-10-min-before-you-walk-in) | 25 one-liners |
| 7 | [Red Flags](#red-flags--do-not-say) | Sentences that end the round |

---

## 0. How this round runs (read first)

**Format:** you get a marker/paper or a laptop with a plain editor (often no autocomplete, sometimes no interpreter). They watch you think more than they run your code.

**The 6-step protocol — say these out loud, in this order, every single time:**

1. **Restate + constraints.** "n up to? Duplicates allowed? Unicode or ASCII? Can I mutate the input? Is it a stream or does it fit in memory?"
2. **Brute force + its O().** Always name it, even if it is stupid. Never start at the optimal without naming the baseline — that reads as memorised.
3. **The insight.** One sentence: "hash map turns the inner scan into O(1)", "sorting makes the overlap check local", "a heap keeps only k items".
4. **Optimal O(time) / O(space)** before writing a line.
5. **Write it** — real Python, real names, type hints if you have room. Leave a blank line between logical blocks so you can insert fixes.
6. **Dry run on one small case + name the edge cases**: empty, single element, all-equal, overflow/negatives, `None`, capacity 0, concurrent access.

**What loses points (in this order):** silent thinking > wrong complexity claim > not handling empty input > non-idiomatic Python (manual index loops, `range(len(x))`, no context manager) > not testing.

**Whiteboard sizing:** write ~30 lines max. If your solution needs 80 lines, you picked the wrong decomposition — say "I'll write the core loop and stub the helpers", and do exactly that.

---

## 1. Blind-75 hit list they actually ask

You already have full solutions in [`../DSA_MASTER.md`](../DSA_MASTER.md) and [`../dsa/`](../dsa/) — do **not** re-read all 150 tonight. These 12 cover ~80% of what a services-company L1 asks a 6-year dev, and the pattern name matters more than the code.

| # | Problem | One-line approach | Time / Space | File in `../dsa/` |
|---|---------|-------------------|--------------|-------------------|
| 1 | Two Sum | Hash map of `value -> index`, look for `target - x` in one pass | O(n) / O(n) | `arrays_hashing/two_sum.py` |
| 2 | Group Anagrams | Key each word by `tuple(sorted(w))` or a 26-length count tuple, bucket in `defaultdict(list)` | O(n·k log k) or O(n·k) / O(n·k) | `arrays_hashing/group_anagrams.py` |
| 3 | Top K Frequent Elements | `Counter` then bucket-sort by frequency (or `heapq.nlargest` for O(n log k)) | O(n) / O(n) | `arrays_hashing/top_k_frequent.py` |
| 4 | Product of Array Except Self | Prefix pass then suffix pass, accumulate into the output array; no division | O(n) / O(1) extra | `arrays_hashing/product_except_self.py` |
| 5 | Longest Substring Without Repeating | Sliding window; on a repeat jump `left` to `last_seen[c] + 1` | O(n) / O(min(n, Σ)) | `sliding_window/longest_substring_without_repeating.py` |
| 6 | Valid Parentheses | Stack; push openers, on a closer pop and compare via a pair dict; stack must end empty | O(n) / O(n) | `stack/valid_parentheses.py` |
| 7 | Merge Intervals | Sort by start, extend `out[-1][1]` while `start <= out[-1][1]` | O(n log n) / O(n) | `intervals/merge_intervals.py` |
| 8 | Search in Rotated Sorted Array | Binary search; each step one half is sorted — test which, then decide the side | O(log n) / O(1) | `binary_search/search_rotated.py` |
| 9 | Number of Islands | Iterate cells; on a `1`, BFS/DFS flood-fill and sink to `0`; count launches | O(m·n) / O(m·n) worst | `graphs/number_of_islands.py` |
| 10 | Course Schedule | Kahn topological sort — if processed count < V there is a cycle (DFS colouring also fine) | O(V+E) / O(V+E) | `graphs/course_schedule.py` |
| 11 | Coin Change | Bottom-up DP `dp[a] = min(dp[a - c] + 1)`, `dp[0] = 0`, unreachable = `inf` | O(amount·coins) / O(amount) | `dp_1d/coin_change.py` |
| 12 | Merge k Sorted Lists | Min-heap of `(val, list_idx, node)`; pop-push k-way merge | O(N log k) / O(k) | `linked_list/merge_k_sorted_lists.py` |

**Also frequently asked and covered in depth below (do not skip these):** LRU Cache → Q8, Merge/Insert Interval → Q6, Kth Largest / Top-K stream → Q7, Edit Distance → Q26, LFU Cache → Q35.

**If they open with a random LeetCode-medium you have not seen:** narrate the pattern search out loud — "sorted input or k-th something ⇒ two pointers / heap; substring or subarray ⇒ sliding window; grid or dependency ⇒ BFS/DFS/topo; count-the-ways or min-cost ⇒ DP". Interviewers score the search, not the recall.

---

## 2. Pythonic / idiom problems

This is where a 6-year dev is separated from a 2-year dev. They are checking whether you reach for `defaultdict`, `heapq`, `itertools`, `contextlib`, generators and decorators without being prompted.

### Q1. Flatten an arbitrarily nested dict into dot-separated keys (and flatten a nested list). Then un-flatten it.

`[MEDIUM]`

**Answer:** Recurse over `Mapping`, building the key path as you descend; a leaf is anything that is not a `Mapping`. Index into lists with `key[i]`. O(n) in the number of leaves, O(d) stack depth. Un-flattening is `setdefault` down the path. For the *list* variant, prefer an explicit stack/generator over recursion so a 10 000-deep structure does not blow `RecursionError` (default limit 1000).

**Constraints to ask:** keys always strings? do lists need indexing or just flattening? are empty dicts leaves? do keys contain the separator character?

**Brute force → optimal:** there is no slow-vs-fast here; the grading is on (a) using `collections.abc.Mapping` instead of `isinstance(v, dict)` so `OrderedDict`/`MappingProxy`/pydantic-dumped models work, (b) not mutating a shared accumulator via a default argument, (c) preserving empty containers.

**Code:**

```python
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

def flatten_dict(d: Mapping[str, Any], parent: str = "", sep: str = ".") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{parent}{sep}{k}" if parent else str(k)
        if isinstance(v, Mapping):
            if v:
                out.update(flatten_dict(v, key, sep))
            else:
                out[key] = {}                 # keep empty dicts, don't lose the key
        elif isinstance(v, list):
            for i, item in enumerate(v):
                ik = f"{key}[{i}]"
                if isinstance(item, (Mapping, list)):
                    out.update(flatten_dict({ik: item}, "", sep))
                else:
                    out[ik] = item
        else:
            out[key] = v
    return out

def unflatten_dict(flat: Mapping[str, Any], sep: str = ".") -> dict[str, Any]:
    root: dict[str, Any] = {}
    for k, v in flat.items():
        parts = k.split(sep)
        cur = root
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = v
    return root

def flatten_iter(nested: Any) -> Iterator[Any]:
    """Iterative, so deep nesting can't blow the recursion limit. Strings stay whole."""
    stack = [iter(nested)]
    while stack:
        it = stack[-1]
        for x in it:
            if isinstance(x, (list, tuple, set)):
                stack.append(iter(x))
                break
            if isinstance(x, str):
                yield x
                continue
            if isinstance(x, Iterable):
                stack.append(iter(x))
                break
            yield x
        else:
            stack.pop()

src = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "f": [10, {"g": 4}], "h": {}}
assert flatten_dict(src) == {"a": 1, "b.c": 2, "b.d.e": 3, "f[0]": 10, "f[1].g": 4, "h": {}}
assert unflatten_dict({"a.b": 1, "a.c": 2}) == {"a": {"b": 1, "c": 2}}
assert list(flatten_iter([1, [2, [3, [4]], 5], (6, 7), "ab"])) == [1, 2, 3, 4, 5, 6, 7, "ab"]
```

**Complexity:** O(L) time for L leaves, O(L) space for the output, O(depth) recursion.

**Gotcha:** `str` is `Iterable` — without the explicit `isinstance(x, str)` branch you recurse into characters forever-ish. And `flatten` is lossy: `{"a.b": 1}` and `{"a": {"b": 1}}` collapse to the same key. Say that out loud. Note also that `unflatten_dict` is **not** a full inverse of `flatten_dict`: it rebuilds dicts only, so the `f[0]` list-index keys come back as literal string keys, not lists — call that out rather than claiming a round trip.

**Follow-up they will ask:** "Where do you use this in a GenAI codebase?" → flattening nested LLM JSON output before writing to a flat store/CSV, flattening config for env-var overrides, and flattening metadata for vector-DB filters (Pinecone/Qdrant payload filters only accept flat scalar fields).

---

### Q2. Write a lazy `batched(iterable, n)` that yields lists of size n. It must work on an infinite generator.

`[EASY]`

**Answer:** `itertools.islice` on a single iterator, in a `while` loop with the walrus operator. Never `list(it)` first — that defeats the purpose and OOMs on a stream.

**Constraints to ask:** last partial batch — yield it or drop it? tuples or lists? need a strict/padded variant?

**Brute force → optimal:** brute force is `[data[i:i+n] for i in range(0, len(data), n)]` — O(n) but requires a **sized, indexable** sequence in memory. The islice version is O(1) extra memory per batch and works on files, DB cursors and generators.

**Code:**

```python
import itertools
from collections.abc import Iterable, Iterator

def batched(it: Iterable, n: int) -> Iterator[list]:
    if n < 1:
        raise ValueError("n must be >= 1")
    itr = iter(it)                       # crucial: ONE iterator, not a fresh one per loop
    while chunk := list(itertools.islice(itr, n)):
        yield chunk

assert list(batched(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
```

**Complexity:** O(N) total, O(n) memory.

**Gotcha:** `itertools.batched` exists **only in Python 3.12+** (and yields tuples, `strict=` added in 3.13). If you claim it, name the version. On 3.10/3.11 you write it yourself. Also: `zip(*[iter(x)]*n)` is the clever trick — it silently **drops** the final partial batch, which is a data-loss bug in an embedding pipeline.

**Follow-up they will ask:** "Now batch by token budget instead of count" → see Q19. "Why batch at all?" → embedding APIs accept an array of inputs per call (OpenAI's `text-embedding-3-*` currently caps the array at ~2048 entries, subject to a per-request token cap too — check the docs, don't quote it as gospel). Batching 100–500 texts/request removes one HTTP round trip per text, so wall-clock drops by roughly the batch size until you saturate the rate limit or bandwidth — an order of magnitude or two in practice.

---

### Q3. Group a list of records by a key. Two ways. When does `itertools.groupby` bite you?

`[EASY]`

**Answer:** `defaultdict(list)` in a single O(n) pass is the default answer. `itertools.groupby` only groups **consecutive** equal keys, so it requires the input to be sorted by the same key first — O(n log n) — and is the wrong tool unless the data already arrives sorted.

**Code:**

```python
import itertools
from collections import defaultdict

rows = [{"u": "a", "t": 1}, {"u": "b", "t": 2}, {"u": "a", "t": 3}]

g = defaultdict(list)
for r in rows:
    g[r["u"]].append(r["t"])
assert dict(g) == {"a": [1, 3], "b": [2]}

key = lambda r: r["u"]
g2 = {k: [r["t"] for r in v] for k, v in itertools.groupby(sorted(rows, key=key), key=key)}
assert g2 == {"a": [1, 3], "b": [2]}
```

**Complexity:** defaultdict O(n) / O(n). groupby O(n log n) because of the sort.

**Gotcha:** the `groupby` group iterator is **shared and consumed lazily** — `list(groupby(...))` gives you empty groups because advancing to the next key invalidates the previous group. You must consume each group before moving on (the dict comprehension above does). Second gotcha: `d[k].append(...)` on a plain dict raises `KeyError`; `defaultdict(list)` or `d.setdefault(k, []).append(...)` fixes it, and merely *reading* `d[missing]` on a defaultdict **inserts** the key.

**Follow-up they will ask:** "Group by two keys?" → `defaultdict(lambda: defaultdict(list))` or a tuple key `(a, b)`. "Count instead of collect?" → `collections.Counter`.

---

### Q4. Implement `deep_get(obj, "choices.0.message.content", default=None)` over arbitrary nested JSON, plus `deep_set`.

`[EASY]`

**Answer:** Split the path, walk one segment at a time, handle `Mapping` and `Sequence` separately, and use a private sentinel (not `None`) to distinguish "missing" from "present but null". This is a real production need: LLM responses are deep, optional and inconsistent.

**Constraints to ask:** are list indices in the path? is `None` a legal stored value? should a wrong-type path raise or return the default?

**Code:**

```python
from collections.abc import Mapping, MutableMapping
from typing import Any

_MISSING = object()

def deep_get(obj: Any, path: str, default: Any = None, sep: str = ".") -> Any:
    cur = obj
    for part in path.split(sep):
        if isinstance(cur, Mapping):
            cur = cur.get(part, _MISSING)
        elif isinstance(cur, (list, tuple)) and part.lstrip("-").isdigit():
            idx = int(part)
            cur = cur[idx] if -len(cur) <= idx < len(cur) else _MISSING
        else:
            return default
        if cur is _MISSING:
            return default
    return cur

def deep_set(obj: MutableMapping, path: str, value: Any, sep: str = ".") -> None:
    parts = path.split(sep)
    cur: Any = obj
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, MutableMapping):
            nxt = {}
            cur[p] = nxt          # overwrite scalars on the path
        cur = nxt
    cur[parts[-1]] = value

doc = {"choices": [{"message": {"content": "hi", "tool_calls": None}}]}
assert deep_get(doc, "choices.0.message.content") == "hi"
assert deep_get(doc, "choices.5.message") is None            # index out of range
assert deep_get(doc, "choices.0.message.tool_calls", "none") is None   # stored None wins
d: dict = {}
deep_set(d, "a.b.c", 1)
assert d == {"a": {"b": {"c": 1}}}
```

**Complexity:** O(p) for p path segments, O(1) space.

**Gotcha:** the sentinel. `cur.get(part)` returning `None` is ambiguous — a stored `null` (very common: `tool_calls: null`) would silently become your default. Use `_MISSING = object()`.

**Follow-up they will ask:** "How is this different from `jmespath`/`glom`/`pydantic`?" → correct answer: for a **known** response shape, parse it into a pydantic v2 model once (`Model.model_validate(payload)`) and get typed access plus validation; `deep_get` is for genuinely dynamic or third-party payloads.

---

### Q5. Deduplicate a list preserving order. Then do it when elements are dicts (unhashable).

`[EASY]`

**Answer:** `set` of seen keys + output list — O(n). `list(set(x))` loses order and dies on unhashable items. For dicts, canonicalise with `json.dumps(d, sort_keys=True)` (or `tuple(sorted(d.items()))` for flat dicts) as the hash key.

**Code:**

```python
import json
from collections.abc import Iterable, Mapping
from typing import Any, Callable

def dedupe(seq: Iterable, key: Callable[[Any], Any] | None = None) -> list:
    seen, out = set(), []
    for x in seq:
        k = key(x) if key else x
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out

def dedupe_unhashable(seq: Iterable[Mapping]) -> list:
    seen, out = set(), []
    for d in seq:
        k = json.dumps(d, sort_keys=True, separators=(",", ":"))
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out

assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
assert dedupe(["Ab", "aB", "c"], key=str.lower) == ["Ab", "c"]
assert dedupe_unhashable([{"a": 1, "b": 2}, {"b": 2, "a": 1}, {"a": 2}]) == [{"a": 1, "b": 2}, {"a": 2}]
```

**Complexity:** O(n) average, O(n) space. The dict variant is O(n·s) where s is the serialised size.

**Gotcha:** `dict.fromkeys(seq)` is the one-liner for hashable items and preserves insertion order since 3.7 — say it, it scores. But `True == 1` and `1.0 == 1` hash equal, so `dedupe([1, True, 1.0])` returns `[1]`.

**Follow-up they will ask:** "Now dedupe *near*-duplicate documents before embedding them" → Q27 (shingles + MinHash), or exact-dedupe by content hash (`hashlib.sha256(text.encode()).hexdigest()`) which is what you use for an ingestion idempotency key.

---

### Q6. Merge overlapping intervals. Then insert a new interval into an already-sorted, non-overlapping list.

`[MEDIUM]`

**Answer:** Merge = sort by start O(n log n), then one pass extending the last output interval while `start <= last_end`. Insert into an already-sorted list = single O(n) pass in three phases: copy the intervals strictly before, absorb every overlapping one into a running `(s, e)`, copy the rest.

**Constraints to ask:** are endpoints inclusive (`[1,4]` and `[4,5]` touch → merge)? are the inputs already sorted? mutate in place or return new?

**Brute force → optimal:** brute force is repeated pairwise merging until no change — O(n²) per sweep and up to n sweeps, so O(n³) time / O(n) space. The insight is that after sorting by start, any interval can only overlap the immediately preceding merged block.

**Code:**

```python
def merge_intervals(iv: list[list[int]]) -> list[list[int]]:
    if not iv:
        return []
    iv = sorted(iv, key=lambda x: x[0])
    out = [list(iv[0])]
    for s, e in iv[1:]:
        if s <= out[-1][1]:                 # use < if endpoints are exclusive
            out[-1][1] = max(out[-1][1], e)   # max matters: [1,10] then [2,3]
        else:
            out.append([s, e])
    return out

def insert_interval(iv: list[list[int]], new: list[int]) -> list[list[int]]:
    out, i, n = [], 0, len(iv)
    s, e = new
    while i < n and iv[i][1] < s:                       # entirely before
        out.append(iv[i]); i += 1
    while i < n and iv[i][0] <= e:                      # overlapping -> absorb
        s, e = min(s, iv[i][0]), max(e, iv[i][1]); i += 1
    out.append([s, e])
    out.extend(iv[i:])                                  # entirely after
    return out

assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert insert_interval([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
```

**Complexity:** merge O(n log n) / O(n). insert O(n) / O(n).

**Gotcha:** `out[-1][1] = e` instead of `max(...)` is the classic bug — it *shrinks* `[1,10]` when `[2,3]` arrives. Also `sorted` returns a new list; `iv.sort()` mutates the caller's list, which they may object to.

**Follow-up they will ask:** "Meeting Rooms II" → sweep line: push all `(start, +1)` and `(end, -1)`, sort, track the running max — or a min-heap of end times, O(n log n). "Where in GenAI?" → merging overlapping character spans when highlighting retrieved citations, and merging overlapping chunk offsets back into a source range.

---

### Q7. Top-K frequent items, and top-K by score from a stream you cannot hold in memory.

`[MEDIUM]`

**Answer:** In-memory: `Counter` + `heapq.nlargest(k, ...)` → O(n log k). Streaming: keep a **min-heap of size k**; for each new item, if the heap is smaller than k push, else compare against `h[0]` and `heappushpop`. O(n log k) time, **O(k) memory** — that is the whole point.

**Constraints to ask:** k relative to n? ties broken how? is the stream infinite? do we need the counts too?

**Brute force → optimal:** sort everything O(n log n) / O(n) memory → heap O(n log k) / O(k) memory. If k is close to n, sorting wins; if you need *all* frequencies bucketed, bucket sort gives O(n).

**Code:**

```python
import heapq
from collections import Counter
from collections.abc import Iterable

def top_k_freq(words: Iterable[str], k: int) -> list[tuple[str, int]]:
    c = Counter(words)
    return heapq.nlargest(k, c.items(), key=lambda kv: kv[1])   # k > n is fine: returns n

def top_k_stream(scores: Iterable[tuple[float, str]], k: int) -> list[tuple[float, str]]:
    """scores: (similarity, doc_id) pairs arriving one at a time. O(k) memory."""
    if k <= 0:
        return []                         # else `item > h[0]` IndexErrors on an empty heap
    h: list[tuple[float, str]] = []
    for item in scores:
        if len(h) < k:
            heapq.heappush(h, item)
        elif item > h[0]:                 # h[0] is the current k-th best (smallest kept)
            heapq.heappushpop(h, item)
    return sorted(h, reverse=True)

assert top_k_freq("a b a c b a".split(), 2) == [("a", 3), ("b", 2)]
assert top_k_stream([(0.1, "a"), (0.9, "b"), (0.5, "c"), (0.7, "d")], 2) == [(0.9, "b"), (0.7, "d")]
```

**Complexity:** O(n log k) time, O(k) space (plus O(distinct) for the Counter variant).

**Gotcha:** `heapq` is a **min**-heap only. For max-behaviour you either negate the key or keep a min-heap of size k as above. `heappushpop` (push then pop) is cheaper than `heappush` + `heappop`; `heapreplace` (pop then push) is the other direction and behaves differently when the new item is the smallest. If items are `(score, obj)` and `obj` is not comparable, ties raise `TypeError` — add a monotonic tiebreaker: `(score, next(counter), obj)`.

**Follow-up they will ask:** "This is exactly what a vector search does" → yes: brute-force k-NN is `sims = M @ q` then a top-k select (Q21); a HNSW index replaces the O(n) scan with an O(log n)-ish graph walk. "Counter under the hood?" → a dict subclass; `most_common(k)` itself calls `heapq.nlargest`.

---

### Q8. Implement an LRU cache with O(1) `get` and `put`. Twice: the Python way and the interview way.

`[MEDIUM]`

**Answer:** Python way — `OrderedDict` with `move_to_end` on access and `popitem(last=False)` on eviction, both O(1). Interview way — `dict` (key → node) plus a **doubly linked list** with head/tail sentinels: dict gives O(1) lookup, the DLL gives O(1) reorder and O(1) eviction of the tail. Write the sentinel version if they say "from scratch"; sentinels remove all the `if node is head` null-checking.

**Constraints to ask:** does `get` count as a use (yes, for LRU)? capacity 0? thread-safe needed? TTL needed?

**Brute force → optimal:** a plain dict + a `last_used` timestamp per key is O(n) eviction (scan for the min). A list-based recency queue is O(n) per touch (`list.remove` is O(n)). The DLL makes the reorder O(1).

**Code:**

```python
from collections import OrderedDict
from typing import Any

class LRUCacheOD:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.cap = capacity
        self._d: OrderedDict[Any, Any] = OrderedDict()

    def get(self, key: Any, default: Any = None) -> Any:
        if key not in self._d:
            return default
        self._d.move_to_end(key)                 # mark most-recently used
        return self._d[key]

    def put(self, key: Any, value: Any) -> None:
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.cap:
            self._d.popitem(last=False)          # evict least-recently used

class _Node:
    __slots__ = ("k", "v", "prev", "next")       # __slots__: no per-instance __dict__,
    def __init__(self, k=None, v=None):          # so noticeably smaller nodes at scale
        self.k, self.v = k, v
        self.prev = self.next = None

class LRUCache:
    """dict + doubly linked list. head.next = MRU, tail.prev = LRU."""
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:                        # else the first put() evicts the sentinel
            raise ValueError("capacity must be positive")
        self.cap = capacity
        self.map: dict[Any, _Node] = {}
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, n: _Node) -> None:
        n.prev.next, n.next.prev = n.next, n.prev

    def _push_front(self, n: _Node) -> None:
        n.next, n.prev = self.head.next, self.head
        self.head.next.prev = n
        self.head.next = n

    def get(self, key, default=None):
        n = self.map.get(key)
        if n is None:
            return default
        self._remove(n); self._push_front(n)
        return n.v

    def put(self, key, value) -> None:
        n = self.map.get(key)
        if n:
            n.v = value
            self._remove(n); self._push_front(n)
            return
        if len(self.map) >= self.cap:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.k]                  # must delete by the NODE's key
        n = _Node(key, value)
        self.map[key] = n
        self._push_front(n)

for cls in (LRUCacheOD, LRUCache):
    c = cls(2)
    c.put("a", 1); c.put("b", 2); assert c.get("a") == 1
    c.put("c", 3)                                # evicts "b"
    assert c.get("b") is None and c.get("a") == 1 and c.get("c") == 3
```

**Complexity:** O(1) `get`/`put` amortised, O(capacity) space.

**Gotcha:** three classic bugs — (1) forgetting to delete the evicted key from the dict → memory leak, cache reports a hit and returns a dangling node; (2) `put` on an existing key not refreshing recency; (3) evicting **before** checking whether the key already exists, which can evict the very key you are updating. Fourth, the one they set as a trap: **capacity 0** — without the guard above, `put` walks `tail.prev` onto the head sentinel and dies on `None.next`. Also: the DLL version is not thread-safe — wrap every method in a `threading.Lock` if shared.

**Follow-up they will ask:** "Why not just `functools.lru_cache`?" → it is C-implemented, thread-safe and faster, but it keys on the *arguments*, has no TTL, no per-entry invalidation, no size-in-bytes limit, and holds strong references to arguments (leak risk with `self`, hence `functools.cached_property` or a weakref for methods). "Make it TTL-aware" → Q9. "Make it LFU" → Q35. "In a GenAI service?" → cache embeddings by `sha256(text)` and cache LLM responses by `hash(model, temperature, prompt)`. On repetitive workloads (FAQ-style traffic, re-ingesting an overlapping corpus) hit rates in the tens of percent are common — but that is workload-dependent, so quote *your* measured number, not a benchmark you half-remember.

---

### Q9. Write a `@ttl_cache(ttl=60)` decorator: memoize with expiry and a max size.

`[MEDIUM]`

**Answer:** Closure holding an `OrderedDict` of `key -> (expires_at, value)`, `time.monotonic()` for the clock, a `Lock` for thread safety, LRU eviction when over `maxsize`. Call the wrapped function **outside** the lock so a slow LLM call does not serialise every other caller.

**Constraints to ask:** thread-safe or single-threaded? per-entry TTL? need `cache_clear`/`cache_info` parity with `functools`? are the arguments hashable?

**Code:**

```python
import threading, time
from collections import OrderedDict
from functools import wraps
from typing import Any

def ttl_cache(ttl: float, maxsize: int = 128):
    def deco(fn):
        store: OrderedDict[Any, tuple[float, Any]] = OrderedDict()
        lock = threading.Lock()
        hits = misses = 0

        @wraps(fn)                                     # keeps __name__, __doc__, __wrapped__
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()                     # monotonic: immune to NTP/DST jumps
            with lock:
                hit = store.get(key)
                if hit and hit[0] > now:
                    store.move_to_end(key)
                    hits += 1
                    return hit[1]
                if hit:
                    del store[key]                     # expired
            val = fn(*args, **kwargs)                  # computed OUTSIDE the lock
            with lock:
                # re-read the clock: fn may have taken longer than ttl, and
                # `now + ttl` would then store an already-expired entry
                store[key] = (time.monotonic() + ttl, val)
                store.move_to_end(key)
                misses += 1
                while len(store) > maxsize:
                    store.popitem(last=False)
            return val

        wrapper.cache_clear = lambda: store.clear()
        wrapper.cache_info = lambda: {"hits": hits, "misses": misses, "size": len(store)}
        return wrapper
    return deco

calls = {"n": 0}

@ttl_cache(ttl=0.05)
def slow(x):
    calls["n"] += 1
    return x * 2

assert slow(2) == 4 and slow(2) == 4 and calls["n"] == 1
time.sleep(0.06)
assert slow(2) == 4 and calls["n"] == 2          # expired -> recomputed
```

**Complexity:** O(1) per call, O(maxsize) memory.

**Gotcha:** computing outside the lock means two threads can miss simultaneously and both compute (a "thundering herd"). That is the deliberate trade — say it. If duplicate work is expensive (an LLM call), add a per-key in-flight `Event` or `future` so the second caller waits on the first. Also: `time.time()` is wall-clock and can go backwards; always `time.monotonic()` for durations.

**Follow-up they will ask:** "Why not `functools.lru_cache`?" → no TTL, and it never expires — stale forever. "Async version?" → the same shape with `asyncio.Lock` and `async def wrapper`, but `functools.lru_cache` on a coroutine function caches the *coroutine object*, which can only be awaited once — a real, frequently-shipped bug. "Distributed?" → Redis `SETEX` with the same hash key; then TTL is server-side and shared across pods.

---

### Q10. Write a retry decorator with exponential backoff and jitter. Sync and async.

`[MEDIUM]`

**Answer:** Loop `tries` times; on a *retryable* exception sleep `random.uniform(0, min(cap, base * 2**attempt))` (full jitter) then retry; re-raise on the last attempt. Jitter matters because synchronised retries from 50 pods re-create the exact spike that caused the 429.

**Constraints to ask:** which exceptions are retryable (429, 500, 502, 503, timeouts — **not** 400/401/422)? is the operation idempotent? is there a `Retry-After` header to honour? total deadline vs per-attempt timeout?

**Code:**

```python
import asyncio, random, time
from functools import wraps

def retry(exceptions=(Exception,), tries=5, base=0.5, cap=30.0, jitter="full", sleep=time.sleep):
    """Full jitter: delay = uniform(0, min(cap, base * 2**attempt)). AWS-recommended."""
    if tries < 1:
        raise ValueError("tries must be >= 1")
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            for attempt in range(tries):
                try:
                    return fn(*a, **kw)
                except exceptions as exc:
                    if attempt == tries - 1:
                        raise                      # exhausted: surface the real error
                    backoff = min(cap, base * 2 ** attempt)
                    sleep(random.uniform(0, backoff) if jitter == "full" else backoff)
            raise AssertionError("unreachable")
        return wrapper
    return deco

def aretry(exceptions=(Exception,), tries=5, base=0.5, cap=30.0):
    if tries < 1:
        raise ValueError("tries must be >= 1")
    def deco(fn):
        @wraps(fn)
        async def wrapper(*a, **kw):
            for attempt in range(tries):
                try:
                    return await fn(*a, **kw)
                except exceptions:
                    if attempt == tries - 1:
                        raise
                    await asyncio.sleep(random.uniform(0, min(cap, base * 2 ** attempt)))
            raise AssertionError("unreachable")
        return wrapper
    return deco

state = {"n": 0}

@retry(exceptions=(ValueError,), tries=4, base=0.001)
def flaky():
    state["n"] += 1
    if state["n"] < 3:
        raise ValueError("boom")
    return "ok"

assert flaky() == "ok" and state["n"] == 3
```

**Complexity:** O(tries) calls; worst-case added latency ≈ `sum(min(cap, base*2**i))`. Quote it: base 0.5 s, 5 tries → up to 0.5+1+2+4 = 7.5 s of sleeping.

**Gotcha:** (1) Retrying a **non-idempotent** POST duplicates work — send an `Idempotency-Key`. (2) Retrying a 400/401 is pure waste and hides the bug. (3) Without jitter you get retry storms. (4) `@wraps` is not optional — without it, FastAPI's introspection of the wrapped handler breaks and your logs show `wrapper` everywhere. (5) Injecting `sleep` (as above) makes the decorator testable without real delays.

**Follow-up they will ask:** "Do you write this yourself in production?" → the honest answer scores: `tenacity` (`@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6), retry=retry_if_exception_type(RateLimitError))`), and note that the `openai` Python SDK v1.x already retries twice by default — configurable via `OpenAI(max_retries=5, timeout=30.0)` — so double-wrapping it silently multiplies your attempts. "Where does the circuit breaker fit?" → Q37: retries handle *blips*, breakers handle *outages*.

---

### Q11. Implement a token-bucket rate limiter.

`[MEDIUM]`

**Answer:** Store `tokens` and `last_refill`. On each request, lazily refill `tokens += elapsed * rate` capped at `capacity`, then spend if `tokens >= cost`. Lazy refill means no background thread. `capacity` is the burst allowance; `rate` is the steady state.

**Constraints to ask:** allow bursts? per-user or global? cost per request uniform (RPM) or weighted (TPM by token count)? distributed across pods?

**Brute force → optimal:** naive fixed-window counters allow a 2× burst at the window edge (100 calls at 0:59 + 100 at 1:01). Token bucket smooths this and still permits a controlled burst.

**Code:**

```python
import threading, time

class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self.rate, self.capacity = rate, capacity     # rate = tokens/sec, capacity = burst
        self.tokens = float(capacity)
        self.ts = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
        self.ts = now

    def allow(self, cost: float = 1.0) -> bool:
        """Non-blocking: True if allowed, False -> caller returns HTTP 429."""
        with self._lock:
            self._refill()
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False

    def acquire(self, cost: float = 1.0) -> float:
        """Blocking: sleeps until enough tokens exist. Returns seconds actually waited."""
        if cost > self.capacity:
            raise ValueError("cost exceeds capacity: this would block forever")
        waited = 0.0
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= cost:
                    self.tokens -= cost
                    return waited                     # emit this as a metric
                wait = (cost - self.tokens) / self.rate
            time.sleep(wait)                          # sleep OUTSIDE the lock
            waited += wait

tb = TokenBucket(rate=100, capacity=3)
assert [tb.allow() for _ in range(4)] == [True, True, True, False]
time.sleep(0.03)
assert tb.allow() is True                             # refilled ~3 tokens
```

**Complexity:** O(1) time and O(1) space per bucket. For per-user limiting: a dict of buckets — bound it with an LRU or you leak memory on unbounded user IDs.

**Gotcha:** sleeping while holding the lock serialises every other thread (deadlock-adjacent). Refill must be **capped** at capacity or an idle bucket accumulates infinite burst. `cost` as a float is how you implement **token-per-minute (TPM)** limits for Azure OpenAI: cost = estimated prompt tokens + `max_tokens`.

**Follow-up they will ask:** "Distributed across 10 pods?" → Redis, either a Lua script doing the compare-and-decrement atomically, or `INCR` + `EXPIRE` for a fixed window; without atomicity you oversend and get 429-storms. "Leaky bucket vs token bucket?" → leaky bucket enforces a strictly constant output rate (queue-based, no bursts); token bucket allows bursts up to capacity. Cloud APIs use token bucket.

---

### Q12. Implement a sliding-window-log rate limiter, and the sliding-window-counter approximation.

`[MEDIUM]`

**Answer:** Log = a `deque` of timestamps per key; evict entries older than the window from the left, allow if `len(dq) < limit`. Exact, but O(limit) memory per key. Counter = keep only the current and previous window counts and interpolate — O(1) memory and a small, bounded misclassification rate (Cloudflare published ~0.003% of requests wrongly allowed/blocked on *their* traffic; treat that as an order of magnitude, not a guarantee for your workload). This is what Cloudflare-style limiters ship.

**Code:**

```python
import threading, time
from collections import defaultdict, deque

class SlidingWindowLog:
    """Exact. Memory O(limit) per key."""
    def __init__(self, limit: int, window: float) -> None:
        self.limit, self.window = limit, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            dq = self.hits[key]
            cutoff = now - self.window
            while dq and dq[0] <= cutoff:
                dq.popleft()                    # amortised O(1) per eviction
            if len(dq) < self.limit:
                dq.append(now)
                return True
            return False

class SlidingWindowCounter:
    """Approximate, O(1) memory: weighted blend of previous and current window."""
    def __init__(self, limit: int, window: float) -> None:
        self.limit, self.window = limit, window
        self.cur_start = time.monotonic()
        self.cur = self.prev = 0

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.cur_start
        if elapsed >= self.window:
            self.prev = self.cur if elapsed < 2 * self.window else 0   # idle gap -> drop
            self.cur = 0
            self.cur_start = now
            elapsed = 0.0
        weight = 1 - elapsed / self.window
        if self.prev * weight + self.cur < self.limit:
            self.cur += 1
            return True
        return False

sw = SlidingWindowLog(limit=2, window=0.05)
assert [sw.allow("u1") for _ in range(3)] == [True, True, False]
assert sw.allow("u2") is True                   # per-key isolation
time.sleep(0.06)
assert sw.allow("u1") is True

swc = SlidingWindowCounter(limit=2, window=0.05)
assert [swc.allow() for _ in range(3)] == [True, True, False]
```

**Complexity:** log — O(1) amortised time, O(limit) space per key. counter — O(1) / O(1).

**Gotcha:** the log limiter's memory is `active_keys × limit × bytes_per_timestamp`. Eight bytes is the *theoretical floor* (a raw C double) — 1 M users at limit 1000 is 8 GB. In CPython a `deque` of `float` objects costs roughly 30–40 bytes per entry (object header + slot pointer), so the real figure is tens of GB. Either way the order of magnitude is the reason the counter approximation exists. Also `defaultdict` never removes empty deques → unbounded key growth; sweep or use an LRU of deques.

**Follow-up they will ask:** "Which one for our LLM gateway?" → token bucket for TPM/RPM upstream shaping, sliding-window counter in Redis for per-tenant quotas, and always surface `Retry-After` on 429 so clients back off correctly. Comparison table:

| Algorithm | Memory/key | Exact? | Bursts | Typical use |
|---|---|---|---|---|
| Fixed window counter | O(1) | No (2× edge burst) | Yes, at edges | Crude quotas |
| Sliding window log | O(limit) | Yes | No | Low-cardinality, strict limits |
| Sliding window counter | O(1) | Approximate (small, bounded error) | Smoothed | Web-scale per-tenant limits |
| Token bucket | O(1) | Yes | Up to capacity | Client-side API pacing, TPM |
| Leaky bucket | O(queue) | Yes | No | Constant-rate egress |

---

### Q13. Make a thread-safe singleton. Three ways. Which do you actually ship?

`[MEDIUM]`

**Answer:** Ship the **module-level instance** — Python modules are imported once and the import machinery holds a lock, so a module global *is* a thread-safe singleton, and it stays testable. If they want a class: a metaclass with **double-checked locking**. `__new__`-based singletons are the trap because `__init__` still runs on every "construction".

**Code:**

```python
import threading
from typing import Any

class SingletonMeta(type):
    _instances: dict[type, Any] = {}
    _lock = threading.Lock()

    def __call__(cls, *a, **kw):
        if cls not in cls._instances:              # fast path: no lock on the hot path
            with cls._lock:
                if cls not in cls._instances:      # re-check: another thread may have won
                    cls._instances[cls] = super().__call__(*a, **kw)
        return cls._instances[cls]

class Settings(metaclass=SingletonMeta):
    def __init__(self, env: str = "dev") -> None:
        self.env = env

assert Settings("prod") is Settings("ignored")     # second call's args are IGNORED
results = []
ts = [threading.Thread(target=lambda: results.append(Settings())) for _ in range(20)]
[t.start() for t in ts]; [t.join() for t in ts]
assert len({id(r) for r in results}) == 1

# What you actually ship: a PLAIN class (drop the metaclass entirely) plus one
# lazily-built, cached factory. lru_cache is what makes it a singleton here.
from functools import lru_cache

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings("prod")                        # FastAPI: Depends(get_settings)
```

**Complexity:** O(1); one lock acquisition on the very first call only.

**Gotcha:** (1) the `__new__` version silently re-runs `__init__` and wipes state — that is the bug they are fishing for. (2) The singleton silently ignores constructor args after the first call. (3) Singletons + `fork` (Gunicorn preload) = each worker gets its own copy; a shared HTTP client or DB pool created **before** fork breaks. Create clients in the worker's startup hook (FastAPI `lifespan`). (4) Under `--reload` or multiple modules imported by different paths you can get two instances.

**Follow-up they will ask:** "Where in your GenAI service?" → one `OpenAI()`/`AsyncAzureOpenAI()` client per process (it holds an `httpx` connection pool — recreating it per request throws away the pool and forces a fresh TCP + TLS handshake, which costs a couple of extra round trips; on a cross-region hop that is typically tens to low hundreds of milliseconds, so measure it rather than quoting a number), one embedding model, one vector-DB client. In FastAPI express it as a `lifespan`-created object on `app.state` plus `Depends`, not a global — because `Depends` is overridable in tests.

---

### Q14. Write a context manager two ways. What does returning `True` from `__exit__` do?

`[EASY]`

**Answer:** Class with `__enter__`/`__exit__`, or a generator with `@contextlib.contextmanager` and `try/finally`. Returning a **truthy** value from `__exit__` **suppresses** the exception; returning `False`/`None` lets it propagate. Suppressing by accident is a top-tier production bug.

**Code:**

```python
import time
from contextlib import contextmanager

class Timer:
    """Class form: reusable, can hold state, can be a decorator via ContextDecorator."""
    def __init__(self, label: str) -> None:
        self.label, self.elapsed = label, 0.0

    def __enter__(self) -> "Timer":
        self.t0 = time.perf_counter()
        return self                      # whatever you return binds to `as`

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.elapsed = time.perf_counter() - self.t0
        print(f"{self.label}: {self.elapsed * 1000:.1f} ms  failed={exc_type is not None}")
        return False                     # False -> do NOT swallow the exception

@contextmanager
def timed(label: str):
    """Generator form: shorter. Exactly ONE yield. try/finally is mandatory."""
    t0 = time.perf_counter()
    try:
        yield t0
    finally:                             # runs even if the body raises
        print(f"{label}: {(time.perf_counter() - t0) * 1000:.1f} ms")

with Timer("llm_call") as t:
    pass
assert t.elapsed >= 0

with timed("retrieval"):
    pass
```

**Complexity:** O(1).

**Gotcha:** without `try/finally` in the generator form, an exception in the body skips your cleanup entirely (the generator is never resumed past the `yield`). `contextlib.suppress(FileNotFoundError)` is the idiomatic "ignore this error". `contextlib.ExitStack` handles a dynamic number of contexts. Async version: `__aenter__`/`__aexit__` or `@asynccontextmanager` (this is exactly what FastAPI's `lifespan` is).

**Follow-up they will ask:** "Real uses in your service?" → DB session/transaction scope, `httpx.AsyncClient` lifetime, temporarily overriding a config, an LLM tracing span (`with tracer.start_as_current_span("rag.retrieve")`), and token/cost accounting per request. "Can a context manager be reentrant?" → the `@contextmanager` generator form is **single-use**; re-entering raises `RuntimeError: generator didn't yield`. Use `contextlib.ContextDecorator` or a fresh instance.

---

### Q15. Read a 50 GB file without loading it into memory. Give me a chunk generator and a batched-lines generator.

`[EASY]`

**Answer:** Generators. `for line in file` is already lazy and buffered — never `f.readlines()` or `f.read()`. For binary/fixed-size work, loop on `f.read(size)` with the walrus operator. Memory stays O(chunk), not O(file).

**Code:**

```python
from collections.abc import Iterator

def read_chunks(path: str, size: int = 1 << 20) -> Iterator[bytes]:
    """Fixed-size binary chunks; 1 MiB is a good default."""
    with open(path, "rb") as fh:
        while chunk := fh.read(size):
            yield chunk

def read_line_batches(path: str, batch: int = 1000) -> Iterator[list[str]]:
    """Line-oriented batching — what you feed an embeddings API."""
    with open(path, "r", encoding="utf-8") as fh:
        buf: list[str] = []
        for line in fh:                  # lazy, buffered, decodes incrementally
            buf.append(line.rstrip("\n"))
            if len(buf) == batch:
                yield buf
                buf = []
        if buf:                          # never forget the final partial batch
            yield buf

def read_jsonl(path: str) -> Iterator[dict]:
    import json
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"bad JSON on line {i}: {exc}") from exc
```

**Complexity:** O(N) time, O(chunk) memory.

**Gotcha:** (1) Fixed-size **byte** chunks split multi-byte UTF-8 characters and split words — if you are chunking text for embeddings, chunk on decoded text with overlap (Q17), not raw bytes. (2) The `with` block closes the file when the generator is exhausted **or** garbage-collected — if a caller abandons the generator halfway, the fd stays open until GC; `contextlib.closing` or consuming fully avoids fd exhaustion. (3) `open()` without `encoding=` uses the platform default (`cp1252` on Windows) → `UnicodeDecodeError` in prod but not on your laptop. Always pass `encoding="utf-8"`.

**Follow-up they will ask:** "How would you parallelise ingestion?" → read lazily on one thread, `batched()` it, then fan out batches to an async pool (Q28) with bounded concurrency; the file read is I/O-bound and the embedding calls are network-bound, so asyncio beats multiprocessing here. "Memory proof?" → `tracemalloc` or `psutil.Process().memory_info().rss` before/after.

---

### Q16. Spot the bug in each of these four snippets.

`[MEDIUM]`

**Answer:** Mutable default argument; late-binding closure; aliased rows from `[[0]*n]*m`; and `is` vs `==` on interned values. These are the four they hand you on paper to see if you actually know Python.

**Code:**

```python
# 1) Mutable default argument: evaluated ONCE, at function-definition time.
def bad(item, bucket=[]):
    bucket.append(item)
    return bucket
assert bad(1) == [1] and bad(2) == [1, 2]          # the second call sees the first's data

def good(item, bucket=None):
    bucket = [] if bucket is None else bucket
    bucket.append(item)
    return bucket
assert good(1) == [1] and good(2) == [2]

# 2) Late binding: the lambda reads `i` when CALLED, not when created.
fs = [lambda: i for i in range(3)]
assert [f() for f in fs] == [2, 2, 2]
fs2 = [lambda i=i: i for i in range(3)]            # bind now via a default arg
assert [f() for f in fs2] == [0, 1, 2]

# 3) List multiplication copies the REFERENCE, not the row.
grid = [[0] * 2] * 2
grid[0][0] = 9
assert grid == [[9, 0], [9, 0]]                    # both "rows" are the same object
grid2 = [[0] * 2 for _ in range(2)]
grid2[0][0] = 9
assert grid2 == [[9, 0], [0, 0]]

# 4) `is` compares identity, not value. Small ints (-5..256) and short strings are interned.
a, b = 256, 256
assert (a is b) is True
c, d = 1000, 1000                                  # True in the REPL per-statement,
assert (c == d) is True                            # never rely on it -> use ==
```

**Complexity:** n/a.

**Gotcha:** the mutable-default bug is *useful* exactly once — as a deliberate memo cache — and even then say so in a comment. In pydantic v2 the equivalent is `Field(default_factory=list)`; a bare `x: list = []` on a `BaseModel` is safe in pydantic (it deep-copies defaults) but **not** in a plain `@dataclass`, which raises `ValueError: mutable default` and forces `field(default_factory=list)`.

**Follow-up they will ask:** "Deep vs shallow copy" → `copy.copy` copies the outer container only; `copy.deepcopy` recurses and handles cycles via a memo dict but is slow — for plain JSON data `json.loads(json.dumps(x))` is often faster. "Why is `[[0]*2]*2` shared but `[0]*2` fine?" → because `int` is immutable, so aliasing is unobservable.

---

## 3. Text & GenAI-flavoured problems

This is the section that maps to the JD. If they ask only one coding question in this round, there is a strong chance it is a **chunker** or a **cosine top-k**.

### Q17. Write a text chunker with overlap — by words and by characters.

`[MEDIUM]`

**Answer:** Step by `size - overlap` and slice. The overlap exists so a fact split across a boundary still appears whole in at least one chunk. Guard `overlap < size` or the loop never advances (infinite generator — a real outage).

**Constraints to ask:** chunk unit — characters, words, or tokens? overlap in the same unit? must chunks align to sentences/paragraphs (Q18)? do we return offsets for citations?

**Brute force → optimal:** the naive `text.split()` + fixed slices is already O(n); the engineering is in the guards, the offsets, and the unit choice.

**Code:**

```python
from collections.abc import Iterator

def chunk_words(text: str, size: int = 200, overlap: int = 40) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap must be < size, else the window never advances")
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(len(words), 1), step)
            if words[i:i + size]]

def chunk_chars(text: str, size: int = 1000, overlap: int = 150) -> Iterator[str]:
    if overlap >= size:
        raise ValueError("overlap must be < size")
    step, n, i = size - overlap, len(text), 0
    while i < n:
        yield text[i:i + size]
        i += step

def chunk_with_offsets(text: str, size: int = 1000, overlap: int = 150):
    """Return (chunk, start, end) so citations can point back at the source."""
    step, n, i = size - overlap, len(text), 0
    while i < n:
        yield text[i:i + size], i, min(i + size, n)
        i += step

t = " ".join(str(i) for i in range(10))
assert chunk_words(t, size=4, overlap=2) == ["0 1 2 3", "2 3 4 5", "4 5 6 7", "6 7 8 9", "8 9"]
assert list(chunk_chars("abcdefg", size=4, overlap=1)) == ["abcd", "defg", "g"]
assert chunk_words("", 4, 2) == []
```

**Complexity:** O(n · size/step) time and output size — i.e. with 20% overlap you store ~1.25× the corpus. Say that number; it drives your vector-DB sizing.

**Gotcha:** (1) `overlap >= size` → infinite loop. (2) Empty input must not produce `[""]`. (3) Word chunking with `" ".join` **destroys the original whitespace/newlines** — you cannot map back to source offsets afterwards, hence the offsets variant. (4) Characters ≠ tokens: English prose averages **~4 characters/token**; code is worse (~3.3 chars/token on `cl100k_base`) and Indic scripts are far worse. Measured on `cl100k_base`, Hindi in Devanagari comes out at roughly **1 token per character** (~1.5 on the older GPT-2/p50k BPEs). So a 1000-char chunk is ~250 tokens of English prose but on the order of **1000 tokens** of Hindi — a 4× blow-up that will silently overflow a budget you sized in characters. `o200k_base` improved Devanagari a lot (~0.3 tokens/char in the same test), so the multiplier is encoding-specific: measure with `tiktoken` on your own corpus.

**Follow-up they will ask:** "What size and overlap did you ship, and why?" → the defensible answer: 400–800 tokens with 10–20% overlap for prose RAG, smaller (200–300) when the corpus is FAQ-like and precision matters, larger (1000–1500) for narrative documents where context is needed; tune by measuring retrieval recall@k on a labelled question set, not by vibes. "Token-accurate version?" → `tiktoken`: `enc = tiktoken.get_encoding("cl100k_base")` (`o200k_base` for GPT-4o-family), chunk on `enc.encode(text)` ids and `enc.decode` the slices.

---

### Q18. Chunk text without splitting sentences, still respecting a token budget with sentence overlap.

`[MEDIUM]`

**Answer:** Split into sentences first, then greedily pack sentences into a chunk until the next one would exceed the budget; start the next chunk with the last k sentences of the previous one as overlap. Sentence splitting by regex needs abbreviation lookbehinds or "Dr. Rao" becomes two sentences.

**Constraints to ask:** language? are there markdown headers/tables/code blocks to preserve? is a single sentence allowed to exceed the budget (yes — then hard-split it)?

**Brute force → optimal:** naive `text.split(". ")` is the brute force and it breaks on abbreviations, decimals ("3.5 turbo"), ellipses and quoted speech. The regex below fixes the common cases; a real system uses `spacy`/`nltk`/`pysbd` or a markdown-aware recursive splitter.

**Code:**

```python
import math, re

_ABBR = (r"(?<!\bMr\.)(?<!\bMrs\.)(?<!\bDr\.)(?<!\bNo\.)(?<!\bFig\.)"
         r"(?<!\bvs\.)(?<!\bi\.e\.)(?<!\be\.g\.)(?<!\bEq\.)")
_SENT = re.compile(_ABBR + r"(?<=[.!?])[\"')\]]*\s+")

def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text.strip()) if s.strip()]

def approx_tokens(s: str) -> int:
    return max(1, math.ceil(len(s) / 4))          # ~4 chars/token for English

def chunk_sentences(text: str, max_tokens: int = 256, overlap_sentences: int = 1,
                    count=approx_tokens) -> list[str]:
    sents = split_sentences(text)
    chunks: list[str] = []
    cur: list[str] = []
    cur_tok = 0
    for s in sents:
        n = count(s)
        if cur and cur_tok + n > max_tokens:      # flush before adding
            chunks.append(" ".join(cur))
            cur = cur[-overlap_sentences:] if overlap_sentences else []
            cur_tok = sum(count(x) for x in cur)
        cur.append(s)
        cur_tok += n
    if cur:
        chunks.append(" ".join(cur))
    return chunks

txt = "Dr. Rao joined in 2019. He built RAG systems. They scaled to 5M docs! Was it fast? Yes."
assert split_sentences(txt) == ["Dr. Rao joined in 2019.", "He built RAG systems.",
                                "They scaled to 5M docs!", "Was it fast?", "Yes."]
cs = chunk_sentences(txt, max_tokens=12, overlap_sentences=1)
for prev, nxt in zip(cs, cs[1:]):
    assert nxt.startswith(split_sentences(prev)[-1])     # overlap really carries over
```

**Complexity:** O(n) in characters if `count` is O(len(s)); the `sum` over the overlap tail is O(overlap) per flush, negligible.

**Gotcha:** a single sentence longer than `max_tokens` will produce an over-budget chunk — you must hard-split it with Q17's char chunker, or you blow the embedding model's input limit (8191 tokens for `text-embedding-3-*`). Also: `re` lookbehinds must be **fixed-width** in Python, which is why each abbreviation gets its own `(?<!...)` group.

**Follow-up they will ask:** "What does LangChain do?" → `RecursiveCharacterTextSplitter` tries separators in order `["\n\n", "\n", " ", ""]` and recurses until the chunk fits — same idea, more separators. Modern import: `from langchain_text_splitters import RecursiveCharacterTextSplitter`. "Semantic chunking?" → embed sentences, cut where consecutive-sentence cosine similarity drops below a percentile threshold; often better recall, but you now pay one embedding call per *sentence* at ingest instead of one per chunk — so ingest cost scales with sentences-per-chunk, roughly an order of magnitude on typical prose.

---

### Q19. You have 40 ranked chunks and a 6000-token context budget. Pack the prompt.

`[MEDIUM]`

**Answer:** Greedy by score: walk best-first, add a chunk if it fits the remaining budget, skip if not, keep going (a small chunk further down may still fit). Reserve headroom for the system prompt, the question, and `max_tokens` for the answer — the budget is **shared** between input and output.

**Constraints to ask:** is a partial chunk acceptable (usually no)? must the final order be by score or by document order? how many tokens for the answer?

**Brute force → optimal:** this is 0/1 knapsack (value = relevance, weight = tokens); exact DP is O(n·budget) which is 40 × 6000 = fine, but pointless — relevance scores are noisy estimates, so greedy is within noise and O(n log n). Say exactly that: "knapsack is available but not worth it here."

**Code:**

```python
import math

def approx_tokens(s: str) -> int:
    return max(1, math.ceil(len(s) / 4))

def pack_context(chunks: list[tuple[str, float]], budget: int, count=approx_tokens,
                 reserve: int = 0) -> tuple[list[str], int]:
    """chunks: (text, score). Greedy best-first fill; `reserve` = room for the answer."""
    remaining = budget - reserve
    picked: list[str] = []
    for text, _score in sorted(chunks, key=lambda c: -c[1]):
        n = count(text)
        if n <= remaining:
            picked.append(text)
            remaining -= n
    return picked, budget - reserve - remaining

picked, used = pack_context([("a" * 40, 0.9), ("b" * 40, 0.8), ("c" * 400, 0.7)],
                            budget=25, reserve=5)
assert picked == ["a" * 40, "b" * 40] and used == 20
```

**Complexity:** O(n log n) for the sort, O(n) for the fill.

**Gotcha:** (1) Use the real tokenizer (`tiktoken`) for the final gate — `len/4` under-counts code by ~20% and Devanagari-script text by ~4× on `cl100k_base` (Q17), and an under-count means the API rejects the request with a 400 before it generates anything. (2) **Lost in the middle**: models attend best to the beginning and end of the context, so after packing, re-order the chosen chunks so the strongest are first and last. (3) Deduplicate near-identical chunks *before* packing (Q27) or you waste half the budget on the same paragraph.

**Follow-up they will ask:** "What are the real budgets?" → GPT-4o/4.1-class context windows are 128K+ (GPT-4.1 family goes to ~1M), but cost and latency scale with *actual* tokens sent, and quality degrades well before the limit — most production RAG sends 2K–8K tokens of context, not 100K. "How do you count tokens for a chat call?" → tokenize each message's content and add the per-message overhead (~3–4 tokens/message plus a few for the reply priming); the exact scheme is documented per model family.

---

### Q20. Cosine similarity from scratch — pure Python and numpy. Then for a whole matrix.

`[EASY]`

**Answer:** `cos(a,b) = (a·b) / (|a||b|)`. Pure Python is one loop accumulating dot and both norms. In numpy it is `a @ b / (norm(a) * norm(b))`. For 1-vs-N, **pre-normalise once** and the whole thing collapses to a single matrix-vector product — that is the trick they want.

**Constraints to ask:** are the embeddings already L2-normalised (OpenAI's are)? dimension? zero vectors possible?

**Brute force → optimal:** a Python loop over 1 M × 1536 floats runs into the minutes; the numpy `@` version is BLAS-backed and lands around a second. Quote it as "roughly two orders of magnitude" rather than an exact multiple — the factor depends on BLAS build, threading and dtype.

**Code:**

```python
import math
import numpy as np

def cosine_py(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dim mismatch")
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0                       # define it; don't divide by zero
    return dot / math.sqrt(na * nb)

def cosine_np(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else float(a @ b / (na * nb))

def cosine_matrix(q: np.ndarray, M: np.ndarray) -> np.ndarray:
    """1 query vs N docs -> (N,) similarities. One BLAS call."""
    qn = q / (np.linalg.norm(q) + 1e-12)
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
    return Mn @ qn

assert abs(cosine_py([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9      # same direction, any scale
assert abs(cosine_py([1, 0], [0, 1])) < 1e-9                  # orthogonal
assert cosine_py([0, 0], [1, 1]) == 0.0
sims = cosine_matrix(np.array([1.0, 0]), np.array([[1.0, 0], [0, 1.0], [1.0, 1.0]]))
assert abs(sims[2] - 0.7071) < 1e-3
```

**Complexity:** O(d) per pair; O(N·d) for 1-vs-N — with N = 1 M and d = 1536 that is 1.5 G multiply-adds ≈ 0.5–2 s single-threaded numpy, ~6 GB of float32 to hold the matrix.

**Gotcha:** (1) If vectors are already unit-length, cosine **is** the dot product — skip the norms (this is why vector DBs offer an "inner product" metric and why OpenAI docs say you can use dot product directly). (2) Cosine ranks identically to Euclidean distance **only** for normalised vectors. (3) `1e-12` guard beats an `if` for vectorised code. (4) Cosine ranges [-1, 1] mathematically but real embedding pairs cluster in [0, 1] — an "absolute" threshold like 0.8 is model-specific and does not transfer between embedding models.

**Follow-up they will ask:** "Dimensions and cost?" → `text-embedding-3-small` = 1536 dims (`-large` = 3072, both support Matryoshka truncation via the `dimensions` parameter); `ada-002` = 1536. float32 storage = dims × 4 bytes/vector, so 1 M × 1536 × 4 ≈ 6.1 GB before index overhead. "Why not Euclidean?" → for text embeddings, magnitude carries little semantic signal; cosine removes it.

---

### Q21. Brute-force k-NN: given a query vector and a matrix of N document vectors, return the top-k.

`[MEDIUM]`

**Answer:** `sims = M_normalised @ q_normalised`, then `np.argpartition(-sims, k-1)[:k]` for an **O(N)** selection, then sort just those k. Full `np.argsort` is O(N log N) and wasteful when k ≪ N.

**Constraints to ask:** N? does the matrix fit in RAM? pre-normalised? do we need scores or just ids? filters (metadata) applied before or after?

**Brute force → optimal:** loop + `cosine_py` per row (O(N·d) in slow Python) → vectorised matmul (same O, ~two orders of magnitude better constant) → `argpartition` instead of `argsort` for the top-k step.

**Code:**

```python
import numpy as np

def cosine_matrix(q: np.ndarray, M: np.ndarray) -> np.ndarray:
    qn = q / (np.linalg.norm(q) + 1e-12)
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
    return Mn @ qn

def top_k_vectors(query: np.ndarray, matrix: np.ndarray, k: int = 5,
                  normalized: bool = False) -> list[tuple[int, float]]:
    sims = matrix @ query if normalized else cosine_matrix(query, matrix)
    k = max(0, min(k, sims.shape[0]))               # guard k > N and negative k
    if k == 0:
        return []
    idx = np.argpartition(-sims, k - 1)[:k]         # O(N) select, unordered
    idx = idx[np.argsort(-sims[idx])]               # O(k log k) order the k
    return [(int(i), float(sims[i])) for i in idx]

rng = np.random.default_rng(0)
M = rng.normal(size=(1000, 64))
hits = top_k_vectors(M[7] * 1.5, M, k=3)
assert hits[0][0] == 7 and abs(hits[0][1] - 1.0) < 1e-6
```

**Complexity:** O(N·d) for the scores + O(N) for the selection, O(N) memory for `sims`. At N = 1 M, d = 1536, float32: ~6 GB resident, ~0.5–2 s per query — which is precisely why you switch to an ANN index (HNSW/IVF) above roughly 100 K vectors.

**Gotcha:** (1) `argpartition` gives you the k smallest by default — negate for largest, and the returned k are **unordered**. (2) The `kth` argument is `k - 1` and must be in `[0, N-1]`, so `k` may be anywhere in `1..N` — `k = N` is legal, the common "k must be < N" belief is wrong, and the `min(k, N)` clamp is what makes `k > N` safe. The nastier case is a **negative** k: numpy happily accepts a negative `kth` and `[:k]` then trims from the end, so `k = -1` silently returns `N-1` results instead of raising. Clamp with `max(0, ...)`. (3) Normalise **once at ingest**, store unit vectors, and then every query is a pure dot product. (4) float32 not float64 — half the memory, no measurable recall loss.

**Follow-up they will ask:** "When do you stop doing this and use FAISS/pgvector/Azure AI Search?" → past ~100 K vectors or when p95 latency must be <50 ms; HNSW gives ~O(log N) search with 95–99% recall, tuned by `M` (graph degree, 16–64) and `ef_search` (candidate list, 40–400). "Filtered search?" → post-filtering breaks recall (you may filter away all k); pre-filtering needs index support (Qdrant/Weaviate/Azure AI Search do it natively); a common fallback is over-fetching k × 5 and filtering after.

---

### Q22. Your top-5 results are five copies of the same paragraph. Fix it in code.

`[HARD]`

**Answer:** Maximal Marginal Relevance. Select iteratively: `score(d) = λ · sim(q, d) − (1 − λ) · max_{s ∈ selected} sim(d, s)`. λ = 1 is pure relevance, λ = 0 is pure diversity; ship λ ≈ 0.5–0.7.

**Constraints to ask:** candidate pool size (run MMR on the top ~50, not the whole corpus)? do we already have the doc vectors, or must we re-embed?

**Brute force → optimal:** brute force is "fetch k, dedupe by exact text" — misses paraphrases. MMR is O(k·C·d) where C is the candidate pool; keeping C at 50 makes it free relative to the retrieval call itself.

**Code:**

```python
import numpy as np

def mmr(query: np.ndarray, docs: np.ndarray, k: int = 5, lam: float = 0.7) -> list[int]:
    """Returns selected doc indices, most relevant first, penalised for redundancy."""
    d = docs / (np.linalg.norm(docs, axis=1, keepdims=True) + 1e-12)
    qn = query / (np.linalg.norm(query) + 1e-12)
    rel = d @ qn
    selected: list[int] = []
    candidates = list(range(len(docs)))
    while candidates and len(selected) < k:
        if not selected:
            best = max(candidates, key=lambda i: rel[i])
        else:
            sim_sel = d[candidates] @ d[selected].T      # (C, S) candidate-vs-selected
            div = sim_sel.max(axis=1)                    # worst-case redundancy
            scores = lam * rel[candidates] - (1 - lam) * div
            best = candidates[int(np.argmax(scores))]
        selected.append(best)
        candidates.remove(best)
    return selected

q3 = np.array([1.0, 0.5, 0.0])
docs = np.array([[1.0, 0.0, 0.0],        # 0
                 [0.999, 0.045, 0.0],    # 1  near-duplicate of 0
                 [0.0, 1.0, 0.0]])       # 2  different, still relevant
plain = [i for i, _ in top_k_vectors(q3, docs, k=2)]
assert plain == [1, 0]                    # pure similarity returns two near-identical docs
assert mmr(q3, docs, k=2, lam=0.5) == [1, 2]     # MMR swaps in the diverse one
```

**Complexity:** O(k · C · d) time, O(C · d) memory. Recomputed for C = 50, k = 5, d = 1536: the relevance pass is 50 × 1536 ≈ 77 K multiply-adds, and the four redundancy passes are 1536 × 50 × (1+2+3+4) ≈ 768 K, so **under a million multiply-adds** — microseconds, and utterly dominated by the retrieval call itself.

**Gotcha:** `candidates.remove(best)` is O(C) — fine at C = 50, replace with a boolean mask at C = 100 K. And MMR needs the **document vectors**, so keep them from the retrieval call rather than re-embedding.

**Follow-up they will ask:** "Alternatives?" → a cross-encoder reranker (`bge-reranker`, Cohere Rerank) improves *relevance*, MMR improves *diversity* — they compose: retrieve 50 → rerank → MMR → top 5. "Where is it built in?" → LangChain vector stores expose `search_type="mmr"` with `fetch_k` and `lambda_mult`.

---

### Q23. Your streaming LLM is emitting JSON and the user closed the tab mid-stream. Parse the partial JSON.

`[HARD]`

**Answer:** Best-effort repair: scan once tracking `in_string`/escape state and a stack of open brackets, drop any dangling escape, close an unterminated string, strip a trailing `,` or `:` (plus the orphan key the `:` belonged to), then append the closers in reverse. If it still fails, truncate back to the previous structural delimiter and retry. This is exactly what "partial JSON" helpers in the LLM SDKs do so you can render fields as they arrive.

**Constraints to ask:** is a partially-filled object acceptable, or must it be all-or-nothing? do we ever see prose around the JSON (markdown fences)? do we need per-field callbacks?

**Brute force → optimal:** brute force is `try: json.loads(buf) except: pass` on every token — O(n) per token, O(n²) overall, and it produces nothing until the last byte. The repair approach yields a usable object at every step in O(n) per attempt.

**Code:**

```python
import json
from typing import Any

def _string_start(s: str) -> int:
    """Index of the opening quote of the JSON string that ends at s[-1]."""
    i = len(s) - 2
    while i >= 0:
        if s[i] == '"':
            b, n = i - 1, 0
            while b >= 0 and s[b] == "\\":
                n += 1; b -= 1
            if n % 2 == 0:              # not escaped -> this is the real opener
                return i
        i -= 1
    return -1

def _closed(s: str) -> str:
    stack: list[str] = []
    in_str = esc = False
    for ch in s:
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
        elif ch == '"': in_str = True
        elif ch in "{[": stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack: stack.pop()
    if esc:
        s = s[:-1]                      # dangling backslash
    if in_str:
        s += '"'                        # close the open string
    while True:
        s = s.rstrip()
        if s.endswith(","):
            s = s[:-1]; continue
        if s.endswith(":"):             # key with no value yet -> drop the key too
            s = s[:-1].rstrip()
            if s.endswith('"'):
                j = _string_start(s)
                s = s[:j] if j >= 0 else s
            continue
        break
    return s + "".join(reversed(stack))

def _cut_back(s: str) -> str:
    k = max(s.rfind(c, 0, len(s) - 1) for c in ",:[{")   # strictly shrinks
    return "" if k < 0 else s[:k + 1]

def parse_partial_json(text: str) -> Any | None:
    """Best-effort parse of a truncated JSON payload from a streaming LLM."""
    s = text.strip()
    while s:
        try:
            return json.loads(_closed(s))
        except json.JSONDecodeError:
            s = _cut_back(s)
    return None

full = '{"name":"Ravi","tools":[{"id":1,"args":{"q":"vector db, hnsw"}}],"ok":true,"score":1.25}'
assert parse_partial_json(full) == json.loads(full)
for i in range(1, len(full) + 1):                 # EVERY prefix must parse or return None
    assert parse_partial_json(full[:i]) is None or isinstance(parse_partial_json(full[:i]), dict)
assert parse_partial_json('{"a": 1, "b": tru') == {"a": 1}      # partial literal dropped
assert parse_partial_json('{"a": 1, "b": "hel') == {"a": 1, "b": "hel"}
assert parse_partial_json('{"a": [1, 2,') == {"a": [1, 2]}
assert parse_partial_json("not json at all") is None
```

**Complexity:** O(n) per attempt, O(depth) stack; worst case O(n·structural-delims) ≈ O(n²) on pathological garbage, bounded in practice because each cut strictly shrinks the buffer.

**Gotcha:** you **must** track string state — a `{`, `}` or `,` inside a string value must not touch the bracket stack. The trailing-`:` case is the one everyone forgets: `{"a":1,"b":` must drop `"b"` as well, not just the colon.

**Follow-up they will ask:** "Would you write this in production?" → no: use structured outputs (`response_format={"type": "json_schema", "json_schema": {...,"strict": True}}` on OpenAI/Azure OpenAI, `Instructor`, or pydantic validation with one repair-retry), and for streaming UIs use the SDK's partial-parse helper or the `json-repair`/`partial-json-parser` packages. Write it yourself only when you must render fields *while* they stream. "How do you validate afterwards?" → `Model.model_validate(obj)` in pydantic v2, and on `ValidationError` send the error text back to the model as a repair turn (one retry, then fail closed).

---

### Q24. Parse a raw SSE stream from a chat completions endpoint and reassemble the message + tool calls.

`[MEDIUM]`

**Answer:** SSE events are `\n\n`-separated blocks of `field: value` lines. Take the `data:` lines, ignore `[DONE]`, `json.loads` each, then accumulate: concatenate `delta.content` for text, and for tool calls **accumulate by `index`** because the name arrives once and the `arguments` string arrives in fragments that are only valid JSON once complete.

**Constraints to ask:** is `data` ever multi-line (yes — concatenate with `\n`)? do we need usage stats (`stream_options={"include_usage": True}`)? reconnection with `Last-Event-ID`?

**Code:**

```python
import json
from collections.abc import Iterator

def parse_sse(raw: str) -> Iterator[dict]:
    for block in raw.split("\n\n"):
        data = "\n".join(l[5:].lstrip() for l in block.splitlines() if l.startswith("data:"))
        if not data or data == "[DONE]":
            continue
        yield json.loads(data)

def accumulate_stream(events) -> dict:
    text: list[str] = []
    calls: dict[int, dict] = {}
    finish = None
    for ev in events:
        ch = (ev.get("choices") or [{}])[0]
        delta = ch.get("delta") or {}
        if delta.get("content"):
            text.append(delta["content"])
        for tc in delta.get("tool_calls") or []:
            slot = calls.setdefault(tc["index"], {"id": "", "name": "", "arguments": ""})
            slot["id"] += tc.get("id") or ""
            fn = tc.get("function") or {}
            slot["name"] += fn.get("name") or ""
            slot["arguments"] += fn.get("arguments") or ""   # fragments -> concatenate
        finish = ch.get("finish_reason") or finish
    return {"content": "".join(text),
            "tool_calls": [calls[i] for i in sorted(calls)],
            "finish_reason": finish}

raw = (
    'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
    'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
    'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
    '"function":{"name":"search","arguments":"{\\"q\\":"}}]}}]}\n\n'
    'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
    '"function":{"arguments":"\\"hnsw\\"}"}}]},"finish_reason":"tool_calls"}]}\n\n'
    "data: [DONE]\n\n"
)
acc = accumulate_stream(parse_sse(raw))
assert acc["content"] == "Hello"
assert json.loads(acc["tool_calls"][0]["arguments"]) == {"q": "hnsw"}
assert acc["finish_reason"] == "tool_calls"
```

**Real client (openai>=1.x) — do not write the legacy `openai.ChatCompletion.create`, it was removed in 1.0:**

```python
from openai import OpenAI

client = OpenAI()                     # reads OPENAI_API_KEY
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "explain HNSW in one line"}],
    stream=True,
)
for chunk in stream:
    piece = chunk.choices[0].delta.content
    if piece:
        print(piece, end="", flush=True)
```

**Complexity:** O(total bytes), O(output size) memory.

**Gotcha:** (1) Never `split(":")` — the value contains colons; slice off the 5-char `data:` prefix. (2) `delta.content` is `None` on the tool-call and role chunks — `if piece:` is mandatory or you `TypeError` on concatenation. (3) The *last* chunk carries `finish_reason`; `"length"` means you were truncated by `max_tokens`, and users report that as "the bot stops mid-sentence". (4) Behind nginx you must set `X-Accel-Buffering: no` and disable proxy buffering or the whole stream arrives at once.

**Follow-up they will ask:** "How do you serve this from FastAPI?" → `StreamingResponse(gen(), media_type="text/event-stream")` with an async generator yielding `f"data: {json.dumps(x)}\n\n"`, plus a heartbeat comment line every ~15 s to keep idle proxies from killing the connection. "Why SSE and not WebSockets?" → one-directional, plain HTTP, auto-reconnect, survives corporate proxies; WebSockets only when the client also streams.

---

### Q25. Mask PII (email, Indian phone, PAN, Aadhaar, card, IP) before sending text to an LLM.

`[MEDIUM]`

**Answer:** An ordered dict of compiled regexes, longest/most-specific first, applied with `pattern.sub(callback)` so you can count hits and validate (Luhn for cards). Order matters: Aadhaar's 12-digit pattern will eat part of a 16-digit card number if it runs first.

**Constraints to ask:** mask or tokenise-and-restore (do we need to put the real values back into the answer)? which entity types are in scope for compliance (DPDP Act / GDPR)? do we need an audit log of what was masked?

**Brute force → optimal:** naive `str.replace` per known value only works if you already know the values. Regex catches the shapes; validators (Luhn, Verhoeff) cut false positives; an NER model (spaCy, Presidio) catches names and addresses that regex fundamentally cannot.

**Code:**

```python
import re

# ORDER MATTERS: most specific first, else CARD digits get eaten by AADHAAR.
PII_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL":    re.compile(r"\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PAN":      re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),             # ABCDE1234F
    # digit-separator-digit, NOT (digit separator)+ — the latter eats the trailing space
    "CARD":     re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)"),
    "AADHAAR":  re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"),  # never starts 0/1
    "PHONE_IN": re.compile(r"(?<!\d)(?:\+91[\-\s]?|0)?[6-9]\d{9}(?!\d)"),
    "IP":       re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

def luhn_ok(num: str) -> bool:
    digits = [int(c) for c in num if c.isdigit()]
    if len(digits) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def mask_pii(text: str, keep_last: int = 0) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    def repl_factory(label: str):
        def repl(m: re.Match) -> str:
            raw = m.group(0)
            if label == "CARD" and not luhn_ok(raw):
                return raw                       # validator kills false positives
            counts[label] = counts.get(label, 0) + 1
            tail = raw[-keep_last:] if keep_last else ""
            return f"[{label}{'_' + tail if tail else ''}]"
        return repl
    for label, pat in PII_PATTERNS.items():
        text = pat.sub(repl_factory(label), text)
    return text, counts

s = ("Mail ravi@corp.co.in or call +91 9876543210. PAN ABCDE1234F, "
     "Aadhaar 4321 8765 1234, card 4111 1111 1111 1111, ip 10.2.3.4")
masked, cnt = mask_pii(s)
assert "[EMAIL]" in masked and "[PAN]" in masked and "[AADHAAR]" in masked
assert "[CARD]" in masked and "ravi@corp.co.in" not in masked
assert luhn_ok("4111 1111 1111 1111") and not luhn_ok("4111 1111 1111 1112")
# the greedy-repetition form of the CARD regex would consume the space after the number:
assert mask_pii("card 4111111111111111 and phone")[0] == "card [CARD] and phone"
```

**Complexity:** O(P·n) for P patterns over n characters. Compile once at import (module-level), never inside the function — `re.compile` in a hot loop is a real profiler finding, though `re` does cache the last 512 patterns.

**Gotcha:** (1) Regex cannot find **names, addresses, or free-text health data** — say this explicitly or you sound naive about compliance. (2) Masking is destructive: if the user asks "email that to ravi@corp.co.in", the model can no longer answer. The production pattern is **tokenise → call LLM → detokenise**, keeping a request-scoped map `{"[EMAIL_1]": "ravi@corp.co.in"}` in memory only. (3) Aadhaar should also pass the **Verhoeff** checksum; PAN's 4th character encodes holder type. (4) Log the *counts*, never the matched values.

**Follow-up they will ask:** "Production tool?" → Microsoft **Presidio** (recognisers + NER + anonymiser), or Azure AI Language PII detection; both give you spans and confidence, and Presidio supports custom Indian recognisers. "Where do you run it?" → in the gateway, before the prompt is built, and again on the LLM output before it is logged or returned.

---

### Q26. Levenshtein edit distance — DP, then O(min(m,n)) space, then recover the edit operations.

`[MEDIUM]`

**Answer:** `dp[i][j] = min(delete, insert, substitute)` where substitute costs `a[i-1] != b[j-1]`. Only the previous row is needed for the distance, so keep two rows — O(min(m,n)) space. To recover the ops you need the full matrix and a backtrace.

**Constraints to ask:** are transpositions a single edit (Damerau)? case-sensitive? weighted costs per operation? do we need the ops or just the number?

**Brute force → optimal:** naive recursion is O(3^(m+n)); memoised recursion is O(mn) but blows the stack at ~1000 chars; bottom-up DP is O(mn) time / O(mn) space; rolling rows cut it to O(min(m,n)) space.

**Code:**

```python
def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a                       # keep the shorter string as the row -> less memory
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1,          # delete from a
                         cur[j - 1] + 1,       # insert into a
                         prev[j - 1] + (ca != cb))   # substitute / match
        prev = cur
    return prev[-1]

def edit_ops(a: str, b: str) -> list[str]:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1,
                           dp[i-1][j-1] + (a[i-1] != b[j-1]))
    ops, i, j = [], m, n
    while i or j:
        if i and j and dp[i][j] == dp[i-1][j-1] + (a[i-1] != b[j-1]):
            if a[i-1] != b[j-1]:
                ops.append(f"sub {a[i-1]}->{b[j-1]} @{i-1}")
            i, j = i - 1, j - 1
        elif i and dp[i][j] == dp[i-1][j] + 1:
            ops.append(f"del {a[i-1]} @{i-1}"); i -= 1
        else:
            ops.append(f"ins {b[j-1]} @{i}"); j -= 1
    return ops[::-1]

assert levenshtein("kitten", "sitting") == 3
assert levenshtein("", "abc") == 3 and levenshtein("abc", "abc") == 0
assert len(edit_ops("kitten", "sitting")) == 3
```

**Complexity:** distance O(m·n) time / O(min(m,n)) space. Ops O(m·n) time / O(m·n) space.

**Gotcha:** initialising row 0 and column 0 to `range(...)` is the base case (turning an empty string into a k-length string costs k) — forgetting it is the #1 bug. `enumerate(a, 1)` keeps the 1-based DP indices while `a[i-1]` reads the character.

**Follow-up they will ask:** "Normalised similarity?" → `1 - dist / max(len(a), len(b))`, and use `rapidfuzz` (C++ core, orders of magnitude faster than a pure-Python DP; `difflib.SequenceMatcher` is stdlib but implements Ratcliff/Obershelp gestalt matching, **not** Levenshtein, so its ratio is not `1 - dist/max_len`). "Where in GenAI?" → fuzzy-matching an LLM-emitted entity against a canonical list (tool names, SKU codes, column names) before dispatching, and as a cheap eval metric against gold answers alongside embedding similarity.

---

### Q27. Detect near-duplicate documents before you embed them (they cost money and pollute retrieval).

`[HARD]`

**Answer:** k-shingles + Jaccard similarity for the exact answer, MinHash signatures when N is large. A MinHash signature of P permutations estimates Jaccard with standard error `sqrt(J(1-J)/P)` — at P = 128 that is at most ~0.044, and the conservative rule of thumb people quote is `1/sqrt(P)` ≈ 0.09. It turns an O(N²·|set|) all-pairs comparison into O(N·P) plus LSH banding for candidate generation.

**Constraints to ask:** N? threshold for "duplicate" (0.8 Jaccard is typical)? is exact dedupe by hash enough (identical files) or do we need near-dupe?

**Brute force → optimal:** all-pairs Jaccard is O(N²) set intersections — 10 K docs = 50 M comparisons. MinHash + LSH banding makes it near-linear by only comparing docs that collide in at least one band.

**Code:**

```python
import re, zlib

def shingles(text: str, k: int = 5) -> set[str]:
    """k-word shingles. k=5 for prose, k=3 for short text, char-shingles for code."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

def minhash(sh: set[str], num_perm: int = 128) -> list[int]:
    """One hash family per permutation; the signature is the per-family minimum.
    P(sig_a[i] == sig_b[i]) == Jaccard(a, b)."""
    if not sh:
        return [0] * num_perm
    return [min(zlib.crc32(s.encode(), seed) for s in sh) for seed in range(num_perm)]

def minhash_sim(sa: list[int], sb: list[int]) -> float:
    return sum(x == y for x, y in zip(sa, sb)) / len(sa)

d1 = "the quick brown fox jumps over the lazy dog near the river bank today"
d2 = "the quick brown fox jumps over the lazy dog near the river bank yesterday"
d3 = "vector databases index embeddings with hnsw graphs for fast search"
s1, s2, s3 = shingles(d1, 3), shingles(d2, 3), shingles(d3, 3)
assert jaccard(s1, s2) > 0.6 and jaccard(s1, s3) == 0.0
assert abs(minhash_sim(minhash(s1), minhash(s2)) - jaccard(s1, s2)) < 0.15
```

**Complexity:** shingling O(w) per doc; exact Jaccard O(|s1| + |s2|) per pair, O(N²) pairs. MinHash: O(|s| · P) to build (P = 128), O(P) per comparison, and LSH banding (b bands × r rows, `P = b·r`) reduces candidate pairs to near-linear with a tunable threshold ≈ `(1/b)^(1/r)`.

**Gotcha:** (1) Python's built-in `hash()` for `str` is **randomised per process** (PYTHONHASHSEED) — signatures would not match across runs or workers. Use `zlib.crc32(s, seed)`, `hashlib`, or `mmh3`. (2) Be honest about the toy above: CRC32 is *linear*, so seeding it is **not** a proper independent hash family and the 128 "permutations" are correlated — good enough to demo the idea, but in production use `mmh3.hash(s, seed)` or `hashlib.blake2b(s, key=...)`, or just `datasketch`. (3) MinHash approximates *set* overlap, so it catches copy-paste and boilerplate, **not** paraphrase — for paraphrase you need embedding cosine (Q20) at a high threshold (~0.95 on many models, but calibrate it per model exactly as in Q20's gotcha).

**Follow-up they will ask:** "Production?" → `datasketch` (`MinHashLSH`), or SimHash for very short text; in a RAG ingest pipeline you dedupe at three levels — exact (sha256 of normalised text), near-dup (MinHash/LSH), and semantic (embedding cosine after embedding, to collapse boilerplate headers/footers). "Why do you care?" → duplicate chunks eat the context budget, skew retrieval scores toward the most-repeated boilerplate, and inflate the embedding bill.

---

## 4. Concurrency

The JD says "external API integration" and "multi-agent workflows" — which is *entirely* an I/O-bound concurrency problem. Expect at least one asyncio question.

### Q28. Call an API for 10 000 items with at most 8 requests in flight. Results in input order, one failure must not kill the batch.

`[MEDIUM]`

**Answer:** `asyncio.Semaphore(8)` acquired inside the per-item coroutine, then `asyncio.gather(*coros, return_exceptions=True)` — `gather` preserves **input order** regardless of completion order, and `return_exceptions=True` turns a failure into a value in the results list instead of cancelling the batch. Add `asyncio.wait_for` for a per-item timeout.

**Constraints to ask:** 10 000 items — do we materialise 10 000 coroutines (memory!) or stream them? per-item timeout or total deadline? retries per item? do we need results as they arrive?

**Brute force → optimal:** sequential `for` loop = 10 000 × 200 ms = 33 minutes. Unbounded `gather` over 10 000 coroutines = instant socket exhaustion / 429 storm / OOM. Semaphore-bounded gather = 10 000 / 8 × 200 ms ≈ 4 minutes with a stable connection pool.

**Code:**

```python
import asyncio, time
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

async def bounded_gather(fn: Callable[[Any], Awaitable[Any]], items: Sequence[Any],
                         limit: int = 8, timeout: float | None = None) -> list[Any]:
    """At most `limit` in flight. Results keep INPUT order. Failures come back as objects."""
    sem = asyncio.Semaphore(limit)
    async def one(item):
        async with sem:                       # acquire INSIDE, so only the call is limited
            coro = fn(item)
            return await (asyncio.wait_for(coro, timeout) if timeout else coro)
    return await asyncio.gather(*(one(i) for i in items), return_exceptions=True)

async def bounded_stream(fn, items, limit=8):
    """Same bound, but yields (item, result) as soon as each one finishes."""
    sem = asyncio.Semaphore(limit)
    async def one(item):
        async with sem:
            return item, await fn(item)
    for fut in asyncio.as_completed([one(i) for i in items]):
        yield await fut

async def demo() -> None:
    async def work(x: int) -> int:
        await asyncio.sleep(0.01)
        if x == 3:
            raise ValueError("bad 3")
        return x * x

    t0 = time.perf_counter()
    res = await bounded_gather(work, list(range(10)), limit=5)
    assert res[2] == 4 and isinstance(res[3], ValueError)      # order preserved, error boxed
    assert 0.02 <= time.perf_counter() - t0 < 0.15             # 10 items / 5 = 2 waves

    seen = [pair async for pair in bounded_stream(work, [1, 2, 4], limit=2)]
    assert sorted(seen) == [(1, 1), (2, 4), (4, 16)]

asyncio.run(demo())
```

**Complexity:** wall clock ≈ `ceil(N / limit) × per_call_latency`; memory O(N) for the task objects — for millions of items, stream with a queue (Q29) instead of creating N tasks.

**Gotcha:** (1) Acquiring the semaphore *outside* the coroutine (e.g. around `gather`) does nothing. (2) `return_exceptions=True` means you must **inspect** the results for exception instances — silently treating them as data is a classic bug. (3) With `return_exceptions=False` (the default) the first exception propagates but the other tasks keep running until you await them — orphan warnings in your logs. (4) On Python 3.11+ prefer `async with asyncio.TaskGroup() as tg: tg.create_task(...)` for **fail-fast with automatic cancellation** — but note it raises an `ExceptionGroup`, so `except*` or `eg.exceptions`. (5) The concurrency limit must also respect the HTTP client's pool: `httpx.AsyncClient(limits=httpx.Limits(max_connections=100))` — a semaphore of 500 over a pool of 10 just queues inside httpx.

**Follow-up they will ask:** "Why not threads?" → these calls are I/O-bound; asyncio holds ~10 K concurrent sockets in one thread at roughly a KB of task overhead each, whereas each OS thread reserves the default stack (8 MB of *virtual* address space on typical Linux — resident memory is far lower, but the scheduling and context-switch cost is real). Threads work fine to the low hundreds; asyncio is what gets you to five figures. "CPU-bound work?" → `ProcessPoolExecutor` / `multiprocessing`, because the GIL serialises CPU-bound Python bytecode. "Rate limits per provider?" → Q30.

---

### Q29. Build a producer/consumer pipeline with `asyncio.Queue` and shut it down cleanly.

`[MEDIUM]`

**Answer:** Bounded `asyncio.Queue(maxsize=...)` for backpressure, N consumer tasks in a `while True: item = await q.get()` loop with `q.task_done()` in a `finally`, then `await q.join()` to wait for completion and `task.cancel()` to stop the idle workers. Wrap the work in `try/except` inside the consumer so one bad item never kills a worker.

**Constraints to ask:** unbounded or bounded queue (bounded = backpressure)? must ordering be preserved (queues do not preserve it)? at-least-once or at-most-once semantics on crash?

**Brute force → optimal:** a plain list as a queue plus polling burns CPU; an unbounded queue lets a fast producer read the whole 50 GB file into RAM before the first consumer finishes — `maxsize` is the fix and is the point of the question.

**Code:**

```python
import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

async def pipeline(sources: Iterable[Any], work: Callable[[Any], Awaitable[Any]],
                   n_workers: int = 4, maxsize: int = 32) -> list[Any]:
    q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)     # maxsize == backpressure
    out: list[Any] = []

    async def consumer():
        while True:
            item = await q.get()
            try:
                out.append(await work(item))
            except Exception as exc:                       # never let a worker die
                out.append(exc)
            finally:
                q.task_done()                              # MUST pair with every get()

    workers = [asyncio.create_task(consumer()) for _ in range(n_workers)]
    for s in sources:
        await q.put(s)                                     # blocks when full -> backpressure
    await q.join()                                         # all items task_done()
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True) # swallow CancelledError
    return out

async def demo() -> None:
    async def work(x: int) -> int:
        await asyncio.sleep(0.01)
        if x == 3:
            raise ValueError("bad 3")
        return x * x
    out = await pipeline(range(10), work, n_workers=4, maxsize=3)
    assert len(out) == 10
    assert sum(v for v in out if isinstance(v, int)) == sum(i * i for i in range(10) if i != 3)

asyncio.run(demo())
```

**Complexity:** O(N) work, O(maxsize + n_workers) memory — independent of the source size, which is the selling point.

**Gotcha:** (1) Forgetting `task_done()` makes `q.join()` hang forever — put it in `finally`. (2) `create_task` results must be kept in a variable; a task with no strong reference can be garbage collected mid-flight (documented CPython behaviour). (3) Cancelling raises `CancelledError` **inside** the worker — do not swallow it in a bare `except Exception` if you have cleanup that must run (in 3.8+ `CancelledError` inherits from `BaseException`, so `except Exception` is safe). (4) The sentinel alternative (`await q.put(None)` × n_workers) is fine too and avoids cancellation entirely — mention both.

**Follow-up they will ask:** "Multi-stage pipeline?" → chain queues: parse → chunk → embed → upsert, each stage with its own worker count sized to its bottleneck (embedding is network-bound → 16 workers; parsing is CPU-bound → run it in `ProcessPoolExecutor` via `loop.run_in_executor`). "Crash safety?" → an in-memory queue loses items on crash; for at-least-once use a real broker (SQS/Rabbit/Kafka/Azure Service Bus) with visibility timeouts and idempotent consumers.

---

### Q30. Fan out to several third-party APIs, but each host has its own rate limit.

`[HARD]`

**Answer:** One **async token bucket per host** for the request *rate* plus one **semaphore per host** for concurrent connections. The bucket paces you; the semaphore caps in-flight sockets. Look them up in a dict keyed by host and create lazily.

**Constraints to ask:** rate limits per host (RPM and TPM)? are they per-key or per-org? do responses carry `Retry-After` / `x-ratelimit-remaining` headers we should honour dynamically?

**Brute force → optimal:** a single global semaphore either starves the fast host or hammers the slow one. Per-host state is the fix.

**Code:**

```python
import asyncio, time
from collections.abc import Awaitable, Callable
from typing import Any

class AsyncTokenBucket:
    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        self.tokens = float(self.capacity)
        self.ts = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, cost: float = 1.0) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
                self.ts = now
                if self.tokens >= cost:
                    self.tokens -= cost
                    return
                wait = (cost - self.tokens) / self.rate
            await asyncio.sleep(wait)              # sleep OUTSIDE the lock

class HostLimiter:
    def __init__(self, rate_per_host: float, burst: float, max_conns: int = 5) -> None:
        self.rate, self.burst, self.max_conns = rate_per_host, burst, max_conns
        self._buckets: dict[str, AsyncTokenBucket] = {}
        self._sems: dict[str, asyncio.Semaphore] = {}

    def _for(self, host: str):
        if host not in self._buckets:
            self._buckets[host] = AsyncTokenBucket(self.rate, self.burst)
            self._sems[host] = asyncio.Semaphore(self.max_conns)
        return self._buckets[host], self._sems[host]

    async def run(self, host: str, coro_fn: Callable[[], Awaitable[Any]]) -> Any:
        bucket, sem = self._for(host)
        await bucket.acquire()                     # pace: requests per second
        async with sem:                            # cap: concurrent connections
            return await coro_fn()

async def demo() -> None:
    lim = HostLimiter(rate_per_host=50, burst=1, max_conns=2)   # 50 rps, burst 1
    async def ping():
        return "pong"
    t0 = time.perf_counter()
    got = await asyncio.gather(*(lim.run("api.openai.com", ping) for _ in range(3)))
    assert got == ["pong"] * 3
    assert time.perf_counter() - t0 >= 0.03        # 2 extra calls x 20 ms spacing

asyncio.run(demo())
```

**Complexity:** O(1) per request; memory O(hosts).

**Gotcha:** (1) `asyncio.Lock`/`Semaphore` are **not** thread-safe. Since 3.10 they no longer take a `loop=` argument and bind lazily to the loop they are first awaited on — so constructing one at import time is fine, but using it from a second loop or a second thread is not (that is `threading.Lock`'s job). (2) Creating the limiter at import time under `uvicorn --workers 4` gives each worker its own limiter, so your effective rate is 4× the configured one — divide by the worker count or move the limiter into Redis. (3) Azure OpenAI enforces **TPM** as well as RPM, so cost should be `prompt_tokens + max_tokens`, not 1.

**Follow-up they will ask:** "Do you honour the response headers?" → yes: on 429 sleep `Retry-After` (Azure OpenAI returns it in seconds) rather than your own backoff; track `x-ratelimit-remaining-requests`/`-tokens` to slow down before you get throttled. "Multi-region?" → route across two Azure OpenAI deployments with a weighted picker and fail over on 429/5xx; that is the standard PTU + pay-go spillover pattern.

---

### Q31. Make a counter thread-safe. Is `counter += 1` atomic in CPython?

`[EASY]`

**Answer:** **No.** `x += 1` compiles to LOAD / ADD / STORE and the interpreter can switch threads between them (every 5 ms by default, `sys.setswitchinterval`). Use a `threading.Lock`. A single C-level call like `itertools.count().__next__` *is* effectively atomic under the GIL, which is the standard lock-free ID generator trick.

**Code:**

```python
import itertools, threading

class Counter:
    def __init__(self) -> None:
        self._n = 0
        self._lock = threading.Lock()
    def incr(self, by: int = 1) -> int:
        with self._lock:
            self._n += by
            return self._n
    @property
    def value(self) -> int:
        with self._lock:            # lock the read too: 64-bit reads are fine, but
            return self._n          # compound "read-then-decide" logic is not

class AtomicIdGen:
    """itertools.count().__next__ is one C call -> atomic under CPython's GIL."""
    def __init__(self, start: int = 1) -> None:
        self._next = itertools.count(start).__next__
    def __call__(self) -> int:
        return self._next()

c = Counter()
def work():
    for _ in range(5000):
        c.incr()
ts = [threading.Thread(target=work) for _ in range(8)]
[t.start() for t in ts]; [t.join() for t in ts]
assert c.value == 40000            # without the lock this loses thousands of increments
```

**Complexity:** O(1) — an uncontended `threading.Lock` acquire/release is on the order of tens of nanoseconds, i.e. cheap enough that "the lock is too slow" is almost never the real objection.

**Gotcha:** (1) People "prove" `+=` is atomic with a 100-iteration test — the race needs volume; use 8 threads × 5000. (2) `Lock` is **not** reentrant — a method holding the lock that calls another locking method self-deadlocks; use `RLock` there. (3) `queue.Queue` is already thread-safe (it has its own lock) so you rarely need your own. (4) Python 3.13+ free-threaded builds (PEP 703) remove the GIL — the "GIL makes it safe" argument dies there, so lock properly regardless. (5) Across **processes** use `multiprocessing.Value("i", 0, lock=True)` or Redis `INCR`.

**Follow-up they will ask:** "What does the GIL actually protect?" → CPython's internal state (refcounts, dict/list internals) — so individual bytecodes are safe, but *sequences* of them are not. "Where does this bite you in a GenAI app?" → per-request token/cost accumulators, in-flight-request gauges, and cache statistics under Gunicorn threads. Use `prometheus_client` counters (already atomic) rather than hand-rolling.

---

### Q32. Your vector-DB SDK is synchronous and blocks for 300 ms. You are inside FastAPI's async endpoint. What do you do?

`[MEDIUM]`

**Answer:** `await asyncio.to_thread(blocking_call, args)` (3.9+) — it runs on the default thread pool executor and yields the loop. **Never** call a blocking function directly in a coroutine: it freezes the entire event loop, so every other request stalls for 300 ms. The FastAPI-native alternative is to declare the endpoint `def` (not `async def`) — Starlette then runs it in a threadpool automatically.

**Code:**

```python
import asyncio, time
from concurrent.futures import ThreadPoolExecutor

def blocking_sdk_call(x: int) -> int:
    time.sleep(0.02)                              # a sync SDK / requests / psycopg2 call
    return x * 2

async def call_blocking(x: int, timeout: float = 1.0) -> int:
    return await asyncio.wait_for(asyncio.to_thread(blocking_sdk_call, x), timeout)

# Custom pool when you need to size it or isolate a dependency:
POOL = ThreadPoolExecutor(max_workers=16, thread_name_prefix="vecdb")

async def call_with_pool(x: int) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(POOL, blocking_sdk_call, x)

async def demo() -> None:
    assert await call_blocking(21) == 42
    t0 = time.perf_counter()
    out = await asyncio.gather(*(call_with_pool(i) for i in range(8)))   # 8 in parallel
    assert out == [i * 2 for i in range(8)] and time.perf_counter() - t0 < 0.1
    try:
        await asyncio.wait_for(asyncio.to_thread(time.sleep, 1.0), 0.02)
        raise AssertionError("should have timed out")
    except (asyncio.TimeoutError, TimeoutError):        # same class on 3.11+
        pass

asyncio.run(demo())
```

**Complexity:** parallelism is capped by the executor size — `asyncio.to_thread` uses the default executor (`min(32, cpu_count + 4)` workers). If you need 100 concurrent blocking calls, build your own pool or use an async SDK.

**Gotcha:** (1) `asyncio.wait_for` **cannot actually kill** a thread — the timeout returns control to you but `blocking_sdk_call` keeps running to completion in the background, so a leaked slow call still occupies a worker. Only true async I/O is cancellable. (2) `time.sleep()` in a coroutine is the canonical event-loop-blocking bug; `await asyncio.sleep()` is the fix. (3) CPU-bound work in a thread does **not** parallelise (GIL) — use `ProcessPoolExecutor`. (4) On 3.11+ `asyncio.timeout()` is the nicer context-manager form: `async with asyncio.timeout(1.0): ...`.

**Follow-up they will ask:** "How do you find these blocking calls?" → run with `PYTHONASYNCIODEBUG=1` or `loop.set_debug(True)` and it logs any callback that holds the loop longer than `loop.slow_callback_duration` (default 0.1 s). For detection rather than luck: the `blockbuster` package patches known blocking stdlib calls to raise inside a running loop, and statically, Ruff's `ASYNC` rules (the `flake8-async` set) flag things like `time.sleep` and `requests` inside `async def`. "FastAPI rule of thumb?" → `async def` endpoint + all-async libraries (`httpx`, `asyncpg`, `redis.asyncio`, `AsyncOpenAI`), or plain `def` endpoint for sync libraries. The disaster case is `async def` + `requests`.

---

## 5. OOP design on paper

They will hand you a marker and say "design me X, I want the class structure and the method signatures". Draw the data structures first, then the API, then complexity per operation.

### Q33. Design an in-memory key-value store with per-key TTL.

`[HARD]`

**Answer:** `dict` for `key -> (expires_at, value)` plus a **min-heap** of `(expires_at, key)`. Expire **lazily** on read (O(1)) and **actively** in bounded batches on write (amortised O(log n)) so that keys nobody reads still get reclaimed. Guard against stale heap entries after an overwrite by comparing the stored expiry. This is a scaled-down Redis.

**Constraints to ask:** thread-safe? do we need eviction on memory pressure (LRU) as well as TTL? must `len()` be exact? persistence?

**Brute force → optimal:** (a) scan every key on every operation = O(n) per call; (b) a background thread sweeping everything every second = wasted CPU and a lock convoy on a big store; (c) lazy + bounded active expiry = O(1) reads, no thread. Redis does exactly (c) with random sampling.

**Code:**

```python
import heapq, threading, time
from typing import Any

class TTLStore:
    """dict + expiry heap. Lazy expiry on read, bounded active expiry on write."""
    _MISS = object()

    def __init__(self, default_ttl: float | None = None, max_purge: int = 32) -> None:
        self._data: dict[Any, tuple[float | None, Any]] = {}
        self._heap: list[tuple[float, Any]] = []
        self._lock = threading.RLock()
        self.default_ttl, self.max_purge = default_ttl, max_purge

    def set(self, key: Any, value: Any, ttl: float | None = -1.0) -> None:
        ttl = self.default_ttl if ttl == -1.0 else ttl        # None == never expires
        exp = None if ttl is None else time.monotonic() + ttl
        with self._lock:
            self._data[key] = (exp, value)
            if exp is not None:
                heapq.heappush(self._heap, (exp, key))
            self._purge()

    def get(self, key: Any, default: Any = None) -> Any:
        with self._lock:
            hit = self._data.get(key, self._MISS)
            if hit is self._MISS:
                return default
            exp, value = hit
            if exp is not None and exp <= time.monotonic():
                self._data.pop(key, None)                     # lazy expiry
                return default
            return value

    def delete(self, key: Any) -> bool:
        with self._lock:
            return self._data.pop(key, self._MISS) is not self._MISS

    def ttl(self, key: Any) -> float | None:
        with self._lock:
            hit = self._data.get(key)
            if not hit or hit[0] is None:
                return None
            return max(0.0, hit[0] - time.monotonic())

    def _purge(self) -> None:
        now = time.monotonic()
        for _ in range(self.max_purge):                       # bounded: never a long stall
            if not self._heap or self._heap[0][0] > now:
                return
            exp, key = heapq.heappop(self._heap)
            cur = self._data.get(key)
            if cur and cur[0] == exp:      # skip STALE heap entries left by an overwrite
                del self._data[key]

    def __len__(self) -> int:
        with self._lock:
            self._purge()
            return len(self._data)

kv = TTLStore()
kv.set("a", 1, ttl=0.05)
kv.set("b", 2, ttl=None)
assert kv.get("a") == 1 and 0 < kv.ttl("a") <= 0.05 and kv.ttl("b") is None
time.sleep(0.06)
assert kv.get("a") is None and kv.get("b") == 2
kv.set("c", 3, ttl=0.01); kv.set("c", 4, ttl=None)            # overwrite -> stale heap entry
time.sleep(0.02)
kv.set("d", 0, ttl=None)                                      # triggers _purge
assert kv.get("c") == 4                                       # must NOT be deleted
```

**Complexity:** `get`/`delete` O(1); `set` is O(log n) for the `heappush` plus a **bounded** purge of at most `max_purge` pops, so O(max_purge · log n) worst case per write with a small constant — the point of the bound is that no single write can stall. Memory O(n + heap), where the heap can temporarily exceed n because of stale entries (that is the trade for O(log n) writes).

**Gotcha:** the **stale heap entry** is the whole interview. `set("c", ..., ttl=short)` then `set("c", ..., ttl=None)` leaves the old `(exp, "c")` in the heap; without the `cur[0] == exp` check the purge deletes a live key. The alternatives are a `heapq` entry-versioning scheme or a lazy-delete tombstone — say you chose the expiry-comparison because it needs no extra state.

**Follow-up they will ask:** "Add LRU eviction on top" → keep an `OrderedDict` for recency alongside; evict on `len > max_items` (that is Redis `allkeys-lru`). "Distributed?" → Redis: `SET key value EX 60`, and `TTL key`; then TTL is server-side and shared across pods, which is what you actually ship. "Where in a GenAI service?" → semantic cache for LLM responses (60–300 s), session state for an agent, and short-lived nonce/idempotency keys.

---

### Q34. Design a tool/plugin registry for an agent: register Python functions, expose them as LLM tool schemas, dispatch a call safely.

`[MEDIUM]`

**Answer:** A decorator-based registry that (1) introspects the function signature to build a **pydantic v2** model, (2) emits `model_json_schema()` in the OpenAI tools format, and (3) validates arguments before calling and returns errors **as data** so the model can self-correct rather than the process crashing. This is the single most JD-relevant design question in the file.

**Constraints to ask:** sync or async tools? do tools need auth/user context? per-tool timeouts and rate limits? how many tools (selection accuracy degrades as the list grows — past a couple of dozen you want a router or a retriever over tool descriptions rather than one flat list)?

**Code:**

```python
import inspect, json
from dataclasses import dataclass
from typing import Any, Callable
from pydantic import BaseModel, ValidationError, create_model

@dataclass(slots=True)
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    model: type[BaseModel]

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, fn: Callable[..., Any] | None = None, *, name: str | None = None):
        """Usable as @registry.register or @registry.register(name="x")."""
        def deco(f: Callable[..., Any]) -> Callable[..., Any]:
            tname = name or f.__name__
            if tname in self._tools:
                raise ValueError(f"duplicate tool: {tname}")
            sig = inspect.signature(f)
            hints = inspect.get_annotations(f, eval_str=True)
            fields: dict[str, tuple[Any, Any]] = {}
            for pname, p in sig.parameters.items():
                if pname == "self":
                    continue
                ann = hints.get(pname, str)
                default = ... if p.default is inspect.Parameter.empty else p.default
                fields[pname] = (ann, default)
            model = create_model(f"{tname}_Args", **fields)      # pydantic v2
            self._tools[tname] = Tool(tname, (f.__doc__ or "").strip(), f, model)
            return f                                            # tool stays normally callable
        return deco(fn) if fn else deco

    def openai_tools(self, strict: bool = False) -> list[dict]:
        """chat.completions format. (The Responses API uses a flattened variant.)"""
        out = []
        for t in self._tools.values():
            schema = t.model.model_json_schema()
            schema.pop("title", None)
            fn: dict[str, Any] = {"name": t.name, "description": t.description,
                                  "parameters": schema}
            if strict:
                # Structured-outputs strict mode: additionalProperties MUST be false and
                # EVERY property must be listed in `required`. Optional params are expressed
                # as a nullable type, not by omission -- otherwise the API 400s.
                schema["additionalProperties"] = False
                schema["required"] = list(schema.get("properties", {}))
                fn["strict"] = True
            out.append({"type": "function", "function": fn})
        return out

    def dispatch(self, name: str, arguments: str | dict) -> Any:
        """NEVER raise: the agent loop feeds the return value back to the model."""
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"unknown tool '{name}'", "available": list(self._tools)}
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            validated = tool.model(**args)
        except (json.JSONDecodeError, ValidationError) as exc:
            return {"error": "invalid_arguments", "detail": str(exc)}
        try:
            return tool.fn(**validated.model_dump())
        except Exception as exc:
            return {"error": type(exc).__name__, "detail": str(exc)}

registry = ToolRegistry()

@registry.register
def search_docs(query: str, top_k: int = 5) -> list[str]:
    """Search the internal knowledge base."""      # docstring becomes the tool description
    return [f"{query}#{i}" for i in range(top_k)]

schemas = registry.openai_tools()
assert schemas[0]["function"]["name"] == "search_docs"
assert schemas[0]["function"]["parameters"]["properties"]["top_k"]["default"] == 5
assert registry.dispatch("search_docs", '{"query":"rag","top_k":2}') == ["rag#0", "rag#1"]
assert registry.dispatch("search_docs", '{"top_k":2}')["error"] == "invalid_arguments"
assert registry.dispatch("nope", "{}")["error"].startswith("unknown tool")
# strict mode forces every property into `required` -- a defaulted param is NOT optional there
strict_schema = registry.openai_tools(strict=True)[0]["function"]
assert strict_schema["strict"] is True
assert sorted(strict_schema["parameters"]["required"]) == ["query", "top_k"]
assert strict_schema["parameters"]["additionalProperties"] is False
```

**Wiring it into the agent loop (openai>=1.x):**

```python
from openai import OpenAI
client = OpenAI()

messages = [{"role": "user", "content": "search the KB for hnsw"}]
for _ in range(6):                                  # ALWAYS bound the loop
    r = client.chat.completions.create(model="gpt-4o-mini", messages=messages,
                                       tools=registry.openai_tools())
    msg = r.choices[0].message
    messages.append(msg.model_dump(exclude_none=True))
    if not msg.tool_calls:
        break
    for tc in msg.tool_calls:
        result = registry.dispatch(tc.function.name, tc.function.arguments)
        messages.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(result)})     # content must be a string
```

**Complexity:** registration O(params) once at import; `openai_tools()` O(tools) — cache it; dispatch O(1) + the tool's own cost.

**Gotcha:** (1) **Never let a tool raise into the agent loop** — return the error as JSON so the model can retry with corrected arguments; that single decision is the difference between a demo and a product. (2) The tool `description` and parameter descriptions are *prompt* — vague docstrings are the #1 cause of wrong tool selection. (3) `strict: True` requires `additionalProperties: false` **and** every property listed in `required` — which is why the code above makes strict *opt-in* rather than always-on. Emitting `strict: True` while a defaulted parameter is absent from `required` (the naive version of this class) is rejected with a 400 at the first call, so know the rule: under strict mode there are no optional parameters, only nullable ones. (4) Tool names must match `^[a-zA-Z0-9_-]{1,64}$`. (5) A model can emit **parallel** tool calls — loop over `msg.tool_calls` and append one `tool` message per call, each with its own `tool_call_id`, or the next request 400s.

**Follow-up they will ask:** "What about 50 tools?" → selection accuracy degrades as the list grows; group tools per sub-agent, or retrieve the top-8 relevant tool schemas by embedding the user query against tool descriptions. "How does MCP change this?" → MCP is the standard protocol for exposing tools/resources/prompts over stdio or HTTP so the same server works with any client; your registry becomes an MCP server and the schema generation is identical. "Async tools?" → make `dispatch` `async` and `await` the tool if `inspect.iscoroutinefunction(tool.fn)`, and run independent tool calls with `asyncio.gather`.

---

### Q35. Implement an LFU cache with O(1) get and put.

`[HARD]`

**Answer:** Three structures: `vals` (key→value), `freq` (key→use count), and `buckets` (count→`OrderedDict` of keys in that bucket, insertion-ordered). Track `min_freq`. On access, move the key from bucket f to bucket f+1; on eviction, `popitem(last=False)` from `buckets[min_freq]` — which breaks LFU ties by LRU, exactly like the LeetCode variant.

**Constraints to ask:** tie-break rule (LRU is standard)? does `put` on an existing key count as a use (yes)? capacity 0? aging (should old frequencies decay)?

**Brute force → optimal:** a dict + a linear scan for the minimum frequency = O(n) eviction. A heap of frequencies = O(log n) and needs lazy deletion. The bucket-of-OrderedDicts gives true O(1) because `min_freq` can only increase by 1 on a bump, or reset to 1 on an insert.

**Code:**

```python
from collections import OrderedDict, defaultdict
from typing import Any

class LFUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.vals: dict[Any, Any] = {}
        self.freq: dict[Any, int] = {}
        self.buckets: defaultdict[int, OrderedDict] = defaultdict(OrderedDict)
        self.min_freq = 0

    def _bump(self, key: Any) -> None:
        f = self.freq[key]
        del self.buckets[f][key]
        if not self.buckets[f]:
            del self.buckets[f]
            if self.min_freq == f:            # only ever +1: that's why this is O(1)
                self.min_freq = f + 1
        self.freq[key] = f + 1
        self.buckets[f + 1][key] = None       # value lives in self.vals; this is an ordered set

    def get(self, key: Any, default: Any = None) -> Any:
        if key not in self.vals:
            return default
        self._bump(key)
        return self.vals[key]

    def put(self, key: Any, value: Any) -> None:
        if self.cap <= 0:
            return
        if key in self.vals:
            self.vals[key] = value
            self._bump(key)
            return
        if len(self.vals) >= self.cap:
            evict, _ = self.buckets[self.min_freq].popitem(last=False)   # LRU within LFU tie
            if not self.buckets[self.min_freq]:
                del self.buckets[self.min_freq]
            del self.vals[evict], self.freq[evict]
        self.vals[key] = value
        self.freq[key] = 1
        self.buckets[1][key] = None
        self.min_freq = 1                     # a brand-new key resets the minimum

lfu = LFUCache(2)
lfu.put("a", 1); lfu.put("b", 2)
assert lfu.get("a") == 1            # a:2 uses, b:1 use
lfu.put("c", 3)                     # evicts b (lowest freq)
assert lfu.get("b") is None and lfu.get("c") == 3 and lfu.get("a") == 1
lfu.put("d", 4)                     # a:3, c:2 -> evicts c
assert lfu.get("c") is None and lfu.get("d") == 4
```

**Complexity:** O(1) `get` and `put`; O(capacity) space across three dicts.

**Gotcha:** (1) `self.min_freq = 1` on every insert — forgetting it evicts the wrong key next time. (2) You must delete the emptied bucket **and** advance `min_freq` only when the emptied bucket *was* the minimum. (3) LFU without aging is pathological: a key hit 10 000 times last week is immortal even if never used again. Real systems use a decay/window (TinyLFU with a count-min sketch + LRU admission window is the modern answer — Caffeine/`W-TinyLFU`).

**Follow-up they will ask:** "LRU vs LFU — which for an LLM response cache?" → LRU (or a TTL cache) because query popularity shifts and staleness matters more than frequency; LFU wins for stable hot sets like embedding lookups of a fixed catalogue.

---

### Q36. Design the memory for a chat agent: keep the last N turns under a token budget without corrupting tool calls.

`[MEDIUM]`

**Answer:** Keep the system prompt pinned, keep the last `keep_last` turns verbatim, and evict from the front until the token estimate fits — but evict a message **together with its dependent `tool` messages**, because an orphan `tool` message whose `assistant`+`tool_calls` parent was dropped makes the API return a hard 400. Summarise what you evicted into a rolling summary appended after the system prompt.

**Constraints to ask:** budget in tokens? summarise or hard-drop? per-user persistence (Redis/Postgres)? do we also need long-term semantic memory?

**Brute force → optimal:** "keep last 10 messages" ignores message size and breaks with long tool outputs. Token-aware trimming + summarisation of the evicted prefix keeps continuity within a fixed cost per turn.

**Code:**

```python
import json
from dataclasses import dataclass, field
from typing import Any, Callable

def approx_tokens(msg: dict) -> int:
    return max(1, len(json.dumps(msg, ensure_ascii=False)) // 4) + 4   # +4 msg overhead

@dataclass
class ConversationMemory:
    budget: int = 4000
    keep_last: int = 4
    counter: Callable[[dict], int] = approx_tokens
    summarizer: Callable[[list[dict]], str] | None = None
    messages: list[dict] = field(default_factory=list)
    summary: str = ""

    def add(self, role: str, content: str, **extra: Any) -> None:
        self.messages.append({"role": role, "content": content, **extra})
        self.trim()

    def _system(self) -> list[dict]:
        head = [m for m in self.messages if m["role"] == "system"]
        if self.summary:
            head = head + [{"role": "system", "content": f"Conversation so far: {self.summary}"}]
        return head

    def trim(self) -> None:
        convo = [m for m in self.messages if m["role"] != "system"]
        used = sum(self.counter(m) for m in self._system() + convo)
        dropped: list[dict] = []
        while used > self.budget and len(convo) > self.keep_last:
            drop = [convo.pop(0)]
            while convo and convo[0]["role"] == "tool":     # never orphan a tool result
                drop.append(convo.pop(0))
            dropped += drop
            used = sum(self.counter(m) for m in self._system() + convo)
        if dropped and self.summarizer:
            prior = [] if not self.summary else [{"role": "system", "content": self.summary}]
            self.summary = self.summarizer(prior + dropped)
        self.messages = [m for m in self.messages if m["role"] == "system"] + convo

    def render(self) -> list[dict]:
        return self._system() + [m for m in self.messages if m["role"] != "system"]

mem = ConversationMemory(budget=120, keep_last=2,
                         summarizer=lambda msgs: f"summary of {len(msgs)} msgs")
mem.add("system", "You are a helpful assistant.")
for i in range(8):
    mem.add("user", f"question number {i} about retrieval augmented generation")
    mem.add("assistant", f"answer number {i} with plenty of filler text here")
r = mem.render()
assert r[0]["role"] == "system" and "summary of" in r[1]["content"]
assert len([m for m in r if m["role"] != "system"]) >= 2
```

**Complexity:** `trim` is O(n²) as written (it re-sums after each eviction) — fine for n ≤ a few hundred messages; make it O(n) by maintaining a running total. Say this before they do.

**Gotcha:** (1) The orphaned-`tool`-message 400 is the bug they are hunting for. (2) Summarising on **every** turn doubles your LLM calls — trigger it only when eviction actually happens, and cache the summary. (3) `len/4` is an estimate; gate the final payload with `tiktoken`. (4) Storing raw history per user is a PII surface — apply Q25 before persisting.

**Follow-up they will ask:** "Memory types in an agent?" → short-term (this buffer), long-term semantic (embed and store turns in a vector DB, retrieve top-k per query), episodic (past task traces), procedural (the system prompt/skills). "Framework equivalents?" → LangGraph checkpointers (`MemorySaver`, `SqliteSaver`, `PostgresSaver`) persist state per `thread_id`; LangChain's older `ConversationBufferMemory`/`ConversationSummaryMemory` classes are deprecated in 0.3 in favour of LangGraph persistence — do not name them as your current stack.

---

### Q37. Design a resilient client for a flaky third-party LLM/API: retries, rate limiting, circuit breaker, idempotency.

`[HARD]`

**Answer:** Four composed layers. The **retry loop is the outermost** wrapper, and *each attempt* passes through **rate limiter** (do not send what will be rejected) → **circuit breaker** (stop sending to a dead dependency) → the call itself, with an **idempotency key** attached so a retry cannot double-write. Be precise about that nesting — "retry outside, limiter and breaker inside, re-entered per attempt" is the answer; a breaker *outside* the retry loop would count one logical request as N failures. The breaker has three states: CLOSED (normal), OPEN (fail fast, no traffic), HALF_OPEN (one probe after the cooldown; success closes it, failure re-opens it).

**Constraints to ask:** which errors are retryable? is the operation idempotent? what is the total request deadline (a retry budget must respect the caller's SLA)? per-tenant or global limits?

**Brute force → optimal:** retries alone turn a dependency outage into a self-inflicted DDoS and burn your latency budget on calls that cannot succeed. The breaker caps the damage: after k consecutive failures you fail fast in microseconds instead of waiting 30 s per call.

**Code:**

```python
import random, threading, time
from typing import Any, Callable

class CircuitOpen(RuntimeError):
    pass

class CircuitBreaker:
    def __init__(self, fail_max: int = 5, reset_after: float = 30.0) -> None:
        self.fail_max, self.reset_after = fail_max, reset_after
        self.fails, self.opened_at, self.state = 0, 0.0, "closed"
        self._lock = threading.Lock()

    def _allow(self) -> bool:
        with self._lock:
            if self.state == "open":
                if time.monotonic() - self.opened_at >= self.reset_after:
                    self.state = "half_open"          # probe window opens
                    return True                       # NOTE: every waiting caller now gets
                                                      # through -- see Gotcha (2) for the fix
                return False
            return True

    def on_success(self) -> None:
        with self._lock:
            self.fails, self.state = 0, "closed"

    def on_failure(self) -> None:
        with self._lock:
            self.fails += 1
            if self.state == "half_open" or self.fails >= self.fail_max:
                self.state, self.opened_at = "open", time.monotonic()

    def call(self, fn, *a, **kw):
        if not self._allow():
            raise CircuitOpen("circuit open")         # fail fast, no network call
        try:
            out = fn(*a, **kw)
        except Exception:
            self.on_failure()
            raise
        self.on_success()
        return out

class Transient(Exception):
    pass

def _retryable(exc: Exception) -> bool:
    return isinstance(exc, (Transient, TimeoutError, ConnectionError))

class _SimpleBucket:
    def __init__(self, rate: float) -> None:
        self.rate, self.tokens, self.ts = rate, rate, time.monotonic()
    def acquire(self, sleep=time.sleep) -> None:
        while True:
            now = time.monotonic()
            self.tokens = min(self.rate, self.tokens + (now - self.ts) * self.rate)
            self.ts = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            sleep((1 - self.tokens) / self.rate)

class ResilientClient:
    """rate limit -> circuit breaker -> retry with full jitter -> idempotency key."""
    def __init__(self, send: Callable[..., Any], rps: float = 5, tries: int = 3,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.send, self.tries, self.sleep = send, tries, sleep
        self.bucket = _SimpleBucket(rps)
        self.breaker = CircuitBreaker(fail_max=3, reset_after=30.0)

    def request(self, payload: dict, idem_key: str | None = None) -> Any:
        headers = {"Idempotency-Key": idem_key} if idem_key else {}
        for attempt in range(self.tries):
            self.bucket.acquire(sleep=self.sleep)
            try:
                return self.breaker.call(self.send, payload, headers)
            except CircuitOpen:
                raise                                  # do NOT retry an open circuit
            except Exception as exc:
                if not _retryable(exc) or attempt == self.tries - 1:
                    raise
                self.sleep(random.uniform(0, min(8.0, 0.2 * 2 ** attempt)))

hits = {"n": 0}
def flaky_send(payload, headers):
    hits["n"] += 1
    if hits["n"] < 3:
        raise Transient("429")
    return {"ok": True, "seen": hits["n"], "idem": headers.get("Idempotency-Key")}

client = ResilientClient(flaky_send, rps=1000, tries=5, sleep=lambda s: None)
assert client.request({"q": 1}, idem_key="abc-123") == {"ok": True, "seen": 3, "idem": "abc-123"}
```

**Complexity:** O(1) bookkeeping per call; worst-case latency = `tries × (call timeout + backoff)` — always bound it against the caller's deadline.

**Gotcha:** (1) An **open circuit must not be retried** — otherwise your retry loop just burns the breaker. (2) The half-open probe must be limited to one concurrent request, or the moment the cooldown expires all queued threads stampede the recovering service. The implementation above deliberately does **not** do this — flag it yourself before they do, and say the fix is a `probe_in_flight` flag (or a `Semaphore(1)`) cleared in `on_success`/`on_failure`. (3) Retrying without an idempotency key on a POST double-charges/double-writes. (4) A per-process breaker means 10 pods each need their own k failures before protecting the dependency — acceptable, but say it. (5) Failure counting should be by *consecutive failures* or a rolling error **rate**; a fixed cumulative count trips eventually on a healthy service.

**Follow-up they will ask:** "Libraries?" → `tenacity` for retries, `pybreaker`/`circuitbreaker` for breakers, `httpx` transports for timeouts and pooling; at the platform layer, Envoy/Istio or Azure API Management do this outside your code. "What timeouts?" → always set **both** connect and read timeouts. Get the httpx signature right: `httpx.Timeout(60.0, connect=5.0)` — a bare `httpx.Timeout(connect=5, read=60)` raises `ValueError`, because httpx requires either a default or all four of `connect/read/write/pool`. An LLM streaming call needs a long read timeout but a short connect timeout. "How do you observe it?" → emit breaker state transitions, retry counts, and 429 rates as metrics — if you cannot see the breaker open, you cannot debug the outage.

---

## Rapid-Fire (last 10 min before you walk in)

| # | Q | A |
|---|---|---|
| 1 | Time complexity of `x in list` vs `x in set`? | O(n) vs O(1) average, O(n) worst on hash collisions. |
| 2 | Is `list.append` O(1)? | Amortised O(1) — the array over-allocates ~12.5% headroom on growth. |
| 3 | `deque` vs `list` for a queue? | `deque.popleft()` is O(1); `list.pop(0)` is O(n). |
| 4 | Which heap does `heapq` implement? | Min-heap only — negate values or keep a size-k min-heap for top-k. |
| 5 | `heappushpop` vs `heapreplace`? | push-then-pop vs pop-then-push; `heappushpop` can return the item you just pushed. |
| 6 | O(1) LRU needs which two structures? | Hash map + doubly linked list (or `OrderedDict.move_to_end`). |
| 7 | Is `counter += 1` atomic? | No — LOAD/ADD/STORE; use `threading.Lock`. |
| 8 | Bound async concurrency with? | `asyncio.Semaphore(n)` acquired **inside** the coroutine. |
| 9 | Preserve result order across async calls? | `asyncio.gather` returns in input order; `as_completed` in finish order. |
| 10 | Blocking call inside `async def`? | `await asyncio.to_thread(fn, ...)` — direct calls freeze the whole loop. |
| 11 | Token bucket vs sliding window log? | Bucket = O(1) memory, allows bursts; log = exact, O(limit) memory per key. |
| 12 | Backoff formula you quote? | `delay = random.uniform(0, min(cap, base * 2**attempt))` — full jitter. |
| 13 | Retry a 400? | Never. Retry 408/429/500/502/503/504 and timeouts only. |
| 14 | Chunk size and overlap you defend? | 400–800 tokens, 10–20% overlap; tune by recall@k, never by feel. |
| 15 | Chars per token, English? | ~4 (≈0.75 words); much worse for code and Indic scripts. |
| 16 | Cosine equals dot product when? | Both vectors are L2-normalised — so normalise once at ingest. |
| 17 | Top-k from N scores in O(N)? | `np.argpartition(-sims, k-1)[:k]`, then sort just those k. |
| 18 | Embedding dims you should know? | `text-embedding-3-small` 1536, `-large` 3072, `ada-002` 1536; float32 = 4 B/dim. |
| 19 | Duplicate results in top-5, fix? | MMR: `λ·sim(q,d) − (1−λ)·max sim(d, selected)`, λ ≈ 0.5–0.7. |
| 20 | Parse truncated streaming JSON? | Track string/bracket state, close open brackets, drop the dangling `,`/`:`/partial literal. |
| 21 | `@wraps` — why? | Preserves `__name__`/`__doc__`/`__wrapped__`; without it FastAPI introspection and logs break. |
| 22 | `functools.lru_cache` limitation? | No TTL, keys on args, holds strong refs; caching a coroutine caches an un-reawaitable object. |
| 23 | Mutable default argument fix? | `def f(x=None): x = [] if x is None else x` (pydantic: `Field(default_factory=list)`). |
| 24 | Circuit breaker states? | CLOSED → (k failures) → OPEN → (cooldown) → HALF_OPEN → success closes / failure re-opens. |
| 25 | Generator vs list for a 50 GB file? | Generator: O(chunk) memory; `readlines()` loads all 50 GB. |

---

## Red Flags / Do NOT say

- **"I'd just use `openai.ChatCompletion.create`."** — removed in openai 1.0 (2023). Say `client.chat.completions.create(...)` from `from openai import OpenAI`.
- **"`from langchain.llms import OpenAI`."** — legacy pre-0.1 import. Current: `from langchain_openai import ChatOpenAI` / `AzureChatOpenAI`, `from langchain_core.prompts import ChatPromptTemplate`.
- **"I use `ConversationBufferMemory`."** — deprecated in LangChain 0.3; say LangGraph checkpointers / your own trimming (Q36).
- **"The GIL means Python can't do concurrency."** — wrong framing. The GIL limits **CPU-bound parallelism in threads**; I/O-bound work scales fine with asyncio or threads, and CPU-bound work goes to processes.
- **"`counter += 1` is atomic because of the GIL."** — it is not; it is three bytecodes.
- **"I'd sort to get the top-k."** — for k ≪ N say heap O(n log k) or `argpartition` O(n) first, then mention sorting as the simple fallback.
- **"Cosine similarity above 0.8 means it's relevant."** — thresholds are model-specific and do not transfer; calibrate on your own data.
- **"I'd retry until it succeeds."** — unbounded retries with no jitter, no breaker and no idempotency key is how you take down a dependency.
- **"I'd load the whole file/corpus into memory."** — for anything sized in GB, lead with a generator.
- **Silence.** In a face-to-face round, thinking quietly for 90 seconds reads as being stuck. Narrate: "brute force is X at O(n²); I think a hash map makes it O(n) — let me check the edge cases first."
- **Do not claim a library API you are unsure of.** Say "I'd check the exact signature, but the shape is `client.embeddings.create(model=..., input=[...])`." Confident wrong API names are worse than an honest hedge.
