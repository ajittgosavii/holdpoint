"""
HOLDPOINT — Permit Corpus
=========================

Permit packs submitted for authorisation. Each carries the permit, the isolation plan, the JSA,
the assigned personnel with their competency records, and the live state of the unit (including
other permits already active — the SIMOPS check).

PERMIT PTW-2026-0417 is the centrepiece. It is deliberately shaped like the permit the US
Chemical Safety Board described in its final report on the PEMEX Deer Park incident
(released 23 February 2026):

    "The refinery issued a broad work permit covering multiple jobs with varying hazards and
     without clear hold points."
    "Workers overlooked a written instruction to stop work and obtain an operator's presence
     before opening the hydrogen sulfide piping."

Note what that means, because it is the whole thesis of this product: the correct safeguard was
ALREADY IN THE PERMIT. It was buried in a narrative field, inside an over-broad scope, and it was
read past. Two contract workers died. A tool that "recommends hazards" would have recommended a
hazard that was already there. What was missing was an adversary that decomposed the scope and
forced that sentence to become an enforced, signed hold point.

DATA PROVENANCE: these permits are ILLUSTRATIVE reconstructions, written to carry the structural
defects that real investigations describe. They are not the actual PEMEX permit, which is not
public. The CSB quotes above are real; the permit text below is not.
"""

PERMITS = [
    # =====================================================================================
    # THE DEER PARK PATTERN — the demo case
    # =====================================================================================
    {
        "permit_id": "PTW-2026-0417",
        "title": "Turnaround maintenance — Unit 12 sour water stripper area",
        "unit": "Unit 12 — Sour Water Stripper (SWS)",
        "requested_by": "M. Alvarez (Maintenance Supervisor)",
        "shift": "Days, 06:00–18:00",
        "status": "AWAITING AUTHORISATION",
        "planted_defect": "deer_park",  # for the backlog-scan metric; never shown to the agents
        "work_description": """Turnaround scope of work for Unit 12 SWS area, days shift.

Crews to carry out the following as required during the shift: (1) replace the pressure relief
valve on the overhead line; (2) remove and refit the spool piece on the 6" sour water line to the
stripper feed pump; (3) scaffold erection around the stripper column for insulation work;
(4) replace instrument tubing on the level transmitter; (5) grinding and welding repairs to the
pipe support brackets at grade.

Work to be carried out by Repcon crew (mechanical) and ISC crew (scaffold/instrument) as
scheduled by the maintenance supervisor across the shift. Crews to coordinate between themselves
on sequencing. Note that the sour water line contains H2S and prior to opening the line the crew
should stop and obtain an operator to be present at the flange before breaking containment, and
the line must be confirmed drained. Standard PPE plus H2S monitors. Area is a known sour service
area, take care. Scaffold crew to work around the mechanical crew as access permits.""",
        "hazards_identified": [
            "Hydrogen sulphide (H2S)",
            "Working at height",
            "Hot work (welding/grinding)",
            "Manual handling",
        ],
        "controls_listed": [
            "Standard PPE",
            "Personal H2S monitors to be worn",
            "Toolbox talk before work",
            "Scaffold to be tagged by competent scaffolder",
        ],
        "hold_points_listed": [],  # <-- none. This is the defect.
        "isolation_plan": """Isolation IS-2026-0212: Sour water line to stripper feed pump.
Close upstream block valve V-1204 and downstream block valve V-1207. Lock and tag both valves.
Bleed via low point drain LP-12-03.
(No spade/blind fitted. Positive isolation not applied.)""",
        "jsa_summary": """JSA-2026-0417: Sour water line spool replacement.
Steps: isolate line, drain, slacken bolts, remove spool, fit new spool, torque, leak test.
Hazards: H2S, pressure, dropped objects. Controls: PPE, gas monitor, toolbox talk.""",
        "personnel": [
            {"name": "J. Ruiz", "company": "Repcon", "role": "Performing Authority (mechanical)",
             "site_induction": "current (2026-01-14)",
             "competencies": ["Mechanical fitting (current)", "Confined space (current)"],
             "h2s_competency": "EXPIRED 2024-11-02"},
            {"name": "D. Okafor", "company": "Repcon", "role": "Fitter",
             "site_induction": "current (2026-02-03)",
             "competencies": ["Mechanical fitting (current)", "H2S awareness (current 2025-08-19)"],
             "h2s_competency": "current (2025-08-19)"},
            {"name": "T. Brannon", "company": "ISC Constructors", "role": "Scaffolder",
             "site_induction": "current (2026-03-01)",
             "competencies": ["Scaffold erection (current)"],
             "h2s_competency": "NONE ON RECORD"},
            {"name": "S. Whitfield", "company": "ISC Constructors", "role": "Instrument tech",
             "site_induction": "current (2026-03-01)",
             "competencies": ["Instrumentation (current)"],
             "h2s_competency": "NONE ON RECORD"},
        ],
        "unit_state": """Unit 12 SWS: PARTIALLY OPERATIONAL. Stripper column remains in service on
recycle. Sour water feed header live and pressurised upstream of V-1204. H2S concentration in
process fluid: 8,400 ppm. Wind: light and variable. Hours of darkness: N/A (days shift).""",
        "concurrent_permits": [
            {"permit_id": "PTW-2026-0402", "description": "Hot work — welding repairs to pipe rack, Unit 12 grade level",
             "status": "ACTIVE", "unit": "Unit 12"},
            {"permit_id": "PTW-2026-0410", "description": "Sample point maintenance — Unit 12 SWS overhead drain, drain left open",
             "status": "ACTIVE", "unit": "Unit 12"},
        ],
    },

    # =====================================================================================
    # A well-formed permit — HOLDPOINT should authorise this. A tool that flags everything
    # is as useless as one that flags nothing.
    # =====================================================================================
    {
        "permit_id": "PTW-2026-0431",
        "title": "Replace pressure gauge on cooling water line, Unit 7",
        "unit": "Unit 7 — Cooling Water",
        "requested_by": "R. Chen (Maintenance Planner)",
        "shift": "Days, 06:00–18:00",
        "status": "AWAITING AUTHORISATION",
        "planted_defect": None,
        "work_description": """Replace pressure gauge PI-0712 on the cooling water return line at
grade, Unit 7. Single task. Non-hazardous fluid (treated cooling water, ambient temperature,
3 barg). Isolate at instrument root valve, depressurise, replace gauge, recommission.""",
        "hazards_identified": ["Stored pressure (low)", "Manual handling"],
        "controls_listed": [
            "Isolate at root valve RV-0712 and lock",
            "Prove depressurised at bleed before removing gauge",
            "Standard PPE",
        ],
        "hold_points_listed": [
            "HP1: Prove line depressurised at bleed — signed by Performing Authority before gauge removed",
        ],
        "isolation_plan": """Isolation IS-2026-0233: Instrument root valve RV-0712 closed, locked
and tagged. Bleed to atmosphere via instrument bleed. Low-hazard fluid; valve isolation
appropriate.""",
        "jsa_summary": """JSA-2026-0431: Gauge replacement. Steps: isolate, bleed, prove dead,
remove, replace, recommission. Hazards: residual pressure. Controls: lock/tag, prove at bleed.""",
        "personnel": [
            {"name": "A. Kowalski", "company": "In-house", "role": "Performing Authority (instrument)",
             "site_induction": "current (2026-01-08)",
             "competencies": ["Instrumentation (current)", "Isolation authority (current)"],
             "h2s_competency": "current (2025-12-01)"},
        ],
        "unit_state": """Unit 7 cooling water: NORMAL OPERATION. Cooling water return line at
3 barg, ambient. No toxic or flammable inventory.""",
        "concurrent_permits": [],
    },

    # =====================================================================================
    # Competency mismatch + shift-handover / reassignment defect
    # =====================================================================================
    {
        "permit_id": "PTW-2026-0428",
        "title": "Confined space entry — Vessel V-305 internal inspection",
        "unit": "Unit 3 — Crude Distillation",
        "requested_by": "P. Nakamura (Inspection Lead)",
        "shift": "Days, 06:00–18:00",
        "status": "AWAITING AUTHORISATION",
        "planted_defect": "competency_gap",
        "work_description": """Internal inspection of vessel V-305 following shutdown and cleaning.
Entry to be made by inspection contractor. Vessel has been steamed and purged. Crew reassigned
from Unit 9 mid-shift yesterday to support this scope.""",
        "hazards_identified": ["Confined space", "Oxygen deficiency", "Residual hydrocarbon"],
        "controls_listed": [
            "Gas test before entry",
            "Standby man at entry point",
            "Rescue plan in place",
            "Entry log maintained",
        ],
        "hold_points_listed": [
            "HP1: Gas test satisfactory — signed before entry",
        ],
        "isolation_plan": """Isolation IS-2026-0229: V-305 isolated by spades on feed, product and
steam lines. Locks applied by Operations. Vessel opened and ventilated.""",
        "jsa_summary": """JSA-2026-0428: Confined space entry for visual inspection. Steps: gas test,
enter, inspect, exit. Hazards: O2 deficiency, hydrocarbon residue, entrapment.""",
        "personnel": [
            {"name": "L. Traoré", "company": "InspecTech", "role": "Performing Authority (inspector)",
             "site_induction": "current (2026-02-20)",
             "competencies": ["Vessel inspection (current)"],
             "h2s_competency": "current (2025-10-05)",
             "confined_space_competency": "EXPIRED 2023-09-30"},
            {"name": "M. Farrow", "company": "InspecTech", "role": "Standby man",
             "site_induction": "current (2026-02-20)",
             "competencies": ["Standby/hole watch (current)"],
             "h2s_competency": "current (2025-10-05)",
             "confined_space_competency": "current (2025-06-11)"},
        ],
        "unit_state": """Unit 3 CDU: SHUTDOWN. V-305 open, steamed and purged. Adjacent V-306
remains in service and contains hydrocarbon. Note: crew reassigned from Unit 9 mid-shift; no
record of a Unit 3 specific hazard briefing on file.""",
        "concurrent_permits": [
            {"permit_id": "PTW-2026-0425", "description": "Line break on V-306 product draw — adjacent vessel, in service",
             "status": "ACTIVE", "unit": "Unit 3"},
        ],
    },

    # =====================================================================================
    # SIMOPS conflict: hot work authorised alongside a live toxic line break
    # =====================================================================================
    {
        "permit_id": "PTW-2026-0433",
        "title": "Hot work — structural weld repair, Unit 12 pipe rack",
        "unit": "Unit 12 — Sour Water Stripper (SWS)",
        "requested_by": "K. Mbeki (Construction Supervisor)",
        "shift": "Days, 06:00–18:00",
        "status": "AWAITING AUTHORISATION",
        "planted_defect": "simops",
        "work_description": """Welding repair to cracked support bracket on Unit 12 pipe rack at
grade. Grinding to prepare, weld, dress. Approximately 4 hours.""",
        "hazards_identified": ["Hot work", "Sparks/hot metal", "Fume"],
        "controls_listed": [
            "Gas test before commencing",
            "Fire watch posted",
            "Fire blanket over drains in immediate vicinity",
            "Welding screens",
        ],
        "hold_points_listed": [
            "HP1: Gas test clear — signed before arc struck",
        ],
        "isolation_plan": "N/A — no energy isolation required for external structural weld.",
        "jsa_summary": """JSA-2026-0433: Structural weld. Steps: erect screens, gas test, grind,
weld, dress, fire watch. Hazards: ignition of flammable/toxic vapour, hot metal, fume.""",
        "personnel": [
            {"name": "G. Iversen", "company": "WeldCo", "role": "Performing Authority (welder)",
             "site_induction": "current (2026-01-30)",
             "competencies": ["Coded welding (current)", "Hot work (current)"],
             "h2s_competency": "current (2025-11-14)"},
            {"name": "B. Achebe", "company": "WeldCo", "role": "Fire watch",
             "site_induction": "current (2026-01-30)",
             "competencies": ["Fire watch (current)"],
             "h2s_competency": "current (2025-11-14)"},
        ],
        "unit_state": """Unit 12 SWS: PARTIALLY OPERATIONAL. Sour water feed header live,
H2S 8,400 ppm. Sample point drain on SWS overhead currently OPEN under PTW-2026-0410.""",
        "concurrent_permits": [
            {"permit_id": "PTW-2026-0417", "description": "Sour water line break — H2S service, containment to be broken",
             "status": "PENDING AUTHORISATION", "unit": "Unit 12"},
            {"permit_id": "PTW-2026-0410", "description": "Sample point maintenance — SWS overhead drain left OPEN",
             "status": "ACTIVE", "unit": "Unit 12"},
        ],
    },

    # =====================================================================================
    # Isolation adequacy: valve-only isolation on a toxic line
    # =====================================================================================
    {
        "permit_id": "PTW-2026-0436",
        "title": "Replace control valve CV-1188 — amine regenerator bottoms",
        "unit": "Unit 11 — Amine Regeneration",
        "requested_by": "H. Lindqvist (Maintenance Planner)",
        "shift": "Nights, 18:00–06:00",
        "status": "AWAITING AUTHORISATION",
        "planted_defect": "isolation_and_darkness",
        "work_description": """Remove and replace control valve CV-1188 on amine regenerator bottoms
line. Line contains rich amine with dissolved H2S. Night shift scope.""",
        "hazards_identified": ["H2S", "Hot fluid", "Stored pressure"],
        "controls_listed": [
            "Close and lock block valves BV-1188A and BV-1188B",
            "Drain via low point",
            "H2S monitors worn",
            "Escape sets carried",
        ],
        "hold_points_listed": [
            "HP1: Line proven drained — signed before bolts slackened",
        ],
        "isolation_plan": """Isolation IS-2026-0241: Close block valves BV-1188A (upstream) and
BV-1188B (downstream). Lock and tag. Drain via LP-11-07.
(Valve isolation only. No spade or blind fitted.)""",
        "jsa_summary": """JSA-2026-0436: Control valve replacement on rich amine line. Steps: isolate,
drain, purge, remove valve, fit replacement, torque, leak test.""",
        "personnel": [
            {"name": "C. Duval", "company": "Repcon", "role": "Performing Authority (mechanical)",
             "site_induction": "current (2026-01-14)",
             "competencies": ["Mechanical fitting (current)"],
             "h2s_competency": "current (2025-09-30)"},
            {"name": "N. Petrov", "company": "Repcon", "role": "Fitter",
             "site_induction": "current (2026-01-14)",
             "competencies": ["Mechanical fitting (current)"],
             "h2s_competency": "current (2025-09-30)"},
        ],
        "unit_state": """Unit 11 Amine Regeneration: IN SERVICE. Rich amine line contains dissolved
H2S at approximately 12,000 ppm in the vapour space on depressurisation. Night shift — hours of
darkness.""",
        "concurrent_permits": [],
    },
]


def get_permit(permit_id: str) -> dict | None:
    for p in PERMITS:
        if p["permit_id"] == permit_id:
            return p
    return None


def permit_ids() -> list[str]:
    return [p["permit_id"] for p in PERMITS]
