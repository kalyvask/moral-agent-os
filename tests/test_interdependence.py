from __future__ import annotations

import unittest

from bench.interdependence import run_all


class InterdependenceTest(unittest.TestCase):
    def test_interdependence_improves_cooperation(self) -> None:
        results = {result.condition: result for result in run_all()}

        baseline = results["one_shot_baseline"]
        interdependent = results["interdependent_norm_learning"]

        self.assertGreater(
            interdependent.cooperation_rate,
            baseline.cooperation_rate,
        )
        self.assertGreater(
            interdependent.mean_payoff,
            baseline.mean_payoff,
        )

    def test_interdependence_reduces_betrayal(self) -> None:
        results = {result.condition: result for result in run_all()}

        repeated_no_sanction = results["repeated_no_sanction"]
        interdependent = results["interdependent_norm_learning"]

        self.assertLessEqual(
            interdependent.betrayal_rate,
            repeated_no_sanction.betrayal_rate,
        )


if __name__ == "__main__":
    unittest.main()
