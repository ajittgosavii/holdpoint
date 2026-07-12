"""
HOLDPOINT — Major-Accident Precedent Corpus
===========================================

Thirty years of fatal-accident investigations, turned into a live control.

When a permit is submitted, HOLDPOINT retrieves against this corpus and tells the authoriser:
"this permit shares the structural pattern of the permit that killed two people at Deer Park."
That is a different and far more powerful statement than "you may have missed a hazard".

HONESTY ABOUT SOURCES — this matters, and the app surfaces it:
  verification = "verified"    -> the finding and quotes come from the public investigation report
                                  named in `source`. Quoted text is the investigator's own wording.
  verification = "illustrative"-> a realistic pattern written to exercise the matcher. NOT a real
                                  incident. The app labels these clearly and never presents them as
                                  real precedent.

We do not blur that line. A safety tool that cites a fabricated fatality to make its point has
forfeited the right to be believed about anything.
"""

INCIDENTS = [
    {
        "incident_id": "CSB-2024-DEERPARK",
        "title": "PEMEX Deer Park refinery — hydrogen sulphide release, two contract workers killed",
        "date": "2024-10-10",
        "industry": "Refining",
        "fatalities": 2,
        "verification": "verified",
        "source": "US Chemical Safety and Hazard Investigation Board (CSB), final report released 23 February 2026",
        "source_url": "https://www.csb.gov/investigations/",
        "summary": (
            "Contract workers opened a line on a hydrogen sulphide service while the unit was "
            "partially operational. More than 27,000 lb of H2S was released. Two contract workers "
            "from two different contracting firms were killed; 13 were transported to medical "
            "facilities and dozens more treated on site. Two cities sheltered in place."
        ),
        "investigator_findings": [
            "\"The refinery issued a broad work permit covering multiple jobs with varying hazards and without clear hold points.\"",
            "\"Workers overlooked a written instruction to stop work and obtain an operator's presence before opening the hydrogen sulfide piping.\"",
        ],
        "root_cause_note": (
            "IMPORTANT AND STATED HONESTLY: the CSB's ROOT cause was failure to positively identify "
            "the correct equipment — workers opened a near-identical flange approximately five feet "
            "from the intended one. The permit deficiencies were CONTRIBUTING factors. A permit "
            "reviewer would not have prevented the root cause. It would have addressed the "
            "contributing structure that let the root cause become fatal."
        ),
        "structural_pattern": [
            "over_broad_scope",          # one permit, multiple jobs, differing hazards
            "no_hold_points",            # safeguard present in prose, never an enforced step
            "buried_stop_work",          # the correct instruction WAS written down, and was read past
            "contractor_multi_company",  # two firms on one scope
            "partially_operational_unit",# live toxic inventory adjacent to the work
        ],
        "lesson": (
            "The safeguard was already in the permit. The failure was structural, not authorial. "
            "A tool that recommends hazards would have recommended one that was already listed. "
            "What was missing was decomposition of the scope and enforcement of the stop-work "
            "instruction as a discrete, signed hold point."
        ),
    },
    {
        "incident_id": "PIPER-ALPHA-1988",
        "title": "Piper Alpha — permit-to-work and shift-handover failure, 167 killed",
        "date": "1988-07-06",
        "industry": "Oil & Gas (offshore)",
        "fatalities": 167,
        "verification": "verified",
        "source": "The Public Inquiry into the Piper Alpha Disaster (Cullen Inquiry, 1990)",
        "source_url": "https://www.hse.gov.uk/offshore/piper-alpha-disaster-public-inquiry.htm",
        "summary": (
            "A pressure safety valve had been removed from a condensate pump for maintenance and a "
            "blank flange fitted in its place. The permit covering that work was not effectively "
            "communicated at shift handover. The oncoming shift, unaware, started the pump. "
            "Condensate escaped from the incomplete assembly and ignited. 167 people died. The "
            "Cullen Inquiry's findings on the permit-to-work system became the foundation of modern "
            "control-of-work practice."
        ),
        "investigator_findings": [
            "The permit-to-work system was found to be applied inconsistently, with permits not "
            "reliably communicated between shifts.",
            "Two permits relating to the same equipment were not cross-referenced.",
        ],
        "root_cause_note": (
            "The canonical permit-to-work failure. The information required to prevent the disaster "
            "existed on a permit. It did not reach the person who needed it."
        ),
        "structural_pattern": [
            "shift_handover_gap",
            "concurrent_permits_same_equipment",
            "isolation_state_not_communicated",
            "no_hold_points",
        ],
        "lesson": (
            "Two permits touching the same equipment must be cross-referenced, and a permit must be "
            "revalidated against the actual plant condition at handover — not against the previous "
            "shift's word for it."
        ),
    },
    {
        "incident_id": "CSB-2005-TEXASCITY",
        "title": "BP Texas City refinery — explosion during unit startup, 15 killed",
        "date": "2005-03-23",
        "industry": "Refining",
        "fatalities": 15,
        "verification": "verified",
        "source": "US Chemical Safety and Hazard Investigation Board (CSB), investigation report 2007",
        "source_url": "https://www.csb.gov/bp-america-refinery-explosion/",
        "summary": (
            "During startup of the raffinate splitter, the tower was overfilled and liquid was routed "
            "to a blowdown drum that vented to atmosphere. The resulting vapour cloud ignited. All 15 "
            "of those killed were contractors, working in and around temporary trailers that had been "
            "sited close to the blowdown stack."
        ),
        "investigator_findings": [
            "The siting of occupied contractor trailers near a process unit undergoing startup was a "
            "critical factor in the fatality count.",
            "Non-essential personnel were not removed from the area during a hazardous, non-routine "
            "operation.",
        ],
        "root_cause_note": (
            "The fatalities were driven by WHO was allowed to be WHERE during a high-hazard "
            "non-routine operation — a work-authorisation and simultaneous-operations question."
        ),
        "structural_pattern": [
            "simops_conflict",
            "non_essential_personnel_in_hazard_zone",
            "non_routine_operation",
            "contractor_exposure",
        ],
        "lesson": (
            "Authorising work is not only about the crew doing the job. It is about everyone else who "
            "is permitted to be nearby while a hazardous non-routine operation is under way."
        ),
    },
    {
        "incident_id": "ICMM-2020-2024",
        "title": "ICMM industry safety data 2020–2024 — where mining fatalities actually happen",
        "date": "2025-07-01",
        "industry": "Mining & Metals",
        "fatalities": 42,
        "verification": "verified",
        "source": "ICMM, '2020–2024 Safety Performance: Insights' (July 2025), covering ~1/3 of the global metals and mining industry",
        "source_url": "https://www.icmm.com/en-gb/research/health-safety/2025/insights-2020-2024-safety-data",
        "summary": (
            "42 fatalities across ICMM member companies in 2024, up from 36 in 2023 and 33 in 2022 — "
            "a second consecutive annual rise, which ICMM itself calls 'hugely troubling and demands "
            "a response'. Contractors accounted for 45% of 2024 fatalities."
        ),
        "investigator_findings": [
            "\"In process plants, nearly half of all fatal incidents (41%) occur during unusual or "
            "non-routine tasks, often undertaken by contractors.\"",
            "\"Weaknesses in site safety paperwork (the 'permit-to-work') or in isolating and locking "
            "out energy sources ('lock-out/tag-out') frequently contribute.\"",
            "ICMM prescribes moving \"from a mindset of simply 'identify and document' to one of "
            "'verify and act'\".",
        ],
        "root_cause_note": (
            "STATED HONESTLY: ICMM's single largest fatal cause is mobile-equipment interaction, whose "
            "remedies are proximity detection and LiDAR — nothing to do with permits. The "
            "permit/isolation slice is real but is a MINORITY of total harm. Also, on an "
            "exposure-adjusted basis contractor fatality frequency (0.012) was LOWER than employees' "
            "(0.020) in 2024."
        ),
        "structural_pattern": [
            "non_routine_task",
            "contractor_executed",
            "ptw_weakness",
            "loto_weakness",
        ],
        "lesson": (
            "The risk concentrates in non-routine, contractor-executed work — precisely the work a "
            "permit exists to control. And the industry's own prescription is verification, not more "
            "documentation."
        ),
    },
    {
        "incident_id": "ILL-MINING-LOTO-01",
        "title": "Conveyor entrapment during non-routine clearing — stored energy not isolated",
        "date": "2025-xx-xx",
        "industry": "Mining & Metals",
        "fatalities": 1,
        "verification": "illustrative",
        "source": "ILLUSTRATIVE — not a real incident. Written to exercise the pattern matcher against the LOTO failure mode ICMM describes.",
        "source_url": None,
        "summary": (
            "A contractor entered a conveyor to clear a blockage during a non-routine stoppage. The "
            "drive motor was isolated electrically but the gravity/stored energy in the loaded belt was "
            "not restrained. The belt moved when the blockage cleared."
        ),
        "investigator_findings": [
            "The isolation plan addressed electrical energy only. Gravity and stored mechanical energy "
            "were not identified as energy sources.",
            "The permit was raised as a general 'clear blockage' permit with no task-specific hazard "
            "identification.",
        ],
        "root_cause_note": "Illustrative pattern, not a real investigation.",
        "structural_pattern": [
            "incomplete_energy_identification",
            "over_broad_scope",
            "non_routine_task",
            "contractor_executed",
        ],
        "lesson": (
            "An isolation plan that names only the obvious energy source is not an isolation plan. "
            "Gravity and stored mechanical energy kill people who believed they were isolated."
        ),
    },
    {
        "incident_id": "ILL-UTILITY-SWITCH-01",
        "title": "Contractor contact with energised conductor — switching order not cross-checked",
        "date": "2025-xx-xx",
        "industry": "Utilities (Transmission & Distribution)",
        "fatalities": 1,
        "verification": "illustrative",
        "source": "ILLUSTRATIVE — not a real incident. Written to test whether the permit pattern carries into utility switching/clearance work, which is a HYPOTHESIS this product has not yet verified.",
        "source_url": None,
        "summary": (
            "A contractor crew took a clearance on a distribution circuit. An adjacent circuit sharing "
            "the same structure remained energised. The clearance document described the work location "
            "by pole number but did not identify the second circuit."
        ),
        "investigator_findings": [
            "The clearance covered a work zone rather than a specific circuit and structure.",
            "No hold point required the crew to positively identify and test the specific conductor "
            "before contact.",
        ],
        "root_cause_note": (
            "Illustrative. NOTE: whether the permit-assurance thesis holds in UTILITIES is currently a "
            "hypothesis, not a verified finding. This entry exists to be tested, not to be cited."
        ),
        "structural_pattern": [
            "over_broad_scope",
            "no_hold_points",
            "positive_identification_absent",
            "contractor_executed",
        ],
        "lesson": (
            "Positive identification of the specific energised asset — not the work zone — is the "
            "control. The Deer Park root cause in another industry's clothing."
        ),
    },
]


def incident_corpus() -> list[dict]:
    return INCIDENTS


def verified_incidents() -> list[dict]:
    return [i for i in INCIDENTS if i["verification"] == "verified"]


def incident_as_text(inc: dict) -> str:
    findings = "\n".join(f"- {f}" for f in inc["investigator_findings"])
    return f"""INCIDENT {inc['incident_id']} — {inc['title']}
Date: {inc['date']} | Industry: {inc['industry']} | Fatalities: {inc['fatalities']}
Source: {inc['source']}
Evidence status: {inc['verification'].upper()}

Summary: {inc['summary']}

Investigator findings:
{findings}

Root cause note: {inc['root_cause_note']}

Structural pattern: {', '.join(inc['structural_pattern'])}

Lesson: {inc['lesson']}"""


# Human-readable names for the structural patterns the matcher keys on.
PATTERN_LABELS = {
    "over_broad_scope": "Over-broad permit scope (multiple jobs, differing hazards, one permit)",
    "no_hold_points": "No enforced hold points",
    "buried_stop_work": "Stop-work instruction present in prose but not enforced as a step",
    "contractor_multi_company": "Multiple contracting companies on one work scope",
    "partially_operational_unit": "Live hazardous inventory adjacent to the work",
    "shift_handover_gap": "Permit/isolation state not carried across shift handover",
    "concurrent_permits_same_equipment": "Concurrent permits touching the same equipment",
    "isolation_state_not_communicated": "Isolation state not communicated to those affected",
    "simops_conflict": "Simultaneous operations conflict",
    "non_essential_personnel_in_hazard_zone": "Non-essential personnel permitted in the hazard zone",
    "non_routine_operation": "Non-routine operation",
    "non_routine_task": "Non-routine task",
    "contractor_exposure": "Contractor exposure",
    "contractor_executed": "Contractor-executed work",
    "ptw_weakness": "Permit-to-work weakness",
    "loto_weakness": "Lock-out / tag-out weakness",
    "incomplete_energy_identification": "Isolation plan does not identify all energy sources",
    "positive_identification_absent": "No positive identification of the specific equipment",
}
