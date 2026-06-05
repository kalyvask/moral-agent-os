"""Runtime wrapper for assessing and routing proposed agent actions."""

from __future__ import annotations

from dataclasses import replace
from functools import wraps
from inspect import signature
from typing import Any, Callable

from moral_agent_os.assess import HeuristicAssessor
from moral_agent_os.norms import LocalNormMemory
from moral_agent_os.route import NormRouter
from moral_agent_os.schema import (
    ActionProposal,
    ContextAssessment,
    ContextSnapshot,
    Disposition,
    GuardedToolResult,
    MoralDecision,
    MoralRoute,
    RelationshipState,
    RouteDecision,
    Scenario,
    ScenarioLabel,
)


class MoralAgentOS:
    def __init__(
        self,
        assessor: HeuristicAssessor | None = None,
        router: NormRouter | None = None,
        memory: LocalNormMemory | None = None,
    ) -> None:
        self.assessor = assessor or HeuristicAssessor()
        self.router = router or NormRouter()
        self.memory = memory or LocalNormMemory()

    def evaluate(self, scenario: Scenario) -> RouteDecision:
        remembered = self.memory.lookup(scenario)
        assessment = self.assessor.assess(scenario)
        decision = self.router.route(scenario, assessment)

        if remembered is None:
            return decision

        if remembered == Disposition.AUTO and decision.disposition == Disposition.CONFIRM:
            return RouteDecision(
                disposition=Disposition.AUTO,
                rationale="Local norm memory says this situation family can auto-execute.",
                assessment=assessment,
                trace={**decision.trace, "memory_override": "confirm_to_auto"},
            )

        return decision

    def assess(self, action: ActionProposal, context: ContextSnapshot) -> MoralDecision:
        """Assess a proposed agent action with the product-facing SDK schema."""

        scenario = self._scenario_from_action(action, context)
        assessment = self._apply_context_overrides(
            self.assessor.assess(scenario),
            context,
        )
        route_decision = self.router.route(scenario, assessment)

        route = self._route_from_disposition(route_decision.disposition)
        required_review = False
        state_updates: list[str] = []
        reasons: list[str] = [route_decision.rationale]

        if self._joint_commitment_missing(context):
            route = self._stronger_route(route, MoralRoute.CONFIRM)
            state_updates.append("joint_commitment_required")
            reasons.append("Shared task needs an explicit joint commitment before acting.")

        if self._joint_commitment_present(context):
            state_updates.append("joint_commitment_recorded")

        max_repair_obligation = self._max_repair_obligation(context.relationships)
        if max_repair_obligation > 0:
            state_updates.append(f"repair_obligation={max_repair_obligation:.2f}")
        if max_repair_obligation >= 0.50:
            route = self._stronger_route(route, MoralRoute.CONFIRM)
            reasons.append("Outstanding repair obligation means the agent should not act silently.")

        if self._requires_public_review(context, assessment):
            route = self._stronger_route(route, MoralRoute.ESCALATE)
            required_review = True
            state_updates.append("public_review_required")
            reasons.append("Affected stakeholders or dependency level require accountable review.")

        norm_conflicts = context.norm_conflicts
        if route_decision.options and not norm_conflicts:
            norm_conflicts = tuple(option.name for option in route_decision.options)

        return MoralDecision(
            route=route,
            reason=" ".join(reasons),
            stakes=self._stakes_label(assessment.stakes),
            norm_conflicts=norm_conflicts,
            required_review=required_review,
            state_updates=tuple(state_updates),
            trace={
                **route_decision.trace,
                "action_id": action.id,
                "action_type": action.action_type,
                "sdk_route": route.value,
                "required_review": required_review,
                "state_updates": list(state_updates),
            },
        )

    before_action = assess

    def guard_tool(
        self,
        *,
        action_type: str | None = None,
        context: ContextSnapshot | None = None,
        proposal_builder: Callable[..., ActionProposal] | None = None,
        context_builder: Callable[..., ContextSnapshot] | None = None,
        execute_routes: tuple[MoralRoute, ...] = (MoralRoute.ALLOW,),
    ) -> Callable[[Callable[..., Any]], Callable[..., GuardedToolResult]]:
        """Decorate an agent tool so Moral Agent OS gates execution."""

        def decorator(func: Callable[..., Any]) -> Callable[..., GuardedToolResult]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> GuardedToolResult:
                action = (
                    proposal_builder(*args, **kwargs)
                    if proposal_builder
                    else self._default_action_proposal(func, action_type, args, kwargs)
                )
                context_snapshot = (
                    context_builder(*args, **kwargs)
                    if context_builder
                    else context
                    if context
                    else self._default_context_snapshot(func)
                )
                decision = self.assess(action, context_snapshot)

                if decision.route in execute_routes:
                    result = func(*args, **kwargs)
                    return GuardedToolResult(
                        decision=decision,
                        executed=True,
                        result=result,
                        message="Executed after Moral Agent OS allowed the action.",
                    )

                return GuardedToolResult(
                    decision=decision,
                    executed=False,
                    message=self._blocked_tool_message(decision),
                )

            return wrapper

        return decorator

    @staticmethod
    def _scenario_from_action(action: ActionProposal, context: ContextSnapshot) -> Scenario:
        context_parts = [
            context.user_intent,
            context.situation,
            " ".join(
                f"{stakeholder.role}:{stakeholder.name}"
                for stakeholder in context.stakeholders
            ),
            " ".join(f"{key}:{value}" for key, value in action.params.items()),
        ]
        expected_label = (
            ScenarioLabel.PLURAL
            if context.norm_conflicts
            else ScenarioLabel.CLEAR_APPROPRIATE
        )
        return Scenario(
            id=action.id,
            action_family=action.action_type,
            action_text=action.description,
            context=" ".join(part for part in context_parts if part),
            agent_role=context.agent_role,
            expected_label=expected_label,
        )

    @staticmethod
    def _default_action_proposal(
        func: Callable[..., Any],
        action_type: str | None,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ActionProposal:
        bound = signature(func).bind_partial(*args, **kwargs)
        params = {
            name: value
            for name, value in bound.arguments.items()
            if isinstance(value, str | int | float | bool | type(None))
        }
        return ActionProposal(
            id=f"tool:{func.__name__}",
            action_type=action_type or func.__name__,
            description=f"Run agent tool {func.__name__}.",
            params=params,
        )

    @staticmethod
    def _default_context_snapshot(func: Callable[..., Any]) -> ContextSnapshot:
        return ContextSnapshot(
            agent_role="agent tool runner",
            user_intent=f"Run {func.__name__}.",
            situation=f"tool:{func.__name__}",
        )

    @staticmethod
    def _apply_context_overrides(
        assessment: ContextAssessment,
        context: ContextSnapshot,
    ) -> ContextAssessment:
        overrides: dict[str, Any] = {}
        if context.stakes is not None:
            overrides["stakes"] = round(max(0.0, min(1.0, context.stakes)), 2)
        if context.reversibility is not None:
            overrides["reversibility"] = round(
                max(0.0, min(1.0, context.reversibility)),
                2,
            )
        if context.privacy_sensitivity is not None:
            overrides["privacy_sensitivity"] = round(
                max(0.0, min(1.0, context.privacy_sensitivity)),
                2,
            )
        if context.norm_conflicts:
            overrides["norm_conflict"] = max(assessment.norm_conflict, 0.80)
            overrides["confidence"] = min(assessment.confidence, 0.65)
        if context.stakeholders:
            overrides["stakeholders"] = tuple(
                stakeholder.name for stakeholder in context.stakeholders
            )
        if not overrides:
            return assessment
        return replace(assessment, **overrides)

    @staticmethod
    def _route_from_disposition(disposition: Disposition) -> MoralRoute:
        return {
            Disposition.AUTO: MoralRoute.ALLOW,
            Disposition.CONFIRM: MoralRoute.CONFIRM,
            Disposition.PRESENT_OPTIONS: MoralRoute.ALTERNATIVES,
            Disposition.ESCALATE: MoralRoute.ESCALATE,
            Disposition.BLOCK: MoralRoute.BLOCK,
        }[disposition]

    @staticmethod
    def _stronger_route(current: MoralRoute, candidate: MoralRoute) -> MoralRoute:
        order = {
            MoralRoute.ALLOW: 0,
            MoralRoute.CONFIRM: 1,
            MoralRoute.ALTERNATIVES: 2,
            MoralRoute.ESCALATE: 3,
            MoralRoute.BLOCK: 4,
        }
        return candidate if order[candidate] > order[current] else current

    @staticmethod
    def _max_repair_obligation(relationships: tuple[RelationshipState, ...]) -> float:
        if not relationships:
            return 0.0
        return max(relationship.repair_obligation for relationship in relationships)

    @staticmethod
    def _joint_commitment_missing(context: ContextSnapshot) -> bool:
        return any(
            relationship.joint_commitment_required
            and not relationship.joint_commitment_present
            for relationship in context.relationships
        )

    @staticmethod
    def _joint_commitment_present(context: ContextSnapshot) -> bool:
        return any(
            relationship.joint_commitment_required
            and relationship.joint_commitment_present
            for relationship in context.relationships
        )

    @staticmethod
    def _requires_public_review(
        context: ContextSnapshot,
        assessment: ContextAssessment,
    ) -> bool:
        if any(stakeholder.requires_review for stakeholder in context.stakeholders):
            return True
        if any(relationship.public_review_required for relationship in context.relationships):
            return True

        dependencies = [
            stakeholder.dependency for stakeholder in context.stakeholders
        ] + [
            relationship.dependency for relationship in context.relationships
        ]
        max_dependency = max(dependencies) if dependencies else 0.0
        return (
            context.public_review_available
            and max_dependency >= 0.70
            and (assessment.stakes >= 0.50 or assessment.privacy_sensitivity >= 0.50)
        )

    @staticmethod
    def _stakes_label(stakes: float) -> str:
        if stakes >= 0.70:
            return "high"
        if stakes >= 0.40:
            return "medium"
        return "low"

    @staticmethod
    def _blocked_tool_message(decision: MoralDecision) -> str:
        if decision.route == MoralRoute.CONFIRM:
            return "Tool call paused for user confirmation."
        if decision.route == MoralRoute.ALTERNATIVES:
            return "Tool call paused to present alternative interpretations."
        if decision.route == MoralRoute.ESCALATE:
            return "Tool call paused for accountable review."
        if decision.route == MoralRoute.BLOCK:
            return "Tool call blocked by Moral Agent OS."
        return "Tool call paused by Moral Agent OS."
