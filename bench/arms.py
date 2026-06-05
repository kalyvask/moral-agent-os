"""Benchmark arms."""

from __future__ import annotations

from ai_safety_os import MoralAgentOS
from ai_safety_os.floor import ConstitutionFloor
from ai_safety_os.schema import ArmResult, Disposition, Scenario


class HardRulesArm:
    name = "hard_rules"

    def __init__(self) -> None:
        self.floor = ConstitutionFloor()

    def run(self, scenario: Scenario) -> ArmResult:
        text = f"{scenario.action_text} {scenario.context}".lower()
        violations = self.floor.check(scenario)
        if violations:
            disposition = Disposition.BLOCK
            rationale = "Static hard-rule violation."
        elif any(term in text for term in ("delete", "send", "email", "refund", "main branch")):
            disposition = Disposition.CONFIRM
            rationale = "Static action type requires confirmation."
        else:
            disposition = Disposition.AUTO
            rationale = "No static hard rule matched."

        return ArmResult(
            arm=self.name,
            scenario_id=scenario.id,
            expected_label=scenario.expected_label,
            disposition=disposition,
            rationale=rationale,
        )


class HighRiskPolicyArm:
    name = "high_risk_policy"

    def __init__(self) -> None:
        self.floor = ConstitutionFloor()

    def run(self, scenario: Scenario) -> ArmResult:
        """A stronger static enterprise-policy baseline."""

        text = f"{scenario.action_text} {scenario.context}".lower()
        violations = self.floor.check(scenario)
        if violations:
            disposition = Disposition.BLOCK
            rationale = "Static high-risk policy: hard-floor violation."
        elif self._escalates(text):
            disposition = Disposition.ESCALATE
            rationale = "Static high-risk policy: sensitive external or irreversible class."
        elif self._confirms(text):
            disposition = Disposition.CONFIRM
            rationale = "Static high-risk policy: consequential action class."
        else:
            disposition = Disposition.AUTO
            rationale = "Static high-risk policy: no policy term matched."

        return ArmResult(
            arm=self.name,
            scenario_id=scenario.id,
            expected_label=scenario.expected_label,
            disposition=disposition,
            rationale=rationale,
        )

    @staticmethod
    def _escalates(text: str) -> bool:
        external = any(
            term in text for term in ("external", "investor", "public", "vendor", "customer")
        )
        sensitive = any(
            term in text
            for term in (
                "api key",
                "board deck",
                "compensation",
                "confidential",
                "customer data",
                "health info",
                "legal",
                "password",
                "private",
                "regulated",
                "secret",
                "ssn",
                "token",
            )
        )
        commitment = any(
            term in text for term in ("commitment", "definitely", "promise", "legal hold")
        )
        destructive = any(
            term in text
            for term in ("delete", "drop", "wipe", "main branch", "production", "prod")
        )
        return (external and (sensitive or commitment)) or destructive

    @staticmethod
    def _confirms(text: str) -> bool:
        return any(
            term in text
            for term in (
                "account",
                "access",
                "calendar",
                "crm",
                "customer",
                "delete",
                "doc",
                "email",
                "external",
                "meeting",
                "post",
                "refund",
                "schedule",
                "send",
                "share",
                "social",
            )
        )


class AlwaysConfirmArm:
    name = "always_confirm"

    def run(self, scenario: Scenario) -> ArmResult:
        return ArmResult(
            arm=self.name,
            scenario_id=scenario.id,
            expected_label=scenario.expected_label,
            disposition=Disposition.CONFIRM,
            rationale="Control arm: ask for every action.",
        )


class NormOSArm:
    name = "normos"

    def __init__(self, runtime: MoralAgentOS | None = None, assessor=None) -> None:
        self.runtime = runtime or MoralAgentOS(assessor=assessor)

    def run(self, scenario: Scenario) -> ArmResult:
        decision = self.runtime.evaluate(scenario)
        return ArmResult(
            arm=self.name,
            scenario_id=scenario.id,
            expected_label=scenario.expected_label,
            disposition=decision.disposition,
            rationale=decision.rationale,
        )
