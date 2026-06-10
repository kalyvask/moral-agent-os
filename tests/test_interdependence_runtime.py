"""Runtime interdependence loop: outcomes update standing, trust modulates routing.

These cover the live-runtime half of the thesis (interdependence as behavior, not only a
benchmark): a caught violation lowers an agent's standing with a counterparty, clean action
rebuilds it, and trust both tightens and (conservatively) relaxes routing.
"""

from __future__ import annotations

import unittest

from ai_safety_os import MoralAgentOS, WorkspaceMemory
from ai_safety_os.schema import (
    ActionProposal,
    ContextSnapshot,
    MoralRoute,
    RelationshipState,
    Stakeholder,
)

CUSTOMER = (Stakeholder(name="acme"),)


def _ctx(**overrides) -> ContextSnapshot:
    base = dict(
        agent_role="operations agent",
        user_intent="do the work",
        situation="workspace",
        stakeholders=CUSTOMER,
    )
    base.update(overrides)
    return ContextSnapshot(**base)


def _routine_action() -> ActionProposal:
    return ActionProposal(id="routine", action_type="note", description="share a quick status note")


def _violation_action() -> ActionProposal:
    return ActionProposal(
        id="violation", action_type="delete", description="delete the production database"
    )


class RuntimeInterdependenceTest(unittest.TestCase):
    # ----------------------------------------------------------------- piece 1: outcomes

    def test_block_sanctions_counterparty(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)
        decision = runtime.assess(_violation_action(), _ctx(situation="production"))
        self.assertEqual(decision.route, MoralRoute.BLOCK)

        runtime.observe_outcome(decision, _ctx(situation="production"), executed=False)
        rel = memory.relationship("acme")
        self.assertGreater(rel.repair_obligation, 0.0)
        self.assertLess(rel.trust, 0.5)

    def test_clean_execution_records_cooperation_and_pays_down_debt(self) -> None:
        memory = WorkspaceMemory()
        memory.observe_sanction("acme", severity=0.6)  # start in debt
        before = memory.relationship("acme")
        runtime = MoralAgentOS(memory=memory)

        decision = runtime.assess(_routine_action(), _ctx(stakes=0.1, reversibility=1.0))
        runtime.observe_outcome(decision, _ctx(stakes=0.1, reversibility=1.0), executed=True)

        after = memory.relationship("acme")
        self.assertLess(after.repair_obligation, before.repair_obligation)
        self.assertGreater(after.trust, before.trust)

    def test_frozen_control_does_not_learn(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory, learn_from_outcomes=False)
        decision = runtime.assess(_violation_action(), _ctx(situation="production"))
        runtime.observe_outcome(decision, _ctx(situation="production"), executed=False)

        rel = memory.relationship("acme")
        self.assertEqual(rel.repair_obligation, 0.0)
        self.assertEqual(rel.trust, 0.5)

    # ----------------------------------------------------------------- piece 2: trust gate

    def test_low_trust_tightens_routing(self) -> None:
        memory = WorkspaceMemory()
        memory.upsert_relationship(RelationshipState(stakeholder="acme", trust=0.2))
        runtime = MoralAgentOS(memory=memory)

        decision = runtime.assess(_routine_action(), _ctx(stakes=0.1, reversibility=1.0))
        self.assertEqual(decision.route, MoralRoute.CONFIRM)
        self.assertTrue(any("low_trust" in update for update in decision.state_updates))

    def test_high_trust_earns_auto_on_routine_action(self) -> None:
        action = ActionProposal(
            id="commit", action_type="reply", description="promise a quick follow-up"
        )

        # Default trust: a mild role-authority confirm stands.
        base = MoralAgentOS(memory=WorkspaceMemory())
        self.assertEqual(base.assess(action, _ctx()).route, MoralRoute.CONFIRM)

        # Established trust earns auto-approval on the same routine action.
        trusted = WorkspaceMemory()
        trusted.upsert_relationship(RelationshipState(stakeholder="acme", trust=0.9))
        runtime = MoralAgentOS(memory=trusted)
        decision = runtime.assess(action, _ctx())
        self.assertEqual(decision.route, MoralRoute.ALLOW)
        self.assertTrue(any("trusted_auto" in update for update in decision.state_updates))

    def test_trust_never_relaxes_a_flagged_action(self) -> None:
        trusted = WorkspaceMemory()
        trusted.upsert_relationship(RelationshipState(stakeholder="acme", trust=0.95))
        runtime = MoralAgentOS(memory=trusted)

        # A floor violation stays blocked no matter how trusted the counterparty is.
        blocked = runtime.assess(_violation_action(), _ctx(situation="production"))
        self.assertEqual(blocked.route, MoralRoute.BLOCK)

        # A high-stakes confirm is not relaxed either (earned autonomy is routine-only).
        high_stakes = runtime.assess(_routine_action(), _ctx(stakes=0.6, reversibility=1.0))
        self.assertEqual(high_stakes.route, MoralRoute.CONFIRM)

    # --------------------------------------------------------- end-to-end via guard_tool

    def test_guard_tool_closes_the_loop(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)

        @runtime.guard_tool(
            context=_ctx(situation="production"),
            proposal_builder=lambda *a, **k: _violation_action(),
        )
        def drop_db() -> str:
            return "dropped"

        result = drop_db()
        self.assertFalse(result.executed)
        self.assertEqual(result.decision.route, MoralRoute.BLOCK)
        # The blocked attempt left the agent owing repair to the counterparty.
        self.assertGreater(memory.relationship("acme").repair_obligation, 0.0)


if __name__ == "__main__":
    unittest.main()
