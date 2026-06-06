"""Thin hard-rule floor for legal, safety, and irreversible actions."""

from __future__ import annotations

import re

from ai_safety_os.schema import Scenario


class ConstitutionFloor:
    """Detect non-negotiable action constraints.

    The floor is intentionally narrow. It catches actions where the product
    should not rely on contextual appropriateness alone.
    """

    _privacy_terms = (
        "api key",
        "board deck",
        "confidential",
        "secret",
        "password",
        "private doc",
        "roadmap",
        "token",
        "customer data",
        "customer contract",
        "health info",
        "compensation",
        "ssn",
    )
    _external_terms = ("external", "investor", "candidate", "vendor", "public")
    _destructive_terms = ("delete", "drop", "wipe", "remove prod", "production config")

    def check(self, scenario: Scenario) -> tuple[str, ...]:
        text = f"{scenario.action_text} {scenario.context}".lower()
        violations: list[str] = []

        if self._has_any(text, self._privacy_terms) and self._has_any(
            text, self._external_terms
        ):
            violations.append("privacy_or_confidentiality_leak")

        if self._has_any(text, self._destructive_terms) and self._has_any(
            text, ("prod", "production", "main branch")
        ):
            violations.append("irreversible_or_production_destructive_action")

        if self._has_any(text, ("legal hold", "regulated")):
            violations.append("regulated_or_legal_review_required")

        return tuple(violations)

    @staticmethod
    def _has_any(text: str, terms: tuple[str, ...]) -> bool:
        return any(ConstitutionFloor._has_phrase(text, term) for term in terms)

    @staticmethod
    def _has_phrase(text: str, phrase: str) -> bool:
        escaped = re.escape(phrase)
        pattern = rf"(?<![a-z0-9_]){escaped}(?![a-z0-9_])"
        return re.search(pattern, text) is not None
