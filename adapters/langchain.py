"""LangChain adapter.

Wrap any callable as a LangChain tool that is gated by AI Safety OS. If LangChain is
installed, returns a ``StructuredTool``; otherwise returns the guarded callable, which you
can register however you like.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from adapters.base import ContextLike, guard_callable
from ai_safety_os import MoralAgentOS, MoralRoute


def guard_langchain_tool(
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
        from langchain_core.tools import StructuredTool
    except ImportError:
        return guarded
    return StructuredTool.from_function(
        func=guarded,
        name=name or func.__name__,
        description=description or (func.__doc__ or action_type or func.__name__).strip(),
    )
