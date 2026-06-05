"""Routing logic from assessment to UI disposition."""

from __future__ import annotations

from moral_agent_os.kaleidoscope import Kaleidoscope
from moral_agent_os.schema import ContextAssessment, Disposition, RouteDecision, Scenario


class NormRouter:
    def __init__(self, kaleidoscope: Kaleidoscope | None = None) -> None:
        self.kaleidoscope = kaleidoscope or Kaleidoscope()

    def route(self, scenario: Scenario, assessment: ContextAssessment) -> RouteDecision:
        if assessment.floor_violations:
            severe = any(
                violation
                in {
                    "privacy_or_confidentiality_leak",
                    "irreversible_or_production_destructive_action",
                }
                for violation in assessment.floor_violations
            )
            disposition = Disposition.BLOCK if severe else Disposition.ESCALATE
            return RouteDecision(
                disposition=disposition,
                rationale=(
                    "Thin safety floor triggered: "
                    + ", ".join(assessment.floor_violations)
                ),
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if assessment.reward_hacking_signals and assessment.stakes >= 0.45:
            return RouteDecision(
                disposition=Disposition.ESCALATE,
                rationale=(
                    "Possible reward hacking detected: "
                    + ", ".join(assessment.reward_hacking_signals)
                ),
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if assessment.norm_conflict >= 0.7:
            return RouteDecision(
                disposition=Disposition.PRESENT_OPTIONS,
                rationale="Genuine norm conflict; present multiple reasonable interpretations.",
                assessment=assessment,
                options=self.kaleidoscope.options_for(scenario),
                trace=self._trace(assessment),
            )

        if assessment.is_high_stakes or assessment.is_irreversible:
            return RouteDecision(
                disposition=Disposition.ESCALATE,
                rationale="High stakes or low reversibility requires an accountable human.",
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if (
            assessment.confidence < 0.75
            or assessment.stakes > 0.5
            or assessment.role_authority < 0.55
        ):
            return RouteDecision(
                disposition=Disposition.CONFIRM,
                rationale="Moderate uncertainty or authority gap; ask before acting.",
                assessment=assessment,
                trace=self._trace(assessment),
            )

        return RouteDecision(
            disposition=Disposition.AUTO,
            rationale="Low stakes, reversible, familiar norm, and sufficient confidence.",
            assessment=assessment,
            trace=self._trace(assessment),
        )

    @staticmethod
    def _trace(assessment: ContextAssessment) -> dict[str, float | str | list[str]]:
        return {
            "situation": assessment.situation,
            "role_authority": assessment.role_authority,
            "stakes": assessment.stakes,
            "reversibility": assessment.reversibility,
            "privacy_sensitivity": assessment.privacy_sensitivity,
            "norm_conflict": assessment.norm_conflict,
            "confidence": assessment.confidence,
            "stakeholders": list(assessment.stakeholders),
        }
