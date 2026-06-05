"""Tests for persistent workspace memory."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_safety_os import MoralAgentOS, WorkspaceMemory, hydrate_context
from ai_safety_os.schema import (
    ContextSnapshot,
    Disposition,
    RelationshipState,
    Scenario,
    ScenarioLabel,
    Stakeholder,
)


def _scenario(id_: str, context: str) -> Scenario:
    return Scenario(
        id=id_,
        action_family="send_email",
        action_text="Send the quarterly numbers to the distribution list.",
        context=context,
        agent_role="workspace assistant",
        expected_label=ScenarioLabel.CLEAR_APPROPRIATE,
    )


class TestCorrections(unittest.TestCase):
    def test_lookup_returns_recorded_disposition(self) -> None:
        memory = WorkspaceMemory()
        scenario = _scenario("s1", "internal finance team, already shared")
        self.assertIsNone(memory.lookup(scenario))
        memory.record_correction(scenario, Disposition.AUTO)
        self.assertEqual(memory.lookup(scenario), Disposition.AUTO)

    def test_nearest_neighbor_generalizes_to_similar_situations(self) -> None:
        memory = WorkspaceMemory(similarity_threshold=0.5)
        trained = _scenario("s1", "internal finance team already shared final numbers")
        memory.record_correction(trained, Disposition.AUTO)
        # Same family/role, heavily overlapping context wording.
        similar = _scenario("s2", "internal finance team already shared the final numbers")
        self.assertEqual(memory.lookup(similar), Disposition.AUTO)

    def test_frozen_records_but_never_applies(self) -> None:
        memory = WorkspaceMemory(frozen=True)
        scenario = _scenario("s1", "internal finance team")
        memory.record_correction(scenario, Disposition.AUTO)
        self.assertEqual(memory.correction_count(), 1)
        self.assertIsNone(memory.lookup(scenario))

    def test_persists_across_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mem.sqlite"
            scenario = _scenario("s1", "internal finance team")
            WorkspaceMemory(path).record_correction(scenario, Disposition.AUTO)
            # A fresh instance on the same file sees the committed correction.
            self.assertEqual(WorkspaceMemory(path).lookup(scenario), Disposition.AUTO)


class TestRelationships(unittest.TestCase):
    def test_sanction_creates_repair_debt_cooperation_pays_it(self) -> None:
        memory = WorkspaceMemory()
        after_sanction = memory.observe_sanction("customer", severity=0.6)
        self.assertGreater(after_sanction.repair_obligation, 0.0)
        self.assertLess(after_sanction.trust, 0.5)

        after_repair = memory.observe_cooperation("customer", amount=0.3)
        self.assertLess(after_repair.repair_obligation, after_sanction.repair_obligation)
        self.assertGreater(after_repair.trust, after_sanction.trust)

    def test_relationship_round_trips(self) -> None:
        memory = WorkspaceMemory()
        memory.upsert_relationship(
            RelationshipState(stakeholder="vendor", dependency=0.8, public_review_required=True)
        )
        loaded = memory.relationship("vendor")
        self.assertAlmostEqual(loaded.dependency, 0.8)
        self.assertTrue(loaded.public_review_required)

    def test_review_history(self) -> None:
        memory = WorkspaceMemory()
        memory.record_review("customer", "act-1", "approved")
        memory.record_review("customer", "act-2", "blocked")
        history = memory.review_history("customer")
        self.assertEqual([r.outcome for r in history], ["approved", "blocked"])


class TestRuntimeIntegration(unittest.TestCase):
    def test_workspace_memory_drives_runtime_override(self) -> None:
        # An appropriate action the base router confirms can be relaxed to auto by memory.
        scenario = Scenario(
            id="loop_in",
            action_family="thread_escalation",
            action_text="Loop the manager into the customer thread.",
            context="The IC owner can resolve it; routine hand-off.",
            agent_role="customer ops assistant",
            expected_label=ScenarioLabel.CLEAR_APPROPRIATE,
        )
        memory = WorkspaceMemory()
        runtime = MoralAgentOS(memory=memory)
        before = runtime.evaluate(scenario).disposition
        memory.record_correction(scenario, Disposition.AUTO)
        after = runtime.evaluate(scenario).disposition
        # Memory can only relax to auto; it should never make things less safe.
        if before == Disposition.CONFIRM:
            self.assertEqual(after, Disposition.AUTO)

    def test_hydrate_context_fills_relationships_from_storage(self) -> None:
        memory = WorkspaceMemory()
        memory.observe_sanction("customer", severity=0.6)
        context = ContextSnapshot(
            agent_role="customer ops assistant",
            user_intent="Send a follow-up.",
            stakeholders=(Stakeholder(name="customer"),),
        )
        hydrated = hydrate_context(memory, context)
        self.assertEqual(len(hydrated.relationships), 1)
        self.assertGreater(hydrated.relationships[0].repair_obligation, 0.0)


if __name__ == "__main__":
    unittest.main()
