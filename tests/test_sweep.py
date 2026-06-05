"""Tests for the threshold sweep and the parameterized router."""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from ai_safety_os.route import NormRouter
from ai_safety_os.schema import ContextAssessment, Disposition, Scenario, ScenarioLabel
from bench import figures
from bench.sweep import run_sweep


def _assessment(stakes: float) -> ContextAssessment:
    return ContextAssessment(
        scenario_id="s",
        situation="x",
        role_authority=0.8,
        stakes=stakes,
        reversibility=0.9,
        privacy_sensitivity=0.0,
        norm_conflict=0.1,
        confidence=0.9,
    )


_SCENARIO = Scenario(
    id="s",
    action_family="send_email",
    action_text="a",
    context="b",
    agent_role="r",
    expected_label=ScenarioLabel.CLEAR_APPROPRIATE,
)


class TestParameterizedRouter(unittest.TestCase):
    def test_raising_escalate_threshold_relaxes_routing(self) -> None:
        # Stakes 0.72 escalates under the default 0.7 threshold but not under 0.9.
        strict = NormRouter()
        lax = NormRouter(escalate_stakes=0.9, confirm_stakes=0.9)
        assessment = _assessment(0.72)
        self.assertEqual(
            strict.route(_SCENARIO, assessment).disposition, Disposition.ESCALATE
        )
        self.assertEqual(lax.route(_SCENARIO, assessment).disposition, Disposition.AUTO)

    def test_defaults_unchanged(self) -> None:
        # A high-stakes action still escalates with default thresholds.
        self.assertEqual(
            NormRouter().route(_SCENARIO, _assessment(0.8)).disposition,
            Disposition.ESCALATE,
        )


class TestSweep(unittest.TestCase):
    def test_sweep_traces_a_curve_that_dominates_hard_rules(self) -> None:
        data = run_sweep()
        self.assertGreaterEqual(len(data["points"]), 8)
        # Friction should fall monotonically-ish as thresholds relax (lax end < cautious).
        self.assertLess(data["points"][-1].friction, data["points"][0].friction)
        # At least one operating point dominates the hard-rules baseline.
        self.assertTrue(data["dominators"])

    def test_pareto_figure_is_valid(self) -> None:
        data = run_sweep()
        svg = figures.pareto_frontier(
            "Sweep",
            curve=[(p.friction, p.unsafe) for p in data["points"]],
            references=[figures.ScatterPoint(*data["hard_point"], "hard_rules")],
            x_label="friction",
            y_label="unsafe",
        )
        ET.fromstring(svg)


if __name__ == "__main__":
    unittest.main()
