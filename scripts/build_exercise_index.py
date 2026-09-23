"""Build the standalone exercise stem index.

The collection lives in data/chroma-exercises and is not the textbook index.
Only reference stems are embedded. Solutions stay in the JSONL file.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, exercise_bank, rag  # noqa: E402


def main() -> None:
    rows = [
        row for row in exercise_bank.load()
        if row.get("serve_as_reference") is not False
        and not row.get("duplicate_of")
        and row.get("primary_section_id")
        and row.get("stem")
    ]
    exercise_bank.reset_cache()
    client = exercise_bank._client()
    name = config.EXERCISE_CHROMA_COLLECTION
    try:
        client.delete_collection(name)
    except Exception:
        pass
    collection = client.create_collection(name)
    if not rows:
        print("no reference rows to index")
        return
    model = rag._embedding_model()
    stems = [row["stem"] for row in rows]
    vectors = model.encode(stems, normalize_embeddings=True, show_progress_bar=False)
    collection.add(
        ids=[row["exercise_id"] for row in rows],
        documents=stems,
        embeddings=vectors.tolist(),
        metadatas=[
            {
                "exercise_id": row["exercise_id"],
                "primary_section_id": row["primary_section_id"],
                "difficulty": row["designed_difficulty"],
                "source": row["source"],
            }
            for row in rows
        ],
    )
    textbook_count = rag.index_status().get("chunks")
    print({
        "exercise_collection": name,
        "exercise_chunks": collection.count(),
        "textbook_chunks": textbook_count,
        "dir": str(config.EXERCISE_CHROMA_DIR),
    })


if __name__ == "__main__":
    main()
