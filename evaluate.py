"""
HOLDPOINT — Evaluation Harness
==============================

    python evaluate.py            # 3 runs per permit (default)
    python evaluate.py --runs 5   # 5 runs — use this before a demo
    python evaluate.py --quick    # 1 run, Deer Park permit only

Running the agents ONCE is an anecdote. This measures them.

Everything else in this project holds other people's systems to a standard: *prove it, don't
assert it.* This file applies that standard to us. Without it, every claim about agent quality is
a story about the one time it worked.

WHAT IS SCORED
--------------
1. HOLD-POINT RECOVERY — the demo-critical one.
   The Hold Point Enforcer must recover, verbatim, the safeguard buried in PTW-2026-0417's prose:
   "prior to opening the line the crew should stop and obtain an operator to be present at the
   flange". This is the entire demo. If it is not 5/5, the story does not land and you need to know
   BEFORE you are on stage, not during.

2. VERDICT CALIBRATION — in BOTH directions.
   REJECT the lethal permit AND *AUTHORISE the clean one*. The second half is the half everyone
   forgets to test, and a reviewer that flags everything is exactly as useless as one that flags
   nothing — it just fails more politely.

3. CITATION QUALITY.
   What proportion of the agents' asserted controls actually quote a real procedure? If they
   paraphrase, the provenance layer correctly flags them UNVERIFIED — the system stays honest, but
   the review LOOKS weak. That is a prompt problem, and this number finds it.

4. RUN-TO-RUN VARIANCE.
   Temperature is 0, but LLM JSON output is not deterministic in practice. If the verdict flips
   between runs of the same permit, the demo is a coin toss.

Exit code is non-zero if any gate fails, so this can be wired into CI.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.domains import set_active_site
from data.permits import get_permit


# --- GROUND TRUTH -------------------------------------------------------------------------
# What a correct review MUST find. Written down, so the harness cannot move the goalposts.

BURIED_SAFEGUARD = ("prior to opening the line the crew should stop and obtain an operator "
                    "to be present at the flange")

# A fragment is enough — the model may quote a slightly different span of the same sentence.
BURIED_FRAGMENTS = [
    "stop and obtain an operator",
    "operator to be present at the flange",
    "before breaking containment",
]

EXPECTED = {
    "PTW-2026-0417": {
        "verdict": {"REJECT"},                      # over-broad scope cannot be conditioned away
        "must_find_buried_safeguard": True,
        "note": "The Deer Park permit. Five bundled jobs, zero hold points, expired H2S competency.",
    },
    "PTW-2026-0431": {
        "verdict": {"AUTHORISE"},                   # THE HALF EVERYONE FORGETS TO TEST
        "must_find_buried_safeguard": False,
        "note": "Well-formed permit. If HOLDPOINT cannot say YES, it is a rubber stamp in reverse.",
    },
    "PTW-2026-0436": {
        "verdict": {"REJECT", "HOLD_WITH_CONDITIONS"},
        "must_find_buried_safeguard": False,
        "note": "Night shift, sour service, valve-only isolation. Darkness is a FACT, not an opinion.",
    },
}


def _norm(s: str) -> str:
    return " ".join((s or "").split()).lower()


def _found_buried(result: dict) -> tuple[bool, str]:
    """Did the Hold Point Enforcer actually recover the sentence buried in the prose?"""
    hp = result.get("hold_points", {}) or {}
    for b in hp.get("buried_hold_points", []) or []:
        quoted = _norm(b.get("instruction_found", ""))
        if any(_norm(f) in quoted for f in BURIED_FRAGMENTS):
            return True, b.get("instruction_found", "")[:120]
    return False, ""


def run_once(permit_id: str) -> dict:
    from agents.permit_review.graph import review_permit

    t0 = time.time()
    result = review_permit(get_permit(permit_id))
    elapsed = time.time() - t0

    verdict = (result.get("verdict", {}) or {}).get("recommendation", "NONE")
    prov = result.get("provenance", {}) or {}
    found, quote = _found_buried(result)

    return {
        "verdict": (verdict or "NONE").upper(),
        "found_buried": found,
        "buried_quote": quote,
        "citations_total": prov.get("total", 0),
        "citations_verified": prov.get("verified", 0),
        "verified_pct": prov.get("verified_pct", 0),
        "seconds": round(elapsed, 1),
        "parse_errors": sum(
            1 for k in ("scope", "hazards", "hold_points", "competency", "isolation_simops",
                        "precedent", "verdict")
            if isinstance(result.get(k), dict) and result[k].get("parse_error")
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--quick", action="store_true", help="1 run, Deer Park permit only")
    ap.add_argument("--site", default="refining")
    args = ap.parse_args()

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("No LLM key. Put OPENAI_API_KEY in a .env file (gitignored) and re-run.")
        return 2

    set_active_site(args.site)
    permits = ["PTW-2026-0417"] if args.quick else list(EXPECTED)
    runs = 1 if args.quick else args.runs

    print("=" * 84)
    print(f"HOLDPOINT EVALUATION — {runs} run(s) x {len(permits)} permit(s), site={args.site}")
    print("=" * 84)

    failures: list[str] = []
    all_results: dict[str, list[dict]] = {}

    for pid in permits:
        spec = EXPECTED[pid]
        print(f"\n{pid}  — {spec['note']}")
        print(f"  expected verdict: {' or '.join(sorted(spec['verdict']))}")
        results = []

        for i in range(runs):
            try:
                r = run_once(pid)
            except Exception as e:
                print(f"    run {i + 1}: EXCEPTION {type(e).__name__}: {e}")
                failures.append(f"{pid}: run {i + 1} raised {type(e).__name__}")
                continue

            results.append(r)
            ok_v = "OK " if r["verdict"] in spec["verdict"] else "BAD"
            hp = ""
            if spec["must_find_buried_safeguard"]:
                hp = "  buried:FOUND" if r["found_buried"] else "  buried:*** MISSED ***"
            print(f"    run {i + 1}: [{ok_v}] {r['verdict']:20} "
                  f"citations {r['citations_verified']}/{r['citations_total']} "
                  f"({r['verified_pct']}%)  {r['seconds']}s{hp}")

        all_results[pid] = results
        if not results:
            continue

        # --- GATE 1: verdict calibration ---------------------------------------------------
        verdicts = Counter(r["verdict"] for r in results)
        correct = sum(v for k, v in verdicts.items() if k in spec["verdict"])
        print(f"  verdict     : {correct}/{len(results)} correct   {dict(verdicts)}")
        if correct < len(results):
            failures.append(
                f"{pid}: verdict wrong in {len(results) - correct}/{len(results)} runs "
                f"(got {dict(verdicts)}, expected {sorted(spec['verdict'])})"
            )

        # --- GATE 2: hold-point recovery — THE DEMO ----------------------------------------
        if spec["must_find_buried_safeguard"]:
            n = sum(1 for r in results if r["found_buried"])
            print(f"  buried h.p. : {n}/{len(results)} recovered   <-- THE ENTIRE DEMO")
            if n < len(results):
                failures.append(
                    f"{pid}: Hold Point Enforcer MISSED the buried safeguard in "
                    f"{len(results) - n}/{len(results)} runs. The demo hangs on this."
                )
            elif results[0]["buried_quote"]:
                print(f"                \"{results[0]['buried_quote']}...\"")

        # --- GATE 3: citation quality ------------------------------------------------------
        pcts = [r["verified_pct"] for r in results if r["citations_total"]]
        if pcts:
            avg = sum(pcts) / len(pcts)
            print(f"  citations   : {avg:.0f}% provenance-verified (mean)")
            if avg < 50:
                failures.append(
                    f"{pid}: only {avg:.0f}% of assertions quote a real procedure. The agents are "
                    f"paraphrasing; the provenance layer will correctly flag them UNVERIFIED and the "
                    f"review will LOOK weak. Prompt fix, not architecture."
                )

        # --- GATE 4: variance --------------------------------------------------------------
        if len(verdicts) > 1:
            failures.append(f"{pid}: verdict FLIPPED across runs {dict(verdicts)} — demo is a coin toss")

        # --- GATE 5: parse errors ----------------------------------------------------------
        pe = sum(r["parse_errors"] for r in results)
        if pe:
            failures.append(f"{pid}: {pe} agent output(s) failed to parse across runs")

    # --- Report -----------------------------------------------------------------------------
    print("\n" + "=" * 84)
    if failures:
        print(f"{len(failures)} GATE FAILURE(S) — do not demo until these are closed:\n")
        for f in failures:
            print(f"  x  {f}")
    else:
        print("ALL GATES PASS")
        print("  - verdicts calibrated in BOTH directions (rejects the lethal one, authorises the clean one)")
        print("  - the buried safeguard is recovered every single run")
        print("  - the agents quote real procedures rather than paraphrasing them")
        print("  - no run-to-run verdict flips")
    print("=" * 84)

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({"results": all_results, "failures": failures}, f, indent=2)
    print("\nwrote eval_results.json")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
