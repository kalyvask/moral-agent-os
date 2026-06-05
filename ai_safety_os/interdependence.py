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
    ASYMMETRIC_DEPENDENCE = "asymmetric_dependence"


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
    static_policy_enabled: bool = False
    third_party_enforcement_enabled: bool = False
    shared_intent_enabled: bool = False


@dataclass
class AgentState:
    agent_id: str
    prosocial_bias: float
    reputation: float = 0.5
    payoff: float = 0.0
    repair_obligation: float = 0.0


@dataclass(frozen=True)
class InteractionRecord:
    round_index: int
    agent_a: str
    agent_b: str
    action_a: InteractionAction
    action_b: InteractionAction
    payoff_a: float
    payoff_b: float
    blocked: tuple[str, ...] = ()
    sanctioned: tuple[str, ...] = ()
    reviewed: tuple[str, ...] = ()
    repaired: tuple[str, ...] = ()
    joint_commitment: bool = False
    norm_strength: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    condition: str
    family: EnvironmentFamily
    records: tuple[InteractionRecord, ...]
    final_agents: tuple[AgentState, ...]
    cooperation_rate: float
    autonomous_cooperation_rate: float
    blocked_rate: float
    betrayal_rate: float
    repair_rate: float
    mean_repair_obligation: float
    stewardship_rate: float
    dependent_harm_rate: float
    third_party_review_rate: float
    joint_commitment_rate: float
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
            round_reviews = 0
            round_joint_commitments = 0

            for agent_a, agent_b in pairs:
                joint_commitment = self._forms_joint_commitment(agent_a, agent_b)
                action_a, blocked_a = self._choose_action_with_policy(
                    agent_a,
                    agent_b,
                    joint_commitment,
                )
                action_b, blocked_b = self._choose_action_with_policy(
                    agent_b,
                    agent_a,
                    joint_commitment,
                )
                payoff_a, payoff_b, sanctioned, reviewed, repaired = self._apply_outcome(
                    agent_a,
                    agent_b,
                    action_a,
                    action_b,
                )

                round_cooperations += int(action_a == InteractionAction.COOPERATE)
                round_cooperations += int(action_b == InteractionAction.COOPERATE)
                round_actions += 2
                round_sanctions += len(sanctioned)
                round_reviews += len(reviewed)
                round_joint_commitments += int(joint_commitment)

                records.append(
                    InteractionRecord(
                        round_index=round_index,
                        agent_a=agent_a.agent_id,
                        agent_b=agent_b.agent_id,
                        action_a=action_a,
                        action_b=action_b,
                        payoff_a=payoff_a,
                        payoff_b=payoff_b,
                        blocked=tuple(
                            agent.agent_id
                            for agent, blocked in (
                                (agent_a, blocked_a),
                                (agent_b, blocked_b),
                            )
                            if blocked
                        ),
                        sanctioned=sanctioned,
                        reviewed=reviewed,
                        repaired=repaired,
                        joint_commitment=joint_commitment,
                        norm_strength=round(self.norm_strength, 3),
                    )
                )

            if round_actions:
                self._update_norm_strength(
                    cooperation_rate=round_cooperations / round_actions,
                    sanction_rate=round_sanctions / round_actions,
                    review_rate=round_reviews / round_actions,
                    joint_commitment_rate=(
                        round_joint_commitments / len(pairs) if pairs else 0.0
                    ),
                )
                self._apply_unrepaired_obligation_drag()

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

    def _choose_action_with_policy(
        self,
        agent: AgentState,
        partner: AgentState,
        joint_commitment: bool = False,
    ) -> tuple[InteractionAction, bool]:
        desired_action = self._choose_action(agent, partner, joint_commitment)
        if (
            self.config.static_policy_enabled
            and desired_action == InteractionAction.DEFECT
        ):
            return InteractionAction.COOPERATE, True
        return desired_action, False

    def _choose_action(
        self,
        agent: AgentState,
        partner: AgentState,
        joint_commitment: bool = False,
    ) -> InteractionAction:
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

        if self.config.sanction_enabled and agent.repair_obligation > 0.0:
            trust += 0.35 * agent.repair_obligation
        if self.config.third_party_enforcement_enabled:
            trust += 0.05 + 0.10 * self.norm_strength
        if joint_commitment:
            trust += 0.28

        return (
            InteractionAction.COOPERATE
            if trust >= 0.55
            else InteractionAction.DEFECT
        )

    def _forms_joint_commitment(self, agent_a: AgentState, agent_b: AgentState) -> bool:
        if not self.config.shared_intent_enabled or not self.config.repeated_interaction:
            return False
        readiness = (
            0.30 * min(agent_a.reputation, agent_b.reputation)
            + 0.30 * min(agent_a.prosocial_bias, agent_b.prosocial_bias)
            + 0.40 * self.norm_strength
        )
        return readiness >= 0.48

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
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        if self.config.family == EnvironmentFamily.COMMONS:
            return self._apply_commons_outcome(agent_a, agent_b, action_a, action_b)
        if self.config.family == EnvironmentFamily.DELEGATION:
            return self._apply_delegation_outcome(agent_a, agent_b, action_a, action_b)
        if self.config.family == EnvironmentFamily.ASYMMETRIC_DEPENDENCE:
            return self._apply_asymmetric_dependence_outcome(
                agent_a,
                agent_b,
                action_a,
                action_b,
            )
        return self._apply_stag_hunt_outcome(agent_a, agent_b, action_a, action_b)

    def _apply_stag_hunt_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        reviewed: list[str] = []
        repaired: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 4.0
            self._adjust_reputation(agent_a, 0.08)
            self._adjust_reputation(agent_b, 0.08)
            payoff_a -= self._attempt_repair(agent_a, repaired)
            payoff_b -= self._attempt_repair(agent_b, repaired)
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
                self._add_repair_obligation(agent_a, 0.35)
                self._review_violation(agent_a, reviewed, 0.10)
        else:
            payoff_a, payoff_b = 0.0, 3.0
            self._adjust_reputation(agent_a, 0.03)
            self._adjust_reputation(agent_b, -0.08)
            if self.config.sanction_enabled:
                payoff_b -= 1.5
                self._adjust_reputation(agent_b, -0.22)
                sanctioned.append(agent_b.agent_id)
                self._add_repair_obligation(agent_b, 0.35)
                self._review_violation(agent_b, reviewed, 0.10)

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(reviewed), tuple(repaired)

    def _apply_commons_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        reviewed: list[str] = []
        repaired: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 3.2
            self._adjust_reputation(agent_a, 0.07)
            self._adjust_reputation(agent_b, 0.07)
            payoff_a -= self._attempt_repair(agent_a, repaired)
            payoff_b -= self._attempt_repair(agent_b, repaired)
        elif action_a == InteractionAction.DEFECT and action_b == InteractionAction.DEFECT:
            payoff_a = payoff_b = 0.6
            self._adjust_reputation(agent_a, -0.12)
            self._adjust_reputation(agent_b, -0.12)
            if self.config.sanction_enabled:
                sanctioned.extend((agent_a.agent_id, agent_b.agent_id))
                payoff_a -= 0.4
                payoff_b -= 0.4
                self._add_repair_obligation(agent_a, 0.25)
                self._add_repair_obligation(agent_b, 0.25)
                self._review_violation(agent_a, reviewed, 0.08)
                self._review_violation(agent_b, reviewed, 0.08)
        elif action_a == InteractionAction.DEFECT:
            payoff_a, payoff_b = 3.8, 1.0
            self._adjust_reputation(agent_a, -0.18)
            self._adjust_reputation(agent_b, 0.04)
            if self.config.sanction_enabled:
                payoff_a -= 1.3
                sanctioned.append(agent_a.agent_id)
                self._add_repair_obligation(agent_a, 0.35)
                self._review_violation(agent_a, reviewed, 0.12)
        else:
            payoff_a, payoff_b = 1.0, 3.8
            self._adjust_reputation(agent_a, 0.04)
            self._adjust_reputation(agent_b, -0.18)
            if self.config.sanction_enabled:
                payoff_b -= 1.3
                sanctioned.append(agent_b.agent_id)
                self._add_repair_obligation(agent_b, 0.35)
                self._review_violation(agent_b, reviewed, 0.12)

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(reviewed), tuple(repaired)

    def _apply_delegation_outcome(
        self,
        agent_a: AgentState,
        agent_b: AgentState,
        action_a: InteractionAction,
        action_b: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        reviewed: list[str] = []
        repaired: list[str] = []

        if action_a == InteractionAction.COOPERATE and action_b == InteractionAction.COOPERATE:
            payoff_a = payoff_b = 3.5
            self._adjust_reputation(agent_a, 0.09)
            self._adjust_reputation(agent_b, 0.09)
            payoff_a -= self._attempt_repair(agent_a, repaired)
            payoff_b -= self._attempt_repair(agent_b, repaired)
        elif action_a == InteractionAction.DEFECT and action_b == InteractionAction.DEFECT:
            payoff_a = payoff_b = 1.1
            self._adjust_reputation(agent_a, -0.1)
            self._adjust_reputation(agent_b, -0.1)
            if self.config.sanction_enabled:
                sanctioned.extend((agent_a.agent_id, agent_b.agent_id))
                self._add_repair_obligation(agent_a, 0.30)
                self._add_repair_obligation(agent_b, 0.30)
                self._review_violation(agent_a, reviewed, 0.10)
                self._review_violation(agent_b, reviewed, 0.10)
        elif action_a == InteractionAction.DEFECT:
            payoff_a, payoff_b = 4.0, -0.5
            self._adjust_reputation(agent_a, -0.25)
            self._adjust_reputation(agent_b, 0.03)
            if self.config.sanction_enabled:
                payoff_a -= 2.0
                sanctioned.append(agent_a.agent_id)
                self._add_repair_obligation(agent_a, 0.45)
                self._review_violation(agent_a, reviewed, 0.15)
        else:
            payoff_a, payoff_b = -0.5, 4.0
            self._adjust_reputation(agent_a, 0.03)
            self._adjust_reputation(agent_b, -0.25)
            if self.config.sanction_enabled:
                payoff_b -= 2.0
                sanctioned.append(agent_b.agent_id)
                self._add_repair_obligation(agent_b, 0.45)
                self._review_violation(agent_b, reviewed, 0.15)

        agent_a.payoff += payoff_a
        agent_b.payoff += payoff_b
        return payoff_a, payoff_b, tuple(sanctioned), tuple(reviewed), tuple(repaired)

    def _apply_asymmetric_dependence_outcome(
        self,
        steward: AgentState,
        dependent: AgentState,
        steward_action: InteractionAction,
        dependent_action: InteractionAction,
    ) -> tuple[float, float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        sanctioned: list[str] = []
        reviewed: list[str] = []
        repaired: list[str] = []
        self._record_review(steward, reviewed)

        if (
            steward_action == InteractionAction.COOPERATE
            and dependent_action == InteractionAction.COOPERATE
        ):
            steward_payoff, dependent_payoff = 3.2, 4.2
            self._adjust_reputation(steward, 0.10)
            self._adjust_reputation(dependent, 0.05)
            steward_payoff -= self._attempt_repair(steward, repaired)
            dependent_payoff -= self._attempt_repair(dependent, repaired)
        elif (
            steward_action == InteractionAction.DEFECT
            and dependent_action == InteractionAction.COOPERATE
        ):
            steward_payoff, dependent_payoff = 4.6, -1.4
            self._adjust_reputation(steward, -0.30)
            self._adjust_reputation(dependent, 0.02)
            if self.config.sanction_enabled:
                steward_payoff -= 2.2
                sanctioned.append(steward.agent_id)
                self._add_repair_obligation(steward, 0.60)
                self._review_violation(steward, reviewed, 0.20)
        elif steward_action == InteractionAction.COOPERATE:
            steward_payoff, dependent_payoff = 1.0, 1.8
            self._adjust_reputation(steward, 0.04)
            self._adjust_reputation(dependent, -0.05)
        else:
            steward_payoff, dependent_payoff = 1.2, 0.4
            self._adjust_reputation(steward, -0.12)
            self._adjust_reputation(dependent, -0.03)
            if self.config.sanction_enabled:
                sanctioned.append(steward.agent_id)
                self._add_repair_obligation(steward, 0.25)
                self._review_violation(steward, reviewed, 0.10)

        steward.payoff += steward_payoff
        dependent.payoff += dependent_payoff
        return steward_payoff, dependent_payoff, tuple(sanctioned), tuple(reviewed), tuple(repaired)

    def _adjust_reputation(self, agent: AgentState, delta: float) -> None:
        if not self.config.reputation_enabled:
            return
        agent.reputation = min(1.0, max(0.0, agent.reputation + delta))

    def _add_repair_obligation(self, agent: AgentState, amount: float) -> None:
        if not self.config.sanction_enabled or not self.config.reputation_enabled:
            return
        agent.repair_obligation = min(1.0, agent.repair_obligation + amount)

    def _review_violation(
        self,
        agent: AgentState,
        reviewed: list[str],
        obligation_bonus: float,
    ) -> None:
        if not self.config.third_party_enforcement_enabled:
            return
        self._record_review(agent, reviewed)
        self._adjust_reputation(agent, -0.10)
        self._add_repair_obligation(agent, obligation_bonus)

    def _record_review(self, agent: AgentState, reviewed: list[str]) -> None:
        if not self.config.third_party_enforcement_enabled:
            return
        if agent.agent_id not in reviewed:
            reviewed.append(agent.agent_id)

    def _attempt_repair(self, agent: AgentState, repaired: list[str]) -> float:
        if not self.config.sanction_enabled or not self.config.reputation_enabled:
            return 0.0
        if agent.repair_obligation <= 0.0:
            return 0.0
        if agent.prosocial_bias + self.norm_strength + agent.repair_obligation < 0.90:
            return 0.0

        repair_amount = min(
            agent.repair_obligation,
            0.20 + 0.20 * agent.prosocial_bias,
        )
        agent.repair_obligation = max(0.0, agent.repair_obligation - repair_amount)
        self._adjust_reputation(agent, 0.10 + 0.25 * repair_amount)
        repaired.append(agent.agent_id)
        return 0.50 * repair_amount

    def _apply_unrepaired_obligation_drag(self) -> None:
        if not self.config.sanction_enabled or not self.config.reputation_enabled:
            return
        for agent in self.agents:
            if agent.repair_obligation > 0.0:
                self._adjust_reputation(agent, -0.01 * agent.repair_obligation)

    def _update_norm_strength(
        self,
        cooperation_rate: float,
        sanction_rate: float,
        review_rate: float,
        joint_commitment_rate: float,
    ) -> None:
        if (
            not self.config.sanction_enabled
            and not self.config.shared_intent_enabled
            and not self.config.third_party_enforcement_enabled
        ):
            return
        enforcement_bonus = 0.0
        if self.config.sanction_enabled:
            enforcement_bonus = 0.15 * min(1.0, sanction_rate * 4)
        review_bonus = 0.0
        if self.config.third_party_enforcement_enabled:
            review_bonus = 0.20 * min(1.0, review_rate * 4)
        joint_bonus = 0.0
        if self.config.shared_intent_enabled:
            joint_bonus = 0.18 * joint_commitment_rate
        target = (
            0.15
            + 0.70 * cooperation_rate
            + enforcement_bonus
            + review_bonus
            + joint_bonus
        )
        inertia = 0.75 if self.config.third_party_enforcement_enabled else 0.8
        self.norm_strength = inertia * self.norm_strength + (1 - inertia) * target
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
        blocked = [agent_id for record in records for agent_id in record.blocked]
        reviewed_records = [record for record in records if record.reviewed]
        joint_commitments = [record for record in records if record.joint_commitment]
        dependent_harms = [
            record
            for record in records
            if self.config.family == EnvironmentFamily.ASYMMETRIC_DEPENDENCE
            and record.action_a == InteractionAction.DEFECT
        ]
        cooperation_count = sum(action == InteractionAction.COOPERATE for action in actions)
        autonomous_cooperation_count = max(0, cooperation_count - len(blocked))
        steward_cooperation_count = sum(
            record.action_a == InteractionAction.COOPERATE
            for record in records
        )
        total_payoff = sum(agent.payoff for agent in self.agents)
        total_reputation = sum(agent.reputation for agent in self.agents)
        total_repair_obligation = sum(agent.repair_obligation for agent in self.agents)
        norm_stability = self._norm_stability(records)

        return SimulationResult(
            condition=self.config.name,
            family=self.config.family,
            records=tuple(records),
            final_agents=tuple(self.agents),
            cooperation_rate=(
                cooperation_count / len(actions) if actions else 0.0
            ),
            autonomous_cooperation_rate=(
                autonomous_cooperation_count / len(actions) if actions else 0.0
            ),
            blocked_rate=len(blocked) / len(actions) if actions else 0.0,
            betrayal_rate=len(betrayals) / len(records) if records else 0.0,
            repair_rate=len(repairs) / len(records) if records else 0.0,
            mean_repair_obligation=(
                total_repair_obligation / len(self.agents) if self.agents else 0.0
            ),
            stewardship_rate=(
                steward_cooperation_count / len(records)
                if records and self.config.family == EnvironmentFamily.ASYMMETRIC_DEPENDENCE
                else 0.0
            ),
            dependent_harm_rate=(
                len(dependent_harms) / len(records)
                if records and self.config.family == EnvironmentFamily.ASYMMETRIC_DEPENDENCE
                else 0.0
            ),
            third_party_review_rate=(
                len(reviewed_records) / len(records) if records else 0.0
            ),
            joint_commitment_rate=(
                len(joint_commitments) / len(records) if records else 0.0
            ),
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
            name="stag_hunt_static_policy",
            family=EnvironmentFamily.STAG_HUNT,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
            static_policy_enabled=True,
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
            name="stag_hunt_shared_intent",
            family=EnvironmentFamily.STAG_HUNT,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=False,
            initial_norm_strength=0.45,
            cooperative_cluster=True,
            shared_intent_enabled=True,
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
            name="commons_static_policy",
            family=EnvironmentFamily.COMMONS,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
            static_policy_enabled=True,
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
            name="delegation_static_policy",
            family=EnvironmentFamily.DELEGATION,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
            static_policy_enabled=True,
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
        InterdependenceConfig(
            name="asymmetric_one_shot",
            family=EnvironmentFamily.ASYMMETRIC_DEPENDENCE,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
        ),
        InterdependenceConfig(
            name="asymmetric_static_policy",
            family=EnvironmentFamily.ASYMMETRIC_DEPENDENCE,
            repeated_interaction=False,
            reputation_enabled=False,
            partner_choice_enabled=False,
            sanction_enabled=False,
            initial_norm_strength=0.0,
            static_policy_enabled=True,
        ),
        InterdependenceConfig(
            name="asymmetric_interdependent",
            family=EnvironmentFamily.ASYMMETRIC_DEPENDENCE,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.6,
            cooperative_cluster=True,
        ),
        InterdependenceConfig(
            name="asymmetric_third_party_enforced",
            family=EnvironmentFamily.ASYMMETRIC_DEPENDENCE,
            repeated_interaction=True,
            reputation_enabled=True,
            partner_choice_enabled=True,
            sanction_enabled=True,
            initial_norm_strength=0.6,
            cooperative_cluster=True,
            third_party_enforcement_enabled=True,
        ),
    )
