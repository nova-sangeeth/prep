# Financial Services Integration — the domain layer this JD is built on

> EY GDS — DE-Cloud Integration Platform Engineer (Req 1724333, 4–8 yrs) · EY **Digital Engineering**, Financial Services

**What this file buys you in the interview:** EY markets itself as *"the only professional services organization who has a separate business dedicated exclusively to the financial services marketplace."* This req sits inside it. You have **no FS background** — and you do not need one. What you need is to say *cut-off*, *reconciliation break*, *maker-checker*, *pacs.008*, *T+1*, *WORM* without hesitating, and to show that the constraints an FS client cares about are constraints you have already engineered for. Domain vocabulary is the cheapest credibility available in eight hours: it is what separates a generic integration engineer from someone a bank will let into a design review. This is a **breadth** file. One line per concept, not a chapter.

**How to use it:** 45 minutes total. Read §0 (the honest-framing rule — this is the highest-value paragraph in the file), memorise the §2 standards table well enough to *recognise* the acronyms, read §4 (patterns) and §5 (the six design-review questions) properly, skim §6, then rehearse §8 out loud. Everything else is recognition-only.

**Bridge from your stack:** an FS integration is a FastAPI service with three extra non-functionals bolted on — *every state change is append-only*, *every request carries an idempotency key*, and *every deployment must be provably the reviewed artefact*. You have built idempotent APIs. You have built append-only event stores. You have built pipelines. FS just makes them non-negotiable and asks an auditor to check.

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 0 | [The honest-framing rule — read first](#0-the-honest-framing-rule--read-first) | — |
| 1 | [The FS landscape by industry group](#1-the-fs-landscape-by-industry-group) | Q1–Q5 |
| 2 | [The standards you must recognise](#2-the-standards-you-must-recognise) | Q6–Q12 |
| 3 | [Regulation that changes architecture](#3-regulation-that-changes-architecture) | Q13–Q21 |
| 4 | [FS-specific integration patterns](#4-fs-specific-integration-patterns) | Q22–Q31 |
| 5 | [The six questions an FS client asks in a design review](#5-the-six-questions-an-fs-client-asks-in-a-design-review) | Q32–Q37 |
| 6 | [Three worked designs](#6-three-worked-designs) | 3 |
| 7 | [EY Digital Engineering — how to talk about it](#7-ey-digital-engineering--how-to-talk-about-it) | Q38–Q40 |
| 8 | [Honest framing: 8 lines + 8 questions to ask](#8-honest-framing-8-lines--8-questions-to-ask) | — |
| 9 | [30-second whiteboard versions](#9-30-second-whiteboard-versions) | 3 |
| 10 | [Interviewer traps](#10-interviewer-traps) | 9 |
| 11 | [Rapid fire](#11-rapid-fire) | 40 |

Sibling files: [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md) · [API Design](01-api-design-rest-soap-graphql-openapi.md) · [Azure Integration Services](02-azure-integration-services.md) · [Messaging & Event Streaming](03-messaging-and-event-streaming.md) · [Microservices, Containers & K8s](04-microservices-containers-kubernetes.md) · [CI/CD, IaC & GitOps](05-cicd-iac-and-gitops.md) · [Auth & Security](06-auth-and-security.md) · [Python for Integration](07-python-for-integration-and-coding-round.md) · [System Design](08-system-design-integration.md) · [Behavioural, EY & HR](09-behavioral-ey-and-hr.md) · [GenAI → Integration Bridge](10-genai-to-integration-bridge.md)

---

## 0. The honest-framing rule — read first

**Never claim FS experience you do not have.** An FS interviewer at EY has spent a decade in banking. They will find the seam in ninety seconds, and once they do, every other answer you gave is re-scored downward. Worse, candidate reports from GDS interviews describe interviews **ended early** because answers kept improving across follow-ups and the panel suspected outside help. Treat that as a pattern to avoid rather than a documented fact — but the pattern is real, and bluffing a domain you don't have produces exactly it: a thin first answer that gets suspiciously better.

**The exact framing to use, verbatim:**

> "I have not worked in banking. But the constraints you are describing — an immutable audit trail, exactly-once *effect* on a payment, data residency — are ones I have built for. Here is how."

Then immediately give the *how*. That sentence only works if the next 30 seconds are concrete. It converts a gap into a bridge in one move: you concede the fact, you claim the capability, you prove the capability. Three beats.

**The three things that make this credible rather than evasive:**

1. **Name the constraint before they do.** "In an FS context I'd assume the audit trail is WORM and the retention is measured in years, not days — is that right for this client?" You are now asking their question for them.
2. **Have one real system to point at.** Your RAG/agent platform had immutable ingestion logs, idempotent tool calls, tenant data isolation and a deployment pipeline. Those are the same three properties. Use it. See [GenAI → Integration Bridge](10-genai-to-integration-bridge.md) for the mapping.
3. **Ask an intelligent question at the end** (§8). Domain fluency is demonstrated as much by the questions you ask as the answers you give.

**What you must never say:** "I've worked with payments" (you haven't), "we were PCI compliant" (you weren't in scope), "I've done ISO 20022" (you have not). One unverifiable claim destroys the file.

---

## 1. The FS landscape by industry group

The JD names EY's industry groups: **Asset Management, Banking and Capital Markets, Insurance, Private Equity**, plus Health, Government, Power and Utilities. You need one paragraph of vocabulary per group — enough to ask "which system is the book of record here?" and understand the answer.

### Q1. Walk me through the system landscape in a retail/commercial bank.
`[MEDIUM]` `[Banking & Capital Markets]`

**Answer:** At the centre is the **core banking system** — the book of record for accounts and balances (Temenos, Finacle, Flexcube, Mambu, or a mainframe). Everything else orbits it. Around that: **payment hubs** for the rails (NEFT/RTGS/UPI in India, ACH/Fedwire/RTP in the US, SEPA/TARGET2 in Europe, SWIFT for cross-border), **card systems** for issuing and acquiring, **treasury and liquidity** for the bank's own positions, **AML/sanctions screening**, **fraud scoring**, a **data warehouse** for regulatory reporting, and a growing layer of **digital channels** — mobile, internet banking, open-banking APIs — that talk to all of it through a middleware tier. That middleware tier is the job.

The critical mental model: **the core is slow, batched, expensive to change and often SOAP or a proprietary protocol; the channels are fast, JSON, and change weekly.** Integration exists to absorb that impedance mismatch — which is exactly the Anti-Corruption Layer pattern from [Azure Integration Services §1](02-azure-integration-services.md).

```text
  Channels (change weekly)          Middleware (you)                 Core (changes yearly)
  ─────────────────────────    ────────────────────────────    ──────────────────────────────
  Mobile app        ─┐         ┌─ APIM  (authn, throttle,   ┐   ┌─ Core banking (SOAP/MQ/COBOL)
  Internet banking  ─┤         │        versioning, quota)  │   ├─ Payment hub (ISO 20022)
  Open Banking API  ─┼──────►  ├─ Canonical model + ACL     ├─► ├─ Card platform
  Branch / teller   ─┤         ├─ Service Bus / Kafka       │   ├─ AML & sanctions (sync)
  Partner fintech   ─┘         └─ Batch bridge (SFTP→queue) ┘   └─ Data warehouse (T+1 batch)
```

**Capital Markets** adds: **OMS** (order management), **EMS** (execution management), **trading venues** reached over **FIX**, **market data** feeds, **post-trade** confirmation/allocation/settlement, **custodians**, and **clearing houses**. Different vocabulary, same shape.

**If they push back — "So what is actually hard about it?"** — Two things. First, the core usually cannot take channel-rate traffic, so you own load levelling, caching and a degraded-mode story. Second, the core's data model and the channel's data model disagree, and the canonical model in the middle is where every future change lands. Get the canonical model wrong and every integration after it pays interest.

---

### Q2. What does an Asset Management landscape look like?
`[MEDIUM]` `[Asset Management]`

**Answer:** The book of record splits in two, and that split *is* the integration problem. The **IBOR** (Investment Book of Record) — usually the OMS/PMS, e.g. Aladdin, Charles River, SimCorp, Bloomberg AIM — is what the portfolio manager trades against. The **ABOR** (Accounting Book of Record) — the fund administrator's portfolio accounting system, e.g. BNY, State Street, Northern Trust, Citco — is what the NAV is struck from. They will disagree every single night, and the nightly **position and cash reconciliation** between them is a first-class production system, not a script.

Around that: **custodians** (who actually hold the assets), **fund administrators** (who strike NAV and produce investor statements), **market data and pricing vendors**, **performance and risk analytics**, **transfer agents** (who own the investor register), and **regulatory reporting**.

| Term | One line |
|---|---|
| **NAV** | Net Asset Value — (assets − liabilities) ÷ units. Struck daily for most funds, on a hard deadline. |
| **IBOR vs ABOR** | Trade-date, real-time, PM's view vs settlement-date, accounting-grade, auditor's view. |
| **Break** | A discrepancy between two sources for the same position/cash line. Breaks are *worked*, not deleted. |
| **T+1 / T+2** | Settlement cycle. The **US moved on 28 May 2024**; **Canada, Mexico and Argentina moved a day earlier, 27 May 2024**, because 27 May was Memorial Day in the US and not a holiday there. **UK, EU and Switzerland move together on 11 October 2027** — ESMA, the UK Accelerated Settlement Taskforce and the Swiss Securities Post-Trade Council have a joint testing and readiness plan. Getting the split North American dates right is a cheap way to sound like you read the actual notices. |
| **Corporate action** | Dividend, split, merger. A notorious source of breaks because two systems apply it on different days. |
| **Custodian file** | Usually SWIFT MT535/536/537 or an ISO 20022 semt/sese equivalent, dropped over SFTP overnight. |

**If they push back — "Why can't they just use one system?"** — Because they answer different questions and different regulators. The IBOR must reflect an order the instant it's placed so the PM doesn't over-trade; the ABOR must only reflect what has legally settled, because the NAV is a number investors transact on. Merging them means one of the two becomes wrong. So you reconcile instead — which is why design #2 in §6 exists.

---

### Q3. What does an Insurance landscape look like?
`[MEDIUM]` `[Insurance]`

**Answer:** Four core platforms: **policy administration** (the book of record for the contract — Guidewire PolicyCenter, Duck Creek, Sapiens), **claims** (Guidewire ClaimCenter), **billing**, and **underwriting/rating**. Around them: **broker and agent portals**, **reinsurance** (ceding risk to a reinsurer, which needs bordereaux — periodic risk/premium/claims files), **actuarial and reserving**, **document generation**, and **regulatory reporting** (Solvency II in the EU, IRDAI in India, and **IFRS 17** as the insurance-contract accounting standard, effective for annual periods from 1 January 2023 — it is the reason many carriers rebuilt their actuarial data pipelines, so it is a live integration driver, not a historical footnote).

The integration texture is different from banking: **more file-based, more EDI, more partner-to-partner**. Insurance is a B2B industry where brokers, carriers and reinsurers exchange bulk files on schedules, so **EDI X12 / EDIFACT over AS2 or SFTP** is still the transport of record for a lot of it. In US health insurance specifically the X12 transaction sets are mandated: **834** benefit enrolment and maintenance, **837** health care claim, **835** claim payment/advice, **820** group premium payment.

```text
ISA*00*          *00*          *ZZ*SPONSOR123     *ZZ*CARRIER456     *260901*0930*^*00501*000000001*0*P*:~
GS*BE*SPONSOR123*CARRIER456*20260901*0930*1*X*005010X220A1~
ST*834*0001*005010X220A1~
BGN*00*REF20260901*20260901*0930****4~
N1*P5*ACME CORP*FI*123456789~
N1*IN*NORTHSTAR HEALTH*FI*987654321~
INS*Y*18*030*XN*A***FT~
REF*0F*123456789~
NM1*IL*1*PATEL*ARJUN****34*123456789~
DMG*D8*19880412*M~
HD*030**HLT*PLAN-GOLD~
DTP*348*D8*20260901~
SE*11*0001~
GE*1*1~
IEA*1*000000001~
```

Read it as: ISA/IEA is the interchange envelope, GS/GE the functional group, ST/SE the transaction set. `SE*11*` is the segment count including ST and SE. That is genuinely all you need to recognise an X12 file and not panic.

**If they push back — "Have you built an EDI integration?"** — No. I've built the equivalent shape: a partner drops a batch on an SFTP landing zone, we validate the envelope, split it into per-record messages onto a queue, process each idempotently, and emit an acknowledgement file plus a per-record status. In X12 terms the acknowledgement is a 997/999; in AS2 it's an MDN. The parser is the part I'd need to learn; the pipeline around it is the part I've already built twice.

---

### Q4. And Private Equity?
`[EASY]` `[Private Equity]`

**Answer:** Much smaller data volumes, much higher data sensitivity, and almost everything is document-shaped rather than message-shaped. The systems are **fund accounting** (Investran, eFront, Allvue), **CRM and deal flow**, **LP (Limited Partner) reporting portals**, **capital call and distribution notices**, and **valuation** for illiquid assets. Integration work is dominated by document ingestion, entity/investor master data, and periodic reporting packs — **ILPA templates** are the standard reporting format the industry converged on.

This is the group where your GenAI background is most obviously relevant: PE reporting is unstructured-document extraction at its core, which is exactly what Azure AI Document Intelligence is in the EY–Microsoft named stack. Say it once, in L2, not L1.

**If they push back — "Why is PE lower volume but harder?"** — Because there is no standard message. A bank exchanges pacs.008s that a machine validates against a schema. A PE fund exchanges a capital call notice as a PDF from a different template per GP. The hard part moves from throughput to extraction, entity resolution and human-in-the-loop review.

---

### Q5. What's the one integration question you'd ask in any FS engagement, regardless of industry group?
`[MEDIUM]` `[Consulting-shaped — L2]`

**Answer:** *"Which system is the book of record for this data, and who is allowed to change it?"* Everything follows. If the core banking system is the book of record for balances, my integration never computes a balance — it reads one, and any local copy is a cache with a stated staleness. If the fund administrator's ABOR is the book of record for NAV, my job is to reconcile against it, not to argue with it. Getting this wrong is how you end up with two systems that both think they're authoritative and a reconciliation that never closes.

The second question is *"what is the cut-off?"* — because in FS almost every flow has a deadline, and the deadline determines the architecture more than the throughput does.

**If they push back — "Isn't that just domain-driven design?"** — It is. FS just names it explicitly and puts a regulator behind it. "Book of record" is the FS word for aggregate root, and the difference is that in FS being wrong about it is a reportable event.

---

## 2. The standards you must recognise

**You are not expected to implement these.** You are expected to not be lost when someone says them. One line each. Learn to *recognise*, not to recite.

### Q6. What is ISO 20022 and why is everyone migrating to it?
`[MEDIUM]` `[HIGH-FREQUENCY — the single most likely FS standards question]`

**Answer:** ISO 20022 is the XML (and increasingly JSON) message standard that is replacing the old SWIFT MT and domestic proprietary formats across payments and securities. The reason everyone is moving is **structured, richer data**: an MT103 crams the remittance information into free-text lines, while a pacs.008 carries structured debtor/creditor parties, addresses, purpose codes and remittance data as discrete elements. That directly improves sanctions screening, AML, reconciliation and straight-through processing — which is why regulators pushed it rather than the banks.

**The state of play as of now:**

| Migration | Status |
|---|---|
| SWIFT cross-border, MT/MX coexistence | **Ended 22 November 2025** — but know the scope, because this is where people overstate it. In 2024 SWIFT **refocused** the November 2025 deadline onto **payment clearing and settlement** messages (the MT103/MT202 → `pacs` family, exchanged over FINplus); retirement of the MT **cash management and reporting** messages (MT940/MT942 → `camt`) and of MT payment initiation was **deferred beyond November 2025** with no confirmed date at the time of writing. So "MT is switched off" is wrong; "in-scope cross-border payment instructions must now be MX" is right. Non-compliant in-scope MT may be negatively acknowledged (NAK'd) by the network; SWIFT offers contingency processing, which nobody sane relies on as a primary path. |
| **Fedwire Funds Service** (US) | Migrated in a **single-day cutover on 14 July 2025**, retiring the proprietary FAIM format. Originally scheduled 10 March 2025, deferred. Scale for context: Fedwire Funds' **average daily value was ≈$4.59 trillion in 2025** (Federal Reserve annual statistics) — quote it as "about four and a half trillion a day", not a false-precision figure. |
| CHAPS, TARGET2, EBA, most domestic RTGS | Already migrated. |

**The message families — memorise these four letters, they are the whole vocabulary:**

| Family | Covers | Canonical examples |
|---|---|---|
| **pain** | **Pay**ment **in**itiation — customer → their bank | `pain.001` CustomerCreditTransferInitiation; `pain.002` payment status report |
| **pacs** | **Pa**yments **c**learing and **s**ettlement — bank ↔ bank | `pacs.008` FIToFICustomerCreditTransfer; `pacs.009` FI credit transfer (bank's own funds); `pacs.004` PaymentReturn (moves money back); `pacs.002` status report (does **not** move money) |
| **camt** | **Ca**sh **m**anagemen**t** — reporting back to the customer | `camt.053` bank-to-customer statement (replaces MT940/950); `camt.054` debit/credit notification |
| **sese / semt / setr** | Securities settlement, statements, trade | The securities analogues of MT54x / MT53x |

**Code example — a minimal but structurally correct `pain.001`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>MSG-2026-0901-0001</MsgId>
      <CreDtTm>2026-09-01T09:30:00+05:30</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>12500.00</CtrlSum>
      <InitgPty><Nm>ACME TRADING LTD</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMTINF-0001</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>12500.00</CtrlSum>
      <ReqdExctnDt><Dt>2026-09-01</Dt></ReqdExctnDt>
      <Dbtr><Nm>ACME TRADING LTD</Nm></Dbtr>
      <DbtrAcct><Id><IBAN>GB29NWBK60161331926819</IBAN></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BICFI>NWBKGB2L</BICFI></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId>
          <InstrId>INSTR-0001</InstrId>
          <EndToEndId>E2E-INV-88213</EndToEndId>
        </PmtId>
        <Amt><InstdAmt Ccy="EUR">12500.00</InstdAmt></Amt>
        <CdtrAgt><FinInstnId><BICFI>DEUTDEFF</BICFI></FinInstnId></CdtrAgt>
        <Cdtr><Nm>MUELLER GMBH</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>DE89370400440532013000</IBAN></Id></CdtrAcct>
        <RmtInf><Ustrd>INVOICE 88213</Ustrd></RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>
```

The two fields you should be able to name without looking: **`EndToEndId`** — the reference the originator sets, which survives the whole chain and is what reconciliation joins on (max 35 characters); and **`CtrlSum` / `NbOfTxs`** — the control totals that make the file self-checking. Those two ideas are the entire reason FS files reconcile and REST payloads don't.

**If they push back — "Isn't ISO 20022 just XML? What's the engineering difficulty?"** — The difficulty is that it's a *huge* schema with **market-specific usage guidelines** layered on top. A pacs.008 valid against the ISO schema can still be rejected by CBPR+, HVPS+ or a domestic scheme because that market restricts cardinalities, mandates optional fields and constrains code lists. So validation is two-stage: schema, then scheme rulebook. Practically that means the usage guideline is the contract, not the XSD — and I'd hold it in the repo alongside the code and test against it in CI, the same way I hold an OpenAPI spec.

---

### Q7. What SWIFT MT message types should I know?
`[EASY]` `[Recognition only]`

**Answer:** Enough to know which category you're looking at. The number's first digit is the category: 1xx customer payments, 2xx financial-institution transfers, 3xx treasury/FX, 5xx securities, 9xx cash management. The six that come up:

| MT | Name | ISO 20022 successor |
|---|---|---|
| **MT103** | Single Customer Credit Transfer — the classic cross-border payment | `pacs.008` |
| **MT202 / MT202COV** | General FI Transfer / cover payment. COV (2009) added traceability of the underlying customer payment through the cover leg. | `pacs.009` / `pacs.009 COV` |
| **MT940** | Customer Statement Message — end-of-day account statement | `camt.053` |
| **MT950** | Statement Message (to the account owner/bank) | `camt.053` |
| **MT535 / MT536 / MT537** | Statement of Holdings / Statement of Transactions / Statement of Pending Transactions | `semt.002` / `semt.017` / `semt.018` |
| **MT540–543 / MT544–547 / MT548** | Settlement instructions (Receive Free, Receive Against Payment, Deliver Free, Deliver Against Payment) / their confirmations / Settlement Status and Processing Advice | `sese.023` / `sese.025` / `sese.024` |

```text
{1:F01NWBKGB2LAXXX0000000000}{2:I103DEUTDEFFXXXXN}{4:
:20:REF20260901001
:23B:CRED
:32A:260901EUR12500,00
:50K:/GB29NWBK60161331926819
ACME TRADING LTD
LONDON
:57A:DEUTDEFF
:59:/DE89370400440532013000
MUELLER GMBH
FRANKFURT
:70:INVOICE 88213
:71A:SHA
-}
```

Read it as: block 1 = sender, block 2 = message type + receiver, block 4 = the fields. `:32A:` is value date (YYMMDD) + currency + amount with a **comma** decimal separator. `:50K:` ordering customer, `:59:` beneficiary, `:70:` remittance info as free text, `:71A:` charge bearer (SHA/OUR/BEN). Compare `:70:` free text against the structured `<RmtInf>` in the pain.001 above and you can explain the entire ISO 20022 business case in one sentence.

**If they push back — "MT is dead, why learn it?"** — Only the in-scope cross-border *payment instruction* messages ended coexistence in November 2025. MT is far from gone: **securities messaging (category 5) was never in that scope**, retirement of the **category 9 cash management and reporting** messages (MT940/MT942) was deferred past November 2025, many bilateral bank-to-corporate feeds still run on MT, and a large amount of *archived* data speaks MT. Translation layers between MT and MX will be in production for years. If a client hands me an MT parser to maintain, "it's deprecated" is not a delivery plan.

---

### Q8. What is FIX, and where does it show up?
`[EASY]` `[Capital Markets]`

**Answer:** FIX (Financial Information eXchange) is the messaging protocol for **pre-trade and trade** — orders, executions, quotes — between buy-side, sell-side and venues. It is a long-lived stateful TCP session with sequence numbers, heartbeats, gap fill and resend, carrying tag=value messages. Since FIX 5.0 the session layer (**FIXT 1.1**) and the application layer are versioned separately; the application layer has since moved from "FIX 5.0 SP2" to a rolling **"FIX Latest"** updated by cumulative Extension Packs. In practice you will still meet **FIX 4.2 and 4.4** in production far more often than anything newer.

```text
8=FIX.4.4|9=<len>|35=D|49=BUYSIDE01|56=SELLSIDE01|34=1090|52=20260901-09:30:00.000|
11=ORD-2026-0901-0001|21=1|55=INFY|54=1|38=5000|40=2|44=142.50|59=0|
60=20260901-09:30:00.000|10=<chk>|

35=D  NewOrderSingle      54=1   Side: Buy          40=2  OrdType: Limit
11    ClOrdID (yours)     38     OrderQty           44    Price
34    MsgSeqNum           55     Symbol             59=0  TimeInForce: Day
```

(`9=` BodyLength and `10=` CheckSum are computed by the engine — never hand-written. `|` is SOH, `0x01`, in the wire format. The first three tags must be `8`, `9`, `35` and the last must be `10`; the rest of the standard header follows the spec's order, `49`/`56` before `34`/`52`.)

**The one thing to say that sounds like you've been near it:** *"FIX sessions are stateful and sequence-numbered, so recovery is a resend request against a sequence gap, not an HTTP retry. That means a FIX gateway cannot be a stateless pod you scale horizontally — it's a singleton per session with sticky, ordered, durable state, and that changes how you deploy it on Kubernetes."* That is a genuinely senior observation and it ties straight to [Microservices, Containers & K8s](04-microservices-containers-kubernetes.md) — a FIX engine is a StatefulSet, not a Deployment.

**If they push back — "Why not just use REST for orders?"** — Latency and session semantics. REST gives you a new connection, no ordering guarantee across requests, and no built-in gap recovery. FIX gives you an ordered stream with an explicit recovery protocol over one long-lived connection. For order flow measured in microseconds with a legal obligation to prove what was sent, that matters.

---

### Q9. Give me one line each on the other standards.
`[EASY]` `[Recognition]`

| Standard | What it is | Where it shows up in an integration |
|---|---|---|
| **FpML** | XML standard for OTC derivatives, managed by ISDA. Rates, credit, equity, FX, commodities, securities, loans. | Trade capture and confirmation feeds between a bank and a derivatives platform. Big, deeply nested XML — you will be doing XSLT or a schema-generated binding. |
| **SEPA** | Single Euro Payments Area — euro credit transfers (SCT) and direct debits (SDD), IBAN-addressed, ISO 20022 natively. | The euro-area domestic rail. Rulebooks change annually. |
| **SEPA Instant / SCT Inst** | Instant euro payments, **10-second** end-to-end target. EU Instant Payments Regulation (EU) 2024/886: euro-area PSPs had to **receive from 9 Jan 2025** and **send + do Verification of Payee from 9 Oct 2025**; PSPs in **non-euro-area** Member States get later dates (receive 9 Jan 2027, send 9 Jul 2027). | Turns a batch-shaped bank into a 24/7 real-time one — no maintenance window, no "we're closed for end-of-day". Verification of Payee (name-vs-IBAN match) is a new *synchronous* hop before send, which eats your latency budget. |
| **UPI / NPCI** | India's real-time retail rail (UPI), plus IMPS, NEFT, RTGS, NACH, AePS. | The Indian domestic story. Standard per-day P2P limit is **₹1 lakh**, with higher limits for verified merchant and specific categories (capital markets, insurance, education, healthcare, IPO, government). *Verify current limits against the live NPCI circular before quoting a number.* |
| **ACH / Nacha** | US batch retail rail. Same Day ACH per-payment limit is **$1 million** (since 18 March 2022), rising to **$10 million effective 17 September 2027** (approved April 2026). | Batch files, windows, return codes (R01 insufficient funds, R02 account closed…). Returns arrive days later — your state machine must handle them. |
| **Fedwire** | US high-value RTGS. ISO 20022 since 14 July 2025. | Large-value, same-day-final, irrevocable. No "undo". |
| **EDI X12** | US B2B/EDI standard (ANSI ASC X12). 834/837/835/820 in health insurance; 850/810/856 in supply chain. | Batch files over AS2 or SFTP; envelope validation; 997/999 acknowledgements. |
| **EDIFACT** | The UN/ISO equivalent used outside the US. | Same shape, different syntax. |
| **AS2** | **RFC 4130** — "MIME-Based Secure Peer-to-Peer Business Data Interchange Using HTTP, Applicability Statement 2". S/MIME signing + encryption over HTTP(S), with **MDN** receipts (sync or async) giving **non-repudiation of receipt**. AS1 was the SMTP version. | The B2B transport of record. When a partner says "we'll send you an AS2 feed", they mean signed, encrypted MIME over HTTPS with a signed receipt. |
| **SFTP** | Still, genuinely, the most common FS file transport. | Landing zone → validate → split → queue. Design #2 in §6. |
| **MISMO** | Mortgage Industry Standards Maintenance Organization — a not-for-profit subsidiary of the Mortgage Bankers Association (est. 1999). XML/data standard across the US mortgage loan lifecycle; ULDD is the Fannie/Freddie delivery flavour. | Loan origination and delivery integrations. One line is enough. |
| **BCBS 239** | Basel Committee, Jan 2013 — "Principles for effective risk data aggregation and risk reporting". **14 principles** (11 for banks, 3 for supervisors) across governance & infrastructure, aggregation capability, reporting practices, supervisory review. | Why a bank will ask you for **end-to-end data lineage** on a feed. Say "BCBS 239" and a banking interviewer will assume you've been in the room. |

**If they push back — "Which of these have you actually used?"** — None of the FS-specific ones, and I'd rather say that plainly. What I have built is the layer underneath them: signed payloads, envelope and control-total validation, split-and-queue with idempotent consumers, acknowledgement generation, schema-versioned contracts enforced in CI. The format itself is a parser plus a usage guideline; the platform around it is the part that takes months, and that part is the same whether the payload is a `pacs.008` or a JSON event.

---

### Q10. What is straight-through processing, and why does an integration engineer care?
`[EASY]`

**Answer:** STP is the proportion of transactions that complete end-to-end without a human touching them. It is the number an FS client will actually hold you to, because every manual repair costs money and time. Integration decisions map directly onto it: rich structured data raises STP (that's the ISO 20022 argument), permissive validation lowers it (bad data gets in and fails downstream where repair is expensive), and a sanctions false positive drops a payment into a manual queue.

**If they push back — "How would you improve STP on a feed?"** — Measure first: classify every exception by reason code over a month and Pareto it. In every system I've seen, two or three causes are 80% of the repairs. Then fix at the earliest possible point — usually by tightening validation at the *ingress* so bad data is rejected to the sender with a precise error rather than accepted and repaired by an ops team at 2 a.m.

---

### Q11. What's the difference between clearing and settlement?
`[EASY]` `[Vocabulary check — get this right, it's a shibboleth]`

**Answer:** **Clearing** is agreeing what is owed — validating, matching, netting and confirming the obligation. **Settlement** is the actual, final transfer of value that discharges it. They are separate steps, often separated by days, and in an integration they are separate states with separate events. A payment can be cleared and still fail to settle.

**If they push back — "Give me the practical consequence."** — Your payment state machine must not collapse them. If your API returns "SUCCESS" when the payment is merely *accepted for clearing*, you have told the customer their money moved when it hasn't. The correct response is `202 Accepted` plus a status resource, and separate terminal states for cleared and settled. See [API Design](01-api-design-rest-soap-graphql-openapi.md) for the async request-reply shape.

---

### Q12. What is a nostro/vostro account? What is netting?
`[EASY]` `[Vocabulary]`

**Answer:** A **nostro** is "our account with you" — the account a bank holds at a correspondent bank in a foreign currency; **vostro** is the mirror, "your account with us". Cross-border payments move through them, and **nostro reconciliation** — matching the bank's own ledger against the correspondent's statement (camt.053/MT940) — is one of the biggest reconciliation workloads in banking. **Netting** is settling only the net difference between two parties instead of every gross obligation, which reduces settlement risk and liquidity needs; a clearing house does it at scale.

**If they push back — "Why does netting matter to you?"** — Because it changes what "a payment" means in the message flow. A netted rail means the individual instructions clear but a single aggregate settles, so your reconciliation joins many instruction-level records against one settlement record. If you designed a 1:1 join you're already wrong.

---

## 3. Regulation that changes architecture

This is the section that actually earns you the interview. Anyone can name a regulation; a platform engineer names the **architectural consequence**.

### Q13. What does "immutable audit trail" mean concretely, and how would you build one?
`[HARD]` `[HIGH-VALUE — this is the one to be genuinely good at]`

**Answer:** It means: every business-significant event is written once, is retrievable for a defined retention period, cannot be modified or deleted by anyone — **including an administrator** — and the record of who did what is itself part of the trail. Concretely I'd use **WORM object storage with a locked time-based retention policy**, append-only, with the application holding no delete permission at all. The regulatory anchors are SEC Rule **17a-4** for US broker-dealers, **FINRA 4511**, **CFTC 1.31(c)-(d)**, and **MiFID II Article 16(7)** in the EU.

**The retention numbers worth knowing:**

- **SEC 17a-4**: records preserved for **six years, with the first two in an easily accessible place**. The October 2022 amendments (effective 3 Jan 2023, compliance 3 May 2023) added an **audit-trail alternative** to strict WORM: instead of non-rewriteable/non-erasable media, you may use a system that logs every modification or deletion and can recreate the original record. That is a genuinely useful thing to know — it means an append-only, cryptographically-chained event store can be compliant, not just tape.
- **MiFID II Art 16(7)** (with Delegated Regulation 2017/565 Art 76): relevant telephone and electronic communications retained **five years, extendable to seven where the competent authority requests it**, in tamper-proof storage with full access traceability.

**Code — the paved-road module a platform engineer ships, not a one-off:**

```hcl
# modules/fs-audit-archive/main.tf
# Reusable WORM archive for FS integration audit trails. Every integration in the
# landing zone consumes this module; nobody hand-rolls a storage account.

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "retention_days" {
  type        = number
  description = "Time-based retention. 5 years = 1826 days; 6 years (SEC 17a-4) = 2191."
  default     = 2191
  validation {
    # Azure supports 1 day minimum, 146000 days (400 years) maximum.
    condition     = var.retention_days >= 1 && var.retention_days <= 146000
    error_message = "retention_days must be between 1 and 146000."
  }
}

variable "location" {
  type        = string
  description = "Must satisfy the client's data-residency clause."
  default     = "South India"
}

resource "azurerm_resource_group" "audit" {
  name     = "rg-int-audit-prod"
  location = var.location
}

resource "azurerm_storage_account" "audit" {
  name                          = "stintauditprod01"
  resource_group_name           = azurerm_resource_group.audit.name
  location                      = azurerm_resource_group.audit.location
  account_tier                  = "Standard"
  account_replication_type      = "GZRS"
  min_tls_version               = "TLS1_2"
  public_network_access_enabled = false
  shared_access_key_enabled     = false # Entra ID only. No shared key to leak or rotate.

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
  }
}

resource "azurerm_storage_container" "audit" {
  name                  = "integration-audit-log"
  storage_account_id    = azurerm_storage_account.audit.id
  container_access_type = "private"
}

resource "azurerm_storage_container_immutability_policy" "audit" {
  storage_container_resource_manager_id = azurerm_storage_container.audit.id
  immutability_period_in_days           = var.retention_days
  locked                                = true

  # Two DIFFERENT flags, and people conflate them:
  #   protected_append_writes_enabled     -> appends to APPEND blobs only
  #   protected_append_writes_all_enabled -> appends to BLOCK blobs too (SQL Backup to URL)
  protected_append_writes_enabled     = true
  protected_append_writes_all_enabled = false
}
```

**Hard numbers, verified against Microsoft Learn:** minimum retention interval **1 day**, maximum **146,000 days (400 years)**. An **unlocked** policy can be shortened, extended or deleted — it is for testing only. A **locked** policy can be **extended but never shortened**, and a container-level locked policy allows a **maximum of five increases** over its lifetime (version-level policies have no such limit). Microsoft had Cohasset Associates assess the feature against **SEC 17a-4(f), FINRA 4511 and CFTC 1.31(c)-(d)**. Container-level WORM is capped at **10,000 containers per account**, which is the usual reason to choose version-level WORM instead.

**If they push back — "What breaks when you lock it?"** — Two things, and I'd say both up front. First, **deletion**: once the policy is locked you can delete the container only if it is *empty*, and you cannot delete a blob until its effective retention has expired — so in practice the container, and the storage account holding it, are undeletable for the retention period. `terraform destroy` on that environment fails, and anyone who locks a policy in a sandbox has created a resource that outlives the project and bills for years. Second, **append semantics**: workloads that create a blob and then append to it fail against a plain locked policy. `protected_append_writes_enabled` re-permits appends to *append blobs*; you need `protected_append_writes_all_enabled` to cover *block* blobs as well, which is what patterns like SQL Backup to URL need. Both are the kind of thing you find in production if you didn't find them in design.

---

### Q14. Data residency — how do you design for it?
`[HARD]` `[India-relevant; near-certain if the client is Indian FS]`

**Answer:** Residency is a *deployment topology* constraint, not a feature you add later. You pin the region for compute, storage, backups, logs and — the one everyone forgets — **the monitoring and telemetry sinks**. Then you enforce it with policy in the platform, not with a wiki page: the built-in **"Allowed locations"** Azure Policy definition (`listOfAllowedLocations` parameter) assigned at **management-group** scope with a `Deny` effect, plus its sibling **"Allowed locations for resource groups"** — assign only the first and someone can still create an RG in the wrong region. Then run the same check in CI against the Terraform plan, so a non-compliant region fails the pull request instead of failing at apply.

**The three regimes to know:**

| Regime | The rule | Architectural consequence |
|---|---|---|
| **RBI payment data localisation** | Circular *Storage of Payment System Data*, **6 April 2018**, six months to comply. The **26 June 2019 FAQ** clarified: processing abroad is permitted, but the data must be **deleted from the foreign systems and brought back to India within one business day or 24 hours from processing, whichever is earlier**. Applies to full end-to-end transaction detail, customer data, payment-sensitive data and payment credentials. | You may run a cross-border processing hop, but you own a **repatriate-and-purge** job with evidence. Most teams conclude it's cheaper to just keep everything in an Indian region. Your DR pair must also be in India. |
| **India DPDP** | DPDP Act 2023; the **DPDP Rules 2025 notified 13 November 2025**, phased: Data Protection Board immediately; consent-manager provisions **+12 months (13 Nov 2026)**; the substantive obligations **+18 months (13 May 2027)**. | Consent capture, purpose limitation, breach notification, and erasure rights become enforceable obligations on a known clock. Design for them now; they land in 2027. |
| **GDPR** | Chapter V transfer rules; SCCs; Art 17 erasure. | Cross-border transfer needs a lawful mechanism, and your logs count as personal data if they carry identifiers. |

**If they push back — "What about a global SaaS the client already uses?"** — Then residency becomes a contract and a data-flow question rather than a deployment one, and it is the client's legal team's call, not mine. My job is to produce the **data flow map** — for each hop: what data, which jurisdiction, which legal basis, what retention — and to be able to show it. That map is the deliverable an FS client actually wants from an integration engineer, and it's a thing I'd build once as a template and reuse across the practice.

---

### Q15. PCI DSS — how do you reduce scope?
`[HARD]` `[The correct answer is counter-intuitive; this is a trap question]`

**Answer:** The correct answer is: **you keep the PAN out of your systems entirely.** Every system that stores, processes or transmits cardholder data is in scope for PCI DSS assessment, and scope is expensive — segmentation, quarterly scans, penetration testing, an annual assessment. So the design goal is not "secure the PAN"; it is "never hold the PAN". You do that with **tokenisation** at the edge — the customer's card details go directly from the browser or app to a PCI-certified payment service provider via a hosted field, iframe or SDK, and your systems only ever see an opaque token. Your integration then transmits a token that is worthless if stolen.

**Current version state:** PCI DSS **v3.2.1 retired 31 March 2024**; **v4.0 retired 31 December 2024**; **v4.0.1** (published 11 June 2024) is the active version. Of the 64 new requirements in v4.x, the **51 future-dated ones became mandatory on 31 March 2025**.

**If they push back — "But we need the card number for refunds/recurring billing."** — You need a *reference* to the card, not the card. The PSP's token supports refund, recurring and card-on-file. If a genuine business case requires part of the PAN — say, a routing decision on the BIN — take a **truncated** value: PCI SSC's truncation guidance permits at most the **first six (or first eight, for longer PANs) plus the last four**, and never more than 12 digits in total, at which point it is no longer a PAN. Better still, ask the PSP for a BIN attribute on the token so you hold nothing. The moment you say "let's just store it encrypted", you have brought your whole platform into scope and added key management, key rotation and an annual assessment to your roadmap.

---

### Q16. Right-to-be-forgotten versus an immutable ledger — resolve it.
`[HARD]` `[Genuinely good discussion question — expect this from a strong interviewer]`

**Answer:** They only look contradictory if you conflate the *transaction record* with the *personal data attached to it*. GDPR Article 17 gives a right to erasure, but **Article 17(3)(b)** exempts processing necessary "for compliance with a legal obligation which requires processing by Union or Member State law", and **17(3)(e)** exempts "the establishment, exercise or defence of legal claims". A bank has a statutory obligation to retain transaction records — so the ledger entry stays. What must go is the personal data that isn't required to be retained.

**The engineering answer is separation plus crypto-shredding:**

1. **Split the stores.** The ledger holds a `party_id` and financial facts. A separate **party/PII store** holds name, address, contact details, keyed by `party_id`.
2. **Erasure deletes from the PII store, not the ledger.** The ledger keeps a referentially-intact but now-anonymous `party_id`. Balances still foot; the audit trail still reconstructs; the human is no longer identifiable.
3. **For PII you were forced to embed in an immutable payload** (an archived pacs.008 in WORM storage, say), use **crypto-shredding**: encrypt the PII fields with a per-subject data key held in a key vault, and on erasure destroy the key. The ciphertext remains in the immutable object, satisfying WORM; the plaintext is unrecoverable, satisfying erasure. Regulators broadly accept irreversible key destruction as equivalent to deletion — but I'd get that confirmed by the client's privacy counsel rather than assert it, because it's a legal judgement, not an engineering one.
4. **Log the erasure itself** as an event in the audit trail. "We deleted her data" must itself be provable.

**If they push back — "Isn't crypto-shredding just a workaround?"** — It's a trade-off with a stated risk: it depends on the key being genuinely destroyed everywhere, including backups of the key vault, and on the cipher not being broken within the retention window. I would document both. The alternative — not writing PII into immutable objects in the first place — is strictly better, so I'd design for tokenised references in the archive and treat crypto-shredding as the remediation for data I inherited, not the pattern for new data.

---

### Q17. What is SOX separation of duties, and how does it constrain a CI/CD pipeline?
`[HARD]` `[Ties directly to the heaviest block of this JD]`

**Answer:** SOX (Sarbanes-Oxley) requires that controls over financial reporting be effective and evidenced. For a deployment pipeline that lands as three concrete constraints: **the person who writes a change cannot be the person who approves it**, **the person who approves it cannot be the person who can bypass the approval**, and **there must be an auditable record linking the change in production to the approval**. In practice: no direct push to `main`, protected branches with required reviewers from a different group than the author, no standing production write access for humans, and deployment performed by an identity that only the pipeline holds.

**Config — the platform-level guardrails, expressed as policy rather than process:**

```yaml
# .github/workflows/deploy-prod.yml (the audit-relevant fragment)
name: Deploy integration service to production

on:
  push:
    tags: ["v*.*.*"]

permissions:
  contents: read
  id-token: write        # OIDC federation to Azure. No long-lived secret in the repo.
  packages: write        # REQUIRED to push to ghcr.io — omit it and the push 403s
  attestations: write    # SLSA provenance attached to the image

jobs:
  release:
    runs-on: ubuntu-latest
    environment:
      name: production   # GitHub environment protection rule = the four-eyes gate
      url: https://payments.int.example.com
    steps:
      - uses: actions/checkout@v5

      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      # Without this the buildx --push below cannot authenticate to the registry.
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        id: build
        run: |
          set -euo pipefail
          IMAGE="ghcr.io/${{ github.repository }}/payment-adapter"
          docker buildx build --push -t "$IMAGE:${{ github.ref_name }}" \
            --metadata-file /tmp/meta.json .
          echo "digest=$(jq -r '."containerimage.digest"' /tmp/meta.json)" >> "$GITHUB_OUTPUT"

      # v4 is the current major; from v4 it is a thin wrapper over actions/attest,
      # which is what GitHub now points new workflows at.
      - name: Attest build provenance
        uses: actions/attest-build-provenance@v4
        with:
          subject-name: ghcr.io/${{ github.repository }}/payment-adapter
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

The controls an auditor can actually test: branch protection requires a review from `@payments-approvers` (a group the authors are not in); the `production` GitHub environment requires a named reviewer and records who clicked; the pipeline authenticates by **OIDC federation** so no human holds production credentials; and the image is **attested**, so the artefact in the registry is cryptographically bound to the commit and workflow that built it. Full pipeline detail lives in [CI/CD, IaC & GitOps](05-cicd-iac-and-gitops.md).

**If they push back — "Emergency fix at 2 a.m. — now what?"** — A documented break-glass path, not an exception culture. Break-glass is a separate, alerting, time-boxed elevated role (PIM with a maximum activation window and mandatory justification), the change still goes through the pipeline, and the retrospective approval is recorded within an agreed SLA. The audit finding is never "you deployed at 2 a.m."; it's "you deployed at 2 a.m. and nobody can tell me who authorised it".

---

### Q18. Sanctions and AML screening — where does it sit in the flow?
`[MEDIUM]` `[Design-shaping]`

**Answer:** **Sanctions screening is a synchronous, blocking hop before the payment leaves.** It is not an enrichment you can do asynchronously, because the legal obligation is to *not send* a payment to a sanctioned party — once it's gone, you've committed the offence. So the flow is: validate → screen → release, and if screening is down, the payment **stops**. Fail-closed, always. That is the opposite of nearly every availability instinct you have, and saying it out loud is a strong signal.

Screening returns one of three outcomes: **clear** (continue), **hit** (block, route to a compliance investigation queue, and note that in many jurisdictions you must not tell the customer why), or **timeout/error** (treat as a hit, hold the payment, alert).

**Code — the blocking hop, with the FS-correct failure mode:**

```python
# sanctions.py — the one place in the platform where a circuit breaker must NOT fail open.
from __future__ import annotations

import asyncio
from enum import Enum

import httpx

# Persistence helpers live in the payment repository module; both are async and
# both are idempotent on payment_id, so a redelivered instruction re-holds cleanly.
from payments.repository import hold_for_investigation, mark_released


class ScreeningOutcome(str, Enum):
    CLEAR = "CLEAR"
    HIT = "HIT"
    UNAVAILABLE = "UNAVAILABLE"


class ScreeningHeld(Exception):
    """Payment must be held. Never converted into a success by a caller."""


_TIMEOUT = httpx.Timeout(connect=2.0, read=5.0, write=2.0, pool=2.0)


async def screen(client: httpx.AsyncClient, payload: dict) -> ScreeningOutcome:
    try:
        r = await client.post("/v1/screen", json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
    except (httpx.HTTPError, asyncio.TimeoutError):
        # Fail CLOSED. An unscreened payment is a regulatory breach, not a degraded UX.
        return ScreeningOutcome.UNAVAILABLE
    return ScreeningOutcome.CLEAR if r.json()["matches"] == [] else ScreeningOutcome.HIT


async def release_or_hold(client: httpx.AsyncClient, payment_id: str, payload: dict) -> None:
    outcome = await screen(client, payload)
    if outcome is ScreeningOutcome.CLEAR:
        await mark_released(payment_id)
        return
    reason = "sanctions_hit" if outcome is ScreeningOutcome.HIT else "screening_unavailable"
    await hold_for_investigation(payment_id, reason)
    raise ScreeningHeld(reason)
```

**Fraud scoring is the opposite.** It is an **asynchronous enrichment** on most flows: score the payment, and if the score crosses a threshold, act — hold, step-up authentication, or reverse. Fraud is a risk-management judgement with a false-positive cost; sanctions is a binary legal obligation. Different placement, different failure mode. Being able to state that distinction in one sentence is the whole answer to this question.

**If they push back — "Screening adds 300 ms to every payment. The business is complaining."** — Then we cache and pre-screen, we don't skip. Beneficiary screening results for a known, unchanged counterparty can be cached with a TTL tied to the sanctions-list update frequency; new beneficiaries are screened at *setup* time rather than payment time; and list-refresh triggers a re-screen of the cached population as a batch. That keeps the synchronous path short without ever sending an unscreened payment.

---

### Q19. What is maker-checker / four-eyes, and how does it show up in integration?
`[MEDIUM]`

**Answer:** Maker-checker (dual control, four-eyes) means a second authorised human must approve an action before it takes effect, and the maker cannot be the checker. In FS it applies to high-value payments, standing-instruction changes, beneficiary additions, limit changes — and, per Q17, production deployments.

**The integration consequence:** the approval is a **state in your workflow, not a UI feature.** Your payment resource has an `AWAITING_APPROVAL` state, an approval is an event with an actor identity and a timestamp, the approval is idempotent (a double-click must not create two approvals), and the maker's identity is compared against the checker's *by the service*, not by the front end. If you let the UI decide, you've built a control that a `curl` bypasses.

**If they push back — "Where do you enforce the maker ≠ checker rule?"** — In the service, against the authenticated principal from the token, and I'd also assert it as a database constraint on the approval row (`CHECK (approver_id <> maker_id)`) so it holds even if a future code path forgets. Controls that exist in exactly one layer are controls that get regressed.

---

### Q20. If AI touches a decision in an FS flow, what changes?
`[MEDIUM]` `[Your card — use it in L2]`

**Answer:** Model risk management applies. In FS, a model that influences a credit, pricing, fraud or suitability decision is a governed artefact: it needs documented purpose, validation evidence, monitoring for drift, a human-review path for adverse decisions, and **explainability** proportionate to the impact. The architectural consequences are concrete: version the model and the prompt as deployable artefacts alongside the code; log the full decision context — inputs, model version, retrieved context, output, confidence — into the same immutable audit store as everything else; and never let a model be the *final* authority on a decision with a customer-adverse outcome without a human path.

**If they push back — "So can you use an LLM in a bank at all?"** — Yes — EY and Microsoft committed over a billion dollars to exactly that in May 2026. But the safe pattern is to put the model where it *assists* rather than *decides*: document extraction with a confidence threshold and human review below it, summarisation for an investigator, retrieval to surface the right rulebook clause. That is also the honest read on EY's own multiagent framework inside EY Canvas — it augments 130,000 Assurance professionals, it doesn't replace the sign-off. See [GenAI → Integration Bridge](10-genai-to-integration-bridge.md).

---

### Q21. What is DORA and why should an integration platform engineer care?
`[MEDIUM]` `[EU-relevant; EY sells resilience work]`

**Answer:** DORA — the EU Digital Operational Resilience Act — **entered into force 16 January 2023 and applies from 17 January 2025**. It puts ICT risk for EU financial entities on a statutory footing: ICT risk management, incident classification and reporting, **digital operational resilience testing**, and — the part that touches you — **ICT third-party risk**, including a mandatory **Register of Information** of every contractual arrangement with an ICT third-party provider, maintained at entity, sub-consolidated and consolidated level and submitted to the competent authority. It is already live, not theoretical: competent authorities had to pass the first Registers of Information to the ESAs by **30 April 2025**, and the ESAs designated the first **critical ICT third-party providers (CTPPs)** — whom they then oversee directly — from **July 2025**. The major cloud and SaaS providers are on that list, which is the point for us.

**Why it matters to an integration engineer:** every SaaS you integrate, every cloud service you provision, every managed broker becomes an entry someone has to justify, and concentration risk becomes a design input. "Can we exit this provider?" becomes a question you must be able to answer with an actual plan, which pushes you toward portable abstractions — AMQP over a proprietary SDK, Kubernetes over a lock-in PaaS — where the cost is acceptable.

**If they push back — "So should we avoid managed services?"** — No. DORA doesn't ban dependency, it bans *unmanaged* dependency. The answer is to be deliberate: document the dependency, know the exit path and its cost, test the degraded mode, and make the choice consciously. I'd rather run Azure Service Bus with a documented, tested exit to AMQP-compatible alternatives than run my own broker badly.

---

## 4. FS-specific integration patterns

### Q22. Can you guarantee exactly-once delivery?
`[HARD]` `[NEAR-CERTAIN — and most candidates get it wrong]`

**Answer:** **No — exactly-once *delivery* is impossible over an unreliable network, and anyone who claims it is selling something.** The sender cannot distinguish "the message was lost" from "the acknowledgement was lost", so it must retry, so duplicates are inevitable. What is achievable — and what a bank actually needs — is **exactly-once *effect***: at-least-once delivery combined with an idempotent consumer, so that N deliveries of the same message produce exactly one state change. That distinction is the whole answer, and stating it in the first sentence is what separates a senior answer from a junior one.

The three mechanisms that produce exactly-once effect:

1. **An idempotency key on the write path** — a client-supplied key, stored with a uniqueness constraint, so the second attempt returns the first result instead of doing the work again.
2. **A deduplication table on the read path** — insert the event ID into a `processed_event` table in the *same transaction* as the side effect. If the insert conflicts, the effect already happened.
3. **The transactional outbox** — write the business row and the outbox row in one local transaction, then relay to the broker separately, because writing to a database and a broker is not atomic.

**Code — idempotency on a payment initiation API. This is the single most useful snippet in this file.**

```python
# payment_idempotency.py — exactly-once EFFECT for a payment initiation API.
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()
router = APIRouter()


async def get_session() -> AsyncSession:
    """Provided by the app's sessionmaker. Declared here so the route below is
    complete: FastAPI needs a Depends() for a non-Pydantic parameter, otherwise it
    tries to parse AsyncSession out of the request body and fails at import time."""
    ...


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_key"

    key = Column(String(255), primary_key=True)
    request_fingerprint = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class PaymentInitiation(BaseModel):
    debtor_iban: str = Field(min_length=15, max_length=34)
    creditor_iban: str = Field(min_length=15, max_length=34)
    amount_minor: int = Field(gt=0)              # minor units. NEVER float for money.
    currency: str = Field(min_length=3, max_length=3)
    end_to_end_id: str = Field(max_length=35)    # ISO 20022 EndToEndId is max 35 chars


def fingerprint(payload: BaseModel) -> str:
    canonical = json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def post_to_ledger_and_enqueue(
    session: AsyncSession, body: PaymentInitiation, key: str
) -> str:
    payment_id = str(uuid.uuid4())
    await session.execute(
        text(
            "INSERT INTO ledger_entry "
            "  (entry_id, payment_id, account_iban, direction, amount_minor, currency, posted_at) "
            "VALUES (:dr_id, :pid, :dr_acct, 'DR', :amt, :ccy, now()), "
            "       (:cr_id, :pid, :cr_acct, 'CR', :amt, :ccy, now())"
        ),
        {
            "dr_id": str(uuid.uuid4()), "cr_id": str(uuid.uuid4()), "pid": payment_id,
            "dr_acct": body.debtor_iban, "cr_acct": body.creditor_iban,
            "amt": body.amount_minor, "ccy": body.currency,
        },
    )
    # Transactional outbox: same transaction as the ledger write. A relay publishes it.
    await session.execute(
        text(
            "INSERT INTO outbox (outbox_id, aggregate_id, event_type, payload, created_at) "
            "VALUES (:oid, :pid, 'PaymentInitiated', CAST(:body AS jsonb), now())"
        ),
        {
            "oid": str(uuid.uuid4()), "pid": payment_id,
            "body": json.dumps({"paymentId": payment_id, "idempotencyKey": key,
                                **body.model_dump()}),
        },
    )
    return payment_id


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    body: PaymentInitiation,
    response: Response,
    session: AsyncSession = Depends(get_session),
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, Any]:
    fp = fingerprint(body)

    claim = (
        pg_insert(IdempotencyRecord.__table__)
        .values(key=idempotency_key, request_fingerprint=fp,
                created_at=datetime.now(timezone.utc))
        .on_conflict_do_nothing(index_elements=["key"])
    )
    result = await session.execute(claim)

    if result.rowcount == 0:
        # Key already claimed: either a genuine replay, or key reuse with a new payload.
        prior = (
            await session.execute(
                select(IdempotencyRecord).where(IdempotencyRecord.key == idempotency_key)
            )
        ).scalar_one()
        if prior.request_fingerprint != fp:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Idempotency-Key reused with a different payload",
            )
        if prior.response_body is None:
            # Original request is still in flight. Do NOT execute a second time.
            raise HTTPException(status.HTTP_409_CONFLICT, "Request in progress; retry later")
        response.status_code = prior.status_code
        return json.loads(prior.response_body)

    payment_id = await post_to_ledger_and_enqueue(session, body, idempotency_key)
    payload = {"paymentId": payment_id, "status": "ACCP", "endToEndId": body.end_to_end_id}

    await session.execute(
        IdempotencyRecord.__table__.update()
        .where(IdempotencyRecord.key == idempotency_key)
        .values(status_code=201, response_body=json.dumps(payload))
    )
    # One commit: ledger + outbox + idempotency record are atomic together.
    await session.commit()
    return payload
```

Three details an interviewer will look for and most candidates miss: the **fingerprint check** (same key + different body is a client bug and must be a 422, not a silent replay of the wrong answer), the **in-flight 409** (a concurrent duplicate must not execute twice while the first is still running), and **one commit** covering the business write, the outbox and the idempotency record.

**If they push back — "Kafka says it does exactly-once. Are you wrong?"** — Kafka's exactly-once semantics are exactly-once *within Kafka*: an idempotent producer plus transactions plus `isolation.level=read_committed` give you exactly-once read-process-write across Kafka topics. `enable.idempotence` has defaulted to `true` since Kafka 3.0, which also forces `acks=all`, `retries > 0` and `max.in.flight.requests.per.connection <= 5`. But the moment your side effect leaves Kafka — a database write, a call to the core banking system, an SMS — the transaction doesn't cover it, and you are back to idempotent consumers. So: exactly-once inside the log, exactly-once effect outside it. See [Messaging & Event Streaming](03-messaging-and-event-streaming.md).

*(Keep the version story current if Kafka comes up at all: **ZooKeeper was removed entirely in Kafka 4.0, released March 2025** — KRaft is the only supported mode, and a bank still on 3.x has a ZooKeeper-to-KRaft migration on its roadmap. Saying "we'd run ZooKeeper for the quorum" in 2026 dates you instantly.)*

---

### Q23. Show me the idempotent consumer on the read side.
`[MEDIUM]`

**Answer:** Insert the event ID into a dedupe table in the **same transaction** as the side effect, then commit the broker offset **after** the database commits. Never auto-commit offsets in a financial consumer — auto-commit means the offset can move past a message you haven't finished processing.

```python
# settlement_consumer.py — at-least-once delivery, exactly-once effect.
from __future__ import annotations

import json

import psycopg
from confluent_kafka import Consumer, KafkaException, TopicPartition

CONSUMER_CONF = {
    "bootstrap.servers": "kafka-cin-01:9093",
    "group.id": "settlement-poster",
    "enable.auto.commit": False,           # commit only after the DB transaction succeeds
    "isolation.level": "read_committed",   # never read aborted transactional writes
    "auto.offset.reset": "earliest",
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "OAUTHBEARER",
    # OAUTHBEARER needs a token callback; librdkafka will not acquire one for you.
    # e.g. "oauth_cb": lambda cfg: (entra_access_token(), expiry_epoch_seconds)
}


def apply_settlement(conn: psycopg.Connection, event: dict) -> None:
    conn.execute(
        "UPDATE payment SET state = 'SETTLED', settled_at = %s "
        "WHERE payment_id = %s AND state = 'CLEARED'",
        (event["settledAt"], event["paymentId"]),
    )


def run() -> None:
    consumer = Consumer(CONSUMER_CONF)
    consumer.subscribe(["payments.settled.v1"])
    try:
        with psycopg.connect("postgresql://app@pg-prod/ledger") as conn:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                event = json.loads(msg.value())
                with conn.transaction():
                    inserted = conn.execute(
                        'INSERT INTO processed_event (event_id, topic, partition, "offset") '
                        "VALUES (%s, %s, %s, %s) ON CONFLICT (event_id) DO NOTHING",
                        (event["eventId"], msg.topic(), msg.partition(), msg.offset()),
                    ).rowcount
                    if inserted:
                        apply_settlement(conn, event)   # the side effect, exactly once

                consumer.commit(
                    offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)],
                    asynchronous=False,
                )
    finally:
        consumer.close()
```

**If they push back — "The dedupe table grows forever."** — Partition it by day and drop partitions older than the maximum possible redelivery window plus a safety margin — typically the topic retention period. The table only needs to remember long enough that a replay cannot outlive it. If the business requires replaying a year of history, the dedupe table isn't the right control for that path; a deterministic rebuild into a fresh projection is.

---

### Q24. Why must an integration never mutate a posted ledger entry?
`[MEDIUM]` `[HIGH-VALUE — the double-entry answer]`

**Answer:** Because the ledger is the evidence. A posted entry is a historical fact: on this date, this amount moved between these accounts. If you can `UPDATE` it, then every balance derived from it is unprovable and the audit trail is fiction. So the ledger is **append-only**, and a correction is expressed as a **new, offsetting entry that references the original** — a reversal, not a delete. Double-entry gives you the integrity check for free: every transaction posts equal debits and credits, so the whole ledger must always sum to zero, and a system that can't foot has a bug you can detect automatically.

```sql
-- Enforce append-only at the database, not just in the application.
REVOKE UPDATE, DELETE ON ledger_entry FROM app_writer;

-- Belt and braces: even a privileged mistake becomes a no-op.
CREATE RULE ledger_entry_no_update AS ON UPDATE TO ledger_entry DO INSTEAD NOTHING;
CREATE RULE ledger_entry_no_delete AS ON DELETE TO ledger_entry DO INSTEAD NOTHING;

-- A reversal is a NEW pair of entries pointing at the originals.
INSERT INTO ledger_entry (entry_id, payment_id, account_iban, direction,
                          amount_minor, currency, posted_at, reverses_entry_id)
SELECT gen_random_uuid(),
       e.payment_id,
       e.account_iban,
       CASE e.direction WHEN 'DR' THEN 'CR' ELSE 'DR' END,
       e.amount_minor,
       e.currency,
       now(),
       e.entry_id
FROM ledger_entry e
WHERE e.payment_id = :payment_id
  AND e.reverses_entry_id IS NULL;

-- The invariant a monitoring job asserts every cycle: the ledger must foot.
SELECT payment_id,
       SUM(CASE direction WHEN 'DR' THEN amount_minor ELSE -amount_minor END) AS imbalance
FROM ledger_entry
GROUP BY payment_id
HAVING SUM(CASE direction WHEN 'DR' THEN amount_minor ELSE -amount_minor END) <> 0;
```

**If they push back — "What about a genuine data-entry error — wrong amount typed?"** — Still a reversal plus a re-post, and the audit trail shows all three events. The customer's statement will show the original, the reversal and the correction, and that is *correct behaviour* — the bank is obliged to show what happened, not a tidied version of it. Hiding the error is the compliance failure, not making it.

---

### Q25. Walk me through the payment state machine.
`[MEDIUM]` `[Vocabulary + design]`

**Answer:** Initiated → validated → authorised → cleared → settled, with returns and reversals as forward transitions rather than rollbacks.

```text
                            ┌──────────────────────────────┐
                            │        REJECTED (terminal)   │
                            └──────────▲───────────────────┘
                                       │ validation / screening / limits
  INITIATED ──► VALIDATED ──► AUTHORISED ──► CLEARED ──► SETTLED (terminal-ish)
      │             │             │              │            │
      │             │             │              │            └──► RETURNED ──► REVERSED
      │             │             │              └──► FAILED (downstream reject)
      │             │             └──► HELD (sanctions hit / maker-checker pending)
      │             └──► HELD
      └──► CANCELLED (only while not yet authorised)

  Rules that matter:
   • SETTLED is not "final" — a return can arrive days later (ACH R-codes, recall requests).
   • RETURNED and REVERSED are NEW ledger entries, never a delete of the originals.
   • CANCELLED is only reachable before authorisation. After that, it's a reversal.
   • Every transition is an event with an actor, a timestamp and a reason code.
```

**If they push back — "Why is SETTLED not terminal?"** — Because rails have return windows. An ACH debit can be returned for insufficient funds days after posting; a SEPA payment can be recalled; a card transaction can be charged back months later. If your model treats settlement as final, the return arrives and you have no state to move to, so someone opens a spreadsheet. Design the return path on day one — it's the path that gets exercised in production and never in the demo.

---

### Q26. Why do end-of-day batch and real-time both exist? Isn't batch legacy?
`[MEDIUM]` `[The "batch jobs using event streaming" line in the JD]`

**Answer:** No — batch exists because the *business* is batch. NAV is struck once a day. Interest accrues daily. Regulatory reports are periodic. Netting only makes sense over a window. Even a bank with fully real-time payments still has an end-of-day: a point where books close, a statement is produced, and reconciliation runs. So real-time and batch coexist permanently, and the integration job is to **bridge them**, not to abolish one.

**The modern bridge — and this is exactly what the JD's oddly-worded "Batch Jobs using event streaming" means** — is to stop treating batch as "cron plus a shared drive" and instead drive bulk workloads through the same async messaging backbone as everything else:

```text
  OLD                                    NEW
  ───────────────────────────────        ────────────────────────────────────────────────
  cron @ 02:00                           Event: file landed  (Event Grid / S3 notification)
    └─ SFTP pull                              └─ Validate envelope + control totals
       └─ 400k-row loop in one process           └─ Split into N messages onto a queue
          └─ dies at row 380k                       └─ Competing consumers, idempotent
             └─ rerun the whole thing                  └─ Failures → DLQ, not a full rerun
                └─ nobody knows how far it got            └─ Progress + completion event
```

The wins are the ones an FS client cares about: **restartability** (a poison record doesn't kill the run), **observability** (you can answer "how far did it get?"), **backpressure** (the consumer pool throttles to what the core banking system can absorb), and **the same code path for a real-time single item and a batch of 400,000**. Add a **control-total check** — the file's declared record count and sum must equal what you processed — and you have a batch bridge an auditor will accept.

**If they push back — "Doesn't per-message overhead make that slower than a bulk load?"** — Yes, for the happy path, and I'd measure it. If the window is tight I'd keep the split but process in **batched chunks** — one message per 1,000 rows, bulk-inserted — which keeps restartability and DLQ semantics while amortising the overhead. The thing I would not give up is the ability to answer "which records failed and why" without re-running the job.

---

### Q27. What are cut-off times and settlement windows, and how do they affect design?
`[MEDIUM]`

**Answer:** A cut-off is the time after which an instruction no longer makes today's processing cycle and rolls to the next business day. Every rail has them, they are in local time, and they interact with weekends and market holidays. Architecturally they mean three things: the **value date is computed, not supplied**; the system must behave differently either side of the cut-off; and **"the downstream is down at cut-off" is a designed-for scenario, not an incident**.

```python
# value_date.py — cut-off and business-day arithmetic. Times are illustrative:
# always take the real cut-offs from the client's rail schedule, they change.
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

CUTOFFS: dict[str, time] = {
    "RTGS": time(16, 30),
    "NEFT": time(18, 45),
}


def value_date(rail: str, submitted: datetime, holidays: set[date]) -> date:
    """Business date on which this instruction will actually be processed."""
    local = submitted.astimezone(IST)
    d = local.date()
    if local.time() >= CUTOFFS[rail]:
        d += timedelta(days=1)
    while d.weekday() >= 5 or d in holidays:   # Sat=5, Sun=6
        d += timedelta(days=1)
    return d
```

**Never store or compare these in UTC alone.** A cut-off is a wall-clock time in a market's timezone, and the offset changes under daylight saving in markets that observe it. Store the instant in UTC, but evaluate the cut-off in the market's zone.

**If they push back — "The downstream is down and cut-off is in 10 minutes. What happens?"** — This is the real question, and the answer is agreed with the business before go-live, not invented at 16:20. The options, in order: (1) queue and keep retrying until cut-off, since a queue-based design means nothing is lost; (2) at cut-off, stop retrying and **roll to the next value date** with an explicit customer-visible status change — never silently; (3) if the flow is genuinely time-critical, fail over to the secondary rail if the client has one. What you must not do is keep retrying past cut-off and let the payment settle a day late with the original value date, because that's a value-dating error and it's reportable.

---

### Q28. Why is reconciliation a first-class component?
`[MEDIUM]` `[HIGH-VALUE]`

**Answer:** Because in a distributed system with at-least-once delivery, compensating transactions and multiple books of record, **divergence is normal, not exceptional**. Reconciliation is the control that detects it. In FS it isn't a nightly script somebody wrote — it's a system with its own SLA, its own break workflow, its own ageing report and its own audit trail, because "the two systems disagreed and nobody noticed for a week" is a reportable control failure.

The design has five parts: **extract** both sides for a period, **normalise** to a canonical shape (currency, decimals, identifiers, timezone), **match** on a defined key with defined tolerance, **classify** the residual as break types, and **route** each break to an owner with an ageing clock.

```python
# reconcile.py — break detection between an IBOR (ours) and an ABOR (fund admin's).
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable


class BreakType(str, Enum):
    MISSING_IN_ADMIN = "MISSING_IN_ADMIN"
    MISSING_IN_PMS = "MISSING_IN_PMS"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    VALUE_TOLERANCE = "VALUE_TOLERANCE"


@dataclass(frozen=True)
class Position:
    fund_id: str
    isin: str
    as_of: str
    quantity: Decimal
    market_value: Decimal
    currency: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.fund_id, self.isin, self.as_of)


@dataclass(frozen=True)
class Break:
    key: tuple[str, str, str]
    type: BreakType
    ours: Decimal | None
    theirs: Decimal | None
    delta: Decimal | None


# Tolerance is a business agreement with the fund administrator, in the SLA. Not a magic number.
TOLERANCE_BPS = Decimal("1")


def reconcile(pms: Iterable[Position], admin: Iterable[Position]) -> list[Break]:
    left = {p.key: p for p in pms}
    right = {p.key: p for p in admin}
    breaks: list[Break] = []

    for k in left.keys() - right.keys():
        breaks.append(Break(k, BreakType.MISSING_IN_ADMIN, left[k].quantity, None, None))

    for k in right.keys() - left.keys():
        breaks.append(Break(k, BreakType.MISSING_IN_PMS, None, right[k].quantity, None))

    for k in left.keys() & right.keys():
        a, b = left[k], right[k]
        if a.quantity != b.quantity:
            breaks.append(
                Break(k, BreakType.QUANTITY_MISMATCH, a.quantity, b.quantity,
                      a.quantity - b.quantity)
            )
            continue
        if b.market_value == 0:
            continue
        drift_bps = abs(a.market_value - b.market_value) / b.market_value * Decimal(10_000)
        if drift_bps > TOLERANCE_BPS:
            breaks.append(
                Break(k, BreakType.VALUE_TOLERANCE, a.market_value, b.market_value,
                      a.market_value - b.market_value)
            )
    return breaks
```

Note `Decimal` throughout. Using a float for money in an FS interview is a disqualifying tell.

**If they push back — "What if a break is genuinely unexplainable?"** — Then it is aged, escalated and, if the business accepts it, **written off through an explicit adjustment entry with an approver** — never by quietly changing one side to match the other. The write-off is itself a posting with a maker and a checker. "Someone forced it to match" is the single worst answer available here.

---

### Q29. Market data fan-out and entitlements — what's the shape?
`[MEDIUM]` `[Capital Markets / Asset Management]`

**Answer:** High-volume, one-to-many, mostly non-durable — and **licensed**. Exchanges and vendors charge per user per feed and audit the counts, so **entitlement enforcement is a contractual and legal requirement, not an authorisation nicety**. The shape is: ingest from the vendor once, normalise, publish to a fan-out layer, and enforce entitlements at the edge — per-user, per-feed, per-instrument-class — while logging every access for the vendor audit.

The Azure mapping: **Event Hubs** (or Kafka) for the ingest and fan-out because you need high throughput and multiple independent consumer groups over the same stream; **Web PubSub / SignalR** for browser delivery; **APIM** for the request/response snapshot API with the entitlement policy; **Redis** for the latest-value cache so a new subscriber gets an immediate snapshot rather than waiting for the next tick.

```xml
<!-- APIM inbound policy: entitlement check on a market-data snapshot API -->
<policies>
  <inbound>
    <base />
    <validate-jwt header-name="Authorization"
                  failed-validation-httpcode="401"
                  failed-validation-error-message="Unauthorized"
                  output-token-variable-name="jwt">
      <openid-config url="https://login.microsoftonline.com/{{tenant-id}}/v2.0/.well-known/openid-configuration" />
      <audiences>
        <audience>api://marketdata</audience>
      </audiences>
    </validate-jwt>
    <!-- Escaping rule, and it trips everyone up once: a policy expression written
         inside an XML *attribute* (value="@(...)", condition="@{...}") must escape
         every double quote as &quot;, or the document is not well-formed and the
         import fails. An expression in *element content* (<set-body>@(...)</set-body>)
         does not — raw " is legal there, which is why the two blocks below differ. -->
    <set-variable name="feed" value="@(context.Request.MatchedParameters[&quot;feed&quot;])" />
    <choose>
      <when condition="@{
          var jwt = (Jwt)context.Variables[&quot;jwt&quot;];
          string[] ent = jwt.Claims.ContainsKey(&quot;entitlement&quot;)
              ? jwt.Claims[&quot;entitlement&quot;]
              : new string[0];
          return !ent.Contains((string)context.Variables[&quot;feed&quot;]);
      }">
        <return-response>
          <set-status code="403" reason="Forbidden" />
          <set-header name="Content-Type" exists-action="override">
            <value>application/problem+json</value>
          </set-header>
          <set-body>@("{\"type\":\"https://api.example.com/problems/not-entitled\",\"title\":\"Feed not entitled\",\"status\":403,\"detail\":\"No entitlement for feed "
                      + (string)context.Variables["feed"] + "\"}")</set-body>
        </return-response>
      </when>
    </choose>
    <rate-limit-by-key calls="600" renewal-period="60"
                       counter-key="@((string)context.Variables[&quot;feed&quot;] + &quot;|&quot; + context.Subscription.Id)" />
    <log-to-eventhub logger-id="marketdata-entitlement-audit">@(
      new JObject(
        new JProperty("ts", DateTime.UtcNow.ToString("o")),
        new JProperty("sub", ((Jwt)context.Variables["jwt"]).Subject),
        new JProperty("feed", (string)context.Variables["feed"]),
        new JProperty("op", context.Operation.Id)
      ).ToString(Newtonsoft.Json.Formatting.None)
    )</log-to-eventhub>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

Policy mechanics in depth live in [Azure Integration Services §3](02-azure-integration-services.md).

*One currency detail worth having ready, because it is the kind of thing an interviewer drops in:* the error body above is a **problem details** document. The spec is now **RFC 9457**, which obsoleted RFC 7807 in July 2023 — the media type is unchanged (`application/problem+json`) and 9457 mainly adds guidance plus the optional `errors` extension for multiple problems. Cite 9457, not 7807.

**If they push back — "Why not just filter in the client app?"** — Because the vendor audits *your* logs, not the client's good intentions, and an unentitled tick that reached a browser is a licence breach even if the UI hid it. Enforcement must be server-side, at the last hop you control, with an access log the vendor can be shown.

---

### Q30. What latency should each FS flow target?
`[MEDIUM]` `[Say ranges, not fake precision]`

**Answer:** I'd frame it by flow class rather than quoting a number I can't source, and I'd take the actual figure from the client's SLA. The orders of magnitude:

| Flow | Order of magnitude | Why |
|---|---|---|
| Market data tick distribution | microseconds–milliseconds | Competitive; co-located for latency-sensitive strategies |
| Order routing (FIX) | sub-millisecond–milliseconds | Execution quality |
| Card authorisation | hundreds of milliseconds; the scheme sets a hard timeout | Cardholder is standing at a terminal |
| Instant payment (UPI, SEPA Inst, RTP) | seconds. **SEPA Instant's regulatory target is 10 seconds end-to-end.** | Regulated user experience |
| Payment initiation API (customer-facing) | `202 Accepted` in < 1 s; settlement asynchronous | Never block the customer on clearing |
| Sanctions screening hop | tens–hundreds of ms, inside the payment budget | Synchronous and blocking |
| Nightly recon / NAV / regulatory report | minutes–hours, but a **hard deadline** | Deadline matters more than latency |

**If they push back — "What's the number for our payment API?"** — I wouldn't guess it. I'd ask what the customer-facing commitment is, decompose it into a per-hop budget, and find out which hop has the least headroom — usually the core banking call or the screening hop. Then the design conversation is about that hop, not about the whole flow.

---

### Q31. What is a compensating transaction, and how is it different from a rollback?
`[MEDIUM]`

**Answer:** A rollback undoes an uncommitted change inside a transaction boundary and leaves no trace. A compensating transaction is a **new, forward business action** that offsets an already-committed one, and it *does* leave a trace — because in FS the trace is the point. You cannot roll back a payment that has left the bank; you issue a return. You cannot roll back a posted ledger entry; you post a reversal. The saga pattern is the orchestration of those compensations across services.

The FS-specific subtlety: **compensation is not always available, and not always symmetric.** A Fedwire payment is final and irrevocable — the compensation is a *request* to the beneficiary bank to return funds, which they may refuse. So the design rule is: perform the irreversible step **last**, after everything reversible has succeeded. That single ordering rule prevents most saga pain.

**If they push back — "Give me the ordering in a payment."** — Reserve funds (reversible) → screen (no side effect) → maker-checker approval (reversible) → post to ledger (reversible via reversal) → **send to the rail (irreversible)** → await settlement confirmation. The rail call is last, it is idempotent on the end-to-end ID, and after it the only remaining path is a return, not a compensation.

---

## 5. The six questions an FS client asks in a design review

Memorise these six. They are the whole design review, and each has a one-sentence answer you should be able to give before elaborating.

### Q32. "Can you prove a message was delivered exactly once?"
**Answer:** No — and no honest engineer will tell you otherwise, because exactly-once *delivery* is impossible over an unreliable network. What I can prove is exactly-once **effect**: the message is delivered at least once, the consumer records the event ID in the same database transaction as the side effect, and a duplicate hits a uniqueness constraint and becomes a no-op. The proof is the dedupe table plus the ledger — for any event ID I can show you exactly one row of effect and exactly one set of postings. See Q22.

### Q33. "Can you replay a day?"
**Answer:** Yes, and it's designed in rather than improvised. Every inbound message is persisted verbatim to immutable storage before processing, keyed by correlation ID and business date, so replay reads from the archive rather than asking the counterparty to resend. Replay goes through the same idempotent consumer, so re-running a day is safe by construction — duplicates are absorbed, only genuinely missing effects apply. The two things I'd flag: replay must be able to target a *subset* (one file, one counterparty, one hour), and it must run against the same code version that failed, which is a GitOps question — I can check out the exact commit that was in production at that timestamp.

### Q34. "Who approved this deployment?"
**Answer:** Git can tell you, precisely, and that is the point of running deployments through GitOps rather than a console. The change is a pull request with a required review from someone who is not the author; merging it is what triggers deployment; the merge commit carries the approver's identity; and the production environment gate records who released it. There is no path to production that bypasses that, because no human holds write credentials to the cluster — the pipeline authenticates via workload-identity federation and the cluster reconciles from Git. See [CI/CD, IaC & GitOps](05-cicd-iac-and-gitops.md).

### Q35. "Where does this data physically live?"
**Answer:** In the regions named in the residency clause, and enforced by policy rather than convention. Every resource is provisioned from Terraform modules that take region as a validated input; the built-in **"Allowed locations"** and **"Allowed locations for resource groups"** Azure Policy definitions are assigned with a `Deny` effect at management-group scope, blocking anything else at the control plane; and the same check runs against the plan in CI so a non-compliant region fails the pull request rather than reaching production. The parts people forget and I'd call out explicitly: backups, geo-replication pairs, log and telemetry sinks, and any managed service with a global control plane.

### Q36. "What happens when the downstream is down at cut-off?"
**Answer:** Nothing is lost, and nothing settles late with the wrong value date. Instructions sit durably in a queue and retry with exponential backoff; at cut-off the retry loop stops and the payments roll to the next value date with an explicit, customer-visible status change and an operational alert. That behaviour is agreed with the business before go-live and tested, because it's the path that gets exercised. What I would not do is keep retrying past cut-off and let payments settle a day late carrying today's value date — that's a value-dating error and it's reportable. See Q27.

### Q37. "How do you prove to an auditor that the code running in production is the code that was reviewed?"
**Answer:** **This is precisely the GitOps argument, and it's the strongest single answer in this file.** The desired state of production lives in a Git repository, in a commit that carries the reviewer's approval. A controller in the cluster — Argo CD or Flux — continuously reconciles the cluster to that commit and reports drift. So the question "what is running?" has a Git answer, not a `kubectl` answer, and the answer is a commit SHA I can trace to a pull request, a reviewer and a build. Two things strengthen it further: workloads are pinned by **image digest**, not a mutable tag, so `:latest` can't quietly change what's running; and the image carries a **build provenance attestation** binding it to the commit and the workflow that produced it. If someone hand-patches a Deployment, the controller either reverts it or raises drift — either way, it's visible.

That chain — *reviewed commit → attested build → digest-pinned manifest → continuously reconciled cluster* — is the auditability story, and it happens to be the exact reason GitOps moved from "good to have" into this JD's explicit responsibility list. Full mechanics in [CI/CD, IaC & GitOps](05-cicd-iac-and-gitops.md).

---

## 6. Three worked designs

### Design 1 — Payment initiation, end to end, with the reversal path

**Requirement:** a corporate client initiates a payment from a portal. Validate, screen, approve, post, send to the rail, settle. Handle returns.

```text
                                                    ┌───────────────────────────────┐
  Client portal                                     │  IMMUTABLE AUDIT (WORM blob)  │
       │  POST /payments                            │  locked retention, append-only│
       │  Idempotency-Key: <uuid>                   └───────────▲───────────────────┘
       ▼                                                        │ every event, verbatim
  ┌─────────────┐  validate-jwt, rate-limit, schema-validate     │
  │    APIM     │────────────────────────────────────────────────┤
  └─────┬───────┘                                                │
        │ 202 Accepted + Location: /payments/{id}                │
        ▼                                                        │
  ┌──────────────────────────────────┐                           │
  │ Payment API (FastAPI, AKS)       │                           │
  │  1. idempotency claim  ─────────┐│                           │
  │  2. business validation         ││ ONE DB TRANSACTION        │
  │  3. DR/CR ledger entries        ││ (ledger + outbox +        │
  │  4. outbox row                  ││  idempotency record)      │
  └──────────────┬──────────────────┘│                           │
                 │  outbox relay      ▼                          │
                 ▼            ┌──────────────┐                   │
        ┌────────────────┐    │  PostgreSQL  │                   │
        │ Service Bus /  │◄───│  append-only │                   │
        │ Kafka topic    │    │  ledger      │                   │
        └───────┬────────┘    └──────────────┘                   │
                │                                                │
                ▼                                                │
   ┌───────────────────────────┐   SYNC, BLOCKING, FAIL-CLOSED   │
   │ Sanctions / AML screening │◄────────────────────────────────┤
   └──────┬──────────────┬─────┘                                 │
     CLEAR│              │HIT or UNAVAILABLE                     │
          │              ▼                                       │
          │      ┌──────────────────────┐                        │
          │      │ Compliance hold queue│  (human investigation) │
          │      └──────────────────────┘                        │
          ▼                                                      │
   ┌──────────────────────┐  maker ≠ checker, enforced in the    │
   │ Maker-checker gate   │  service AND as a CHECK constraint   │
   └──────┬───────────────┘                                      │
          ▼                                                      │
   ┌──────────────────────────────┐  LAST, because IRREVERSIBLE  │
   │ Rail adapter → pacs.008      │──────────────────────────────┤
   │ idempotent on EndToEndId     │                              │
   └──────┬───────────────────────┘                              │
          │                                                      │
          ▼          pacs.002 status / camt.054 credit notif.    │
   ┌──────────────────────────────┐                              │
   │ Settlement listener          │──────────────────────────────┘
   │ CLEARED → SETTLED            │
   └──────┬───────────────────────┘
          │
          ▼  pacs.004 PaymentReturn arrives days later
   ┌──────────────────────────────────────────────────────────────┐
   │ RETURN PATH: post a REVERSAL (new offsetting entries         │
   │ referencing the originals) → state RETURNED → notify client. │
   │ Never UPDATE or DELETE the original postings.                │
   └──────────────────────────────────────────────────────────────┘
```

**The five decisions to defend:**
1. `202 Accepted` + status resource, never a synchronous "SUCCESS" — clearing and settlement are separate (Q11).
2. Ledger write, outbox write and idempotency record commit in **one transaction** (Q22).
3. Screening is synchronous and **fails closed** (Q18).
4. The irreversible rail call happens **last** (Q31).
5. A return is a new reversal entry, not a mutation (Q24).

---

### Design 2 — Nightly position/NAV reconciliation, fund admin ↔ portfolio system

**Requirement:** the fund administrator drops an end-of-day holdings file; reconcile it against the PMS, detect breaks, report before the NAV deadline.

```text
  Fund administrator                                     Portfolio system (IBOR)
        │  MT535 / semt.002 / CSV                              │
        │  dropped on SFTP ~22:00 local                        │ REST or DB extract
        ▼                                                      ▼
  ┌───────────────────────┐                        ┌──────────────────────────┐
  │ SFTP landing zone     │                        │ Extract job (as-of date) │
  │ (immutable copy first)│                        └────────────┬─────────────┘
  └──────────┬────────────┘                                     │
             │ Event Grid: BlobCreated                          │
             ▼                                                  │
  ┌────────────────────────────────────────────┐                │
  │ Ingest fn: verify PGP sig, envelope,       │                │
  │ CONTROL TOTALS (record count + sum)        │                │
  │ FAIL FAST if totals disagree — never       │                │
  │ reconcile against a truncated file.        │                │
  └──────────┬─────────────────────────────────┘                │
             │ split → N messages                               │
             ▼                                                  │
  ┌────────────────────────┐   competing consumers, idempotent  │
  │ Service Bus / Kafka    │──────────────────┐                 │
  └────────────────────────┘                  ▼                 ▼
                                   ┌────────────────────────────────────┐
                                   │ Normalise both sides:              │
                                   │  • ISIN as the instrument key      │
                                   │  • Decimal, not float              │
                                   │  • trade date vs settlement date   │
                                   │  • FX to fund base currency        │
                                   └───────────────┬────────────────────┘
                                                   ▼
                                   ┌────────────────────────────────────┐
                                   │ MATCH on (fund, ISIN, as_of)       │
                                   │ TOLERANCE agreed in the SLA (bps)  │
                                   └───────────────┬────────────────────┘
                                                   ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │ BREAK CLASSIFICATION  (reconcile.py, Q28)                        │
        │  MISSING_IN_ADMIN · MISSING_IN_PMS · QUANTITY_MISMATCH ·         │
        │  VALUE_TOLERANCE                                                 │
        └───────────┬───────────────────────────────┬──────────────────────┘
                    │ zero breaks                   │ breaks
                    ▼                               ▼
        ┌───────────────────────┐      ┌────────────────────────────────────┐
        │ RECONCILED event      │      │ Break register: owner, ageing      │
        │ → NAV process proceeds│      │ clock, escalation at T+n, evidence │
        └───────────────────────┘      │ pack. Write-off needs an approver. │
                                       └────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │ DEADLINE GUARD: if not reconciled by <NAV cut-off>, page.        │
        │ The alert is on the DEADLINE, not on job failure. A job that     │
        │ never started fires no failure alert — that is the outage that   │
        │ actually happens.                                                │
        └──────────────────────────────────────────────────────────────────┘
```

**The senior detail here is the deadline guard.** Most candidates monitor job failure. The production incident is the job that silently never ran, and the only alert that catches it is a *deadline* alert: "by 04:00 there must be a RECONCILED event for business date D, else page." That one sentence is worth saying out loud.

---

### Design 3 — Real-time market data distribution with entitlements

```text
  Vendor / exchange feed(s)
        │  multicast / FIX / proprietary binary
        ▼
  ┌───────────────────────────────┐
  │ Feed handler (StatefulSet —   │   sequence-numbered session, gap recovery,
  │ one pod per session, ordered, │   NOT a stateless Deployment (see Q8)
  │ durable, sticky)              │
  └──────────────┬────────────────┘
                 │ normalise to canonical tick
                 ▼
  ┌───────────────────────────────────────────────────────────┐
  │ Event Hubs / Kafka — partition by instrument              │
  │ (ordering per instrument; parallelism across instruments) │
  └───┬──────────────┬──────────────┬─────────────────────────┘
      │ CG: cache    │ CG: analytics│ CG: archive
      ▼              ▼              ▼
 ┌──────────┐  ┌────────────┐  ┌──────────────────────────────┐
 │ Redis    │  │ Streaming  │  │ WORM archive — the licensing │
 │ last     │  │ analytics  │  │ audit trail AND the replay   │
 │ value    │  └────────────┘  │ source                       │
 └────┬─────┘                  └──────────────────────────────┘
      │ snapshot on connect
      ▼
 ┌───────────────────────────────────────────────────────────┐
 │ ENTITLEMENT LAYER — server-side, always                   │
 │  • APIM policy for snapshot/REST  (Q29 policy XML)        │
 │  • Web PubSub group per (feed × entitlement class);       │
 │    the join is authorised server-side, so an unentitled   │
 │    client is never in the group and never receives a tick │
 │  • Every access logged for the vendor's licence audit     │
 └────────────┬──────────────────────────┬───────────────────┘
              ▼                          ▼
        Browser (WebSocket)        Internal consumers (Kafka CG)

  Backpressure: market data is CONFLATABLE. Under load, drop stale ticks for the
  same instrument and send the latest — a slow consumer must never build an
  unbounded queue. This is the opposite of payments, where nothing may be dropped.
```

**The line that lands:** *"Market data and payments have opposite failure semantics. If a payment message is slow, you queue it — you may never drop it. If a market data tick is slow, you drop it and send the newer one — nobody wants a stale price delivered reliably. Same broker, opposite policy."*

---

## 7. EY Digital Engineering — how to talk about it

### Q38. What do you understand by EY Digital Engineering?
`[EASY]` `[NEAR-CERTAIN "why us" adjacent — have this ready]`

**Answer:** Digital Engineering is the delivery arm of EY's digital transformation work — the practice that takes a strategy and turns it into something running. EY describes the arc as **analyse, formulate, design, mobilize, drive**: understand the client's current state, shape the target, design it technically, stand up the team and the platform, and then actually run the change. The distinguishing feature versus a pure consultancy is that DE *builds*, and the distinguishing feature versus a pure engineering shop is that it's **industry-aligned** — this req sits in the Financial Services business, so the engineering is done by people who know what a cut-off is.

**Where an integration platform engineer fits:** in the *mobilize* phase and onward. When a transformation programme has ten workstreams each needing to connect a new cloud service to an old core, the integration platform is the shared dependency all ten sit on. My job is to make that a **paved road** — reusable pipeline templates, a golden Helm chart, shared APIM policy fragments, Terraform modules with the residency and WORM constraints already baked in — so that workstream nine doesn't rediscover the client's compliance requirements from scratch. That's the difference between a platform engineer and an integration developer, and it's what the title on this req says.

**If they push back — "Give me a concrete example of a paved road."** — The WORM audit-archive Terraform module in §3. It encodes the retention period, the region constraint, the no-shared-keys rule and the locked policy once. A team consuming it gets compliance by default and cannot accidentally provision a non-compliant archive. That is governance expressed as a module rather than as a document nobody reads.

---

### Q39. What does "industry-focused" change about how you work with a client?
`[MEDIUM]` `[L2 — consulting shape]`

**Answer:** Three things. **The vocabulary is theirs, not mine** — I say "cut-off" and "break" and "book of record", not "deadline" and "discrepancy" and "source of truth", because using the client's words is how you find out fast whether you've understood the problem. **The non-functionals are known up front** rather than discovered — in FS I can safely assume immutability, retention, residency, segregation of duties and a reconciliation requirement before anyone tells me, so I put them in the first design rather than retrofitting them in UAT. And **the acceptance criteria include an auditor**, not just a QA team — a design that works but can't be evidenced will fail.

**If they push back — "You don't have the domain. Isn't that a problem?"** — It's a gap I close by asking, not by guessing, and the asking is fast because I know the *shape* of the questions: which system is the book of record, what's the cut-off, what's the retention, where must the data live, what's the reconciliation control. What I bring is the platform half — the CI/CD, the IaC, the Kubernetes, the messaging backbone, the observability — which is the half that's identical across industries and where the client's own people usually have the least depth.

---

### Q40. Where does EY's AI investment intersect with this role?
`[MEDIUM]` `[Your one deliberate card — L2 only, not L1]`

**Answer:** EY and Microsoft announced a joint investment of **more than $1 billion over five years on 21 May 2026** to move enterprise AI past pilots, on a named stack — Azure, Microsoft Foundry, Microsoft Fabric, Copilot and Copilot Studio, Power Platform, Azure AI Document Intelligence — pairing Microsoft's Forward Deployed Engineers with EY's industry teams, and with EY as "client zero" (Copilot from an initial 150,000 users out to 400,000+ EY people). Separately, in **April 2026** EY launched a **multiagent framework inside EY Canvas**, its global Assurance platform, spanning **130,000 Assurance professionals across 160,000 audit engagements**. That is not a pilot; that is agents calling enterprise systems at scale.

*Say one of those two facts, not both.* Reciting a press release at length reads as preparation theatre; naming one number and immediately pivoting to what it implies for the integration layer reads as judgement.

The intersection with this role is direct: **an agent platform is an integration platform.** Tool calling is API invocation. An MCP server is an API gateway for models. RAG ingestion is an ETL pipeline. Agent orchestration is workflow orchestration with compensation. And in an FS context every one of those needs exactly what we've been discussing — an immutable log of what the agent did, idempotency so a retried tool call doesn't double-post, entitlements so an agent can't read data the user can't, and residency so the inference stays in-region. I'd expect the hardest problems in the next two years of DE work to be governance of AI-initiated integrations, and that's where my background and this JD meet.

**If they push back — "We need an integration engineer, not an AI person."** — Agreed, and that's the job I'm applying for. I'm not proposing to bring AI into it; I'm saying the platform properties this role builds — auditability, idempotency, entitlement, residency — are exactly what EY's AI programme will need from its integration layer, and I've built systems on both sides of that line. Full framing in [GenAI → Integration Bridge](10-genai-to-integration-bridge.md) and [ANSWERS.md](ANSWERS.md) §E.

---

## 8. Honest framing: 8 lines + 8 questions to ask

### The eight rehearsed lines

Say these out loud until they're fluent. Each is a complete, sayable answer.

1. **The core line.** *"I have not worked in banking. But the constraints you are describing — an immutable audit trail, exactly-once effect on a payment, data residency — are ones I have built for. Here is how."*

2. **When they name a system you don't know.** *"I don't know Guidewire. Tell me what it is the book of record for and what it can expose — a REST API, a database, a nightly file — and I can tell you how I'd integrate it. Most of my integration career has been learning one new system of record per project."*

3. **When they ask if you've done payments.** *"No. I've built idempotent, append-only, at-least-once systems where a duplicate must not double-apply — which is the payments problem with a different noun in front of it. What I'd want to learn fast is the domain-specific parts: the rail's return codes, the cut-off schedule, and the value-dating rules. Those are learnable in weeks; the platform underneath isn't."*

4. **On standards.** *"I can read an MT103 and a pain.001 and tell you what each field is for, and I know why the industry moved from one to the other. I have not implemented a scheme-compliant translator, and I'd expect the usage guideline — CBPR+ or the domestic rulebook — to be more of the work than the XSD."*

5. **Turning the gap into a question.** *"Before I answer, can I check an assumption? In an FS context I'd assume the audit trail is WORM with multi-year retention and that the deployment pipeline has an enforced separation of duties. Is that the shape here, or is it lighter?"*

6. **On compliance you haven't been assessed against.** *"I've never been in PCI scope, and the reason is that in the systems I built we deliberately never held the card number — tokenisation at the edge. That's the design goal I'd bring: reduce scope rather than secure scope."*

7. **When they push on the gap directly.** *"You're right that I'd be learning the domain. I'd rather be honest about that than have you find out in month two. What I'm not learning on the job is Kubernetes, pipelines, IaC, messaging or API design — and in my experience the domain is the faster half to close, because the client's own people will teach it to you if you ask precise questions."*

8. **The close.** *"The thing I'd want from the first month is to sit with whoever owns the reconciliation and whoever owns the release process. Those two conversations tell you more about an FS platform than any architecture diagram."*

### The eight questions to ask them

These signal domain shape without claiming domain experience. Ask two or three, not all eight.

1. **"Which industry group does this team sit in — Banking and Capital Markets, Asset Management, Insurance? And is it one client or a shared platform across several?"** *(Also flushes out the GDS bench/redeployment question without asking it rudely.)*
2. **"For the integrations this team owns, which system is the book of record, and how much of the flow is real-time versus end-of-day batch?"**
3. **"Is the client already on ISO 20022 end-to-end, or is there still an MT translation layer in the path?"**
4. **"What does the audit and retention requirement look like — are we in SEC 17a-4 / MiFID II territory, or is it lighter than that?"**
5. **"Is there a data-residency constraint that pins the region? For an Indian client I'd assume the RBI payment-data localisation rules apply."**
6. **"How does a change reach production today — is it GitOps-reconciled, or is there still a manual deployment step with a change ticket?"** *(This is a platform-engineer question and it will land.)*
7. **"Is reconciliation a system with its own team, or is it scripts owned by whoever wrote them?"** *(Reveals platform maturity instantly.)*
8. **"Is there a client-facing round after the EY rounds, and if so, which client?"** *(Documented GDS pattern. Ask it in HR, not L1.)*

---

## 9. 30-second whiteboard versions

### 9.1 Exactly-once effect

```text
  EXACTLY-ONCE DELIVERY = IMPOSSIBLE.  EXACTLY-ONCE EFFECT = ACHIEVABLE.

  Why impossible:   sender cannot distinguish "msg lost" from "ack lost"
                    → must retry → duplicates exist. Always.

  Achieve the effect with three things:

   1. WRITE PATH      Idempotency-Key header + UNIQUE constraint
                      → 2nd attempt replays the 1st response, does no work
                      → different body + same key = 422, not a silent replay

   2. READ PATH       INSERT event_id INTO processed_event
                        ON CONFLICT DO NOTHING
                      ...in the SAME transaction as the side effect
                      → commit the broker offset AFTER the DB commit

   3. PUBLISH PATH    Transactional outbox: business row + outbox row in one
                      local txn; a relay publishes. DB and broker are not atomic.

  Say last: "Kafka's exactly-once is exactly-once INSIDE Kafka. The moment the
  side effect leaves Kafka, you're back to idempotent consumers."
```

### 9.2 The GitOps audit answer

```text
  AUDITOR: "Prove the code in prod is the code that was reviewed."

    reviewed commit  ──►  attested build  ──►  digest-pinned manifest  ──►  cluster
    (PR, approver         (SLSA provenance     (sha256:..., never          (Argo CD /
     ≠ author)             bound to commit      :latest)                    Flux
                           + workflow)                                      reconciles
                                                                            continuously)

  Therefore:
   • "What is running?" has a GIT answer, not a kubectl answer.
   • No human holds cluster write creds — pipeline uses OIDC federation.
   • Hand-patch a Deployment → controller reverts it or raises drift. Visible either way.
   • SOX separation of duties = branch protection + environment approval, enforced by
     the platform, not by process documentation.

  This is why GitOps moved from "good to have" into the responsibility list on this JD.
```

### 9.3 FS non-functionals you assume before being told

```text
  Before the client says a word, assume:

   IMMUTABLE      append-only ledger; reversal, never UPDATE/DELETE
   RETAINED       years, not days. WORM + locked policy. SEC 17a-4 = 6 yrs
                  (first 2 easily accessible); MiFID II = 5, extendable to 7
   RESIDENT       region pinned by policy — incl. backups, DR pair, LOG SINKS
   SEGREGATED     maker ≠ checker, in the service AND as a DB constraint;
                  same rule on the deploy pipeline
   RECONCILED     two books of record WILL disagree; recon is a system with an
                  SLA, an ageing clock and an approver for write-offs
   DEADLINED      cut-offs, not just throughput. Alert on the DEADLINE, not on
                  job failure — the job that never started fires no failure alert

  Then ask which of the six is actually lighter than you assumed. Asking that
  question is the demonstration of domain fluency.
```

---

## 10. Interviewer traps

**Trap 1 — "Our messaging gives exactly-once delivery, so we don't need idempotency."**
*Wrong answer:* agreeing, or saying "yes, Kafka/Service Bus handles that."
*Right answer:* exactly-once delivery is impossible over an unreliable network; the vendor means exactly-once *within their system*. The moment the effect leaves the broker — a DB write, a core banking call — you need an idempotent consumer. Service Bus duplicate detection is a **time-windowed** dedupe on `MessageId`, not a guarantee; a redelivery outside the window still duplicates.

**Trap 2 — "Sanctions screening is down. Let the payments through and screen later."**
*Wrong answer:* treating it as an availability trade-off and failing open, because that's the instinct every distributed-systems course trains into you.
*Right answer:* fail **closed**. Sending an unscreened payment to a sanctioned party is a legal breach that cannot be undone by screening afterwards. Payments hold, ops is alerted, and the business decides whether to invoke a manual screening process. This is the one place where a circuit breaker must not have a fallback that proceeds.

**Trap 3 — "The two systems disagree. Just update ours to match theirs."**
*Wrong answer:* "I'd sync from the authoritative side."
*Right answer:* you never silently force a match. A break is investigated and resolved by understanding *why* they diverged, because the divergence is usually a symptom of a real defect — a missed message, a corporate action applied on different dates, an FX rate mismatch. If the business accepts the difference, it's written off through an **explicit adjustment entry with a maker and a checker**, which is itself auditable. Overwriting one side destroys the evidence of the defect.

**Trap 4 — "Store the card number encrypted so we can do refunds."**
*Wrong answer:* proposing AES-256 + Key Vault and feeling secure about it.
*Right answer:* encryption doesn't remove you from PCI DSS scope — storing, processing *or transmitting* cardholder data puts you in scope, and scope is the expensive part. Tokenise at the edge so the PAN never enters your systems; refunds and card-on-file work against the token. The right instinct in FS security is *reduce scope*, not *secure scope*.

**Trap 5 — "It's an immutable audit log, so GDPR erasure is impossible."**
*Wrong answer:* declaring the two requirements irreconcilable, or worse, proposing to delete from the audit log.
*Right answer:* separate the transaction record from the personal data. GDPR Art 17(3)(b) exempts processing required by legal obligation and 17(3)(e) exempts legal claims, so the ledger entry stays; erasure targets a separate PII store keyed by `party_id`. Where PII is already embedded in an immutable object, crypto-shred: per-subject key, destroy the key, ciphertext remains. And log the erasure itself.

**Trap 6 — "Just retry until the downstream comes back."**
*Wrong answer:* infinite exponential backoff, feeling good about resilience.
*Right answer:* retries must stop at the **cut-off**. Past it, the payment rolls to the next value date with an explicit status change and an alert. Retrying past cut-off and settling a day late with today's value date is a value-dating error — a reportable control failure, and worse than an honest delay.

**Trap 7 — "Lock the immutability policy in the sandbox too, for consistency."**
*Wrong answer:* applying `locked = true` everywhere because it's the compliant setting.
*Right answer:* once a container-level policy is locked, the container is deletable only when empty and its blobs cannot be deleted until retention expires — so the container **and the storage account holding it are effectively undeletable** for the whole period. `terraform destroy` fails and you've created a resource that outlives the engagement, billing forever. Locked policies belong in production only; lower environments use **unlocked** policies with short retention, which can be shortened or removed. Also set the append flags deliberately: `protected_append_writes_enabled` covers append blobs, `protected_append_writes_all_enabled` also covers block blobs — workloads that create-then-append break against a plain locked policy.

**Trap 8 — "The nightly job didn't fail, so reconciliation is fine."**
*Wrong answer:* monitoring job exit codes.
*Right answer:* alert on the **deadline**, not the failure. "By 04:00 there must be a RECONCILED event for business date D, else page." A job that never started produces no failure signal at all, and that is the outage that actually happens in production — a scheduler misconfiguration, a triggering file that never landed, a paused pipeline.

**Trap 9 — "I've worked on financial systems."** *(the self-inflicted trap)*
*Wrong answer:* stretching a payments-adjacent project into domain experience, then getting three follow-up questions deep and improving suspiciously with each one. Candidate reports describe GDS interviews **terminated early** for exactly that pattern.
*Right answer:* concede the fact in the first sentence, claim the capability in the second, prove it in the third. §0. Then commit to your answer and refine it once — don't let it get better under pressure in a way that reads as external help.

---

## 11. Rapid fire

| # | Q | A |
|---|---|---|
| 1 | Exactly-once delivery? | Impossible. Exactly-once **effect** via at-least-once + idempotent consumer. |
| 2 | ISO 20022 `pain` | Payment **initiation** — customer to their bank. `pain.001` = CustomerCreditTransferInitiation. |
| 3 | `pacs` | Payments **clearing and settlement** — bank to bank. `pacs.008` customer credit transfer. |
| 4 | `camt` | **Cash management** / reporting. `camt.053` statement, `camt.054` debit/credit notification. |
| 5 | `pacs.004` vs `pacs.002` | `.004` PaymentReturn **moves money back**; `.002` is a status report and moves nothing. |
| 6 | MT103 | Single Customer Credit Transfer. ISO 20022 successor: `pacs.008`. |
| 7 | MT202COV | FI transfer carrying the underlying customer payment detail — introduced 2009 for traceability. |
| 8 | MT940 / MT950 | End-of-day account statements → `camt.053`. |
| 9 | MT535 / 536 / 537 | Statement of Holdings / Transactions / Pending Transactions. |
| 10 | MT548 | Settlement Status and Processing Advice. |
| 11 | SWIFT MT/MX coexistence ended | **22 November 2025** — for the in-scope cross-border **payment clearing & settlement** messages (MT103/MT202 → `pacs`). MT cash management/reporting (MT940/942) retirement was **deferred past Nov 2025**; category 5 securities MT was never in scope. |
| 12 | Fedwire ISO 20022 | Single-day cutover **14 July 2025**, retiring FAIM. Avg daily value **≈$4.59T (2025)**. |
| 13 | T+1 | **US 28 May 2024**; **Canada/Mexico/Argentina 27 May 2024** (US Memorial Day). UK/EU/Switzerland together on **11 October 2027**. |
| 14 | SEPA Instant target | **10 seconds** end to end. Euro-area: receive from 9 Jan 2025, send + Verification of Payee from 9 Oct 2025. Non-euro-area Member States: 9 Jan 2027 / 9 Jul 2027. |
| 15 | Same Day ACH limit | **$1M** per payment since 18 Mar 2022; **$10M effective 17 Sep 2027**. |
| 16 | FIX | Stateful sequence-numbered session for orders/executions. Session layer FIXT 1.1; app layer now "FIX Latest". 4.2/4.4 still everywhere. |
| 17 | Why a FIX gateway is a StatefulSet | Ordered, sequence-numbered, durable session state. Recovery is a resend request, not an HTTP retry. |
| 18 | FpML | XML for OTC derivatives, managed by ISDA. |
| 19 | MISMO | US mortgage data/XML standard; MBA subsidiary, est. 1999. |
| 20 | X12 834 / 837 / 835 / 820 | Enrolment / claim / claim payment-advice / group premium payment. |
| 21 | EDIFACT | The non-US equivalent of X12. |
| 22 | AS2 | **RFC 4130** — signed + encrypted S/MIME over HTTP(S), with MDN receipts giving non-repudiation of receipt. AS1 was SMTP. |
| 23 | Clearing vs settlement | Clearing = agreeing the obligation. Settlement = final transfer of value. Days apart. |
| 24 | Nostro / vostro | Our account with them / their account with us. Nostro recon is a huge banking workload. |
| 25 | IBOR vs ABOR | Trade-date PM view vs settlement-date accounting view. They disagree nightly — that's why recon exists. |
| 26 | NAV | (Assets − liabilities) ÷ units. Struck daily, hard deadline. |
| 27 | A "break" | A discrepancy between two sources. Worked and evidenced, never silently overwritten. |
| 28 | STP | Straight-through processing — % completing with no human touch. The number clients hold you to. |
| 29 | Sanctions screening placement | **Synchronous, blocking, fail-CLOSED.** Unscreened ≠ acceptable degradation. |
| 30 | Fraud scoring placement | **Async enrichment** with thresholds. Risk judgement, not a binary legal obligation. |
| 31 | Maker-checker | Second authorised human approves; maker ≠ checker, enforced in the service **and** as a DB CHECK constraint. |
| 32 | Reversal vs delete | A reversal is a **new offsetting entry referencing the original**. Never UPDATE/DELETE a posted entry. |
| 33 | Ledger integrity check | Every transaction's debits and credits must sum to zero. Assert it on a schedule. |
| 34 | Money type in Python | `Decimal`, in minor units. A float in an FS interview is a disqualifying tell. |
| 35 | SEC 17a-4 retention | **6 years, first 2 easily accessible.** Oct 2022 amendments added an **audit-trail alternative** to strict WORM. |
| 36 | MiFID II Art 16(7) | Record relevant calls/e-comms; retain **5 years, extendable to 7** on competent-authority request. |
| 37 | Azure WORM limits | Min **1 day**, max **146,000 days (400 yrs)**. Locked policy can be extended, never shortened; container-level max **5 increases** (version-level: unlimited). Container-level WORM caps at **10,000 containers/account**. Locked container → deletable only when empty, so account is effectively undeletable for the retention period. |
| 38 | RBI localisation | Circular 6 Apr 2018; 2019 FAQ — processing abroad OK, but data deleted abroad and back in India within **one business day / 24 hours, whichever is earlier**. |
| 39 | DPDP timeline | Rules notified **13 Nov 2025**; consent managers **+12 months**; substantive obligations **+18 months (13 May 2027)**. |
| 40 | DORA | In force 16 Jan 2023, **applies from 17 Jan 2025**. ICT risk, incident reporting, resilience testing, **Register of Information** for third parties (first submissions to the ESAs by **30 Apr 2025**), first **CTPP** designations from **July 2025**. |
| 41 | PCI DSS current version | **v4.0.1**. v3.2.1 retired 31 Mar 2024, v4.0 retired 31 Dec 2024; 51 future-dated requirements mandatory from **31 Mar 2025**. |
| 42 | PCI scope reduction | Tokenise at the edge. Keep the PAN out entirely. Encryption does **not** remove scope. |
| 43 | RTBF vs immutable ledger | Split PII from the ledger; erase PII, keep the entry (GDPR Art 17(3)(b)/(e)); crypto-shred where PII is already embedded. |
| 44 | BCBS 239 | Basel, Jan 2013. **14 principles** (11 banks, 3 supervisors). Why banks demand end-to-end **data lineage**. |
| 45 | Kafka idempotent producer | `enable.idempotence` defaults **true** since Kafka 3.0; forces `acks=all`, `retries>0`, `max.in.flight ≤ 5`. |
| 45b | Kafka control plane | **ZooKeeper removed in Kafka 4.0 (March 2025)** — KRaft is the only mode. Don't mention ZooKeeper except as a migration a client may still owe. |
| 46 | Consumer config for FS | `enable.auto.commit=false`, `isolation.level=read_committed`, commit offset **after** the DB transaction. |
| 47 | "Batch jobs using event streaming" | Batch driven through async messaging, not cron-and-a-shared-drive: file event → validate control totals → split → queue → idempotent competing consumers → DLQ per record. |
| 48 | Control totals | Declared record count + sum in the file envelope. Fail fast if they disagree — never reconcile against a truncated file. |
| 49 | Cut-off | Time after which an instruction rolls to the next business day. Value date is **computed**, never supplied. |
| 50 | Downstream down at cut-off | Queue and retry until cut-off; then roll the value date with an explicit status change + alert. Never settle late with today's value date. |
| 51 | Recon monitoring | Alert on the **deadline**, not on job failure. A job that never ran fires no failure alert. |
| 52 | Ordering rule for irreversible steps | Do the irreversible step **last**, after every reversible step has succeeded. |
| 53 | Market data vs payments backpressure | Market data: conflate and drop stale ticks. Payments: never drop, queue. Same broker, opposite policy. |
| 54 | Entitlements enforcement point | Server-side, last hop you control, with an access log — the vendor audits your logs, not the client's intentions. |
| 54b | API error format | Problem details, **RFC 9457** (obsoleted RFC 7807 in July 2023). Media type unchanged: `application/problem+json`. Cite 9457. |
| 55 | "Prove prod == reviewed code" | GitOps: reviewed commit → attested build → digest-pinned manifest → continuously reconciled cluster. Drift is visible. |
| 56 | SOX in a pipeline | Author ≠ approver, no standing prod write access, OIDC federation, environment approval recorded, break-glass time-boxed and alerting. |
| 57 | The honest-framing line | "I have not worked in banking. But the constraints — immutable audit trail, exactly-once effect on a payment, data residency — are ones I have built for. Here is how." |
| 58 | The first question in any FS engagement | "Which system is the book of record, and who is allowed to change it?" Second: "What's the cut-off?" |
| 59 | EY DE arc | Analyse, formulate, design, mobilize, drive — strategy into technical design, industry-aligned. |
| 60 | Platform-engineer framing | Paved road: reusable pipeline templates, golden Helm charts, shared APIM policy fragments, compliant Terraform modules. Governance as a module, not a document. |

---

**Last word before the interview:** you will not out-domain an FS interviewer, and you should not try. What you can do is demonstrate that you already know the *shape* of their constraints and that you'd close the gap by asking precise questions rather than guessing. Concede the fact, claim the capability, prove the capability — three beats, every time.
