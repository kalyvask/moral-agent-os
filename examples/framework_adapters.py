"""Gate the same agent tool through four framework adapters.

This runs with no framework installed: each adapter falls back to a guarded callable, which
we call directly to show the gate. With LangChain / CrewAI / AutoGen / the OpenAI Agents
SDK installed, the same calls return that framework's native tool object instead, wrapping
the identical guard. Registration lines for each are shown in comments.

    python examples/framework_adapters.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters import (
    guard_autogen_tool,
    guard_crewai_tool,
    guard_langchain_tool,
    guard_openai_tool,
)
from moral_agent_os import ContextSnapshot, MoralAgentOS


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    return f"SENT to {to}: {subject}"


def email_context(to: str, subject: str, body: str) -> ContextSnapshot:
    """Build context from the actual arguments: external mail is higher-stakes."""
    external = not to.endswith("@ourcompany.com")
    return ContextSnapshot(
        agent_role="workspace assistant",
        user_intent="Send an email the user asked for.",
        situation="external_communication" if external else "internal_communication",
        stakes=0.85 if external else 0.2,
        reversibility=0.1 if external else 0.9,
    )


ADAPTERS = {
    "langchain": guard_langchain_tool,
    "crewai": guard_crewai_tool,
    "autogen": guard_autogen_tool,
    "openai_agents": guard_openai_tool,
}


def _callable(tool):
    """Return something we can call directly, whether tool is a native object or a fn."""
    for attr in ("func", "_run", "on_invoke_tool", "run"):
        if hasattr(tool, attr) and callable(getattr(tool, attr)):
            return getattr(tool, attr)
    return tool


def main() -> None:
    runtime = MoralAgentOS()

    internal = ("alex@ourcompany.com", "Draft plan", "Sharing the draft.")
    external = ("investor@vc.com", "Update", "We are definitely raising next quarter.")

    for name, adapter in ADAPTERS.items():
        guarded = adapter(
            runtime,
            send_email,
            context=email_context,
            action_type="send_email",
            description="Send an email to a recipient.",
        )
        run = _callable(guarded)
        print(f"## {name}")
        print(f"  internal -> {run(*internal)}")
        print(f"  external -> {run(*external)}")
        print()

    print(
        "Without a framework installed, each adapter returned a guarded callable.\n"
        "Native registration when the framework is present:\n"
        "  LangChain:     tools=[guard_langchain_tool(runtime, send_email, context=...)]\n"
        "  CrewAI:        Agent(tools=[guard_crewai_tool(runtime, send_email, context=...)])\n"
        "  AutoGen:       AssistantAgent(tools=[guard_autogen_tool(runtime, send_email, ...)])\n"
        "  OpenAI Agents: Agent(tools=[guard_openai_tool(runtime, send_email, context=...)])"
    )


if __name__ == "__main__":
    main()
