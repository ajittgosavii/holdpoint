"""
HOLDPOINT — Provenance Verification
===================================

The single most important module in this system.

An AI that confidently invents a safety control is worse than no AI at all. If HOLDPOINT
tells an authoriser "the procedure requires an operator to be present before the line is
opened" and no procedure says any such thing, we have manufactured a false assurance in a
system whose entire purpose is to prevent false assurance.

So every control, hazard and requirement the agents assert MUST be accompanied by a verbatim
quote from a real source document — and this module PROGRAMMATICALLY CHECKS that the quote
actually appears in that document. This is a code check, not a prompt instruction. The model
cannot talk its way past it.

An assertion whose quote cannot be located in the source corpus is not silently dropped and
not silently trusted. It is surfaced to the human as UNVERIFIED, with its confidence
downgraded, so a person decides what to do about it.

This is also the vendor's own indemnity, not just the client's assurance.
"""

import re
from dataclasses import dataclass


# Minimum length below which a "quote" is too generic to be meaningful evidence.
MIN_QUOTE_CHARS = 15
# When a model elides mid-quote ("... shall be ..."), accept a substantial leading span.
ELISION_HEAD_CHARS = 60
MIN_ELISION_HEAD = 40


def normalize(text: str) -> str:
    """Collapse whitespace and case so a quote matches text that was wrapped or re-indented."""
    return " ".join((text or "").split()).lower()


def _strip_quote_marks(text: str) -> str:
    return (text or "").strip().strip('"').strip("'").strip("“”").strip()


@dataclass
class Citation:
    """The result of checking one asserted quote against the source corpus."""
    quote: str
    verified: bool
    document_id: str | None
    document_title: str | None
    reason: str

    @property
    def badge(self) -> str:
        if self.verified:
            return "VERIFIED"
        return "UNVERIFIED"


def verify_quote(quote: str, corpus: list[dict]) -> Citation:
    """Check whether `quote` genuinely appears in any document in `corpus`.

    corpus: list of {doc_id, title, text} — the site's actual procedures, permits and standards.

    Returns a Citation. verified=False means the model produced a quote we could NOT find in
    any source document — i.e. it paraphrased, or it made it up. Either way a human must look.
    """
    q = normalize(_strip_quote_marks(quote))

    if not q:
        return Citation(quote, False, None, None, "No quote supplied — assertion is unsupported.")
    if len(q) < MIN_QUOTE_CHARS:
        return Citation(quote, False, None, None,
                        f"Quote too short ({len(q)} chars) to constitute evidence.")

    for doc in corpus:
        src = normalize(doc.get("text", ""))
        if not src:
            continue
        if q in src:
            return Citation(quote, True, doc.get("doc_id"), doc.get("title"),
                            "Exact match found in source document.")

    # Tolerate elision: the model quoted the opening of a real sentence then trailed off.
    head = q[:ELISION_HEAD_CHARS]
    if len(head) >= MIN_ELISION_HEAD:
        for doc in corpus:
            if head in normalize(doc.get("text", "")):
                return Citation(quote, True, doc.get("doc_id"), doc.get("title"),
                                "Leading span matched in source document (quote appears elided).")

    return Citation(quote, False, None, None,
                    "Quote NOT found in any source document. The control may be paraphrased, "
                    "misattributed, or fabricated — verify manually before relying on it.")


def verify_assertions(assertions: list[dict], corpus: list[dict], quote_key: str = "source_quote") -> list[dict]:
    """Verify a list of agent assertions in place, attaching citation metadata to each.

    Adds: citation_verified (bool), citation_document, citation_reason.
    Downgrades `confidence` to "low" whenever a citation cannot be verified — an unverifiable
    claim never gets to look as trustworthy as a verified one.
    """
    out = []
    for a in assertions or []:
        cit = verify_quote(a.get(quote_key, ""), corpus)
        enriched = {
            **a,
            "citation_verified": cit.verified,
            "citation_document": cit.document_title,
            "citation_document_id": cit.document_id,
            "citation_reason": cit.reason,
        }
        if not cit.verified:
            enriched["confidence"] = "low"
        out.append(enriched)
    return out


def provenance_summary(assertions: list[dict]) -> dict:
    """Aggregate provenance health — shown to the authoriser before they trust anything."""
    total = len(assertions or [])
    verified = sum(1 for a in assertions or [] if a.get("citation_verified"))
    return {
        "total": total,
        "verified": verified,
        "unverified": total - verified,
        "verified_pct": round(100 * verified / total) if total else 0,
        "trustworthy": total > 0 and verified == total,
    }
