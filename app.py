"""
HOLDPOINT — the adversary at the permit gate.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="HOLDPOINT", page_icon="🛑", layout="wide",
                   initial_sidebar_state="expanded")

from core.styles import inject_styles, render_hero, render_kpi_row, render_section
from core.ui import bootstrap, render_data_provenance
from data.permits import PERMITS
from data.incidents import verified_incidents, incident_corpus
from core.backlog import scan_backlog

inject_styles()
site = bootstrap()

scan = scan_backlog(PERMITS)
fatalities = sum(i["fatalities"] for i in verified_incidents())

render_hero(
    title="HOLDPOINT",
    subtitle="The adversary at the permit gate. It reads the permit nobody re-read, and refuses to let it through.",
    tech_text="7-Agent LangGraph Review  ·  Provenance-Verified Citations  ·  Human Authorises",
)

render_kpi_row([
    {"value": "7", "label": "Adversarial Agents", "sublabel": "Supervisor + 5 specialists + precedent"},
    {"value": str(scan["deer_park_count"]), "label": "Deer Park–Shaped Permits",
     "sublabel": f"of {scan['total']} in this backlog"},
    {"value": str(len(incident_corpus())), "label": "Major-Accident Corpus",
     "sublabel": f"{len(verified_incidents())} verified investigations"},
    {"value": f"{fatalities:,}", "label": "Deaths in the Corpus",
     "sublabel": "Deer Park · Piper Alpha · Texas City · ICMM"},
    {"value": "0", "label": "Permits It Authorises", "sublabel": "A human always decides"},
])

# ---------------------------------------------------------------------------------------
render_section("The sentence this product exists for")

st.markdown("""
<div class="module-card" style="border-left: 5px solid #dc2626;">
    <div style="font-size:1.05rem;line-height:1.7;color:#1e293b;">
    On 10 October 2024, contract workers opened a hydrogen sulphide line at the PEMEX Deer Park
    refinery. Over 27,000 lb of H₂S was released. <strong>Two contract workers were killed.</strong>
    Two cities sheltered in place.
    <br><br>
    The US Chemical Safety Board published its final report on 23 February 2026. Two findings:
    <br><br>
    <div class="source-quote" style="font-size:1.0rem;">
    "The refinery issued a broad work permit covering multiple jobs with varying hazards and
    without clear hold points."
    </div>
    <div class="source-quote" style="font-size:1.0rem;">
    "Workers overlooked a written instruction to stop work and obtain an operator's presence before
    opening the hydrogen sulfide piping."
    </div>
    <br>
    Read that second sentence again. <strong>The instruction was already there.</strong> It was
    written on the permit. It was buried in a narrative field, inside a scope that covered five
    different jobs, and it was read past.
    <br><br>
    A tool that <em>recommends hazards</em> would have recommended a hazard that was already listed.
    What was missing was <strong>an adversary whose only job was to attack the finished permit and
    refuse to let it through.</strong>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
c1, c2 = st.columns([1, 1])
with c1:
    st.page_link("pages/1_Permit_Review.py",
                 label="Review PTW-2026-0417 — the Deer Park pattern →", icon="🔍")
with c2:
    st.page_link("pages/2_Backlog_Scan.py",
                 label="Scan the permit backlog — the metric that decides →", icon="📊")

# ---------------------------------------------------------------------------------------
render_section("What HOLDPOINT does", "Seven agents, all adversaries")

st.markdown("""
HOLDPOINT sits **in front of the authorisation gate**. A permit pack goes in — the permit, the
isolation plan, the JSA, the assigned people and their competencies, and the live state of the
unit including every other permit already active on it. A supervisor plans the attack, five
specialists execute it, and a recommendation comes out. **A human then decides.**
""")

a, b = st.columns(2)
with a:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-number">The specialists</div>
        <div class="module-desc" style="line-height:1.75;">
        <strong>Scope Decomposer</strong> — is this one job, or five wearing a trench coat?<br>
        <strong>Hazard Coverage Challenger</strong> — is that control real, or is it the word
        "carefully"?<br>
        <strong>Hold Point Enforcer</strong> — what safeguard is buried in the prose where nobody
        will see it?<br>
        <strong>Competency Matcher</strong> — is <em>this person</em> qualified for <em>this
        hazard</em>? Induction is not competence.<br>
        <strong>Isolation &amp; SIMOPS Verifier</strong> — what else is live on this unit right now?
        </div>
    </div>
    """, unsafe_allow_html=True)
with b:
    st.markdown("""
    <div class="module-card genai">
        <div class="module-number">The two that make it trustworthy</div>
        <div class="module-desc" style="line-height:1.75;">
        <strong>Incident Precedent Analyst</strong> — RAG over the CSB, the Cullen Inquiry and ICMM.
        Not "you may have missed a hazard", but <em>"this permit has the structural shape of the
        permit that killed two people at Deer Park."</em><br><br>
        <strong>Provenance Verifier</strong> — every control the agents claim is mandated must quote
        a real procedure, and the system <em>programmatically checks the quote exists</em>. It is
        code, not a prompt. The model cannot talk its way past it.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.info(
    "**Why the provenance check is the whole ballgame.** An AI that invents a safety control has "
    "manufactured false assurance inside the one system built to prevent false assurance. That is "
    "worse than no AI at all. So HOLDPOINT does not ask the model to be honest — it checks. "
    "Anything it cannot trace to a real procedure is shown to the authoriser as **UNVERIFIED**, "
    "never as fact."
)

# ---------------------------------------------------------------------------------------
render_section("Why this is a business case, not a safety poster")

v1, v2, v3 = st.columns(3)
with v1:
    st.markdown("""
    <div class="module-card">
        <div class="module-title" style="font-size:1.05rem;">The permit desk is two bottlenecks</div>
        <div class="module-desc">
        In a turnaround, the permit desk issues <em>hundreds of permits a day</em>. It is
        simultaneously the <strong>safety chokepoint</strong> and the <strong>schedule
        chokepoint</strong> — and they are the same queue.<br><br>
        Crews stand idle waiting for authorisation, while authorisers under queue pressure are
        exactly the humans who read past a buried stop-work line.
        </div>
    </div>
    """, unsafe_allow_html=True)
with v2:
    st.markdown("""
    <div class="module-card">
        <div class="module-title" style="font-size:1.05rem;">It has a hard gate</div>
        <div class="module-desc">
        Deloitte (Jan 2026): only <strong>25%</strong> of enterprises move even 40% of AI pilots into
        production. Optional copilots die in the pilot graveyard.<br><br>
        <strong>A permit cannot be issued without passing through the gate.</strong> That is a line
        item, not an experiment.
        </div>
    </div>
    """, unsafe_allow_html=True)
with v3:
    st.markdown("""
    <div class="module-card">
        <div class="module-title" style="font-size:1.05rem;">The test can fail</div>
        <div class="module-desc">
        Run HOLDPOINT over a year of the client's <em>historical, already-authorised</em> permits and
        count the Deer-Park-shaped defects.<br><br>
        <strong>If the number is zero, the product has no case and we say so.</strong> A test that
        cannot fail proves nothing.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------
render_section("What HOLDPOINT will not do", "Stated before anyone has to ask")

st.error("""
**It would not have prevented the Deer Park root cause.** The CSB's root cause was failure to
positively identify the correct equipment — the workers opened a near-identical flange about five
feet from the intended one. The permit deficiencies were **contributing factors**. HOLDPOINT
addresses the structure that let the root cause become fatal. It does not address the root cause.

**It is a minority of the harm.** ICMM's single largest killer in mining is mobile-equipment
interaction, whose remedies are proximity detection and LiDAR. The slice of field safety that lives
inside documents is real — and it is a minority. Own that boundary and everything else gets more
believable, not less.

**Utilities is a hypothesis, not a finding.** The refining and mining packs rest on verified
evidence (CSB, ICMM). The utilities pack rests on a plausible argument — OSHA controlling-employer
liability, NFPA 70E, contractor-heavy line work — that **has not been verified**. The app labels it
as such rather than quietly presenting it as proven.
""")

render_data_provenance()
