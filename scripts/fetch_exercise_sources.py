"""Download registered exercise-source PDFs that are not already local."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config  # noqa: E402


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"skip {dest.name}")
        return
    print(f"get  {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "GenAI-Calculus-Tutor"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    dest.write_bytes(data)
    print(f"saved {dest} ({len(data)} bytes)")


def main() -> None:
    payload = json.loads(config.EXERCISE_SOURCES_FILE.read_text(encoding="utf-8"))
    chapters = [int(arg) for arg in sys.argv[1:]] or None
    for source in payload["sources"]:
        if source.get("download") != "auto":
            print(f"local source {source['source_id']}")
            continue
        pattern = source["pdf_pattern"]
        folder = config.EXERCISES_DIR / source["save_dir"]
        selected = chapters or source["chapters"]
        for chapter in selected:
            if chapter not in source["chapters"]:
                continue
            url = pattern.format(nn=f"{chapter:02d}")
            dest = folder / source["filename_pattern"].format(nn=f"{chapter:02d}")
            _download(url, dest)


if __name__ == "__main__":
    main()
