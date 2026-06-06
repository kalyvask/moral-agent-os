"""The runtime interdependence demo's claim, as a regression-guarded fact."""

from __future__ import annotations

from ai_safety_os.schema import MoralRoute
from bench.relationship_demo import _post_violation_friction, run_demo


def test_learning_adds_post_violation_friction_and_recovers() -> None:
    data = run_demo()

    # The loop holds routine actions for confirmation after a violation; the control does not.
    assert _post_violation_friction(data["learning"]) > _post_violation_friction(data["frozen"])
    assert _post_violation_friction(data["frozen"]) == 0

    # The violation itself is blocked in both arms: safety is the floor's job, not the loop's.
    assert data["learning"][1]["route"] == MoralRoute.BLOCK
    assert data["frozen"][1]["route"] == MoralRoute.BLOCK

    # Trust is repaired by the end, so autonomy is earned back.
    assert data["learning"][-1]["route"] == MoralRoute.ALLOW
    assert data["learning"][-1]["trust"] > data["learning"][1]["trust"]
