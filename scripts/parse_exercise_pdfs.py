"""Parse exercise PDFs with MinerU into data/exercises/parsed/.

The local mineru-api is checked over HTTP. This machine's system proxy
answers for 127.0.0.1 and returns 502, so localhost is added to NO_PROXY
before MinerU starts.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config  # noqa: E402


def _mineru_env() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("NO_PROXY") or env.get("no_proxy") or ""
    parts = [item.strip() for item in current.split(",") if item.strip()]
    for host in ("127.0.0.1", "localhost", "::1"):
        if host not in parts:
            parts.append(host)
    joined = ",".join(parts)
    env["NO_PROXY"] = joined
    env["no_proxy"] = joined
    return env


def main() -> None:
    if shutil.which("mineru") is None:
        raise SystemExit("mineru is not on PATH")
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        raise SystemExit("pass one or more PDF paths")
    out = config.EXERCISE_PARSED_DIR
    out.mkdir(parents=True, exist_ok=True)
    env = _mineru_env()
    for pdf in paths:
        if not pdf.exists():
            raise SystemExit(f"missing {pdf}")
        target = out / pdf.stem
        print(f"parse {pdf.name} -> {target}")
        subprocess.run(
            [
                "mineru",
                "-p", str(pdf),
                "-o", str(target),
                "-b", "pipeline",
                "-m", "txt",
                "-f", "false",
                "-t", "true",
            ],
            check=True,
            env=env,
        )


if __name__ == "__main__":
    main()
