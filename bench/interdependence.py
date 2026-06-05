"""Run the interdependence benchmark."""

from __future__ import annotations

from moral_agent_os.interdependence import (
    InterdependenceEnvironment,
    SimulationResult,
    default_conditions,
)


def run_all() -> list[SimulationResult]:
    return [
        InterdependenceEnvironment(config).run()
        for config in default_conditions()
    ]


def main() -> None:
    print("# Interdependence Benchmark")
    print()
    print(
        "Repeated dependence, partner choice, reputation, and sanction are "
        "the environmental conditions the course says moral behavior grew inside."
    )
    print()

    for result in run_all():
        print(f"## {result.condition}")
        print(f"- cooperation_rate: {result.cooperation_rate:.1%}")
        print(f"- autonomous_cooperation_rate: {result.autonomous_cooperation_rate:.1%}")
        print(f"- blocked_rate: {result.blocked_rate:.1%}")
        print(f"- betrayal_rate: {result.betrayal_rate:.1%}")
        print(f"- repair_rate: {result.repair_rate:.1%}")
        print(f"- mean_repair_obligation: {result.mean_repair_obligation:.2f}")
        print(f"- stewardship_rate: {result.stewardship_rate:.1%}")
        print(f"- dependent_harm_rate: {result.dependent_harm_rate:.1%}")
        print(f"- third_party_review_rate: {result.third_party_review_rate:.1%}")
        print(f"- joint_commitment_rate: {result.joint_commitment_rate:.1%}")
        print(f"- mean_payoff: {result.mean_payoff:.2f}")
        print(f"- mean_reputation: {result.mean_reputation:.2f}")
        print(f"- norm_strength: {result.norm_strength:.2f}")
        print(f"- norm_stability: {result.norm_stability:.1%}")
        print()


if __name__ == "__main__":
    main()
