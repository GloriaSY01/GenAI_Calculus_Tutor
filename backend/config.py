"""Central configuration loaded from environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the backend/ package
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
PROBLEMS_FILE = DATA_DIR / "problems.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
TEXTBOOK_DIR = DATA_DIR / "textbook" / "mit-calculus"
TEXTBOOK_MANIFEST_FILE = TEXTBOOK_DIR / "manifest.json"
TEXTBOOK_TOC_FILE = TEXTBOOK_DIR / "toc.json"
TEXTBOOK_VERIFIED_CONTENT_FILE = TEXTBOOK_DIR / "verified_content.json"
TEXTBOOK_EXERCISES_FILE = TEXTBOOK_DIR / "curated_exercises.json"
TEXTBOOK_ASSETS_DIR = TEXTBOOK_DIR / "parsed"
TEXTBOOK_PDF_DIR = TEXTBOOK_DIR / "pdfs"

load_dotenv(ROOT_DIR / ".env")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://yunwu.ai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

_chroma_dir = Path(os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma")))
CHROMA_DIR = _chroma_dir if _chroma_dir.is_absolute() else ROOT_DIR / _chroma_dir
CHROMA_POINTER_FILE = CHROMA_DIR / "current.json"
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "mit_calculus")
RAG_EMBEDDING_MODEL = os.getenv(
    "RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
_embedding_model_dir = Path(
    os.getenv(
        "RAG_EMBEDDING_MODEL_DIR",
        str(DATA_DIR / "models" / "all-MiniLM-L6-v2"),
    )
)
RAG_EMBEDDING_MODEL_DIR = (
    _embedding_model_dir
    if _embedding_model_dir.is_absolute()
    else ROOT_DIR / _embedding_model_dir
)
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "4500"))
TEXTBOOK_EXERCISE_RATIO = min(
    1.0, max(0.0, float(os.getenv("TEXTBOOK_EXERCISE_RATIO", "0.5")))
)

# Stable IDs are logged and stored; labels are only for display. Replace these
# demo classes when the real course roster is known.
CLASS_OPTIONS = [
    {"id": "demo", "label": "Demo class"},
    {"id": "calc1-a", "label": "Calculus I · Class A"},
    {"id": "calc1-b", "label": "Calculus I · Class B"},
]

LOG_DIR.mkdir(parents=True, exist_ok=True)
TEXTBOOK_DIR.mkdir(parents=True, exist_ok=True)
