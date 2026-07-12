"""Page 3 — The major-accident corpus. Thirty years of investigations, turned into a live control."""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Incident Precedent | HOLDPOINT", page_icon="📕", layout="wide")

from core.styles import (inject_styles, render_page_header, render_section,
                         render_kpi_row, render_empty_state)
from core.ui import bootstrap, require_llm, render_quote, render_data_provenance
from data.incidents import incident_corpus, verified_incidents, PATTERN_LABELS

inject_styles()
site = bootstrap()

render_page_header(
    title="Incident Precedent",
    description="Major-accident investigations, retrievable at the permit gate. Not 'you may have missed a hazard' — 'this permit has the shape of one that killed people.'",
    ai_type="genai",
)

corpus = incident_corpus()
verified = verified_incidents()
deaths = sum(i["fatalities"] for i in verified)

render_kpi_row([
    {"value": str(len(corpus)), "label": "Incidents in Corpus"},
    {"value": str(len(verified)), "label": "Verified Investigations",
     "sublabel": "CSB · Cullen Inquiry · ICMM"},
    {"value": f"{deaths:,}", "label": "Deaths Represented",
     "sublabel": "in the verified set alone"},
    {"value": str(len(corpus) - len(verified)), "label": "Illustrative Patterns",
     "sublabel": "labelled, never passed off as real"},
])

st.warning("""
**On honesty in a safety corpus.** Entries marked **VERIFIED** come from the public investigation
named — the CSB, the Cullen Inquiry, ICMM — and quote the investigators' own words. Entries marked
**ILLUSTRATIVE** are realistic patterns written to exercise the matcher, and are **not real
accidents**.

We do not blur that line anywhere in this product. A safety tool that cites a fabricated fatality to
make its point has forfeited the right to be believed about anything else it says.
""")

# --- The corpus --------------------------------------------------------------------------
render_section("The corpus")

for inc in corpus:
    is_verified = inc["verification"] == "verified"
    badge = "🔴 VERIFIED" if is_verified else "🟡 ILLUSTRATIVE"

    with st.expander(
        f"{badge} · {inc['title']} — {inc['fatalities']} killed" if inc["fatalities"]
        else f"{badge} · {inc['title']}",
        expanded=(inc["incident_id"] == "CSB-2024-DEERPARK"),
    ):
        st.markdown(f"**{inc['date']}** · {inc['industry']}")

        if is_verified:
            st.caption(f"Source: {inc['source']}")
            if inc.get("source_url"):
                st.caption(inc["source_url"])
        else:
            st.warning(f"**NOT A REAL INCIDENT.** {inc['source']}")

        st.markdown(inc["summary"])

        st.markdown("**What the investigators found**")
        for f in inc["investigator_findings"]:
            render_quote(f.strip('"'), inc["source"] if is_verified else "illustrative")

        st.info(f"**Stated honestly:** {inc['root_cause_note']}")

        st.markdown("**Structural pattern**")
        cols = st.columns(2)
        for i, p in enumerate(inc["structural_pattern"]):
            with cols[i % 2]:
                st.markdown(f"- `{p}` — {PATTERN_LABELS.get(p, p)}")

        st.success(f"**The lesson:** {inc['lesson']}")

# --- Why this matters --------------------------------------------------------------------
render_section("Why a corpus beats a checklist")

c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    <div class="module-card">
        <div class="module-title" style="font-size:1.05rem;">A checklist asks a question</div>
        <div class="module-desc">
        "Have you identified all hazards?" — and the honest answer from a supervisor at the end of a
        twelve-hour shift is always <em>yes</em>, because they believe they have.
        <br><br>
        A checklist cannot tell you that the way you have <em>structured</em> this permit is the way a
        permit was structured on a day when people died.
        </div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="module-card genai">
        <div class="module-title" style="font-size:1.05rem;">A corpus makes a statement</div>
        <div class="module-desc">
        <em>"This permit shares four structural features with the permit at Deer Park: an over-broad
        scope covering multiple jobs of differing hazard, a stop-work instruction present in prose but
        not enforced as a hold point, two contracting companies on one work party, and live toxic
        inventory adjacent to the work."</em>
        <br><br>
        That is a sentence that stops a shift.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.page_link("pages/1_Permit_Review.py",
             label="See the matcher run against a live permit →", icon="🔍")

render_data_provenance()
