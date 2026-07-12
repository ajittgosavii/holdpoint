# HOLDPOINT — Solution Blueprint

> Complete architectural, functional and commercial description of HOLDPOINT, structured for
> import into **Infosys Topaz Fabric** as an agentic solution asset.
>
> Repository: `https://github.com/ajittgosavii/holdpoint` · Blueprint updated 2026-07-11 · commit `9fe4618`
>
> **Status at a glance:** structure, safety layers and UI are **verified by test**. The **live LLM
> path has not yet been exercised** (no API key in the build environment) — so the agents' reasoning
> quality is *unproven*. See §10. Do not demo until that is closed.

---

## 1. Solution Metadata

```yaml
solution:
  id: holdpoint
  name: HOLDPOINT — Adversarial Permit-to-Work Assurance
  tagline: The adversary at the permit gate.
  version: 0.1.0
  maturity: working prototype — structure and safety layers verified; live LLM path not yet exercised
  domain: Operational Safety / Control of Work / Conduct of Operations
  primary_industries: [Refining & Chemicals, Mining & Metals]
  hypothesis_industries: [Utilities (T&D)]          # NOT verified — see §9
  not_applicable: [Business Services, Retail]        # stated plainly; no permit-to-work exists
  pattern: Multi-agent adversarial review + incident-precedent retrieval + programmatic provenance
  interface: Streamlit multipage
  language: Python 3.11+
  loc: ~3,800
  buyer: COO / VP Operations (conduct-of-operations) — NOT the CIO
  budget_line: Operations (mandatory gate), not innovation (discretionary pilot)

deployment:
  target: Streamlit Cloud
  repo: ajittgosavii/holdpoint
  branch: main
  entrypoint: app.py
  secrets: OPENAI_API_KEY (required) · ANTHROPIC_API_KEY (optional — enables automatic failover)
  local: create .env with OPENAI_API_KEY=... (gitignored); load_secrets() resolves
         .env -> Streamlit secrets -> environment
```

### One-line description

An AI adversary that attacks a work permit **before** it is authorised — decomposing over-broad
scopes, forcing safeguards buried in prose into enforced hold points, matching people to hazards,
and refusing to let a defective permit through. **A human always makes the actual decision.**

---

## 2. The Problem — and the sentence the product exists for

On 10 October 2024, contract workers opened a hydrogen sulphide line at the PEMEX Deer Park
refinery. Over **27,000 lb of H₂S** was released. **Two contract workers were killed**; 13 were
hospitalised; two cities sheltered in place.

The US Chemical Safety Board's final report (**23 February 2026**) found:

> *"The refinery issued a broad work permit covering multiple jobs with varying hazards and without
> clear hold points."*

> *"Workers overlooked a written instruction to stop work and obtain an operator's presence before
> opening the hydrogen sulfide piping."*

**The safeguard was already on the permit.** It was buried in a narrative field, inside a scope
covering five separate jobs, and it was read past.

This is a failure of **structure and enforcement**, not of authorship. And it is the precise failure
that a reasoning agent can attack — because it lives entirely inside the content and structure of a
document.

### Why this is not a niche

| Evidence | Source | Status |
|---|---|---|
| Two contract workers killed; permit "covering multiple jobs… without clear hold points"; stop-work instruction present and overlooked | US CSB final report, 23 Feb 2026 | **VERIFIED** |
| 42 ICMM-member fatalities in 2024, up from 36 (2023) and 33 (2022) — a second consecutive rise ICMM calls *"hugely troubling"* | ICMM, *2020–2024 Safety Performance: Insights*, Jul 2025 | **VERIFIED** |
| *"In process plants, nearly half of all fatal incidents (41%) occur during unusual or non-routine tasks, often undertaken by contractors."* | ICMM (as above) | **VERIFIED** |
| *"Weaknesses in site safety paperwork (the 'permit-to-work') or in isolating and locking out energy sources ('lock-out/tag-out') frequently contribute."* | ICMM (as above) | **VERIFIED** |
| ICMM's own prescription: move *"from a mindset of simply 'identify and document' to one of 'verify and act'."* | ICMM (as above) | **VERIFIED** |
| 167 killed at Piper Alpha — a permit-to-work and shift-handover failure | Cullen Inquiry, 1990 | **VERIFIED** |
| 15 contractors killed at BP Texas City — who was permitted to *be* where during a non-routine operation | US CSB, 2007 | **VERIFIED** |

ICMM is an industry body reporting adverse results **against its own interest**. That is the
strongest class of evidence available.

---

## 3. Competitive Position — the whitespace, precisely

| Vendor | What they ship | Verified? |
|---|---|---|
| **Enablon** (Wolters Kluwer) | *"AI-powered Permit Advisor that retrieves historical permits for reference, **checks description quality, and recommends hazards and controls**"* | **3-0 verified** |
| **Sphera** | *"Standardize policy into operational practice using **templates and standardized workflows**"* — an electronic permit **form**, not a reasoner | **3-0 verified** |
| Cority · Avetta · ISN · Honeywell · eVision · SAP WCM | **NOT SCANNED** — the competitive pass was cut short | ⚠️ **OPEN** |

### The distinction the whole product rests on

Enablon's AI is a **drafting copilot for the permit author**. It helps you *write a better permit*.

But at Deer Park **the description was not poor and the hazard was not missing**. The stop-work
instruction was already written down. A tool that recommends hazards would have recommended a hazard
that was already listed.

> **Enablon helps you write the permit. HOLDPOINT refuses to let a bad one through.**
> Those coexist. They are not the same product.

### Strategic posture: layer, do not replace

Do **not** build a rival EHS suite. Rip-and-replace of a system of record is a multi-year sale a
challenger cannot win, and Infosys likely implements Enablon today — a head-on war puts existing
services revenue in the crossfire.

Instead, HOLDPOINT **reads the permit out of** the incumbent system (Enablon, SAP WCM, Maximo,
Sphera, eVision), attacks it, and **writes findings and hold points back in**. No rip-and-replace.
Weeks to value. Enablon becomes a substrate, not an enemy.

**And a channel opens**: Enablon's Permit Advisor created a problem for *every other vendor*. Sphera,
Cority, eVision, Honeywell and SAP all now need an answer and none wants to build an agentic stack.
Infosys can be that answer — converting a competitive threat into distribution.

> **Honest limit on the moat:** features are not a moat. Enablon can build every capability below.
> The durable advantages are the incident corpus + provenance method, integration depth, client
> relationships, and **speed**. This is a window, not a fortress.

---

## 4. Architecture

```
┌──────────────────────── STREAMLIT UI ─────────────────────────────────┐
│   Permit Review    │    Backlog Scan    │    Incident Precedent       │
└──────────┬─────────┴──────────┬─────────┴─────────────┬───────────────┘
           │                    │                       │
┌──────────▼────────────────────▼───────────────────────▼───────────────┐
│                    LangGraph — 8 nodes, sequential                     │
│  plan → scope → hazards → hold_points → competency → isolation/SIMOPS │
│       → precedent → verdict                                            │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│  core/provenance.py   ← THE GATE. Verifies every citation against the  │
│                          real procedure corpus. CODE, not a prompt.    │
│  core/backlog.py      ← Deterministic structural pre-screen            │
│  core/domains.py      ← Industry packs: refining · mining · utilities  │
│  core/vectorstore.py  ← Retrieval over the incident corpus             │
│  data/incidents.py    ← CSB · Cullen · ICMM major-accident corpus      │
│  data/procedures.py   ← Ground truth every control must trace to       │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│      GPT-4o (primary)  →  automatic failover  →  Claude Sonnet         │
└───────────────────────────────────────────────────────────────────────┘
```

**The agent graph contains no industry-specific logic.** Swapping the site pack re-targets all seven
agents without touching agent code.

### Repository map

| Path | Role |
|---|---|
| `app.py` | Overview — the Deer Park narrative, the value case, the honest limits |
| `pages/1_Permit_Review.py` | The core product: 7 agents attack a permit |
| `pages/2_Backlog_Scan.py` | The business case: count the Deer-Park-shaped permits |
| `pages/3_Incident_Precedent.py` | The corpus, with verified/illustrative rigidly separated |
| `agents/permit_review/graph.py` | 8-node LangGraph + provenance wiring |
| `core/provenance.py` | **The most important file.** Programmatic citation verification |
| `core/backlog.py` | Deterministic structural defect scanner |
| `core/prompts.py` | 8 adversarial role prompts |
| `core/domains.py` | Industry packs + evidence status |
| `core/llm.py` | Model factory, 4 tiers, provider failover |
| `core/vectorstore.py` | TF-IDF retrieval over the incident corpus |
| `core/ui.py` | Sidebar, industry switcher, verdict banner, citation badges, credential resolution |
| `data/procedures.py` | Site procedure corpus — the ground truth |
| `data/permits.py` | Permit packs, incl. the Deer Park pattern |
| `data/incidents.py` | Major-accident corpus |
| `BLUEPRINT.md` | This document |

---

## 5. Agent Registry

Seven agents, eight prompt roles (the Supervisor acts twice — plan and verdict).
**Every one is an adversary, not an assistant.** They are told, deliberately, that *finding nothing
is a failure mode* — and equally that *inventing a control is the one unforgivable error*.

| # | Agent | Job | Output |
|---|---|---|---|
| 1 | **Supervisor** (plan) | Decide where the danger hides; direct the attack | `where_danger_hides`, `what_would_make_this_lethal`, `initial_concern_level` |
| 2 | **Scope Decomposer** | Is this one job, or five wearing a trench coat? An over-broad permit **is** the Deer Park structure | `distinct_tasks[]`, `must_be_split`, `split_rationale` |
| 3 | **Hazard Coverage Challenger** | Is that control real, or is it the word *"carefully"*? Infers hazards the permit never names | `findings[]` with `control_is_verifiable`, `required_control`, `is_inference` |
| 4 | **Hold Point Enforcer** | **The most important agent.** Hunts prose for safeguards nobody enforces | `buried_hold_points[]` (verbatim), `missing_hold_points[]`, `should_read_as` |
| 5 | **Competency Matcher** | Is *this person* qualified for *this hazard*? Induction ≠ competence | `findings[]` per person, `competency_gaps[]` (expired vs missing), `reassignment_briefing_gap` |
| 6 | **Isolation & SIMOPS Verifier** | Every energy source; adequacy of method; **and what else is live on this unit right now** | `isolation_findings[]`, `simops_conflicts[]` with `credible_accident` |
| 7 | **Incident Precedent Analyst** | Which historical fatal accident does this permit **structurally** resemble? | `closest_match` with `the_sentence`, `structural_features_shared`, `..._NOT_shared` |
| 8 | **Supervisor** (verdict) | AUTHORISE · HOLD_WITH_CONDITIONS · REJECT — **advisory only** | `recommendation`, `blocking_findings[]`, `conditions_to_close[]`, `credible_accident_prevented` |

### Verdict rules (encoded in the prompt, not left to taste)

- Any **unenforced hold point** on a permit breaking containment on toxic/flammable service → **≥ HOLD**
- Any person **without current competency** for a hazard they will personally face → **≥ HOLD**
- **Over-broad scope** bundling jobs of differing hazard → **REJECT** (cannot be conditioned away —
  the conditions cannot be attached to the right job)
- Live **SIMOPS conflict** creating a credible ignition/toxic path → **REJECT**
- Found nothing? Say **AUTHORISE** with confidence. *A reviewer who flags everything is as useless as
  one who flags nothing, and will be ignored — which gets people killed just as surely.*

---

## 6. The Trust Architecture — why this is allowed near a permit

### 6.1 Provenance is a CODE check, not a prompt (`core/provenance.py`)

Every control an agent asserts as **mandated** must quote a real site procedure **verbatim**. The
system then **programmatically verifies the quoted sentence exists** in the procedure corpus.

```
verify_quote(quote, corpus) -> Citation(verified: bool, document_id, reason)
```

- Exact match (whitespace/case-normalised) → **VERIFIED**
- Elision tolerated: a ≥40-char leading span matching a real sentence → **VERIFIED**
- Otherwise → **UNVERIFIED**, and `confidence` is force-downgraded to `low`

**The model cannot talk its way past this, because it is code.**

> An AI that invents a safety control has manufactured false assurance inside the one system built to
> prevent false assurance. That is worse than no AI at all.

**Unit-tested:** accepts a real procedure quote; **rejects a hallucinated control, a paraphrase of a
real rule, and an empty citation.**

This is also **the vendor's own indemnity**, not only the client's assurance.

### 6.2 It never authorises anything

Every result is stamped `PENDING_HUMAN_AUTHORISATION`. HOLDPOINT is decision support. A qualified
human authoriser decides. The prompts say so; the UI says so; the output object says so.

### 6.3 Failing loudly

A JSON parse failure does **not** degrade to an empty result. In a safety system, silence reads as
*"nothing wrong here"* — the most dangerous possible failure mode. Parse failures surface as an
explicit unreliable-review finding.

### 6.4 Evidence honesty is displayed, not buried

The incident corpus rigidly separates **VERIFIED** investigations (CSB, Cullen, ICMM — quoting the
investigators, with source URLs) from **ILLUSTRATIVE** patterns. The precedent agent is required to
declare when its match is illustrative.

> A safety tool that cites a fabricated fatality to make its point has forfeited the right to be
> believed about anything else it says.

### 6.5 Retrieval matches on STRUCTURE, not on subject matter

`_retrieve_incidents()` builds its query from **the specialists' findings**, not from the permit
text. This is the difference between a weak match and one that stops a shift:

| Match on… | Produces |
|---|---|
| **Subject matter** (permit text) | *"Both involve H₂S."* — true, useless, and retrieves the wrong lesson |
| **Structural failure shape** (findings) | *"Over-broad scope, stop-work instruction present in prose but not enforced as a hold point, two contracting companies, live toxic inventory adjacent."* — the Deer Park signature |

**An honest threshold.** Below `RETRIEVAL_THRESHOLD = 8` incidents the system passes the **full
corpus** and says so on screen, because a top-k over six documents adds nothing and only risks
dropping the one that mattered. Above it, retrieval runs — because a real client corpus is hundreds
of investigation reports and cannot fit in a prompt.

> **A correction we made to ourselves.** An earlier version of this blueprint and the README claimed
> "RAG over the corpus" while the code injected the whole corpus and the retrieval module was dead.
> That was an overclaim, and it was fixed rather than quietly left in place. A product whose central
> argument is *"verify your evidence"* does not get to be sloppy about its own.

---

## 7. The Metric That Decides the Business Case

**Backlog Scan** (`core/backlog.py`) — deterministic, rules-based, no LLM. A cheap sweep over
thousands of permits.

Run it over permits that were **already authorised, worked and closed without incident**. Count the
**Deer Park signature**: an over-broad scope **plus** a safeguard that nothing enforces.

**Every permit it finds is an incident that did not happen by luck.**

### Detected defects

| Code | Meaning |
|---|---|
| `over_broad_scope` | One permit authorising multiple jobs of differing hazard |
| `buried_stop_work` | Stop-work instruction in prose, not enforced as a hold point |
| `no_hold_points` | No hold points on a high-hazard permit |
| `competency_gap` | A named person lacks current competency for a hazard they face |
| `simops_conflict` | Concurrent permit creating a credible conflict |
| `weak_isolation` | Valve-only isolation on toxic/high-hazard service |
| `multi_company_party` | One permit spanning multiple contracting companies |

### It is built so it CAN return zero

> **If the count is zero, the product has no case and we say so and walk away.**
> A test that cannot fail proves nothing.

The honest pitch to a client is a **question, not a claim**: *how many of these would you like to
have known about?*

---

## 8. Commercial Model

### Why it survives the pilot graveyard

Deloitte, *State of AI in the Enterprise* (5th ed., 21 Jan 2026, n=3,235): **only 25% of enterprises
have moved 40%+ of AI pilots into production.**

Optional copilots die. **A permit cannot be issued without passing through the gate.** That makes
HOLDPOINT a **line item, not an experiment** — and puts it in an *operations* budget, not a
discretionary innovation budget.

### The two ledgers

**Ledger 1 — catastrophic loss avoidance.** Real, but hard to quantify prospectively and reads as
emotional. Carry it; don't lead with it.

**Ledger 2 — turnaround throughput. LEAD WITH THIS.**
Non-routine work clusters violently in turnarounds and outages — exactly where ICMM says the
fatalities happen. During a turnaround the permit desk issues **hundreds of permits a day** and
becomes a hard bottleneck: crews stand idle waiting for authorisation, and authorisers under queue
pressure are precisely the humans who read past a buried stop-work line.

> **The permit desk is simultaneously the safety chokepoint and the schedule chokepoint. They are
> the same queue.**

An agent that pre-screens and fixes permits *before* they reach the authoriser raises the quality of
what the human sees **and** shortens the queue. Turnaround days are extraordinarily expensive.
**Safety funds it. Operations wants it.**

### Indicative deal shape (ILLUSTRATIVE — must be validated)

| Stage | Duration | Indicative revenue |
|---|---|---|
| Discovery & qualify | 4–6 wks | $150k–250k |
| Pilot (one unit / one turnaround) | 8–12 wks | $400k–700k |
| Production build + integration (SAP WCM / Maximo / Enablon / ISN) | 6–9 mo | $1.5M–3M |
| Site rollout | per site | $200k–400k |
| Managed run | annual | $400k–1M ARR |

**Anchor client: ~$3M–6M over 2–3 years.** Portfolio arithmetic across 8–12 operators: $25M–60M —
**arithmetic, not evidence.**

### Why it is good business beyond the invoice

1. **Breaks revenue-equals-headcount.** Engine built once; each client is a pack + integration.
2. **Opens the COO's budget**, not the CIO's — far larger, and gated rather than discretionary.
3. **Pull-through exceeds the AI.** SAP WCM/Maximo integration, contractor competency data cleanup,
   isolation/asset data — often the larger half of the programme.
4. **Safety-critical AI is a trusted-SI purchase**, not a startup purchase. Provenance + HITL +
   auditability is exactly what a regulated operator requires — and what Infosys can stand behind.

### ⚠️ NOT VALIDATED — must be closed before any number is quoted

- What operators currently spend on control-of-work / contractor-safety software
- The cost of a day of turnaround delay at a target client (**the number that converts safety into a
  CFO story**)
- Whether Cority / Avetta / ISN / Honeywell / SAP already ship permit **review** reasoning

---

## 9. Honest Limits — stated in the app, not buried in an appendix

| # | Limit | Why we say it first |
|---|---|---|
| 1 | **It would NOT have prevented the Deer Park root cause.** The CSB's root cause was failure to positively identify the correct equipment — workers opened a near-identical flange ~5 ft away. The permit deficiencies were **contributing**. | Someone will ask. Saying it first makes every other claim believable. |
| 2 | **It is a minority of the harm.** ICMM's largest fatal cause is mobile-equipment interaction — remedied by proximity detection and LiDAR, not by us. | The document-shaped slice is real *and* it is a minority. Own the boundary. |
| 3 | **Utilities is a HYPOTHESIS, not a finding.** Refining (CSB) and mining (ICMM) are verified. Utilities rests on a plausible but unverified argument (OSHA controlling-employer, NFPA 70E, contractor-heavy line work). | The UI shows `HYPOTHESIS — NOT VERIFIED` in amber. |
| 4 | **Contractor safety is improving on an exposure-adjusted basis.** ICMM 2024: contractor share of fatalities fell 69%→45%; contractor fatality frequency (0.012) was *below* employees' (0.020). | Do not claim a worsening contractor gap. |
| 5 | **Services and Retail: no benefit.** They do not run permit-to-work. | Claiming SURE-wide coverage is how you get caught. |
| 6 | **The competitive scan is incomplete.** Cority, Avetta, ISN, Honeywell, eVision, SAP unverified. | If one ships permit-review reasoning, criterion (d) fails. |

---

## 10. Verification Status

The distinction between *"the tests pass"* and *"the product works"* is the whole discipline of this
project. Here it is, without softening.

### ✅ Verified by test

| # | What was proven | How |
|---|---|---|
| 1 | Provenance verifier **rejects a hallucinated control**, a paraphrase of a real rule, and an empty citation — and **accepts** a genuine procedure quote | Unit test. A fabricated sentence (*"…shall record the ambient temperature in the site logbook…"*) returns `UNVERIFIED` and forces `confidence → low` |
| 2 | Backlog scanner **finds the Deer Park permit** (10 defects) and **does not false-positive** the well-formed permit | A reviewer that flags everything is as useless as one that flags nothing — the negative case matters as much as the positive |
| 3 | The buried safeguard is **recovered verbatim** from the permit prose | *"…prior to opening the line the crew should stop and obtain an operator to be present at the flange…"* |
| 4 | 8 LangGraph nodes compile; **8/8 agent prompts build for all 3 industry packs**; every prompt carries the two overriding rules | Assertion on `NEVER INVENT A CONTROL` and `YOU DO NOT AUTHORISE ANYTHING` |
| 5 | **12/12 page × industry-pack combinations render** | Streamlit `AppTest` |
| 6 | Incident corpus integrity: every VERIFIED entry carries a source URL; every ILLUSTRATIVE entry is explicitly labelled | Assertion — cannot silently ship an unlabelled fake fatality |

### ⚠️ NOT verified — the gap that matters

**The live LLM path has never been run.** There was no API key in the build environment, so:

- The *structure*, the *provenance layer*, the *scanner* and the *UI* are proven.
- **The quality of the agents' actual reasoning is not.**

Specifically unproven, and each is a demo-critical question:

1. Does the **Hold Point Enforcer** actually find the buried stop-work sentence in PTW-2026-0417?
   *The entire demo hangs on this single moment.*
2. Does the **Scope Decomposer** correctly split the five bundled tasks?
3. Does the **Supervisor** reach `REJECT` on the Deer Park permit and `AUTHORISE` on the clean one —
   i.e. is it *calibrated*, or does it just flag everything?
4. Do the agents produce **verifiable quotes**, or do they paraphrase (in which case the provenance
   layer will correctly flag them UNVERIFIED and the review will look weak)?

> **Do not demo until this is closed.** If the agents produce mush, none of the architecture matters.
> Add `OPENAI_API_KEY` to a local `.env` (or Streamlit Cloud secrets) and run PTW-2026-0417.

### ⚠️ Also open

- **The competitive scan is incomplete** (§3). Cority, Avetta, ISN, Honeywell, eVision and SAP were
  never scanned. If one already ships permit *review* reasoning — as opposed to a permit *form* —
  the whitespace claim weakens and we need to know before it is made on stage.

---

## 11. Roadmap

**Phase 0 — Prove the reasoning (days).** Add an API key; run the seven agents end-to-end; tune
prompts against the five permits. Finish the competitive scan.

**Phase 1 — Make it real (weeks).** Read permits *out of* SAP WCM / Maximo / Enablon and write
findings back. Replace TF-IDF retrieval with real embeddings. Persist reviews with an immutable audit
trail.

**Phase 2 — Make it trustworthy (weeks).** Structured/tool-call output with schema validation.
Span-level provenance (character offsets into source PDFs). Formal authorise/hold/reject workflow with
sign-off. Evaluation harness against a golden set of historically defective permits.

**Phase 3 — Make it enterprise (weeks).** SSO/RBAC. Access-scoped retrieval. Full tracing and FinOps.
Live unit-state feed from the DCS/historian for real-time hazard-coverage checks.

**Phase 4 — New industry packs.** Refining and mining are verified. **Close the utilities hypothesis
first** with IOGP, OSHA and EEI contractor-fatality data before selling into it.

---

## 12. The Three-Minute Demo

The demo is the product. Structure it so the room feels the problem before it sees the software.

### 0:00–0:35 — The sentence (no software on screen)

> *"On 10 October 2024, two contract workers opened a hydrogen sulphide line at the Deer Park
> refinery. Twenty-seven thousand pounds of H₂S was released. Both of them died.*
>
> *In February this year the Chemical Safety Board published its final report. It found the permit
> covered multiple jobs with varying hazards and no clear hold points. And it found this —*
>
> *'Workers overlooked a written instruction to stop work and obtain an operator's presence before
> opening the hydrogen sulfide piping.'*
>
> *The instruction was already on the permit. It was written down. Somebody read past it."*

**Pause.** Do not fill the silence.

### 0:35–1:00 — The insight

> *"Every AI product in this space helps you WRITE a better permit. Enablon's ships today — it checks
> your description quality and recommends hazards. But the description wasn't poor. The hazard wasn't
> missing. The safeguard was already there.*
>
> *What was missing was somebody whose only job was to attack the finished permit and refuse to let
> it through."*

### 1:00–2:15 — The demo. Permit Review → PTW-2026-0417

Show, in this order — the order is the argument:

1. **The permit as submitted.** Five bundled jobs. Hold points: **NONE**. Let them see it.
2. **Run the review.** Seven agents.
3. **Stop on the Hold Point Enforcer.** It has pulled the buried sentence out of the narrative —
   *"prior to opening the line the crew should stop and obtain an operator to be present at the
   flange"* — and rewritten it as an enforced, signed hold point. **This is the moment. Let it land.**
4. **The verdict: REJECT.** Not a warning. A refusal.
5. **The citation badges.** Every control traced to a real procedure, verified *by code*. Say:
   *"An AI that invents a safety control has manufactured false assurance inside the one system built
   to prevent it. So we don't ask the model to be honest — we check."*
6. **The precedent match.** *"This permit shares four structural features with the permit at Deer
   Park."*

### 2:15–2:45 — The business case. Backlog Scan

> *"Now run it over permits that were already authorised, worked and closed. One in five carries the
> same structural signature. Every one of those is an incident that didn't happen because somebody got
> lucky.*
>
> *And if that number came back zero, we'd tell you the product has no case here. A test that can't
> fail proves nothing."*

### 2:45–3:00 — Close with the limits, not the claims

> *"It would not have prevented the Deer Park root cause — that was equipment mis-identification, and
> the permit failures were contributing. The slice of field safety that lives inside documents is
> real, and it's a minority of the harm. Refining and mining are evidenced; utilities is a hypothesis
> and we label it as one.*
>
> *A permit cannot be issued without passing through this gate. That's why it survives contact with
> an operations budget — and why it doesn't die in the pilot graveyard with everything else."*

**Why closing on limits wins.** Every other team closes on claims. Closing on what your product
*cannot* do — in a safety context, in front of people who know these industries — reads as
credibility, not weakness. It is also the only close that survives Q&A, because you have already said
the thing they were about to ask.

---

## 13. Topaz Fabric Import Summary

```yaml
asset_type: agentic_solution
agents: 7                 # 8 prompt roles; Supervisor acts twice
workflows: 1              # 8-node LangGraph, sequential
industry_packs: 3         # refining (verified) · mining (verified) · utilities (HYPOTHESIS)
knowledge_corpora: 3      # procedures · permits · major-accident investigations
models: GPT-4o primary, Claude Sonnet automatic failover
guardrails:
  - programmatic citation verification (code, not prompt) — rejects hallucinated controls
  - mandatory human authorisation gate (PENDING_HUMAN_AUTHORISATION)
  - fail-loud parsing (no silent empty results in a safety system)
  - verified/illustrative separation in the evidence corpus
pii: none
production_readiness: prototype — see §10
```

### The reusable IP

1. **The adversarial supervisor pattern** — a supervisor that plans an attack, then audits its own
   specialists against the plan it set. Domain-agnostic.
2. **Programmatic provenance verification** — the code that proves a model's citation is real and
   flags it when it isn't. This is the single most transferable asset in the portfolio: it is what
   makes *any* LLM safe to deploy in a domain where a confident wrong answer causes harm.
3. **Incident-precedent matching** — turning a corpus of investigation reports into a live,
   structural control at the moment of decision. Applicable anywhere an industry investigates its own
   failures.
4. **The swappable domain pack** — industry content fully separated from agent logic.

Everything else — the permits, the procedures, the hazard vocabulary — is a **pack** to be replaced
per client.
