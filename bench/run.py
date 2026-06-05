"""Run the Stress benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bench.arms import AlwaysConfirmArm, HardRulesArm, NormOSArm
from bench.assessors import build_assessor
from bench.metrics import format_rate, summarize
from moral_agent_os.schema import Scenario

ROOT = Path(__file__).resolve().parent
SCENARIO_FILE = ROOT / "scenarios" / "workspace_actions.jsonl"


def load_scenarios(path: Path = SCENARIO_FILE) -> list[Scenario]:
    scenarios: list[Scenario] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            scenarios.append(Scenario.from_dict(json.loads(line)))
    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the appropriateness-routing benchmark.")
    parser.add_argument(
        "--assessor",
        choices=("heuristic", "llm"),
        default="heuristic",
        help="Assessor for the normos arm (default: heuristic, runs offline).",
    )
    args = parser.parse_args()

    scenarios = load_scenarios()
    arms = [
        HardRulesArm(),
        AlwaysConfirmArm(),
        NormOSArm(assessor=build_assessor(args.assessor)),
    ]

    print("# Stress Benchmark")
    print()
    print(f"Scenarios: {len(scenarios)}")
    print()

    for arm in arms:
        results = [arm.run(scenario) for scenario in scenarios]
        summary = summarize(results)
        print(f"## {arm.name}")
        for name, metric in summary.items():
            print(f"- {name}: {format_rate(metric)}")
        print()

    print("Same-action twins and matched families are in bench/scenarios/workspace_actions.jsonl.")
    print("Run `python -m bench.ablation` to test whether the win is contextual or definitional.")


if __name__ == "__main__":
    main()
