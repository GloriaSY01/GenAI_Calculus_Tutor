"""Central configuration loaded from environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the backend/ package
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
PROBLEMS_FILE = DATA_DIR / "problems.json"
LEARNING_PATH_FILE = DATA_DIR / "learning_path.json"
ASSIGNMENTS_FILE = DATA_DIR / "assignments.json"

load_dotenv(ROOT_DIR / ".env")

# yunwu.ai retired its API in favour of api.openlux.ai (the old host now answers
# every call with HTTP 403 "account migrated"); keys must be reissued there.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openlux.ai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

LOG_DIR.mkdir(parents=True, exist_ok=True)
