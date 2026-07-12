"""Page 1 — Adversarial permit review. The core of the product."""

import os
import sys
import json

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Permit Review | HOLDPOINT", page_icon="🔍", layout="wide")

from core.styles import (inject_styles, render_page_header, render_section,
                         render_pipeline, render_empty_state, render_kpi_row, severity_badge)
from core.ui import (bootstrap, require_llm, render_verdict, render_authorisation_gate,
                     citation_badge, render_quote, render_data_provenance)
from core.backlog import scan_permit
from data.permits import PERMITS, get_permit
from agents.permit_review.graph import review_permit, STEP_LABELS

inject_styles()
site = bootstrap()


def severity_icon(sev: str | None) -> str:
    """Colour-code severity. Defined before use — this module executes top to bottom."""
    return {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get((sev or "").lower(), "⚪")


render_page_header(
    title="Permit Review",
    description="Seven agents attack a permit before it reaches the authoriser. A human still decides.",
    ai_type="agentic",
)

render_pipeline([
    "Supervisor plans", "Scope", "Hazards", "Hold Points",
    "Competency", "Isolation & SIMOPS", "Precedent", "Verdict",
])

# --- Select a permit ---------------------------------------------------------------------
render_section("Select a permit awaiting authorisation")

labels = {
    p["permit_id"]: f"{p['permit_id']} — {p['title']}"
    + ("   ⚠️ DEER PARK PATTERN" if scan_permit(p)["deer_park_shape"] else "")
    for p in PERMITS
}

col_sel, col_run = st.columns([4, 1])
with col_sel:
    permit_id = st.selectbox(
        "Permit", list(labels), format_func=lambda k: labels[k], label_visibility="collapsed"
    )
with col_run:
    run = st.button("Run Review", type="primary", use_container_width=True)

permit = get_permit(permit_id)
pre = scan_permit(permit)

if pre["deer_park_shape"]:
    st.error(
        "**Structural pre-screen: this permit carries the Deer Park signature.** An over-broad scope "
        "with a safeguard that nothing enforces. The agents will now attack it properly."
    )
elif pre["clean"]:
    st.success("**Structural pre-screen: no defects found.** The agents will still attack it — "
               "a reviewer that only ever agrees with the pre-screen is decoration.")
else:
    st.warning(f"**Structural pre-screen: {pre['defect_count']} defect(s), worst severity "
               f"{pre['worst_severity'].upper()}.**")

with st.expander("View the permit pack as submitted", expanded=False):
    st.markdown(f"**Unit**: {permit['unit']} · **Shift**: {permit['shift']} · "
                f"**Requested by**: {permit['requested_by']}")
    st.markdown("**Work description**")
    st.text(permit["work_description"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Hazards identified**")
        for h in permit.get("hazards_identified", []):
            st.markdown(f"- {h}")
        st.markdown("**Controls listed**")
        for c in permit.get("controls_listed", []):
            st.markdown(f"- {c}")
    with c2:
        st.markdown("**Hold points listed on the face of the permit**")
        holds = permit.get("hold_points_listed") or []
        if holds:
            for h in holds:
                st.markdown(f"- {h}")
        else:
            st.markdown("🛑 **NONE**")
        st.markdown("**Isolation plan**")
        st.text(permit.get("isolation_plan", ""))
    st.markdown("**Personnel**")
    for p in permit.get("personnel", []):
        st.markdown(
            f"- **{p['name']}** ({p['company']}) — {p['role']} · H2S: `{p.get('h2s_competency', 'n/a')}`"
            + (f" · Confined space: `{p['confined_space_competency']}`"
               if p.get("confined_space_competency") else "")
        )
    st.markdown("**Unit state**")
    st.text(permit.get("unit_state", ""))
    if permit.get("concurrent_permits"):
        st.markdown("**Other permits live on this unit**")
        for c in permit["concurrent_permits"]:
            st.markdown(f"- `{c['permit_id']}` [{c['status']}] — {c['description']}")

st.markdown("---")

# --- Run ---------------------------------------------------------------------------------
if run:
    require_llm()

    with st.status("Seven agents attacking the permit…", expanded=True) as status:
        for _, label in STEP_LABELS:
            st.write(label)
        result = review_permit(permit)
        status.update(label="Review complete — a human must now decide.",
                      state="complete", expanded=False)

    verdict = result.get("verdict", {}) or {}
    prov = result.get("provenance", {}) or {}

    render_verdict(verdict)
    render_authorisation_gate()

    render_kpi_row([
        {"value": str(len(verdict.get("blocking_findings", []) or [])), "label": "Blocking Findings"},
        {"value": str(len(verdict.get("conditions_to_close", []) or [])), "label": "Conditions to Close"},
        {"value": f"{prov.get('verified', 0)}/{prov.get('total', 0)}",
         "label": "Citations Verified",
         "sublabel": f"{prov.get('unverified', 0)} could not be traced"
                     if prov.get("unverified") else "all traced to real procedures"},
        {"value": str(len((result.get('hold_points', {}) or {}).get('buried_hold_points', []) or [])),
         "label": "Buried Safeguards Found", "sublabel": "written down, never enforced"},
    ])

    if prov.get("unverified"):
        st.warning(
            f"**{prov['unverified']} assertion(s) quoted a procedure sentence that could not be found "
            f"in the real procedure corpus.** They are shown below with a warning badge and their "
            f"confidence downgraded. The model may have paraphrased or invented them. Verify by hand."
        )

    if verdict.get("rationale"):
        st.markdown(f"> {verdict['rationale']}")

    # --- The money shot: buried hold points ---------------------------------------------
    hp = result.get("hold_points", {}) or {}
    buried = hp.get("buried_hold_points", []) or []
    if buried:
        render_section("Safeguards buried in the prose",
                       "Written on the permit. Never enforced. This is the Deer Park failure.")
        for b in buried:
            st.markdown(f"**Found in the `{b.get('buried_in', 'permit')}`** &nbsp; "
                        f"{severity_badge(b.get('severity', 'high'))}", unsafe_allow_html=True)
            render_quote(b.get("instruction_found", ""), "as written on the permit — and read past")
            st.markdown(f"**Why this matters:** {b.get('why_this_matters', '')}")
            st.success(f"**Should read as:** {b.get('should_read_as', '')}")
            st.markdown(citation_badge(b), unsafe_allow_html=True)
            if b.get("source_quote"):
                render_quote(b["source_quote"], b.get("citation_document") or "site procedure")
            st.markdown("---")

    missing = hp.get("missing_hold_points", []) or []
    if missing:
        render_section("Hold points the procedures require that appear nowhere")
        for m in missing:
            st.markdown(f"🛑 **{m.get('required_hold_point', '')}** &nbsp; "
                        f"{severity_badge(m.get('severity', 'high'))}", unsafe_allow_html=True)
            st.markdown(citation_badge(m), unsafe_allow_html=True)
            render_quote(m.get("source_quote", ""), m.get("citation_document") or "site procedure")

    # --- Scope ---------------------------------------------------------------------------
    scope = result.get("scope", {}) or {}
    if scope and not scope.get("parse_error"):
        render_section("Scope decomposition",
                       f"{scope.get('task_count', '?')} distinct task(s) in one permit")
        if scope.get("must_be_split"):
            st.error(f"**This permit must be split.** {scope.get('split_rationale', '')}")
        else:
            st.success(f"**Scope is coherent.** {scope.get('split_rationale', '')}")
        for t in scope.get("distinct_tasks", []) or []:
            st.markdown(f"- **{t.get('task', '')}** — hazards: "
                        f"{', '.join(t.get('hazards', []))} · performed by {t.get('performed_by', '?')}")
        st.markdown(citation_badge(scope), unsafe_allow_html=True)
        render_quote(scope.get("source_quote", ""), scope.get("citation_document") or "site procedure")

    # --- Isolation & SIMOPS --------------------------------------------------------------
    iso = result.get("isolation_simops", {}) or {}
    conflicts = iso.get("simops_conflicts", []) or []
    if conflicts:
        render_section("Simultaneous operations conflicts", "What else is live on this unit right now")
        for c in conflicts:
            st.error(f"**Conflict with `{c.get('conflicting_permit_id', '?')}`** — "
                     f"{c.get('conflict', '')}\n\n**Credible accident:** {c.get('credible_accident', '')}")
            st.markdown(citation_badge(c), unsafe_allow_html=True)
    iso_findings = iso.get("isolation_findings", []) or []
    if iso_findings:
        render_section("Isolation adequacy")
        for f in iso_findings:
            st.markdown(f"{severity_badge(f.get('severity', 'medium'))} &nbsp; **{f.get('issue', '')}**",
                        unsafe_allow_html=True)
            st.markdown(f"{f.get('why', '')}")
            st.markdown(citation_badge(f), unsafe_allow_html=True)
            render_quote(f.get("source_quote", ""), f.get("citation_document") or "site procedure")

    # --- Competency ----------------------------------------------------------------------
    comp = result.get("competency", {}) or {}
    cfind = comp.get("findings", []) or []
    if cfind:
        render_section("Competency — person by person, hazard by hazard")
        for f in cfind:
            cleared = f.get("cleared_to_work")
            icon = "✅" if cleared else "🛑"
            with st.expander(f"{icon} {f.get('person', '?')} ({f.get('company', '?')}) — "
                             f"{f.get('role', '')}", expanded=not cleared):
                for g in f.get("competency_gaps", []) or []:
                    status = (g.get("status") or "").lower()
                    line = f"**{g.get('hazard', '')}** — {g.get('status', '')}: {g.get('detail', '')}"
                    if status in ("expired", "missing"):
                        st.error(line)
                    else:
                        st.success(line)
                st.markdown(citation_badge(f), unsafe_allow_html=True)
                render_quote(f.get("source_quote", ""), f.get("citation_document") or "site procedure")
        if comp.get("reassignment_briefing_gap") and \
                comp["reassignment_briefing_gap"].lower() not in ("none", "no", ""):
            st.warning(f"**Reassignment briefing gap:** {comp['reassignment_briefing_gap']}")

    # --- Hazards -------------------------------------------------------------------------
    hz = result.get("hazards", {}) or {}
    hfind = hz.get("findings", []) or []
    if hfind:
        render_section("Hazard coverage", "Is the control real, or is it the word 'carefully'?")
        for f in hfind:
            with st.expander(f"{severity_icon(f.get('severity'))} {f.get('hazard', '')}"):
                st.markdown(f"**On the permit:** {f.get('control_listed', 'none')}")
                st.markdown(f"**Verifiable?** {'yes' if f.get('control_is_verifiable') else '**no**'}")
                st.markdown(f"**Why inadequate:** {f.get('why_inadequate', '')}")
                st.info(f"**Procedure requires:** {f.get('required_control', '')}")
                if f.get("is_inference"):
                    st.caption("⚠ This is the agent's professional inference, not a procedural "
                               "requirement. It is labelled as such deliberately.")
                st.markdown(citation_badge(f), unsafe_allow_html=True)
                render_quote(f.get("source_quote", ""), f.get("citation_document") or "site procedure")
    if hz.get("unidentified_hazards"):
        st.warning("**Hazards present in this work that the permit never names:** "
                   + ", ".join(hz["unidentified_hazards"]))

    # --- Precedent -----------------------------------------------------------------------
    prec = (result.get("precedent", {}) or {}).get("closest_match", {}) or {}
    if prec:
        render_section("Incident precedent", "Which accident does this permit resemble?")
        is_illustrative = (prec.get("verification") or "").lower() == "illustrative"
        box = st.warning if is_illustrative else st.error
        box(f"""**{prec.get('title', '')}** — {prec.get('fatalities', '?')} killed
        · match: **{prec.get('match_strength', '?')}**

{prec.get('the_sentence', '')}""")
        if is_illustrative:
            st.caption("⚠ This is an ILLUSTRATIVE pattern, not a real investigated accident. "
                       "HOLDPOINT will not pass one off as the other.")
        if prec.get("investigator_quote"):
            render_quote(prec["investigator_quote"], "the investigator's own words")
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**Structural features shared**")
            for f in prec.get("structural_features_shared", []) or []:
                st.markdown(f"- {f}")
        with cc2:
            st.markdown("**Not shared — stated honestly**")
            for f in prec.get("structural_features_NOT_shared", []) or []:
                st.markdown(f"- {f}")

    # --- Conditions ----------------------------------------------------------------------
    conds = verdict.get("conditions_to_close", []) or []
    if conds:
        render_section("Conditions that must be closed before work proceeds")
        for c in conds:
            st.markdown(f"- **{c.get('condition', '')}** — owner: {c.get('owner', '?')} · "
                        f"before: {c.get('must_be_closed_before', '?')}")

    if verdict.get("credible_accident_prevented"):
        st.error(f"**If this permit went through as written:** {verdict['credible_accident_prevented']}")

    right = verdict.get("what_the_permit_got_RIGHT", []) or []
    if right:
        st.success("**What the permit got right** (a reviewer that only ever attacks is ignored)\n\n"
                   + "\n".join(f"- {r}" for r in right))

    with st.expander("Raw agent output (JSON)"):
        st.json(result)

else:
    render_data_provenance()
    render_empty_state(
        icon="🔍",
        title="Select a permit and run the review",
        description="Start with PTW-2026-0417 — it is built to the shape the CSB described at Deer Park.",
    )

