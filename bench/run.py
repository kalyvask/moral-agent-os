"""Run the Stress benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from bench.arms import AlwaysConfirmArm, HardRulesArm, NormOSArm
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
    scenarios = load_scenarios()
    arms = [HardRulesArm(), AlwaysConfirmArm(), NormOSArm()]

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

    print("Matched-pair scaffold is in bench/scenarios/workspace_actions.jsonl.")
    print("Expand this to 50-60 cases before making README claims.")


if __name__ == "__main__":
    main()
