"""Page 2 — Backlog scan. The metric that decides whether this product has a business case."""

import os
import sys

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Backlog Scan | HOLDPOINT", page_icon="📊", layout="wide")

from core.styles import (inject_styles, render_page_header, render_section,
                         render_kpi_row, severity_badge)
from core.ui import bootstrap, render_data_provenance
from core.backlog import scan_backlog, DEFECTS
from data.permits import PERMITS

inject_styles()
site = bootstrap()

render_page_header(
    title="Backlog Scan",
    description="Run HOLDPOINT over permits that were already authorised, worked and closed. Count the ones that were lucky.",
    ai_type="agentic",
)

st.markdown("""
This is the number that decides whether HOLDPOINT is worth buying, and it is designed so that it
**can come back zero**.

Take a year of the client's *historical* permits — permits that were authorised, worked, and closed
without incident. Scan them for the Deer Park structural signature: an over-broad scope carrying a
safeguard that nothing enforces.

**Every permit it finds is an incident that did not happen by luck.** If it finds none, the product
has no case here and we will say so and walk away. A test that cannot fail proves nothing.
""")

scan = scan_backlog(PERMITS)

# --- Headline ----------------------------------------------------------------------------
if scan["deer_park_count"]:
    st.error(f"### {scan['headline']}")
else:
    st.success(f"### {scan['headline']}")

render_kpi_row([
    {"value": str(scan["total"]), "label": "Permits Scanned"},
    {"value": str(scan["deer_park_count"]), "label": "Deer Park Signature",
     "sublabel": f"{scan['deer_park_pct']}% of the backlog"},
    {"value": str(scan["critical_count"]), "label": "Critical Severity"},
    {"value": str(scan["clean_count"]), "label": "Clean",
     "sublabel": "no structural defect found"},
])

st.caption(
    "This scan is a **deterministic, rules-based pre-screen** — a cheap sweep over thousands of "
    "permits, not the seven-agent review. It is stated as a heuristic rather than dressed up as an "
    "AI review, because a heuristic that claims to be a reasoning engine is just a lie with a "
    "progress bar. The agents do the deep work on Permit Review."
)

# --- Defect distribution -----------------------------------------------------------------
if scan["by_defect"]:
    render_section("Where the defects are")

    df = pd.DataFrame(
        [{"Defect": DEFECTS.get(k, k), "Permits": v} for k, v in scan["by_defect"].items()]
    ).sort_values("Permits", ascending=True)

    fig = px.bar(
        df, x="Permits", y="Defect", orientation="h",
        color="Permits", color_continuous_scale=["#fcd34d", "#f97316", "#dc2626"],
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
        yaxis_title="", xaxis_title="Permits affected",
        coloraxis_showscale=False, height=340,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Per-permit detail -------------------------------------------------------------------
render_section("Permit by permit")

for r in scan["results"]:
    if r["deer_park_shape"]:
        icon, tag = "🛑", " — **DEER PARK SIGNATURE**"
    elif r["clean"]:
        icon, tag = "✅", " — clean"
    else:
        icon, tag = "⚠️", ""

    with st.expander(f"{icon} {r['permit_id']} — {r['title']}{tag}",
                     expanded=r["deer_park_shape"]):
        if r["clean"]:
            st.success("No structural defect found by the pre-screen.")
        for d in r["defects"]:
            st.markdown(
                f"{severity_badge(d['severity'])} &nbsp; **{DEFECTS.get(d['code'], d['code'])}**",
                unsafe_allow_html=True,
            )
            st.markdown(d["detail"])
            for ev in d.get("evidence", []) or []:
                st.markdown(
                    f'<div class="source-quote">"{ev}"<br>'
                    f'<span style="font-style:normal;font-size:0.75rem;color:#64748b;">'
                    f'— buried in the permit text, enforced by nothing</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")

        if r["deer_park_shape"]:
            st.error(
                "**This is the shape the CSB described.** An over-broad scope, and a safeguard "
                "that exists only as a sentence. At Deer Park that combination killed two contract "
                "workers who were doing what the permit allowed."
            )
            st.page_link("pages/1_Permit_Review.py",
                         label=f"Run the full seven-agent review on {r['permit_id']} →", icon="🔍")

# --- The honest framing ------------------------------------------------------------------
render_section("How to read this number")

st.info("""
**What it is.** A count of permits whose *structure* would not have stopped a Deer Park. It is a
measure of latent exposure, not of incidents.

**What it is not.** It is not a prediction that any of these permits would have hurt someone. Most
permits with a structural defect are worked safely, because people are careful and because most days
nothing goes wrong. That is precisely the problem: the defect is invisible until the day it isn't.

**The honest pitch to a client is a question, not a claim:** *how many of these would you like to
have known about?*
""")

render_data_provenance()
