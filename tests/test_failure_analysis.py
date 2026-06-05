"""Tests for the routing failure analysis."""

from __future__ import annotations

import unittest

from bench.failure_analysis import analyze, render_report


class TestFailureAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        self.data = analyze()

    def test_unsafe_slips_include_held_out_twins(self) -> None:
        unsafe_ids = {f.scenario.id for f in self.data["unsafe"]}
        # The constructed held-out OOV twins are exactly the cases the scaffold cannot read.
        self.assertIn("twin_push_shared_bad", unsafe_ids)
        self.assertTrue(any(f.held_out for f in self.data["unsafe"]))

    def test_unsafe_slips_are_low_or_mid_stakes(self) -> None:
        # They slip precisely because the scaffold under-scores their stakes.
        for f in self.data["unsafe"]:
            self.assertLess(f.assessment.stakes, 0.7)

    def test_report_renders(self) -> None:
        report = render_report(self.data)
        self.assertIn("Failure Analysis", report)
        self.assertIn("Verdict", report)


if __name__ == "__main__":
    unittest.main()
