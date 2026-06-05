"""A small interdependence environment for moral-learning experiments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InteractionAction(StrEnum):
    COOPERATE = "cooperate"
    DEFECT = "defect"


class EnvironmentFamily(StrEnum):
    STAG_HUNT = "stag_hunt"
    COMMONS = "shared_resource_commons"
    DELEGATION = "delegation_with_accountability"


@dataclass(frozen=True)
class InterdependenceConfig:
    name: str
    family: EnvironmentFamily = EnvironmentFamily.STAG_HUNT
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
    repaired: tuple[str, ...] = ()
    norm_strength: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    condition: str
    records: tuple[InteractionRecord, ...]
    final_agents: tuple[AgentState, ...]
    cooperation_rate: float
    betrayal_rate: float
    repair_rate: float
    mean_payoff: float
    mean_reputation: float
    norm_strength: float
    norm_stability: float


class InterdependenceEnvironment:
    """Run repeated interdependence experiments.

    This is a scaffold, not a scientific model. It encodes the course mechanism:
    repeated dependence plus partner choice and sanction should make cooperative
    behavior more stable than one-shot action classification. Each environment
    family uses the same action vocabulary but different consequences.
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
            round_sanctions = 0

            for agent_a, agent_b in pairs:
                action_a = self._choose_action(agent_a, agent_b)
                action_b = self._choose_action(agent_b, agent_a)
                payoff_a, payoff_b, sanctioned, repaired = self._apply_outcome(
                    agent_a,
                    agent_b,
                    action_a,
                    action_b,
                )

                round_cooperations += int(action_a == InteractionAction.COOPERATE)
                round_cooperations += int(action_b == InteractionAction.COOPERATE)
                round_actions += 2
                round_sanctions += len(sanctioned)

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
                        repaired=repaired,
                        norm_strength=round(self.norm_strength, 3),
                    )
                )

            if round_actions:
                self._update_norm_strength(
                    cooperation_rate=round_cooperations / round_actions,
                    sanction_rate=round_sanctions / round_actions,
                )

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
            trust = self._one_shot_trust(agent)
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

    def _one_shot_trust(self, agent: AgentState) -> float:
        if self.config.family == EnvironmentFamily.STAG_HUNT:
            # In a one-shot Stag Hunt, even generous agents face the risk-dominant
            # safe option because they cannot count on the partner showing up.
            return 0.30 + 0.20 * agent.prosocial_bias
        if self.config.family == EnvironmentFamily.COMMONS:
            # In a commons, the one-shot temptation is to extract while the cost
            # is distributed.
            return 0.25 + 0.25 * agent.prosocial_bias
        # In delegation, the shortcut is tempting when there is no trace or
        # accountable review.
        return 0.20 + 0.25 * agent.prosocial_bias

    def _apply_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...]]:
        if self.config.family == EnvironmentFamily.COMMONS:
            return self._apply_commons_outcome(agent_a, agent_b, action_a, action_b)
        if self.config.family == EnvironmentFamily.DELEGATION:
            return self._apply_delegation_outcome(agent_a, agent_b, action_a, action_b)
        return self._apply_stag_hunt_outcome(agent_a, agent_b, action_a, action_b)

    def _apply_stag_hunt_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        repaired: list[str] = []

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
                repaired.extend(self._repair(agent_a))
        else:
            payoff_a, payoff_b = 0.0, 3.0
            self._adjust_reputation(agent_a, 0.03)
            self._adjust_reputation(agent_b, -0.08)
            if self.config.sanction_enabled:
                payoff_b -= 1.5
                self._adjust_reputation(agent_b, -0.22)
                sanctioned.append(agent_b.agent_id)
                repaired.extend(self._repair(agent_b))

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(repaired)

    def _apply_commons_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        repaired: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 3.2
            self._adjust_reputation(agent_a, 0.07)
            self._adjust_reputation(agent_b, 0.07)
        elif action_a == InteractionAction.DEFECT and action_b == InteractionAction.DEFECT:
            payoff_a = payoff_b = 0.6
            self._adjust_reputation(agent_a, -0.12)
            self._adjust_reputation(agent_b, -0.12)
            if self.config.sanction_enabled:
                sanctioned.extend((agent_a.agent_id, agent_b.agent_id))
                payoff_a -= 0.4
                payoff_b -= 0.4
                repaired.extend(self._repair(agent_a))
                repaired.extend(self._repair(agent_b))
        elif action_a == InteractionAction.DEFECT:
            payoff_a, payoff_b = 3.8, 1.0
            self._adjust_reputation(agent_a, -0.18)
            self._adjust_reputation(agent_b, 0.04)
            if self.config.sanction_enabled:
                payoff_a -= 1.3
                sanctioned.append(agent_a.agent_id)
                repaired.extend(self._repair(agent_a))
        else:
            payoff_a, payoff_b = 1.0, 3.8
            self._adjust_reputation(agent_a, 0.04)
            self._adjust_reputation(agent_b, -0.18)
            if self.config.sanction_enabled:
                payoff_b -= 1.3
                sanctioned.append(agent_b.agent_id)
                repaired.extend(self._repair(agent_b))

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(repaired)

    def _apply_delegation_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        repaired: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 3.5
            self._adjust_reputation(agent_a, 0.09)
            self._adjust_reputation(agent_b, 0.09)
        elif action_a == InteractionAction.DEFECT and action_b == InteractionAction.DEFECT:
            payoff_a = payoff_b = 1.1
            self._adjust_reputation(agent_a, -0.1)
            self._adjust_reputation(agent_b, -0.1)
            if self.config.sanction_enabled:
                sanctioned.extend((agent_a.agent_id, agent_b.agent_id))
                repaired.extend(self._repair(agent_a))
                repaired.extend(self._repair(agent_b))
        elif action_a == InteractionAction.DEFECT:
            payoff_a, payoff_b = 4.0, -0.5
            self._adjust_reputation(agent_a, -0.25)
            self._adjust_reputation(agent_b, 0.03)
            if self.config.sanction_enabled:
                payoff_a -= 2.0
                sanctioned.append(agent_a.agent_id)
                repaired.extend(self._repair(agent_a))
        else:
            payoff_a, payoff_b = -0.5, 4.0
            self._adjust_reputation(agent_a, 0.03)
            self._adjust_reputation(agent_b, -0.25)
            if self.config.sanction_enabled:
                payoff_b -= 2.0
                sanctioned.append(agent_b.agent_id)
                repaired.extend(self._repair(agent_b))

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(repaired)

    def _adjust_reputation(self, agent: AgentState, delta: float) -> None:
        if not self.config.reputation_enabled:
            return
        agent.reputation = min(1.0, max(0.0, agent.reputation + delta))

    def _repair(self, agent: AgentState) -> tuple[str, ...]:
        if not self.config.sanction_enabled or not self.config.reputation_enabled:
            return ()
        if agent.prosocial_bias + self.norm_strength < 1.05:
            return ()
        self._adjust_reputation(agent, 0.12)
        return (agent.agent_id,)

    def _update_norm_strength(self, cooperation_rate: float, sanction_rate: float) -> None:
        if not self.config.sanction_enabled:
            return
        enforcement_bonus = 0.15 * min(1.0, sanction_rate * 4)
        target = 0.15 + 0.70 * cooperation_rate + enforcement_bonus
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
        repairs = [agent_id for record in records for agent_id in record.repaired]
        total_payoff = sum(agent.payoff for agent in self.agents)
        total_reputation = sum(agent.reputation for agent in self.agents)
        norm_stability = self._norm_stability(records)

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
            repair_rate=len(repairs) / len(records) if records else 0.0,
            mean_payoff=total_payoff / len(self.agents) if self.agents else 0.0,
            mean_reputation=total_reputation / len(self.agents) if self.agents else 0.0,
            norm_strength=self.norm_strength,
            norm_stability=norm_stability,
        )

    @staticmethod
    def _norm_stability(records: list[InteractionRecord]) -> float:
        if not records:
            return 0.0
        final_round = max(record.round_index for record in records)
        late_records = [
            record for record in records if record.round_index >= max(0, final_round - 4)
        ]
        late_actions = [
            action
            for record in late_records
            for action in (record.action_a, record.action_b)
        ]
        if not late_actions:
            return 0.0
        return sum(action == InteractionAction.COOPERATE for action in late_actions) / len(
            late_actions
        )


def default_conditions() -> tuple[InterdependenceConfig, ...]:
    return (
        InterdependenceConfig(
            name="stag_hunt_one_shot",
            family=EnvironmentFamily.STAG_HUNT,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
        ),
        InterdependenceConfig(
            name="stag_hunt_repeated_no_sanction",
            family=EnvironmentFamily.STAG_HUNT,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=False,
            sanction_enabled=False,
        ),
        InterdependenceConfig(
            name="stag_hunt_interdependent",
            family=EnvironmentFamily.STAG_HUNT,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.45,
            cooperative_cluster=True,
        ),
        InterdependenceConfig(
            name="commons_one_shot",
            family=EnvironmentFamily.COMMONS,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
        ),
        InterdependenceConfig(
            name="commons_interdependent",
            family=EnvironmentFamily.COMMONS,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.5,
            cooperative_cluster=True,
        ),
        InterdependenceConfig(
            name="delegation_one_shot",
            family=EnvironmentFamily.DELEGATION,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
        ),
        InterdependenceConfig(
            name="delegation_interdependent",
            family=EnvironmentFamily.DELEGATION,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.55,
            cooperative_cluster=True,
        ),
    )
