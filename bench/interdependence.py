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
        print(f"- betrayal_rate: {result.betrayal_rate:.1%}")
        print(f"- mean_payoff: {result.mean_payoff:.2f}")
        print(f"- mean_reputation: {result.mean_reputation:.2f}")
        print(f"- norm_strength: {result.norm_strength:.2f}")
        print()


if __name__ == "__main__":
    main()
