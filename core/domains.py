"""
HOLDPOINT — Industry Packs
==========================

The agent graph contains no industry-specific logic. What makes HOLDPOINT "a refinery tool" or
"a mine tool" lives here: the hazard vocabulary, the substances, the regulatory frame, the
authorising roles.

Each pack carries an EVIDENCE STATUS, and the app displays it. This is deliberate.

The research behind this product verified the permit-assurance thesis for REFINING/CHEMICALS
(US CSB, PEMEX Deer Park final report, Feb 2026) and for MINING (ICMM 2020-2024 safety data).
It did NOT verify it for UTILITIES — that pack is a well-founded HYPOTHESIS built on OSHA's
controlling-employer policy, NFPA 70E energised-work permits and contractor-heavy line work,
but the supporting data was never gathered.

We label it as a hypothesis rather than quietly presenting it as a finding. A product that
overstates its own evidence has no business telling anyone else to verify theirs.
"""

import os

DEFAULT_SITE = "refining"


REFINING = {
    "key": "refining",
    "label": "Refining & Chemicals",
    "site_name": "Gulf Coast Refinery — Unit 12",
    # Real coordinates — Deer Park, Texas. Used to fetch REAL sunrise/sunset and wind.
    "lat": 29.72, "lon": -95.13, "tz": "America/Chicago",
    "evidence_status": "VERIFIED",
    "evidence_note": (
        "Verified. US Chemical Safety Board final report on the PEMEX Deer Park incident "
        "(released 23 Feb 2026) names an over-broad work permit without clear hold points as a "
        "contributing factor in a hydrogen sulphide release that killed two contract workers."
    ),
    "regulator": "OSHA (Process Safety Management, 29 CFR 1910.119) · US Chemical Safety Board (investigative)",
    "authorising_role": "Issuing Authority (Operations Shift Supervisor)",
    "performing_role": "Performing Authority (Contractor Supervisor)",
    "key_substances": [
        "Hydrogen sulphide (H2S) — acutely toxic, IDLH 100 ppm",
        "Hydrocarbon vapour — flammable",
        "Amine (rich) — dissolved H2S",
        "Hydrofluoric acid (alkylation units)",
        "Steam / hot condensate — thermal",
    ],
    "critical_controls": [
        "Positive isolation (spade/blind) before breaking containment on toxic service",
        "Positive equipment identification by permanent tag number, by two parties, at the equipment",
        "Operations representative present when containment is first broken",
        "Gas test immediately before hot work and at intervals thereafter",
        "Continuous area H2S monitoring with audible alarm",
        "Escape sets and rescue team standing by",
    ],
    "high_risk_activities": [
        "Breaking containment / line breaks",
        "Hot work",
        "Confined space entry",
        "Work during turnaround on a partially operational unit",
    ],
}


MINING = {
    "key": "mining",
    "label": "Mining & Metals",
    "site_name": "Copper Concentrator — Process Plant",
    # Real coordinates — Morenci, Arizona (copper district).
    "lat": 33.05, "lon": -109.36, "tz": "America/Phoenix",
    "evidence_status": "VERIFIED",
    "evidence_note": (
        "Verified. ICMM '2020-2024 Safety Performance: Insights' (July 2025): 42 member fatalities "
        "in 2024, a second consecutive rise. 41% of process-plant fatal incidents occur during "
        "non-routine tasks, often contractor-executed; permit-to-work and lock-out/tag-out "
        "weaknesses 'frequently contribute'. NOTE: mining's LARGEST fatal cause is "
        "mobile-equipment interaction, which this product does not address."
    ),
    "regulator": "MSHA (US) · ICMM member commitments · national mines inspectorates",
    "authorising_role": "Area Owner / Responsible Supervisor",
    "performing_role": "Permit Holder (Contractor Supervisor)",
    "key_substances": [
        "Stored gravitational energy — loaded conveyors, ore bins, chutes",
        "Stored mechanical energy — tensioned belts, springs",
        "Slurry under pressure",
        "Cyanide (leach circuits)",
        "Sulphur dioxide / acid mist (smelting)",
    ],
    "critical_controls": [
        "Energy isolation covering ALL sources — including gravity and stored mechanical energy",
        "Personal locks applied individually; never applied on another's behalf",
        "Isolation proven, not merely applied",
        "Critical control verification in the field, not on paper",
        "Contractor competency verified against the individual",
    ],
    "high_risk_activities": [
        "Clearing blockages on conveyors and chutes (non-routine)",
        "Working under suspended loads",
        "Confined space entry into bins, chutes and mills",
        "Maintenance during plant stoppage",
    ],
}


UTILITIES = {
    "key": "utilities",
    "label": "Utilities (T&D)",
    "site_name": "Distribution Network — Substation & Overhead",
    # Real coordinates — northern California service territory.
    "lat": 38.58, "lon": -121.49, "tz": "America/Los_Angeles",
    "evidence_status": "HYPOTHESIS — NOT VERIFIED",
    "evidence_note": (
        "NOT VERIFIED. This pack is a well-founded hypothesis, not a research finding. The argument: "
        "utilities depend heavily on contractor line and substation crews; OSHA's multi-employer / "
        "controlling-employer policy creates owner liability for contractor work; NFPA 70E energised- "
        "work permits and switching/clearance orders are mandated, audited workflows; and storm "
        "restoration is a non-routine work surge. Utility contractor fatality data was NOT gathered "
        "and this thesis is UNTESTED. Treat findings from this pack as indicative only."
    ),
    "regulator": "OSHA 29 CFR 1910.269 · NFPA 70E · state utility commissions",
    "authorising_role": "Switching & Clearance Authority (Control Room)",
    "performing_role": "Crew Foreman (Contractor)",
    "key_substances": [
        "Energised conductors — electrical",
        "Stored electrical energy — capacitors, batteries",
        "Induced voltage from parallel circuits",
        "SF6 (switchgear)",
        "Stored mechanical energy — tensioned conductors, springs in breakers",
    ],
    "critical_controls": [
        "Positive identification of the specific circuit and structure — not the work zone",
        "Test-before-touch on the specific conductor",
        "Grounding applied on both sides of the work location",
        "Clearance held by a single named individual",
        "Induced-voltage assessment where circuits share a structure",
    ],
    "high_risk_activities": [
        "Switching and clearance operations",
        "Work on or near energised conductors",
        "Storm restoration (non-routine, time-pressured, contractor-surged)",
        "Substation maintenance with adjacent circuits live",
    ],
}


SITE_PACKS = {
    REFINING["key"]: REFINING,
    MINING["key"]: MINING,
    UTILITIES["key"]: UTILITIES,
}

SITE_LABELS = {k: v["label"] for k, v in SITE_PACKS.items()}


def get_active_site_key() -> str:
    key = os.getenv("ACTIVE_SITE", DEFAULT_SITE)
    return key if key in SITE_PACKS else DEFAULT_SITE


def get_site(key: str | None = None) -> dict:
    return SITE_PACKS[key or get_active_site_key()]


def set_active_site(key: str) -> None:
    if key not in SITE_PACKS:
        raise ValueError(f"Unknown site pack '{key}'. Known: {list(SITE_PACKS)}")
    os.environ["ACTIVE_SITE"] = key


def build_site_context(key: str | None = None) -> str:
    """Shared context prepended to every agent prompt. The single point of industry grounding."""
    s = get_site(key)
    substances = "\n".join(f"- {x}" for x in s["key_substances"])
    controls = "\n".join(f"- {x}" for x in s["critical_controls"])

    return f"""You are part of HOLDPOINT, a permit-to-work assurance system operating at:

  SITE:       {s['site_name']}
  INDUSTRY:   {s['label']}
  REGULATOR:  {s['regulator']}
  AUTHORISER: {s['authorising_role']}

Hazardous energies and substances present at this site:
{substances}

Critical controls that carry the fatal risk at this site:
{controls}

WHAT THIS SYSTEM IS FOR
You review a permit AFTER it has been written and BEFORE it is authorised. You are an independent
adversary, not a drafting assistant. Your purpose is to find the defect that would kill someone,
and to refuse to let it through.

TWO RULES THAT OVERRIDE EVERYTHING ELSE

1. NEVER INVENT A CONTROL. Every control, requirement or safeguard you assert as MANDATED must be
   supported by a VERBATIM QUOTE from the site procedures supplied to you. Copy the sentence
   exactly — do not paraphrase it. This system programmatically checks your quote against the real
   document, and an assertion whose quote cannot be found is shown to the human as UNVERIFIED.
   If you believe a control is necessary but no procedure requires it, say so and label it as your
   professional inference. An invented safeguard is the one unforgivable error in a safety system:
   it manufactures false assurance in the exact place built to prevent it.

2. YOU DO NOT AUTHORISE ANYTHING. A qualified human authoriser decides. Your output is decision
   support. Say so.
"""
