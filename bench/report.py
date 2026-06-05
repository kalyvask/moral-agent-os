"""Generate benchmark artifacts: Markdown, CSV, JSON, and SVG figures.

One command turns the deterministic (or LLM) benchmark into committed artifacts:

    python -m bench.report                 # deterministic scaffold
    python -m bench.report --assessor llm  # contextual model, if a key is present

It writes:
  docs/benchmark-report.md       routing frontier + confusion matrix, human-readable
  docs/ablation-report.md        the context-ablation experiment
  docs/figures/*.svg             the five charts plus the ablation chart
  bench/results/*.csv            per-scenario and per-condition rows
  bench/results/*.json           metric summaries with confidence intervals
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from ai_safety_os.schema import ArmResult, Disposition, ScenarioLabel
from bench import figures
from bench.ablation import render_report as render_ablation
from bench.ablation import run_ablation
from bench.arms import AlwaysConfirmArm, HardRulesArm, HighRiskPolicyArm, NormOSArm
from bench.assessors import build_assessor
from bench.interdependence import run_all as run_interdependence
from bench.metrics import Rate, format_rate, summarize
from bench.run import load_scenarios

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DOCS = REPO / "docs"
FIGURES = DOCS / "figures"
RESULTS = ROOT / "results"

LABEL_ORDER = [
    ScenarioLabel.CLEAR_APPROPRIATE,
    ScenarioLabel.CLEAR_INAPPROPRIATE,
    ScenarioLabel.PLURAL,
]
DISPOSITION_ORDER = [
    Disposition.AUTO,
    Disposition.CONFIRM,
    Disposition.PRESENT_OPTIONS,
    Disposition.ESCALATE,
    Disposition.BLOCK,
]
ARM_ORDER = ("hard_rules", "high_risk_policy", "always_confirm", "normos")


# --------------------------------------------------------------------------- routing


def _run_arms(assessor):
    scenarios = load_scenarios()
    arms = [
        HardRulesArm(),
        HighRiskPolicyArm(),
        AlwaysConfirmArm(),
        NormOSArm(assessor=assessor),
    ]
    family = {s.id: s.action_family for s in scenarios}
    per_arm: dict[str, list[ArmResult]] = {}
    for arm in arms:
        per_arm[arm.name] = [arm.run(scenario) for scenario in scenarios]
    return scenarios, per_arm, family


def _confusion_counts(results: list[ArmResult]) -> list[list[int]]:
    counts = [[0 for _ in DISPOSITION_ORDER] for _ in LABEL_ORDER]
    row_index = {label: i for i, label in enumerate(LABEL_ORDER)}
    col_index = {disp: i for i, disp in enumerate(DISPOSITION_ORDER)}
    for result in results:
        counts[row_index[result.expected_label]][col_index[result.disposition]] += 1
    return counts


def _rate_dict(rate: Rate) -> dict:
    return {
        "value": round(rate.value, 4),
        "ci_low": round(rate.ci_low, 4),
        "ci_high": round(rate.ci_high, 4),
        "numerator": rate.numerator,
        "denominator": rate.denominator,
    }


def write_routing_artifacts(assessor, assessor_name: str) -> dict:
    scenarios, per_arm, family = _run_arms(assessor)

    # Per-scenario CSV.
    with (RESULTS / "routing.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["arm", "scenario_id", "action_family", "expected_label", "disposition"]
        )
        for arm_name, results in per_arm.items():
            for result in results:
                writer.writerow([
                    arm_name,
                    result.scenario_id,
                    family[result.scenario_id],
                    result.expected_label.value,
                    result.disposition.value,
                ])

    # Per-arm metric summary JSON.
    summary = {
        arm_name: {name: _rate_dict(metric) for name, metric in summarize(results).items()}
        for arm_name, results in per_arm.items()
    }
    (RESULTS / "routing_summary.json").write_text(
        json.dumps({"assessor": assessor_name, "arms": summary}, indent=2),
        encoding="utf-8",
    )

    return {"scenarios": scenarios, "per_arm": per_arm, "summary": summary}


# ------------------------------------------------------------------- interdependence


def write_interdependence_artifacts() -> list:
    results = run_interdependence()
    fields = [
        "condition", "family", "cooperation_rate", "autonomous_cooperation_rate",
        "blocked_rate", "betrayal_rate", "repair_rate", "mean_repair_obligation",
        "stewardship_rate", "dependent_harm_rate", "third_party_review_rate",
        "joint_commitment_rate", "mean_payoff", "mean_reputation", "norm_strength",
        "norm_stability",
    ]
    with (RESULTS / "interdependence.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for result in results:
            writer.writerow([_scalar(getattr(result, field)) for field in fields])

    payload = [
        {field: _scalar(getattr(result, field)) for field in fields}
        for result in results
    ]
    (RESULTS / "interdependence_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return results


def _scalar(value):
    return value.value if hasattr(value, "value") else value


# ------------------------------------------------------------------------- ablation


def write_ablation_artifacts(assessor) -> object:
    result = run_ablation(assessor=assessor)
    (DOCS / "ablation-report.md").write_text(render_ablation(result), encoding="utf-8")

    def cond(c) -> dict:
        return {
            "pair_discrimination": _rate_dict(c.pair_discrimination),
            "safety": _rate_dict(c.safety),
            "friction": _rate_dict(c.friction),
            "plural_mishandling": _rate_dict(c.plural_mishandling),
        }

    payload = {
        "assessor": result.assessor_name,
        "scenario_count": result.scenario_count,
        "twin_count": result.pair_count,
        "with_context": cond(result.with_context),
        "without_context": cond(result.without_context),
        "discrimination_attributable_to_context": round(result.discrimination_drop, 4),
        "safety_drop_without_context": round(result.safety_drop, 4),
    }
    (RESULTS / "ablation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result


# -------------------------------------------------------------------------- figures


def _by_condition(results) -> dict:
    return {r.condition: r for r in results}


def write_figures(routing, interdependence, ablation) -> list[str]:
    written: list[str] = []
    summary = routing["summary"]

    # 1. Safety/friction frontier.
    points = [
        figures.ScatterPoint(
            x=summary[arm]["unnecessary_intervention_rate"]["value"],
            y=summary[arm]["context_inappropriate_auto_rate"]["value"],
            label=arm,
        )
        for arm in ARM_ORDER
    ]
    written.append(_write_fig("frontier.svg", figures.scatter_frontier(
        "Safety / friction frontier",
        points,
        x_label="Friction: clearly appropriate actions stopped",
        y_label="Unsafe: context-inappropriate actions auto-executed",
        subtitle="Lower-left is better. Hard rules cannot reach it.",
    )))

    # 2. Routing confusion matrix (normos).
    counts = _confusion_counts(routing["per_arm"]["normos"])
    written.append(_write_fig("confusion-matrix.svg", figures.confusion_matrix(
        "Routing confusion matrix (normos)",
        row_labels=[label.value for label in LABEL_ORDER],
        col_labels=[disp.value for disp in DISPOSITION_ORDER],
        counts=counts,
        subtitle="Clear-bad should not land in auto; clear-good should.",
    )))

    index = _by_condition(interdependence)

    # 3. Interdependence: one-shot vs static vs interdependent.
    sh_series = ["stag_hunt_one_shot", "stag_hunt_static_policy", "stag_hunt_interdependent"]
    sh_metrics = [
        ("cooperation_rate", "Cooperation"),
        ("autonomous_cooperation_rate", "Autonomous coop."),
        ("repair_rate", "Repair"),
        ("norm_stability", "Norm stability"),
    ]
    written.append(_write_fig("interdependence.svg", figures.grouped_bar_chart(
        "Interdependence (Stag Hunt)",
        group_labels=[label for _, label in sh_metrics],
        series_labels=["One-shot", "Static policy", "Interdependent"],
        values=[
            [getattr(index[c], attr) for attr, _ in sh_metrics] for c in sh_series
        ],
        subtitle="Static policy forces compliance; only interdependence earns it.",
    )))

    # 3b. Interdependence score by environment: earned cooperation across families.
    families = [
        ("stag_hunt", "Stag Hunt"),
        ("commons", "Commons"),
        ("delegation", "Delegation"),
        ("asymmetric", "Asymmetric"),
    ]
    env_conditions = ["one_shot", "static_policy", "interdependent"]
    written.append(_write_fig("interdependence-by-environment.svg", figures.grouped_bar_chart(
        "Earned cooperation by environment",
        group_labels=[label for _, label in families],
        series_labels=["One-shot", "Static policy", "Interdependent"],
        values=[
            [index[f"{prefix}_{cond}"].autonomous_cooperation_rate for prefix, _ in families]
            for cond in env_conditions
        ],
        subtitle="Autonomous cooperation: static policy forces it, interdependence earns it.",
    )))

    # 4. Asymmetric dependence + third-party enforcement.
    asym_series = [
        "asymmetric_one_shot", "asymmetric_static_policy",
        "asymmetric_interdependent", "asymmetric_third_party_enforced",
    ]
    asym_metrics = [
        ("stewardship_rate", "Stewardship"),
        ("dependent_harm_rate", "Dependent harm"),
        ("third_party_review_rate", "Public review"),
    ]
    written.append(_write_fig("asymmetric.svg", figures.grouped_bar_chart(
        "Asymmetric dependence",
        group_labels=[label for _, label in asym_metrics],
        series_labels=["One-shot", "Static policy", "Interdependent", "Third-party"],
        values=[
            [getattr(index[c], attr) for attr, _ in asym_metrics] for c in asym_series
        ],
        subtitle="Does legibility to an accountable observer stabilize stewardship?",
    )))

    # 5. Shared intent vs plain interdependence (Stag Hunt).
    si_series = ["stag_hunt_interdependent", "stag_hunt_shared_intent"]
    si_metrics = [
        ("autonomous_cooperation_rate", "Autonomous coop."),
        ("joint_commitment_rate", "Joint commitment"),
    ]
    written.append(_write_fig("shared-intent.svg", figures.grouped_bar_chart(
        "Shared intent (Stag Hunt)",
        group_labels=[label for _, label in si_metrics],
        series_labels=["Interdependent", "Shared intent"],
        values=[
            [getattr(index[c], attr) for attr, _ in si_metrics] for c in si_series
        ],
        subtitle="Can agents coordinate as a 'we' before acting, without blocking?",
    )))

    # 6. Context ablation (the centerpiece falsifier).
    written.append(_write_fig("ablation.svg", figures.grouped_bar_chart(
        f"Context ablation ({ablation.assessor_name})",
        group_labels=["Twin discrimination", "Unsafe auto", "Friction"],
        series_labels=["With context", "Without context"],
        values=[
            [
                ablation.with_context.pair_discrimination.value,
                ablation.with_context.safety.value,
                ablation.with_context.friction.value,
            ],
            [
                ablation.without_context.pair_discrimination.value,
                ablation.without_context.safety.value,
                ablation.without_context.friction.value,
            ],
        ],
        subtitle="Without context, twins are identical inputs: discrimination must vanish.",
    )))
    return written


def _write_fig(name: str, svg: str) -> str:
    (FIGURES / name).write_text(svg, encoding="utf-8")
    return f"figures/{name}"


# -------------------------------------------------------------------------- markdown


def write_markdown(routing, ablation, assessor_name: str) -> None:
    summary = routing["summary"]
    metrics = [
        ("context_inappropriate_auto_rate", "Unsafe (inappropriate auto)"),
        ("unnecessary_intervention_rate", "Friction (appropriate stopped)"),
        ("plural_mishandling_rate", "Plural mishandled"),
    ]
    lines = [
        "# Benchmark Report",
        "",
        f"Assessor: `{assessor_name}`. Generated by `python -m bench.report`.",
        "",
        "## Appropriateness routing",
        "",
        "Two-axis frontier across four arms. Lower is better on every column.",
        "",
        "| Arm | " + " | ".join(label for _, label in metrics) + " |",
        "| --- | " + " | ".join("---:" for _ in metrics) + " |",
    ]
    for arm in ARM_ORDER:
        cells = [format_rate(_rate_from_dict(summary[arm][key])) for key, _ in metrics]
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")

    lines.extend([
        "",
        "![Safety/friction frontier](figures/frontier.svg)",
        "",
        "## Routing confusion matrix (normos)",
        "",
        "Rows are the expected label; columns are the routed disposition.",
        "",
        "| Expected \\ Routed | " + " | ".join(d.value for d in DISPOSITION_ORDER) + " |",
        "| --- | " + " | ".join("---:" for _ in DISPOSITION_ORDER) + " |",
    ])
    counts = _confusion_counts(routing["per_arm"]["normos"])
    for label, row in zip(LABEL_ORDER, counts, strict=False):
        lines.append(f"| {label.value} | " + " | ".join(str(c) for c in row) + " |")

    lines.extend([
        "",
        "![Routing confusion matrix](figures/confusion-matrix.svg)",
        "",
        "## Context ablation",
        "",
        f"Same-action twin discrimination with context "
        f"{format_rate(ablation.with_context.pair_discrimination)} vs without context "
        f"{format_rate(ablation.without_context.pair_discrimination)} "
        f"(control, ~0 by construction). Full report in "
        "[ablation-report.md](ablation-report.md).",
        "",
        "![Context ablation](figures/ablation.svg)",
        "",
        "## Interdependence",
        "",
        "Forced compliance vs earned cooperation across environment families.",
        "Full grouped report in [interdependence-report.md](interdependence-report.md).",
        "",
        "![Interdependence](figures/interdependence.svg)",
        "",
        "![Earned cooperation by environment](figures/interdependence-by-environment.svg)",
        "",
        "![Asymmetric dependence](figures/asymmetric.svg)",
        "",
        "![Shared intent](figures/shared-intent.svg)",
        "",
        "Raw rows and metric summaries (with confidence intervals) are in "
        "`bench/results/`.",
        "",
    ])
    (DOCS / "benchmark-report.md").write_text("\n".join(lines), encoding="utf-8")


def _rate_from_dict(d: dict) -> Rate:
    return Rate(d["numerator"], d["denominator"], d["value"], d["ci_low"], d["ci_high"])


# ------------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assessor", choices=("heuristic", "llm", "openrouter"), default="heuristic"
    )
    args = parser.parse_args()

    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    # Build the assessor once and reuse it; None means the deterministic default.
    assessor = build_assessor(args.assessor)
    assessor_name = type(assessor).__name__ if assessor else "HeuristicAssessor"
    routing = write_routing_artifacts(assessor, assessor_name)
    interdependence = write_interdependence_artifacts()
    ablation = write_ablation_artifacts(assessor)
    figure_paths = write_figures(routing, interdependence, ablation)
    write_markdown(routing, ablation, assessor_name)

    print("Wrote:")
    print("  docs/benchmark-report.md")
    print("  docs/ablation-report.md")
    for path in figure_paths:
        print(f"  docs/{path}")
    print("  bench/results/routing.csv, routing_summary.json")
    print("  bench/results/interdependence.csv, interdependence_summary.json")
    print("  bench/results/ablation.json")


if __name__ == "__main__":
    main()
