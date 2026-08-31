"""Expandable textbook catalog."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st

from i18n import tr


@st.cache_data(ttl=60, show_spinner=False)
def fetch_catalog(backend_url: str, fetch_topics_fn=None) -> dict[str, Any]:
    response = requests.get(f"{backend_url}/catalog", timeout=15)
    response.raise_for_status()
    return response.json()


def flatten_section_ids(catalog: dict[str, Any]) -> list[str]:
    return [
        section["id"]
        for chapter in catalog.get("chapters", [])
        for section in chapter.get("sections", [])
    ]


def section_title(catalog: dict[str, Any], section_id: str) -> str:
    for chapter in catalog.get("chapters", []):
        for section in chapter.get("sections", []):
            if section["id"] == section_id:
                return section["title"]
    return section_id


def render_topic_catalog(
    catalog: dict[str, Any],
    current_topic: str,
    *,
    on_select,
    language: str = "en",
) -> None:
    st.markdown(f"**{tr(language, 'Table of contents', '教材目录')}**")
    st.caption(catalog.get("source", "MIT Calculus"))
    for chapter in catalog.get("chapters", []):
        contains_current = any(
            section["id"] == current_topic for section in chapter.get("sections", [])
        )
        with st.expander(chapter["title"], expanded=contains_current):
            for section in chapter.get("sections", []):
                section_id = section["id"]
                is_active = section_id == current_topic
                indent = (
                    tr(language, "Introduction", "导言")
                    if section.get("label") in {"", "Introduction"}
                    else section["title"]
                )
                if st.button(
                    indent,
                    key=f"cat_{section_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    disabled=is_active,
                ):
                    on_select(section_id)
