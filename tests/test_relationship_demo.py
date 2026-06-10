"""The runtime interdependence demo's claim, as a regression-guarded fact."""

from __future__ import annotations

import unittest

from ai_safety_os.schema import MoralRoute
from bench.relationship_demo import _post_violation_friction, run_demo


class RelationshipDemoTest(unittest.TestCase):
    def test_learning_adds_post_violation_friction_and_recovers(self) -> None:
        data = run_demo()

        # The loop holds routine actions for confirmation after a violation; control does not.
        self.assertGreater(
            _post_violation_friction(data["learning"]),
            _post_violation_friction(data["frozen"]),
        )
        self.assertEqual(_post_violation_friction(data["frozen"]), 0)

        # The violation itself is blocked in both arms: safety is the floor's job, not the loop's.
        self.assertEqual(data["learning"][1]["route"], MoralRoute.BLOCK)
        self.assertEqual(data["frozen"][1]["route"], MoralRoute.BLOCK)

        # Trust is repaired by the end, so autonomy is earned back.
        self.assertEqual(data["learning"][-1]["route"], MoralRoute.ALLOW)
        self.assertGreater(data["learning"][-1]["trust"], data["learning"][1]["trust"])


if __name__ == "__main__":
    unittest.main()
