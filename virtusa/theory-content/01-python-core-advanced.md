# Python Core & Advanced — Interview Questions

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

**How to use this file:** read the bold **Answer:** line first — that is your spoken answer. Detail below it is only for follow-ups. On paper/whiteboard write the short version of any **Code:** block. Version tags matter: say "3.11+" out loud, it signals you actually track the language.

## Table of Contents

| # | Section | Qs |
|---|---------|----|
| 1 | [Data Model & Object Internals](#1-data-model--object-internals) | Q1–Q8 |
| 2 | [Functions, Closures, Decorators](#2-functions-closures-decorators) | Q9–Q15 |
| 3 | [Iterators, Generators, Streaming](#3-iterators-generators-streaming) | Q16–Q21 |
| 4 | [Context Managers](#4-context-managers) | Q22–Q24 |
| 5 | [GIL & Concurrency Model](#5-gil--concurrency-model) | Q25–Q29 |
| 6 | [Asyncio Deep Dive](#6-asyncio-deep-dive) | Q30–Q37 |
| 7 | [Memory, GC, Copy Semantics](#7-memory-gc-copy-semantics) | Q38–Q42 |
| 8 | [Typing, Pydantic v2, Data Modelling](#8-typing-pydantic-v2-data-modelling) | Q43–Q50 |
| 9 | [Exceptions & Retry](#9-exceptions--retry) | Q51–Q53 |
| 10 | [Performance & Profiling](#10-performance--profiling) | Q54–Q56 |
| 11 | [Packaging & Environments](#11-packaging--environments) | Q57–Q58 |
| 12 | [Testing](#12-testing) | Q59–Q61 |
| 13 | [Logging & Observability](#13-logging--observability) | Q62–Q63 |
| — | [Red Flags / Do NOT say](#red-flags--do-not-say) | — |
| — | [Rapid-Fire (last 10 min before you walk in)](#rapid-fire-last-10-min-before-you-walk-in) | 25 |

---

## 1. Data Model & Object Internals

### Q1. What is the "Python data model"? What actually happens when you call `len(x)` or `x + y`?
`[EASY]`

**Answer:** The data model is the set of dunder (double-underscore) hooks that let *your* classes plug into built-in syntax. `len(x)` calls `type(x).__len__(x)`; `x + y` calls `type(x).__add__(x, y)` and falls back to `type(y).__radd__(y, x)` if that returns `NotImplemented`.

Key point interviewers probe: **special methods are looked up on the type, not the instance.** Assigning `x.__len__ = lambda: 5` does nothing for `len(x)`. That's why `__enter__`/`__exit__` must be defined on the class, not patched onto an object.

Groups worth naming: construction (`__new__`, `__init__`, `__del__`), representation (`__repr__`, `__str__`, `__format__`), comparison/hash (`__eq__`, `__lt__`, `__hash__`), container (`__len__`, `__getitem__`, `__contains__`, `__iter__`), callable (`__call__`), context (`__enter__`/`__exit__`, `__aenter__`/`__aexit__`), attribute access (`__getattr__`, `__getattribute__`, `__setattr__`), descriptors (`__get__`/`__set__`/`__set_name__`), async (`__await__`, `__aiter__`, `__anext__`).

**Gotcha:** `__repr__` should be unambiguous and ideally eval-able; `__str__` is for humans. If you only define one, define `__repr__` — `str()` falls back to it, not the reverse. In AI apps this matters: your `AgentState` repr is what shows up in every log line.

**Follow-up they will ask:** *"How do you make an object callable?"* → define `__call__`. This is exactly how LangChain-style tools and agent "runnables" are implemented — an object with config in `__init__` and behaviour in `__call__`.

---

### Q2. `__new__` vs `__init__`. When do you actually need `__new__`?
`[MEDIUM]`

**Answer:** `__new__` is the static allocator — it creates and returns the instance. `__init__` is the initialiser — it receives the already-created instance and returns `None`. You need `__new__` only when you must control creation itself: subclassing immutables (`int`, `str`, `tuple`), singletons/pools, or metaclass-ish factory behaviour.

**Code:**

```python
class OpenAIClientPool:
    """One client per (base_url, api_key) — avoids re-opening HTTP pools per request."""
    _instances: dict[tuple[str, str], "OpenAIClientPool"] = {}

    def __new__(cls, base_url: str, api_key: str) -> "OpenAIClientPool":
        key = (base_url, api_key)
        if key not in cls._instances:
            inst = super().__new__(cls)
            inst._initialised = False
            cls._instances[key] = inst
        return cls._instances[key]

    def __init__(self, base_url: str, api_key: str) -> None:
        if self._initialised:          # __init__ runs on EVERY call, guard it
            return
        self.base_url, self.api_key = base_url, api_key
        self._initialised = True
```

**Gotcha:** If `__new__` returns an instance of `cls`, Python then calls `__init__` on it — every time, even for a cached singleton. If `__new__` returns something that is *not* an instance of `cls`, `__init__` is skipped entirely.

**Follow-up they will ask:** *"Better way to do a singleton?"* → module-level instance (modules are singletons in Python), or `@functools.lru_cache` on a factory function. Say that first; it shows judgement.

---

### Q3. Explain MRO and C3 linearization. Solve the diamond by hand.
`[HARD]`

**Answer:** MRO (method resolution order) is the deterministic order Python searches classes for an attribute. CPython computes it with **C3 linearization**: `L[C] = C + merge(L[B1], L[B2], ..., [B1, B2, ...])`, where `merge` repeatedly takes the head of the first list that does not appear in the *tail* of any other list. It guarantees (a) a class precedes its parents, (b) the order of bases in the class statement is preserved (monotonicity). If no consistent order exists, Python raises `TypeError: Cannot create a consistent method resolution order`.

**Code:**

```python
class A:
    def who(self): return "A"
class B(A):
    def who(self): return "B->" + super().who()
class C(A):
    def who(self): return "C->" + super().who()
class D(B, C):
    def who(self): return "D->" + super().who()

print([c.__name__ for c in D.__mro__])  # ['D', 'B', 'C', 'A', 'object']
print(D().who())                        # D->B->C->A
```

Hand-derivation to write on the whiteboard:
`L[D] = D + merge(L[B], L[C], [B, C]) = D + merge([B,A,o], [C,A,o], [B,C])`
→ take `B` (not in any tail) → then `A`? no, `A` is in the tail of `[C,A,o]` → take `C` → then `A` → then `object`. **D, B, C, A, object.**

**Gotcha:** `super()` does **not** mean "my parent". It means "the next class after me *in the MRO of type(self)*". That's why `B.who` calls `C.who` even though `B` doesn't know `C` exists. This is cooperative multiple inheritance — and it only works if every class in the chain calls `super()` and accepts compatible arguments (`**kwargs` pass-through).

**Follow-up they will ask:** *"Why does everyone say prefer composition?"* → because cooperative MI requires every mixin to be written for it. In agent frameworks I'd use composition + `Protocol` for pluggability, mixins only for thin cross-cutting behaviour (e.g. a `RetryMixin`).

---

### Q4. What is a metaclass? Give a real use case. What's the modern alternative?
`[HARD]`

**Answer:** A metaclass is the class of a class — `type` is the default. It runs at **class-creation time** and can inspect/rewrite the namespace. Real uses: auto-registration (plugin/tool registries), enforcing an interface at import time, injecting `__slots__`, ORM/schema DSLs (Django models, pydantic v1 used one). **Modern alternative: `__init_subclass__` + `__set_name__` (3.6+) covers ~90% of cases and is far simpler — use those unless you must change the class object itself.**

**Code:**

```python
# Metaclass version: an agent-tool registry with signature enforcement.
from typing import Any

class ToolMeta(type):
    registry: dict[str, type] = {}

    def __new__(mcls, name: str, bases: tuple, ns: dict[str, Any], **kw):
        cls = super().__new__(mcls, name, bases, ns, **kw)
        if bases:  # skip the abstract base itself
            if "run" not in ns:
                raise TypeError(f"{name} must define run()")
            mcls.registry[ns.get("tool_name", name.lower())] = cls
        return cls

class Tool(metaclass=ToolMeta):
    pass

class SearchTool(Tool):
    tool_name = "search"
    def run(self, q: str) -> str: return f"results for {q}"

assert ToolMeta.registry["search"] is SearchTool
```

```python
# Preferred modern version — no metaclass needed.
class Tool:
    registry: dict[str, type["Tool"]] = {}

    def __init_subclass__(cls, /, name: str | None = None, **kw) -> None:
        super().__init_subclass__(**kw)
        if not hasattr(cls, "run"):
            raise TypeError(f"{cls.__name__} must define run()")
        Tool.registry[name or cls.__name__.lower()] = cls

class SearchTool(Tool, name="search"):
    def run(self, q: str) -> str: return f"results for {q}"
```

**Gotcha:** Metaclass conflicts. If you inherit from two classes with different metaclasses (e.g. an ABC and a pydantic model) you get `TypeError: metaclass conflict`. The metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases.

**Follow-up they will ask:** *"Have you ever written one in production?"* → Honest, strong answer: "Rarely. I've used `__init_subclass__` for a tool registry in an agent framework; metaclasses only when integrating with a library that already used one."

---

### Q5. Explain the descriptor protocol. Data vs non-data descriptor, and the lookup precedence.
`[HARD]`

**Answer:** A descriptor is any object defining `__get__`, and optionally `__set__`/`__delete__`. **Data descriptor** = defines `__set__` or `__delete__`; **non-data descriptor** = only `__get__` (e.g. plain functions, `staticmethod`, `classmethod`). Attribute lookup order on an instance: **type's data descriptor → instance `__dict__` → type's non-data descriptor / class attribute → `__getattr__`.** `property`, `functools.cached_property` (non-data), and bound methods are all descriptors.

**Code:**

```python
class Bounded:
    """Validated, self-naming attribute — e.g. LLM sampling params."""
    def __init__(self, lo: float, hi: float) -> None:
        self.lo, self.hi = lo, hi

    def __set_name__(self, owner: type, name: str) -> None:
        self.private = "_" + name          # 3.6+: learn your own attribute name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self                    # accessed on the class
        return getattr(obj, self.private)

    def __set__(self, obj, value: float) -> None:
        if not self.lo <= value <= self.hi:
            raise ValueError(f"{self.private[1:]} must be in [{self.lo}, {self.hi}]")
        setattr(obj, self.private, value)

class LLMConfig:
    temperature = Bounded(0.0, 2.0)
    top_p = Bounded(0.0, 1.0)
    def __init__(self, temperature: float = 0.7, top_p: float = 1.0):
        self.temperature, self.top_p = temperature, top_p

LLMConfig(temperature=3.0)   # ValueError: temperature must be in [0.0, 2.0]
```

**Gotcha:** `cached_property` is a **non-data** descriptor — that's the whole trick: it computes once, writes the value into the instance `__dict__`, and every later access hits the instance dict first and never calls the descriptor again. It therefore requires the instance to have a `__dict__`, so **`cached_property` does not work with `__slots__`**.

**Follow-up they will ask:** *"Why not just use `property`?"* → `property` doesn't scale: you'd write the same validation three times for three fields. Descriptors are reusable; `property` is the single-attribute special case (it *is* a data descriptor).

---

### Q6. What does `__slots__` do? When is it a win, and what breaks?
`[MEDIUM]`

**Answer:** `__slots__` replaces the per-instance `__dict__` with a fixed array of descriptors, one per named attribute. Wins: **roughly 50–70% less memory per small instance, plus faster attribute access**, which matters when you hold millions of small objects (chunk metadata, embedding records, token events). Breaks: no arbitrary new attributes, no `__dict__`, no `cached_property`, no `weakref` unless you add `"__weakref__"` to slots, and multiple inheritance from two slotted classes with non-empty slots is a `TypeError`.

**Code:**

```python
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)     # slots= is 3.10+
class Chunk:
    doc_id: str
    ordinal: int
    text: str

# Measured on CPython 3.10 for this 3-attribute class (sys.getsizeof):
#   dict-based:  48 B instance  +  ~104 B __dict__   =  ~152 B total
#   slotted:     ~56 B  (16 B header + 3 * 8 B slot pointers)
# ~60% saved per object; at 2M chunks that is a couple of hundred MB.
# Numbers shift by version (3.11+ key-sharing dicts) — quote them as "order of",
# and say you'd measure with tracemalloc on the real class.
```

**Gotcha:** A subclass of a slotted class that does **not** declare `__slots__` silently gets a `__dict__` back — you lose the saving. Every class in the chain must declare it. Also `@dataclass(slots=True)` *returns a new class object*, so any decorator/reference captured before it (or `super()` zero-arg form in some edge cases) can misbehave; keep it as the outermost transform.

**Follow-up they will ask:** *"Measure it?"* → `sys.getsizeof(obj)` plus `pympler.asizeof` for deep size, or just `tracemalloc` snapshots before/after loading N records.

---

### Q7. `__eq__` and `__hash__` contract. What breaks if you get it wrong?
`[MEDIUM]`

**Answer:** Rule: **if `a == b` then `hash(a) == hash(b)`**, and hash must be stable for the object's lifetime. Defining `__eq__` sets `__hash__ = None` automatically, making instances unhashable (can't be dict keys / set members) — that's deliberate, because mutable-and-equal objects break hash tables. Fix by making the object immutable and defining `__hash__` over the same fields, or `@dataclass(frozen=True)` which does both.

**Code:**

```python
from dataclasses import dataclass
import hashlib, json

@dataclass(frozen=True, slots=True)
class PromptKey:
    model: str
    temperature: float
    prompt: str

    def cache_id(self) -> str:            # stable across processes, unlike hash()
        blob = json.dumps(self.__dict__ if not hasattr(self, "__slots__")
                          else {s: getattr(self, s) for s in self.__slots__},
                          sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

cache: dict[PromptKey, str] = {}
```

**Gotcha:** `hash()` of `str`/`bytes` is **randomised per process** (PYTHONHASHSEED, siphash) — never persist it to Redis or a DB as a cache key. Use `hashlib.sha256`/`blake2b` for anything crossing a process boundary. This is a very common real bug in LLM response caches.

**Follow-up they will ask:** *"Mutable object as dict key?"* → allowed only if you define `__hash__` yourself, and it's a bug magnet: mutate the object and you can no longer find it in the dict.

---

### Q8. `__getattr__` vs `__getattribute__`. Show a practical use.
`[MEDIUM]`

**Answer:** `__getattribute__` is called for **every** attribute access; `__getattr__` is called **only as a fallback** when normal lookup raised `AttributeError`. Override `__getattr__` for lazy loading / proxies / dynamic attributes. Almost never override `__getattribute__` (easy infinite recursion, big perf hit) — if you do, call `super().__getattribute__(name)` inside.

**Code:**

```python
from typing import Any

class LazyLLMClient:
    """Defer constructing the SDK client until first real use (fast app import,
    and no crash at import time if the key is missing)."""
    def __init__(self, **cfg: Any) -> None:
        # Set internals in __init__ so they live in the instance __dict__ and
        # never reach __getattr__. (object.__setattr__ only matters if you also
        # override __setattr__ — plain `self._cfg = cfg` is equivalent here.)
        self._cfg = cfg
        self._client: Any = None

    def __getattr__(self, name: str) -> Any:      # only for misses
        if name.startswith("_"):                  # never recurse on internals
            raise AttributeError(name)
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(**self._cfg)
        return getattr(self._client, name)

llm = LazyLLMClient()
# llm.chat.completions.create(...)  -> builds the real client on first touch
```

**Gotcha:** Inside `__getattr__`, referring to a not-yet-set attribute re-enters `__getattr__` → `RecursionError`. Guard by (a) assigning every internal in `__init__` so normal lookup finds it, and (b) raising `AttributeError` early for `name.startswith("_")` — both shown above. If the class *also* overrides `__setattr__`, use `object.__setattr__(self, ...)` in `__init__` to bypass it.

**Follow-up they will ask:** *"What about `__getattr__` on a module?"* → PEP 562 (3.7+): define a module-level `__getattr__(name)` for lazy submodule imports and deprecation shims.

---

## 2. Functions, Closures, Decorators

### Q9. Why is a mutable default argument dangerous? Show the fix.
`[EASY]`

**Answer:** Default values are evaluated **once, at function definition time**, and stored on the function object (`func.__defaults__`). A mutable default is therefore shared across all calls. Fix with a `None` sentinel.

**Code:**

```python
def add_msg(text: str, history: list[str] = []) -> list[str]:   # BUG
    history.append(text); return history

add_msg("a"); add_msg("b")   # -> ['a', 'b']  (history leaked between calls)

def add_msg(text: str, history: list[str] | None = None) -> list[str]:  # FIX
    history = [] if history is None else history
    history.append(text); return history
```

**Gotcha:** Same trap in dataclasses — use `field(default_factory=list)`; in pydantic v2 — `Field(default_factory=list)`. Pydantic v2 actually deep-copies mutable defaults for you, but do not rely on that in interviews or in plain classes.

**Follow-up they will ask:** *"Is a mutable default ever intentional?"* → yes, as a poor-man's memo cache (`def f(x, _cache={})`), but `functools.cache` is clearer.

---

### Q10. Explain the late-binding closure bug and three fixes.
`[MEDIUM]`

**Answer:** Closures capture **variables, not values**. A lambda created in a loop reads the loop variable at *call* time, by which point the loop has finished. Fixes: (1) default-argument binding, (2) `functools.partial`, (3) a factory function.

**Code:**

```python
models = ["gpt-4o", "gpt-4o-mini", "o4-mini"]

bad = [lambda p: call(m, p) for m in models]
bad[0]("hi")     # all three use m == "o4-mini"

fix1 = [lambda p, m=m: call(m, p) for m in models]        # default arg
from functools import partial
fix2 = [partial(call, m) for m in models]                 # partial (cleanest)
def make(m): return lambda p: call(m, p)
fix3 = [make(m) for m in models]                          # factory / new scope
```

**Gotcha:** Comprehensions have their own scope, but that scope is shared by all lambdas created inside them — the bug still bites. `nonlocal` (rebind enclosing scope) vs `global` (rebind module scope) is the standard follow-up; without them, assignment inside a nested function creates a *new local*.

**Follow-up they will ask:** *"Where do closure variables live?"* → `func.__closure__` is a tuple of `cell` objects; `func.__code__.co_freevars` names them.

---

### Q11. Write a decorator that logs latency. Why `functools.wraps`?
`[EASY]`

**Answer:** A decorator is a callable taking a function and returning a replacement. `functools.wraps` copies `__module__`, `__name__`, `__qualname__`, `__doc__`, `__annotations__`, updates `__dict__`, and sets `__wrapped__` — without it your logs, `help()`, pydantic/FastAPI signature introspection, and `inspect.signature` all break. (`inspect.signature` follows `__wrapped__`, which is why the *original* signature survives even though the wrapper is `(*args, **kwargs)`.)

**Code:**

```python
import functools, logging, time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P"); R = TypeVar("R")
log = logging.getLogger(__name__)

def timed(fn: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            log.info("call_complete", extra={"fn": fn.__qualname__,
                                             "ms": round((time.perf_counter() - t0) * 1000, 2)})
    return wrapper
```

**Gotcha:** Use `time.perf_counter()` (monotonic, high resolution), never `time.time()` (wall clock, can jump backwards with NTP). `finally` ensures the timing is recorded even when the wrapped call raises — important for measuring LLM timeouts.

**Follow-up they will ask:** *"How do you get the original function back?"* → `wrapper.__wrapped__`, or `inspect.unwrap(wrapper)`.

---

### Q12. Write a decorator that takes arguments — e.g. `@retry(times=3)`.
`[MEDIUM]`

**Answer:** A parameterised decorator is a function returning a decorator returning a wrapper — three levels. Optionally support bare usage by checking if the first positional argument is callable.

**Code:**

```python
import functools, random, time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P"); R = TypeVar("R")

def retry(times: int = 3,
          base: float = 0.5,
          exceptions: tuple[type[BaseException], ...] = (Exception,)
          ) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*a: P.args, **kw: P.kwargs) -> R:
            last: BaseException | None = None
            for attempt in range(times):
                try:
                    return fn(*a, **kw)
                except exceptions as exc:
                    last = exc
                    if attempt == times - 1:
                        break
                    # exponential backoff with full jitter
                    time.sleep(random.uniform(0, base * 2 ** attempt))
            assert last is not None
            # Re-raise the ORIGINAL exception (tenacity's reraise=True behaviour).
            # Wrapping it in RuntimeError would stop callers catching ConnectionError.
            last.add_note(f"{fn.__qualname__} failed after {times} attempts")  # 3.11+
            raise last
        return wrapper
    return decorator

@retry(times=4, exceptions=(TimeoutError, ConnectionError))
def embed(text: str) -> list[float]:
    ...
```

**Gotcha:** In production use `tenacity` rather than hand-rolling — but know the hand-rolled version for the whiteboard. Never retry non-idempotent or non-transient failures (HTTP 400 `BadRequestError`, context-length exceeded); retrying a 400 burns quota and fixes nothing.

**Follow-up they will ask:** *"Make it work on async functions too."* → see Q14.

---

### Q13. Class decorator vs metaclass vs `__init_subclass__` — pick one.
`[MEDIUM]`

**Answer:** Preference order: **`__init_subclass__` (affects subclasses, simplest) → class decorator (affects exactly the decorated class, explicit and readable) → metaclass (last resort, viral through inheritance).** A class decorator receives the class object after creation and returns a class — that's how `@dataclass`, `@functools.total_ordering` and most registries work.

**Code:**

```python
TOOLS: dict[str, type] = {}

def register_tool(name: str):
    def deco(cls: type) -> type:
        cls.tool_name = name           # type: ignore[attr-defined]
        TOOLS[name] = cls
        return cls
    return deco

@register_tool("web_search")
class WebSearch:
    def run(self, q: str) -> str: ...
```

**Gotcha:** A class decorator does **not** apply to subclasses; `__init_subclass__`/metaclass do. Choose based on that, not on taste.

**Follow-up they will ask:** *"How does `@dataclass` work?"* → it inspects `__annotations__`, builds source for `__init__`/`__repr__`/`__eq__` as strings, `exec`s them, and attaches them to the class.

---

### Q14. Write one decorator that works for both sync and async functions.
`[HARD]`

**Answer:** Detect with `inspect.iscoroutinefunction(fn)` and return the matching wrapper. This matters in AI codebases where the same retry/tracing decorator must wrap `client.chat.completions.create` and `await async_client...create`.

**Code:**

```python
import asyncio, functools, inspect, time, logging
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

def traced(fn: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def awrapper(*a: Any, **kw: Any) -> Any:
            t0 = time.perf_counter()
            try:
                return await fn(*a, **kw)
            finally:
                log.info("%s %.1fms", fn.__qualname__, (time.perf_counter() - t0) * 1000)
        return awrapper

    @functools.wraps(fn)
    def swrapper(*a: Any, **kw: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return fn(*a, **kw)
        finally:
            log.info("%s %.1fms", fn.__qualname__, (time.perf_counter() - t0) * 1000)
    return swrapper
```

**Gotcha:** `inspect.iscoroutinefunction` returns `False` for an already-decorated function whose wrapper is sync, and for `functools.partial` in older versions (3.8+ handles partial). Async **generators** are a separate case — check `inspect.isasyncgenfunction` and wrap with `async for ... yield`, otherwise you silently break token streaming.

**Follow-up they will ask:** *"What if the wrapped function is a FastAPI route?"* → you must preserve the signature (`functools.wraps` does) because FastAPI builds the request model from `inspect.signature`; adding `*args, **kwargs` without `wraps` breaks dependency injection.

---

### Q15. Explain `*args`/`**kwargs`, positional-only `/`, keyword-only `*`.
`[EASY]`

**Answer:** `*args` collects extra positionals into a tuple, `**kwargs` extra keywords into a dict. In a signature, everything **before `/` is positional-only**, everything **after a bare `*` is keyword-only**. Keyword-only params are the API-stability tool: callers can't depend on argument order, so you can insert parameters later without breaking them.

**Code:**

```python
def generate(prompt: str, /, *, model: str = "gpt-4o-mini",
             temperature: float = 0.7, max_tokens: int | None = None) -> str:
    ...

generate("hi", model="o4-mini")      # ok
generate("hi", "o4-mini")            # TypeError: takes 1 positional argument
```

**Gotcha:** In a call, `*` and `**` mean unpacking, not collecting: `f(*lst, **dct)`. Mixing dict unpacking with a duplicate keyword raises `TypeError: got multiple values for keyword argument`.

**Follow-up they will ask:** *"Why positional-only?"* → lets you rename the parameter later, and matches C-implemented builtins (`len(obj, /)`).

---

## 3. Iterators, Generators, Streaming

### Q16. Iterable vs iterator vs generator.
`[EASY]`

**Answer:** **Iterable** = has `__iter__` (can produce a fresh iterator). **Iterator** = has `__next__` *and* `__iter__` returning `self`; it is stateful and exhausts once. **Generator** = an iterator created by a function containing `yield` (or a generator expression); it's lazy and holds its frame between yields.

**Code:**

```python
lst = [1, 2, 3]
it = iter(lst)            # list is iterable, not an iterator
next(it)                  # 1
list(it), list(it)        # ([2, 3], [])  -> iterators exhaust

def gen():
    yield 1; yield 2
g = gen()
iter(g) is g              # True -> generators are their own iterator
```

**Gotcha:** A generator can only be consumed once. If you `yield` retrieved RAG chunks and then try to both re-rank and count them, the second pass sees nothing. Materialise with `list()` when you need multiple passes, or use `itertools.tee` (which buffers).

**Follow-up they will ask:** *"How does a `for` loop work under the hood?"* → calls `iter(obj)`, then `next()` repeatedly, stopping on `StopIteration`. Legacy fallback: if no `__iter__`, Python uses `__getitem__` with 0,1,2,…

---

### Q17. What does `yield from` do? What are `send`, `throw`, `close`?
`[MEDIUM]`

**Answer:** `yield from sub` delegates: it yields everything from `sub`, **and** transparently forwards `send()`/`throw()` into the sub-generator, and makes `sub`'s `return` value the result of the expression. `send(v)` resumes the generator making the paused `yield` evaluate to `v` (coroutine-style); `throw(exc)` raises inside it; `close()` raises `GeneratorExit` at the yield point so `finally` blocks run.

**Code:**

```python
from collections.abc import Iterator, Generator

def read_file(path: str) -> Iterator[str]:
    with open(path, encoding="utf-8") as f:
        yield from f                       # delegate, and close file on exhaustion
    # 'return value' here would become the value of `yield from`

def token_counter() -> Generator[int, str, None]:   # Generator[Yield, Send, Return]
    """Accumulator driven by .send() — counts streamed tokens."""
    total = 0
    while True:
        chunk = yield total                # value sent in becomes `chunk`
        total += len(chunk.split())

c = token_counter(); next(c)               # prime it -> yields 0
c.send("hello world")                      # 2  (0 + 2 words)
c.send("more tokens here")                 # 5  (2 + 3 words)
c.close()
```

**Gotcha:** You must "prime" a `send`-based generator with `next(g)` (or `g.send(None)`) before the first real `send`, else `TypeError: can't send non-None value to a just-started generator`.

**Follow-up they will ask:** *"Relation to async?"* → pre-3.5 coroutines were literally generators with `yield from` (`@asyncio.coroutine`, deprecated in 3.8 and **removed in 3.11** — don't write it). Today `async def`/`await` are distinct types, but the mechanism (suspend/resume a frame) is the same.

---

### Q18. You must embed a 5 GB JSONL corpus. How do you avoid OOM?
`[MEDIUM]`

**Answer:** Never materialise; build a lazy pipeline of generators and batch at the end. Read line-by-line (`for line in f` is already lazy), parse, filter, chunk, then group into fixed-size batches for the embeddings API. Memory stays O(batch), not O(corpus).

**Code:**

```python
import json
from collections.abc import Iterator, Iterable
from itertools import islice

def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:                      # lazy, one line in memory
            if line.strip():
                yield json.loads(line)

def batched(it: Iterable, n: int) -> Iterator[list]:
    """itertools.batched exists in 3.12+; this is the portable equivalent."""
    iterator = iter(it)
    while chunk := list(islice(iterator, n)):
        yield chunk

def embed_corpus(path: str, client, model: str = "text-embedding-3-small") -> Iterator[tuple[str, list[float]]]:
    docs = (d for d in read_jsonl(path) if d.get("text"))
    for batch in batched(docs, 128):        # OpenAI embeddings: batch inputs
        resp = client.embeddings.create(model=model, input=[d["text"] for d in batch])
        for d, item in zip(batch, resp.data, strict=True):
            yield d["id"], item.embedding
```

**Gotcha:** `zip(..., strict=True)` (3.10+) catches silent misalignment between inputs and returned embeddings — a nasty class of RAG bug where vectors get attached to the wrong document. Also: `text-embedding-3-small` is 1536-dim, `-3-large` is 3072-dim, and both support the `dimensions` parameter to shorten (Matryoshka) — quote that if asked about vector DB sizing.

**Follow-up they will ask:** *"How would you parallelise it?"* → async fan-out with a `Semaphore` (Q32), or a process pool if the bottleneck is local CPU (chunking/tokenising), not the API.

---

### Q19. Write a generator that streams LLM tokens, and expose it over FastAPI.
`[MEDIUM]`

**Answer:** Iterate the streaming response and `yield` only the non-empty delta content; the generator keeps constant memory and gives the caller first-token latency instead of full-completion latency. In FastAPI, hand that generator to `StreamingResponse` with `text/event-stream`.

**Code:**

```python
import json
from collections.abc import AsyncIterator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI()

async def stream_tokens(prompt: str, model: str = "gpt-4o-mini") -> AsyncIterator[str]:
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        timeout=60,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue                      # usage-only / filter chunks
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

@app.get("/chat")
async def chat(q: str) -> StreamingResponse:
    async def sse() -> AsyncIterator[str]:
        try:
            async for tok in stream_tokens(q):
                # JSON-encode the payload: a raw token containing "\n" would end
                # the SSE data field early and silently corrupt the stream.
                yield f"data: {json.dumps({'delta': tok})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:                       # never leak a raw traceback
            yield ("event: error\n"
                   f"data: {json.dumps({'detail': type(exc).__name__})}\n\n")
    return StreamingResponse(sse(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})  # disable nginx buffering
```

**Gotcha:** Four real-world traps: (1) `chunk.choices` can be an **empty list** on the final usage chunk when `stream_options={"include_usage": True}` — index it blindly and you get `IndexError` at the very end of every stream; (2) proxies buffer SSE unless you disable it (`X-Accel-Buffering: no`); (3) once headers are sent you cannot change the HTTP status code, so errors must be streamed as an SSE event; (4) **never interpolate a raw token into `data: {tok}`** — code blocks and markdown contain newlines, and a newline terminates the SSE `data` field. JSON-encode the payload.

**Follow-up they will ask:** *"How do you get token usage when streaming?"* → pass `stream_options={"include_usage": True}`; the final chunk carries `usage` with `choices == []`.

---

### Q20. Async generators — how do they differ, and what's the cleanup trap?
`[HARD]`

**Answer:** An `async def` function containing `yield` is an **async generator**: consumed with `async for`, has `__aiter__`/`__anext__`, and can `await` between yields. Trap: if the consumer stops early (client disconnect, `break`), the generator is suspended and its `finally`/`async with` cleanup runs only when it's finalised — which for async generators depends on the loop's async-gen shutdown hooks. Use `contextlib.aclosing` to make cleanup deterministic.

**Code:**

```python
from contextlib import aclosing            # 3.10+
from collections.abc import AsyncIterator
from openai import AsyncOpenAI

client = AsyncOpenAI()                     # one shared client (see Q24)

async def tokens(prompt: str) -> AsyncIterator[str]:
    stream = await client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], stream=True)
    try:
        async for chunk in stream:
            if chunk.choices and (d := chunk.choices[0].delta.content):
                yield d
    finally:
        await stream.close()               # release the HTTP connection

async def first_n(prompt: str, n: int) -> list[str]:
    out: list[str] = []
    async with aclosing(tokens(prompt)) as gen:   # guarantees athrow(GeneratorExit)
        async for tok in gen:
            out.append(tok)
            if len(out) >= n:
                break                      # early exit -> cleanup still runs now
    return out
```

**Gotcha:** You cannot call `next()` on an async generator, and you cannot `await` inside a plain generator's `__next__`. `asyncio.run()` calls `loop.shutdown_asyncgens()` for you — if you drive the loop manually, you must call it or leak connections.

**Follow-up they will ask:** *"Async comprehension?"* → `[x async for x in agen()]` is valid inside an `async def`.

---

### Q21. Show useful `itertools`/`functools` for data pipelines.
`[MEDIUM]`

**Answer:** `islice` (lazy slicing), `batched` (3.12+, fixed-size chunks), `chain.from_iterable` (flatten), `groupby` (requires pre-sorted input), `tee` (duplicate an iterator, buffers), `accumulate`, plus `functools.reduce` and `operator.itemgetter`.

**Code:**

```python
from itertools import islice, chain, groupby, batched   # batched: 3.12+
from operator import itemgetter

chunks = [{"doc": "a", "t": "x"}, {"doc": "a", "t": "y"}, {"doc": "b", "t": "z"}]

# group retrieved chunks by parent doc (MUST sort by the same key first)
chunks.sort(key=itemgetter("doc"))
for doc, grp in groupby(chunks, key=itemgetter("doc")):
    print(doc, [c["t"] for c in grp])

flat = list(chain.from_iterable([[1, 2], [3], [4, 5]]))   # [1,2,3,4,5]
first5 = list(islice(iter(range(1000)), 5))
for b in batched(range(10), 4):                            # (0,1,2,3) (4,5,6,7) (8,9)
    print(b)
```

**Gotcha:** `groupby` groups **consecutive** equal keys only — unsorted input silently produces duplicate groups. And the sub-iterator is invalidated once you advance to the next group, so materialise it (`list(grp)`) if you need it later.

**Follow-up they will ask:** *"`batched` on 3.11?"* → write the `islice` loop from Q18; `batched` is 3.12+.

---

## 4. Context Managers

### Q22. Implement a context manager as a class. What does returning `True` from `__exit__` do?
`[MEDIUM]`

**Answer:** `__enter__` returns the value bound by `as`; `__exit__(exc_type, exc, tb)` runs on exit. **Returning a truthy value from `__exit__` suppresses the exception**; returning `None`/falsy lets it propagate. Never suppress by accident.

**Code:**

```python
import time, logging
from types import TracebackType

log = logging.getLogger(__name__)

class LLMSpan:
    def __init__(self, name: str, **tags: object) -> None:
        self.name, self.tags = name, tags

    def __enter__(self) -> "LLMSpan":
        self.t0 = time.perf_counter()
        self.tokens = 0
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc: BaseException | None,
                 tb: TracebackType | None) -> bool:
        log.info("span", extra={"name": self.name, "ok": exc is None,
                                "ms": (time.perf_counter() - self.t0) * 1000,
                                "tokens": self.tokens, **self.tags})
        return False        # do NOT swallow exceptions

with LLMSpan("rag.retrieve", index="prod") as span:
    span.tokens = 812
```

**Gotcha:** `__exit__` is called even when the body raises, but *not* if `__enter__` itself raises. Also, `with A() as a, B() as b:` is equivalent to nested `with` — `B` is only entered if `A.__enter__` succeeded, and both `__exit__`s run in reverse order.

**Follow-up they will ask:** *"Where have you used one?"* → DB transactions, `httpx.AsyncClient`, timing spans, temporarily overriding a config, acquiring a distributed lock.

---

### Q23. `contextlib` essentials: `@contextmanager`, `suppress`, `ExitStack`.
`[MEDIUM]`

**Answer:** `@contextmanager` turns a generator with exactly one `yield` into a CM — code before `yield` is `__enter__`, after is `__exit__`. Wrap the `yield` in `try/finally` or cleanup is skipped on exceptions. `suppress(Exc)` is a clean `try/except/pass`. `ExitStack` manages a **dynamic** number of context managers.

**Code:**

```python
from contextlib import contextmanager, suppress, ExitStack
from collections.abc import Iterator

import os

@contextmanager
def temporary_env(**kv: str) -> Iterator[None]:
    old = {k: os.environ.get(k) for k in kv}     # None means "was not set"
    os.environ.update(kv)
    try:
        yield
    finally:                                     # MUST be finally
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)          # remove what we added
            else:
                os.environ[k] = v                # restore the old value

with suppress(FileNotFoundError):
    open("optional_config.yaml")

def open_all(paths: list[str]) -> None:
    with ExitStack() as stack:                   # N files, all closed correctly
        files = [stack.enter_context(open(p)) for p in paths]
        ...
```

**Gotcha:** With `@contextmanager`, an exception in the body is *raised at the `yield` statement*. If you want to observe it, use `try/except/raise` around the yield; a bare `except: pass` there silently swallows every error in the body.

**Follow-up they will ask:** *"`contextlib.nullcontext`?"* → placeholder CM for conditional usage: `cm = span() if tracing else nullcontext()`.

---

### Q24. Async context managers + FastAPI lifespan.
`[MEDIUM]`

**Answer:** `__aenter__`/`__aexit__` with `async with`; `@asynccontextmanager` for the generator form; `AsyncExitStack` for dynamic sets. The canonical production use is FastAPI's `lifespan` — build shared clients (LLM, vector DB, HTTP pool) once at startup and close them at shutdown, instead of per request.

**Code:**

```python
from contextlib import asynccontextmanager, AsyncExitStack
from collections.abc import AsyncIterator
from fastapi import FastAPI
from openai import AsyncOpenAI
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        app.state.llm = AsyncOpenAI(max_retries=3, timeout=30.0)
        app.state.http = await stack.enter_async_context(
            httpx.AsyncClient(timeout=10.0, limits=httpx.Limits(max_connections=100))
        )
        stack.push_async_callback(app.state.llm.close)
        yield                                # app serves requests here
    # everything unwound in reverse order on shutdown

app = FastAPI(lifespan=lifespan)
```

**Gotcha:** Creating an `AsyncOpenAI`/`httpx.AsyncClient` **inside each request handler** is the #1 latency bug in LLM services — you pay a fresh TCP + TLS handshake on every call (order of tens to a couple of hundred milliseconds, depending on region and TLS version) and you exhaust sockets under load. One client per process, shared.

**Follow-up they will ask:** *"`@app.on_event('startup')`?"* → deprecated; `lifespan` is the current API.

---

## 5. GIL & Concurrency Model

### Q25. What exactly is the GIL? What does it protect?
`[MEDIUM]`

**Answer:** The Global Interpreter Lock is a single mutex in CPython that lets **only one thread execute Python bytecode at a time**. It exists to make reference counting thread-safe cheaply. Consequences: pure-Python CPU work does not scale across threads in one process; **I/O and most C extensions release the GIL**, so threads *do* help for network/disk-bound work (which is exactly what an LLM app is).

Mechanics worth naming: the interpreter switches threads every `sys.getswitchinterval()` (default **5 ms**), or when a thread blocks on I/O / enters a C call that releases it (`Py_BEGIN_ALLOW_THREADS`). NumPy, `hashlib`, compression, and network sockets all release it.

**Gotcha:** The GIL does **not** make your code thread-safe. `counter += 1` is load/add/store — three bytecodes — and a switch can land in the middle. You still need `threading.Lock`. (List `.append()` happens to be atomic, but do not rely on that as a design.)

**Follow-up they will ask:** *"Do other Pythons have it?"* → Jython and IronPython don't; PyPy does; CPython 3.13+ has an optional free-threaded build (next question).

---

### Q26. What changed with free-threaded Python (PEP 703, 3.13/3.14)?
`[HARD]`

**Answer:** PEP 703 added an **optional build of CPython without the GIL** — free-threaded, shipped as `python3.13t` (experimental in 3.13, built with `--disable-gil`). In **3.14 it moved to officially supported** (PEP 779) but it is still a **separate build, not the default**. In free-threaded builds, real parallelism across threads is possible for pure-Python CPU work; ref-counting uses biased/deferred counting and objects/containers get internal locking.

| | Default build | Free-threaded build (`t`) |
|---|---|---|
| GIL | on | off |
| CPU-bound threads scale | no | yes |
| Single-thread overhead | baseline | reported ~5–10% in 3.14, down from ~20–40% in 3.13 (approximate — quote as "single-digit percent now, was large") |
| C extension support | universal | needs `Py_mod_gil` / recompiled wheels |
| Status | default, stable | supported but opt-in |

**Code:**

```python
import sys, sysconfig
print(sysconfig.get_config_var("Py_GIL_DISABLED"))  # 1 on a free-threaded build
print(sys._is_gil_enabled())                        # 3.13+: runtime check
# PYTHON_GIL=0 / PYTHON_GIL=1 env var can force it at startup on 't' builds
```

**Gotcha:** Do not claim "the GIL is gone in 3.13" — that's a red flag. Say: *"optional build, experimental in 3.13, officially supported in 3.14, not the default, and the ecosystem (C extensions) is still catching up."* Also mention the sibling track: **PEP 734 subinterpreters** (`concurrent.interpreters` module in 3.14, plus `concurrent.futures.InterpreterPoolExecutor`) give per-interpreter GILs — another route to in-process parallelism.

**Follow-up they will ask:** *"Would you use it for your LLM service?"* → No. LLM services are I/O-bound; asyncio already solves it. Free-threading matters for CPU-heavy local work (tokenising, re-ranking, parsing) where you'd otherwise pay multiprocessing IPC costs.

---

### Q27. threading vs multiprocessing vs asyncio — give me the decision matrix.
`[MEDIUM]`

**Answer:** **I/O-bound + high concurrency → asyncio. I/O-bound + blocking libraries you can't change → threads. CPU-bound → processes (or a C/Rust/NumPy path).** For an LLM/agent service the answer is almost always asyncio, with `asyncio.to_thread` as the escape hatch for blocking SDKs.

| Dimension | asyncio | threading | multiprocessing |
|---|---|---|---|
| Best for | network I/O, 1000s of concurrent LLM/HTTP calls | blocking I/O in legacy libs | CPU-bound (parsing, tokenising, image work) |
| Parallel CPU | no (one thread by design) | no (GIL; yes only on a free-threaded build) | yes |
| Cost per unit | ~KBs per task | ~8 MB *virtual* stack (RSS far smaller), OS switch on the order of µs | order of tens of ms to spawn a fresh interpreter |
| Data sharing | same memory, single thread → few races | same memory, needs locks | pickle / shared memory / queues |
| Failure mode | one blocking call stalls everything | deadlocks, races | pickling errors, zombie children |
| Sweet spot in AI apps | fan-out to OpenAI/Azure, vector DB, tools | `boto3`, old DB drivers | chunking a 5 GB corpus, local embeddings |

**Gotcha:** Concurrency ≠ parallelism. asyncio gives concurrency on one thread; only processes (or a free-threaded build) give CPU parallelism. Say this sentence — interviewers listen for it.

**Follow-up they will ask:** *"How many concurrent OpenAI calls?"* → not unlimited: bounded by your rate limit (RPM/TPM), so a `Semaphore` sized to the limit (e.g. 10–50) plus retry-on-429, not `gather` over 5000 coroutines.

---

### Q28. Your agent service is slow. It's 90% waiting on LLM calls. Does the GIL matter?
`[MEDIUM]`

**Answer:** Barely. Waiting on a socket releases the GIL, so the bottleneck is network latency and provider rate limits, not the interpreter. The real fixes, in order: (1) make calls concurrent (`TaskGroup`/`gather` with a semaphore), (2) reuse one HTTP client (connection pooling), (3) stream so time-to-first-token replaces time-to-full-response, (4) cache (exact-match + semantic) and use prompt caching, (5) shrink prompts/context, (6) route easy requests to a smaller model, (7) run multiple uvicorn workers (`--workers N`, one process per core) for CPU-side headroom.

**Gotcha:** A single blocking call inside an async handler (`time.sleep`, `requests.get`, a sync SDK, a heavy `json.loads` of a 50 MB payload) stalls the **entire event loop** for every user. That's the most common production incident in async LLM services.

**Follow-up they will ask:** *"How would you prove where the time goes?"* → per-stage timing spans (Q22), `py-spy top --pid`, and p50/p95/p99 latency histograms, not averages.

---

### Q29. Multiprocessing details: pickling, start methods, and what changed recently.
`[HARD]`

**Answer:** Child processes need arguments and return values to be **picklable** — lambdas, local functions, open sockets, and DB connections are not. Start methods: `fork` (fast, Linux only, unsafe with threads), `spawn` (fresh interpreter, default on macOS/Windows, safe, slow), `forkserver` (fork from a clean helper process). **Python 3.14 changed the Linux default from `fork` to `forkserver`**, because forking a multi-threaded process (which any app with an HTTP client already is) can deadlock.

**Code:**

```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def tokenize(text: str) -> int:            # top-level => picklable
    return len(text.split())

if __name__ == "__main__":                 # REQUIRED for spawn/forkserver
    ctx = mp.get_context("forkserver")      # prefer an explicit context over
    docs = ["a b", "c d e"] * 500_000       # set_start_method(force=True)
    with ProcessPoolExecutor(max_workers=4, mp_context=ctx) as ex:
        # chunksize amortises IPC: 1M tiny items with chunksize=1 is all overhead
        totals = list(ex.map(tokenize, docs, chunksize=1000))
```

**Gotcha:** Without the `if __name__ == "__main__":` guard, `spawn`/`forkserver` re-import your module in the child and re-run the pool creation → infinite process explosion. And `chunksize` matters: with `ex.map` over a million tiny items, per-item IPC dominates; batch them.

**Follow-up they will ask:** *"Sharing a big embedding matrix with workers?"* → `multiprocessing.shared_memory` or memory-mapped NumPy (`np.load(mmap_mode="r")`), not pickling a 4 GB array per worker.

---

## 6. Asyncio Deep Dive

### Q30. Explain the event loop. Coroutine vs Task vs Future.
`[MEDIUM]`

**Answer:** The event loop is a single-threaded scheduler running a ready-queue plus an OS selector (`epoll`/`kqueue`). **Coroutine** = the object returned by calling an `async def` function; inert until awaited. **Task** = a coroutine *scheduled* on the loop (`asyncio.create_task`), runs concurrently. **Future** = a low-level placeholder for a result someone else will set; `Task` is a subclass of `Future`.

`await` means "suspend me and give control back to the loop until this completes". Between awaits your code runs uninterrupted — that's why asyncio needs far fewer locks than threading. **But not zero:** any invariant that must hold *across* an `await` (read-modify-write on shared state, a token-bucket refill, a lazily-built client) still needs an `asyncio.Lock`, because the loop can run another task at that suspension point. The difference from threading is that the interleaving points are visible in the source — they are exactly the `await`s.

**Code:**

```python
import asyncio

async def work(n: int) -> int:
    await asyncio.sleep(1)
    return n * 2

async def main() -> None:
    coro = work(1)                  # nothing running yet
    t = asyncio.create_task(work(2))# scheduled NOW, runs concurrently
    print(await coro, await t)      # ~1s total, not 2s

asyncio.run(main())                 # creates loop, runs, closes, shuts down asyncgens
```

**Gotcha:** Calling an async function without awaiting gives `RuntimeWarning: coroutine ... was never awaited` and it never runs. In an agent loop that silently means "the tool was never called".

**Follow-up they will ask:** *"`asyncio.run` twice / inside a running loop?"* → `RuntimeError: asyncio.run() cannot be called from a running event loop`. Use `await` directly, or `nest_asyncio` only in notebooks (never in prod).

---

### Q31. `gather` vs `as_completed` vs `TaskGroup` — when do you use each?
`[HARD]`

**Answer:** **`TaskGroup` (3.11+) is the default choice**: structured concurrency, and if one child fails the rest are cancelled and errors surface as an `ExceptionGroup`. **`gather`** when you want all results in input order and `return_exceptions=True` to tolerate partial failure. **`as_completed`** when you want to process results *as they arrive* (e.g. stream the first agent that answers).

| | Result order | On child failure | Cancels siblings | Version |
|---|---|---|---|---|
| `gather(*aws)` | input order | first exception propagates, siblings keep running | no | all |
| `gather(..., return_exceptions=True)` | input order | exceptions returned as values | no | all |
| `as_completed(aws)` | completion order | raises when you await that one | no | all |
| `TaskGroup` | via `task.result()` | `ExceptionGroup`, siblings cancelled | yes | 3.11+ |

**Code:**

```python
import asyncio

# 1) TaskGroup — fan out to 3 specialist agents, all-or-nothing
async def run_agents(q: str) -> dict[str, str]:
    async with asyncio.TaskGroup() as tg:
        tasks = {name: tg.create_task(agent(name, q))
                 for name in ("researcher", "coder", "critic")}
    return {n: t.result() for n, t in tasks.items()}

# 2) gather with tolerance — partial results are fine
async def enrich(ids: list[str]) -> list[str | BaseException]:
    return await asyncio.gather(*(fetch(i) for i in ids), return_exceptions=True)

# 3) as_completed — first useful answer wins
async def first_good(qs: list[str]) -> str:
    tasks = [asyncio.create_task(agent("x", q)) for q in qs]
    try:
        for fut in asyncio.as_completed(tasks):
            res = await fut
            if res:
                return res
    finally:
        for t in tasks:
            t.cancel()                   # ALWAYS clean up the losers
        # and await them, or you get "Task exception was never retrieved"
        await asyncio.gather(*tasks, return_exceptions=True)
    return ""
```

**Gotcha:** With plain `gather` and no `return_exceptions`, the first exception propagates but **the other tasks keep running in the background** — a classic leak (and duplicate LLM spend). `TaskGroup` fixes exactly this. Note also 3.13 improved `as_completed` so it can be used with `async for` and yields the original task objects.

**Follow-up they will ask:** *"How do you catch errors from a TaskGroup?"* → `except* SomeError as eg:` (Q52).

---

### Q32. Fan out 500 documents to an LLM without hitting rate limits. Write it.
`[MEDIUM]`

**Answer:** Bound concurrency with `asyncio.Semaphore` sized to your provider limit, one shared async client, per-request timeout, retry on 429/timeouts, and `TaskGroup` for structure. This is *the* question for this JD — practise writing it from memory.

**Code:**

```python
import asyncio, logging, random
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError

log = logging.getLogger(__name__)
client = AsyncOpenAI(max_retries=0, timeout=30.0)   # we own the retry policy
MAX_CONCURRENCY = 16
sem = asyncio.Semaphore(MAX_CONCURRENCY)

async def summarize(doc: str, *, attempts: int = 4) -> str | None:
    for attempt in range(attempts):
        try:
            async with sem:                          # hold ONLY around the call
                resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Summarize in 2 lines."},
                              {"role": "user", "content": doc}],
                    max_tokens=200,
                )
            return resp.choices[0].message.content
        except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
            if attempt == attempts - 1:
                log.error("giving up: %s", exc)
                return None
            backoff = min(2 ** attempt, 30) * (0.5 + 0.5 * random.random())   # jitter
            await asyncio.sleep(backoff)
    return None

async def summarize_all(docs: list[str]) -> list[str | None]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(summarize(d)) for d in docs]
    return [t.result() for t in tasks]
```

**Gotcha:** Creating 500 tasks is fine (each is a few KB) — the semaphore is what protects the provider. Do **not** put the semaphore around the retry loop, or a sleeping retry holds a slot. And `await asyncio.sleep()` for backoff, never `time.sleep()` (blocks the loop).

**Follow-up they will ask:** *"Semaphore vs token-bucket?"* → Semaphore bounds *concurrent requests* (RPM proxy). If the provider limits **tokens per minute (TPM)**, you need a token-bucket that accounts for estimated prompt+completion tokens, because 16 concurrent 100k-token requests will still 429.

---

### Q33. Timeouts and cancellation in asyncio. How does cancellation actually work?
`[HARD]`

**Answer:** Cancellation is cooperative: `task.cancel()` schedules `CancelledError` to be raised **at the task's next await point**. Since 3.8 `CancelledError` inherits from `BaseException`, so `except Exception` does not swallow it. Use `asyncio.timeout()` (3.11+, context-manager form, composable) over the older `wait_for`. Use `asyncio.shield()` to protect a critical section from outer cancellation.

**Code:**

```python
import asyncio

async def with_budget(prompt: str) -> str:
    try:
        async with asyncio.timeout(10):            # 3.11+; timeout_at() also exists
            return await call_llm(prompt)
    except TimeoutError:                            # 3.11+: asyncio.TimeoutError is TimeoutError
        return "(timed out — degraded answer)"

async def cleanup_safe() -> None:
    try:
        await long_running()
    except asyncio.CancelledError:
        await flush_metrics()                       # do cleanup...
        raise                                       # ...then ALWAYS re-raise
```

**Gotcha:** Three rules: (1) never write `except Exception` around cancellation-sensitive code expecting to catch cancellation — it won't; (2) if you catch `CancelledError`, **re-raise it**, otherwise the task looks like it completed and `TaskGroup`/`gather` semantics break; (3) a long CPU-bound block has no await points, so it is **uncancellable** — the timeout fires only after it finishes.

**Follow-up they will ask:** *"Client disconnects mid-stream in FastAPI — what happens?"* → the request task is cancelled; your `finally`/`aclosing` must close the upstream LLM stream, otherwise you keep paying for generated tokens nobody reads.

---

### Q34. A blocking call must run inside an async handler. What do you do?
`[MEDIUM]`

**Answer:** Push it to a thread with `await asyncio.to_thread(fn, *args)` (3.9+), or `loop.run_in_executor(pool, fn)` for a custom/bounded pool, or a `ProcessPoolExecutor` if it's CPU-bound. Never call it directly.

**Code:**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# blocking SDK (e.g. an old vector DB driver or boto3)
def sync_search(q: str) -> list[str]: ...

async def search(q: str) -> list[str]:
    return await asyncio.to_thread(sync_search, q)

# bounded pool + CPU-bound work
CPU = ProcessPoolExecutor(max_workers=4)
async def rerank(pairs: list[tuple[str, str]]) -> list[float]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(CPU, expensive_rerank, pairs)
```

**Gotcha:** The default executor used by `to_thread` is shared and bounded (`min(32, cpu_count + 4)` threads); flooding it with 500 blocking calls serialises them and can starve other `to_thread` users. For heavy use, create your own `ThreadPoolExecutor` with an explicit size. Detect accidental blocking in dev with `asyncio.run(..., debug=True)` or `PYTHONASYNCIODEBUG=1` — it logs callbacks slower than 100 ms.

**Follow-up they will ask:** *"Is the openai SDK async-safe?"* → yes, use `AsyncOpenAI`; the sync `OpenAI` client inside an async handler is exactly the blocking mistake above.

---

### Q35. How do you bridge sync and async code safely?
`[HARD]`

**Answer:** Sync → async: `asyncio.run(coro())` at the top level only (it creates and closes a loop). From a **different thread** while a loop is running: `asyncio.run_coroutine_threadsafe(coro, loop)` which returns a `concurrent.futures.Future`. Async → sync: `asyncio.to_thread`. Never call `asyncio.run` inside a running loop, and never `future.result()` on the loop's own thread (instant deadlock).

**Code:**

```python
import asyncio, threading

def start_background_loop() -> tuple[asyncio.AbstractEventLoop, threading.Thread]:
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=loop.run_forever, daemon=True)
    t.start()
    return loop, t

loop, thread = start_background_loop()

def call_from_sync_world(prompt: str, timeout: float = 30) -> str:
    fut = asyncio.run_coroutine_threadsafe(call_llm(prompt), loop)
    return fut.result(timeout=timeout)      # blocks THIS (non-loop) thread only
```

**Gotcha:** In Jupyter a loop is already running, which is why `asyncio.run` fails there — use `await` directly in a cell. `nest_asyncio` patches this for notebooks; treat it as a dev-only hack (LangChain/LlamaIndex users hit this constantly).

**Follow-up they will ask:** `asyncio.Runner` (3.11+) if you need to run several coroutines against the same loop with `with asyncio.Runner() as r: r.run(main())`.

---

### Q36. Design a bounded async worker pool with backpressure.
`[HARD]`

**Answer:** Producer puts work on an `asyncio.Queue(maxsize=N)`; N fixed workers consume. The bounded queue *is* the backpressure — the producer blocks on `put()` when consumers fall behind, instead of building an unbounded backlog and OOMing. Shut down cleanly with `queue.join()` + cancelling workers, or sentinel values.

**Code:**

```python
import asyncio
from collections.abc import Iterable

async def worker(name: str, q: asyncio.Queue[str], out: list[str]) -> None:
    while True:
        doc = await q.get()
        try:
            out.append(await summarize(doc))
        except Exception:                       # one bad doc must not kill the worker
            out.append("")
        finally:
            q.task_done()

async def pipeline(docs: Iterable[str], workers: int = 8, depth: int = 32) -> list[str]:
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=depth)
    out: list[str] = []
    ws = [asyncio.create_task(worker(f"w{i}", q, out)) for i in range(workers)]
    for d in docs:
        await q.put(d)                          # blocks when queue is full -> backpressure
    await q.join()                              # wait until all task_done()
    for w in ws:
        w.cancel()
    await asyncio.gather(*ws, return_exceptions=True)
    return out
```

**Gotcha:** If a worker raises before `task_done()`, `q.join()` hangs forever — always `task_done()` in `finally`. Unbounded `Queue()` (maxsize=0) removes backpressure and just moves the OOM later.

**Follow-up they will ask:** *"Queue vs Semaphore?"* → Semaphore bounds concurrency for a known, finite set of coroutines; Queue bounds *memory* for a stream of unknown length and lets you decouple producer and consumer rates.

---

### Q37. Name the asyncio bugs you've actually hit in production.
`[MEDIUM]`

**Answer:** Five, with fixes:

1. **Fire-and-forget task garbage collected mid-flight.** `asyncio.create_task(x())` without keeping a reference — the loop only holds a weak reference, so the task can be GC'd. Fix: keep a strong ref (`self._tasks.add(t); t.add_done_callback(self._tasks.discard)`) or use `TaskGroup`.
2. **Swallowed exceptions in background tasks** → "Task exception was never retrieved" at shutdown. Fix: `TaskGroup`, or `add_done_callback` that logs.
3. **Blocking the loop** (`requests`, `time.sleep`, sync SDK, huge `json.loads`). Fix: `to_thread`, plus `debug=True` in dev.
4. **Sharing an `httpx.AsyncClient` across event loops** (e.g. created at import time, used from a different loop) → `RuntimeError: Event loop is closed`. Fix: create clients inside `lifespan`.
5. **No timeout anywhere.** A hung LLM connection holds a task forever. Fix: per-request `timeout=` plus `asyncio.timeout()` on the whole operation.

**Gotcha:** `asyncio.sleep(0)` is the idiom to yield control to the loop once — useful in a tight loop that would otherwise starve other tasks.

**Follow-up they will ask:** *"How do you observe a stuck loop?"* → `py-spy dump --pid <pid>` shows every task's stack; `asyncio.all_tasks()` + `task.get_stack()` programmatically.

---

## 7. Memory, GC, Copy Semantics

### Q38. How does CPython manage memory? Reference counting + generational GC.
`[MEDIUM]`

**Answer:** Primary mechanism is **reference counting** — every object has a counter; at zero it is freed immediately (deterministic). Because refcounting can't free **reference cycles**, CPython adds a **generational cyclic garbage collector** with 3 generations: new objects start in gen 0, survivors are promoted. Gen 0 is collected often (default threshold 700 allocations-minus-deallocations), gen 1 and gen 2 progressively less (`gc.get_threshold()` → `(700, 10, 10)`).

**Code:**

```python
import gc, sys

class Node: pass
a, b = Node(), Node()
a.peer, b.peer = b, a               # cycle
print(sys.getrefcount(a))           # note: +1 for the temporary arg reference
del a, b
print(gc.collect())                 # returns number of unreachable objects collected

gc.get_threshold()                  # (700, 10, 10)
gc.freeze()                         # move current objects out of GC scope (post-fork trick)
```

**Gotcha:** Small integers (−5..256) and interned strings are cached/immortal, so their refcounts are meaningless. Since 3.12 (PEP 683) common singletons like `None`, `True`, small ints are **immortal** — their refcount never changes, which also helps free-threading.

**Follow-up they will ask:** *"Would you ever disable the GC?"* → `gc.disable()` + `gc.freeze()` before forking workers is a known latency trick (avoids copy-on-write page churn), but only if you're sure you create no cycles, and you should still `gc.collect()` periodically.

---

### Q39. What is a reference cycle? How do you find and fix one? What is `weakref` for?
`[HARD]`

**Answer:** A cycle is objects referencing each other so no refcount reaches zero (parent↔child, a cache holding objects that hold the cache, a closure capturing `self`, an exception traceback holding frames holding the exception). The cyclic GC eventually collects them, but memory is held longer and it costs CPU. Fix by breaking the cycle with **`weakref`** — a reference that does not increment the refcount.

**Code:**

```python
import weakref, gc

class Session:
    def __init__(self, sid: str) -> None:
        self.sid = sid
        self.agents: list["Agent"] = []

class Agent:
    def __init__(self, session: Session) -> None:
        self._session = weakref.ref(session)     # no strong ref back -> no cycle
        session.agents.append(self)
    @property
    def session(self) -> Session | None:
        return self._session()                   # None once the session is gone

# Cache that doesn't keep entries alive by itself:
cache: "weakref.WeakValueDictionary[str, Session]" = weakref.WeakValueDictionary()

gc.set_debug(gc.DEBUG_SAVEALL)                   # debug only: ALL unreachable objects
                                                 # are kept in gc.garbage instead of freed
                                                 # (gc.DEBUG_LEAK = SAVEALL + stats)
```

**Gotcha:** In long-running agent processes the classic leak is **conversation history in a module-level dict keyed by session id, never evicted**. That's not a GC problem — it's a live reference. Fix with TTL eviction / `cachetools.TTLCache` / Redis, not `weakref`. Also: `weakref` doesn't work on `int`, `str`, `tuple`, or on slotted classes without `__weakref__` in `__slots__`.

**Follow-up they will ask:** *"Does `__del__` prevent collection?"* → Not since 3.4 (PEP 442); objects with `__del__` in cycles are now collectable. Still avoid `__del__` — use context managers or `weakref.finalize`.

---

### Q40. Your agent service RSS grows 200 MB/hour. Debug it.
`[MEDIUM]`

**Answer:** Method: (1) confirm with RSS over time (`psutil`), (2) `tracemalloc` snapshots N minutes apart and `compare_to(..., 'lineno')` to get the top growing allocation sites, (3) `gc.get_objects()` counts by type to spot the runaway class, (4) `py-spy dump` / `objgraph.show_backrefs` to find who holds the references. Usual culprits: unbounded caches/history dicts, an ever-growing list of `Task` objects, logging handlers buffering, or a leaked HTTP client per request.

**Code:**

```python
import tracemalloc, collections, gc

tracemalloc.start(25)                         # keep 25 frames of traceback
snap1 = tracemalloc.take_snapshot()
...                                           # run traffic for a while
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:10]:
    print(stat)                               # +12.4 MiB  app/rag.py:88

print(collections.Counter(type(o).__name__ for o in gc.get_objects()).most_common(10))
```

**Gotcha:** `sys.getsizeof()` is **shallow** — `sys.getsizeof([obj]*1000)` reports the list's own array of pointers (~8 KB), not the 1000 objects. Use `tracemalloc`, `pympler.asizeof`, or measure process RSS.

**Follow-up they will ask:** *"Memory fragmentation?"* → CPython's pymalloc holds freed arenas; RSS may not return to the OS even after objects are freed. Compare `tracemalloc` (Python-level) against RSS to tell a real leak from fragmentation/allocator retention.

---

### Q41. Shallow vs deep copy. Where does it bite in an agent?
`[EASY]`

**Answer:** Assignment copies a **reference**; `copy.copy()` makes a new outer object sharing inner references; `copy.deepcopy()` recursively copies everything (and tracks a memo dict so cycles work). It bites when an agent node mutates the shared state dict and every other node sees the change.

**Code:**

```python
import copy

state = {"messages": [{"role": "user", "content": "hi"}], "scratch": {}}

shallow = copy.copy(state)
shallow["messages"].append({"role": "assistant", "content": "yo"})
len(state["messages"])            # 2  <- leaked into the original!

deep = copy.deepcopy(state)
deep["messages"].append({"role": "assistant", "content": "yo"})
len(state["messages"])            # unchanged

# 3.13+: copy.replace(obj, **changes) works on dataclasses, namedtuples, datetime...
from dataclasses import dataclass, replace
@dataclass(frozen=True)
class Cfg: model: str; temperature: float
c2 = replace(Cfg("gpt-4o", 0.7), temperature=0.0)     # dataclasses.replace, all versions
```

**Gotcha:** `deepcopy` is slow and will explode on unpicklable/unclonable members (open sockets, an `AsyncOpenAI` client, a DB connection, a thread lock). For agent state prefer **immutable updates** — frozen dataclasses / pydantic `model_copy(update=...)` / LangGraph reducer functions — over deep-copying a mutable blob.

**Follow-up they will ask:** *"How do you customise it?"* → implement `__copy__` and `__deepcopy__(self, memo)`.

---

### Q42. `is` vs `==`, interning, and the mutable-default-in-a-loop gotcha in one.
`[EASY]`

**Answer:** `is` compares identity (same object), `==` compares value (`__eq__`). Use `is` only for singletons: `None`, `True`, `False`, sentinels. CPython caches small ints (−5..256) and interns some string literals, so `a is b` may *accidentally* be `True` — never rely on it.

**Code:**

```python
a = 256; b = 256; a is b        # True  (small-int cache, -5..256)
# 257 is NOT cached, but constants inside ONE code object are de-duplicated,
# so the answer depends on how the code is compiled:
a = 257; b = 257; a is b        # True  — one line == one code object, folded
# but typed as two separate REPL lines (two code objects) it is False:
#   >>> a = 257
#   >>> b = 257
#   >>> a is b        # False
x = "hello"; y = "hello"; x is y  # True (compile-time interning) — do not rely on it

if value is None: ...           # correct
if value == None: ...           # wrong style, and breaks for numpy arrays
```

**Gotcha:** For NumPy arrays and pandas objects, `==` returns an array, so `if arr == None:` raises `ValueError: truth value of an array is ambiguous`. `is None` is the only safe form.

**Follow-up they will ask:** *"3.8+ `SyntaxWarning: is with a literal`"* → Python now warns you at compile time for `x is "str"` / `x is 5`.

---

## 8. Typing, Pydantic v2, Data Modelling

### Q43. Explain `TypeVar` and `Generic`. Show the 3.12 syntax.
`[MEDIUM]`

**Answer:** `TypeVar` is a type placeholder; `Generic[T]` makes a class parametric so the checker can relate input and output types. **PEP 695 (3.12+)** adds native syntax — `class Box[T]:` / `def first[T](xs: list[T]) -> T:` — with no imports and no explicit `TypeVar`.

**Code:**

```python
# 3.12+ native syntax
class Result[T]:
    def __init__(self, value: T | None, error: str | None = None) -> None:
        self.value, self.error = value, error
    def unwrap(self) -> T:
        if self.error is not None:
            raise RuntimeError(self.error)
        assert self.value is not None
        return self.value

def first[T](xs: list[T]) -> T: return xs[0]

# Pre-3.12 equivalent (still what most codebases look like)
from typing import Generic, TypeVar
T = TypeVar("T")
class ResultOld(Generic[T]): ...

# bounded / constrained
def norm[N: (int, float)](x: N) -> N: return abs(x)     # constrained
def get_id[M: "BaseModel"](m: M) -> str: return m.id    # bound
```

**Gotcha:** Type hints are **not enforced at runtime** by Python itself — they're metadata in `__annotations__`. Enforcement comes from mypy/pyright at CI time or from pydantic at runtime. Say that explicitly; interviewers test for it.

**Follow-up they will ask:** *"Variance?"* → `TypeVar("T", covariant=True)` for read-only producers, `contravariant=True` for consumers; `list[Dog]` is *not* a `list[Animal]` because lists are mutable (invariant), while `Sequence[Dog]` is a `Sequence[Animal]`.

---

### Q44. What is a `Protocol` and why is it better than an ABC here?
`[MEDIUM]`

**Answer:** `Protocol` gives **structural typing** ("static duck typing") — a class satisfies it by having the right methods, with no inheritance and no import coupling. Perfect for pluggable AI infrastructure: your code depends on a `VectorStore` shape, and Pinecone/Qdrant/pgvector adapters satisfy it without importing your base class.

**Code:**

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, ids: list[str], vectors: list[list[float]],
               metadata: list[dict]) -> None: ...
    def query(self, vector: list[float], k: int = 5,
              filters: dict | None = None) -> list[tuple[str, float]]: ...

class QdrantStore:                       # no inheritance needed
    def upsert(self, ids, vectors, metadata) -> None: ...
    def query(self, vector, k=5, filters=None): return []

def build_rag(store: VectorStore) -> None: ...
build_rag(QdrantStore())                 # type checks
isinstance(QdrantStore(), VectorStore)   # True — but only checks method NAMES
```

| | `Protocol` | `ABC` |
|---|---|---|
| Coupling | none (structural) | must inherit (nominal) |
| Third-party classes | works | needs `register()` or a wrapper |
| Enforcement | static (mypy/pyright) | runtime `TypeError` on instantiation |
| Shared impl | no (only defaults) | yes (concrete methods) |

**Gotcha:** `@runtime_checkable` `isinstance()` checks **only that the attribute names exist** — it does not verify signatures or return types, and (until recently) not even that they're callable in every case. Don't treat it as validation.

**Follow-up they will ask:** *"When ABC then?"* → when you want to share implementation and force subclasses to override (`@abstractmethod`) inside your own codebase.

---

### Q45. What are `ParamSpec` and `Concatenate` for?
`[HARD]`

**Answer:** `ParamSpec` captures a callable's **entire parameter list** so a decorator can preserve the wrapped function's signature for the type checker (`Callable[..., R]` throws that away). `Concatenate` lets a decorator add or remove leading parameters.

**Code:**

```python
from collections.abc import Callable, Awaitable
from typing import Concatenate

# 3.12+ syntax; pre-3.12: P = ParamSpec("P"); R = TypeVar("R")
def with_client[**P, R](
    fn: Callable[Concatenate[object, P], Awaitable[R]]
) -> Callable[P, Awaitable[R]]:
    """Injects the shared LLM client as the first arg; callers no longer pass it."""
    async def wrapper(*a: P.args, **kw: P.kwargs) -> R:
        return await fn(get_client(), *a, **kw)
    return wrapper

@with_client
async def summarize(client: object, text: str, *, model: str = "gpt-4o-mini") -> str: ...

# inside an async def:
#   await summarize("hello", model="o4-mini")   # checker knows `client` is gone
```

**Gotcha:** `P.args` and `P.kwargs` must be used **together and only** as `*args: P.args, **kwargs: P.kwargs` — anything else is a type error. Without `ParamSpec`, every decorated function in your codebase degrades to `(*args: Any, **kwargs: Any) -> Any` and you lose all type safety at the decoration boundary.

**Follow-up they will ask:** *"`TypeVarTuple`?"* → PEP 646, variadic generics for shapes (`Array[Batch, Height, Width]`) — mostly used in ML array typing.

---

### Q46. `Literal`, `TypedDict`, `NotRequired`, `@overload` — show them on an LLM API.
`[MEDIUM]`

**Answer:** `Literal` restricts to exact values (model names, roles). `TypedDict` types a dict's keys — ideal for OpenAI message payloads you must keep as dicts. `NotRequired`/`Required` (3.11+) mark optional keys. `@overload` declares several signatures so the return type depends on the arguments.

**Code:**

```python
from collections.abc import Iterator
from typing import Literal, TypedDict, NotRequired, overload   # NotRequired: 3.11+
                                                               # (typing_extensions before)

Role = Literal["system", "user", "assistant", "tool"]

class Message(TypedDict):
    role: Role
    content: str
    name: NotRequired[str]                     # 3.11+
    tool_call_id: NotRequired[str]

msgs: list[Message] = [{"role": "system", "content": "You are terse."}]

@overload
def generate(p: str, *, stream: Literal[False] = False) -> str: ...
@overload
def generate(p: str, *, stream: Literal[True]) -> Iterator[str]: ...
def generate(p: str, *, stream: bool = False):      # single implementation
    return _stream(p) if stream else _once(p)

reveal = generate("hi")                 # checker: str
gen = generate("hi", stream=True)       # checker: Iterator[str]
```

**Gotcha:** `@overload` stubs have **no runtime effect** — only the final non-decorated implementation runs, and their bodies must be `...`. Also `TypedDict` is not validated at runtime; if you need actual validation use pydantic (or `TypeAdapter(Message).validate_python(...)`).

**Follow-up they will ask:** *"Exhaustiveness on a Literal?"* → `assert_never(x)` in the final `else` branch makes mypy error if you add a new literal and forget a branch.

---

### Q47. Pydantic v2: what changed from v1, and why is it faster?
`[MEDIUM]`

**Answer:** v2 moved validation into **`pydantic-core`, a compiled Rust engine** — it builds a validation "schema tree" once per model at class creation and executes it in Rust. Pydantic's own benchmarks report **roughly an order of magnitude faster validation** than v1's pure-Python path (they quote "4–50×" depending on the model; don't quote a single number as fact). API renames matter for interviews:

| v1 | v2 |
|---|---|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `parse_raw()` | `model_validate_json()` |
| `.copy()` | `.model_copy()` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `.schema()` | `.model_json_schema()` |
| `Optional[x]` implied optional | must write `x: int | None = None` explicitly |

**Code:**

```python
from pydantic import BaseModel, ConfigDict, Field, computed_field

class RetrievedChunk(BaseModel):
    # frozen=True and validate_assignment=True are mutually exclusive in practice:
    # frozen makes any assignment raise, so validation-on-assignment never fires.
    # Pick one — frozen for immutable value objects, validate_assignment for
    # mutable models you keep editing after construction.
    model_config = ConfigDict(extra="forbid", frozen=True,
                              str_strip_whitespace=True)
    doc_id: str = Field(min_length=1)
    text: str
    score: float = Field(ge=0.0, le=1.0)
    tokens: int = Field(default=0, ge=0)

    @computed_field
    @property
    def preview(self) -> str:
        return self.text[:80]

c = RetrievedChunk.model_validate({"doc_id": "d1", "text": " hi ", "score": 0.9})
c.model_dump(exclude={"tokens"}, mode="json")
```

**Gotcha:** In v2, a field declared `x: int | None` with **no default is still required** (you must pass `None` explicitly). This breaks a lot of v1 code silently. Also `extra="forbid"` is worth defaulting on for LLM-facing schemas — it catches hallucinated extra keys instead of ignoring them.

**Follow-up they will ask:** *"v1 compatibility?"* → `pydantic.v1` namespace shipped inside pydantic 2 for gradual migration; `bump-pydantic` automates most renames.

---

### Q48. Pydantic v2 validators: `field_validator` vs `model_validator`, `mode="before"` vs `"after"`.
`[MEDIUM]`

**Answer:** `field_validator` runs per field; `model_validator` runs across the whole model (cross-field rules). `mode="before"` sees the **raw input** (coerce/normalise messy LLM output there); `mode="after"` sees the **parsed, typed value/model** (business rules there, and it must return the value/`self`).

**Code:**

```python
from pydantic import BaseModel, field_validator, model_validator, ValidationError
from typing import Self          # 3.11+; before that: typing_extensions.Self

class AgentRequest(BaseModel):
    query: str
    top_k: int = 5
    model: str = "gpt-4o-mini"
    max_tokens: int = 512

    @field_validator("query", mode="before")
    @classmethod
    def coerce_query(cls, v: object) -> str:
        if isinstance(v, list):            # LLMs sometimes emit ["a","b"]
            return " ".join(map(str, v))
        return str(v).strip()

    @field_validator("top_k")
    @classmethod
    def sane_k(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError("top_k must be 1..50")
        return v

    @model_validator(mode="after")
    def budget(self) -> Self:              # cross-field rule
        if self.model.startswith("o") and self.max_tokens > 100_000:
            raise ValueError("max_tokens too high for reasoning models")
        return self

try:
    AgentRequest(query="hi", top_k=99)
except ValidationError as e:
    print(e.errors()[0]["msg"], e.errors()[0]["loc"])
```

**Gotcha:** `@field_validator` must be paired with `@classmethod` **below** it (order matters). Raise `ValueError`/`AssertionError` inside validators — pydantic converts them into a `ValidationError`; raising `ValidationError` directly is not supported for user code in v2. And `mode="after"` model validators are **instance** methods returning `self`, unlike v1's `root_validator` classmethods.

**Follow-up they will ask:** *"How do you repair invalid LLM JSON?"* → catch `ValidationError`, feed `e.errors()` back to the model as a repair prompt (one retry), then fail closed. That's a strong, concrete agentic answer.

---

### Q49. How do you get guaranteed-valid structured output from an LLM into a pydantic model?
`[HARD]`

**Answer:** Three layers, best first: (1) **provider-enforced structured output** — pass a JSON Schema with `strict: true` so the model *cannot* emit invalid JSON; (2) **function/tool calling** with the schema as parameters; (3) **prompt + parse + validate + repair-retry** as the portable fallback. In all cases the final gate is `Model.model_validate_json(...)`.

**Code:**

```python
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

client = OpenAI()

class Ticket(BaseModel):
    model_config = {"extra": "forbid"}          # strict schemas need additionalProperties:false
    summary: str
    severity: int = Field(ge=1, le=5)
    components: list[str]

# Portable form: hand the JSON Schema over explicitly
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Classify: prod RAG index returns stale docs"}],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "Ticket", "strict": True,
                        "schema": Ticket.model_json_schema()},
    },
)
msg = resp.choices[0].message
if msg.content is None:                          # refusal / tool call / truncation
    raise ValueError(f"no content, finish_reason={resp.choices[0].finish_reason}")
ticket = Ticket.model_validate_json(msg.content)

# SDK helper (preferred on current openai-python):
#   completion = client.chat.completions.parse(
#       model=..., messages=..., response_format=Ticket)
#   ticket = completion.choices[0].message.parsed        # already a Ticket
# Older 1.x releases only had it under client.beta.chat.completions.parse(...);
# both exist in recent versions, beta is the deprecated spelling.
```

**Gotcha:** OpenAI **strict** JSON schema requires **every** property to appear in `required`, and `additionalProperties: false` on every object; "optional" must be expressed as a nullable type (`str | None`), not by omitting the key. Pydantic's default `model_json_schema()` does *not* match that out of the box: it emits `additionalProperties: false` only when you set `extra="forbid"`, and it **omits any field that has a default from `required`** — which is exactly what strict mode rejects. So either give every field `| None` with no default plus `extra="forbid"`, or let the SDK's `parse()` helper normalise the schema for you. Also always guard for `finish_reason == "length"` — a truncated JSON body fails validation and looks like a model bug.

**Follow-up they will ask:** *"Validate a list of items without a wrapper model?"* → `TypeAdapter(list[Ticket]).validate_json(payload)` — no `BaseModel` wrapper needed, and it's the fast path for bulk validation.

---

### Q50. `dataclass` vs `pydantic` vs `NamedTuple` vs `TypedDict` vs `attrs` — choose.
`[MEDIUM]`

**Answer:** **Pydantic at trust boundaries** (HTTP request/response, LLM output, config from env/YAML) because it *validates and coerces*. **Dataclasses for internal, already-trusted state** (agent state, DTOs between your own functions) because they're stdlib and cheap. **NamedTuple** for small immutable positional records that must also behave like tuples. **TypedDict** when the data must stay a plain dict. **attrs** if you want dataclass-plus (validators, converters, `__slots__` by default) without pydantic's weight.

| | Validation | Mutable | Speed to construct | Stdlib | Use for |
|---|---|---|---|---|---|
| `dataclass` | none (hints only) | yes (`frozen=` opt) | fastest | yes | internal state |
| `pydantic.BaseModel` | full, coercing | yes (`frozen=` opt) | slower (Rust core, still ~µs) | no | API/LLM boundary |
| `NamedTuple` | none | no | fast | yes | tiny immutable records |
| `TypedDict` | none (static only) | yes | n/a (it *is* a dict) | yes | dict-shaped payloads |
| `attrs` | optional | yes | fast | no | rich internal models |

**Code:**

```python
from dataclasses import dataclass, field
from pydantic import BaseModel

@dataclass(slots=True, kw_only=True)          # slots/kw_only: 3.10+
class AgentState:                              # internal, trusted, hot path
    session_id: str
    messages: list[dict] = field(default_factory=list)
    step: int = 0

class ChatRequest(BaseModel):                  # boundary, untrusted
    session_id: str
    message: str
    temperature: float = 0.7
```

**Gotcha:** Don't put pydantic models in a hot inner loop that constructs millions of objects — validation is fast but not free (roughly single-digit microseconds per model). Validate once at the edge, then pass dataclasses inward. Conversely, never accept raw external JSON into a dataclass and assume the types are right.

**Follow-up they will ask:** *"FastAPI uses which?"* → pydantic, for request body, response_model, and OpenAPI schema generation — all from the same class.

---

## 9. Exceptions & Retry

### Q51. Design an exception hierarchy for an agent service.
`[EASY]`

**Answer:** One base app exception, then a branch per failure *category* the caller must handle differently: retryable vs terminal, user error vs provider error. Map them to HTTP codes at the API layer. Always chain with `raise ... from exc` so the original cause survives in the traceback.

**Code:**

```python
class AgentError(Exception):
    """Base for everything this service raises."""

class ConfigError(AgentError): ...              # startup / 500
class UserInputError(AgentError): ...           # -> HTTP 400
class GuardrailBlocked(UserInputError): ...     # -> HTTP 422
class RetryableError(AgentError): ...           # transient
class ProviderRateLimited(RetryableError): ...  # -> 429 upstream
class ProviderUnavailable(RetryableError): ...  # -> 502/503
class ToolExecutionError(AgentError):
    def __init__(self, tool: str, cause: Exception) -> None:
        super().__init__(f"tool {tool!r} failed: {cause}")
        self.tool, self.cause = tool, cause

def run_tool(name: str, **kw):
    try:
        return TOOLS[name](**kw)
    except KeyError as exc:
        raise UserInputError(f"unknown tool {name!r}") from exc
    except Exception as exc:
        raise ToolExecutionError(name, exc) from exc     # preserve __cause__
```

**Gotcha:** `raise X from exc` sets `__cause__` ("The above exception was the direct cause"); a bare `raise X` inside `except` sets `__context__` ("During handling…"). `raise X from None` suppresses the chain — use it to hide secrets that may appear in an upstream message. Never `except Exception: pass`; and never catch `BaseException` (you'd swallow `KeyboardInterrupt` and `CancelledError`).

**Follow-up they will ask:** *"3.11 `add_note`?"* → `exc.add_note(f"session={sid}")` attaches context to an exception without wrapping it — great for adding request ids to errors bubbling up.

---

### Q52. What are exception groups and `except*`?
`[HARD]`

**Answer:** `ExceptionGroup` (3.11+) carries **multiple simultaneous exceptions** — exactly what concurrent code produces. `except*` matches and handles *the subset* of a group that matches a type, and the unmatched part keeps propagating. `TaskGroup` raises `ExceptionGroup` by design.

**Code:**

```python
import asyncio
from openai import RateLimitError

async def fan_out(prompts: list[str]) -> list[str]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(call_llm(p)) for p in prompts]
    return [t.result() for t in tasks]

async def main(prompts: list[str]) -> None:
    try:
        await fan_out(prompts)
    except* RateLimitError as eg:
        print(f"{len(eg.exceptions)} calls rate-limited -> reduce concurrency")
    except* ValueError as eg:
        print("bad prompts:", [str(e) for e in eg.exceptions])
    # any other subgroup keeps propagating automatically
```

**Gotcha:** Every `except*` block that matches **runs** — unlike `except`, where only the first match runs. You cannot mix `except` and `except*` in the same `try`. And `eg.split(TypeError)` / `eg.subgroup(pred)` let you partition a group programmatically.

**Follow-up they will ask:** *"Why not just catch the first error?"* → with 50 parallel LLM calls, "3 rate-limited + 1 invalid prompt + 46 fine" is genuinely different information from "something failed", and it drives different remediation.

---

### Q53. What's your retry policy for LLM and vector-DB calls?
`[MEDIUM]`

**Answer:** Retry **only transient** failures — HTTP 429, 500/502/503/504, connection errors, timeouts. Never retry 400/401/403/404, context-length-exceeded, or content-policy refusals. Use **exponential backoff with jitter**, a cap on attempts (3–5) and a total deadline; respect `Retry-After` when the provider sends it; make the operation idempotent (idempotency key / dedupe on request hash); add a **circuit breaker** so a dead provider doesn't get hammered; and always have a fallback (smaller model, cached answer, degraded response).

**Code:**

```python
from tenacity import (retry, stop_after_attempt, stop_after_delay,
                      wait_exponential_jitter, retry_if_exception_type,
                      before_sleep_log)
import logging
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, InternalServerError

log = logging.getLogger(__name__)
client = AsyncOpenAI(max_retries=0, timeout=30.0)

@retry(
    retry=retry_if_exception_type(
        (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=(stop_after_attempt(5) | stop_after_delay(90)),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def call_llm(prompt: str) -> str:
    r = await client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content or ""
```

**Gotcha:** Double-retry is a real production bug: the OpenAI SDK retries internally (`max_retries=2` by default). If you also wrap it in tenacity with 5 attempts you get up to 15 calls and 15× the bill. Set `max_retries=0` on the client **or** don't add your own layer. Also, jitter is not optional — synchronised retries from 50 pods create a thundering herd that re-triggers the 429.

**Follow-up they will ask:** *"Where do you put the timeout?"* → both: per-request (`timeout=` on the client) and an overall deadline (`asyncio.timeout`) so total retry time stays inside your API's SLA.

---

## 10. Performance & Profiling

### Q54. Your endpoint is slow. Walk me through profiling it.
`[MEDIUM]`

**Answer:** Measure before optimising. (1) **Where** — is it in Python or waiting on I/O? Add timing spans per stage (embed / retrieve / rerank / generate). (2) **Deterministic profile** offline: `cProfile` + `snakeviz`/`pstats` on a representative workload. (3) **Live/prod**: `py-spy top --pid` (sampling, no code change, negligible overhead) or `py-spy record -o flame.svg`. (4) **Line-level**: `line_profiler` (`@profile`). (5) **Async-aware**: `py-spy dump` shows every coroutine's stack; `yappi` handles per-task wall time. Then optimise the top item only, and re-measure.

**Code:**

```bash
python -m cProfile -o out.prof -m myapp.bench      # deterministic; significant overhead
                                                   # (call-heavy code can slow several-fold)
python -m pstats out.prof                          # sort cumtime; or: snakeviz out.prof
py-spy top --pid 4242                              # live, sampling, prod-safe
py-spy record -o flame.svg --pid 4242 --duration 30
py-spy dump --pid 4242                             # all thread + asyncio task stacks
```

```python
import time
t0 = time.perf_counter()
...
elapsed_ms = (time.perf_counter() - t0) * 1000
```

**Gotcha:** `cProfile` measures CPU-ish function call time and **misleads badly on async/I/O-bound code** — it will show `select.epoll` at the top. For an LLM app, per-stage wall-clock spans plus provider-reported latency tell you more than any profiler. Also profile p95/p99, not the mean; LLM latency distributions have long tails.

**Follow-up they will ask:** *"`timeit`?"* → for micro-benchmarks only: `python -m timeit -s "setup" "stmt"`, which handles repetition and disables GC.

---

### Q55. `lru_cache`, `cache`, `cached_property` — and the trap when caching LLM calls.
`[MEDIUM]`

**Answer:** `functools.lru_cache(maxsize=N)` memoises on the argument tuple with LRU eviction; `functools.cache` (3.9+) is `lru_cache(maxsize=None)` — unbounded, so it's a leak by design if keys are unbounded; `cached_property` computes once per instance. Arguments must be **hashable**, so `dict`/`list` params break it.

**Code:**

```python
from functools import lru_cache, cache, cached_property

@lru_cache(maxsize=4096)
def embed_query(text: str) -> tuple[float, ...]:      # return a TUPLE (hashable, immutable)
    return tuple(client.embeddings.create(model="text-embedding-3-small",
                                          input=text).data[0].embedding)

embed_query.cache_info()      # CacheInfo(hits=..., misses=..., maxsize=4096, currsize=...)
embed_query.cache_clear()

class Retriever:
    @cached_property
    def index(self):          # expensive one-time load per instance
        return load_faiss_index("/data/index.faiss")
```

**Gotcha (three, all real):**
1. **Never `@lru_cache` a method on a long-lived class** — the cache holds `self`, so instances are never garbage collected (a leak that looks like a memory bug). Cache a module-level function, or use `cachetools` with a per-instance cache.
2. **Never cache a non-deterministic LLM call keyed only on the prompt** unless `temperature=0` and the model version is part of the key — otherwise you serve one user's answer to another and you can't invalidate on model upgrade.
3. `lru_cache` is **not TTL-aware and not shared across processes/pods**. For a real LLM cache use Redis with a `sha256(model|version|temp|prompt)` key and a TTL.

**Follow-up they will ask:** *"Semantic cache?"* → embed the query, ANN-search previous queries, reuse the answer above a similarity threshold (~0.95+). Cheap wins, but risky: near-duplicate questions with different intent get wrong answers, so gate it.

---

### Q56. Concrete Python optimisations, and when do you leave Python?
`[MEDIUM]`

**Answer:** In order of payoff: (1) **better algorithm/data structure** — `set`/`dict` O(1) membership instead of `list` O(n); (2) **do less work** — batch API calls, cache, avoid recomputation; (3) **avoid per-item interpreter overhead** — comprehensions and `str.join` over `+=` in loops, `map`/built-ins implemented in C; (4) **generators** to cut memory pressure; (5) **`__slots__`** for millions of objects; (6) **faster libraries at the boundary** — `orjson` for JSON (its benchmarks claim several times `json`; verify on your payloads), NumPy for vector math, `polars`/`pyarrow` for tabular; (7) **leave Python** — a Rust/C extension, or just call a compiled library.

**Code:**

```python
# O(n^2) -> O(n)
seen_ids = {c["id"] for c in existing}          # set, not list
new = [c for c in incoming if c["id"] not in seen_ids]

# string building
parts = [f"[{c['doc']}] {c['text']}" for c in chunks]
context = "\n\n".join(parts)                    # not context += ... in a loop

# vectorised cosine similarity instead of a Python loop over 100k vectors
import numpy as np
def top_k(q: np.ndarray, M: np.ndarray, k: int = 5) -> np.ndarray:
    sims = M @ q / (np.linalg.norm(M, axis=1) * np.linalg.norm(q) + 1e-12)
    idx = np.argpartition(-sims, k)[:k]           # O(n), not O(n log n) argsort
    return idx[np.argsort(-sims[idx])]            # argpartition is UNORDERED;
                                                  # sort only the k survivors
```

**Gotcha:** Order-of-magnitude figures only (never quote them as measured fact): a Python function call / attribute lookup is on the order of tens of nanoseconds, so hoisting `append = out.append` out of a hot loop is real but tiny; a NumPy vectorised op is typically one to two orders of magnitude faster than the equivalent Python loop. Always say "roughly, and I'd benchmark it". And know when it doesn't matter — if you're waiting 800 ms on an LLM, shaving 2 ms of Python is noise. Say that; it shows engineering judgement.

**Follow-up they will ask:** *"Rewrite in Rust?"* → only for a measured hot loop with a clean data boundary; PyO3/maturin. In an LLM stack the honest answer is "almost never — the latency is the model, not Python."

---

## 11. Packaging & Environments

### Q57. How do you set up and pin dependencies for a production service?
`[MEDIUM]`

**Answer:** `pyproject.toml` (PEP 621) as the single source of truth, a **lockfile** committed for reproducibility, and a virtualenv per project. I use **uv** now (Rust; the project advertises 10–100× faster installs than pip — treat that as their benchmark, not a measured fact — and it does resolution + venv + lock + run in one tool); poetry is the older equivalent; `pip` + `pip-tools`/`requirements.txt` is the minimal path. In Docker, install dependencies in a separate layer *before* copying source so the layer caches.

**Code:**

```toml
# pyproject.toml
[project]
name = "agent-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "openai>=1.40",
  "pydantic>=2.7",
  "tenacity>=8.3",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "mypy>=1.10", "ruff>=0.5"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

```bash
uv venv && uv sync           # create env + install from uv.lock
uv add openai                # add a dep and update the lock
uv run pytest                # run inside the env without activating
```

```dockerfile
FROM python:3.12-slim
COPY pyproject.toml uv.lock ./
# --no-install-project is REQUIRED here: src/ has not been copied yet, so
# installing the project itself would fail. Deps only -> layer stays cached.
RUN pip install uv && uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
RUN uv sync --frozen --no-dev                       # now install the project
CMD ["uv", "run", "--no-sync", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

**Gotcha:** Pin **loosely in `pyproject.toml`, exactly in the lockfile**. Pinning exact versions in `pyproject.toml` makes every transitive conflict your problem. And never `pip install` into the system Python inside a container without a reason — 3.11+ enforces PEP 668 (`externally-managed-environment`) on many distros.

**Follow-up they will ask:** *"How do you handle the `openai` SDK's fast release cadence?"* → floor-pin (`>=1.40,<2`), lock exactly, and have a contract test that hits a recorded fixture so an SDK bump fails CI, not prod.

---

### Q58. venv, editable installs, src layout, and resolving a dependency conflict.
`[EASY]`

**Answer:** `python -m venv .venv` creates an isolated interpreter+site-packages; activate, or use `uv run`. `pip install -e .` (editable) installs your package by path so imports resolve without reinstalling on every edit. **src layout** (`src/mypkg/…`) prevents accidentally importing the local directory instead of the installed package — it catches "works on my machine, broken in the wheel" bugs. Conflicts: read the resolver error, find the common constraint, and if two libraries genuinely disagree, isolate one behind a service boundary or vendor a shim.

**Code:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip list --outdated
pip install pipdeptree && pipdeptree -r -p pydantic    # who requires pydantic v1?
python -c "import sys; print(sys.prefix, sys.executable)"   # am I in the venv?
```

**Gotcha:** The classic AI-stack conflict is **pydantic v1 vs v2** (older langchain/llamaindex pinned v1). Check with `pipdeptree -r -p pydantic` before debugging phantom validation errors. Second classic: a file named `openai.py` or `types.py` in your project shadows the real module — `ImportError: cannot import name 'OpenAI'`.

**Follow-up they will ask:** *"`PYTHONPATH` hacks?"* → avoid; use an editable install. Manipulating `sys.path` at runtime is a smell that the packaging is wrong.

---

## 12. Testing

### Q59. pytest essentials: fixtures, scope, parametrize, monkeypatch.
`[EASY]`

**Answer:** **Fixtures** provide setup/teardown as arguments (`yield` splits setup from teardown); scopes are `function` (default), `class`, `module`, `session`. **`parametrize`** runs one test over many inputs with separate pass/fail per case. **`monkeypatch`** temporarily patches attributes/env/`sys.path` and auto-restores. Put shared fixtures in `conftest.py`.

**Code:**

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def settings():
    return {"model": "gpt-4o-mini", "top_k": 5}

@pytest.fixture
def temp_index(tmp_path):            # tmp_path is a built-in fixture
    p = tmp_path / "index.bin"
    p.write_bytes(b"")
    yield p                          # teardown after yield
    # tmp_path is cleaned up automatically

# test_chunking.py
@pytest.mark.parametrize(
    "text,size,expected",
    [("a" * 100, 50, 2), ("a" * 101, 50, 3), ("", 50, 0)],
    ids=["exact", "remainder", "empty"],
)
def test_chunk_count(text, size, expected):
    assert len(chunk(text, size)) == expected

def test_reads_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("myapp.config.DEFAULT_MODEL", "gpt-4o-mini")
    assert load_config().model == "gpt-4o-mini"
```

**Gotcha:** A `session`-scoped fixture holding mutable state leaks between tests and creates order-dependent failures. To *expose* them, install **`pytest-randomly`**, which shuffles test order by default (`-p no:randomly` is the flag that turns the shuffling **off** again, e.g. to reproduce a specific ordering). Also `monkeypatch.setattr` must target **where the name is looked up**, not where it's defined: patch `myapp.rag.OpenAI`, not `openai.OpenAI`, if `rag.py` did `from openai import OpenAI`.

**Follow-up they will ask:** *"Fixture vs setup method?"* → fixtures compose, have scopes, and can be requested by name; `setUp` is unittest legacy.

---

### Q60. How do you unit-test code that calls an LLM?
`[MEDIUM]`

**Answer:** Never hit the real API in unit tests — it's slow, costs money, and is non-deterministic. Three levels: (1) **inject a fake** — depend on a `Protocol`, pass a stub in tests (best design); (2) **mock the SDK boundary** with `unittest.mock.patch` / `AsyncMock` returning a realistic response object; (3) **record/replay HTTP** with `respx` (httpx) or `vcrpy` for a few high-value integration tests. Keep 1–2 real "smoke" tests behind a marker, run nightly.

**Code:**

```python
import pytest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

def fake_completion(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=None),
                                 finish_reason="stop")],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

@pytest.mark.asyncio                       # or asyncio_mode = "auto" in pyproject
async def test_summarize_strips_whitespace():
    with patch("myapp.llm.client.chat.completions.create",
               new=AsyncMock(return_value=fake_completion("  hello  "))) as m:
        out = await summarize("some doc")
    assert out == "hello"
    m.assert_awaited_once()
    kwargs = m.await_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"     # assert the CONTRACT, not the prose

@pytest.mark.asyncio
async def test_retries_on_rate_limit():
    import httpx
    from openai import RateLimitError

    # RateLimitError -> APIStatusError, whose __init__ reads response.request,
    # response.status_code and response.headers. You MUST pass a real
    # httpx.Response; `response=None` raises AttributeError inside the SDK.
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    err = RateLimitError("rate limited",
                         response=httpx.Response(429, request=req),
                         body=None)

    m = AsyncMock(side_effect=[err, fake_completion("ok")])
    with patch("myapp.llm.client.chat.completions.create", new=m):
        assert await summarize("doc") == "ok"
    assert m.await_count == 2
```

**Gotcha:** Use `AsyncMock` (not `MagicMock`) for anything awaited, or you get `TypeError: object MagicMock can't be used in 'await' expression`. Constructing SDK exceptions in tests is its own trap — `openai`'s `APIStatusError` subclasses (`RateLimitError`, `APIStatusError`, `BadRequestError`, …) require a real `httpx.Response`, while `APIConnectionError`/`APITimeoutError` take `request=`. And assert on **structure and control flow** (was the schema respected? did it retry? was the tool called with the right args?), never on exact generated wording — that test will flake the day the model updates.

**Follow-up they will ask:** *"pytest-asyncio setup?"* → `asyncio_mode = "auto"` under `[tool.pytest.ini_options]` so you can drop `@pytest.mark.asyncio`; use an `event_loop`-scoped fixture carefully, or `anyio` if you support trio too.

---

### Q61. How do you test something non-deterministic like an agent's answer quality?
`[HARD]`

**Answer:** Split it into layers. **Deterministic unit tests** for everything around the model: chunking, prompt rendering, schema validation, tool dispatch, retry/fallback, state transitions — these should be 90% of your suite and must be fully mocked. **Evaluation (not unit testing)** for the model behaviour: a versioned golden dataset of inputs plus assertions that are robust — schema validity rate, exact match on extraction fields, retrieval recall@k / MRR, groundedness (does every claim cite a retrieved chunk), and LLM-as-judge with a rubric. Track these as **metrics with thresholds** in CI (fail if schema-valid rate < 99% or recall@5 drops > 3 points), not as pass/fail assertions on text.

**Code:**

```python
import json, pytest
from pydantic import ValidationError

GOLDEN = json.load(open("tests/data/extraction_golden.json"))   # versioned, reviewed

@pytest.mark.eval                       # marked; runs nightly, not on every commit
@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: c["id"])
def test_extraction_schema_and_fields(case):
    out = extract(case["input"])                 # real model call
    assert isinstance(out, Ticket)               # schema validity is deterministic
    assert out.severity == case["severity"]      # objective field
    # fuzzy field: assert containment, not equality
    assert set(case["must_mention"]) <= set(w.lower() for w in out.summary.split())

def test_retrieval_recall_at_5():
    hits = sum(case["gold_doc"] in [d.doc_id for d in retrieve(case["q"], k=5)]
               for case in GOLDEN)
    assert hits / len(GOLDEN) >= 0.85            # threshold, tracked over time
```

**Gotcha:** Set `temperature=0` and pin the **exact model snapshot** (e.g. `gpt-4o-mini-2024-07-18`) in eval runs — otherwise a silent provider-side model update looks like your regression. Even at temperature 0, LLM output is not guaranteed byte-identical, so never assert string equality on free text.

**Follow-up they will ask:** *"LLM-as-judge reliability?"* → it's biased (position bias, verbosity bias, self-preference). Mitigate with a fixed rubric, randomised answer order, a stronger judge model than the one under test, and periodic human spot-checks on a sample.

---

## 13. Logging & Observability

### Q62. Structured logging with correlation IDs across async calls.
`[MEDIUM]`

**Answer:** Emit **JSON logs with a stable schema**, not f-strings, so they're queryable. Propagate a `request_id`/`trace_id` using **`contextvars`** — unlike thread-locals, `contextvars` are copied into each asyncio Task, so the id follows the request across `await`s and `create_task`. Inject it with a `logging.Filter` (or use `structlog`'s contextvars integration).

**Code:**

```python
import contextvars, json, logging, uuid
from fastapi import FastAPI, Request

request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}

class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for k, v in record.__dict__.items():          # anything passed via extra=
            if k not in _RESERVED and k not in payload:
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
handler.addFilter(ContextFilter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
log = logging.getLogger("agent")

app = FastAPI()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    token = request_id.set(request.headers.get("x-request-id") or str(uuid.uuid4()))
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id.get()
        return response
    finally:
        request_id.reset(token)

log.info("llm_call", extra={"model": "gpt-4o-mini", "prompt_tokens": 812, "latency_ms": 940})
```

**Gotcha:** `contextvars` propagate into tasks created *after* the value is set; a task created before, or work handed to a `ThreadPoolExecutor`, does **not** inherit it automatically (`loop.run_in_executor` loses it — pass the id explicitly or use `contextvars.copy_context().run`). Also always `reset(token)` in a `finally`.

**Follow-up they will ask:** *"Why not thread-local?"* → asyncio multiplexes many requests onto one thread, so a thread-local would be shared across concurrent requests and give you the wrong id.

---

### Q63. What do you log/monitor in a production LLM app?
`[MEDIUM]`

**Answer:** Per request: `request_id`, `session_id`, user/tenant (hashed), model + **model snapshot version**, prompt/completion/total tokens, **estimated cost**, latency split by stage (embed / retrieve / rerank / generate), time-to-first-token for streams, `finish_reason`, retry count, cache hit/miss, tool calls (name + duration + success), guardrail verdicts, and the error type on failure. Aggregate: p50/p95/p99 latency, error rate by class, 429 rate, tokens/min against the provider quota, cost per request and per tenant. Add tracing (OpenTelemetry) so one trace shows the whole agent run.

**Code:**

```python
COST_PER_1M = {"gpt-4o-mini": (0.15, 0.60)}   # (input, output) USD per 1M tokens — verify current pricing

def log_completion(resp, model: str, stage: str, ms: float) -> None:
    u = resp.usage
    cin, cout = COST_PER_1M.get(model, (0.0, 0.0))
    log.info("llm_call", extra={
        "stage": stage, "model": model,
        "prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
        "latency_ms": round(ms, 1),
        "finish_reason": resp.choices[0].finish_reason,
        "cost_usd": round(u.prompt_tokens / 1e6 * cin + u.completion_tokens / 1e6 * cout, 6),
    })
```

**Gotcha:** **Do not log full prompts and completions by default** — they contain user PII, and in an enterprise (Virtusa's clients: BFSI, healthcare) that's a compliance incident. Log hashes/lengths/token counts by default, put full payloads behind an explicit, access-controlled debug flag with short retention, and redact secrets. Never log the API key, and never let an exception message containing headers reach the logs.

**Follow-up they will ask:** *"How would you detect quality regressions in prod?"* → sample traffic into an offline eval set, track user feedback signals (thumbs, retries, abandonment), and alert on schema-validation failure rate and refusal rate — those move first when a model or prompt changes.

---

## Red Flags / Do NOT say

- ❌ "The GIL was removed in Python 3.13." → ✅ "Optional free-threaded build; experimental in 3.13, officially supported but still opt-in in 3.14."
- ❌ "asyncio makes code faster / gives parallelism." → ✅ "It gives concurrency on one thread; it helps I/O-bound work, not CPU-bound."
- ❌ "I use threads for CPU work to go faster." → ✅ "Processes (or NumPy/C) for CPU; threads only for blocking I/O."
- ❌ "Type hints are enforced at runtime." → ✅ "They're metadata; mypy/pyright enforce statically, pydantic enforces at runtime."
- ❌ "I use `openai.ChatCompletion.create(...)`." → that's the pre-1.0 API, **removed**. ✅ `client.chat.completions.create(...)`.
- ❌ "`from langchain.llms import OpenAI`" → legacy. ✅ `from langchain_openai import ChatOpenAI`.
- ❌ "I cache LLM responses with `@lru_cache`." → unbounded, per-process, no TTL, ignores model version. Say Redis + hashed key + TTL.
- ❌ "I catch `Exception` everywhere so nothing crashes." → hides bugs, swallows `CancelledError` semantics; catch specific types.
- ❌ "`sys.getsizeof` tells me object memory." → it's shallow. Say `tracemalloc`.
- ❌ Guessing an API signature confidently. If unsure, say: *"I'd check the docs, but the shape is roughly X"* — that reads as senior, not weak.
- ❌ Bluffing production experience you don't have. Say "I've read about it / used it in a side project" and then show real depth on something adjacent.

---

## Rapid-Fire (last 10 min before you walk in)

| # | Q | A |
|---|---|---|
| 1 | `list` vs `tuple` vs `set` lookup cost | list `in` = O(n); set/dict `in` = O(1) avg; tuple immutable + hashable |
| 2 | Shallow vs deep copy | `copy.copy` = new outer, shared inner; `deepcopy` = recursive, uses a memo for cycles |
| 3 | Mutable default arg fix | `def f(x=None): x = [] if x is None else x` |
| 4 | `is` vs `==` | identity vs value; use `is` only for `None`/`True`/`False`/sentinels |
| 5 | GIL in one line | one mutex → one thread runs Python bytecode at a time; released on I/O and in many C calls |
| 6 | Free-threading status | PEP 703; optional `python3.13t` build (experimental 3.13, supported 3.14), not the default |
| 7 | asyncio vs threads vs processes | I/O+scale → asyncio; blocking libs → threads; CPU → processes |
| 8 | `gather` vs `TaskGroup` | gather keeps input order and lets siblings run on failure; TaskGroup cancels siblings + raises `ExceptionGroup` (3.11+) |
| 9 | Rate-limit N LLM calls | `asyncio.Semaphore(N)` around the call + retry on 429 with jittered backoff |
| 10 | Blocking call in async code | `await asyncio.to_thread(fn, ...)` — never call it inline |
| 11 | Cancel semantics | `CancelledError` is a `BaseException` (3.8+); if you catch it, re-raise it |
| 12 | Timeout idiom (3.11+) | `async with asyncio.timeout(10): ...` |
| 13 | Generator vs list | generator = lazy, O(1) memory, single pass; list = eager, indexable, reusable |
| 14 | `yield from` | delegate to a sub-generator; forwards `send`/`throw` and captures its `return` |
| 15 | Iterator protocol | `__iter__` + `__next__`; `StopIteration` ends the loop |
| 16 | `__slots__` win | no per-instance `__dict__` → roughly 50–70% less memory on small objects, faster attribute access; breaks dynamic attrs + `cached_property` |
| 17 | Data vs non-data descriptor | data (`__set__`) beats instance `__dict__`; non-data loses to it — that's how `cached_property` works |
| 18 | MRO of `D(B, C)` where `B,C(A)` | D, B, C, A, object (C3) |
| 19 | Metaclass alternative | `__init_subclass__` + `__set_name__` |
| 20 | Refcount + GC | refcount frees immediately; generational GC (3 gens, `(700,10,10)`) collects cycles |
| 21 | Find a leak | `tracemalloc` snapshot `compare_to`; `py-spy dump`; count `gc.get_objects()` by type |
| 22 | Pydantic v2 speed | validation core is compiled Rust (`pydantic-core`), schema built once per model |
| 23 | v1→v2 renames | `.dict()`→`.model_dump()`, `.json()`→`.model_dump_json()`, `@validator`→`@field_validator`, `Config`→`ConfigDict` |
| 24 | `except*` | matches a subgroup of an `ExceptionGroup` (3.11+); all matching blocks run; can't mix with plain `except` |
| 25 | Mock an async LLM call | `patch("mod.client.chat.completions.create", new=AsyncMock(return_value=fake))` |
