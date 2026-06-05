"""Adapters that gate agent-framework tools through AI Safety OS.

The core (`guard_callable`) is framework-agnostic. The per-framework helpers wrap it in the
native tool type when that framework is installed, and fall back to the guarded callable
otherwise, so importing this package never requires any framework to be present.
"""

from ai_safety_os.adapters.autogen import guard_autogen_tool
from ai_safety_os.adapters.base import decision_message, guard_callable
from ai_safety_os.adapters.crewai import guard_crewai_tool
from ai_safety_os.adapters.langchain import guard_langchain_tool
from ai_safety_os.adapters.openai_agents import guard_openai_tool

__all__ = [
    "decision_message",
    "guard_autogen_tool",
    "guard_callable",
    "guard_crewai_tool",
    "guard_langchain_tool",
    "guard_openai_tool",
]
