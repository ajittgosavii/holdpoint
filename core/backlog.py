"""
HOLDPOINT — Backlog Structural Scan
===================================

The metric that decides whether this product has a business case.

Run HOLDPOINT over a client's HISTORICAL permits — permits that were authorised, worked, and
closed without incident — and count how many carried a Deer-Park-shaped structural defect.

Every one of those is an incident that did not happen by luck.

If the count is ZERO, the product has no case and we should say so and walk away. That is the
point of a test that can fail.

This scan is DETERMINISTIC and rules-based on purpose. It is a cheap pre-screen over thousands of
permits — not the agent review. It is stated as a heuristic, never dressed up as the deep
reasoning the agents do, because a heuristic that claims to be an AI review is just a lie with a
progress bar.
"""

import re

# Language that signals a safeguard requiring work to STOP and something to be verified.
# These are the sentences that get read past.
STOP_WORK_PATTERNS = [
    r"\bstop\b.{0,40}\bbefore\b",
    r"\bprior to\b.{0,60}\b(obtain|ensure|confirm|verify|check)\b",
    r"\bbefore\b.{0,60}\b(breaking containment|opening|entry|energis|energiz)",
    r"\bmust be (confirmed|verified|proven|checked|present)\b",
    r"\b(obtain|ensure)\b.{0,40}\b(operator|authority|supervisor)\b.{0,40}\bpresent\b",
    r"\bdo not proceed\b",
    r"\bshall not (commence|proceed|start)\b",
]

# Toxic / flammable service — raises the consequence of every other defect.
HIGH_HAZARD_TERMS = [
    "h2s", "hydrogen sulphide", "hydrogen sulfide", "sour", "amine",
    "hydrocarbon", "flammable", "toxic", "cyanide", "hydrofluoric",
    "energised", "energized", "live conductor",
]

DEFECTS = {
    "over_broad_scope": "Over-broad scope — one permit authorising multiple jobs of differing hazard",
    "buried_stop_work": "Stop-work instruction present in prose but NOT enforced as a hold point",
    "no_hold_points": "No hold points listed on the face of the permit",
    "competency_gap": "A named person lacks a current competency for a hazard they face",
    "simops_conflict": "Concurrent permit on the same unit creating a credible conflict",
    "weak_isolation": "Valve-only isolation on a toxic or high-hazard service",
    "multi_company_party": "Work party spans multiple contracting companies under one permit",
}


def _text_of(permit: dict) -> str:
    return " ".join([
        permit.get("work_description", ""),
        permit.get("jsa_summary", ""),
        permit.get("isolation_plan", ""),
    ]).lower()


def _is_high_hazard(permit: dict) -> bool:
    blob = (_text_of(permit) + " " + permit.get("unit_state", "")).lower()
    return any(t in blob for t in HIGH_HAZARD_TERMS)


def _count_tasks(description: str) -> int:
    """Count enumerated tasks. A permit listing (1)…(2)…(3) is authorising several jobs."""
    numbered = re.findall(r"\(\d\)|\b\d\)\s|\b\d\.\s+[A-Z]", description)
    return len(numbered)


def find_buried_stop_work(permit: dict) -> list[str]:
    """Return the actual sentences containing an unenforced stop-work instruction."""
    hits = []
    for field in ("work_description", "jsa_summary", "isolation_plan"):
        text = permit.get(field, "") or ""
        for sentence in re.split(r"(?<=[.;])\s+", text):
            s = sentence.strip()
            if not s:
                continue
            low = s.lower()
            if any(re.search(p, low) for p in STOP_WORK_PATTERNS):
                hits.append(s)
    return hits


def scan_permit(permit: dict) -> dict:
    """Structural defect scan of a single permit. Deterministic — no LLM."""
    defects: list[dict] = []
    high_hazard = _is_high_hazard(permit)

    # 1. Over-broad scope
    task_count = _count_tasks(permit.get("work_description", ""))
    if task_count >= 2:
        defects.append({
            "code": "over_broad_scope",
            "detail": f"{task_count} distinct tasks enumerated in a single permit.",
            "severity": "critical" if high_hazard else "high",
        })

    # 2 & 3. Hold points
    listed_holds = permit.get("hold_points_listed") or []
    buried = find_buried_stop_work(permit)
    if buried and not listed_holds:
        defects.append({
            "code": "buried_stop_work",
            "detail": f"{len(buried)} stop-work instruction(s) found in prose with NO hold points "
                      f"listed on the permit. First: \"{buried[0][:160]}\"",
            "severity": "critical",
            "evidence": buried,
        })
    elif buried and len(buried) > len(listed_holds):
        defects.append({
            "code": "buried_stop_work",
            "detail": f"{len(buried)} stop-work instruction(s) in prose but only "
                      f"{len(listed_holds)} hold point(s) enforced.",
            "severity": "high",
            "evidence": buried,
        })
    if not listed_holds and high_hazard:
        defects.append({
            "code": "no_hold_points",
            "detail": "No hold points on a permit involving a high-hazard service.",
            "severity": "critical",
        })

    # 4. Competency
    for person in permit.get("personnel", []) or []:
        for key, label in (("h2s_competency", "H2S"), ("confined_space_competency", "Confined space")):
            val = str(person.get(key, "")).lower()
            if not val or val in ("not recorded",):
                continue
            if "expired" in val or "none" in val:
                defects.append({
                    "code": "competency_gap",
                    "detail": f"{person['name']} ({person['company']}): {label} competency "
                              f"{person.get(key)}.",
                    "severity": "critical" if high_hazard else "high",
                })

    # 5. SIMOPS
    for c in permit.get("concurrent_permits", []) or []:
        desc = (c.get("description", "") + " " + permit.get("work_description", "")).lower()
        hot = "hot work" in desc or "weld" in desc or "grind" in desc
        breach = "line break" in desc or "containment" in desc or "drain" in desc or "open" in desc
        if hot and breach:
            defects.append({
                "code": "simops_conflict",
                "detail": f"Concurrent permit {c['permit_id']} ({c['status']}): {c['description']}",
                "severity": "critical",
            })

    # 6. Isolation adequacy
    iso = (permit.get("isolation_plan", "") or "").lower()
    if high_hazard and ("no spade" in iso or "valve isolation only" in iso
                        or ("spade" not in iso and "blind" not in iso and "block valve" in iso)):
        defects.append({
            "code": "weak_isolation",
            "detail": "Valve isolation only — no spade or blind — on a high-hazard service.",
            "severity": "critical",
        })

    # 7. Multiple companies under one permit
    companies = {p.get("company") for p in permit.get("personnel", []) or []}
    companies.discard("In-house")
    if len(companies) > 1:
        defects.append({
            "code": "multi_company_party",
            "detail": f"Work party spans {len(companies)} contracting companies: "
                      f"{', '.join(sorted(companies))}.",
            "severity": "high",
        })

    worst = "none"
    for level in ("critical", "high", "medium", "low"):
        if any(d["severity"] == level for d in defects):
            worst = level
            break

    # The Deer Park signature: an over-broad scope carrying a stop-work instruction that nothing
    # enforces. That precise combination is what the CSB described.
    codes = {d["code"] for d in defects}
    deer_park_shape = "over_broad_scope" in codes and (
        "buried_stop_work" in codes or "no_hold_points" in codes
    )

    return {
        "permit_id": permit["permit_id"],
        "title": permit["title"],
        "unit": permit["unit"],
        "high_hazard": high_hazard,
        "defects": defects,
        "defect_count": len(defects),
        "worst_severity": worst,
        "deer_park_shape": deer_park_shape,
        "clean": not defects,
    }


def scan_backlog(permits: list[dict]) -> dict:
    """Scan a whole backlog. This produces the number that makes or breaks the business case."""
    results = [scan_permit(p) for p in permits]
    total = len(results)
    deer_park = [r for r in results if r["deer_park_shape"]]
    critical = [r for r in results if r["worst_severity"] == "critical"]
    clean = [r for r in results if r["clean"]]

    by_defect: dict[str, int] = {}
    for r in results:
        for d in r["defects"]:
            by_defect[d["code"]] = by_defect.get(d["code"], 0) + 1

    return {
        "results": results,
        "total": total,
        "clean_count": len(clean),
        "critical_count": len(critical),
        "deer_park_count": len(deer_park),
        "deer_park_pct": round(100 * len(deer_park) / total) if total else 0,
        "by_defect": by_defect,
        "headline": (
            f"{len(deer_park)} of {total} permits carry the Deer Park structural signature: an "
            f"over-broad scope with a safeguard that nothing enforces."
        ) if deer_park else (
            f"None of {total} permits carry the Deer Park signature. On this sample, the product "
            f"has no case — and we would tell you so."
        ),
    }
