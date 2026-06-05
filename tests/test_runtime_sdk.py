from __future__ import annotations

import unittest

from moral_agent_os import (
    ActionProposal,
    ContextSnapshot,
    MoralAgentOS,
    MoralRoute,
    RelationshipState,
    Stakeholder,
)


class RuntimeSdkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = MoralAgentOS()

    def test_allows_low_risk_reversible_action(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="draft_internal_note",
                action_type="draft_doc",
                description="Draft an internal meeting note.",
            ),
            ContextSnapshot(
                agent_role="workspace assistant",
                user_intent="The user asked for a private draft.",
                situation="internal drafting",
                reversibility=0.95,
                stakes=0.20,
            ),
        )

        self.assertEqual(decision.route, MoralRoute.ALLOW)
        self.assertEqual(decision.stakes, "low")

    def test_blocks_privacy_leak(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="send_customer_data",
                action_type="send_email",
                description="Send customer data and confidential contract terms to an external vendor.",
            ),
            ContextSnapshot(
                agent_role="workspace assistant",
                user_intent="The user did not approve external disclosure.",
                situation="external communication",
                privacy_sensitivity=0.95,
            ),
        )

        self.assertEqual(decision.route, MoralRoute.BLOCK)

    def test_surfaces_norm_conflicts_as_alternatives(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="refund_edge_case",
                action_type="refund",
                description="Issue a refund even though the policy does not cover this edge case.",
            ),
            ContextSnapshot(
                agent_role="support assistant",
                user_intent="The customer had a confusing experience.",
                norm_conflicts=("policy consistency vs customer care",),
            ),
        )

        self.assertEqual(decision.route, MoralRoute.ALTERNATIVES)
        self.assertIn("policy consistency vs customer care", decision.norm_conflicts)

    def test_repair_obligation_prevents_silent_action(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="followup_customer",
                action_type="send_email",
                description="Send a friendly follow-up email to the customer.",
            ),
            ContextSnapshot(
                agent_role="support assistant",
                user_intent="The agent previously mishandled this customer thread.",
                relationships=(
                    RelationshipState(
                        stakeholder="customer",
                        trust=0.30,
                        repair_obligation=0.70,
                    ),
                ),
            ),
        )

        self.assertEqual(decision.route, MoralRoute.CONFIRM)
        self.assertIn("repair_obligation=0.70", decision.state_updates)

    def test_missing_joint_commitment_requires_confirmation(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="reschedule_team_plan",
                action_type="calendar",
                description="Move the team planning session.",
            ),
            ContextSnapshot(
                agent_role="calendar assistant",
                user_intent="The action affects a shared planning commitment.",
                relationships=(
                    RelationshipState(
                        stakeholder="team",
                        joint_commitment_required=True,
                        joint_commitment_present=False,
                    ),
                ),
            ),
        )

        self.assertEqual(decision.route, MoralRoute.CONFIRM)
        self.assertIn("joint_commitment_required", decision.state_updates)

    def test_public_review_escalates_dependent_stakeholder_action(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="email_customer_commitment",
                action_type="send_email",
                description="Email the customer with a commitment about their migration timeline.",
            ),
            ContextSnapshot(
                agent_role="customer-success assistant",
                user_intent="The customer depends on this timeline for their launch.",
                stakeholders=(
                    Stakeholder(
                        name="customer",
                        role="dependent customer",
                        dependency=0.90,
                    ),
                ),
                relationships=(
                    RelationshipState(
                        stakeholder="customer",
                        dependency=0.90,
                        public_review_required=True,
                    ),
                ),
                stakes=0.60,
                public_review_available=True,
            ),
        )

        self.assertEqual(decision.route, MoralRoute.ESCALATE)
        self.assertTrue(decision.required_review)
        self.assertIn("public_review_required", decision.state_updates)


if __name__ == "__main__":
    unittest.main()
