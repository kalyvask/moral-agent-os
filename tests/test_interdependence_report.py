from __future__ import annotations

import unittest

from bench.interdependence import run_all
from bench.report_interdependence import render_report


class InterdependenceReportTest(unittest.TestCase):
    def test_report_separates_static_policy_from_interdependence(self) -> None:
        report = render_report(run_all())

        self.assertIn("Static policy forces", report)
        self.assertIn("Interdependence produces", report)
        self.assertIn("Autonomous cooperation", report)
        self.assertIn("Norm strength", report)
        self.assertIn("Repair debt", report)
        self.assertIn("Asymmetric Dependence", report)
        self.assertIn("Dependent harm", report)


if __name__ == "__main__":
    unittest.main()
