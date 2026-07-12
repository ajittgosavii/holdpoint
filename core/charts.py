"""
HOLDPOINT — Visuals
===================

Every chart here renders a COMPUTED FACT. None of them is decoration.

That distinction matters in a safety tool. A chart that looks impressive but encodes nothing is a
form of false assurance: it makes a reviewer feel informed without informing them. So each function
below exists because a specific finding is hard to grasp as a sentence and obvious as a picture:

  1. shift_vs_darkness   — "9.6 of 12 hours fall after sunset" is a number. Seeing the shift bar
                           sitting inside the night band is a fact you cannot argue with.
  2. simops_timeline     — a SIMOPS conflict is a statement about TIME. Hot work and a toxic line
                           break "both being live" is exactly what a timeline is for.
  3. structural_similarity — "this permit has the shape of Deer Park" is the product's central
                           claim. This measures it: what fraction of each historical accident's
                           structural pattern is present in this permit.
  4. defect_matrix       — the backlog metric, permit by defect.
  5. provenance_donut    — how much of the review is traceable to a real procedure.
"""

import plotly.graph_objects as go
import plotly.express as px

from core.backlog import scan_permit, DEFECTS
from data.incidents import incident_corpus, PATTERN_LABELS

FONT = dict(family="Inter, system-ui, sans-serif")
CRIT, HIGH, MED, OK, GREY = "#dc2626", "#f97316", "#eab308", "#16a34a", "#cbd5e1"

_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white", font=FONT,
    margin=dict(l=10, r=10, t=40, b=10),
)


# ==================================================================================================
# 1. The permit's shift, drawn against real darkness
# ==================================================================================================

def shift_vs_darkness(rc: dict):
    """Plot the permit's work window against the real sunset/sunrise at the site.

    This is the reality check made visible. The bar is the work the permit authorises; the dark band
    is when the sun is actually down at those coordinates on that date. Overlap = the clause breach.
    """
    dk = rc.get("darkness")
    ww = rc.get("work_window") or {}
    if not dk:
        return None

    def _h(hhmm: str) -> float:
        h, m = (int(x) for x in hhmm.split(":"))
        return h + m / 60.0

    start = _h(ww["start"])
    end = _h(ww["end"])
    if end <= start:
        end += 24  # crosses midnight

    sunset = _h(dk["sunset_local"])
    sunrise = _h(dk["sunrise_local"].split(" ")[0]) + 24  # next morning

    fig = go.Figure()

    # Daylight and darkness bands across the whole span shown.
    x0, x1 = min(start, 0), max(end, sunrise)
    fig.add_shape(type="rect", x0=x0, x1=sunset, y0=-0.5, y1=0.5,
                  fillcolor="#fef9c3", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=sunset, x1=sunrise, y0=-0.5, y1=0.5,
                  fillcolor="#1e293b", opacity=0.85, line_width=0, layer="below")
    fig.add_shape(type="rect", x0=sunrise, x1=x1, y0=-0.5, y1=0.5,
                  fillcolor="#fef9c3", line_width=0, layer="below")

    dark = dk["any_darkness"]
    fig.add_trace(go.Bar(
        x=[end - start], y=["Permit shift"], base=[start], orientation="h",
        marker=dict(color=CRIT if dark else OK, line=dict(color="white", width=2)),
        width=0.34,
        hovertemplate=(f"Shift {ww['start']}–{ww['end']}<br>"
                       f"{dk['dark_hours']}h of {dk['shift_hours']}h in darkness"
                       "<extra></extra>"),
        name="Work authorised",
    ))

    fig.add_vline(x=sunset, line=dict(color="#f59e0b", width=2, dash="dot"),
                  annotation_text=f"sunset {dk['sunset_local']}", annotation_position="top")
    fig.add_vline(x=sunrise, line=dict(color="#f59e0b", width=2, dash="dot"),
                  annotation_text=f"sunrise {dk['sunrise_local'].split(' ')[0]}",
                  annotation_position="top")

    ticks = list(range(int(x0), int(x1) + 1, 2))
    fig.update_layout(
        **_LAYOUT,
        height=200, showlegend=False, bargap=0.6,
        title=dict(
            text=(f"<b>{dk['dark_hours']}h of {dk['shift_hours']}h ({dk['dark_pct']}%) of this "
                  f"permit's work falls after sunset</b>" if dark else
                  "<b>This permit's work window falls entirely in daylight</b>"),
            font=dict(size=13, color=CRIT if dark else "#166534"),
        ),
        xaxis=dict(tickmode="array", tickvals=ticks,
                   ticktext=[f"{t % 24:02d}:00" for t in ticks],
                   showgrid=False, title="local time"),
        yaxis=dict(showgrid=False),
    )
    return fig


# ==================================================================================================
# 2. Simultaneous operations — a conflict is a statement about TIME
# ==================================================================================================

CONFLICT_TERMS = ("hot work", "weld", "grind", "line break", "containment", "drain", "open")


def simops_timeline(permit: dict):
    """Every permit live on this unit, on one timeline. Overlap is the whole point."""
    concurrent = permit.get("concurrent_permits") or []
    if not concurrent:
        return None

    rows = [{
        "id": permit["permit_id"],
        "label": f"{permit['permit_id']} (this permit)",
        "desc": permit["title"],
        "status": permit.get("status", ""),
        "this": True,
    }]
    for c in concurrent:
        rows.append({
            "id": c["permit_id"],
            "label": c["permit_id"],
            "desc": c["description"],
            "status": c["status"],
            "this": False,
        })

    this_blob = (permit.get("work_description", "") + " " + permit.get("title", "")).lower()

    fig = go.Figure()
    for i, r in enumerate(reversed(rows)):
        other_blob = r["desc"].lower()
        hot = any(t in other_blob for t in ("hot work", "weld", "grind")) or \
              any(t in this_blob for t in ("hot work", "weld", "grind"))
        breach = any(t in other_blob for t in ("line break", "containment", "drain", "open")) or \
                 any(t in this_blob for t in ("line break", "containment", "drain", "open"))
        conflict = (not r["this"]) and hot and breach

        color = CRIT if conflict else ("#1e40af" if r["this"] else GREY)
        fig.add_trace(go.Bar(
            x=[12], base=[6], y=[r["label"]], orientation="h",
            marker=dict(color=color, line=dict(color="white", width=2)),
            width=0.55,
            hovertemplate=f"<b>{r['id']}</b><br>{r['desc']}<br>status: {r['status']}"
                          + ("<br><b>CONFLICTS WITH THIS PERMIT</b>" if conflict else "")
                          + "<extra></extra>",
            name="",
        ))

    n_conflict = sum(
        1 for r in rows[1:]
        if (any(t in r["desc"].lower() for t in ("hot work", "weld", "grind"))
            or any(t in this_blob for t in ("hot work", "weld", "grind")))
        and (any(t in r["desc"].lower() for t in ("line break", "containment", "drain", "open"))
             or any(t in this_blob for t in ("line break", "containment", "drain", "open")))
    )

    fig.update_layout(
        **_LAYOUT,
        height=90 + 46 * len(rows), showlegend=False, bargap=0.35,
        title=dict(
            text=(f"<b>{n_conflict} concurrent permit(s) conflict with this work on "
                  f"{permit['unit']}</b>" if n_conflict else
                  f"<b>{len(concurrent)} other permit(s) live on this unit — no conflict detected</b>"),
            font=dict(size=13, color=CRIT if n_conflict else "#166534"),
        ),
        xaxis=dict(range=[5, 19], tickmode="array", tickvals=[6, 9, 12, 15, 18],
                   ticktext=["06:00", "09:00", "12:00", "15:00", "18:00"],
                   showgrid=True, gridcolor="#f1f5f9", title="all live at the same time"),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return fig


# ==================================================================================================
# 3. "This permit has the shape of Deer Park" — measured, not asserted
# ==================================================================================================

# Map the scanner's defect codes onto the structural patterns the investigations describe.
DEFECT_TO_PATTERN = {
    "over_broad_scope": ["over_broad_scope"],
    "buried_stop_work": ["buried_stop_work", "no_hold_points"],
    "no_hold_points": ["no_hold_points"],
    "multi_company_party": ["contractor_multi_company", "contractor_executed"],
    "simops_conflict": ["simops_conflict", "concurrent_permits_same_equipment"],
    "weak_isolation": ["loto_weakness", "incomplete_energy_identification"],
    "competency_gap": ["contractor_executed", "ptw_weakness"],
}


def permit_patterns(permit: dict) -> set[str]:
    """The structural failure patterns present in THIS permit, derived from the scanner."""
    pats: set[str] = set()
    scan = scan_permit(permit)
    for d in scan["defects"]:
        pats.update(DEFECT_TO_PATTERN.get(d["code"], []))
    # A partially operational unit with live hazardous inventory is itself a Deer Park feature.
    if "partially operational" in (permit.get("unit_state", "") or "").lower():
        pats.add("partially_operational_unit")
    if any(k in (permit.get("work_description", "") or "").lower()
           for k in ("turnaround", "non-routine", "shutdown", "clear blockage")):
        pats.add("non_routine_task")
    return pats


def structural_similarity(permit: dict):
    """For each historical accident: what fraction of ITS structural pattern is in THIS permit?

    This is the product's central claim, quantified. Not "both involve H2S" — that is subject
    matter. This is failure SHAPE.
    """
    have = permit_patterns(permit)
    rows = []
    for inc in incident_corpus():
        pat = set(inc["structural_pattern"])
        shared = have & pat
        rows.append({
            "incident": inc["title"][:46] + ("…" if len(inc["title"]) > 46 else ""),
            "pct": round(100 * len(shared) / len(pat)) if pat else 0,
            "n_shared": len(shared),
            "shared": ", ".join(sorted(PATTERN_LABELS.get(p, p) for p in shared)) or "none",
            "verified": inc["verification"] == "verified",
            "fatalities": inc["fatalities"],
        })

    # Break ties on DEPTH of match, not just percentage. Two accidents can both be 100% matched,
    # but one of them shares five structural features and the other three — and the five-feature
    # match is the more serious statement. Without this, an accident with a thin pattern can
    # outrank Deer Park purely because it had fewer boxes to tick.
    rows.sort(key=lambda r: (r["pct"], r["n_shared"]))

    fig = go.Figure(go.Bar(
        x=[r["pct"] for r in rows],
        y=[r["incident"] for r in rows],
        orientation="h",
        marker=dict(
            color=[CRIT if r["pct"] >= 60 else HIGH if r["pct"] >= 40 else MED if r["pct"] > 0
                   else GREY for r in rows],
            line=dict(color="white", width=1),
        ),
        text=[f"{r['pct']}%  ({r['n_shared']} shared)" for r in rows],
        textposition="outside",
        customdata=[[r["shared"], r["fatalities"],
                     "VERIFIED investigation" if r["verified"] else "ILLUSTRATIVE — not a real accident"]
                    for r in rows],
        hovertemplate=("<b>%{y}</b><br>%{customdata[2]}<br>Fatalities: %{customdata[1]}"
                       "<br>Shared structure: %{customdata[0]}<extra></extra>"),
    ))
    fig.update_layout(
        **_LAYOUT,
        height=110 + 44 * len(rows), showlegend=False,
        title=dict(text="<b>How much of each accident's structural pattern is present in this permit?</b>",
                   font=dict(size=13, color="#0f172a")),
        xaxis=dict(range=[0, 118], ticksuffix="%", showgrid=True, gridcolor="#f1f5f9",
                   title="share of that accident's failure shape present here"),
        yaxis=dict(showgrid=False),
    )
    return fig


# ==================================================================================================
# 4. Backlog defect matrix
# ==================================================================================================

def defect_matrix(scan: dict):
    """Permits x defect types. The backlog metric, at a glance."""
    codes = list(DEFECTS)
    permits = [r["permit_id"] for r in scan["results"]]

    sev_rank = {"critical": 3, "high": 2, "medium": 1, "low": 1}
    z, text = [], []
    for r in scan["results"]:
        by_code = {d["code"]: d["severity"] for d in r["defects"]}
        z.append([sev_rank.get(by_code.get(c), 0) for c in codes])
        text.append([by_code.get(c, "") for c in codes])

    fig = go.Figure(go.Heatmap(
        z=z, x=[DEFECTS[c][:34] for c in codes], y=permits, text=text,
        colorscale=[[0.0, "#f8fafc"], [0.33, "#fde68a"], [0.66, HIGH], [1.0, CRIT]],
        zmin=0, zmax=3, showscale=False, xgap=3, ygap=3,
        hovertemplate="<b>%{y}</b><br>%{x}<br>severity: %{text}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT,
        height=120 + 40 * len(permits),
        title=dict(text="<b>Where the structural defects are</b>", font=dict(size=13)),
        xaxis=dict(tickangle=-35, side="bottom"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ==================================================================================================
# 5. Provenance
# ==================================================================================================

def provenance_donut(prov: dict):
    """How much of the agents' reasoning traces to a real procedure? Unverified is not hidden."""
    v, u = prov.get("verified", 0), prov.get("unverified", 0)
    if v + u == 0:
        return None

    fig = go.Figure(go.Pie(
        labels=["Traced to a real procedure", "Could NOT be traced — verify by hand"],
        values=[v, u], hole=0.62,
        marker=dict(colors=[OK, HIGH], line=dict(color="white", width=2)),
        textinfo="value", sort=False,
        hovertemplate="%{label}<br><b>%{value}</b> assertion(s)<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT, height=260,
        title=dict(text=f"<b>{prov.get('verified_pct', 0)}% of assertions provenance-verified</b>",
                   font=dict(size=13)),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        annotations=[dict(text=f"<b>{v}/{v + u}</b>", x=0.5, y=0.5,
                          font=dict(size=22, family="Inter"), showarrow=False)],
    )
    return fig
