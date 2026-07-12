"""
HOLDPOINT — Permit Review Graph
===============================

    plan ─▶ decompose_scope ─▶ challenge_hazards ─▶ enforce_hold_points
         ─▶ match_competency ─▶ verify_isolation_simops ─▶ match_precedent ─▶ verdict

A supervisor plans the attack, five specialists execute it, an incident-precedent analyst tells
the authoriser which historical fatal accident this permit resembles, and the supervisor issues
a recommendation — AUTHORISE, HOLD_WITH_CONDITIONS or REJECT — which a human then decides on.

Every control the specialists assert is run through core/provenance.py, which checks the quoted
sentence against the real procedure corpus. Assertions whose quotes cannot be found are flagged
UNVERIFIED and their confidence downgraded. The model cannot talk its way past that check,
because it is code.
"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_openai_primary
from core.prompts import get_prompt
from core.domains import get_site
from core.provenance import verify_assertions, provenance_summary
from core.reality import conditions_brief, check_permit_against_reality
from core.vectorstore import add_documents, search_documents, COLLECTION_INCIDENTS
from data.procedures import procedure_corpus, procedures_as_text
from data.incidents import incident_corpus, incident_as_text


class PermitState(TypedDict):
    permit: dict
    plan: dict
    scope: dict
    hazards: dict
    hold_points: dict
    competency: dict
    isolation_simops: dict
    precedent: dict
    verdict: dict
    provenance: dict
    reality: dict
    current_step: str


# --- JSON helpers -------------------------------------------------------------------------

def _parse(content: str, expect: str = "object") -> dict | list:
    """Parse the model's JSON. On failure return a structure that FAILS LOUDLY.

    A silent empty result in a safety system reads as 'nothing wrong here'. That is the most
    dangerous possible failure mode, so a parse failure is surfaced as an explicit finding.
    """
    try:
        if expect == "array":
            return json.loads(content[content.find("["):content.rfind("]") + 1])
        return json.loads(content[content.find("{"):content.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        if expect == "array":
            return []
        return {
            "parse_error": True,
            "raw": content[:800],
            "note": "Agent output could not be parsed. This finding is UNRELIABLE — treat as a "
                    "failed review, not as a clean permit.",
        }


def _permit_brief(p: dict) -> str:
    """The permit pack as the agents see it."""
    personnel = "\n".join(
        f"  - {x['name']} ({x['company']}) — {x['role']}\n"
        f"      induction: {x.get('site_induction', 'unknown')}\n"
        f"      competencies: {', '.join(x.get('competencies', [])) or 'none recorded'}\n"
        f"      H2S competency: {x.get('h2s_competency', 'not recorded')}"
        + (f"\n      confined space competency: {x['confined_space_competency']}"
           if x.get("confined_space_competency") else "")
        for x in p.get("personnel", [])
    )
    concurrent = "\n".join(
        f"  - {c['permit_id']} [{c['status']}] on {c['unit']}: {c['description']}"
        for c in p.get("concurrent_permits", [])
    ) or "  (none declared)"

    return f"""PERMIT {p['permit_id']} — {p['title']}
Unit: {p['unit']}
Requested by: {p['requested_by']}
Shift: {p['shift']}

--- WORK DESCRIPTION (as written by the requester) ---
{p['work_description']}

--- HAZARDS IDENTIFIED ON THE PERMIT ---
{chr(10).join('  - ' + h for h in p.get('hazards_identified', [])) or '  (none)'}

--- CONTROLS LISTED ON THE PERMIT ---
{chr(10).join('  - ' + c for c in p.get('controls_listed', [])) or '  (none)'}

--- HOLD POINTS LISTED ON THE FACE OF THE PERMIT ---
{chr(10).join('  - ' + h for h in p.get('hold_points_listed', [])) or '  *** NONE LISTED ***'}

--- ISOLATION PLAN ---
{p.get('isolation_plan', '(none supplied)')}

--- JSA ---
{p.get('jsa_summary', '(none supplied)')}

--- PERSONNEL ASSIGNED ---
{personnel or '  (none listed)'}

--- CURRENT STATE OF THE UNIT ---
{p.get('unit_state', '(not supplied)')}

--- OTHER PERMITS LIVE OR PENDING ON THIS UNIT ---
{concurrent}

{conditions_brief(p, get_site())}"""


def _ask(role: str, prompt: str, expect: str = "object"):
    llm = get_openai_primary()
    resp = llm.invoke([
        SystemMessage(content=get_prompt(role)),
        HumanMessage(content=prompt),
    ])
    return _parse(resp.content, expect)


# --- Nodes --------------------------------------------------------------------------------

def plan(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("supervisor_plan", f"""Plan the attack on this permit.

{_permit_brief(p)}

Return JSON:
{{
  "where_danger_hides": ["the specific things about THIS permit that could kill someone"],
  "priority_order": ["which specialist findings matter most, and why"],
  "what_would_make_this_lethal": "one paragraph — the credible accident sequence this permit permits",
  "initial_concern_level": "low|moderate|high|severe"
}}""")
    return {"plan": out, "current_step": "decompose_scope"}


def decompose_scope(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("scope_decomposer", f"""Decompose the scope of this permit.

{_permit_brief(p)}

SITE PROCEDURES (quote verbatim when you cite a requirement):
{procedures_as_text()}

Return JSON:
{{
  "distinct_tasks": [
    {{"task": "...", "location": "...", "hazards": ["..."], "performed_by": "...",
      "shares_hazards_with_others": true/false}}
  ],
  "task_count": <int>,
  "must_be_split": true/false,
  "split_rationale": "why these tasks can or cannot share one permit",
  "source_quote": "VERBATIM sentence from the procedures that governs permit scope",
  "severity": "none|low|medium|high|critical",
  "confidence": "high|medium|low"
}}""")
    return {"scope": out, "current_step": "challenge_hazards"}


def challenge_hazards(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("hazard_coverage", f"""Attack this permit's claim to be adequately controlled.

{_permit_brief(p)}

SITE PROCEDURES (you MUST quote these verbatim for every mandated control):
{procedures_as_text()}

Return JSON:
{{
  "findings": [
    {{"hazard": "...",
      "identified_on_permit": true/false,
      "control_listed": "what the permit says, or 'none'",
      "control_is_verifiable": true/false,
      "why_inadequate": "...",
      "required_control": "what the procedure actually mandates",
      "source_quote": "VERBATIM sentence from the site procedures — copy it exactly",
      "is_inference": false,
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ],
  "unidentified_hazards": ["hazards present in this work that the permit never names"]
}}""", expect="object")
    return {"hazards": out, "current_step": "enforce_hold_points"}


def enforce_hold_points(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("hold_point_enforcer", f"""Find every hold point buried in the prose of this permit.

{_permit_brief(p)}

SITE PROCEDURES (quote verbatim):
{procedures_as_text()}

Read the WORK DESCRIPTION, the JSA and the ISOLATION PLAN as prose. Hunt for any sentence
requiring work to stop and something to be verified before it continues.

Return JSON:
{{
  "buried_hold_points": [
    {{"instruction_found": "VERBATIM sentence copied from the permit where the safeguard is buried",
      "buried_in": "work_description|jsa|isolation_plan",
      "currently_enforced": false,
      "why_this_matters": "the credible consequence of this being read past",
      "should_read_as": "HP<n>: <discrete, checkable step> — attended and signed by <named role>",
      "source_quote": "VERBATIM sentence from the SITE PROCEDURES requiring hold points to be discrete steps",
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ],
  "missing_hold_points": [
    {{"required_hold_point": "...",
      "source_quote": "VERBATIM procedure sentence requiring it",
      "appears_on_permit": false,
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ],
  "verdict": "one blunt sentence on whether this permit's safeguards are enforced or merely written"
}}""")
    return {"hold_points": out, "current_step": "match_competency"}


def match_competency(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("competency_matcher", f"""Check every named individual against the hazards they will face.

{_permit_brief(p)}

SITE PROCEDURES (quote verbatim):
{procedures_as_text()}

Return JSON:
{{
  "findings": [
    {{"person": "...", "company": "...", "role": "...",
      "hazards_personally_exposed_to": ["..."],
      "competency_gaps": [
        {{"hazard": "...", "status": "expired|missing|current", "detail": "..."}}
      ],
      "cleared_to_work": true/false,
      "source_quote": "VERBATIM procedure sentence on competency",
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ],
  "reassignment_briefing_gap": "any person moved between units without a recorded hazard briefing, or 'none'",
  "performing_authority_clear": true/false
}}""")
    return {"competency": out, "current_step": "verify_isolation_simops"}


def verify_isolation_simops(state: PermitState) -> dict:
    p = state["permit"]
    out = _ask("isolation_simops", f"""Verify the isolation, then check for simultaneous-operations conflicts.

{_permit_brief(p)}

SITE PROCEDURES (quote verbatim):
{procedures_as_text()}

Return JSON:
{{
  "isolation_findings": [
    {{"issue": "...",
      "energy_source_missed": "... or 'none'",
      "method_adequate": true/false,
      "why": "...",
      "source_quote": "VERBATIM procedure sentence governing this isolation",
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ],
  "simops_conflicts": [
    {{"conflicting_permit_id": "...",
      "conflict": "...",
      "credible_accident": "the accident this combination creates",
      "source_quote": "VERBATIM procedure sentence on concurrent work",
      "severity": "low|medium|high|critical",
      "confidence": "high|medium|low"}}
  ]
}}""")
    return {"isolation_simops": out, "current_step": "match_precedent"}


RETRIEVAL_THRESHOLD = 8  # below this, retrieval adds nothing — pass the whole corpus


def _retrieve_incidents(state: PermitState, k: int = 4) -> tuple[list[dict], str]:
    """Retrieve the incidents most structurally similar to this permit.

    With a corpus this small, retrieval is pointless and the honest thing is to pass everything —
    a top-k over six documents just risks dropping the one that mattered. The retrieval path exists
    because a real client corpus is hundreds of investigation reports, and at that size the full
    corpus cannot go in the prompt.

    The query is built from the SPECIALISTS' FINDINGS, not the permit text, because we are matching
    on STRUCTURAL failure shape ("over-broad scope, unenforced stop-work instruction") rather than
    on subject matter ("both involve H2S"). Matching on topic is how you retrieve the wrong lesson.
    """
    all_incidents = incident_corpus()

    if len(all_incidents) <= RETRIEVAL_THRESHOLD:
        return all_incidents, f"full corpus ({len(all_incidents)} incidents — below retrieval threshold)"

    for inc in all_incidents:
        add_documents(
            COLLECTION_INCIDENTS,
            [incident_as_text(inc)],
            [{"incident_id": inc["incident_id"]}],
        )

    query = " ".join([
        json.dumps(state.get("scope", {}), default=str),
        json.dumps(state.get("hold_points", {}), default=str),
        json.dumps(state.get("isolation_simops", {}), default=str),
        state["permit"].get("unit_state", ""),
    ])
    hits = search_documents(COLLECTION_INCIDENTS, query, k=k)
    ids = {doc.metadata.get("incident_id") for doc, _ in hits}
    retrieved = [i for i in all_incidents if i["incident_id"] in ids]
    return retrieved or all_incidents, f"retrieved top-{k} of {len(all_incidents)} by structural similarity"


def match_precedent(state: PermitState) -> dict:
    """Which historical fatal accident does this permit structurally resemble?"""
    p = state["permit"]
    incidents, retrieval_note = _retrieve_incidents(state)
    corpus = "\n\n".join(incident_as_text(i) for i in incidents)

    out = _ask("precedent_matcher", f"""Match this permit against the major-accident corpus.

{_permit_brief(p)}

--- WHAT OUR SPECIALISTS FOUND ---
Scope: {json.dumps(state.get('scope', {}), default=str)[:1200]}
Hold points: {json.dumps(state.get('hold_points', {}), default=str)[:1200]}
Isolation/SIMOPS: {json.dumps(state.get('isolation_simops', {}), default=str)[:1200]}

--- MAJOR-ACCIDENT CORPUS (cite ONLY from here) ---
{corpus}

Return JSON:
{{
  "closest_match": {{
     "incident_id": "...",
     "title": "...",
     "verification": "verified|illustrative",
     "fatalities": <int>,
     "structural_features_shared": ["..."],
     "structural_features_NOT_shared": ["be honest — an overstated match is less persuasive"],
     "investigator_quote": "the investigator's own words, from the corpus",
     "the_sentence": "ONE sentence the authoriser will remember, naming what this permit shares with a permit that killed people",
     "match_strength": "strong|moderate|weak"
  }},
  "other_matches": [{{"incident_id": "...", "why": "..."}}],
  "honesty_note": "if the closest match is ILLUSTRATIVE rather than a real investigated accident, say so here plainly"
}}""")
    if isinstance(out, dict):
        out["retrieval"] = retrieval_note
    return {"precedent": out, "current_step": "verdict"}


def verdict(state: PermitState) -> dict:
    """Provenance-check every assertion, THEN ask the supervisor to decide."""
    corpus = procedure_corpus()

    # Facts established by real external APIs (daylight, wind). These are NOT model output, so they
    # bypass the provenance check — there is nothing to hallucinate. They are simply true.
    reality = check_permit_against_reality(state["permit"], get_site())

    # Gather every assertion that claims a procedural requirement, and verify its quote.
    assertions: list[dict] = []
    for group, key in [
        (state.get("hazards", {}), "findings"),
        (state.get("competency", {}), "findings"),
        (state.get("isolation_simops", {}), "isolation_findings"),
        (state.get("isolation_simops", {}), "simops_conflicts"),
        (state.get("hold_points", {}), "buried_hold_points"),
        (state.get("hold_points", {}), "missing_hold_points"),
    ]:
        if isinstance(group, dict):
            for item in group.get(key, []) or []:
                if isinstance(item, dict):
                    assertions.append({**item, "_group": key})

    scope = state.get("scope", {})
    if isinstance(scope, dict) and scope.get("source_quote"):
        assertions.append({**scope, "_group": "scope"})

    verified = verify_assertions(assertions, corpus)
    summary = provenance_summary(verified)

    # Write the verified flags back into the specialist outputs for display.
    by_group: dict[str, list] = {}
    for v in verified:
        by_group.setdefault(v["_group"], []).append(v)

    unverified = [v for v in verified if not v.get("citation_verified")]
    unverified_note = ""
    if unverified:
        unverified_note = (
            f"\n\n*** PROVENANCE WARNING ***\n{len(unverified)} of {len(verified)} assertions quoted a "
            f"procedure sentence that COULD NOT BE FOUND in the real procedure corpus. Those "
            f"assertions may be paraphrased, misattributed or fabricated. Weight them accordingly "
            f"and tell the authoriser to verify them by hand.\n"
        )

    out = _ask("supervisor_verdict", f"""Issue your recommendation on this permit.

{_permit_brief(state['permit'])}

--- YOUR PLAN ---
{json.dumps(state.get('plan', {}), indent=2, default=str)[:1500]}

--- SPECIALIST FINDINGS ---
SCOPE: {json.dumps(state.get('scope', {}), indent=2, default=str)[:2000]}
HAZARD COVERAGE: {json.dumps(state.get('hazards', {}), indent=2, default=str)[:2000]}
HOLD POINTS: {json.dumps(state.get('hold_points', {}), indent=2, default=str)[:2500]}
COMPETENCY: {json.dumps(state.get('competency', {}), indent=2, default=str)[:2000]}
ISOLATION & SIMOPS: {json.dumps(state.get('isolation_simops', {}), indent=2, default=str)[:2000]}
PRECEDENT: {json.dumps(state.get('precedent', {}), indent=2, default=str)[:1500]}

--- FACTS ESTABLISHED BY LIVE EXTERNAL DATA (not model output — these are simply true) ---
{json.dumps(reality.get('findings', []), indent=2, default=str)[:2000] or "none"}
{reality.get('note', '')}
{unverified_note}
Return JSON:
{{
  "recommendation": "AUTHORISE|HOLD_WITH_CONDITIONS|REJECT",
  "headline": "one sentence the authoriser reads first",
  "rationale": "2-3 paragraphs — why this decision, grounded in the specific findings",
  "blocking_findings": [
     {{"finding": "...", "why_blocking": "...", "raised_by": "which specialist"}}
  ],
  "conditions_to_close": [
     {{"condition": "...", "owner": "...", "must_be_closed_before": "..."}}
  ],
  "credible_accident_prevented": "if this permit went through as written, what would plausibly happen",
  "what_the_permit_got_RIGHT": ["be fair — name what was done well, or state 'nothing of note'"],
  "human_authoriser_note": "explicit statement that a qualified human must make the actual decision"
}}""")

    return {
        "verdict": out,
        "provenance": {**summary, "assertions": verified, "by_group": by_group},
        "reality": reality,
        "current_step": "complete",
    }


# --- Build --------------------------------------------------------------------------------

def build_permit_graph():
    g = StateGraph(PermitState)
    g.add_node("plan", plan)
    g.add_node("decompose_scope", decompose_scope)
    g.add_node("challenge_hazards", challenge_hazards)
    g.add_node("enforce_hold_points", enforce_hold_points)
    g.add_node("match_competency", match_competency)
    g.add_node("verify_isolation_simops", verify_isolation_simops)
    g.add_node("match_precedent", match_precedent)
    g.add_node("verdict", verdict)

    g.set_entry_point("plan")
    g.add_edge("plan", "decompose_scope")
    g.add_edge("decompose_scope", "challenge_hazards")
    g.add_edge("challenge_hazards", "enforce_hold_points")
    g.add_edge("enforce_hold_points", "match_competency")
    g.add_edge("match_competency", "verify_isolation_simops")
    g.add_edge("verify_isolation_simops", "match_precedent")
    g.add_edge("match_precedent", "verdict")
    g.add_edge("verdict", END)
    return g.compile()


def _initial_state(permit: dict) -> PermitState:
    return {
        "permit": permit,
        "plan": {}, "scope": {}, "hazards": {}, "hold_points": {},
        "competency": {}, "isolation_simops": {}, "precedent": {},
        "verdict": {}, "provenance": {}, "reality": {}, "current_step": "plan",
    }


def _finalise(state: dict) -> dict:
    state["review_status"] = "PENDING_HUMAN_AUTHORISATION"
    state["disclaimer"] = (
        "HOLDPOINT is decision support. It does not authorise work. A qualified human authoriser "
        "must make the decision. Findings marked UNVERIFIED could not be traced to a real procedure "
        "and must be checked by hand."
    )
    return state


def review_permit(permit: dict) -> dict:
    """Run the full adversarial review, blocking. Returns the complete state."""
    return _finalise(build_permit_graph().invoke(_initial_state(permit)))


def review_permit_stream(permit: dict):
    """Run the review, yielding after EACH agent finishes.

    Yields (node_name, accumulated_state) so the UI can advance the pipeline on REAL node
    completion. A progress bar driven by a timer is a lie about what the system is doing —
    this one moves when an agent actually returns.

    Final yield is ("__done__", complete_state).
    """
    graph = build_permit_graph()
    state: dict = dict(_initial_state(permit))

    for chunk in graph.stream(state, stream_mode="updates"):
        for node_name, update in chunk.items():
            if isinstance(update, dict):
                state.update(update)
            yield node_name, state

    yield "__done__", _finalise(state)


# The keys MUST match the graph node names exactly — the UI advances the pipeline by matching
# the streamed node name against this list.
STEP_LABELS = [
    ("plan", "Supervisor plans the attack"),
    ("decompose_scope", "Scope Decomposer — is this one job or many?"),
    ("challenge_hazards", "Hazard Coverage Challenger — are the controls real?"),
    ("enforce_hold_points", "Hold Point Enforcer — what is buried in the prose?"),
    ("match_competency", "Competency Matcher — is this person qualified for this hazard?"),
    ("verify_isolation_simops", "Isolation & SIMOPS Verifier — what else is live on this unit?"),
    ("match_precedent", "Incident Precedent — which accident does this resemble?"),
    ("verdict", "Supervisor — authorise, hold, or reject"),
]
