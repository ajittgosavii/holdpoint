"""
HOLDPOINT — Site Procedure Corpus
=================================

The ground truth. Every control HOLDPOINT asserts must trace to a verbatim quote from one of
these documents. If an agent claims "an operator must be present before the line is opened",
that sentence has to actually exist here — or the claim is flagged UNVERIFIED to the human.

In production this is the client's real document management system (SharePoint, Documentum,
SAP DMS). Here it is a small, realistic corpus so the provenance check can be demonstrated
end to end.

DATA PROVENANCE: these procedure texts are ILLUSTRATIVE — written to be realistic in structure
and vocabulary, and to reflect the control language that real permit-to-work, isolation and
hot-work standards use. They are not any operator's actual procedures.
"""

PROCEDURES = [
    {
        "doc_id": "SP-PTW-001",
        "title": "Permit to Work Standard",
        "revision": "Rev 7, 2025-04-01",
        "text": """PERMIT TO WORK STANDARD (SP-PTW-001)

1. SCOPE OF A PERMIT
1.1 A permit to work shall authorise ONE task, in ONE location, with ONE set of hazards and
    ONE responsible performing party. Where a work scope covers multiple tasks with differing
    hazards, a separate permit shall be raised for each task.
1.2 A permit shall not be used as a blanket authorisation for a work campaign, a shift, or a
    contractor's daily scope of work.
1.3 The Issuing Authority shall reject any permit whose description of work does not allow the
    specific hazards of the task to be identified.

2. HOLD POINTS
2.1 Any instruction that requires work to stop and a further check, test or authorisation to be
    obtained before proceeding shall be recorded as a HOLD POINT.
2.2 A hold point shall be listed as a discrete, numbered, signed-off step on the face of the
    permit. It shall not be recorded only within the narrative description of the work.
2.3 Work shall not proceed past a hold point until the named competent person has physically
    attended, verified the condition, and signed the permit.

3. VALIDITY
3.1 A permit is valid for one shift only and shall be revalidated at each shift handover by the
    Issuing Authority and the Performing Authority together.
3.2 On revalidation, the plant condition shall be reconfirmed. A permit shall not be revalidated
    on the basis of the previous shift's confirmation alone.

4. CONCURRENT WORK (SIMOPS)
4.1 The Issuing Authority shall review all permits already live on the affected unit before
    issuing a new permit.
4.2 Hot work shall not be authorised on a unit where a hydrocarbon or toxic line break is live
    under any other permit.
4.3 Where two permits require isolation of the same system, a single coordinated isolation shall
    be raised and both performing parties shall apply their own locks.
""",
    },
    {
        "doc_id": "SP-ISO-002",
        "title": "Energy Isolation and Lock-Out / Tag-Out Standard",
        "revision": "Rev 5, 2025-09-12",
        "text": """ENERGY ISOLATION AND LOCK-OUT / TAG-OUT STANDARD (SP-ISO-002)

1. ISOLATION PLANNING
1.1 An isolation plan shall identify every energy source capable of reaching the work location,
    including process fluids, electrical supply, stored pressure, gravity and stored mechanical
    energy.
1.2 Positive isolation by spade, blind or physical disconnection is required before any line
    containing hydrogen sulphide, hydrofluoric acid, or any Category 1 toxic substance is opened.
    Valve isolation alone is not sufficient for these substances.
1.3 Double block and bleed shall be used where positive isolation is not reasonably practicable,
    and the deviation shall be approved in writing by the Operations Manager.

2. LOCK APPLICATION
2.1 Each individual working under an isolation shall apply a personal lock to the isolation point
    or to the group lock box.
2.2 Locks shall not be applied on behalf of another person under any circumstances.

3. VERIFICATION BEFORE BREAKING CONTAINMENT
3.1 Before any pressure-containing envelope is opened, the equipment shall be positively
    identified against the isolation plan by BOTH the Performing Authority and an Operations
    representative, working together at the equipment.
3.2 Positive identification shall be by permanent equipment tag number. Identification by
    position, description, or proximity to other equipment is not acceptable.
3.3 The line shall be proven depressurised and drained at the low-point bleed before the first
    flange bolt is slackened.
3.4 An Operations representative shall be present at the work location at the moment containment
    is first broken.
""",
    },
    {
        "doc_id": "SP-H2S-004",
        "title": "Hydrogen Sulphide (H2S) Control Standard",
        "revision": "Rev 3, 2026-01-15",
        "text": """HYDROGEN SULPHIDE (H2S) CONTROL STANDARD (SP-H2S-004)

1. APPLICABILITY
1.1 This standard applies to any task that may result in exposure to hydrogen sulphide,
    including any breaking of containment on a sour system.

2. MANDATORY CONTROLS
2.1 Personal H2S monitors shall be worn by every person entering the work area, and shall be
    bump-tested on the day of use.
2.2 Continuous area monitoring with audible alarm shall be established at the work location
    before containment is broken.
2.3 Escape sets (10-minute minimum) shall be carried by every person in the work area.
2.4 Positive-pressure breathing apparatus shall be available at the muster point and the
    rescue team shall be briefed and standing by before containment is broken.
2.5 Work on sour systems shall not proceed during hours of darkness.

3. WIND AND MUSTER
3.1 The wind direction shall be confirmed at the work location immediately before containment is
    broken, and the escape route briefed to all parties.
3.2 A dedicated safety attendant shall be stationed upwind with a clear line of sight to the
    work party, and shall have no other duties.
""",
    },
    {
        "doc_id": "SP-HOT-003",
        "title": "Hot Work Standard",
        "revision": "Rev 4, 2025-06-20",
        "text": """HOT WORK STANDARD (SP-HOT-003)

1. GAS TESTING
1.1 A gas test shall be carried out immediately before hot work commences and shall be repeated
    at intervals not exceeding 60 minutes while the work continues.
1.2 Hot work shall not commence if the gas test indicates any detectable flammable vapour.
1.3 Gas test results shall be recorded on the face of the permit with the time of each test.

2. FIRE WATCH
2.1 A dedicated fire watch shall be posted for the duration of the hot work and shall remain in
    position for 60 minutes after the work is complete.
2.2 The fire watch shall have no duties other than fire watch.

3. EXCLUSION
3.1 Hot work shall not be carried out within 15 metres of any open drain, sample point, or vent
    which is not isolated and blanked.
""",
    },
    {
        "doc_id": "SP-CON-006",
        "title": "Contractor Competency and Induction Standard",
        "revision": "Rev 2, 2025-11-03",
        "text": """CONTRACTOR COMPETENCY AND INDUCTION STANDARD (SP-CON-006)

1. INDUCTION
1.1 Site induction is a prerequisite for site access and does not by itself qualify any person
    to perform hazardous work.

2. TASK-SPECIFIC COMPETENCY
2.1 Every person named on a permit shall hold a current, verified competency for EACH hazard
    identified on that permit.
2.2 Competency shall be verified against the individual, not against the contracting company.
2.3 H2S competency (including escape set use) shall be current within 12 months.
2.4 Confined space entry competency shall be current within 24 months.
2.5 Where a worker is reassigned from one unit to another during a shift, a hazard briefing
    specific to the receiving unit shall be delivered and recorded before that worker enters the
    new work area.

3. SUPERVISION
3.1 Where a work party includes personnel from more than one contracting company, a single named
    Performing Authority shall be accountable for the whole party, and shall be identified on the
    permit.
""",
    },
]


def procedure_corpus() -> list[dict]:
    """The corpus the provenance verifier checks every asserted control against."""
    return PROCEDURES


def procedures_as_text() -> str:
    """Flattened corpus for injection into agent prompts."""
    return "\n\n".join(
        f"=== {p['doc_id']} — {p['title']} ({p['revision']}) ===\n{p['text']}"
        for p in PROCEDURES
    )
