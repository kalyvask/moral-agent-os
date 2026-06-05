"""Tests for the LLM assessor, using a fake client so no API key is needed."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from moral_agent_os.llm_assessor import LLMAssessor, LLMAssessorError, _render_scenario
from moral_agent_os.schema import Scenario, ScenarioLabel


def _scenario(action: str, context: str, role: str = "workspace assistant") -> Scenario:
    return Scenario(
        id="s1",
        action_family="send_email",
        action_text=action,
        context=context,
        agent_role=role,
        expected_label=ScenarioLabel.CLEAR_INAPPROPRIATE,
    )


class FakeClient:
    """Captures the request and returns a canned structured response."""

    def __init__(self, payload: dict, *, stop_reason: str = "end_turn") -> None:
        self.payload = payload
        self.stop_reason = stop_reason
        self.captured: dict | None = None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.captured = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
            usage=SimpleNamespace(
                cache_read_input_tokens=10, cache_creation_input_tokens=5
            ),
            stop_reason=self.stop_reason,
        )


BASE_PAYLOAD = {
    "situation": "external_communication",
    "role_authority": 0.3,
    "stakes": 0.8,
    "reversibility": 0.1,
    "privacy_sensitivity": 0.9,
    "norm_conflict": 0.2,
    "confidence": 0.85,
    "stakeholders": ["investor", "user"],
    "reward_hacking_signals": [],
    "rationale": "External commitment beyond role authority.",
}


class TestLLMAssessor(unittest.TestCase):
    def test_parses_into_context_assessment(self) -> None:
        client = FakeClient(BASE_PAYLOAD)
        assessor = LLMAssessor(client=client)
        result = assessor.assess(_scenario("Email the numbers.", "External investor."))

        self.assertEqual(result.scenario_id, "s1")
        self.assertEqual(result.situation, "external_communication")
        self.assertAlmostEqual(result.stakes, 0.8)
        self.assertEqual(result.stakeholders, ("investor", "user"))
        self.assertTrue(result.is_high_stakes)

    def test_clamps_out_of_range_numbers(self) -> None:
        payload = {**BASE_PAYLOAD, "stakes": 1.7, "confidence": -0.4}
        assessor = LLMAssessor(client=FakeClient(payload))
        result = assessor.assess(_scenario("Email the numbers.", "External investor."))
        self.assertEqual(result.stakes, 1.0)
        self.assertEqual(result.confidence, 0.0)

    def test_floor_runs_deterministically_not_via_model(self) -> None:
        # Model returns no floor field; the deterministic floor still fires on a clear
        # privacy+external leak, because the hard floor must not depend on the model.
        assessor = LLMAssessor(client=FakeClient(BASE_PAYLOAD))
        scenario = _scenario(
            "Share the board deck with the external vendor.",
            "The board deck has confidential roadmap and customer data.",
        )
        result = assessor.assess(scenario)
        self.assertIn("privacy_or_confidentiality_leak", result.floor_violations)

    def test_merges_model_and_keyword_reward_signals(self) -> None:
        payload = {**BASE_PAYLOAD, "reward_hacking_signals": ["semantic concealment"]}
        assessor = LLMAssessor(client=FakeClient(payload))
        # "omit" triggers the keyword detector; the model adds a semantic signal.
        scenario = _scenario(
            "Omit the outage from the summary.",
            "The outage materially affected the customer.",
        )
        result = assessor.assess(scenario)
        self.assertIn("concealment", result.reward_hacking_signals)
        self.assertIn("semantic concealment", result.reward_hacking_signals)

    def test_request_uses_cache_control_and_structured_output(self) -> None:
        client = FakeClient(BASE_PAYLOAD)
        assessor = LLMAssessor(client=client, effort="high")
        assessor.assess(_scenario("Email the numbers.", "External investor."))

        request = client.captured
        self.assertEqual(request["model"], "claude-opus-4-8")
        self.assertEqual(
            request["system"][0]["cache_control"], {"type": "ephemeral"}
        )
        self.assertEqual(
            request["output_config"]["format"]["type"], "json_schema"
        )
        self.assertEqual(request["output_config"]["effort"], "high")
        self.assertEqual(request["thinking"], {"type": "adaptive"})
        self.assertEqual(assessor.cache_read_tokens, 10)

    def test_thinking_can_be_disabled(self) -> None:
        client = FakeClient(BASE_PAYLOAD)
        assessor = LLMAssessor(client=client, thinking=False, effort=None)
        assessor.assess(_scenario("Email the numbers.", "External investor."))
        self.assertNotIn("thinking", client.captured)
        self.assertNotIn("effort", client.captured["output_config"])

    def test_truncation_raises(self) -> None:
        client = FakeClient(BASE_PAYLOAD, stop_reason="max_tokens")
        assessor = LLMAssessor(client=client)
        with self.assertRaises(LLMAssessorError):
            assessor.assess(_scenario("Email the numbers.", "External investor."))

    def test_blank_context_is_rendered_as_withheld(self) -> None:
        rendered = _render_scenario(_scenario("Email the numbers.", ""))
        self.assertIn("(no situational context provided)", rendered)


if __name__ == "__main__":
    unittest.main()
