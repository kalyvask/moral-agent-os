"""Runtime wrapper for assessing and routing proposed agent actions."""

from __future__ import annotations

from moral_agent_os.assess import HeuristicAssessor
from moral_agent_os.norms import LocalNormMemory
from moral_agent_os.route import NormRouter
from moral_agent_os.schema import Disposition, RouteDecision, Scenario


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
