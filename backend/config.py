"""Central configuration loaded from environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the backend/ package
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
PROBLEMS_FILE = DATA_DIR / "problems.json"

load_dotenv(ROOT_DIR / ".env")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://yunwu.ai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

LOG_DIR.mkdir(parents=True, exist_ok=True)
