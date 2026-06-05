"""Select an assessor for the benchmarks, with a graceful offline fallback.

The deterministic scaffold runs everywhere with no secrets. The LLM assessor runs only
when the ``anthropic`` package and a credential are present; otherwise we print a note and
fall back so CI and no-key runs never break.
"""

from __future__ import annotations


def build_assessor(name: str):
    """Return an assessor instance for ``name`` ("heuristic" or "llm"), or None.

    None means "use the runtime default" (the deterministic ``HeuristicAssessor``).
    """
    if name == "heuristic":
        return None
    if name == "llm":
        from moral_agent_os import LLMAssessor

        if not LLMAssessor.available():
            print(
                "[bench] LLM assessor unavailable (no anthropic package or "
                "ANTHROPIC_API_KEY); falling back to the deterministic scaffold."
            )
            return None
        return LLMAssessor()
    raise SystemExit(f"Unknown assessor: {name!r} (use 'heuristic' or 'llm').")
