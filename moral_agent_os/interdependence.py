"""A small interdependence environment for moral-learning experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class InteractionAction(StrEnum):
    COOPERATE = "cooperate"
    DEFECT = "defect"


@dataclass(frozen=True)
class InterdependenceConfig:
    name: str
    rounds: int = 20
    population_size: int = 12
    repeated_interaction: bool = True
    reputation_enabled: bool = True
    partner_choice_enabled: bool = True
    sanction_enabled: bool = True
    initial_norm_strength: float = 0.2
    cooperative_cluster: bool = False


@dataclass
class AgentState:
    agent_id: str
    prosocial_bias: float
    reputation: float = 0.5
    payoff: float = 0.0


@dataclass(frozen=True)
class InteractionRecord:
    round_index: int
    agent_a: str
    agent_b: str
    action_a: InteractionAction
    action_b: InteractionAction
    payoff_a: float
    payoff_b: float
    sanctioned: tuple[str, ...] = ()
    norm_strength: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    condition: str
    records: tuple[InteractionRecord, ...]
    final_agents: tuple[AgentState, ...]
    cooperation_rate: float
    betrayal_rate: float
    mean_payoff: float
    mean_reputation: float
    norm_strength: float


class InterdependenceEnvironment:
    """Run repeated Stag Hunt style interactions.

    This is a scaffold, not a scientific model. It encodes the course mechanism:
    repeated dependence plus partner choice and sanction should make cooperative
    behavior more stable than one-shot action classification.
    """

    def __init__(self, config: InterdependenceConfig) -> None:
        self.config = config
        self.norm_strength = config.initial_norm_strength
        self.agents = self._make_agents(config.population_size)
        if config.cooperative_cluster:
            self._seed_cooperative_cluster()

    def run(self) -> SimulationResult:
        records: list[InteractionRecord] = []

        for round_index in range(self.config.rounds):
            pairs = self._pair_agents(round_index)
            round_cooperations = 0
            round_actions = 0

            for agent_a, agent_b in pairs:
                action_a = self._choose_action(agent_a, agent_b)
                action_b = self._choose_action(agent_b, agent_a)
                payoff_a, payoff_b, sanctioned = self._apply_outcome(
                    agent_a,
                    agent_b,
                    action_a,
                    action_b,
                )

                round_cooperations += int(action_a == InteractionAction.COOPERATE)
                round_cooperations += int(action_b == InteractionAction.COOPERATE)
                round_actions += 2

                records.append(
                    InteractionRecord(
                        round_index=round_index,
                        agent_a=agent_a.agent_id,
                        agent_b=agent_b.agent_id,
                        action_a=action_a,
                        action_b=action_b,
                        payoff_a=payoff_a,
                        payoff_b=payoff_b,
                        sanctioned=sanctioned,
                        norm_strength=round(self.norm_strength, 3),
                    )
                )

            if round_actions:
                self._update_norm_strength(round_cooperations / round_actions)

        return self._result(records)

    @staticmethod
    def _make_agents(population_size: int) -> list[AgentState]:
        base_biases = (0.2, 0.35, 0.5, 0.65, 0.8, 0.95)
        return [
            AgentState(
                agent_id=f"agent_{index:02d}",
                prosocial_bias=base_biases[index % len(base_biases)],
            )
            for index in range(population_size)
        ]

    def _seed_cooperative_cluster(self) -> None:
        cluster_size = max(2, len(self.agents) // 3)
        for agent in sorted(self.agents, key=lambda item: item.prosocial_bias, reverse=True)[
            :cluster_size
        ]:
            agent.reputation = 0.8

    def _pair_agents(self, round_index: int) -> list[tuple[AgentState, AgentState]]:
        agents = list(self.agents)

        if self.config.partner_choice_enabled:
            agents.sort(key=lambda agent: (agent.reputation, agent.prosocial_bias), reverse=True)
        elif not self.config.repeated_interaction:
            shift = round_index % len(agents)
            agents = agents[shift:] + agents[:shift]
        else:
            # Stable partners without active partner choice.
            pass

        return [
            (agents[index], agents[index + 1])
            for index in range(0, len(agents) - 1, 2)
        ]

    def _choose_action(self, agent: AgentState, partner: AgentState) -> InteractionAction:
        if not self.config.repeated_interaction:
            # In a one-shot Stag Hunt, even generous agents face the risk-dominant
            # safe option because they cannot count on the partner showing up.
            trust = 0.30 + 0.20 * agent.prosocial_bias
        elif self.config.reputation_enabled:
            trust = (
                0.40 * partner.reputation
                + 0.30 * agent.prosocial_bias
                + 0.30 * self.norm_strength
            )
        else:
            trust = 0.55 * agent.prosocial_bias + 0.45 * self.norm_strength

        return (
            InteractionAction.COOPERATE
            if trust >= 0.55
            else InteractionAction.DEFECT
        )

    def _apply_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...]]:
        sanctioned: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 4.0
            self._adjust_reputation(agent_a, 0.08)
            self._adjust_reputation(agent_b, 0.08)
        elif action_a == InteractionAction.DEFECT and action_b == InteractionAction.DEFECT:
            payoff_a = payoff_b = 1.0
            self._adjust_reputation(agent_a, -0.04)
            self._adjust_reputation(agent_b, -0.04)
        elif action_a == InteractionAction.DEFECT:
            payoff_a, payoff_b = 3.0, 0.0
            self._adjust_reputation(agent_a, -0.08)
            self._adjust_reputation(agent_b, 0.03)
            if self.config.sanction_enabled:
                payoff_a -= 1.5
                self._adjust_reputation(agent_a, -0.22)
                sanctioned.append(agent_a.agent_id)
        else:
            payoff_a, payoff_b = 0.0, 3.0
            self._adjust_reputation(agent_a, 0.03)
            self._adjust_reputation(agent_b, -0.08)
            if self.config.sanction_enabled:
                payoff_b -= 1.5
                self._adjust_reputation(agent_b, -0.22)
                sanctioned.append(agent_b.agent_id)

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned)

    def _adjust_reputation(self, agent: AgentState, delta: float) -> None:
        if not self.config.reputation_enabled:
            return
        agent.reputation = min(1.0, max(0.0, agent.reputation + delta))

    def _update_norm_strength(self, cooperation_rate: float) -> None:
        if not self.config.sanction_enabled:
            return
        target = 0.15 + 0.85 * cooperation_rate
        self.norm_strength = 0.8 * self.norm_strength + 0.2 * target
        self.norm_strength = min(1.0, max(0.0, self.norm_strength))

    def _result(self, records: list[InteractionRecord]) -> SimulationResult:
        actions = [
            action
            for record in records
            for action in (record.action_a, record.action_b)
        ]
        betrayals = [
            record
            for record in records
            if {record.action_a, record.action_b}
            == {InteractionAction.COOPERATE, InteractionAction.DEFECT}
        ]
        total_payoff = sum(agent.payoff for agent in self.agents)
        total_reputation = sum(agent.reputation for agent in self.agents)

        return SimulationResult(
            condition=self.config.name,
            records=tuple(records),
            final_agents=tuple(self.agents),
            cooperation_rate=(
                sum(action == InteractionAction.COOPERATE for action in actions) / len(actions)
                if actions
                else 0.0
            ),
            betrayal_rate=len(betrayals) / len(records) if records else 0.0,
            mean_payoff=total_payoff / len(self.agents) if self.agents else 0.0,
            mean_reputation=total_reputation / len(self.agents) if self.agents else 0.0,
            norm_strength=self.norm_strength,
        )


def default_conditions() -> tuple[InterdependenceConfig, ...]:
    return (
        InterdependenceConfig(
            name="one_shot_baseline",
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
        ),
        InterdependenceConfig(
            name="repeated_no_sanction",
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=False,
            sanction_enabled=False,
        ),
        InterdependenceConfig(
            name="interdependent_norm_learning",
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.45,
            cooperative_cluster=True,
        ),
    )
