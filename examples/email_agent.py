"""Example: guard an email-sending tool with Moral Agent OS."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from moral_agent_os import (  # noqa: E402
    ActionProposal,
    ContextSnapshot,
    MoralAgentOS,
    RelationshipState,
    Stakeholder,
)

runtime = MoralAgentOS()


def email_action(to: str, subject: str, body: str) -> ActionProposal:
    return ActionProposal(
        id="email_customer_commitment",
        action_type="send_email",
        description=f"Email {to} about: {subject}. Body: {body}",
        params={"to": to, "subject": subject},
    )


def email_context(to: str, subject: str, body: str) -> ContextSnapshot:
    return ContextSnapshot(
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
    )


@runtime.guard_tool(proposal_builder=email_action, context_builder=email_context)
def send_email(to: str, subject: str, body: str) -> str:
    return f"sent email to {to}: {subject}"


if __name__ == "__main__":
    guarded = send_email(
        to="customer@example.com",
        subject="Migration launch timeline",
        body="We can definitely complete the migration by Friday.",
    )
    print(f"executed={guarded.executed}")
    print(f"route={guarded.decision.route.value}")
    print(guarded.message)
