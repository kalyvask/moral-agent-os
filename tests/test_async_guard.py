"""Async tool guarding: the same gate, interdependence loop, and audit on async tools."""

from __future__ import annotations

import asyncio
import unittest

from ai_safety_os import MoralAgentOS, WorkspaceMemory
from ai_safety_os.schema import ActionProposal, ContextSnapshot, MoralRoute, Stakeholder


def _ctx(situation: str, **overrides) -> ContextSnapshot:
    base = dict(
        agent_role="operations agent",
        user_intent="serve the account",
        situation=situation,
        stakeholders=(Stakeholder(name="acme"),),
    )
    base.update(overrides)
    return ContextSnapshot(**base)


class AsyncGuardToolTest(unittest.TestCase):
    def test_allowed_async_tool_executes_and_records_cooperation(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)

        @runtime.guard_tool(
            context=_ctx("status update", stakes=0.1, reversibility=1.0),
            proposal_builder=lambda *a, **k: ActionProposal(
                id="note", action_type="note", description="share a quick status note"
            ),
        )
        async def send_note() -> str:
            await asyncio.sleep(0)
            return "sent"

        result = asyncio.run(send_note())
        self.assertTrue(result.executed)
        self.assertEqual(result.result, "sent")
        self.assertGreater(memory.relationship("acme").trust, 0.5)

    def test_blocked_async_tool_never_runs_and_sanctions(self) -> None:
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)
        ran: list[str] = []

        @runtime.guard_tool(
            context=_ctx("production"),
            proposal_builder=lambda *a, **k: ActionProposal(
                id="violation",
                action_type="delete",
                description="delete the production database",
            ),
        )
        async def drop_db() -> str:
            ran.append("ran")
            return "dropped"

        result = asyncio.run(drop_db())
        self.assertFalse(result.executed)
        self.assertEqual(result.decision.route, MoralRoute.BLOCK)
        self.assertEqual(ran, [])  # the coroutine body never executed
        self.assertGreater(memory.relationship("acme").repair_obligation, 0.0)


if __name__ == "__main__":
    unittest.main()
