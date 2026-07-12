"""Page 1 — Adversarial permit review. The core of the product."""

import os
import sys
import json

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Permit Review | HOLDPOINT", page_icon="🔍", layout="wide")

from core.styles import (inject_styles, render_page_header, render_section,
                         render_pipeline, pipeline_html, render_empty_state, render_kpi_row,
                         severity_badge)
from core.ui import (bootstrap, require_llm, render_verdict, render_authorisation_gate,
                     citation_badge, render_quote, render_data_provenance)
from core.backlog import scan_permit
from core.connectors import get_connector, CONNECTORS, DEFAULT_CONNECTOR
from core.reality import check_permit_against_reality
from core.charts import (shift_vs_darkness, simops_timeline, structural_similarity,
                         provenance_donut, assurance_web)
from data.permits import PERMITS, get_permit
from agents.permit_review.graph import review_permit_stream, STEP_LABELS

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

PIPELINE_STEPS = ["Supervisor plans", "Scope", "Hazards", "Hold Points",
                  "Competency", "Isolation & SIMOPS", "Precedent", "Verdict"]
NODE_ORDER = [k for k, _ in STEP_LABELS]

# A placeholder, not a static render — the graph stream drives this as each agent finishes.
pipeline_slot = st.empty()
pipeline_slot.markdown(pipeline_html(PIPELINE_STEPS), unsafe_allow_html=True)

# ==========================================================================================
# STAGE 1 — INPUTS. Everything below is what goes IN. Nothing here is a review finding.
# ==========================================================================================
render_section("1 \u00b7 Inputs",
               "The permit as submitted, and the real conditions at the work site")

labels = {
    p["permit_id"]: f"{p['permit_id']} \u2014 {p['title']}"
    + ("   \u26a0\ufe0f DEER PARK PATTERN" if scan_permit(p)["deer_park_shape"] else "")
    for p in PERMITS
}

permit_id = st.selectbox(
    "Permit awaiting authorisation", list(labels), format_func=lambda k: labels[k]
)

# Source the permit through whatever system of record is connected. The agents never see the
# vendor's payload shape — the connector normalises it first. Falls back to local fixtures.
conn = get_connector(st.session_state.get("connector", DEFAULT_CONNECTOR))
permit = conn.fetch_canonical(permit_id) or get_permit(permit_id)
pre = scan_permit(permit)

if conn.key != "local":
    st.caption(f"Permit fetched from **{conn.product}** and normalised to HOLDPOINT's canonical "
               f"shape. *(simulated connector — see Connections)*")

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

# --- REAL external conditions. An INPUT to the review, not an output of it. --------------
rc = check_permit_against_reality(permit, site)
cond = rc["conditions"]
ww = rc.get("work_window") or {}
dk = rc.get("darkness")

st.markdown("##### Conditions at the work site, for this permit's own work window")

# State the linkage explicitly. This is WHY the live data is here at all: the permit authorises
# work at a real place on a real date, and two clauses in the site's own H2S standard (darkness,
# wind direction) cannot be judged from the permit alone. They depend on the world outside it.
st.info(
    f"**This permit authorises work at {permit['unit']}, on "
    f"{ww.get('date') or '(no date on permit)'}, {ww.get('shift', '')}.**\n\n"
    f"So HOLDPOINT fetches the real sun and wind **for that place, on that date** — because the "
    f"site's own H2S standard forbids sour work in darkness and requires the wind direction to be "
    f"confirmed. Neither can be judged from the permit alone."
)

if rc.get("unavailable"):
    st.warning(
        "**Live external conditions unavailable.** HOLDPOINT does not guess the weather — daylight "
        "and wind direction must be confirmed by hand at the work location before containment is "
        "broken."
    )
else:
    lc1, lc2, lc3, lc4 = st.columns(4)
    with lc1:
        st.metric("Permit's shift (local)", f"{ww.get('start', '?')}–{ww.get('end', '?')}")
    with lc2:
        st.metric("Sunset → sunrise (local)",
                  f"{dk['sunset_local']}–{dk['sunrise_local'].split(' ')[0]}" if dk else "—")
    with lc3:
        st.metric("Shift hours in darkness",
                  f"{dk['dark_hours']}h / {dk['shift_hours']}h" if dk else "—",
                  delta=f"{dk['dark_pct']}% dark" if dk else None,
                  delta_color="inverse" if dk and dk["any_darkness"] else "off")
    with lc4:
        st.metric("Wind", f"{cond['wind_direction'] or '—'} {cond['wind_speed'] or ''}",
                  help=cond["forecast"] or "")
    st.caption(
        f"🌐 **LIVE DATA — not simulated.** Sun and wind fetched from `{cond['source']}` for "
        f"{cond['site_name']} ({cond['lat']}, {cond['lon']}) on **{cond['date']}** — the permit's "
        f"own work date. The darkness overlap is **computed** from the permit's shift window in the "
        f"site's timezone ({site.get('tz', 'n/a')}), not assumed from the word \"night\"."
    )


    fig_dark = shift_vs_darkness(rc)
    if fig_dark is not None:
        st.plotly_chart(fig_dark, use_container_width=True)

# The SIMOPS picture is an INPUT fact: these permits are already live on this unit.
fig_simops = simops_timeline(permit)
if fig_simops is not None:
    st.markdown("##### What else is live on this unit")
    st.plotly_chart(fig_simops, use_container_width=True)
    st.caption(
        "A simultaneous-operations conflict is a statement about **time** — two permits being live "
        "at once. Text hides that. A timeline does not."
    )

if rc.get("findings"):
    st.error(
        f"**{len(rc['findings'])} conflict(s) between this permit and the real world.** "
        f"Established by live external data **before any agent has run** \u2014 these are facts, not "
        f"model opinions, and they cannot be hallucinations because no model produced them. "
        f"The agents are handed these as evidence."
    )
    for f in rc["findings"]:
        st.markdown(f"{severity_badge(f['severity'])} &nbsp; **{f['finding']}**",
                    unsafe_allow_html=True)
        render_quote(f["procedure_clause"], f["procedure_doc"])
        st.caption(f"✅ Established by **{f['established_by']}** — a real API, not the model. "
                   f"This finding cannot be a hallucination, because no model produced it.")
        st.markdown("")

# --- The assurance web. The point is the edges that AREN'T there. -------------------------
render_section("The assurance chain", "A missing edge is a missing safeguard")

web, broken = assurance_web(permit)
st.plotly_chart(web, use_container_width=True)

if broken:
    st.error(
        f"**{broken} broken link(s).** Red nodes are where the chain fails: a hazard with no "
        f"control, a control nothing enforces, a person without competency for a hazard they will "
        f"personally face. **At Deer Park, the stop-work instruction was a node with no edge to a "
        f"hold point.**"
    )
else:
    st.success(
        "**Assurance chain complete.** Every hazard has a control, every control is enforced by a "
        "hold point, every person is competent for what they face."
    )

st.caption(
    "**What this graph checks, and what it does not.** It traces one chain: hazard → control → "
    "hold point, and person → competency. A complete chain here does **not** mean the permit is "
    "safe — isolation adequacy, darkness and SIMOPS are checked separately, above and below. "
    "A graph that claimed to check everything would be lying."
)

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

st.markdown("")
_, col_run, _ = st.columns([1, 2, 1])
with col_run:
    run = st.button("\u25b6  Run the seven-agent review", type="primary",
                    use_container_width=True)

st.markdown("---")

# ==========================================================================================
# STAGE 2 — THE REVIEW. Everything below this line is OUTPUT.
# ==========================================================================================
if run:
    require_llm()

    render_section("2 \u00b7 The review", "Seven adversarial agents. A human still decides.")

    result = None
    with st.status("Seven agents attacking the permit…", expanded=True) as status:
        log = st.empty()
        done_labels = []

        for node_name, state in review_permit_stream(permit):
            if node_name == "__done__":
                result = state
                break

            idx = NODE_ORDER.index(node_name) if node_name in NODE_ORDER else -1
            label = dict(STEP_LABELS).get(node_name, node_name)

            # Advance the pipeline to the NEXT step: this one just finished.
            pipeline_slot.markdown(
                pipeline_html(PIPELINE_STEPS, active_index=min(idx + 1, len(PIPELINE_STEPS) - 1)),
                unsafe_allow_html=True,
            )
            done_labels.append(f"✓ {label}")
            log.markdown("\n\n".join(done_labels))

        pipeline_slot.markdown(pipeline_html(PIPELINE_STEPS, complete=True), unsafe_allow_html=True)
        status.update(label="Review complete — a human must now decide.",
                      state="complete", expanded=False)

    if result is None:
        st.error("The review did not complete. Treat this as a FAILED review, not a clean permit.")
        st.stop()

    verdict = result.get("verdict", {}) or {}
    prov = result.get("provenance", {}) or {}

    render_section("3 \u00b7 Recommendation", "Advisory only \u2014 HOLDPOINT authorises nothing")
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

    fig_prov = provenance_donut(prov)
    if fig_prov is not None:
        pc1, pc2 = st.columns([1, 2])
        with pc1:
            st.plotly_chart(fig_prov, use_container_width=True)
        with pc2:
            st.markdown("##### Why this donut matters")
            st.markdown(
                "Every control the agents claim is *mandated* must quote a real procedure "
                "**verbatim** — and HOLDPOINT then checks, in code, that the quoted sentence "
                "actually exists in the document.\n\n"
                "The amber slice is the part of this review that **could not be traced**. It is "
                "not hidden and it is not silently dropped. It is shown, downgraded, and handed "
                "to a human.\n\n"
                "An AI that invents a safety control has manufactured false assurance inside the "
                "one system built to prevent it. So we do not ask the model to be honest — "
                "**we check.**"
            )

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

        # The product's central claim, MEASURED rather than asserted. Not "both involve H2S" —
        # that is subject matter. This is failure SHAPE.
        st.plotly_chart(structural_similarity(permit), use_container_width=True)
        st.caption(
            "Matched on **structural failure shape**, not subject matter. \"Both involve H2S\" is a "
            "weak match that retrieves the wrong lesson. \"Both are one broad permit covering "
            "multiple jobs, with the stop-work instruction present in prose but never enforced\" is "
            "the match that stops a shift."
        )
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

