"""Example: guard an email-sending tool with Moral Agent OS."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from moral_agent_os import (  # noqa: E402
    ActionProposal,
    ContextSnapshot,
    MoralAgentOS,
    MoralRoute,
    RelationshipState,
    Stakeholder,
)


def send_email(to: str, subject: str, body: str) -> str:
    return f"sent email to {to}: {subject}"


def guarded_send_email(to: str, subject: str, body: str) -> str:
    runtime = MoralAgentOS()
    decision = runtime.assess(
        ActionProposal(
            id="email_customer_commitment",
            action_type="send_email",
            description=f"Email {to} about: {subject}. Body: {body}",
            params={"to": to, "subject": subject},
        ),
        ContextSnapshot(
            agent_role="customer-success assistant",
            user_intent="The customer depends on this migration timeline.",
            situation="external customer communication",
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

    if decision.route == MoralRoute.ALLOW:
        return send_email(to, subject, body)
    if decision.route == MoralRoute.CONFIRM:
        return f"needs user confirmation: {decision.reason}"
    if decision.route == MoralRoute.ALTERNATIVES:
        return f"present alternatives: {', '.join(decision.norm_conflicts)}"
    if decision.route == MoralRoute.ESCALATE:
        return f"needs accountable review: {decision.reason}"
    return f"blocked: {decision.reason}"


if __name__ == "__main__":
    print(
        guarded_send_email(
            to="customer@example.com",
            subject="Migration launch timeline",
            body="We can definitely complete the migration by Friday.",
        )
    )
