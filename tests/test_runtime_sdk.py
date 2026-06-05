from __future__ import annotations

import unittest

from ai_safety_os import (
    ActionProposal,
    ContextSnapshot,
    MoralAgentOS,
    MoralRoute,
    RelationshipState,
    Stakeholder,
    WorkspaceMemory,
)
from ai_safety_os.schema import Disposition


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
                description=(
                    "Send customer data and confidential contract terms to an "
                    "external vendor."
                ),
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
        self.assertGreaterEqual(len(decision.alternatives), 2)
        self.assertTrue(decision.alternatives[0].interpretation)
        self.assertTrue(decision.alternatives[0].recommended_action)

    def test_memory_override_applies_to_sdk_assess(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)
        action = ActionProposal(
            id="send_internal_note",
            action_type="send_email",
            description="Send a routine internal status note.",
            params={"recipient": "team"},
        )
        context = ContextSnapshot(
            agent_role="workspace assistant",
            user_intent="Send a routine internal status note.",
            situation="internal status update",
            stakes=0.55,
            reversibility=0.80,
        )

        before = runtime.assess(action, context)
        scenario = runtime._scenario_from_action(action, context)
        memory.record_correction(scenario, Disposition.AUTO)
        after = runtime.assess(action, context)

        self.assertEqual(before.route, MoralRoute.CONFIRM)
        self.assertEqual(after.route, MoralRoute.ALLOW)
        self.assertEqual(after.trace["memory_override"], "confirm_to_auto")

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

    def test_high_stakes_escalation_requires_review_flag(self) -> None:
        decision = self.runtime.assess(
            ActionProposal(
                id="external_commitment",
                action_type="send_email",
                description="Email an external investor a commitment.",
            ),
            ContextSnapshot(
                agent_role="workspace assistant",
                user_intent="Commit externally on the user's behalf.",
                stakes=0.85,
                reversibility=0.10,
            ),
        )

        self.assertEqual(decision.route, MoralRoute.ESCALATE)
        self.assertTrue(decision.required_review)

    def test_guard_tool_executes_allowed_action(self) -> None:
        calls: list[str] = []

        @self.runtime.guard_tool(
            context=ContextSnapshot(
                agent_role="workspace assistant",
                user_intent="The user asked for a private draft.",
                stakes=0.20,
                reversibility=0.95,
            )
        )
        def draft_note(title: str) -> str:
            calls.append(title)
            return f"drafted {title}"

        result = draft_note("weekly plan")

        self.assertTrue(result.executed)
        self.assertEqual(result.result, "drafted weekly plan")
        self.assertEqual(calls, ["weekly plan"])
        self.assertEqual(result.decision.route, MoralRoute.ALLOW)

    def test_guard_tool_pauses_review_required_action(self) -> None:
        calls: list[str] = []

        def proposal_builder(to: str, subject: str) -> ActionProposal:
            return ActionProposal(
                id="customer_commitment",
                action_type="send_email",
                description=f"Email {to} about {subject}.",
            )

        def context_builder(to: str, subject: str) -> ContextSnapshot:
            return ContextSnapshot(
                agent_role="customer-success assistant",
                user_intent="The customer depends on this commitment.",
                stakeholders=(Stakeholder(name="customer", dependency=0.90),),
                relationships=(
                    RelationshipState(
                        stakeholder="customer",
                        dependency=0.90,
                        public_review_required=True,
                    ),
                ),
                stakes=0.60,
                public_review_available=True,
            )

        @self.runtime.guard_tool(
            proposal_builder=proposal_builder,
            context_builder=context_builder,
        )
        def send_email(to: str, subject: str) -> str:
            calls.append(to)
            return "sent"

        result = send_email("customer@example.com", "launch timeline")

        self.assertFalse(result.executed)
        self.assertIsNone(result.result)
        self.assertEqual(calls, [])
        self.assertEqual(result.decision.route, MoralRoute.ESCALATE)
        self.assertIn("accountable review", result.message)

    def test_guard_tool_default_proposal_includes_safe_params(self) -> None:
        @self.runtime.guard_tool(
            action_type="draft_doc",
            context=ContextSnapshot(
                agent_role="workspace assistant",
                user_intent="The user asked for an internal draft.",
                stakes=0.20,
                reversibility=0.95,
            ),
        )
        def draft_doc(title: str, private: bool) -> str:
            return f"{title}:{private}"

        result = draft_doc("internal recap", True)

        self.assertTrue(result.executed)
        self.assertEqual(result.decision.trace["action_type"], "draft_doc")


if __name__ == "__main__":
    unittest.main()
