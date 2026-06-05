"""Shared schemas for the runtime and benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ScenarioLabel(StrEnum):
    CLEAR_APPROPRIATE = "clear_appropriate"
    CLEAR_INAPPROPRIATE = "clear_inappropriate"
    PLURAL = "plural"


class Disposition(StrEnum):
    AUTO = "auto"
    CONFIRM = "confirm"
    PRESENT_OPTIONS = "present_options"
    ESCALATE = "escalate"
    BLOCK = "block"


@dataclass(frozen=True)
class Scenario:
    id: str
    action_family: str
    action_text: str
    context: str
    agent_role: str
    expected_label: ScenarioLabel
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        return cls(
            id=str(data["id"]),
            action_family=str(data["action_family"]),
            action_text=str(data["action_text"]),
            context=str(data["context"]),
            agent_role=str(data["agent_role"]),
            expected_label=ScenarioLabel(data["expected_label"]),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class ContextAssessment:
    scenario_id: str
    situation: str
    role_authority: float
    stakes: float
    reversibility: float
    privacy_sensitivity: float
    norm_conflict: float
    confidence: float
    stakeholders: tuple[str, ...] = ()
    reward_hacking_signals: tuple[str, ...] = ()
    floor_violations: tuple[str, ...] = ()
    rationale: str = ""

    @property
    def is_high_stakes(self) -> bool:
        return self.stakes >= 0.7

    @property
    def is_irreversible(self) -> bool:
        return self.reversibility <= 0.25

    @property
    def is_privacy_sensitive(self) -> bool:
        return self.privacy_sensitivity >= 0.7


@dataclass(frozen=True)
class KaleidoscopeOption:
    name: str
    interpretation: str
    recommended_action: str


@dataclass(frozen=True)
class RouteDecision:
    disposition: Disposition
    rationale: str
    assessment: ContextAssessment
    options: tuple[KaleidoscopeOption, ...] = ()
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArmResult:
    arm: str
    scenario_id: str
    expected_label: ScenarioLabel
    disposition: Disposition
    rationale: str
