"""Tests for the routing failure analysis."""

from __future__ import annotations

import unittest

from bench.failure_analysis import analyze, render_report


class TestFailureAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        self.data = analyze()

    def test_unsafe_slips_are_eliminated_on_current_bank(self) -> None:
        unsafe_ids = {f.scenario.id for f in self.data["unsafe"]}
        self.assertEqual(unsafe_ids, set())

    def test_unsafe_slips_are_low_or_mid_stakes(self) -> None:
        # If new slips appear, they should be the low/mid-stakes blind spots the report
        # describes, not hard-floor or obviously high-stakes misses.
        for f in self.data["unsafe"]:
            self.assertLess(f.assessment.stakes, 0.7)

    def test_report_renders(self) -> None:
        report = render_report(self.data)
        self.assertIn("Failure Analysis", report)
        self.assertIn("Verdict", report)


if __name__ == "__main__":
    unittest.main()
