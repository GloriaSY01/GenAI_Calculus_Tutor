"""Concept panel — UI shell ready for future RAG-backed content."""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st


def fetch_concept(topic: str) -> Optional[dict[str, Any]]:
    """Placeholder for RAG-backed concept cards.

    Future: GET /concept?topic=... returning title, summary, formulas, etc.
    """
    return None


def render_concept_panel(current_topic: str) -> None:
    """Render concept card for the topic selected in the sidebar catalog."""
    st.markdown("##### Learn the concept")
    st.caption("Select a topic from the sidebar, review the concept, then start practice.")

    card = fetch_concept(current_topic)
    with st.container(border=True):
        st.markdown(f"### Topic: {current_topic}")

        if card:
            if card.get("summary"):
                st.markdown(card["summary"])
            for formula in card.get("formulas", []):
                st.markdown(formula)
            if card.get("example"):
                st.markdown("**Example**")
                st.markdown(card["example"])
            if card.get("pitfalls"):
                st.markdown("**Common mistakes**")
                st.markdown(card["pitfalls"])
        else:
            st.info(
                f"Concept content for **{current_topic}** will load from the textbook "
                "(via RAG once connected). When ready, click **Start practice** below."
            )
