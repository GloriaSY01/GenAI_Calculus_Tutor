"""Topic catalog sidebar — flat list now, hierarchical TOC after RAG/textbook import."""

from __future__ import annotations

from typing import Any

import streamlit as st


def fetch_catalog(backend_url: str, fetch_topics_fn) -> list[dict[str, Any]]:
    """Return catalog entries. Now: flat topics; future: tree from /catalog."""
    topics = fetch_topics_fn()
    return [{"id": t, "title": t, "level": 0} for t in topics]


def render_topic_catalog(
    catalog: list[dict[str, Any]],
    current_topic: str,
    *,
    on_select,
) -> None:
    st.markdown("**Topics**")
    for entry in catalog:
        topic_id = entry["id"]
        title = entry["title"]
        is_active = topic_id == current_topic
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            title,
            key=f"cat_{topic_id}",
            use_container_width=True,
            type=btn_type,
            disabled=is_active,
        ):
            on_select(topic_id)
