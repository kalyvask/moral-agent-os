"""AutoGen adapter.

Wrap any callable as an AutoGen tool gated by AI Safety OS. If autogen-core is installed,
returns a ``FunctionTool``; otherwise returns the guarded callable, which AutoGen also
accepts directly (e.g. ``register_function`` or ``tools=[...]``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_safety_os import MoralAgentOS, MoralRoute
from ai_safety_os.adapters.base import ContextLike, guard_callable


def guard_autogen_tool(
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
        from autogen_core.tools import FunctionTool
    except ImportError:
        return guarded
    return FunctionTool(
        guarded,
        name=name or func.__name__,
        description=description or (func.__doc__ or action_type or func.__name__).strip(),
    )
