"""Thin wrapper around the OpenAI-compatible chat completion endpoint."""
import json
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from . import config

_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def chat(messages: List[Dict[str, str]], temperature: float = 0.4,
         max_tokens: int = 700, response_format: Optional[dict] = None,
         retries: int = 1) -> str:
    """Return the raw assistant text, retrying once on transient failures."""
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            kwargs: Dict[str, Any] = dict(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response_format is not None:
                kwargs["response_format"] = response_format
            resp = _client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            # Some proxies reject response_format; drop it and retry plainly.
            response_format = None
            if attempt < retries:
                time.sleep(0.8)
    raise last_exc  # type: ignore[misc]


def chat_json(messages: List[Dict[str, str]], temperature: float = 0.4,
              max_tokens: int = 700) -> Dict[str, Any]:
    """Call the model and best-effort parse a JSON object from the reply."""
    text = chat(
        messages, temperature=temperature, max_tokens=max_tokens,
        response_format={"type": "json_object"}, retries=2,
    )
    return _extract_json(text)


def chat_to_json(messages: List[Dict[str, str]], temperature: float = 0.5,
                 max_tokens: int = 1000) -> Dict[str, Any]:
    """Parse JSON without forcing response_format (more reliable with LaTeX)."""
    text = chat(messages, temperature=temperature, max_tokens=max_tokens, retries=2)
    return _extract_json(text)


def _extract_json(text: str) -> Dict[str, Any]:
    """Robustly pull the first JSON object out of a model reply.

    Handles LaTeX in string values, where models often emit single backslashes
    (e.g. \\frac) that are invalid JSON escapes -- we double those and retry.
    """
    # Strip code fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace.group(0) if brace else None
    if candidate is None:
        raise ValueError(f"No JSON object found in model reply: {text[:200]!r}")

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return json.loads(_repair_backslashes(candidate))


def _repair_backslashes(s: str) -> str:
    """Double any backslash that is not part of a valid JSON escape.

    Valid JSON escapes: \\" \\\\ \\/ \\b \\f \\n \\r \\t \\uXXXX. LaTeX commands
    like \\frac or \\underline (and \\u not followed by 4 hex digits) are
    invalid and get their backslash doubled so json.loads accepts them.
    """
    pattern = re.compile(r'\\(u(?![0-9a-fA-F]{4})|[^"\\/bfnrtu])')
    return pattern.sub(lambda m: "\\\\" + m.group(1), s)
