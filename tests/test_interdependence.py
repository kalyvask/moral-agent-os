from __future__ import annotations

import unittest

from bench.interdependence import run_all


class InterdependenceTest(unittest.TestCase):
    def test_stag_hunt_interdependence_improves_cooperation(self) -> None:
        results = {result.condition: result for result in run_all()}

        baseline = results["stag_hunt_one_shot"]
        interdependent = results["stag_hunt_interdependent"]

        self.assertGreater(
            interdependent.cooperation_rate,
            baseline.cooperation_rate,
        )
        self.assertGreater(
            interdependent.mean_payoff,
            baseline.mean_payoff,
        )

    def test_stag_hunt_interdependence_reduces_betrayal(self) -> None:
        results = {result.condition: result for result in run_all()}

        repeated_no_sanction = results["stag_hunt_repeated_no_sanction"]
        interdependent = results["stag_hunt_interdependent"]

        self.assertLessEqual(
            interdependent.betrayal_rate,
            repeated_no_sanction.betrayal_rate,
        )

    def test_commons_interdependence_improves_cooperation(self) -> None:
        results = {result.condition: result for result in run_all()}

        baseline = results["commons_one_shot"]
        interdependent = results["commons_interdependent"]

        self.assertGreater(
            interdependent.cooperation_rate,
            baseline.cooperation_rate,
        )
        self.assertGreater(
            interdependent.norm_stability,
            baseline.norm_stability,
        )

    def test_delegation_interdependence_improves_accountability(self) -> None:
        results = {result.condition: result for result in run_all()}

        baseline = results["delegation_one_shot"]
        interdependent = results["delegation_interdependent"]

        self.assertGreater(
            interdependent.cooperation_rate,
            baseline.cooperation_rate,
        )
        self.assertGreater(
            interdependent.mean_reputation,
            baseline.mean_reputation,
        )


if __name__ == "__main__":
    unittest.main()
