"""The review console's interdependence wiring: approve builds standing, flag erodes it."""

from __future__ import annotations

import unittest

from ai_safety_os import WorkspaceMemory
from web.app import SCENARIOS, apply_review


def _a_scenario():
    return next(iter(SCENARIOS.values()))


class ConsoleReviewTest(unittest.TestCase):
    def test_all_relationships_lists_stored_state(self) -> None:
        memory = WorkspaceMemory()
        memory.observe_sanction("acme")
        memory.observe_cooperation("globex")
        names = {rel.stakeholder for rel in memory.all_relationships()}
        self.assertEqual(names, {"acme", "globex"})

    def test_approve_builds_trust(self) -> None:
        memory = WorkspaceMemory()
        apply_review(memory, _a_scenario(), approve=True)
        rels = memory.all_relationships()
        self.assertTrue(rels)  # at least the implicit "user" stakeholder now has state
        self.assertTrue(all(rel.trust >= 0.5 for rel in rels))
        self.assertTrue(any(rel.trust > 0.5 for rel in rels))

    def test_flag_sanctions_stakeholders(self) -> None:
        memory = WorkspaceMemory()
        apply_review(memory, _a_scenario(), approve=False)
        rels = memory.all_relationships()
        self.assertTrue(rels)
        self.assertTrue(any(rel.repair_obligation > 0.0 for rel in rels))
        self.assertTrue(any(rel.trust < 0.5 for rel in rels))


if __name__ == "__main__":
    unittest.main()
