# HOLDPOINT

**The adversary at the permit gate.**

---

## The sentence this exists for

On 10 October 2024, contract workers opened a hydrogen sulphide line at the PEMEX Deer Park
refinery. Over 27,000 lb of H₂S was released. **Two contract workers were killed.**

The US Chemical Safety Board's final report (23 February 2026) found:

> "The refinery issued a broad work permit covering multiple jobs with varying hazards and without
> clear hold points."

> "Workers overlooked a written instruction to stop work and obtain an operator's presence before
> opening the hydrogen sulfide piping."

Read the second one again. **The instruction was already on the permit.** It was buried in a
narrative field, inside a scope covering five different jobs, and it was read past.

A tool that *recommends hazards* would have recommended a hazard that was already listed. What was
missing was an adversary whose only job was to attack the finished permit and refuse to let it
through.

That is HOLDPOINT.

---

## What it does

HOLDPOINT sits **in front of the authorisation gate**. A permit pack goes in — the permit, the
isolation plan, the JSA, the assigned people with their competencies, and the live state of the unit
including every other permit already active on it. Seven agents attack it. A recommendation comes
out. **A human decides.**

| Agent | Job |
|---|---|
| **Supervisor** (plan) | Decides where the danger hides, and directs the attack |
| **Scope Decomposer** | Is this one job, or five wearing a trench coat? An over-broad permit is the Deer Park structure |
| **Hazard Coverage Challenger** | Is that control real, or is it the word "carefully"? |
| **Hold Point Enforcer** | What safeguard is buried in the prose where nobody will see it? **The most important agent in the system** |
| **Competency Matcher** | Is *this person* qualified for *this hazard*? Induction is not competence |
| **Isolation & SIMOPS Verifier** | Is the isolation adequate — and what else is live on this unit right now? |
| **Incident Precedent Analyst** | Which historical fatal accident does this permit structurally resemble? |
| **Supervisor** (verdict) | AUTHORISE · HOLD_WITH_CONDITIONS · REJECT — advisory only |

---

## The two things that make it trustworthy

### 1. Provenance is a code check, not a prompt

Every control the agents claim is *mandated* must quote a real site procedure **verbatim**, and
`core/provenance.py` then **programmatically verifies that the quoted sentence actually exists** in
the procedure corpus. Assertions whose quotes cannot be found are shown to the authoriser as
**UNVERIFIED**, with confidence downgraded — never as fact.

The model cannot talk its way past this, because it is code.

> An AI that invents a safety control has manufactured false assurance inside the one system built
> to prevent false assurance. That is worse than no AI at all.

This is unit-tested: the verifier accepts a real procedure quote and **rejects a hallucinated
control, a paraphrase, and an empty citation**.

### 2. It never authorises anything

Every output is stamped `PENDING_HUMAN_AUTHORISATION`. HOLDPOINT is decision support. A qualified
human authoriser makes the call.

---

## The metric that decides the business case

**Backlog Scan** runs over permits that were *already authorised, worked and closed without
incident*, and counts how many carried the Deer Park structural signature — an over-broad scope with
a safeguard that nothing enforces.

**Every one it finds is an incident that did not happen by luck.**

If the count is **zero**, the product has no case and we say so. A test that cannot fail proves
nothing.

---

## Honest limits — stated before anyone has to ask

- **It would not have prevented the Deer Park root cause.** The CSB's root cause was failure to
  positively identify the correct equipment (workers opened a near-identical flange ~5 ft away). The
  permit deficiencies were *contributing*. HOLDPOINT addresses the structure that let the root cause
  become fatal — not the root cause.
- **It is a minority of the harm.** ICMM's largest fatal cause in mining is mobile-equipment
  interaction, remedied by proximity detection and LiDAR. The document-shaped slice of field safety
  is real, and it is a minority.
- **Utilities is a hypothesis, not a finding.** Refining and mining rest on verified evidence (CSB,
  ICMM). The utilities pack rests on a plausible but *unverified* argument. The app labels it as
  such.
- **The incumbent is real.** Enablon ships an "AI-powered Permit Advisor" that *"checks description
  quality, and recommends hazards and controls."* That is a **drafting aid for the author**.
  HOLDPOINT is an **adversary attacking the finished permit**. At Deer Park the description was not
  poor and the hazard was not missing — the safeguard was already written down. Different job.

---

## Data provenance

Permits and site procedures here are **illustrative** — written to carry the structural defects real
investigations describe. The incident corpus distinguishes **verified** investigations (CSB, Cullen
Inquiry, ICMM — quoting the investigators' own words, with source URLs) from **illustrative**
patterns, and never presents one as the other.

---

## Architecture

```
Streamlit UI ──▶ LangGraph (8 nodes) ──▶ GPT-4o (Claude Sonnet failover)
                        │
                        ├─▶ core/provenance.py   verifies every citation against real procedures
                        ├─▶ core/backlog.py      deterministic structural pre-screen
                        ├─▶ core/domains.py      industry packs: refining · mining · utilities
                        └─▶ data/incidents.py    CSB · Cullen · ICMM corpus (RAG precedent match)
```

The agent graph contains **no industry-specific logic**. Swapping the site pack re-targets all seven
agents without touching agent code.

---

## Run

```bash
pip install -r requirements.txt
cp .env.example .env      # add OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY for failover)
streamlit run app.py
```

Start with **PTW-2026-0417** — it is built to the shape the CSB described.
