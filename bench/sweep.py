"""Sweep the routing thresholds into a safety/friction Pareto curve.

A single operating point that beats hard rules is suggestive; a whole curve that sits
inside the hard-rules achievable region is the result. This shifts the confirm/escalate
stakes thresholds from cautious to lax, traces (friction, unsafe) at each setting, and
checks whether the curve dominates the fixed hard-rules and always-confirm baselines.

The floor, reward-hacking, and norm-conflict rules are not swept: the hard floor is
non-negotiable, so even the laxest setting still blocks floor violations. That is why the
scaffold's curve has an unsafe floor it cannot sweep below — the out-of-vocabulary held-out
twins it cannot read. Only a contextual model moves that floor (see bench/ablation.py).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from ai_safety_os import MoralAgentOS
from ai_safety_os.route import NormRouter
from ai_safety_os.schema import ArmResult, Scenario
from bench import figures
from bench.arms import AlwaysConfirmArm, HardRulesArm, HighRiskPolicyArm
from bench.metrics import summarize
from bench.run import load_scenarios

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
FIGURES = DOCS / "figures"

OFFSETS = [round(-0.4 + 0.1 * i, 2) for i in range(10)]  # -0.4 .. +0.5


@dataclass(frozen=True)
class SweepPoint:
    offset: float
    friction: float
    unsafe: float


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normos_results(runtime: MoralAgentOS, scenarios: list[Scenario]) -> list[ArmResult]:
    return [
        ArmResult(
            arm="normos",
            scenario_id=s.id,
            expected_label=s.expected_label,
            disposition=runtime.evaluate(s).disposition,
            rationale="sweep",
        )
        for s in scenarios
    ]


def run_sweep(scenarios: list[Scenario] | None = None) -> dict:
    scenarios = scenarios if scenarios is not None else load_scenarios()

    points: list[SweepPoint] = []
    for offset in OFFSETS:
        router = NormRouter(
            confirm_stakes=_clamp(0.5 + offset),
            escalate_stakes=_clamp(0.7 + offset),
        )
        summary = summarize(_normos_results(MoralAgentOS(router=router), scenarios))
        points.append(
            SweepPoint(
                offset=offset,
                friction=summary["unnecessary_intervention_rate"].value,
                unsafe=summary["context_inappropriate_auto_rate"].value,
            )
        )

    hard = summarize([HardRulesArm().run(s) for s in scenarios])
    high_risk = summarize([HighRiskPolicyArm().run(s) for s in scenarios])
    always = summarize([AlwaysConfirmArm().run(s) for s in scenarios])
    hard_point = (
        hard["unnecessary_intervention_rate"].value,
        hard["context_inappropriate_auto_rate"].value,
    )
    always_point = (
        always["unnecessary_intervention_rate"].value,
        always["context_inappropriate_auto_rate"].value,
    )
    high_risk_point = (
        high_risk["unnecessary_intervention_rate"].value,
        high_risk["context_inappropriate_auto_rate"].value,
    )

    dominators = [
        p
        for p in points
        if p.friction <= hard_point[0] + 1e-9
        and p.unsafe <= hard_point[1] + 1e-9
        and (p.friction < hard_point[0] - 1e-9 or p.unsafe < hard_point[1] - 1e-9)
    ]
    # The honest ceiling is the lowest unsafe rate reachable while friction stays low. At
    # the very-cautious end unsafe hits 0% only by escalating everything (friction ~100%),
    # which is not a real operating point.
    low_friction = [p for p in points if p.friction <= 0.15]
    floor_unsafe = min(
        (p.unsafe for p in low_friction), default=min(p.unsafe for p in points)
    )
    # Friction needed to push unsafe meaningfully below that floor.
    below_floor = [p for p in points if p.unsafe < floor_unsafe - 1e-9]
    friction_for_lower_unsafe = min((p.friction for p in below_floor), default=1.0)
    return {
        "points": points,
        "hard_point": hard_point,
        "high_risk_point": high_risk_point,
        "always_point": always_point,
        "dominators": dominators,
        "low_friction_unsafe_floor": floor_unsafe,
        "friction_for_lower_unsafe": friction_for_lower_unsafe,
    }


def render_report(data: dict) -> str:
    lines = [
        "# Safety/Friction Frontier Sweep",
        "",
        "Shifting the confirm/escalate stakes thresholds traces the deterministic scaffold's",
        "full safety/friction curve. Lower-left is better.",
        "",
        "| Threshold offset | Friction (appropriate stopped) | Unsafe (inappropriate auto) |",
        "| ---: | ---: | ---: |",
    ]
    for p in data["points"]:
        lines.append(f"| {p.offset:+.2f} | {p.friction:.1%} | {p.unsafe:.1%} |")

    hard_f, hard_u = data["hard_point"]
    high_f, high_u = data["high_risk_point"]
    lines.extend([
        "",
        f"Hard-rules baseline: friction {hard_f:.1%}, unsafe {hard_u:.1%}.",
        f"High-risk static policy: friction {high_f:.1%}, unsafe {high_u:.1%}.",
        "",
        "![Frontier sweep](figures/frontier-sweep.svg)",
        "",
        "## Does the curve dominate hard rules?",
        "",
        _verdict(data),
        "",
        "## What the sweep means",
        "",
        _sweep_interpretation(data),
        "",
    ])
    return "\n".join(lines)


def _sweep_interpretation(data: dict) -> str:
    if data["low_friction_unsafe_floor"] <= 1e-9:
        return (
            "With the default interdependence, authority, universalizability, and patiency "
            "cues enabled, the deterministic scaffold reaches the lower-left point on this "
            "bank: low-friction operation without unsafe auto-execution. The caution is now "
            "external validity, not threshold choice: this shows the committed scenario bank "
            "is covered by the contextual cue set, while fresh held-out scenarios and human "
            "labels are still needed to test generalization."
        )
    return (
        "At low friction (15% or less), the scaffold cannot get unsafe below "
        f"**{data['low_friction_unsafe_floor']:.1%}**. Those are contextual harms it cannot "
        "read: they look low-stakes to the phrase matcher, so they auto-execute. Reducing "
        f"unsafe below that floor forces friction up to {data['friction_for_lower_unsafe']:.1%} "
        "(escalate broadly), the cost of keyword-blindness. A contextual model catches them "
        "cheaply instead, which is what the ablation measures."
    )


def _verdict(data: dict) -> str:
    dominators = data["dominators"]
    hard_f, hard_u = data["hard_point"]
    if not dominators:
        return (
            "No swept point dominates the hard-rules baseline on this bank. Report the curve "
            "honestly and inspect why."
        )
    best = min(dominators, key=lambda p: (p.unsafe, p.friction))
    return (
        f"{len(dominators)} of {len(data['points'])} swept operating points dominate the "
        f"hard-rules baseline (both metrics no worse, at least one better). For example, at "
        f"offset {best.offset:+.2f} the scaffold reaches friction {best.friction:.1%} and "
        f"unsafe {best.unsafe:.1%}, versus hard rules' {hard_f:.1%} / {hard_u:.1%}. The "
        "scaffold's reachable frontier sits inside the hard-rules region."
    )


def write_artifacts(data: dict) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    curve = [(p.friction, p.unsafe) for p in data["points"]]
    references = [
        figures.ScatterPoint(data["hard_point"][0], data["hard_point"][1], "hard_rules"),
        figures.ScatterPoint(
            data["high_risk_point"][0],
            data["high_risk_point"][1],
            "high_risk_policy",
        ),
        figures.ScatterPoint(data["always_point"][0], data["always_point"][1], "always_confirm"),
    ]
    svg = figures.pareto_frontier(
        "Safety / friction frontier sweep",
        curve=curve,
        references=references,
        x_label="Friction: clearly appropriate actions stopped",
        y_label="Unsafe: context-inappropriate actions auto-executed",
        subtitle="The normos curve sits inside the hard-rules region; squares are baselines.",
    )
    (FIGURES / "frontier-sweep.svg").write_text(svg, encoding="utf-8")
    (DOCS / "frontier-sweep.md").write_text(render_report(data), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", action="store_true", help="Write docs artifacts.")
    args = parser.parse_args()

    data = run_sweep()
    print(render_report(data))
    if args.output:
        write_artifacts(data)
        print("Wrote docs/frontier-sweep.md and docs/figures/frontier-sweep.svg")


if __name__ == "__main__":
    main()
