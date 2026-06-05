"""Tests for the framework adapters (run without any framework installed)."""

from __future__ import annotations

import unittest

from adapters import (
    decision_message,
    guard_autogen_tool,
    guard_callable,
    guard_crewai_tool,
    guard_langchain_tool,
    guard_openai_tool,
)
from moral_agent_os import ContextSnapshot, MoralAgentOS, MoralRoute


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"SENT:{to}"


INTERNAL = ContextSnapshot(
    agent_role="workspace assistant",
    user_intent="Send an internal note.",
    stakes=0.2,
    reversibility=0.9,
)
EXTERNAL = ContextSnapshot(
    agent_role="workspace assistant",
    user_intent="Send an external commitment.",
    stakes=0.85,
    reversibility=0.1,
)


class TestGuardCallable(unittest.TestCase):
    def test_executes_when_allowed(self) -> None:
        runtime = MoralAgentOS()
        guarded = guard_callable(runtime, send_email, action_type="send_email",
                                 context=INTERNAL)
        self.assertEqual(guarded("a@x.com", "s", "b"), "SENT:a@x.com")

    def test_returns_message_when_blocked(self) -> None:
        runtime = MoralAgentOS()
        guarded = guard_callable(runtime, send_email, action_type="send_email",
                                 context=EXTERNAL)
        result = guarded("inv@vc.com", "s", "b")
        self.assertIn("[Moral Agent OS]", result)
        self.assertIn("escalate", result)

    def test_context_builder_receives_args(self) -> None:
        seen = {}

        def builder(to, subject, body):
            seen["to"] = to
            return INTERNAL

        runtime = MoralAgentOS()
        guarded = guard_callable(runtime, send_email, action_type="send_email",
                                 context=builder)
        guarded("a@x.com", "s", "b")
        self.assertEqual(seen["to"], "a@x.com")

    def test_on_decision_hook_fires(self) -> None:
        decisions = []
        runtime = MoralAgentOS()
        guarded = guard_callable(runtime, send_email, action_type="send_email",
                                 context=EXTERNAL, on_decision=decisions.append)
        guarded("inv@vc.com", "s", "b")
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].route, MoralRoute.ESCALATE)

    def test_execute_routes_can_widen(self) -> None:
        # Allowing CONFIRM to execute means a medium-uncertainty action runs anyway.
        runtime = MoralAgentOS()
        ctx = ContextSnapshot(
            agent_role="workspace assistant",
            user_intent="Send.",
            stakes=0.55,  # routes to confirm
            reversibility=0.6,
        )
        blocked = guard_callable(runtime, send_email, action_type="send_email", context=ctx)
        self.assertIn("[Moral Agent OS]", blocked("a@x.com", "s", "b"))
        allowed = guard_callable(
            runtime, send_email, action_type="send_email", context=ctx,
            execute_routes=(MoralRoute.ALLOW, MoralRoute.CONFIRM),
        )
        self.assertEqual(allowed("a@x.com", "s", "b"), "SENT:a@x.com")


class TestFrameworkAdaptersFallback(unittest.TestCase):
    def test_each_adapter_returns_a_working_gate(self) -> None:
        runtime = MoralAgentOS()
        for adapter in (
            guard_langchain_tool,
            guard_crewai_tool,
            guard_autogen_tool,
            guard_openai_tool,
        ):
            tool = adapter(runtime, send_email, context=INTERNAL, action_type="send_email")
            # Frameworks absent -> guarded callable; it must gate correctly.
            self.assertTrue(callable(tool))
            self.assertEqual(tool("a@x.com", "s", "b"), "SENT:a@x.com")


class TestDecisionMessage(unittest.TestCase):
    def test_includes_route_and_reason(self) -> None:
        runtime = MoralAgentOS()
        decisions = []
        guard_callable(runtime, send_email, action_type="send_email", context=EXTERNAL,
                       on_decision=decisions.append)("inv@vc.com", "s", "b")
        message = decision_message(decisions[0])
        self.assertIn("route=escalate", message)
        self.assertIn("Reason:", message)


if __name__ == "__main__":
    unittest.main()
