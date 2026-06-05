"""OpenAI Agents-style adapter.

Wrap any callable as a tool gated by AI Safety OS. If the OpenAI Agents SDK (``agents``)
is installed, returns a ``function_tool``; otherwise returns the guarded callable, which
works with raw OpenAI function calling (you dispatch the call yourself).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_safety_os import MoralAgentOS, MoralRoute
from ai_safety_os.adapters.base import ContextLike, guard_callable


def guard_openai_tool(
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
    try:
        from agents import function_tool
    except ImportError:
        return guarded
    # The Agents SDK reads the name/description from the function; preserve them.
    if name:
        guarded.__name__ = name
    if description:
        guarded.__doc__ = description
    return function_tool(guarded)
