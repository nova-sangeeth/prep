# Virtusa — Python GenAI / Agentic AI Developer (6+ yrs)

> **L1 Face-to-Face Technical Interview**
> **Date:** 01 Aug 2026
> **Venue:** Virtusa Consulting Services Pvt. Ltd., 34, IT Highway, Navalur, Chennai — 600130
> **Mode:** In person. Expect whiteboard/paper coding + rapid verbal grilling.

---

## The Files

| # | File | What it covers | Priority |
|---|------|----------------|----------|
| 01 | [Python Core & Advanced](01-python-core-advanced.md) | Data model, MRO, decorators, generators, GIL, asyncio, memory, pydantic v2, typing | ⭐⭐⭐ |
| 02 | [Python Coding Problems](02-python-coding-problems.md) | Whiteboard problems: LRU, rate limiter, chunker, cosine top-k, async pools | ⭐⭐⭐ |
| 03 | [REST APIs — FastAPI/Flask/Django](03-api-frameworks-fastapi-flask-django.md) | DI, SSE streaming, auth, async vs def, workers, production checklist | ⭐⭐⭐ |
| 04 | [LLM Fundamentals](04-llm-fundamentals-genai.md) | Transformers, tokens, decoding params, tool calling, cost/latency, evals | ⭐⭐⭐ |
| 05 | [Prompt Engineering](05-prompt-engineering.md) | Prompt anatomy, CoT/ReAct, structured output, injection defense, before/after rewrites | ⭐⭐ |
| 06 | [RAG Pipelines](06-rag-pipelines.md) | Chunking, hybrid+RRF, rerank, ACLs, RAGAS, failure triage, end-to-end code | ⭐⭐⭐ |
| 07 | [Vector DBs & Embeddings](07-vector-databases-embeddings.md) | HNSW/IVF knobs, filtering, pgvector/FAISS/Azure AI Search, sizing math | ⭐⭐⭐ |
| 08 | [Agentic AI Concepts](08-agentic-ai-concepts.md) | Agent loop, ReAct, tool design, memory types, multi-agent patterns, guardrails | ⭐⭐⭐ |
| 09 | [Agent Frameworks](09-agent-frameworks-langchain-langgraph-mcp.md) | LangChain LCEL, LangGraph StateGraph, CrewAI, AutoGen, Semantic Kernel, MCP | ⭐⭐⭐ |
| 10 | [Cloud / Azure OpenAI / LLMOps](10-cloud-deployment-azure-openai-mlops.md) | Azure OpenAI, TPM/PTU, 429s, Docker, K8s, CI/CD, OWASP LLM Top 10 | ⭐⭐ |
| 11 | [System Design — GenAI](11-system-design-genai.md) | 14 end-to-end designs + a 25-min answering framework | ⭐⭐ |
| 12 | [Hands-On Coding Challenges](12-hands-on-coding-challenges.md) | 18 build-it tasks with full runnable solutions | ⭐⭐⭐ |
| 13 | [Behavioral / Experience / HR](13-behavioral-experience-and-hr.md) | STAR answers, project deep-dive, services-company Qs, CTC, logistics | ⭐⭐ |
| 14 | [Rapid-Fire Cheatsheet](14-rapid-fire-cheatsheet.md) | ~250 one-liners + cheat tables. **Read this last.** | ⭐⭐⭐ |

Existing repo material worth reusing: [../DSA_MASTER.md](../DSA_MASTER.md), [../dsa/](../dsa/), [../python_basics/](../python_basics/), [../system_design/](../system_design/), [../plan.txt](../plan.txt).

---

## T-19 Hour Battle Plan

Assumes you start now and the interview is tomorrow morning. **Sleep is non-negotiable — a tired brain fails whiteboard rounds.**

| Block | Hours | Do this | Files |
|-------|-------|---------|-------|
| **1. Core differentiators** | 3.0 | RAG + Agentic concepts. This JD is 60% these two. Read fully, out loud where possible. | 06, 08 |
| **2. Frameworks** | 1.5 | LangGraph StateGraph + tool-calling agent. Type the 3 code samples by hand at least once. | 09 |
| **3. Hands-on drill** | 2.5 | Actually run tasks 1, 3, 5, 6, 8 from the build-it file. Muscle memory beats reading. | 12 |
| **4. Python + API** | 2.0 | Skim 01 (focus: asyncio, GIL, decorators, generators, pydantic v2), then 03 (focus: Depends, StreamingResponse/SSE, async vs def, workers). | 01, 03 |
| **5. LLM fundamentals** | 1.5 | Decoding params, tokenization, tool calling, fine-tune vs RAG, cost math. | 04 |
| **6. Vector DB** | 1.0 | HNSW knobs, cosine vs dot, filtering, pgvector vs Azure AI Search, memory sizing formula. | 07 |
| **7. SLEEP** | 6.0 | **Non-negotiable.** | — |
| **8. Morning: coding warm-up** | 1.0 | 3 problems on paper, timed. Pick: LRU cache, text chunker with overlap, async bounded worker pool. | 02, 12 |
| **9. Morning: story + logistics** | 0.5 | "Tell me about yourself" out loud 3×. Project deep-dive. Notice period + CTC answers. | 13 |
| **10. Final hour** | 1.0 | Rapid-fire cheatsheet only. Nothing new. | 14 |

**If you fall behind, cut in this order:** 11 (system design) → 05 (prompt engineering) → 10 (cloud). Never cut 06, 08, 12, or 14.

---

## What They Will Almost Certainly Ask

Have a crisp, rehearsed answer for each of these before you walk in:

1. Walk me through a RAG pipeline you built, end to end.
2. How do you chunk documents, and why that size/overlap?
3. Dense vs sparse vs hybrid retrieval — what did you ship and why?
4. What is an AI agent vs a chain? When do you *not* use an agent?
5. Explain ReAct. Now write one without a framework.
6. How does function/tool calling actually work under the hood?
7. How do you manage agent memory across a long conversation?
8. How do you stop an agent looping forever / burning budget?
9. Multi-agent: supervisor vs sequential — pick one for my use case and defend it.
10. LangGraph state + checkpointing — why does it beat AgentExecutor?
11. `async def` vs `def` in FastAPI — what breaks if you get it wrong?
12. Stream LLM tokens to a browser. Write the endpoint.
13. How do you handle a 429 from Azure OpenAI in production?
14. How did you evaluate quality? Give me numbers.
15. How did you reduce cost/latency? Give me numbers.
16. Prompt injection through retrieved documents — how do you defend?
17. Enterprise doc access control in RAG — how do you enforce per-user ACLs?
18. Design a document Q&A system for 10M docs.

**Rule:** every answer that *can* have a number, gets a number. "We cut p95 from 4.2s to 1.6s" beats "we optimized it."

---

## Interview-Day Logistics

- Venue is Navalur (OMR). Chennai OMR traffic is unforgiving — **leave 90 min early**.
- Carry: 3 printed CVs, photo ID, last 3 payslips, offer letter, relieving letter (if any), pen + notebook.
- Whiteboard etiquette: state assumptions out loud → brute force first → then optimize → then complexity. Never start coding silently.
- Don't know an answer? Three-step recovery (detail in [13](13-behavioral-experience-and-hr.md)): say what you *do* know that's adjacent → state how you'd find out → ask a clarifying question that shows you understand the problem shape.

---

*Generated 31 Jul 2026.*
