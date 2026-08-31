"""Concept panel grounded in ordered MIT textbook content."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urljoin

import requests
import streamlit as st

from i18n import tr


@st.cache_data(ttl=600, show_spinner=False)
def fetch_concept(topic: str, backend_url: str) -> Optional[dict[str, Any]]:
    response = requests.get(
        f"{backend_url}/concept", params={"topic": topic}, timeout=30
    )
    if response.status_code == 503:
        return None
    response.raise_for_status()
    return response.json()


def _block_label(block: dict[str, Any], language: str = "en") -> str:
    subtype = str(block.get("subtype", "")).lower()
    if subtype == "definition":
        return tr(language, "Definition", "定义")
    if block.get("content_type") == "example" or subtype == "worked_example":
        return tr(language, "Example", "例题")
    if subtype in {"rule", "key_idea"}:
        return tr(language, "Key idea", "核心思想")
    return tr(language, "Concept", "概念")


def _figure_caption(figure: dict[str, Any]) -> str:
    return " — ".join(
        part
        for part in (
            str(figure.get("figure_number", "")).strip(),
            str(figure.get("caption", "")).strip(),
        )
        if part
    )


def render_concept_panel(
    current_topic: str, backend_url: str, language: str = "en"
) -> None:
    """Render the selected textbook section as a readable concept page."""
    st.markdown(f"##### {tr(language, 'Learn the concept', '学习概念')}")
    st.caption(
        tr(
            language,
            "Choose a section in the table of contents, then start practice.",
            "从教材目录选择一个小节，然后开始练习。",
        )
    )

    with st.spinner(
        tr(
            language,
            "Loading this section from the local textbook...",
            "正在从本地教材加载本小节……",
        )
    ):
        try:
            card = fetch_concept(current_topic, backend_url)
        except Exception as exc:  # noqa: BLE001
            st.error(tr(language, "Could not load this section: {error}", "无法加载本小节：{error}", error=exc))
            return

    with st.container(border=True):
        if not card:
            st.info(
                tr(
                    language,
                    "The local textbook index is not ready. Run "
                    "`python -m scripts.ingest_mit`, then refresh this page.",
                    "本地教材索引尚未就绪。请运行 "
                    "`python -m scripts.ingest_mit`，然后刷新页面。",
                )
            )
            return

        st.markdown(f"### {card.get('title') or current_topic}")
        if card.get("chapter"):
            st.caption(card["chapter"])
        content = card.get("content", [])
        if content:
            shown_figure_ids: set[str] = set()
            for block in content:
                st.markdown(f"#### {_block_label(block, language)}")
                if block.get("heading"):
                    st.markdown(f"**{block['heading']}**")
                st.markdown(block["text"])
                for formula in block.get("formulas", []):
                    st.markdown(f"`{formula}`")
                figures = [
                    figure
                    for figure in block.get("figures", [])
                    if figure.get("id") not in shown_figure_ids
                ]
                for figure in figures:
                    shown_figure_ids.add(figure.get("id"))
                    figure_url = urljoin(
                        backend_url.rstrip("/") + "/",
                        figure["url"].lstrip("/"),
                    )
                    st.image(
                        figure_url,
                        caption=_figure_caption(figure),
                        use_container_width=True,
                    )
                if block.get("requires_figure") and not figures:
                    st.caption(
                        tr(
                            language,
                            "The referenced textbook figure is unavailable.",
                            "对应的教材图片暂时无法显示。",
                        )
                    )
                if block.get("printed_page"):
                    st.caption(
                        tr(
                            language,
                            "Textbook page {page}",
                            "教材第 {page} 页",
                            page=block["printed_page"],
                        )
                    )
                st.divider()
        else:
            if card.get("summary"):
                st.markdown(f"**{tr(language, 'Key idea', '核心思想')}**")
                st.markdown(card["summary"])
            if card.get("definition"):
                st.markdown(f"**{tr(language, 'Definition', '定义')}**")
                st.markdown(card["definition"])
            if card.get("example"):
                st.markdown(f"**{tr(language, 'Example', '例题')}**")
                st.markdown(card["example"])
        source_url = card.get("source_url")
        if source_url:
            source = card.get("source") or "MIT Calculus — Gilbert Strang"
            publisher = card.get("publisher") or "MIT OpenCourseWare"
            license_name = card.get("license")
            term = card.get("term")
            st.markdown(
                f"**{tr(language, 'Source', '来源')}：** {source}  \n"
                f"**{tr(language, 'Section', '小节')}：** "
                f"[{card.get('title')}]({source_url})  \n"
                f"**{tr(language, 'Publisher', '发布方')}：** {publisher}"
            )
            details = " · ".join(value for value in (term, license_name) if value)
            if details:
                st.caption(details)
