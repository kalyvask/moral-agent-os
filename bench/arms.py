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
