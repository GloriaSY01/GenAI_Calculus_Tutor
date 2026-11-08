"""Regression for Railway startup without model credentials."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from backend import config, llm


def test_app_starts_without_model_credentials(tmp_path):
    environment = dict(os.environ, LLM_API_KEY="", OPENAI_API_KEY="",
                       DATABASE_URL="sqlite:///" + str(tmp_path / "startup.sqlite3"))
    script = """
from fastapi.testclient import TestClient
from backend import rag
from backend.main import app
rag.warmup = lambda: None
with TestClient(app) as client:
    health = client.get('/health')
    assert health.status_code == 200
    assert health.json()['llm_configured'] is False
    response = client.get('/learning/config')
    assert response.status_code == 200 and response.json()['classes']
"""
    result = subprocess.run([sys.executable, "-c", script], env=environment,
                            cwd=Path(__file__).resolve().parents[1],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stderr


def test_missing_key_fails_before_network_or_retries(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    monkeypatch.setattr(llm, "_client", None)
    def unexpected(*args, **kwargs):
        pytest.fail("Missing credentials must not start network calls or retry delays")
    monkeypatch.setattr(llm, "OpenAI", unexpected)
    monkeypatch.setattr(llm.time, "sleep", unexpected)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        llm.chat([{"role": "user", "content": "Hello"}], retries=2)


def test_configured_client_is_created_on_first_call_and_reused(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "_client", None)
    creations = []
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hint"))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))
    def create(**kwargs):
        creations.append(kwargs)
        return client
    monkeypatch.setattr(llm, "OpenAI", create)
    assert llm.chat([]) == llm.chat([]) == "hint"
    assert len(creations) == 1
    assert creations[0]["api_key"] == "test-key"
