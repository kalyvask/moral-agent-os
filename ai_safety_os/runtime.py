"""Runtime wrapper for assessing and routing proposed agent actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from functools import wraps
from inspect import iscoroutinefunction, signature
from typing import Any

from ai_safety_os.assess import Assessor, HeuristicAssessor
from ai_safety_os.norms import CorrectionStore, LocalNormMemory
from ai_safety_os.route import NormRouter
from ai_safety_os.schema import (
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
        assessor: Assessor | None = None,
        router: NormRouter | None = None,
        memory: CorrectionStore | None = None,
        *,
        low_trust_threshold: float = 0.35,
        high_trust_threshold: float = 0.8,
        sanction_severity: float = 0.7,
        cooperation_amount: float = 0.15,
        learn_from_outcomes: bool = True,
    ) -> None:
        self.assessor = assessor or HeuristicAssessor()
        self.router = router or NormRouter()
        self.memory = memory or LocalNormMemory()
        # Interdependence loop: trust gates and the sanction/cooperation step sizes that
        # let an agent earn or lose autonomy with a counterparty from its own track record.
        self.low_trust_threshold = low_trust_threshold
        self.high_trust_threshold = high_trust_threshold
        self.sanction_severity = sanction_severity
        self.cooperation_amount = cooperation_amount
        self.learn_from_outcomes = learn_from_outcomes

    def evaluate(self, scenario: Scenario) -> RouteDecision:
        assessment = self.assessor.assess(scenario)
        decision = self.router.route(scenario, assessment)
        return self._apply_memory_override(scenario, assessment, decision)

    def assess(self, action: ActionProposal, context: ContextSnapshot) -> MoralDecision:
        """Assess a proposed agent action with the product-facing SDK schema."""

        context = self._hydrate_context(context)
        scenario = self._scenario_from_action(action, context)
        assessment = self._apply_context_overrides(
            self.assessor.assess(scenario),
            context,
        )
        route_decision = self.router.route(scenario, assessment)
        route_decision = self._apply_memory_override(scenario, assessment, route_decision)

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

        # Trust as a routing signal (the runtime analog of the interdependence trust gate):
        # low trust with an affected counterparty tightens; established clean trust on a
        # routine action relaxes a mild confirm back to auto.
        min_trust = self._min_trust(context.relationships)
        if min_trust is not None and min_trust < self.low_trust_threshold:
            route = self._stronger_route(route, MoralRoute.CONFIRM)
            state_updates.append(f"low_trust={min_trust:.2f}")
            reasons.append("Low trust with an affected counterparty; ask before acting.")

        if route == MoralRoute.CONFIRM and self._trust_earns_auto(assessment, context):
            route = MoralRoute.ALLOW
            state_updates.append(f"trusted_auto={min_trust:.2f}")
            reasons.append(
                "Established trust with this counterparty on a low-stakes, reversible action; "
                "auto-approved on track record."
            )

        norm_conflicts = context.norm_conflicts
        if route_decision.options and not norm_conflicts:
            norm_conflicts = tuple(option.name for option in route_decision.options)

        required_review = required_review or route == MoralRoute.ESCALATE

        decision = MoralDecision(
            route=route,
            reason=" ".join(reasons),
            stakes=self._stakes_label(assessment.stakes),
            norm_conflicts=norm_conflicts,
            alternatives=route_decision.options,
            required_review=required_review,
            state_updates=tuple(state_updates),
            trace={
                **route_decision.trace,
                "action_id": action.id,
                "action_type": action.action_type,
                "sdk_route": route.value,
                "required_review": required_review,
                "state_updates": list(state_updates),
                "alternatives": [
                    {
                        "name": option.name,
                        "interpretation": option.interpretation,
                        "recommended_action": option.recommended_action,
                    }
                    for option in route_decision.options
                ],
            },
        )
        self._log_decision(action, decision, assessment)
        return decision

    before_action = assess

    def observe_outcome(
        self,
        decision: MoralDecision,
        context: ContextSnapshot,
        *,
        executed: bool,
    ) -> None:
        """Update durable relationship state from an action's outcome.

        This is what makes interdependence a runtime behavior, not just a benchmark:
        reputation and repair move from the agent's own track record instead of hand-passed
        state. A caught hard violation (block) sanctions the affected counterparties and
        lowers trust; an action that actually ran (auto-allowed or human-approved) records
        cooperation that pays the repair debt down and rebuilds trust; an escalation is
        logged for accountable review. No-ops on memory backends without relationship
        support, or when ``learn_from_outcomes`` is off (the frozen control).
        """
        if not self.learn_from_outcomes:
            return
        memory = self.memory
        if not all(
            hasattr(memory, name)
            for name in ("observe_sanction", "observe_cooperation", "record_review")
        ):
            return
        names = tuple(stakeholder.name for stakeholder in context.stakeholders)
        if not names:
            return
        action_id = str(decision.trace.get("action_id", ""))
        for name in names:
            if decision.route == MoralRoute.BLOCK:
                memory.observe_sanction(name, severity=self.sanction_severity)
                memory.record_review(name, action_id, "blocked")
            elif decision.route == MoralRoute.ESCALATE:
                memory.record_review(name, action_id, "escalated")
            if executed:
                memory.observe_cooperation(name, amount=self.cooperation_amount)

    def _log_decision(
        self,
        action: ActionProposal,
        decision: MoralDecision,
        assessment: ContextAssessment,
    ) -> None:
        """Append the decision to the memory's audit log, if the backend keeps one.

        Recording happens on every SDK ``assess()`` regardless of ``learn_from_outcomes``:
        the audit trail is observation, not learning, so the frozen control logs too.
        """
        record = getattr(self.memory, "record_decision", None)
        if record is None:
            return
        record(action, decision, stakeholders=assessment.stakeholders)

    def guard_tool(
        self,
        *,
        action_type: str | None = None,
        context: ContextSnapshot | None = None,
        proposal_builder: Callable[..., ActionProposal] | None = None,
        context_builder: Callable[..., ContextSnapshot] | None = None,
        execute_routes: tuple[MoralRoute, ...] = (MoralRoute.ALLOW,),
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate an agent tool so AI Safety OS gates execution.

        Works on both sync and async tools: an ``async def`` tool gets an async wrapper
        that awaits the tool only when the decision allows execution, so the guard drops
        into asyncio-based agent frameworks unchanged.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def prepare(
                args: tuple[Any, ...], kwargs: dict[str, Any]
            ) -> tuple[ActionProposal, ContextSnapshot]:
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
                return action, context_snapshot

            def finish(
                decision: MoralDecision,
                context_snapshot: ContextSnapshot,
                executed: bool,
                result: Any,
            ) -> GuardedToolResult:
                # Close the interdependence loop: the outcome updates the agent's standing
                # with each affected counterparty for next time.
                self.observe_outcome(decision, context_snapshot, executed=executed)
                if executed:
                    return GuardedToolResult(
                        decision=decision,
                        executed=True,
                        result=result,
                        message="Executed after AI Safety OS allowed the action.",
                    )
                return GuardedToolResult(
                    decision=decision,
                    executed=False,
                    message=self._blocked_tool_message(decision),
                )

            if iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> GuardedToolResult:
                    action, context_snapshot = prepare(args, kwargs)
                    decision = self.assess(action, context_snapshot)
                    executed = decision.route in execute_routes
                    result = await func(*args, **kwargs) if executed else None
                    return finish(decision, context_snapshot, executed, result)

                return async_wrapper

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> GuardedToolResult:
                action, context_snapshot = prepare(args, kwargs)
                decision = self.assess(action, context_snapshot)
                executed = decision.route in execute_routes
                result = func(*args, **kwargs) if executed else None
                return finish(decision, context_snapshot, executed, result)

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

    def _apply_memory_override(
        self,
        scenario: Scenario,
        assessment: ContextAssessment,
        decision: RouteDecision,
    ) -> RouteDecision:
        remembered = self.memory.lookup(scenario)
        if remembered is None:
            return decision

        if remembered == Disposition.AUTO and decision.disposition == Disposition.CONFIRM:
            return RouteDecision(
                disposition=Disposition.AUTO,
                rationale="Local norm memory says this situation family can auto-execute.",
                assessment=assessment,
                options=decision.options,
                trace={**decision.trace, "memory_override": "confirm_to_auto"},
            )

        return decision

    def _hydrate_context(self, context: ContextSnapshot) -> ContextSnapshot:
        if context.relationships or not hasattr(self.memory, "relationships_for"):
            return context
        names = tuple(stakeholder.name for stakeholder in context.stakeholders)
        if not names:
            return context
        relationships_for = self.memory.relationships_for
        return replace(context, relationships=relationships_for(names))

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
    def _min_trust(relationships: tuple[RelationshipState, ...]) -> float | None:
        trusts = [relationship.trust for relationship in relationships]
        return min(trusts) if trusts else None

    def _trust_earns_auto(
        self,
        assessment: ContextAssessment,
        context: ContextSnapshot,
    ) -> bool:
        """Whether an established, clean relationship has earned auto-approval here.

        Conservative by construction: it only relaxes a confirm that came from mild
        uncertainty on a low-stakes, reversible, floor-clean action, and only when every
        affected counterparty is highly trusted with no outstanding debt, pending review, or
        unmet joint commitment. Anything the safety layer flags is never relaxed, so the
        benchmark's no-unsafe-auto result (which runs without relationships) is unaffected.
        """
        relationships = context.relationships
        if not relationships:
            return False
        min_trust = self._min_trust(relationships)
        if min_trust is None or min_trust < self.high_trust_threshold:
            return False
        if assessment.floor_violations or assessment.reward_hacking_signals:
            return False
        if assessment.universalizability < self.router.universalizability_floor:
            return False
        if self.router.protect_patients and assessment.endangers_vulnerable_patient:
            return False
        if assessment.norm_conflict >= self.router.norm_conflict_threshold:
            return False
        if assessment.stakes >= self.router.confirm_stakes:
            return False
        if assessment.reversibility <= self.router.escalate_reversibility:
            return False
        for relationship in relationships:
            if relationship.repair_obligation > 0.0 or relationship.public_review_required:
                return False
            if (
                relationship.joint_commitment_required
                and not relationship.joint_commitment_present
            ):
                return False
        return True

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
            return "Tool call blocked by AI Safety OS."
        return "Tool call paused by AI Safety OS."
