"""Framework-agnostic core for gating agent tools through AI Safety OS.

Every tool-calling framework ultimately calls a Python callable. ``guard_callable`` wraps
one so that, before it runs, AI Safety OS assesses the action in context and routes it.
When the route is allowed, the tool runs and returns its result. When it is not, the
wrapper returns a short, agent-readable message instead of executing, so the model can do
what the route asks: confirm with the user, present alternatives, or escalate. Returning a
message (rather than raising) is the right shape for tool-calling agents, which expect a
string back from a tool and can act on it.

The framework-specific modules (langchain, crewai, autogen, openai_agents) are thin: they
build a guarded callable here and, if that framework is installed, wrap it in the
framework's native tool type. If it is not installed, they return the guarded callable,
which every framework accepts in some form.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import Any

from ai_safety_os import (
    ActionProposal,
    ContextSnapshot,
    MoralAgentOS,
    MoralDecision,
    MoralRoute,
)

ContextLike = ContextSnapshot | Callable[..., ContextSnapshot]


def decision_message(decision: MoralDecision) -> str:
    """A concise, agent-readable explanation of why a tool did not execute."""
    guidance = {
        MoralRoute.CONFIRM: "Ask the user to confirm before this runs.",
        MoralRoute.ALTERNATIVES: "Present the alternative interpretations; let the user choose.",
        MoralRoute.ESCALATE: "Escalate to an accountable human for review; do not proceed alone.",
        MoralRoute.BLOCK: "Do not attempt this action; it violates a hard safety or legal floor.",
    }.get(decision.route, "This action was paused.")
    parts = [
        f"[AI Safety OS] Not executed (route={decision.route.value}, stakes={decision.stakes}).",
        guidance,
        f"Reason: {decision.reason}",
    ]
    if decision.norm_conflicts:
        parts.append("Interpretations: " + "; ".join(decision.norm_conflicts))
    return " ".join(parts)


def _proposal(func: Callable[..., Any], action_type: str, description: str | None,
              args: tuple, kwargs: dict) -> ActionProposal:
    try:
        bound = signature(func).bind_partial(*args, **kwargs).arguments
    except TypeError:
        bound = dict(kwargs)
    params = {
        name: value
        for name, value in bound.items()
        if isinstance(value, (str, int, float, bool, type(None)))
    }
    return ActionProposal(
        id=f"tool:{func.__name__}",
        action_type=action_type or func.__name__,
        description=description or (func.__doc__ or f"Run {func.__name__}.").strip(),
        params=params,
    )


def guard_callable(
    runtime: MoralAgentOS,
    func: Callable[..., Any],
    *,
    action_type: str | None = None,
    context: ContextLike,
    description: str | None = None,
    execute_routes: tuple[MoralRoute, ...] = (MoralRoute.ALLOW,),
    on_decision: Callable[[MoralDecision], None] | None = None,
) -> Callable[..., Any]:
    """Wrap ``func`` so AI Safety OS gates it. Returns a signature-preserving callable.

    Args:
        runtime: the AI Safety OS instance to assess with.
        func: the underlying tool callable.
        action_type: action family (defaults to the function name).
        context: a ContextSnapshot, or a builder called with the tool's args that returns
            one. A builder lets context depend on the actual arguments (recipient, target).
        execute_routes: routes that are allowed to run the tool. Defaults to allow-only.
        on_decision: optional hook receiving every MoralDecision (for logging/telemetry).
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        snapshot = context(*args, **kwargs) if callable(context) else context
        proposal = _proposal(func, action_type or func.__name__, description, args, kwargs)
        decision = runtime.assess(proposal, snapshot)
        if on_decision is not None:
            on_decision(decision)
        if decision.route in execute_routes:
            return func(*args, **kwargs)
        return decision_message(decision)

    wrapper.__moral_guarded__ = True  # marker for introspection/tests
    return wrapper
