"""Context assessment.

The current assessor is deterministic so the scaffold runs without API keys.
Future LLM assessors should emit the same ContextAssessment schema.
"""

from __future__ import annotations

from moral_agent_os.floor import ConstitutionFloor
from moral_agent_os.reward_hacking import RewardHackingDetector
from moral_agent_os.schema import ContextAssessment, Scenario


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

        role_authority = 0.75
        if any(
            term in text
            for term in ("commitment", "promise", "definitely", "legal", "refund")
        ):
            role_authority -= 0.25
        if any(term in text for term in ("production", "main branch", "investor")):
            role_authority -= 0.2
        role_authority = max(0.0, role_authority)

        norm_conflict = 0.15
        if any(
            term in text
            for term in (
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
            )
        ):
            norm_conflict = 0.55
        if any(
            phrase in text
            for phrase in (
                "but the policy",
                "but the account",
                "but the team",
                "but the customer",
                "reasonable people",
                "could go either way",
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

        return ContextAssessment(
            scenario_id=scenario.id,
            situation=situation,
            role_authority=round(role_authority, 2),
            stakes=round(min(stakes, 1.0), 2),
            reversibility=round(reversibility, 2),
            privacy_sensitivity=round(min(privacy, 1.0), 2),
            norm_conflict=round(norm_conflict, 2),
            confidence=round(confidence, 2),
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
            if phrase in text:
                score += weight
        return min(score, 1.0)

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
            if term in text and stakeholder not in stakeholders:
                stakeholders.append(stakeholder)
        return tuple(stakeholders)

    @staticmethod
    def _situation(text: str) -> str:
        if "email" in text or "send" in text:
            return "external_communication" if "external" in text else "communication"
        if "delete" in text:
            return "destructive_workspace_action"
        if "crm" in text:
            return "customer_record_update"
        if "calendar" in text or "schedule" in text:
            return "calendar_coordination"
        if "test" in text or "benchmark" in text:
            return "evaluation_or_code_workflow"
        return "workspace_action"
