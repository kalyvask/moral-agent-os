"""Generate a grouped Markdown report for the interdependence benchmark."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from bench.interdependence import run_all
from moral_agent_os.interdependence import EnvironmentFamily, SimulationResult


FAMILY_LABELS = {
    EnvironmentFamily.STAG_HUNT: "Stag Hunt",
    EnvironmentFamily.COMMONS: "Shared-Resource Commons",
    EnvironmentFamily.DELEGATION: "Delegation With Accountability",
    EnvironmentFamily.ASYMMETRIC_DEPENDENCE: "Asymmetric Dependence",
}


def condition_label(condition: str) -> str:
    if condition.endswith("_one_shot"):
        return "One-shot"
    if condition.endswith("_static_policy"):
        return "Static policy"
    if condition.endswith("_repeated_no_sanction"):
        return "Repeated, no sanction"
    if condition.endswith("_interdependent"):
        return "Interdependent learning"
    return condition


def percent(value: float) -> str:
    return f"{value:.1%}"


def render_report(results: list[SimulationResult]) -> str:
    grouped: dict[EnvironmentFamily, list[SimulationResult]] = defaultdict(list)
    for result in results:
        grouped[result.family].append(result)

    lines = [
        "# Interdependence Report",
        "",
        "This report separates forced compliance from autonomous cooperation.",
        "Static policy can block defection, but the moral-learning signal is whether agents",
        "cooperate without being blocked, repair after sanction, and build norm strength.",
        "",
        "## Summary",
        "",
        "| Family | Condition | Cooperation | Autonomous cooperation | Blocked | Repair | Repair debt | Stewardship | Dependent harm | Norm strength | Norm stability |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for family in EnvironmentFamily:
        for result in grouped.get(family, []):
            lines.append(
                "| "
                + " | ".join(
                    [
                        FAMILY_LABELS[family],
                        condition_label(result.condition),
                        percent(result.cooperation_rate),
                        percent(result.autonomous_cooperation_rate),
                        percent(result.blocked_rate),
                        percent(result.repair_rate),
                        f"{result.mean_repair_obligation:.2f}",
                        percent(result.stewardship_rate),
                        percent(result.dependent_harm_rate),
                        f"{result.norm_strength:.2f}",
                        percent(result.norm_stability),
                    ]
                )
                + " |"
            )

    lines.extend(["", "## Family Readouts", ""])

    for family in EnvironmentFamily:
        family_results = grouped.get(family, [])
        if not family_results:
            continue
        static = next(
            (result for result in family_results if result.condition.endswith("_static_policy")),
            None,
        )
        interdependent = next(
            (result for result in family_results if result.condition.endswith("_interdependent")),
            None,
        )

        lines.append(f"### {FAMILY_LABELS[family]}")
        lines.append("")

        if static and interdependent:
            lines.append(
                "- Static policy forces "
                f"{percent(static.cooperation_rate)} cooperation, but "
                f"{percent(static.autonomous_cooperation_rate)} is autonomous and "
                f"norm strength remains {static.norm_strength:.2f}."
            )
            lines.append(
                "- Interdependence produces "
                f"{percent(interdependent.autonomous_cooperation_rate)} autonomous cooperation, "
                f"{percent(interdependent.repair_rate)} repair, and "
                f"norm strength {interdependent.norm_strength:.2f}, with "
                f"{interdependent.mean_repair_obligation:.2f} repair debt left."
            )
            if family == EnvironmentFamily.ASYMMETRIC_DEPENDENCE:
                lines.append(
                    "- In the asymmetric case, interdependence produces "
                    f"{percent(interdependent.stewardship_rate)} stewardship and "
                    f"{percent(interdependent.dependent_harm_rate)} dependent harm."
                )
        elif interdependent:
            lines.append(
                "- Interdependence produces "
                f"{percent(interdependent.autonomous_cooperation_rate)} autonomous cooperation "
                f"and norm strength {interdependent.norm_strength:.2f}."
            )

        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "The point is not that static policy is useless. It is the thin floor.",
            "The point is that a hard rule can create compliant behavior without creating",
            "earned trust, repair, or a norm that agents learn to uphold when the rule is absent.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the Markdown report.",
    )
    args = parser.parse_args()

    report = render_report(run_all())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
