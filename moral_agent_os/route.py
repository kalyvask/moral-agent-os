"""Routing logic from assessment to UI disposition."""

from __future__ import annotations

from moral_agent_os.kaleidoscope import Kaleidoscope
from moral_agent_os.schema import ContextAssessment, Disposition, RouteDecision, Scenario


class NormRouter:
    """Maps an assessment to a UI disposition.

    The decision thresholds are constructor parameters (defaults reproduce the original
    behavior) so the safety/friction frontier can be swept into a full Pareto curve rather
    than a single operating point. The floor, reward-hacking, and norm-conflict rules are
    not swept: the hard floor is non-negotiable by design.
    """

    def __init__(
        self,
        kaleidoscope: Kaleidoscope | None = None,
        *,
        escalate_stakes: float = 0.7,
        escalate_reversibility: float = 0.25,
        norm_conflict_threshold: float = 0.7,
        reward_hacking_stakes: float = 0.45,
        confirm_confidence: float = 0.75,
        confirm_stakes: float = 0.5,
        confirm_role_authority: float = 0.55,
        universalizability_floor: float = 0.0,
    ) -> None:
        self.kaleidoscope = kaleidoscope or Kaleidoscope()
        self.escalate_stakes = escalate_stakes
        self.escalate_reversibility = escalate_reversibility
        self.norm_conflict_threshold = norm_conflict_threshold
        self.reward_hacking_stakes = reward_hacking_stakes
        self.confirm_confidence = confirm_confidence
        self.confirm_stakes = confirm_stakes
        self.confirm_role_authority = confirm_role_authority
        # Kantian gate, off by default (0.0): when set above 0, an action the assessor judges
        # non-universalizable is escalated even if its stakes look low, because gaming and
        # deception read as low-stakes to the other axes. Off by default so it does not
        # silently change the reported baselines; turn it on to evaluate the Kantian lens.
        self.universalizability_floor = universalizability_floor

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

        if assessment.reward_hacking_signals and assessment.stakes >= self.reward_hacking_stakes:
            return RouteDecision(
                disposition=Disposition.ESCALATE,
                rationale=(
                    "Possible reward hacking detected: "
                    + ", ".join(assessment.reward_hacking_signals)
                ),
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if assessment.universalizability < self.universalizability_floor:
            return RouteDecision(
                disposition=Disposition.ESCALATE,
                rationale=(
                    "Not universalizable: this would undermine the norm if every agent in "
                    "this role did it by default."
                ),
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if assessment.norm_conflict >= self.norm_conflict_threshold:
            return RouteDecision(
                disposition=Disposition.PRESENT_OPTIONS,
                rationale="Genuine norm conflict; present multiple reasonable interpretations.",
                assessment=assessment,
                options=self.kaleidoscope.options_for(scenario),
                trace=self._trace(assessment),
            )

        if (
            assessment.stakes >= self.escalate_stakes
            or assessment.reversibility <= self.escalate_reversibility
        ):
            return RouteDecision(
                disposition=Disposition.ESCALATE,
                rationale="High stakes or low reversibility requires an accountable human.",
                assessment=assessment,
                trace=self._trace(assessment),
            )

        if (
            assessment.confidence < self.confirm_confidence
            or assessment.stakes > self.confirm_stakes
            or assessment.role_authority < self.confirm_role_authority
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
            "universalizability": assessment.universalizability,
            "stakeholders": list(assessment.stakeholders),
        }
