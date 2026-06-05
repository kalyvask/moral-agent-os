"""Validate scenario-bank shape."""

from __future__ import annotations

from collections import Counter, defaultdict

from bench.run import load_scenarios
from moral_agent_os.schema import ScenarioLabel


def main() -> None:
    scenarios = load_scenarios()
    ids = [scenario.id for scenario in scenarios]
    duplicates = [scenario_id for scenario_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise SystemExit(f"Duplicate scenario ids: {', '.join(sorted(duplicates))}")

    label_counts = Counter(scenario.expected_label for scenario in scenarios)
    missing_labels = [
        label.value for label in ScenarioLabel if label_counts.get(label, 0) == 0
    ]
    if missing_labels:
        raise SystemExit(f"Missing labels: {', '.join(missing_labels)}")

    families: dict[str, list[str]] = defaultdict(list)
    for scenario in scenarios:
        families[scenario.action_family].append(scenario.id)

    matched_families = {
        family: scenario_ids
        for family, scenario_ids in families.items()
        if len(scenario_ids) >= 2
    }

    print(f"Scenarios: {len(scenarios)}")
    print(
        "Labels: "
        + ", ".join(
            f"{label.value}={label_counts[label]}" for label in ScenarioLabel
        )
    )
    print(f"Matched action families: {len(matched_families)}")


if __name__ == "__main__":
    main()
