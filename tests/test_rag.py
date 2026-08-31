import json
from array import array
from uuid import uuid4

import chromadb

from backend import rag


class FakeModel:
    def encode(self, texts, **kwargs):
        return [array("f", [1.0, 0.0])]


def _collection():
    collection = chromadb.EphemeralClient().create_collection(
        f"test_mit_calculus_{uuid4().hex}",
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=["limits", "integrals", "exercise"],
        documents=[
            "A limit describes behavior near a point.",
            "A definite integral is a limit of sums.",
            "Compute the limit.",
        ],
        embeddings=[[1.0, 0.0], [0.5, 0.5], [1.0, 0.0]],
        metadatas=[
            {
                "chapter": "2",
                "section_id": "mit-2-2-limits",
                "title": "Limits",
                "content_type": "concept",
                "order": 2,
                "pdf_page": 3,
                "requires_figure": False,
                "figure_ids": "[]",
            },
            {
                "chapter": "5",
                "section_id": "mit-5-2-integrals",
                "title": "Integrals",
                "content_type": "concept",
                "order": 1,
                "pdf_page": 4,
                "requires_figure": False,
                "figure_ids": "[]",
            },
            {
                "chapter": "2",
                "section_id": "mit-2-2-limits",
                "title": "Limits",
                "content_type": "exercise",
                "order": 3,
                "pdf_page": 5,
                "requires_figure": False,
                "figure_ids": json.dumps(["fig-2-1"]),
                "difficulty": "easy",
                "question_type": "fill_blank",
                "answer_available": True,
            },
        ],
    )
    return collection


def test_retrieve_uses_section_and_content_type_filters(monkeypatch):
    monkeypatch.setattr(rag, "_collection", _collection)
    monkeypatch.setattr(rag, "_embedding_model", lambda: FakeModel())

    results = rag.retrieve(
        "what is a limit",
        section_id="mit-2-2-limits",
        content_types=["concept"],
        k=3,
    )

    assert [item["id"] for item in results] == ["limits"]
    assert results[0]["content_type"] == "concept"
    assert rag.citations(results)[0]["page"] == 3


def test_exact_metadata_query_decodes_figures_and_filters_answers(monkeypatch):
    monkeypatch.setattr(rag, "_collection", _collection)

    results = rag.get_by_metadata(
        section_id="mit-2-2-limits",
        content_types=["exercise"],
        answer_available=True,
    )

    assert [item["id"] for item in results] == ["exercise"]
    assert results[0]["figure_ids"] == ["fig-2-1"]


def test_missing_collection_has_clear_status(monkeypatch):
    def unavailable():
        raise rag.RAGUnavailable("build the collection")

    monkeypatch.setattr(rag, "_collection", unavailable)
    status = rag.index_status()
    assert status["ready"] is False
    assert "build the collection" in status["detail"]


def test_section_page_uses_ordered_concept_and_example(monkeypatch):
    chunks = [
        {
            "id": "overview",
            "source": "MIT Calculus",
            "source_url": "https://example.test",
            "title": "Average velocities",
            "section": "Instantaneous velocity",
            "section_id": "mit-1-3-the-velocity-at-an-instant",
            "content_type": "concept",
            "subtype": "concept_explanation",
            "order": 1,
            "pdf_page": 17,
            "requires_figure": True,
            "figure_ids": ["fig-1-9"],
            "text": "Instantaneous velocity is the limit of average velocities.",
        },
        {
            "id": "definition",
            "source": "MIT Calculus",
            "source_url": "https://example.test",
            "title": "Instantaneous velocity",
            "section": "Instantaneous velocity",
            "section_id": "mit-1-3-the-velocity-at-an-instant",
            "content_type": "concept",
            "subtype": "definition",
            "order": 2,
            "pdf_page": 17,
            "requires_figure": True,
            "figure_ids": ["fig-1-9"],
            "text": "The derivative is the limiting slope of secant lines.",
        },
        {
            "id": "example",
            "source": "MIT Calculus",
            "source_url": "https://example.test",
            "title": "Falling body",
            "section": "Falling body",
            "section_id": "mit-1-3-the-velocity-at-an-instant",
            "content_type": "example",
            "subtype": "worked_example",
            "order": 3,
            "pdf_page": 18,
            "requires_figure": False,
            "figure_ids": [],
            "text": "Compute average velocities over shorter intervals.",
        },
    ]
    monkeypatch.setattr(rag, "get_by_metadata", lambda **kwargs: chunks)
    monkeypatch.setattr(
        rag,
        "_figures",
        lambda: {
            "fig-1-9": {
                "path": "parsed/ch01/example.jpg",
                "caption": "Fig. 1.9 Secant slopes.",
                "pdf_page": 17,
            }
        },
    )

    card = rag.section_page("mit-1-3-the-velocity-at-an-instant")

    assert card["summary"] != card["definition"]
    assert "limiting slope" in card["definition"]
    assert "shorter intervals" in card["example"]
    assert [block["order"] for block in card["content"]] == [1, 2, 3]
    assert sum(len(block["figures"]) for block in card["content"]) == 1
    assert card["content"][0]["figures"][0]["figure_number"] == "Figure 1.9"
    assert card["source"] == "MIT Calculus — Gilbert Strang"
    assert card["publisher"] == "MIT OpenCourseWare"
