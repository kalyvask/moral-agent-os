"""Cost and latency of the contextual assessor, the product dimension a PM has to own.

A reading model is more accurate than the keyword scaffold but it is not free: every
decision is an API call with a price and a latency. This measures both on a small sample and
projects the economics, then states the obvious tiered design: run the free deterministic
floor and scaffold on the clear cases, and spend a model call only on the contested ones.

    export OPENROUTER_API_KEY=...
    python -m bench.cost_latency [--sample 12]
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

from ai_safety_os import MoralAgentOS, OpenRouterAssessor
from ai_safety_os.openrouter_assessor import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    OpenRouterAssessorError,
)
from ai_safety_os.schema import Disposition
from bench.run import load_scenarios

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def fetch_pricing(model: str, api_key: str) -> tuple[float, float]:
    """Return (prompt $/token, completion $/token) for a model from OpenRouter."""
    request = urllib.request.Request(
        f"{DEFAULT_BASE_URL}/models", headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    for entry in data["data"]:
        if entry["id"] == model:
            pricing = entry.get("pricing", {})
            return float(pricing.get("prompt", 0)), float(pricing.get("completion", 0))
    return 0.0, 0.0


def run(model: str, sample: int) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENROUTER_API_KEY.")
    prompt_price, completion_price = fetch_pricing(model, api_key)

    scenarios = load_scenarios()[:sample]
    assessor = OpenRouterAssessor(model)

    latencies: list[float] = []
    prompt_tokens: list[int] = []
    completion_tokens: list[int] = []
    failures = 0
    for scenario in scenarios:
        try:
            assessor.assess(scenario)
        except OpenRouterAssessorError:
            failures += 1
            continue
        latencies.append(assessor.last_latency_s)
        prompt_tokens.append(assessor.last_usage.get("prompt_tokens", 0) or 0)
        completion_tokens.append(assessor.last_usage.get("completion_tokens", 0) or 0)
    if not latencies:
        raise SystemExit("All sample calls failed; check connectivity or model slug.")

    mean_prompt = sum(prompt_tokens) / len(prompt_tokens)
    mean_completion = sum(completion_tokens) / len(completion_tokens)
    cost_per_decision = mean_prompt * prompt_price + mean_completion * completion_price

    # How many decisions the cheap path could absorb: the scaffold auto-allows or hard-floor
    # blocks the clear ones, leaving the contested middle for the model.
    scaffold = MoralAgentOS()
    full = load_scenarios()
    contested = sum(
        1
        for s in full
        if scaffold.evaluate(s).disposition not in (Disposition.AUTO, Disposition.BLOCK)
    )
    contested_share = contested / len(full)

    return {
        "model": model,
        "sample": len(latencies),
        "failures": failures,
        "p50_latency_s": _percentile(latencies, 50),
        "p95_latency_s": _percentile(latencies, 95),
        "mean_prompt_tokens": mean_prompt,
        "mean_completion_tokens": mean_completion,
        "cost_per_decision": cost_per_decision,
        "prompt_price": prompt_price,
        "completion_price": completion_price,
        "contested_share": contested_share,
        "bank_size": len(full),
    }


def render_report(data: dict) -> str:
    cpd = data["cost_per_decision"]
    contested = data["contested_share"]
    every = cpd
    tiered = cpd * contested
    return "\n".join([
        "# Cost And Latency",
        "",
        f"Model: `{data['model']}` over a {data['sample']}-scenario sample.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| p50 latency | {data['p50_latency_s']:.2f} s |",
        f"| p95 latency | {data['p95_latency_s']:.2f} s |",
        f"| Mean prompt tokens | {data['mean_prompt_tokens']:.0f} |",
        f"| Mean completion tokens | {data['mean_completion_tokens']:.0f} |",
        f"| Cost per decision | ${cpd:.5f} |",
        "",
        "## Tiered routing economics",
        "",
        f"The deterministic floor and scaffold auto-allow or hard-block "
        f"{(1 - contested):.0%} of this bank for free, leaving {contested:.0%} contested "
        "decisions that actually need contextual judgment.",
        "",
        "| Strategy | Cost per 1,000 agent actions |",
        "| --- | ---: |",
        f"| Model on every action | ${every * 1000:.2f} |",
        f"| Model only on contested actions | ${tiered * 1000:.2f} |",
        "",
        f"Routing only the contested {contested:.0%} to the model cuts spend by "
        f"{(1 - contested):.0%} while keeping the contextual judgment exactly where the "
        "scaffold is blind. Latency is hidden the same way: clear actions return instantly; "
        "only the contested ones wait on a model call. This is the product argument for the "
        "thin-floor-plus-thick-layer split, now in dollars.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sample", type=int, default=12)
    args = parser.parse_args()
    data = run(args.model, args.sample)
    report = render_report(data)
    (DOCS / "cost-latency.md").write_text(report, encoding="utf-8")
    print(report)
    print("\nWrote docs/cost-latency.md")


if __name__ == "__main__":
    main()
