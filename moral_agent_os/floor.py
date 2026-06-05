"""Thin hard-rule floor for legal, safety, and irreversible actions."""

from __future__ import annotations

from moral_agent_os.schema import Scenario


class ConstitutionFloor:
    """Detect non-negotiable action constraints.

    The floor is intentionally narrow. It catches actions where the product
    should not rely on contextual appropriateness alone.
    """

    _privacy_terms = (
        "api key",
        "secret",
        "password",
        "token",
        "customer data",
        "health info",
        "compensation",
        "ssn",
    )
    _external_terms = ("external", "customer", "investor", "candidate", "vendor")
    _destructive_terms = ("delete", "drop", "wipe", "remove prod", "production config")

    def check(self, scenario: Scenario) -> tuple[str, ...]:
        text = f"{scenario.action_text} {scenario.context}".lower()
        violations: list[str] = []

        if any(term in text for term in self._privacy_terms) and any(
            term in text for term in self._external_terms
        ):
            violations.append("privacy_or_confidentiality_leak")

        if any(term in text for term in self._destructive_terms) and (
            "prod" in text or "production" in text or "main branch" in text
        ):
            violations.append("irreversible_or_production_destructive_action")

        if "legal hold" in text or "regulated" in text:
            violations.append("regulated_or_legal_review_required")

        return tuple(violations)
