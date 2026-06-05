"""CrewAI adapter.

Wrap any callable as a CrewAI tool gated by AI Safety OS. If CrewAI is installed,
returns a CrewAI ``Tool``; otherwise returns the guarded callable. The CrewAI tool import
path has moved across versions, so both known locations are tried.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_safety_os import MoralAgentOS, MoralRoute
from ai_safety_os.adapters.base import ContextLike, guard_callable


def guard_crewai_tool(
    runtime: MoralAgentOS,
    func: Callable[..., Any],
    *,
    context: ContextLike,
    action_type: str | None = None,
    name: str | None = None,
    description: str | None = None,
    execute_routes: tuple[MoralRoute, ...] = (MoralRoute.ALLOW,),
    on_decision: Callable | None = None,
) -> Any:
    guarded = guard_callable(
        runtime,
        func,
        action_type=action_type,
        context=context,
        description=description,
        execute_routes=execute_routes,
        on_decision=on_decision,
    )
    tool_decorator = _crewai_tool_decorator()
    if tool_decorator is None:
        return guarded
    return tool_decorator(name or func.__name__)(guarded)


def _crewai_tool_decorator():
    for module in ("crewai.tools", "crewai_tools"):
        try:
            mod = __import__(module, fromlist=["tool"])
        except ImportError:
            continue
        if hasattr(mod, "tool"):
            return mod.tool
    return None
