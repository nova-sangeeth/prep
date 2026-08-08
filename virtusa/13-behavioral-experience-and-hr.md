# Behavioral, Experience & HR Round

> Virtusa Python GenAI/Agentic AI — L1 F2F prep

**Context:** Virtusa is an IT **services / consulting** firm. That changes what they probe. Product companies ask "how deep can you go." Services companies ask that *and*: can you face a client, can you work with an onsite/offshore split, can you absorb ambiguous requirements, will you stay, and will you take the non-glamorous work when the GenAI project ends. Answer with both hands.

## Table of Contents

| # | Section |
|---|---|
| 1 | [Project Deep-Dive — the questions they will actually ask](#1-project-deep-dive) |
| 2 | [STAR template + 4 fully-written model answers](#2-star-template--model-answers) |
| 3 | ["Tell me about yourself" — 2-minute skeleton](#3-tell-me-about-yourself) |
| 4 | [Services-company specific questions](#4-services-company-specific) |
| 5 | [Conflict, failure, pressure, feedback](#5-conflict-failure-pressure-feedback) |
| 6 | [HR & logistics — Virtusa specific](#6-hr--logistics) |
| 7 | [Questions YOU ask them](#7-questions-you-ask-them) |
| 8 | [Red flags — do NOT say](#8-red-flags--do-not-say) |
| 9 | [F2F day mechanics](#9-f2f-day-mechanics) |
| — | [Rapid-Fire](#rapid-fire-last-10-min-before-you-walk-in) |

---

## 1. Project Deep-Dive

This is 40-60% of an L1 F2F. They pick one project from your CV and dig until you hit bottom. **Prepare ONE GenAI project so thoroughly you could whiteboard it from memory** — architecture, numbers, trade-offs, failures. A second project prepared at medium depth. Everything else, one line.

### Q1. Walk me through your GenAI project end to end.

`[MEDIUM]`

**Answer:** Use a fixed 6-beat structure, 3-4 minutes, then stop and let them steer:

1. **Problem + business impact** — "Support agents spent ~12 minutes per ticket searching a 40k-document knowledge base; the goal was to cut handle time without dropping resolution quality."
2. **Constraints** — data residency, latency SLO, budget, team size, timeline.
3. **Architecture in one breath** — "FastAPI service → hybrid retrieval over Azure AI Search → cross-encoder rerank → Azure OpenAI generation with citations, all traced to Langfuse."
4. **My specific contribution** — say "I" for what you built, "we" for what the team built. Never blur this; panels probe it deliberately.
5. **Numbers** — scale, latency, accuracy, cost, adoption.
6. **What I'd change** — one honest thing. This is the line that reads as senior.

**Gotcha:** Do not start with the tech stack. Starting with "we used LangChain and Pinecone" signals a tool user, not an engineer. Start with the problem.

**Follow-up they will ask:** "What was *your* part?" — have the answer pre-drafted, at file/component granularity.

---

### Q2. What exactly did you build vs what did the team build?

`[MEDIUM]`

**Answer:** Be precise and unembarrassed about scope. "I owned the retrieval layer and the evaluation harness: chunking strategy, the hybrid search + RRF fusion, the reranker integration, and the RAGAS-based CI gate. A colleague owned the ingestion pipeline; our architect owned the Azure landing zone. I reviewed their PRs and we pair-designed the chunk schema."

**Gotcha:** Claiming everything on a 6-person project is the single most common credibility failure. Owning two components deeply beats claiming eight shallowly — and they *will* drill the ones you claim.

---

### Q3. How did you measure success? Give me numbers.

`[HARD]`

**Answer:** Three layers, and say all three:
- **Retrieval:** hit-rate@5 and NDCG@10 on a 200-question golden set built with SMEs — "we went from 0.71 to 0.89 hit-rate@5 after adding hybrid search and a reranker." Be ready to define hit-rate@5 if asked: the fraction of questions where at least one chunk containing the answer appears in the top 5.
- **Generation:** RAGAS faithfulness and answer-relevancy, plus a human-audited sample weekly.
- **Business:** average handle time, deflection rate, thumbs-down rate, adoption (weekly active users).

**Gotcha:** If you have no numbers, do not invent them — invented numbers collapse under one follow-up. Say: "We didn't have a formal eval harness at first, which was a mistake I'd fix; what we did have was thumbs-down rate, which dropped from ~18% to ~7% after the reranker." Honest partial measurement beats fabricated precision.

**Follow-up they will ask:** "Who built the golden set and how?" → SMEs wrote real questions from ticket history, we froze answers, versioned it in git, and added every production failure as a permanent case.

---

### Q4. How did you handle hallucinations in production?

`[HARD]`

**Answer:** Layered, and name the layers:
1. **Retrieval quality first** — most "hallucinations" are retrieval failures. Fixing chunking and adding a reranker removed the majority.
2. **Grounding instructions + citations** — the model must cite chunk IDs; an answer with no citation is treated as a refusal.
3. **Abstention path** — an explicit "I don't have that information" branch, and we measured how often it fired. A system that never abstains is lying somewhere.
4. **Post-generation validation** — check cited chunk IDs exist and the answer's numbers appear in the retrieved context.
5. **Monitoring** — faithfulness scoring on a traffic sample, thumbs-down capture with the full trace.

**Gotcha:** "We set temperature to 0" alone is a junior answer. Temperature 0 makes it deterministically confident, not correct.

---

### Q5. What was the hardest bug you hit?

`[MEDIUM]`

**Answer:** Pick a bug with a **non-obvious root cause and a measurable fix**. Strong candidates from real GenAI work: chunk boundaries splitting tables so numbers were retrieved without their headers; a `SET LOCAL hnsw.ef_search = ...` issued on an autocommit connection, so it was scoped to a transaction that ended before the query ran and the index kept using the default `ef_search` (Postgres logs a warning here, but the driver swallowed it); an event loop blocked by a sync SDK call inside `async def`, serialising every request in that worker process to one at a time; a cache key missing the tenant ID, leaking one tenant's answer to another (say how you found it and that you disclosed it).

Structure: symptom → what you first suspected (and why that was wrong) → how you isolated it → root cause → fix → what you added so it can't recur.

**Gotcha:** The "what you added so it can't recur" beat is what they're scoring. A bug story with no regression test is half an answer.

---

### Q6. Why did you choose X over Y? (LangChain vs LangGraph, Pinecone vs pgvector…)

`[MEDIUM]`

**Answer:** Always: **requirement → options considered → deciding constraint → what you gave up.**

"We used pgvector rather than a dedicated vector DB because the corpus was ~2M chunks, we already ran Postgres with the ACL tables, and joining permissions in SQL at query time was worth more to us than raw ANN throughput. The trade-off: at 50M+ vectors we'd have outgrown it, and we accepted a rebuild later."

**Gotcha:** "It's the industry standard" or "the architect chose it" are both non-answers. If you genuinely inherited the choice, say so and then say what you'd have chosen and why — that still demonstrates judgment.

---

### Q7. What was your cost, and how did you reduce it?

`[HARD]`

**Answer:** Have a real number and a real lever. "We were at roughly $8k/month against ~40k queries — call it $0.20 a query, which told me straight away we were sending too much context. Three levers took it to around $3k: routing classification and simple lookups to a small model (~55% of traffic), prompt caching on the static system prefix, and cutting the chunks we passed to the model from 10 to 4 once the reranker was good enough to make the tail irrelevant — which also took roughly 700 ms off p95."

**Gotcha:** Know the mechanism, not just the correlation. Input tokens drive cost *and* the prefill/time-to-first-token part of latency; output tokens drive the rest of latency but relatively little of the cost. RAG is input-heavy and output-light — a few thousand tokens of context for a two-line answer — so trimming context moves both numbers together. Say it that way; "cost and latency are the same thing" on its own invites a correction.

---

### Q8. What scale did it run at?

`[EASY]`

**Answer:** Users, requests/day, corpus size, peak concurrency, p95 latency. If it was a pilot, say pilot — "180 provisioned users, ~140 weekly active, ~1.8k queries on a working day (~40k/month), 40k documents, p95 around 3.5s after the optimisation work" is a perfectly respectable, honest answer. Inflating to "millions of users" invites capacity questions you will not survive.

**Gotcha:** Whatever numbers you give, make sure they divide correctly — panels do the arithmetic. Queries/day × working days must match your monthly figure, and your monthly cost ÷ monthly queries must match the per-query cost you quote in Q7. Getting caught by mental arithmetic is a very cheap way to lose credibility.

---

### Q9. What would you do differently?

`[MEDIUM]`

**Answer:** One real thing, stated without self-flagellation. Best answers: "build the eval harness in week one instead of month three — we spent weeks arguing about whether changes helped"; "version the retrieval config alongside the prompt from the start"; "push back harder on scope and ship one department properly instead of three partially."

**Gotcha:** Don't pick a fake weakness ("I'd have documented more"). Don't pick something that indicts a colleague.

---

### Q10. What did you do when the model just wasn't good enough?

`[MEDIUM]`

**Answer:** Show a diagnostic ladder rather than a magic fix: attribute the failure first (retrieval vs generation — pull the retrieved chunks for 30 failing questions and check whether the answer was even *in* the context), then fix the layer that's actually broken. In our case ~70% of failures were retrieval, so prompt engineering would have been wasted effort. Say that number-first instinct out loud; it's the difference between debugging and guessing.

---

## 2. STAR Template + Model Answers

> **Read this before you memorise anything below.** Every number in these four answers is a *worked example* showing the shape and density a senior answer needs. They are not your numbers. Swap in your real figures tonight — and where you don't have a figure, use the honest substitute from Q3 rather than borrowing one from this page. Quoting a metric you never measured survives exactly one follow-up ("how did you measure that?"), and the rest of the interview is then spent doubting everything else you said. The four stories are also one project told in sequence, so the numbers below are internally consistent with each other and with Q7/Q8 — if you change one, change the others to match.

### The template — fill this in for 5 stories tonight

```
SITUATION  (15s)  Where, when, what was at stake. One sentence. Include a number.
TASK       (10s)  YOUR specific responsibility. Say "I was responsible for..."
ACTION     (60s)  3-4 concrete steps YOU took. Verbs. Include a decision + why.
RESULT     (20s)  Quantified. Then one line on what you learned / kept.
```

Five stories cover most behavioral questions: **(1)** shipped something hard, **(2)** fixed a production incident, **(3)** disagreed with someone senior, **(4)** failed / missed a deadline, **(5)** influenced without authority / mentored. The four model answers below cover stories 1, 2 and 3 (plus a cost/performance story, which comes up often enough in services interviews to be worth having). Story 4's raw material is in Q21 and story 5's is in Q16 — write those two out in full yourself, because the ones you draft are the ones you can actually deliver under pressure.

---

### Model answer 1 — "Tell me about a project you're proud of"

> **S:** Our support org handled ~2,000 tickets a week, and agents were spending around 12 minutes per ticket hunting through a 40,000-document knowledge base that spanned three systems.
>
> **T:** I was the senior engineer on a two-person build team, responsible for the retrieval layer and the evaluation harness — the architecture was mine to propose, and quality was mine to prove.
>
> **A:** I started by building the eval before the product: 200 real questions from ticket history, answers frozen with two SMEs, versioned in git. The first naive RAG scored 0.71 hit-rate@5, which told us retrieval — not prompting — was the problem. I moved from fixed 1,000-character chunking to header-aware chunking with parent-document retrieval, because our docs were structured runbooks and fixed chunking was severing tables from their headers. Then I added BM25 alongside dense retrieval with RRF fusion, which fixed the error-code queries that embeddings were failing completely — exact tokens like `ERR-4021` are the classic dense-retrieval blind spot. Finally a cross-encoder reranker over a 30-candidate pool, so the 10 chunks we actually passed to the model were the right ten rather than the ten the ANN index liked. Every change was merged only if the golden-set score improved.
>
> **R:** Hit-rate@5 went 0.71 → 0.89, RAGAS faithfulness 0.83 → 0.94, and p95 latency came down from 6.1s to about 4.2s — the reranker *added* roughly 200ms of its own, but header-scoped chunks replaced a pile of overlapping near-duplicates, so the net context we sent shrank. Handle time fell from ~12 to ~7 minutes on the tickets where agents used it, and we hit 140 weekly active agents within two months. The thing I kept from it: build the eval harness first. It turned every debate about "does this feel better" into a number.

*Why this works: numbers at every beat, a decision with a stated reason, a diagnosis before a fix, and a transferable lesson.*

---

### Model answer 2 — "Tell me about a time you cut cost or improved performance"

> **S:** Three months post-launch our Azure OpenAI spend hit about $8,000 a month against a $4,000 budget, and finance escalated it.
>
> **T:** I owned the reduction, with a hard constraint: no measurable drop in answer quality on the golden set.
>
> **A:** First I instrumented rather than guessed — added per-request token and cost logging tagged by query type, and found that 55% of traffic was simple classification and lookup that didn't need the large model. So I built a lightweight router: a cheap classifier picks the tier, with the large model as the fallback for anything ambiguous. Second, I restructured the prompt so the static system instructions and few-shot examples sat in a stable prefix and the variable retrieved context came after it, because prefix caching only pays off if the shared part is byte-identical and long enough to qualify — we'd been interpolating the user's question near the top, which invalidated the prefix on every single call. Third, I ran an experiment cutting the chunks passed to the model from 10 to 4 — the golden-set score was flat, and that removed about 60% of the retrieved context, which worked out to a bit under half our total input tokens once you account for the static prefix. I gated all three behind the eval suite so I could prove quality held.
>
> **R:** Spend went from roughly $8,000 to roughly $3,100 a month — the router was about two-thirds of that, the context cut most of the rest — p95 latency improved by around 700ms as a side effect, taking us to about 3.5s, and golden-set faithfulness actually ticked up slightly because there was less irrelevant context to distract the model. What I took from it: RAG is input-heavy and output-light, so context size is the one knob that moves cost and time-to-first-token together — and you should always instrument before optimizing.

---

### Model answer 3 — "Tell me about a production incident"

> **S:** On a Tuesday morning our assistant started returning answers that were fluent but wrong — citing documents that didn't contain the claims. Thumbs-down rate went from about 7% to 30% inside an hour.
>
> **T:** I was on call and took incident lead.
>
> **A:** First move was to stop the bleeding, not to find the cause: we rolled the service back to the previous release, and quality recovered within ten minutes. Then I pulled the traces for the failing requests and compared retrieved chunk IDs against the answers. The retrieval was returning chunks from the *previous* index generation. The root cause was a re-embedding migration from the night before. It was two steps — roll out config pointing at the new embedding model, then flip the index alias to the newly-built index — and the flip script had failed partway through without anyone checking its exit code. So the app was embedding queries with the new model while a share of them were still being served against the index built with the old one. Two different embedding models put vectors in two unrelated spaces, so the nearest neighbours were effectively arbitrary — and because both models happened to output the same dimensionality, nothing threw. A dimension mismatch would have given us a loud error on the first query; matching dimensions gave us confident nonsense instead, which is why it took a trace comparison rather than a stack trace to find. The fix was to complete the flip properly; the *real* fix was making the alias flip atomic and adding a startup assertion that the embedding model version in config matches the version recorded on the index metadata, so the service refuses to serve rather than serving garbage.
>
> **R:** Total customer impact was about 70 minutes. We shipped the atomic flip and the version assertion that week, and I added the "mixed index generation" case to the eval suite so it can't silently return. I also wrote the runbook entry, because I'd had to reconstruct the migration steps from Slack history during the incident, which cost us twenty minutes we didn't have.

*Why this works: rollback before root-cause is the correct on-call instinct, and interviewers specifically listen for it.*

---

### Model answer 4 — "Tell me about a time you disagreed with a senior person"

> **S:** Our architect wanted to fine-tune a model on our internal documentation to answer product questions, and had already socialized it with the client as the plan.
>
> **T:** I thought it was the wrong approach, and I was the one who'd have to build it.
>
> **A:** I didn't argue it in the meeting — I asked for a week and built the comparison. I stood up a RAG baseline in three days, and generated ~1,200 Q&A pairs from the docs to fine-tune a smaller model as the fair test of his approach, then ran both against the same 200-question golden set, graded as answer accuracy against the frozen SME answers. I was careful about which cost I was quoting: the fine-tuning *job* itself ran in a few hours and cost on the order of a hundred dollars — that was never the problem. The problem was the *cycle*: data regeneration, eval, and sign-off put it at roughly two weeks from "docs changed" to "new model serving," and our documentation changed weekly. Then I brought one slide: RAG at 0.86, updatable in minutes, around $600/month at pilot volume; the fine-tune at 0.79 on the same set, a two-week change cycle, no way to cite a source, and it still confidently answered about anything added after the snapshot it was trained on. The mechanism matters and I said it explicitly — fine-tuning reliably teaches a model *how* to behave, but it's a poor and unauditable way to install *what* it knows. I framed the whole thing as "here's what I found" rather than "you were wrong," and I flagged the case where his approach *would* win — a consistent output format and house tone — which we later did use a small fine-tune for.
>
> **R:** We went with RAG, and shipped roughly six weeks earlier than the fine-tuning plan would have allowed. The architect was the one who presented the change to the client. What I learned: with a senior stakeholder, data moves the decision and opinion just moves the temperature — and leaving them a way to be right about something is what keeps the relationship intact.

*Why this works: it separates job cost from cycle cost (the distinction most candidates fumble), gives the mechanism rather than the slogan, and concedes the one case where the other person was right.*

**Gotcha:** If you use this story, do not say "fine-tuning takes two weeks" unqualified. Any interviewer who has run a fine-tune knows the job finishes in hours; the two weeks is your organisation's data-prep-and-approval loop. Say which one you mean and the answer lands as experience instead of hearsay.

---

## 3. "Tell Me About Yourself"

**Rules:** 90-120 seconds. Present → past → why here. No childhood, no full CV chronology. End by handing them a hook.

**Skeleton:**

```
[1] NOW      "I'm a <role> with <N> years in Python backend, and for the last
              <M> I've been building <GenAI/agentic systems> — currently at
              <company> where I <one-line scope>."
[2] PROOF    "Most recently I built <system> that <business outcome with a number>.
              My part was <specific components>."
[3] RANGE    "Before GenAI, my background is <backend/APIs/data> — <one line
              that shows engineering depth, not just LLM glue>."
[4] WHY HERE "I'm looking for <specific thing Virtusa offers> — <enterprise-scale
              GenAI across regulated clients / breadth of domains> — which is why
              this role stood out."
[5] HOOK     "Happy to go deep on any part of that — the retrieval design is
              probably the most interesting piece."
```

**Worked example:**

> "I'm a senior Python engineer with just over six years' experience, and for the last two I've been focused on Generative AI — designing and shipping RAG and agentic systems on Azure OpenAI. At my current company I own the AI services layer: FastAPI backends, retrieval pipelines, and the agent orchestration on top.
>
> The system I'm proudest of is a support knowledge assistant over about 40,000 internal documents. I owned the retrieval layer and the evaluation harness — hybrid search with reranking took us from 0.71 to 0.89 hit-rate@5, and average handle time dropped from around 12 minutes to 7.
>
> Before GenAI my background is straight backend engineering — high-throughput REST APIs, Postgres, async Python, the usual production concerns — which I think matters, because most GenAI systems fail on ordinary engineering problems rather than model problems.
>
> What draws me to Virtusa is the enterprise scale and the range of client domains. I've built one system deeply; I'd like to build them across banking, healthcare, and retail, where the compliance and data-boundary constraints are genuinely hard.
>
> Happy to go deep wherever you'd like — the retrieval and evaluation side is probably the most interesting."

**Practice this out loud three times before you go.** Not in your head — out loud. The first spoken run is always 40% worse than the version in your head, and you don't want that run to be in the room.

---

## 4. Services-Company Specific

### Q11. How do you handle ambiguous or changing requirements?

`[MEDIUM]`

**Answer:** "I convert ambiguity into written assumptions rather than waiting for clarity. I'll write down what I'm assuming, share it with the client contact, and start building the part that's true under every interpretation. For a GenAI project specifically, I push to get a small golden set defined early — nothing forces a client to say what 'good' means faster than asking them to grade twenty sample answers."

**Gotcha:** Never answer this with "I ask for clear requirements." In services, unclear requirements are the job, not an obstacle to it.

---

### Q12. How do you work with an onsite/offshore split?

`[MEDIUM]`

**Answer:** Concrete mechanics beat platitudes: overlap-window discipline (defend the 2-3 hours you share, use it for decisions not status), written-first communication so decisions survive the timezone gap, a daily async handoff note, and explicit ownership so no ticket waits on a person who's asleep. "The failure mode is a two-day round trip on a five-minute question — the fix is writing down enough context that the answer doesn't need a follow-up."

---

### Q13. A client asks for something you know is technically wrong. What do you do?

`[HARD]`

**Answer:** "I state the concern once, clearly, with the consequence and a number if I have one — 'this will roughly triple our per-query cost and I don't think it improves accuracy; here's a cheaper option.' Then, if they still want it, I build it. It's their system and their budget. What I do insist on is writing the trade-off down in the design doc so nobody's surprised in three months."

**Gotcha:** Panels are testing whether you're either a pushover or a blocker. The correct shape is: *disagree with evidence, commit fully, document the decision.*

---

### Q14. Tight deadline and you won't make it. What do you do?

`[MEDIUM]`

**Answer:** "Escalate early with options, not just a problem. The moment my own burndown says I'm going to miss — the week the trend turns, not the week before delivery — I go with three options: cut scope to X and hit the date, keep scope and slip by N days, or add a person and hit the date but pay a handover cost that makes them slower for the first week. I state a recommendation and I say which risk each option carries." Add one concrete example if you have it.

**Gotcha:** The tell they're listening for is *when* you escalated, not how you recovered. "I flagged it three weeks out" scores; "I worked weekends and just about made it" reads as someone who hides bad news until it's expensive. Also be ready for the follow-up on adding people — say Brooks' law in your own words rather than the name: on a late project, a new person costs the team more in ramp-up than they return in the short term, so it only works if the work genuinely splits.

---

### Q15. How do you handle scope creep?

`[MEDIUM]`

**Answer:** "I don't say no; I make the cost visible. Every addition goes into the backlog with an estimate, and the conversation becomes 'this is two days — what moves out to make room?' That reframes it from me refusing work to the client choosing priority, which is the honest framing anyway."

---

### Q16. Have you mentored juniors?

`[EASY]`

**Answer:** Give a specific mechanism, not a claim. "I onboarded two engineers onto the GenAI work. What worked was pairing on their first real ticket, then reviewing their PRs with questions rather than corrections — 'what happens if the retrieval returns nothing here?' rather than 'add a null check.' I also wrote a one-page 'how our RAG pipeline works' doc, mostly because I was tired of explaining it four times."

---

### Q17. How do you estimate work you've never done before?

`[MEDIUM]`

**Answer:** "I timebox a spike first — two or three days to remove the biggest unknown — then estimate. For GenAI work I estimate the engineering honestly and flag the *quality* work separately, because 'build a RAG pipeline' is two weeks and 'make a RAG pipeline good enough for a bank' is two months. Conflating those is how these projects blow up."

**Gotcha:** This answer scores very well in services interviews because it's the #1 way GenAI PoCs turn into failed deliveries — the demo takes two weeks and the last 10% of quality takes six months. Naming that shows you've actually shipped one.

---

### Q18. Are you comfortable with production support / on-call?

`[EASY]`

**Answer:** Yes, with a mechanism: "I've been on a rotation. What I care about is that on-call is survivable — runbooks for the top failure modes, alerts that mean something, and every incident producing either a fix or a regression test. I've written runbooks for the systems I've owned."

---

### Q19. What if the GenAI project ends and you're put on legacy Python maintenance?

`[MEDIUM]`

**Answer:** They ask this because it happens. "I'd take it. Most of my career has been ordinary backend work and I'm good at it. I'd want an honest conversation about the horizon — a quarter of maintenance between GenAI engagements is normal in services; two years of it would be a different conversation. But I'm not precious about only touching the shiny thing."

**Gotcha:** Answering "I only want to work on GenAI" gets you rejected at a services company. So does answering "anything is fine" — that reads as no direction. Take it, with a stated horizon.

---

### Q20. How do you keep up with a field that moves this fast?

`[EASY]`

**Answer:** Be specific and modest in volume. "I read provider changelogs and release notes for the things I actually run — that's where breaking changes live. Beyond that: a small number of engineering blogs, and I rebuild something small when a technique looks relevant, because reading about reranking and implementing it are different amounts of understanding. I don't try to track everything; most of it doesn't survive six months."

---

## 5. Conflict, Failure, Pressure, Feedback

### Q21. Tell me about a time you failed.

`[MEDIUM]`

**Answer:** Pick a real failure with an owned cause and a systemic fix. Strong shape: "We shipped a PoC that demoed brilliantly and then landed badly with real users, because our test questions were written by us and real users asked messier, shorter, more ambiguous questions. I owned that — I'd built the test set from documentation instead of from actual support tickets. We rebuilt the golden set from real ticket history, scores dropped to 0.6 overnight, and the next six weeks of work were on the things that actually mattered. Now I refuse to build an eval set from anything but real user language."

**Gotcha:** Do not pick a failure caused entirely by someone else, and do not pick one with no consequence. "I once worked too hard" is a non-answer that costs you credibility.

---

### Q22. Tell me about difficult feedback you received.

`[MEDIUM]`

**Answer:** Show you changed something. "A tech lead told me my design docs were unreadable — I was writing them for myself, all implementation detail and no framing. It stung because I thought thoroughness was the point. I started opening every doc with a three-line summary and a decision table, and putting the detail in an appendix. Review turnaround went from days of back-and-forth to one pass."

---

### Q23. How do you handle pressure?

`[EASY]`

**Answer:** Mechanism, not temperament. "I get narrow and written. Under pressure I write the list, pick the one thing that unblocks the most, and communicate status more often than feels necessary — because most of the pressure in an incident comes from stakeholders not knowing what's happening. During our index migration incident I posted an update every fifteen minutes even when the update was 'still investigating,' and it kept people out of the war room."

---

### Q24. A teammate isn't pulling their weight. What do you do?

`[MEDIUM]`

**Answer:** "Talk to them first, privately, and assume there's a reason before assuming there isn't — usually there is. If it's a skill gap I'll pair. If it doesn't change and it's affecting delivery, I raise it with the lead as a delivery risk, factually, without making it a character claim." Never answer this by going straight to the manager, and never by saying you'd cover for them indefinitely.

---

### Q25. What's your biggest weakness?

`[EASY]`

**Answer:** Real, bounded, with an active mitigation. Good options: "I over-engineer early — I'll build the abstraction before I have two use cases. I've started forcing myself to write the dumb version first and refactor at the second caller." Or: "I under-communicate when I'm deep in a problem; I set a calendar nudge to post status even when there's nothing exciting to say."

**Gotcha:** "Perfectionism" and "I care too much" are read as evasion. So is naming a weakness that's core to the job ("I'm not great at Python").

---

## 6. HR & Logistics

### Q26. Why Virtusa?

`[EASY]`

**Answer:** Three ingredients: scale, domain range, and something specific to the role. "Two things. First, enterprise scale across regulated domains — the GenAI problems I find interesting aren't model problems, they're data-boundary, ACL and compliance problems, and that's what building for banks and healthcare clients forces you to solve properly. Second, this role is explicitly agentic AI rather than generic Python, and that's the direction I've been deliberately moving for two years. The Chennai base also works for me long-term."

**Gotcha:** Do not say "I've heard good things" or recite their revenue. Do not say "for the brand."

---

### Q27. Why are you leaving your current company?

`[EASY]`

**Answer:** Forward-looking, never bitter. "I've built one GenAI system deeply and I've hit the ceiling of what that one product needs — the interesting problems there are solved. I want breadth: different domains, harder compliance constraints, and more agentic work than my current roadmap has room for."

**Gotcha:** Never criticize your current employer, manager, or colleagues. Even if it's justified and even if the interviewer invites it — especially then.

---

### Q28. What's your notice period? (JD says immediate to August joiners preferred)

`[EASY]`

**Answer:** Be exact and honest, then show flexibility with a concrete lever. "My official notice is 60 days from resignation. There are two levers I can try — offsetting unused leave and buying out the balance — and my read is 30-45 days is realistic, though I'd want to confirm both with HR rather than commit to a date I haven't checked. I'd start that conversation the day I have an offer in hand." If you can genuinely join immediately, say so plainly — it is a real advantage for this posting.

**Gotcha:** Check your own policy tonight before you promise either lever. Leave-against-notice offset is at the employer's discretion and plenty of Indian IT employers refuse it outright; buyout is usually at *your* cost unless the hiring company agrees to reimburse, and reimbursement is a negotiated exception rather than a standard benefit — raise it at the offer stage, not now. Do not overpromise a date you cannot hit: a retracted joining date is the fastest way to lose an offer and a reference simultaneously.

---

### Q29. What's your expected CTC? (JD says "as per company standards")

`[MEDIUM]`

**Answer:** Deflect once, then give a researched range with a reason. 

> First deflection: "I'd like to understand the role's scope a bit better first — but I'm sure we can align, and I'm not looking to make this the sticking point."
>
> If pressed: "My current fixed is ₹X. Given this is a senior GenAI role with 6+ years expected, I'd be looking at ₹Y to ₹Z fixed, and I'm flexible on the split between fixed and variable."

Rules: **name a range, not a point**, anchor on total fixed (not CTC-with-inflated-variable), and know your floor before you walk in. Never say "as per company standards" back at them — that hands them the entire negotiation.

Know the difference between the two numbers before you quote either. Indian CTC routinely bundles the employer's PF contribution, gratuity, and a performance-variable component that pays out at the company's discretion — so a headline CTC can sit 15-25% above what actually reaches you as fixed pay, and the gap varies by employer. Quote your range on **fixed**, say you're quoting fixed, and ask for their breakup in writing at the offer stage.

**Gotcha:** If they ask for a current salary slip, that's normal in Indian IT services; have the last 3 months' payslips with you. Do not inflate your current CTC — offer letters get verified in background checks and a mismatch voids the offer.

---

### Q30. Are you comfortable with hybrid work in Chennai?

`[EASY]`

**Answer:** Direct yes, with logistics that prove you've thought about it. "Yes — I'm based in / relocating to Chennai and Navalur is a manageable commute for me. I'd want to know the expected office days so I can plan around OMR traffic, but hybrid suits how I work." If relocating: state the timeline and that you'll handle it yourself.

---

### Q31. Where do you see yourself in 3-5 years?

`[EASY]`

**Answer:** Ambitious but plausible within *their* structure. "Technically deeper rather than away from the code — I'd like to be the person who owns the GenAI architecture for a large client engagement end to end, and mentors the engineers building it. Lead/architect track rather than pure people management, at least for the next few years."

---

### Q32. Do you have other offers / are you interviewing elsewhere?

`[MEDIUM]`

**Answer:** Honest, unpanicked, non-adversarial. "I'm in process with a couple of other companies, yes — nothing signed. Virtusa is the one I'm most interested in because of the agentic AI focus, so if there's a way to keep the timelines aligned I'd appreciate that." Do not fabricate a competing offer; if they call the bluff by asking for details, you lose all leverage at once.

---

### Q33. Explain the gap in your CV. / Why did you switch jobs frequently?

`[MEDIUM]`

**Answer:** One sentence of fact, one sentence of what you did with it, then move on. Do not over-explain — length reads as guilt. "I took four months off for a family medical situation in 2024; I used part of it to work through the LangChain/LangGraph ecosystem properly, which is what got me into agentic work." For frequent switches: name the pattern honestly and say what you're optimizing for now ("the last two moves were both for GenAI scope; I'm looking to stay put and go deep now").

---

### Q34. Any certifications?

`[EASY]`

**Answer:** If yes, name them with the exam code — Microsoft Certified: Azure AI Engineer Associate (**AI-102**) and Azure Solutions Architect Expert (**AZ-305**) are the ones most relevant to this stack. If no: "None currently — I've prioritized shipping over certification, but AI-102 is the one that maps directly to this stack and I'd be happy to take it." Never apologize at length.

**Gotcha:** Don't wave certifications off entirely either. They rarely decide a *senior technical* hire on their own, but services firms have a real commercial interest in them — cloud partner tiers are tied to certified headcount, and certified staff can be easier to bill onto client engagements. So "I'd be happy to take it" is a genuinely useful thing to say here, not just politeness. And only claim a certification you actually hold; they are trivially verifiable and turn up in background checks.

---

## 7. Questions YOU Ask Them

Ask 3-4. Having none reads as disinterest. Pick from these by whoever's in the room.

**Technical / role**
1. "What does the GenAI stack look like today — Azure OpenAI throughout, or multi-provider?"
2. "Is this role building a product/accelerator, or client-facing delivery on engagements?"
3. "How are you handling evaluation? Is there a shared harness across engagements or does each project build its own?"
4. "Which agent framework has actually stuck for you in production — LangGraph, Semantic Kernel, something in-house?"
5. "What's the split between greenfield GenAI work and integrating into existing enterprise systems?"

**Team / ways of working**
6. "How large is the team, and what's the onsite/offshore split?"
7. "Who would I be working with day to day, and who makes the architecture calls?"
8. "How much client interaction does this role have — am I in the room with them or behind a BA?"
9. "What does the first 90 days look like for someone in this seat?"

**Growth / honesty probes**
10. "What's the hardest problem the team is stuck on right now?" — the answer tells you more than the JD did.
11. "How do people move from senior engineer to architect here — what does that path actually look like?"
12. "What's the biggest thing that would make you say, a year from now, that this hire went really well?"

**Close with:** "Is there anything about my background you'd like me to go deeper on before we finish?" — it surfaces doubts while you can still address them.

---

## 8. Red Flags / Do NOT say

- **"I did everything on that project."** — On a team project, panels probe until this collapses. Own two things deeply.
- **Any criticism of your current employer, manager, or teammates.** — The interviewer will nod along and mark you down. Zero exceptions.
- **Fabricated metrics.** — "We got 95% accuracy." On what set, measured how, versus what baseline? One follow-up and the whole interview is now suspect.
- **"As per company standards"** in reply to the CTC question. — You've given away the negotiation and signalled you don't know your worth.
- **Overpromising a joining date.** — Say the real notice period and the real lever. A blown joining date is worse than a longer one.
- **"I only want to work on GenAI."** — Services companies staff you where the demand is. Say yes with a stated horizon instead.
- **"I'd just use the latest GPT / LangChain for that."** — Tool-first answers read as junior. Problem → constraint → choice → trade-off. Naming a model version that has already been superseded compounds it, so if you name a model at all, name the one you actually ran and say when.
- **Bluffing a technical answer.** — In a face-to-face round the follow-up is immediate. Calibrated uncertainty is a *positive* signal in an AI role, which is literally about not hallucinating.
- **No questions at the end.** — Reads as no interest.
- **Rambling past 3 minutes on any one answer.** — Answer, land it, stop. Let them steer. If they want depth they'll ask.
- **Bringing up salary before they do.** — Let them raise it. If they don't, ask at the end whether they'll cover comp in a later round.
- **Reciting your CV chronologically for "tell me about yourself."** — They have the CV. Give them the narrative.

---

## 9. F2F Day Mechanics

**Venue:** Virtusa Consulting Services Pvt. Ltd., 34, IT Highway, Navalur, Chennai — 600130. **Date: 01/08/2026.**

**Carry:**
- 3 printed copies of your CV
- Photo ID (Aadhaar/PAN/passport) — mandatory for gate entry
- Last 3 months' payslips, current offer/appointment letter, previous relieving letters
- Educational certificates (some Virtusa drives check these at L1)
- Pen and a plain notebook — useful for design questions and for noting their names
- Water, and something to eat; walk-in/scheduled drives routinely run long

**Timing:** Navalur is on OMR. Traffic is genuinely unpredictable — **leave 90 minutes early.** Arriving 30 minutes early and waiting is free; arriving late is not recoverable.

**Dress:** Business formals or smart formals. Services companies are more conservative than product startups on this; overdressing costs you nothing.

**Whiteboard etiquette:**
1. **Restate the problem** in your own words and confirm. Costs 20 seconds, prevents solving the wrong thing.
2. **State assumptions out loud** and write them in a corner of the board.
3. **Brute force first**, with its complexity. Then optimize. Jumping to the clever answer and getting stuck looks far worse.
4. **Narrate continuously.** Silence for 90 seconds reads as stuck. "I'm thinking about whether a hash map helps here — the trade-off is memory."
5. **Leave whitespace.** Write on the top-left third; you will need room to fix things.
6. **Test your code out loud** on one small example and one edge case before saying you're done.
7. **Take the hint.** If an interviewer nudges, they are helping you pass. Say "ah — yes, that's better because…" and take it.

**When you don't know — the 3-step recovery (use it verbatim):**
1. **Say what you do know adjacent to it.** "I haven't used AutoGen in production; I've built the equivalent supervisor pattern in LangGraph, so let me tell you how I'd map it."
2. **Say how you'd find out.** "I'd check the current docs for the exact API — I know the shape is a group chat with a manager agent routing turns."
3. **Ask a question that shows you understand the problem.** "Is the concern here the orchestration model, or the code-execution sandboxing?"

Never bluff a library API in a room where someone has used it last week. Calibrated uncertainty is a *hiring signal* for an AI role.

**Micro-habits that matter:** get the interviewers' names and use them once; ask permission before writing on their whiteboard; if you realize mid-answer you were wrong, say so immediately and correct it — self-correction reads as strength, not weakness; and at the end, ask about next steps and timelines.

---

## Rapid-Fire (last 10 min before you walk in)

- **First 30 seconds of "tell me about yourself"?** — Present role, years, GenAI focus. Not childhood, not chronology.
- **How long should any behavioral answer be?** — 90 seconds to 2 minutes. Land it and stop.
- **"I" or "we"?** — "I" for your work, "we" for the team's. Never blur; they probe it.
- **Project deep-dive opener?** — Business problem and its cost, not the tech stack.
- **No metrics for your project?** — Say so honestly, give the proxy you *do* have. Never invent numbers.
- **Asked about a tech you haven't used?** — Adjacent experience → how you'd find out → clarifying question.
- **Asked why you're leaving?** — Forward-looking growth reason. Zero criticism of the current employer.
- **Asked your expected CTC?** — Deflect once, then a researched *range* on fixed pay. Never "as per standards."
- **Asked your notice period?** — Exact number + the lever (leave offset / buyout) + a realistic joining date.
- **Asked about a weakness?** — Real, bounded, with an active fix. Not perfectionism.
- **Asked about failure?** — Owned cause, systemic fix, what you now refuse to repeat.
- **Disagreeing with a senior?** — Disagree with data, commit fully, document the decision.
- **Client asks for something wrong?** — Say it once with the cost, then build it, and write the trade-off down.
- **Put on legacy maintenance?** — Yes, with a stated horizon. Not "only GenAI," not "anything's fine."
- **Ambiguous requirements?** — Write assumptions down, build what's true under all readings, force a golden set early.
- **How many stories should be ready?** — Five: shipped-something-hard, incident, disagreement, failure, mentoring.
- **Questions at the end?** — Always 3-4. "What's the hardest problem the team is stuck on right now?" is the best one.
- **What do you carry?** — 3 CVs, photo ID, 3 payslips, relieving letters, certificates, pen, notebook.
- **When do you leave home?** — 90 minutes early. OMR traffic decides interviews it was never invited to.
- **Last thing before you walk in?** — Say your 2-minute intro out loud once, and remember: answer first, then elaborate, and bring every abstract answer back to something you actually built.
