"""Tests for the Kantian universalizability dimension and router gate."""

from __future__ import annotations

import unittest

from ai_safety_os.route import NormRouter
from ai_safety_os.schema import ContextAssessment, Disposition, Scenario, ScenarioLabel

_SCENARIO = Scenario(
    id="s",
    action_family="support_ticket",
    action_text="a",
    context="b",
    agent_role="r",
    expected_label=ScenarioLabel.CLEAR_INAPPROPRIATE,
)


def _assessment(universalizability: float) -> ContextAssessment:
    # Low stakes on every other axis, so only universalizability can change the routing.
    return ContextAssessment(
        scenario_id="s",
        situation="x",
        role_authority=0.8,
        stakes=0.2,
        reversibility=0.9,
        privacy_sensitivity=0.0,
        norm_conflict=0.1,
        confidence=0.9,
        universalizability=universalizability,
    )


class TestUniversalizability(unittest.TestCase):
    def test_default_is_neutral(self) -> None:
        a = ContextAssessment(
            scenario_id="s", situation="x", role_authority=0.5, stakes=0.5,
            reversibility=0.5, privacy_sensitivity=0.5, norm_conflict=0.5, confidence=0.5,
        )
        self.assertEqual(a.universalizability, 0.5)
        self.assertFalse(a.is_low_universalizability)

    def test_low_universalizability_property(self) -> None:
        self.assertTrue(_assessment(0.1).is_low_universalizability)
        self.assertFalse(_assessment(0.6).is_low_universalizability)

    def test_gate_off_by_default(self) -> None:
        # With the floor at 0.0, even a 0.0 action is not escalated for universalizability:
        # routing is unchanged from before the feature existed.
        router = NormRouter()
        self.assertEqual(
            router.route(_SCENARIO, _assessment(0.0)).disposition, Disposition.AUTO
        )

    def test_gate_escalates_when_enabled(self) -> None:
        router = NormRouter(universalizability_floor=0.4)
        # A non-universalizable but otherwise low-stakes action now escalates.
        self.assertEqual(
            router.route(_SCENARIO, _assessment(0.2)).disposition, Disposition.ESCALATE
        )
        # A universalizable action still auto-executes.
        self.assertEqual(
            router.route(_SCENARIO, _assessment(0.9)).disposition, Disposition.AUTO
        )


def _patiency_assessment(patiency: float, salience: float) -> ContextAssessment:
    # Low on every other axis, so only patiency/salience can move the routing.
    return ContextAssessment(
        scenario_id="s", situation="x", role_authority=0.8, stakes=0.2, reversibility=0.9,
        privacy_sensitivity=0.0, norm_conflict=0.1, confidence=0.9,
        moral_patiency=patiency, affective_salience=salience,
    )


class TestPatiencyGate(unittest.TestCase):
    def test_endangers_vulnerable_patient_property(self) -> None:
        self.assertTrue(_patiency_assessment(0.8, 0.8).endangers_vulnerable_patient)
        self.assertFalse(_patiency_assessment(0.8, 0.4).endangers_vulnerable_patient)

    def test_gate_off_by_default(self) -> None:
        router = NormRouter()
        self.assertEqual(
            router.route(_SCENARIO, _patiency_assessment(1.0, 1.0)).disposition,
            Disposition.AUTO,
        )

    def test_gate_escalates_when_enabled(self) -> None:
        router = NormRouter(protect_patients=True)
        self.assertEqual(
            router.route(_SCENARIO, _patiency_assessment(0.9, 0.9)).disposition,
            Disposition.ESCALATE,
        )
        # An action with no exposed patient still auto-executes.
        self.assertEqual(
            router.route(_SCENARIO, _patiency_assessment(0.2, 0.2)).disposition,
            Disposition.AUTO,
        )


if __name__ == "__main__":
    unittest.main()
