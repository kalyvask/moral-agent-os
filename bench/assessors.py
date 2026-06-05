"""Select an assessor for the benchmarks, with a graceful offline fallback.

The deterministic scaffold runs everywhere with no secrets. The LLM assessors run only when
a credential is present; otherwise we print a note and fall back so CI and no-key runs never
break. ``llm`` uses the Anthropic SDK and ``ANTHROPIC_API_KEY``; ``openrouter`` uses
OpenRouter and ``OPENROUTER_API_KEY`` (model via ``OPENROUTER_MODEL``).
"""

from __future__ import annotations

import os

CHOICES = ("heuristic", "llm", "openrouter")


def build_assessor(name: str):
    """Return an assessor instance for ``name``, or None for the deterministic default."""
    if name == "heuristic":
        return None
    if name == "llm":
        from ai_safety_os import LLMAssessor

        if not LLMAssessor.available():
            print(
                "[bench] LLM assessor unavailable (no anthropic package or "
                "ANTHROPIC_API_KEY); falling back to the deterministic scaffold."
            )
            return None
        return LLMAssessor()
    if name == "openrouter":
        from ai_safety_os import OpenRouterAssessor

        if not OpenRouterAssessor.available():
            print(
                "[bench] OpenRouter assessor unavailable (no OPENROUTER_API_KEY); "
                "falling back to the deterministic scaffold."
            )
            return None
        model = os.environ.get("OPENROUTER_MODEL")
        return OpenRouterAssessor(model) if model else OpenRouterAssessor()
    raise SystemExit(f"Unknown assessor: {name!r} (use one of {CHOICES}).")
