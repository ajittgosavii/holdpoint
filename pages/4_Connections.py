"""Page 4 — System-of-record connections. HOLDPOINT stands in FRONT of your permit system."""

import os
import sys
import json

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Connections | HOLDPOINT", page_icon="🔌", layout="wide")

from core.styles import (inject_styles, render_page_header, render_section,
                         render_kpi_row, render_pipeline)
from core.ui import bootstrap
from core.connectors import (CONNECTORS, get_connector, roundtrip_check,
                             CANONICAL_FIELDS, DEFAULT_CONNECTOR)
from data.permits import PERMITS

inject_styles()
site = bootstrap()

render_page_header(
    title="System-of-Record Connections",
    description="HOLDPOINT does not replace your permit system. It stands in front of it.",
    ai_type="agentic",
)

st.error("""
**These connectors are SIMULATED.** No network call is made. The vendor payload shapes are
*representative* — written to be realistic in structure and naming so the normalisation problem can
be shown honestly — but they are **not documented API schemas**, and the real field mapping for any
client is discovery work.

Pretending otherwise would be exactly the overclaim this product exists to prevent.
""")

# --- The posture -------------------------------------------------------------------------
render_section("Why layering beats replacing")

c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    <div class="module-card" style="border-left:4px solid #dc2626;">
        <div class="module-title" style="font-size:1.05rem;">The fight we do NOT pick</div>
        <div class="module-desc">
        Building a rival EHS suite means asking a refinery to rip out the system holding its permits,
        its e-signatures, its audit trail and its regulator-facing evidence.
        <br><br>
        That is a multi-year, politically brutal, rip-and-replace sale. <strong>Challengers do not win
        those.</strong> And an SI that already implements Enablon would be putting existing services
        revenue in the crossfire to chase product revenue it isn't built to capture.
        </div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-title" style="font-size:1.05rem;">The fight we win</div>
        <div class="module-desc">
        Read the permit <strong>out</strong> of whatever they already run. Attack it. Write the
        findings and hold points <strong>back in</strong>.
        <br><br>
        No rip-and-replace. Weeks to value. The incumbent becomes a <strong>substrate, not an
        enemy</strong> — and HOLDPOINT works <em>better</em> where Enablon exists, because a
        structured digital permit is easier to reason over than a paper one.
        </div>
    </div>
    """, unsafe_allow_html=True)

render_pipeline([
    "Source system", "Fetch native payload", "Normalise to canonical",
    "7 agents attack", "Write findings back", "Human authorises",
])

# --- Pick a source system ----------------------------------------------------------------
render_section("Connect a system of record")

keys = list(CONNECTORS)
sel = st.selectbox(
    "System of record",
    keys,
    index=keys.index(st.session_state.get("connector", DEFAULT_CONNECTOR))
    if st.session_state.get("connector", DEFAULT_CONNECTOR) in keys else 0,
    format_func=lambda k: CONNECTORS[k].product,
    key="connector",
)
conn = get_connector(sel)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"**Vendor**  \n{conn.vendor}")
    st.markdown(f"**API style**  \n`{conn.api_style}`")
with m2:
    st.markdown(f"**Auth**  \n`{conn.auth}`")
    st.markdown(f"**Endpoint**  \n`{conn.endpoint}`")
with m3:
    st.markdown("**Connection**  \n🟢 Connected *(simulated)*")
    st.markdown(f"**Permits available**  \n{len(PERMITS)}")

st.info(f"**Market note.** {conn.market_note}")

# --- The normalisation problem — the actual integration work -----------------------------
render_section("The real integration work is normalisation",
               "Every system names the same thing differently. The agents must never see any of it.")

st.markdown("""
This is the part people underestimate. The API call is trivial. The work is that a permit's work
description is `workOrderDescription` in one system, `LTXT` in another, and
`description_longdescription` in a third — and the agents must be shown **one canonical shape** or
they will reason about the wrong field.

**Add a new system of record → write one adapter. The agents do not change.**
""")

fm = conn.field_map
rows = "".join(
    f"<tr><td><code>{k}</code></td><td>→</td><td><code>{v}</code></td></tr>"
    for k, v in fm.items()
)
st.markdown(
    f'<table class="data-table"><tr><th>HOLDPOINT canonical</th><th></th>'
    f'<th>{conn.product}</th></tr>{rows}</table>',
    unsafe_allow_html=True,
)

# --- Round-trip proof --------------------------------------------------------------------
render_section("Lossless mapping check",
               "A dropped field is a defect that LOOKS like a clean review")

st.markdown("""
A silently lossy field map in a safety system means the agents review a permit that is missing a
hazard, a person, or a concurrent permit — **and confidently declare it safe.** So the mapping is
round-trip tested, not assumed: canonical → vendor-native → canonical must return exactly what went
in.
""")

permit_ids = [p["permit_id"] for p in PERMITS]
pid = st.selectbox("Permit to trace", permit_ids, index=0)

rt = roundtrip_check(conn, pid)

render_kpi_row([
    {"value": str(rt["fields_checked"]), "label": "Canonical Fields"},
    {"value": str(len(rt["fields_lost"])), "label": "Fields Lost",
     "sublabel": "must be zero"},
    {"value": str(len(rt["fields_changed"])), "label": "Fields Corrupted",
     "sublabel": "must be zero"},
    {"value": "PASS" if rt["ok"] else "FAIL", "label": "Round-Trip"},
])

if rt["ok"]:
    st.success(
        f"**Lossless.** All {rt['fields_checked']} canonical fields survive the round trip through "
        f"{conn.product}. The agents will see the permit exactly as the source system holds it."
    )
else:
    st.error(
        f"**LOSSY MAPPING — do not run agents against this connector.** "
        f"Lost: {rt['fields_lost'] or 'none'}. Corrupted: {rt['fields_changed'] or 'none'}. "
        f"The agents would review an incomplete permit and could declare it safe."
    )

tab_native, tab_canon = st.tabs([f"1 · Native payload from {conn.vendor}", "2 · Normalised canonical"])
with tab_native:
    st.caption(f"What `GET {conn.endpoint}/permits/{pid}` returns — in the source system's own shape.")
    st.json(rt["native_payload"])
with tab_canon:
    st.caption("What HOLDPOINT's agents actually see. One shape, whatever the source.")
    st.json(rt["canonical_payload"])

# --- Write-back --------------------------------------------------------------------------
render_section("Write-back", "The privileged operation — and the hardest thing to get signed off")

st.markdown("""
Findings and enforced hold points are posted **back onto the permit in the source system**, and the
permit is held pending closeout. This is what makes HOLDPOINT a gate rather than a report nobody
reads.

It is also, in production, **the hardest thing to get approved** — a system that can annotate or
block a live safety-critical record is a privileged integration, and it will be scrutinised
accordingly. That is the right instinct, and we should not pretend it is a config toggle.
""")

sample_findings = [
    {"_group": "buried_hold_points", "severity": "critical",
     "required_hold_point": "HP1: STOP. Operations representative to attend the flange and sign "
                            "before containment is broken.",
     "citation_document": "Energy Isolation and Lock-Out / Tag-Out Standard",
     "citation_verified": True},
    {"_group": "competency", "severity": "critical",
     "issue": "J. Ruiz (Repcon) — H2S competency EXPIRED 2024-11-02",
     "citation_document": "Contractor Competency and Induction Standard",
     "citation_verified": True},
    {"_group": "scope", "severity": "critical",
     "issue": "Permit bundles 5 tasks of differing hazard — must be split",
     "citation_document": "Permit to Work Standard",
     "citation_verified": True},
]

wb = conn.write_back(pid, sample_findings, "REJECT")

wc1, wc2 = st.columns(2)
with wc1:
    st.markdown(f"**Request** — `POST {wb['request']['url']}`")
    st.caption(f"Auth: `{wb['request']['auth']}`")
    st.json(wb["request"]["body"])
with wc2:
    st.markdown(f"**Response** — `{wb['response']['status']} Created`")
    st.json(wb["response"]["body"])

st.warning(
    "**Note what did NOT happen.** HOLDPOINT set the permit to HELD. It did **not** authorise "
    "anything, and it did not close the findings. A qualified human authoriser still decides — the "
    "write-back only ensures they cannot decide *without seeing this*."
)

# --- What a real integration needs -------------------------------------------------------
render_section("What a real integration actually needs", "Stated plainly, because the demo makes it look easy")

st.markdown("""
| Requirement | Why it is not trivial |
|---|---|
| **Authentication** | OAuth2 / SAML / principal propagation, per vendor, per tenant |
| **The real API surface** | Versioned, with field *semantics* — not just names — validated against the client's config |
| **Field mapping signed off by a control-of-work SME** | The mapping is a safety artefact. A wrong mapping is a wrong review |
| **Rate limits, pagination, retry, idempotency** | A turnaround generates hundreds of permits a day |
| **Write-back permissions** | The hardest approval in the programme. A system that can block a live permit is privileged |
| **Custom fields** | Every operator has extended their WCM/Maximo schema. There is no generic adapter |

**Honest estimate:** the first connector is weeks, not days. The *second* one for the same vendor at
a different client is also not free, because operators customise their schemas. This is the largest
single work item in Phase 1 — and it is why the SI pull-through is bigger than the AI build.
""")
