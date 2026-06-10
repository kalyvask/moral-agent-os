"""The decision audit log: every SDK assessment is recorded and queryable."""

from __future__ import annotations

import unittest

from ai_safety_os import MoralAgentOS, WorkspaceMemory
from ai_safety_os.schema import ActionProposal, ContextSnapshot, MoralRoute, Stakeholder


def _ctx(situation: str = "workspace") -> ContextSnapshot:
    return ContextSnapshot(
        agent_role="operations agent",
        user_intent="do the work",
        situation=situation,
        stakeholders=(Stakeholder(name="acme"),),
    )


class DecisionLogTest(unittest.TestCase):
    def test_assess_appends_to_the_audit_log(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)

        allowed = runtime.assess(
            ActionProposal(id="note-1", action_type="note", description="share a status note"),
            _ctx(),
        )
        blocked = runtime.assess(
            ActionProposal(
                id="violation-1",
                action_type="delete",
                description="delete the production database",
            ),
            _ctx("production"),
        )
        self.assertEqual(blocked.route, MoralRoute.BLOCK)

        log = memory.decision_log()
        self.assertEqual(len(log), 2)
        # Newest first; every entry carries route, reason, stakeholders, and the score trace.
        self.assertEqual(log[0].action_id, "violation-1")
        self.assertEqual(log[0].route, MoralRoute.BLOCK.value)
        self.assertEqual(log[1].action_id, "note-1")
        self.assertEqual(log[1].route, allowed.route.value)
        for record in log:
            self.assertIn("stakes", record.trace)
            self.assertIn("acme", record.stakeholders)
            self.assertTrue(record.reason)

    def test_frozen_memory_still_audits(self) -> None:
        memory = WorkspaceMemory(frozen=True)
        runtime = MoralAgentOS(memory=memory, learn_from_outcomes=False)
        runtime.assess(
            ActionProposal(id="note-2", action_type="note", description="share a status note"),
            _ctx(),
        )
        # The audit trail is observation, not learning: the frozen control records too.
        self.assertEqual(len(memory.decision_log()), 1)

    def test_default_memory_without_audit_support_is_fine(self) -> None:
        runtime = MoralAgentOS()  # LocalNormMemory has no decision log; assess must not fail
        decision = runtime.assess(
            ActionProposal(id="note-3", action_type="note", description="share a status note"),
            _ctx(),
        )
        self.assertIn(decision.route, set(MoralRoute))


if __name__ == "__main__":
    unittest.main()
