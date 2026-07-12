"""
HOLDPOINT — System-of-Record Connectors
=======================================

**HOLDPOINT does not replace your permit system. It stands in front of it.**

That is the entire commercial posture, and this module is what makes it real rather than a claim on
a slide. HOLDPOINT reads a permit OUT of whatever system the operator already runs — Enablon,
SAP Work Clearance Management, IBM Maximo, eVision Permit Vision — attacks it, and writes findings
and hold points BACK IN.

No rip-and-replace. Weeks to value instead of years. And the incumbent becomes a substrate rather
than an enemy — which also protects the services revenue an SI already earns implementing them.

--------------------------------------------------------------------------------------------------
THE HONEST PART, STATED UP FRONT
--------------------------------------------------------------------------------------------------
These connectors are **SIMULATED**. They make no network calls. Nothing here is a real integration.

The vendor payload shapes below are **representative, not authoritative** — they are written to be
realistic in structure and naming convention (SAP's terse uppercase fields, Maximo's `wonum`,
Enablon's camelCase REST) so that the *normalisation problem* can be demonstrated honestly. They are
NOT documented API schemas, and the real field mapping for any given client is discovery work.

What a real integration actually needs, and what this does not have:
  - Authentication (OAuth2 / SAML / API keys, per vendor, per tenant)
  - The vendor's actual, versioned API surface and field semantics
  - Rate limits, pagination, retry and idempotency
  - Write-back PERMISSIONS — the ability to post a finding onto a live permit is a privileged
    operation and will be the hardest thing to get signed off, not the easiest
  - Field-level mapping validated by the client's own control-of-work SME

Pretending otherwise would be exactly the overclaim this product exists to prevent.
--------------------------------------------------------------------------------------------------

WHY THE NORMALISATION LAYER IS THE REAL WORK
Every system of record names the same thing differently. A permit's work description is
`workOrderDescription` in one, `LTXT` in another, `description` in a third. The agents must never
see any of that. They see ONE canonical permit shape, and the connector is what earns that.

Add a new system of record => write one adapter. The agents do not change.
"""

from dataclasses import dataclass, field
from typing import Callable

from data.permits import PERMITS


# ==================================================================================================
# The canonical permit shape the agents consume. Every connector must produce exactly this.
# ==================================================================================================

CANONICAL_FIELDS = [
    "permit_id", "title", "unit", "requested_by", "shift", "status",
    "work_description", "hazards_identified", "controls_listed", "hold_points_listed",
    "isolation_plan", "jsa_summary", "personnel", "unit_state", "concurrent_permits",
]


@dataclass
class Connector:
    """A simulated system-of-record adapter."""
    key: str
    vendor: str
    product: str
    api_style: str
    auth: str
    endpoint: str
    market_note: str
    # canonical -> vendor-native payload (so we can SHOW what the source system really returns)
    to_native: Callable[[dict], dict]
    # vendor-native payload -> canonical (the mapping that is the actual integration work)
    from_native: Callable[[dict], dict]
    # what a write-back of findings would look like against this system
    writeback_shape: Callable[[str, list, str], dict]
    field_map: dict = field(default_factory=dict)

    # ---- simulated transport ----------------------------------------------------------------

    def list_permits(self) -> list[dict]:
        """Simulated: GET the permits awaiting authorisation."""
        return [self.to_native(p) for p in PERMITS]

    def fetch_permit(self, permit_id: str) -> dict | None:
        """Simulated: GET one permit, in the source system's own payload shape."""
        for p in PERMITS:
            if p["permit_id"] == permit_id:
                return self.to_native(p)
        return None

    def fetch_canonical(self, permit_id: str) -> dict | None:
        """Fetch, then normalise. This is what HOLDPOINT actually consumes."""
        native = self.fetch_permit(permit_id)
        if native is None:
            return None
        return self.from_native(native)

    def write_back(self, permit_id: str, findings: list, recommendation: str) -> dict:
        """Simulated: POST findings and hold points back onto the permit in the source system.

        In production this is the privileged operation and the hardest to get approved. A system
        that can annotate — or block — a live permit is touching a safety-critical record.
        """
        payload = self.writeback_shape(permit_id, findings, recommendation)
        return {
            "simulated": True,
            "request": {"method": "POST", "url": f"{self.endpoint}/permits/{permit_id}/findings",
                        "auth": self.auth, "body": payload},
            "response": {"status": 201, "body": {
                "accepted": True,
                "permit_id": permit_id,
                "findings_written": len(findings),
                "permit_status_set_to": (
                    "HELD — HOLDPOINT findings require closeout" if recommendation != "AUTHORISE"
                    else "READY FOR AUTHORISATION"
                ),
                "note": "SIMULATED. No network call was made.",
            }},
        }


# ==================================================================================================
# Adapters
# ==================================================================================================

def _person_names(p: dict) -> str:
    return "; ".join(f"{x['name']} ({x['company']})" for x in p.get("personnel", []))


# --- 1. Enablon (Wolters Kluwer) — Control of Work ------------------------------------------------
# The incumbent that matters. Its AI "Permit Advisor" assists the AUTHOR (checks description quality,
# recommends hazards). HOLDPOINT reads the finished permit OUT of it and attacks it. Different job.

def _enablon_to_native(p: dict) -> dict:
    return {
        "permitNumber": p["permit_id"],
        "permitTitle": p["title"],
        "locationHierarchy": {"site": "Gulf Coast Refinery", "unit": p["unit"]},
        "requestor": {"displayName": p["requested_by"]},
        "validityWindow": {"shift": p["shift"]},
        "permitStatus": p["status"],
        "workOrderDescription": p["work_description"],
        "hazardAssessment": {
            "identifiedHazards": [{"hazardName": h} for h in p.get("hazards_identified", [])],
            "appliedControls": [{"controlName": c} for c in p.get("controls_listed", [])],
        },
        "holdPoints": [{"description": h} for h in (p.get("hold_points_listed") or [])],
        "isolationCertificate": {"narrative": p.get("isolation_plan", "")},
        "jobSafetyAnalysis": {"summary": p.get("jsa_summary", "")},
        "assignedResources": [
            {"fullName": x["name"], "contractorOrg": x["company"], "roleOnPermit": x["role"],
             "inductionStatus": x.get("site_induction"),
             "competencyRecords": x.get("competencies", []),
             "h2sCertification": x.get("h2s_competency"),
             "confinedSpaceCertification": x.get("confined_space_competency")}
            for x in p.get("personnel", [])
        ],
        "assetOperatingState": p.get("unit_state", ""),
        "concurrentPermits": [
            {"permitNumber": c["permit_id"], "summary": c["description"],
             "permitStatus": c["status"], "unit": c["unit"]}
            for c in p.get("concurrent_permits", [])
        ],
    }


def _enablon_from_native(n: dict) -> dict:
    return {
        "permit_id": n["permitNumber"],
        "title": n["permitTitle"],
        "unit": n["locationHierarchy"]["unit"],
        "requested_by": n["requestor"]["displayName"],
        "shift": n["validityWindow"]["shift"],
        "status": n["permitStatus"],
        "work_description": n["workOrderDescription"],
        "hazards_identified": [h["hazardName"] for h in n["hazardAssessment"]["identifiedHazards"]],
        "controls_listed": [c["controlName"] for c in n["hazardAssessment"]["appliedControls"]],
        "hold_points_listed": [h["description"] for h in n.get("holdPoints", [])],
        "isolation_plan": n["isolationCertificate"]["narrative"],
        "jsa_summary": n["jobSafetyAnalysis"]["summary"],
        "personnel": [
            {"name": r["fullName"], "company": r["contractorOrg"], "role": r["roleOnPermit"],
             "site_induction": r.get("inductionStatus"),
             "competencies": r.get("competencyRecords", []),
             "h2s_competency": r.get("h2sCertification"),
             **({"confined_space_competency": r["confinedSpaceCertification"]}
                if r.get("confinedSpaceCertification") else {})}
            for r in n.get("assignedResources", [])
        ],
        "unit_state": n.get("assetOperatingState", ""),
        "concurrent_permits": [
            {"permit_id": c["permitNumber"], "description": c["summary"],
             "status": c["permitStatus"], "unit": c["unit"]}
            for c in n.get("concurrentPermits", [])
        ],
    }


def _enablon_writeback(pid: str, findings: list, rec: str) -> dict:
    return {
        "permitNumber": pid,
        "reviewSource": "HOLDPOINT",
        "reviewOutcome": rec,
        "findings": [
            {"findingType": f.get("_group", "finding"),
             "severity": f.get("severity", "medium"),
             "description": f.get("required_hold_point") or f.get("issue")
                            or f.get("hazard") or f.get("conflict") or "finding",
             "sourceReference": f.get("citation_document") or "unverified",
             "citationVerified": bool(f.get("citation_verified"))}
            for f in findings
        ],
        "requiresCloseoutBeforeAuthorisation": rec != "AUTHORISE",
    }


ENABLON = Connector(
    key="enablon",
    vendor="Wolters Kluwer",
    product="Enablon — Control of Work",
    api_style="REST / JSON (camelCase)",
    auth="OAuth 2.0 client credentials",
    endpoint="https://api.enablon.example/cow/v2",
    market_note=(
        "The incumbent that matters. Ships an AI 'Permit Advisor' that checks description quality and "
        "recommends hazards — a DRAFTING aid for the author. HOLDPOINT reads the finished permit out "
        "of it and attacks it. Substrate, not enemy."
    ),
    to_native=_enablon_to_native,
    from_native=_enablon_from_native,
    writeback_shape=_enablon_writeback,
    field_map={
        "permit_id": "permitNumber",
        "work_description": "workOrderDescription",
        "hazards_identified": "hazardAssessment.identifiedHazards[].hazardName",
        "controls_listed": "hazardAssessment.appliedControls[].controlName",
        "hold_points_listed": "holdPoints[].description",
        "isolation_plan": "isolationCertificate.narrative",
        "personnel": "assignedResources[]",
        "unit_state": "assetOperatingState",
    },
)


# --- 2. SAP EHS + Work Clearance Management -------------------------------------------------------

def _sap_to_native(p: dict) -> dict:
    return {
        "WCMKEY": p["permit_id"],
        "KTEXT": p["title"],
        "TPLNR": p["unit"],                       # functional location
        "ERNAM": p["requested_by"],               # created by
        "SCHICHT": p["shift"],
        "STATUS": p["status"],
        "LTXT": p["work_description"],            # long text
        "GEFAEHRDUNG": [{"TXT": h} for h in p.get("hazards_identified", [])],
        "MASSNAHME": [{"TXT": c} for c in p.get("controls_listed", [])],
        "HALTEPUNKT": [{"TXT": h} for h in (p.get("hold_points_listed") or [])],
        "WCM_LOTO": p.get("isolation_plan", ""),
        "JSA_TXT": p.get("jsa_summary", ""),
        "PERSONAL": [
            {"NACHN": x["name"], "LIFNR": x["company"], "STELL": x["role"],
             "QUALIF": x.get("competencies", []),
             "ZZ_H2S": x.get("h2s_competency"),
             "ZZ_CSE": x.get("confined_space_competency"),
             "ZZ_INDUCT": x.get("site_induction")}
            for x in p.get("personnel", [])
        ],
        "ANLAGENSTATUS": p.get("unit_state", ""),
        "PARALLEL_WCM": [
            {"WCMKEY": c["permit_id"], "KTEXT": c["description"],
             "STATUS": c["status"], "TPLNR": c["unit"]}
            for c in p.get("concurrent_permits", [])
        ],
    }


def _sap_from_native(n: dict) -> dict:
    return {
        "permit_id": n["WCMKEY"],
        "title": n["KTEXT"],
        "unit": n["TPLNR"],
        "requested_by": n["ERNAM"],
        "shift": n["SCHICHT"],
        "status": n["STATUS"],
        "work_description": n["LTXT"],
        "hazards_identified": [h["TXT"] for h in n.get("GEFAEHRDUNG", [])],
        "controls_listed": [c["TXT"] for c in n.get("MASSNAHME", [])],
        "hold_points_listed": [h["TXT"] for h in n.get("HALTEPUNKT", [])],
        "isolation_plan": n.get("WCM_LOTO", ""),
        "jsa_summary": n.get("JSA_TXT", ""),
        "personnel": [
            {"name": r["NACHN"], "company": r["LIFNR"], "role": r["STELL"],
             "site_induction": r.get("ZZ_INDUCT"),
             "competencies": r.get("QUALIF", []),
             "h2s_competency": r.get("ZZ_H2S"),
             **({"confined_space_competency": r["ZZ_CSE"]} if r.get("ZZ_CSE") else {})}
            for r in n.get("PERSONAL", [])
        ],
        "unit_state": n.get("ANLAGENSTATUS", ""),
        "concurrent_permits": [
            {"permit_id": c["WCMKEY"], "description": c["KTEXT"],
             "status": c["STATUS"], "unit": c["TPLNR"]}
            for c in n.get("PARALLEL_WCM", [])
        ],
    }


def _sap_writeback(pid: str, findings: list, rec: str) -> dict:
    return {
        "WCMKEY": pid,
        "ZZ_HOLDPOINT_RESULT": rec,
        "ZZ_FINDINGS": [
            {"TYP": f.get("_group", "FINDING"),
             "PRIO": f.get("severity", "medium").upper(),
             "TXT": (f.get("required_hold_point") or f.get("issue") or f.get("hazard")
                     or f.get("conflict") or "finding")[:255],
             "QUELLE": f.get("citation_document") or "UNVERIFIED"}
            for f in findings
        ],
        "SPERRE": "X" if rec != "AUTHORISE" else "",   # block flag
    }


SAP_WCM = Connector(
    key="sap_wcm",
    vendor="SAP",
    product="SAP EHS + Work Clearance Management (WCM)",
    api_style="OData v4 / RFC (terse uppercase German-rooted field names)",
    auth="SAML / Principal propagation",
    endpoint="https://sap.example/sap/opu/odata4/wcm",
    market_note=(
        "Where the permit often actually lives at large operators, because it is bolted to the "
        "maintenance order. The hardest integration and the stickiest — which is exactly why it is "
        "worth having."
    ),
    to_native=_sap_to_native,
    from_native=_sap_from_native,
    writeback_shape=_sap_writeback,
    field_map={
        "permit_id": "WCMKEY",
        "title": "KTEXT",
        "unit": "TPLNR (functional location)",
        "work_description": "LTXT (long text)",
        "hazards_identified": "GEFAEHRDUNG[].TXT",
        "controls_listed": "MASSNAHME[].TXT",
        "hold_points_listed": "HALTEPUNKT[].TXT",
        "isolation_plan": "WCM_LOTO",
        "personnel": "PERSONAL[]",
    },
)


# --- 3. IBM Maximo --------------------------------------------------------------------------------

def _maximo_to_native(p: dict) -> dict:
    return {
        "wonum": p["permit_id"],
        "description": p["title"],
        "location": p["unit"],
        "reportedby": p["requested_by"],
        "shift": p["shift"],
        "status": p["status"],
        "description_longdescription": p["work_description"],
        "hazard": [{"hazardid": h} for h in p.get("hazards_identified", [])],
        "precaution": [{"precautionid": c} for c in p.get("controls_listed", [])],
        "wosafetyplan": {"holdpoint": [{"description": h}
                                       for h in (p.get("hold_points_listed") or [])]},
        "loto": {"lotodescription": p.get("isolation_plan", "")},
        "jsa": {"jsadescription": p.get("jsa_summary", "")},
        "labtrans": [
            {"laborcode": x["name"], "vendor": x["company"], "craft": x["role"],
             "certification": x.get("competencies", []),
             "h2s_cert": x.get("h2s_competency"),
             "cse_cert": x.get("confined_space_competency"),
             "induction": x.get("site_induction")}
            for x in p.get("personnel", [])
        ],
        "assetstatus": p.get("unit_state", ""),
        "relatedwo": [
            {"wonum": c["permit_id"], "description": c["description"],
             "status": c["status"], "location": c["unit"]}
            for c in p.get("concurrent_permits", [])
        ],
    }


def _maximo_from_native(n: dict) -> dict:
    return {
        "permit_id": n["wonum"],
        "title": n["description"],
        "unit": n["location"],
        "requested_by": n["reportedby"],
        "shift": n["shift"],
        "status": n["status"],
        "work_description": n["description_longdescription"],
        "hazards_identified": [h["hazardid"] for h in n.get("hazard", [])],
        "controls_listed": [c["precautionid"] for c in n.get("precaution", [])],
        "hold_points_listed": [h["description"]
                               for h in n.get("wosafetyplan", {}).get("holdpoint", [])],
        "isolation_plan": n.get("loto", {}).get("lotodescription", ""),
        "jsa_summary": n.get("jsa", {}).get("jsadescription", ""),
        "personnel": [
            {"name": r["laborcode"], "company": r["vendor"], "role": r["craft"],
             "site_induction": r.get("induction"),
             "competencies": r.get("certification", []),
             "h2s_competency": r.get("h2s_cert"),
             **({"confined_space_competency": r["cse_cert"]} if r.get("cse_cert") else {})}
            for r in n.get("labtrans", [])
        ],
        "unit_state": n.get("assetstatus", ""),
        "concurrent_permits": [
            {"permit_id": c["wonum"], "description": c["description"],
             "status": c["status"], "unit": c["location"]}
            for c in n.get("relatedwo", [])
        ],
    }


def _maximo_writeback(pid: str, findings: list, rec: str) -> dict:
    return {
        "wonum": pid,
        "holdpoint_review": rec,
        "worklog": [
            {"logtype": "HOLDPOINT",
             "summary": f"{f.get('severity', 'medium').upper()}: "
                        f"{(f.get('required_hold_point') or f.get('issue') or f.get('hazard') or f.get('conflict') or 'finding')[:120]}",
             "reference": f.get("citation_document") or "UNVERIFIED"}
            for f in findings
        ],
        "status": "WAPPR" if rec != "AUTHORISE" else "APPR",
    }


MAXIMO = Connector(
    key="maximo",
    vendor="IBM",
    product="IBM Maximo — Safety Plans / Permits",
    api_style="Maximo REST (OSLC) / JSON (lowercase)",
    auth="API key / MAXAUTH",
    endpoint="https://maximo.example/maximo/oslc/os/mxwo",
    market_note="Common where the permit is an extension of the work order in the EAM.",
    to_native=_maximo_to_native,
    from_native=_maximo_from_native,
    writeback_shape=_maximo_writeback,
    field_map={
        "permit_id": "wonum",
        "title": "description",
        "work_description": "description_longdescription",
        "hazards_identified": "hazard[].hazardid",
        "controls_listed": "precaution[].precautionid",
        "hold_points_listed": "wosafetyplan.holdpoint[].description",
        "isolation_plan": "loto.lotodescription",
        "personnel": "labtrans[]",
    },
)


# --- 4. Local fixtures (no source system) ---------------------------------------------------------

LOCAL = Connector(
    key="local",
    vendor="—",
    product="Local fixtures (no system of record)",
    api_style="in-process",
    auth="none",
    endpoint="file://data/permits.py",
    market_note="Greenfield / demo mode. HOLDPOINT reads permits directly with no upstream system.",
    to_native=lambda p: dict(p),
    from_native=lambda n: {k: v for k, v in n.items() if k in CANONICAL_FIELDS},
    writeback_shape=lambda pid, findings, rec: {
        "permit_id": pid, "recommendation": rec, "findings": len(findings),
        "note": "No system of record configured — findings held in HOLDPOINT only.",
    },
    field_map={f: f for f in CANONICAL_FIELDS},
)


CONNECTORS = {c.key: c for c in (LOCAL, ENABLON, SAP_WCM, MAXIMO)}
CONNECTOR_LABELS = {k: c.product for k, c in CONNECTORS.items()}

DEFAULT_CONNECTOR = "local"


def get_connector(key: str | None = None) -> Connector:
    return CONNECTORS.get(key or DEFAULT_CONNECTOR, CONNECTORS[DEFAULT_CONNECTOR])


def roundtrip_check(connector: Connector, permit_id: str) -> dict:
    """Prove the mapping is lossless: canonical -> vendor-native -> canonical must round-trip.

    This is not decoration. A silently lossy field map in a safety system means the agents review a
    permit that is missing a hazard, a person, or a concurrent permit — and confidently declare it
    safe. A dropped field is a defect that LOOKS like a clean review.
    """
    original = next((p for p in PERMITS if p["permit_id"] == permit_id), None)
    if original is None:
        return {"ok": False, "error": f"unknown permit {permit_id}"}

    native = connector.to_native(original)
    back = connector.from_native(native)

    lost, changed = [], []
    for f in CANONICAL_FIELDS:
        if f not in back:
            lost.append(f)
        elif back[f] != original.get(f):
            changed.append(f)

    return {
        "ok": not lost and not changed,
        "connector": connector.product,
        "fields_checked": len(CANONICAL_FIELDS),
        "fields_lost": lost,
        "fields_changed": changed,
        "native_payload": native,
        "canonical_payload": back,
    }
