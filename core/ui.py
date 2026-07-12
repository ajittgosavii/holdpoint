"""HOLDPOINT — shared UI helpers."""

import os
import streamlit as st

from core.domains import SITE_PACKS, SITE_LABELS, get_site, DEFAULT_SITE


def load_secrets() -> None:
    """Resolve credentials from, in order: a local .env, Streamlit Cloud secrets, the environment.

    Streamlit does NOT read .env automatically, so without load_dotenv() a local key is silently
    ignored and the app reports "not configured" while the file sits right there.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()  # no-op if there is no .env
    except ImportError:
        pass

    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        try:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
        except Exception:
            pass  # no secrets.toml (local dev) — fall back to .env / the real environment


def _init_site() -> str:
    key = st.session_state.get("active_site", DEFAULT_SITE)
    if key not in SITE_PACKS:
        key = DEFAULT_SITE
    if "active_site" not in st.session_state:
        st.session_state["active_site"] = key
    os.environ["ACTIVE_SITE"] = key
    return key


def _publish_site() -> str:
    """Read-only after the widget exists — Streamlit forbids writing a widget's key post-creation."""
    key = st.session_state.get("active_site", DEFAULT_SITE)
    if key not in SITE_PACKS:
        key = DEFAULT_SITE
    os.environ["ACTIVE_SITE"] = key
    return key


def bootstrap(show_nav: bool = True) -> dict:
    load_secrets()
    keys = list(SITE_PACKS)
    _init_site()

    with st.sidebar:
        if show_nav:
            st.markdown("### HOLDPOINT")
            st.page_link("app.py", label="Overview", icon="🛑")
            st.page_link("pages/1_Permit_Review.py", label="Permit Review", icon="🔍")
            st.page_link("pages/2_Backlog_Scan.py", label="Backlog Scan", icon="📊")
            st.page_link("pages/3_Incident_Precedent.py", label="Incident Precedent", icon="📕")
            st.markdown("---")

        st.markdown("### Industry")
        st.selectbox(
            "Site pack",
            keys,
            format_func=lambda k: SITE_LABELS[k],
            key="active_site",
            help="The agents contain no industry logic. Switching the pack swaps the hazard "
                 "vocabulary, substances, critical controls and authorising roles.",
        )
        site = get_site(_publish_site())
        st.caption(f"**{site['site_name']}**")

        # Evidence honesty — displayed, not buried.
        if site["evidence_status"] == "VERIFIED":
            st.success(f"Evidence: {site['evidence_status']}")
        else:
            st.warning(f"Evidence: {site['evidence_status']}")

        st.markdown("---")
        st.markdown("##### Engine")
        st.markdown("""
        - **7 agents** (LangGraph)
        - **Provenance-verified** citations
        - **Human authorises** — always
        """)
        ok = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        st.markdown(f"**LLM**: {'🟢 Connected' if ok else '🔴 Not configured'}")

    return site


def require_llm() -> None:
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        st.error(
            "No LLM configured. Set OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY for automatic "
            "failover) in Streamlit secrets or your environment."
        )
        st.stop()


VERDICT_STYLE = {
    "AUTHORISE": ("#166534", "#dcfce7", "#86efac", "✅"),
    "HOLD_WITH_CONDITIONS": ("#92400e", "#fef3c7", "#fcd34d", "⏸️"),
    "REJECT": ("#991b1b", "#fee2e2", "#fca5a5", "🛑"),
}


def render_verdict(verdict: dict) -> None:
    rec = (verdict.get("recommendation") or "UNKNOWN").upper()
    fg, bg, border, icon = VERDICT_STYLE.get(rec, ("#334155", "#f1f5f9", "#cbd5e1", "❓"))
    st.markdown(
        f"""
        <div style="background:{bg};border:2px solid {border};border-radius:10px;
                    padding:1.1rem 1.3rem;margin:0.6rem 0 1rem 0;">
            <div style="font-size:0.72rem;letter-spacing:0.12em;color:{fg};font-weight:700;
                        text-transform:uppercase;opacity:0.75;">
                HOLDPOINT recommendation — a human authoriser decides
            </div>
            <div style="font-size:1.75rem;font-weight:800;color:{fg};margin:0.15rem 0 0.4rem 0;">
                {icon}&nbsp; {rec.replace('_', ' ')}
            </div>
            <div style="font-size:1.02rem;color:{fg};line-height:1.5;">
                {verdict.get('headline', '')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_authorisation_gate() -> None:
    st.warning(
        "**HOLDPOINT does not authorise work.** This is decision support for a qualified human "
        "authoriser. Any finding marked UNVERIFIED could not be traced to a real site procedure and "
        "must be checked by hand before it is relied upon."
    )


def citation_badge(item: dict) -> str:
    if item.get("citation_verified"):
        doc = item.get("citation_document") or "procedure"
        return f'<span class="badge badge-verified">✓ Verified against {doc}</span>'
    if item.get("source_quote"):
        return '<span class="badge badge-unverified">⚠ Quote not found in any procedure — verify by hand</span>'
    return '<span class="badge badge-unverified">⚠ No citation — verify by hand</span>'


def render_quote(text: str, attribution: str = "") -> None:
    if not text:
        return
    attr = (f'<br><span style="font-style:normal;font-size:0.75rem;color:#64748b;">— {attribution}</span>'
            if attribution else "")
    st.markdown(
        f'<div class="source-quote">"{text}"{attr}</div>',
        unsafe_allow_html=True,
    )


def render_data_provenance() -> None:
    st.caption(
        "Data provenance: permits and site procedures in this demonstration are **illustrative** — "
        "written to carry the structural defects that real investigations describe. The incident "
        "corpus distinguishes **verified** investigations (CSB, Cullen Inquiry, ICMM — with the "
        "investigators' own words) from **illustrative** patterns, and never presents one as the "
        "other."
    )
