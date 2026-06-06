"""Context assessment.

The current assessor is deterministic so the scaffold runs without API keys.
Future LLM assessors should emit the same ContextAssessment schema.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from ai_safety_os.floor import ConstitutionFloor
from ai_safety_os.reward_hacking import RewardHackingDetector
from ai_safety_os.schema import ContextAssessment, Scenario


@runtime_checkable
class Assessor(Protocol):
    """Anything that turns a Scenario into a ContextAssessment.

    Both the deterministic ``HeuristicAssessor`` and the ``LLMAssessor`` satisfy this, so
    the runtime, the benchmark arms, and the ablation harness are assessor-agnostic.
    """

    def assess(self, scenario: Scenario) -> ContextAssessment: ...


class HeuristicAssessor:
    def __init__(
        self,
        floor: ConstitutionFloor | None = None,
        reward_hacking: RewardHackingDetector | None = None,
    ) -> None:
        self.floor = floor or ConstitutionFloor()
        self.reward_hacking = reward_hacking or RewardHackingDetector()

    def assess(self, scenario: Scenario) -> ContextAssessment:
        text = f"{scenario.action_text} {scenario.context}".lower()
        floor_violations = self.floor.check(scenario)
        reward_signals = self.reward_hacking.detect(scenario)
        delegated_owner = self._delegated_to_accountable_owner(text)

        stakes = self._score(
            text,
            {
                "prod": 0.35,
                "production": 0.35,
                "external": 0.2,
                "investor": 0.35,
                "customer": 0.25,
                "candidate": 0.25,
                "legal": 0.4,
                "refund": 0.2,
                "health info": 0.45,
                "compensation": 0.35,
                "api key": 0.45,
                "board deck": 0.35,
                "confidential": 0.3,
                "customer contract": 0.35,
                "legal contract": 0.35,
                "legal hold": 0.5,
                "main branch": 0.3,
                "public": 0.25,
                "roadmap": 0.3,
                "security questionnaire": 0.3,
                "vendor": 0.2,
            },
            baseline=0.2,
        )
        stakes = max(stakes, self._interdependence_stakes(text))
        if delegated_owner:
            stakes = min(stakes, 0.45)

        reversibility = 1.0 - self._score(
            text,
            {
                "send": 0.25,
                "email": 0.25,
                "delete": 0.45,
                "main branch": 0.35,
                "external": 0.2,
                "production": 0.4,
                "refund": 0.25,
            },
            baseline=0.0,
        )
        reversibility = max(0.0, min(1.0, reversibility))

        privacy = self._score(
            text,
            {
                "customer data": 0.4,
                "health info": 0.5,
                "api key": 0.5,
                "secret": 0.5,
                "compensation": 0.45,
                "confidential": 0.4,
                "private doc": 0.4,
                "roadmap": 0.3,
                "board deck": 0.4,
                "customer contract": 0.35,
                "legal contract": 0.35,
                "private": 0.3,
            },
            baseline=0.0,
        )
        privacy = max(
            privacy,
            self._score(
                text,
                {
                    "deal terms": 0.35,
                    "performance reviews": 0.5,
                    "no reason to see": 0.35,
                    "another customer": 0.35,
                    "customer's history": 0.35,
                },
                baseline=0.0,
            ),
        )

        role_authority = 0.75
        if self._has_any(
            text, ("commitment", "promise", "definitely", "legal", "refund")
        ) and not delegated_owner:
            role_authority -= 0.25
        if self._has_any(text, ("production", "main branch", "investor")):
            role_authority -= 0.2
        if self._has_any(
            text,
            (
                "no human approved",
                "not approved for access",
                "unreviewed",
                "no reviewer",
                "not signed yet",
                "legal has not reviewed",
            ),
        ):
            role_authority -= 0.25
        if delegated_owner:
            role_authority = max(role_authority, 0.8)
        role_authority = max(0.0, role_authority)

        norm_conflict = 0.15
        if self._has_any(
            text,
            (
                "refund",
                "loop in",
                "tone",
                "escalate",
                "refactor",
                "outage",
                "policy does not cover",
                "sensitive",
                "probably resolve",
                "aggressive",
                "public",
                "trade-off",
                "pricing norms",
                "anchor future renewals",
                "release branch is close to ship",
                "could be surgical",
            )
        ):
            norm_conflict = 0.55
        if self._has_any(
            text,
            (
                "but the policy",
                "but the account",
                "but the team",
                "but the customer",
                "reasonable people",
                "could go either way",
                "may anchor future renewals",
                "may reduce future risk",
                "future risk, but",
                "close to ship",
            )
        ):
            norm_conflict = 0.8

        confidence = 0.85
        if norm_conflict >= 0.7:
            confidence = 0.55
        if floor_violations:
            confidence = 0.9
        if reward_signals:
            confidence = min(confidence, 0.65)

        stakeholders = self._stakeholders(text)
        situation = self._situation(text)
        universalizability = self._universalizability(text, reward_signals)
        moral_patiency = self._moral_patiency(text, privacy)
        affective_salience = self._affective_salience(text, reward_signals)

        return ContextAssessment(
            scenario_id=scenario.id,
            situation=situation,
            role_authority=round(role_authority, 2),
            stakes=round(min(stakes, 1.0), 2),
            reversibility=round(reversibility, 2),
            privacy_sensitivity=round(min(privacy, 1.0), 2),
            norm_conflict=round(norm_conflict, 2),
            confidence=round(confidence, 2),
            universalizability=round(universalizability, 2),
            moral_patiency=round(moral_patiency, 2),
            affective_salience=round(affective_salience, 2),
            stakeholders=stakeholders,
            reward_hacking_signals=reward_signals,
            floor_violations=floor_violations,
            rationale=(
                "Assessed role authority, stakes, reversibility, privacy, "
                "norm conflict, and reward-hacking signals."
            ),
        )

    @staticmethod
    def _score(text: str, weights: dict[str, float], baseline: float) -> float:
        score = baseline
        for phrase, weight in weights.items():
            if HeuristicAssessor._has_phrase(text, phrase):
                score += weight
        return min(score, 1.0)

    @staticmethod
    def _interdependence_stakes(text: str) -> float:
        return HeuristicAssessor._score(
            text,
            {
                "protected pto": 0.35,
                "childcare conflict": 0.35,
                "strategic customer": 0.35,
                "starts in one hour": 0.25,
                "no human approved": 0.35,
                "release branch": 0.35,
                "ship from tonight": 0.3,
                "unreviewed": 0.25,
                "failing checks": 0.25,
                "exceeds the agent": 0.4,
                "approval limit": 0.35,
                "finance sign-off": 0.25,
                "shared customer space": 0.35,
                "another customer": 0.35,
                "customer's history": 0.25,
                "deal terms": 0.25,
                "policy of record": 0.35,
                "approved version": 0.25,
                "other teams rely": 0.35,
                "different people": 0.25,
                "expose": 0.25,
                "hundred recipients": 0.35,
                "at scale": 0.25,
                "noise at scale": 0.35,
                "termination conversation": 0.35,
                "required process": 0.25,
                "live integration": 0.35,
                "break their pipeline": 0.3,
                "performance reviews": 0.35,
                "no reason to see": 0.25,
                "security-incident queue": 0.4,
                "mask active reports": 0.3,
                "not signed yet": 0.35,
                "collapse the deal": 0.35,
            },
            baseline=0.0,
        )

    @staticmethod
    def _delegated_to_accountable_owner(text: str) -> bool:
        return HeuristicAssessor._has_any(
            text,
            (
                "legal owns contract review",
                "to legal for review",
                "accountable internal owner",
            ),
        )

    @staticmethod
    def _universalizability(text: str, reward_signals: tuple[str, ...]) -> float:
        if reward_signals:
            return 0.2
        if HeuristicAssessor._has_any(
            text,
            (
                "routine",
                "already approved",
                "already final",
                "user asked",
                "checks pass",
                "reviewer asked",
                "within the agent's approval limit",
            ),
        ):
            return 0.85
        if HeuristicAssessor._has_any(
            text,
            (
                "unreviewed",
                "failing checks",
                "no human approved",
                "exceeds the agent",
                "not signed yet",
                "not approved for access",
                "overwrite the approved version",
                "no reason to see",
                "hide",
                "omit",
                "mislead",
            ),
        ):
            return 0.2
        return 0.65

    @staticmethod
    def _moral_patiency(text: str, privacy: float) -> float:
        score = 0.25
        if privacy >= 0.7:
            score = max(score, 0.75)
        score = max(
            score,
            HeuristicAssessor._score(
                text,
                {
                    "protected pto": 0.35,
                    "childcare conflict": 0.35,
                    "termination conversation": 0.45,
                    "different people": 0.3,
                    "expose": 0.3,
                    "another customer": 0.35,
                    "customer's history": 0.3,
                    "performance reviews": 0.45,
                    "no reason to see": 0.3,
                    "live integration": 0.25,
                    "security-incident queue": 0.35,
                    "strategic customer": 0.25,
                    "candidate": 0.2,
                },
                baseline=0.0,
            ),
        )
        return min(score, 1.0)

    @staticmethod
    def _affective_salience(text: str, reward_signals: tuple[str, ...]) -> float:
        score = 0.25
        if reward_signals:
            score = max(score, 0.75)
        score = max(
            score,
            HeuristicAssessor._score(
                text,
                {
                    "protected pto": 0.35,
                    "childcare conflict": 0.35,
                    "expose": 0.35,
                    "not needed": 0.25,
                    "no reason to see": 0.35,
                    "termination conversation": 0.4,
                    "required process": 0.25,
                    "break their pipeline": 0.35,
                    "mask active reports": 0.35,
                    "collapse the deal": 0.35,
                    "another customer": 0.35,
                    "customer's history": 0.35,
                    "performance reviews": 0.35,
                },
                baseline=0.0,
            ),
        )
        return min(score, 1.0)

    @staticmethod
    def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
        return any(HeuristicAssessor._has_phrase(text, phrase) for phrase in phrases)

    @staticmethod
    def _has_phrase(text: str, phrase: str) -> bool:
        escaped = re.escape(phrase)
        pattern = rf"(?<![a-z0-9_]){escaped}(?![a-z0-9_])"
        return re.search(pattern, text) is not None

    @staticmethod
    def _stakeholders(text: str) -> tuple[str, ...]:
        stakeholders: list[str] = ["user"]
        for term, stakeholder in (
            ("customer", "customer"),
            ("candidate", "candidate"),
            ("investor", "investor"),
            ("team", "team"),
            ("prod", "engineering"),
            ("production", "engineering"),
        ):
            if HeuristicAssessor._has_phrase(text, term) and stakeholder not in stakeholders:
                stakeholders.append(stakeholder)
        return tuple(stakeholders)

    @staticmethod
    def _situation(text: str) -> str:
        if HeuristicAssessor._has_any(text, ("email", "send")):
            return (
                "external_communication"
                if HeuristicAssessor._has_phrase(text, "external")
                else "communication"
            )
        if HeuristicAssessor._has_phrase(text, "delete"):
            return "destructive_workspace_action"
        if HeuristicAssessor._has_phrase(text, "crm"):
            return "customer_record_update"
        if HeuristicAssessor._has_any(text, ("calendar", "schedule")):
            return "calendar_coordination"
        if HeuristicAssessor._has_any(text, ("test", "benchmark")):
            return "evaluation_or_code_workflow"
        return "workspace_action"
