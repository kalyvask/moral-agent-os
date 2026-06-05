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

    def test_static_policy_forces_compliance_without_norm_learning(self) -> None:
        results = {result.condition: result for result in run_all()}

        for condition in (
            "stag_hunt_static_policy",
            "commons_static_policy",
            "delegation_static_policy",
        ):
            static_policy = results[condition]
            self.assertGreater(static_policy.blocked_rate, 0.5)
            self.assertEqual(static_policy.autonomous_cooperation_rate, 0.0)
            self.assertEqual(static_policy.norm_strength, 0.0)
            self.assertEqual(static_policy.repair_rate, 0.0)
            self.assertEqual(static_policy.mean_repair_obligation, 0.0)

    def test_interdependence_does_not_depend_on_blocking(self) -> None:
        results = {result.condition: result for result in run_all()}

        for condition in (
            "stag_hunt_interdependent",
            "commons_interdependent",
            "delegation_interdependent",
        ):
            interdependent = results[condition]
            self.assertEqual(interdependent.blocked_rate, 0.0)
            self.assertGreater(interdependent.autonomous_cooperation_rate, 0.0)
            self.assertGreater(interdependent.norm_strength, 0.0)

    def test_interdependence_can_restore_trust_after_sanction(self) -> None:
        results = {result.condition: result for result in run_all()}

        for condition in (
            "commons_interdependent",
            "delegation_interdependent",
        ):
            interdependent = results[condition]
            self.assertGreater(interdependent.repair_rate, 0.0)
            self.assertLess(interdependent.mean_repair_obligation, 0.05)


if __name__ == "__main__":
    unittest.main()
