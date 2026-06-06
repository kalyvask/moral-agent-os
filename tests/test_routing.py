from __future__ import annotations

import unittest

from ai_safety_os import Disposition, HeuristicAssessor, MoralAgentOS
from ai_safety_os.schema import Scenario, ScenarioLabel
from bench.arms import HighRiskPolicyArm
from bench.metrics import summarize
from bench.run import load_scenarios


class RoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = MoralAgentOS()
        self.scenarios = {scenario.id: scenario for scenario in load_scenarios()}

    def test_blocks_production_destructive_action(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["delete_prod_config_bad"])
        self.assertEqual(decision.disposition, Disposition.BLOCK)

    def test_surfaces_plural_options(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["refund_policy_plural"])
        self.assertEqual(decision.disposition, Disposition.PRESENT_OPTIONS)
        self.assertGreaterEqual(len(decision.options), 2)

    def test_allows_clear_low_risk_action(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["delete_scratch_file_ok"])
        self.assertEqual(decision.disposition, Disposition.AUTO)

    def test_product_does_not_trigger_prod_keyword(self) -> None:
        assessment = HeuristicAssessor().assess(self.scenarios["update_contract_test_ok"])
        self.assertLess(assessment.stakes, 0.5)
        decision = self.runtime.evaluate(self.scenarios["update_contract_test_ok"])
        self.assertEqual(decision.disposition, Disposition.AUTO)

    def test_accountable_internal_owner_can_handle_sensitive_doc(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["forward_contract_to_legal_ok"])
        self.assertEqual(decision.disposition, Disposition.AUTO)

    def test_interdependence_lens_catches_release_branch_dependency(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["twin_push_shared_bad"])
        self.assertNotEqual(decision.disposition, Disposition.AUTO)

    def test_large_audience_externality_is_not_silent(self) -> None:
        decision = self.runtime.evaluate(self.scenarios["twin_reply_all_bad"])
        self.assertNotEqual(decision.disposition, Disposition.AUTO)

    def test_high_risk_policy_baseline_escalates_sensitive_external_action(self) -> None:
        result = HighRiskPolicyArm().run(self.scenarios["share_board_deck_bad"])
        self.assertIn(result.disposition, {Disposition.ESCALATE, Disposition.BLOCK})

    def test_expected_label_does_not_drive_routing(self) -> None:
        original = self.scenarios["refund_policy_plural"]
        relabeled = Scenario(
            id="relabeled_refund_policy",
            action_family=original.action_family,
            action_text=original.action_text,
            context=original.context,
            agent_role=original.agent_role,
            expected_label=ScenarioLabel.CLEAR_APPROPRIATE,
            notes=original.notes,
        )

        original_decision = self.runtime.evaluate(original)
        relabeled_decision = self.runtime.evaluate(relabeled)

        self.assertEqual(original_decision.disposition, relabeled_decision.disposition)

    def test_metrics_include_primary_rates(self) -> None:
        results = [
            type(
                "Result",
                (),
                {
                    "expected_label": ScenarioLabel.CLEAR_INAPPROPRIATE,
                    "disposition": Disposition.AUTO,
                },
            )()
        ]
        summary = summarize(results)
        self.assertIn("context_inappropriate_auto_rate", summary)


if __name__ == "__main__":
    unittest.main()
