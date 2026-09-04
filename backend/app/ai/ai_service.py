"""
Thin, provider-agnostic wrapper around whichever AI_PROVIDER is configured.

Intentionally NOT hardcoded to a single vendor. Add a branch per provider as
needed. Returns None on any failure/misconfiguration so callers can fall back
to deterministic behavior — the app must keep working with AI_PROVIDER=none.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


def call_ai(system_prompt: str, user_prompt: str) -> Optional[dict]:
    if settings.AI_PROVIDER == "none" or not settings.AI_API_KEY:
        return None

    try:
        if settings.AI_PROVIDER == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=settings.AI_API_KEY)
            resp = client.messages.create(
                model=settings.AI_MODEL or "claude-sonnet-4-6",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = "".join(block.text for block in resp.content if block.type == "text")
            return json.loads(text)

        logger.warning("Unsupported AI_PROVIDER=%s; falling back to deterministic behavior.", settings.AI_PROVIDER)
        return None
    except Exception:
        logger.exception("AI call failed; falling back to deterministic behavior.")
        return None


def explain_result(decision_text: str, summary: dict) -> Optional[str]:
    """Optional: ask the AI to phrase an explanation. Numbers in `summary` are
    already computed by the simulation engine — the AI only rewords them,
    it never invents new figures."""
    if settings.AI_PROVIDER == "none" or not settings.AI_API_KEY:
        return None
    result = call_ai(
        system_prompt=(
            "Rewrite the given simulation summary as 2-3 plain-English sentences for a "
            "small business owner. Do not introduce any numbers that are not already present "
            "in the input. Respond with JSON: {\"text\": \"...\"}"
        ),
        user_prompt=json.dumps({"decision": decision_text, "summary": summary}),
    )
    return result.get("text") if result else None
