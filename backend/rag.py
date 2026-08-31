"""Chroma retrieval over MIT Calculus textbook chunks."""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Iterable, Sequence

from . import config, textbook

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")


class RAGUnavailable(RuntimeError):
    """Raised when the local textbook collection has not been built."""


@lru_cache(maxsize=1)
def _embedding_model():
    from sentence_transformers import SentenceTransformer

    if (config.RAG_EMBEDDING_MODEL_DIR / "modules.json").exists():
        return SentenceTransformer(str(config.RAG_EMBEDDING_MODEL_DIR))
    try:
        return SentenceTransformer(config.RAG_EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        from modelscope import snapshot_download

        config.RAG_EMBEDDING_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = snapshot_download(
            config.RAG_EMBEDDING_MODEL,
            local_dir=str(config.RAG_EMBEDDING_MODEL_DIR),
            allow_patterns=[
                "*.json",
                "*.txt",
                "*.safetensors",
                "1_Pooling/*",
            ],
        )
        return SentenceTransformer(model_path)


@lru_cache(maxsize=1)
def _client():
    try:
        import chromadb
    except ImportError as exc:
        raise RAGUnavailable("Chroma is not installed. Run: pip install -r requirements.txt") from exc
    path = config.CHROMA_DIR
    if config.CHROMA_POINTER_FILE.exists():
        pointer = json.loads(config.CHROMA_POINTER_FILE.read_text(encoding="utf-8"))
        candidate = config.CHROMA_DIR / str(pointer["path"])
        if not candidate.is_dir() or candidate.parent != config.CHROMA_DIR:
            raise RAGUnavailable("The active Chroma index pointer is invalid.")
        path = candidate
    return chromadb.PersistentClient(path=str(path))


@lru_cache(maxsize=1)
def _collection():
    try:
        return _client().get_collection(config.CHROMA_COLLECTION)
    except Exception as exc:
        raise RAGUnavailable(
            "MIT Chroma collection is missing. Run: python -m scripts.ingest_mit"
        ) from exc


def reset_cache() -> None:
    _collection.cache_clear()
    _client.cache_clear()


def _decode_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value:
        return []
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return [str(item) for item in decoded] if isinstance(decoded, list) else []


def _record(
    chunk_id: str,
    document: str,
    metadata: dict[str, Any] | None,
    distance: float | None = None,
) -> dict[str, Any]:
    chunk = dict(metadata or {})
    chunk.update({
        "id": chunk_id,
        "text": document,
        "figure_ids": _decode_list(chunk.get("figure_ids")),
        "formulas": _decode_list(chunk.get("formulas")),
    })
    manifest = textbook.load_manifest()
    chunk.setdefault("source", f"{manifest['book']} — {manifest['author']}")
    page = chunk.get("pdf_page")
    source_url = manifest["source_url"].split("#", 1)[0]
    chunk.setdefault(
        "source_url",
        f"{source_url}#page={page}" if page else source_url,
    )
    chunk.setdefault("section", chunk.get("title", ""))
    if distance is not None:
        chunk["score"] = round(1.0 - float(distance), 4)
    return chunk


def index_status() -> dict[str, Any]:
    try:
        collection = _collection()
        result = collection.get(include=["metadatas"])
    except RAGUnavailable as exc:
        return {"ready": False, "chunks": 0, "detail": str(exc)}
    metadatas = result.get("metadatas") or []
    return {
        "ready": True,
        "chunks": collection.count(),
        "collection": config.CHROMA_COLLECTION,
        "sections": len({item.get("section_id") for item in metadatas if item}),
        "content_types": sorted(
            {str(item.get("content_type")) for item in metadatas if item}
        ),
    }


def warmup() -> None:
    collection = _collection()
    if collection.count():
        _embedding_model().encode(
            ["Calculus 1"], normalize_embeddings=True, show_progress_bar=False
        )


def _where(
    section_id: str | None,
    content_types: Sequence[str] | None,
    include_figure_dependent: bool,
    answer_available: bool | None = None,
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if section_id:
        clauses.append({"section_id": section_id})
    if content_types:
        allowed = list(dict.fromkeys(content_types))
        clauses.append(
            {"content_type": allowed[0]}
            if len(allowed) == 1
            else {"content_type": {"$in": allowed}}
        )
    if not include_figure_dependent:
        clauses.append({"requires_figure": False})
    if answer_available is not None:
        clauses.append({"answer_available": answer_available})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def retrieve(
    query: str,
    topic: str | None = None,
    k: int | None = None,
    section_id: str | None = None,
    content_types: Sequence[str] | None = None,
    subtypes: Sequence[str] | None = None,
    include_figure_dependent: bool = True,
) -> list[dict[str, Any]]:
    """Return semantic matches after Chroma metadata filtering."""
    del subtypes  # The MVP collection intentionally does not store subtype metadata.
    collection = _collection()
    if collection.count() == 0:
        return []
    query_text = f"{topic or section_id or 'Calculus 1'}: {query}".strip()
    vector = _embedding_model().encode(
        [query_text], normalize_embeddings=True, show_progress_bar=False
    )[0]
    kwargs: dict[str, Any] = {
        "query_embeddings": [vector.tolist()],
        "n_results": min(k or config.RAG_TOP_K, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    where = _where(section_id, content_types, include_figure_dependent)
    if where:
        kwargs["where"] = where
    result = collection.query(**kwargs)
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    return [
        _record(chunk_id, document, metadata, distance)
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances
        )
    ]


def get_by_metadata(
    *,
    section_id: str,
    content_types: Sequence[str],
    include_figure_dependent: bool = True,
    answer_available: bool | None = None,
) -> list[dict[str, Any]]:
    """Return exact metadata matches ordered as they appear in the textbook."""
    collection = _collection()
    where = _where(
        section_id,
        content_types,
        include_figure_dependent,
        answer_available,
    )
    result = collection.get(
        where=where,
        include=["documents", "metadatas"],
    )
    chunks = [
        _record(chunk_id, document, metadata)
        for chunk_id, document, metadata in zip(
            result.get("ids") or [],
            result.get("documents") or [],
            result.get("metadatas") or [],
        )
    ]
    return sorted(
        chunks,
        key=lambda chunk: (int(chunk.get("order", 0)), str(chunk["id"])),
    )


def format_context(chunks: Iterable[dict[str, Any]]) -> str:
    parts: list[str] = []
    used = 0
    for number, chunk in enumerate(chunks, start=1):
        page = chunk.get("pdf_page")
        page_text = f", PDF page {page}" if page else ""
        block = (
            f"[{number}] {chunk['title']}{page_text}\n"
            f"Source: {chunk.get('source_url', '')}\n{str(chunk['text']).strip()}"
        )
        remaining = config.RAG_MAX_CONTEXT_CHARS - used
        if remaining <= 0:
            break
        parts.append(block[:remaining])
        used += len(block)
    return "\n\n".join(parts)


def citations(chunks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        url = str(chunk.get("source_url", ""))
        page = chunk.get("pdf_page")
        key = f"{chunk.get('section_id')}::{page}"
        if key in seen:
            continue
        seen.add(key)
        output.append({
            "number": len(output) + 1,
            "source": chunk["source"],
            "title": chunk["title"],
            "section": chunk.get("section", ""),
            "url": url,
            "page": page,
        })
    return output


def _clean_excerpt(text: str, limit: int = 900) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit].rsplit(" ", 1)[0] + "…"


@lru_cache(maxsize=1)
def _figures() -> dict[str, dict[str, Any]]:
    path = config.TEXTBOOK_DIR / "figures.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _figure_payload(
    figure_id: str, printed_page: int | None
) -> dict[str, Any] | None:
    figure = _figures().get(figure_id, {})
    path = str(figure.get("path", ""))
    if not path:
        return None
    if path.startswith("parsed/"):
        path = path[len("parsed/") :]
    caption = str(figure.get("caption", "")).strip()
    figure_number = str(figure.get("figure_number", "")).strip()
    if not figure_number:
        match = re.search(r"\bFig(?:ure)?\.?\s*(\d+\.\d+)", caption, re.IGNORECASE)
        if match:
            figure_number = f"Figure {match.group(1)}"
        else:
            match = re.fullmatch(r"fig-(\d+)-(\d+)", figure_id)
            if match:
                figure_number = f"Figure {match.group(1)}.{match.group(2)}"
    if figure_number:
        caption = re.sub(
            r"^Fig(?:ure)?\.?\s*\d+\.\d+\s*",
            "",
            caption,
            flags=re.IGNORECASE,
        ).strip()
    return {
        "id": figure_id,
        "url": f"/textbook-assets/{path}",
        "figure_number": figure_number,
        "caption": caption or f"Textbook illustration on page {printed_page}",
        "printed_page": printed_page,
    }


def section_page(section_id: str) -> dict[str, Any]:
    """Build a Learn page from ordered concept/example chunks."""
    meta = textbook.get_section(section_id)
    if meta is None:
        raise KeyError(section_id)
    chunks = get_by_metadata(
        section_id=section_id,
        content_types=["concept", "example"],
    )
    if not chunks:
        raise RAGUnavailable(
            f"No indexed text for {meta['display_title']}. "
            "Run: python -m scripts.ingest_mit"
        )
    concepts = [chunk for chunk in chunks if chunk["content_type"] == "concept"]
    examples = [chunk for chunk in chunks if chunk["content_type"] == "example"]
    overview = concepts[0] if concepts else chunks[0]
    example = examples[0] if examples else None
    def printed_page(chunk: dict[str, Any]) -> int | None:
        page = chunk.get("pdf_page")
        if page is None or "printed_page_start" not in meta:
            return None
        return (
            int(meta["printed_page_start"])
            + int(page)
            - int(meta["pdf_page_start"])
        )

    content: list[dict[str, Any]] = []
    shown_figures: set[str] = set()
    for chunk in chunks:
        figures: list[dict[str, Any]] = []
        for figure_id in chunk.get("figure_ids", []):
            if figure_id in shown_figures:
                continue
            figure = _figure_payload(figure_id, printed_page(chunk))
            if figure is None:
                continue
            shown_figures.add(figure_id)
            figures.append(figure)
        content.append({
            "id": chunk["id"],
            "content_type": chunk["content_type"],
            "subtype": chunk.get("subtype", chunk["content_type"]),
            "heading": chunk["title"],
            "text": _clean_excerpt(str(chunk["text"]), 1400),
            "formulas": chunk.get("formulas", []),
            "order": int(chunk.get("order", 0)),
            "printed_page": printed_page(chunk),
            "requires_figure": bool(chunk.get("requires_figure", False)),
            "figures": figures,
        })
    definition = next(
        (
            chunk
            for chunk in concepts
            if chunk.get("subtype") == "definition"
            and str(chunk["text"]).strip() != str(overview["text"]).strip()
        ),
        None,
    )
    manifest = textbook.load_manifest()
    return {
        "topic": section_id,
        "title": meta["display_title"],
        "chapter": meta["chapter_title"],
        "summary": _clean_excerpt(str(overview["text"]), 700),
        "definition": _clean_excerpt(str(definition["text"]), 900) if definition else "",
        "formulas": [],
        "example": _clean_excerpt(str(example["text"]), 700) if example else "",
        "pitfalls": "",
        "source_url": meta["url"],
        "source": f"MIT {manifest['book']} — {manifest['author']}",
        "publisher": manifest["publisher_source"],
        "license": manifest["license"],
        "attribution": manifest["attribution"],
        "term": manifest.get("term", ""),
        "content": content,
        "citations": citations(chunks),
    }


def concept_card(topic: str) -> dict[str, Any]:
    meta = textbook.get_section(topic)
    if meta is None:
        needle = topic.lower()
        for _, section in textbook.iter_sections():
            info = textbook.get_section(section["id"])
            if info and needle in {
                info["title"].lower(),
                info["display_title"].lower(),
                info["chapter_title"].lower(),
            }:
                meta = info
                break
    if meta is None:
        raise KeyError(topic)
    return section_page(meta["id"])
