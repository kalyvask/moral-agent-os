"""Pluralism surface for genuine norm conflicts."""

from __future__ import annotations

from ai_safety_os.schema import KaleidoscopeOption, Scenario


class Kaleidoscope:
    def options_for(self, scenario: Scenario) -> tuple[KaleidoscopeOption, ...]:
        text = f"{scenario.action_text} {scenario.context}".lower()

        if "refund" in text:
            return (
                KaleidoscopeOption(
                    name="Customer trust",
                    interpretation="Prioritize repair and relationship quality.",
                    recommended_action="Offer the refund with a note explaining the exception.",
                ),
                KaleidoscopeOption(
                    name="Policy consistency",
                    interpretation="Avoid setting an unsupported precedent.",
                    recommended_action="Deny the refund but offer a lower-risk make-good.",
                ),
                KaleidoscopeOption(
                    name="Accountable escalation",
                    interpretation="The agent lacks authority to decide the exception.",
                    recommended_action="Escalate to a manager with the trade-off summarized.",
                ),
            )

        if "loop in" in text or "escalate" in text:
            return (
                KaleidoscopeOption(
                    name="Direct ownership",
                    interpretation="Keep the thread small and let the agent resolve the task.",
                    recommended_action="Proceed only if the action is reversible and low stakes.",
                ),
                KaleidoscopeOption(
                    name="Shared accountability",
                    interpretation="Bring in the person who owns the affected relationship.",
                    recommended_action="Ask whether to include the accountable owner.",
                ),
            )

        return (
            KaleidoscopeOption(
                name="User-intent view",
                interpretation="Follow the user's immediate instruction.",
                recommended_action="Proceed after confirmation.",
            ),
            KaleidoscopeOption(
                name="Role-integrity view",
                interpretation="Constrain the agent to what someone in its role should do.",
                recommended_action="Ask for a human decision or narrower instruction.",
            ),
        )
