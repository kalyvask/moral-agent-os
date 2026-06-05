"""Tests for inter-rater agreement metrics."""

from __future__ import annotations

import unittest

from labeling.agreement import (
    agreement_rate,
    cohen_kappa,
    fleiss_kappa,
    interpret_kappa,
    majority_consensus,
)


class TestCohenKappa(unittest.TestCase):
    def test_perfect_agreement(self) -> None:
        a = {"1": "x", "2": "y", "3": "x"}
        self.assertEqual(cohen_kappa(a, dict(a)), 1.0)
        self.assertEqual(agreement_rate(a, dict(a)), 1.0)

    def test_total_disagreement_is_negative(self) -> None:
        a = {"1": "x", "2": "x", "3": "y", "4": "y"}
        b = {"1": "y", "2": "y", "3": "x", "4": "x"}
        self.assertLess(cohen_kappa(a, b), 0.0)

    def test_known_value(self) -> None:
        # 8/10 agree; marginals chosen so expected agreement is 0.5 -> kappa 0.6.
        a = {str(i): "x" for i in range(5)} | {str(i): "y" for i in range(5, 10)}
        b = dict(a)
        b["0"] = "y"  # one x->y flip
        b["5"] = "x"  # one y->x flip
        # observed 0.8; marginals 0.5/0.5 each -> expected 0.5 -> kappa 0.6
        self.assertAlmostEqual(cohen_kappa(a, b), 0.6, places=2)


class TestFleissKappa(unittest.TestCase):
    def test_all_raters_agree(self) -> None:
        labels = {"1": "a", "2": "b", "3": "a"}
        self.assertEqual(fleiss_kappa([dict(labels), dict(labels), dict(labels)]), 1.0)

    def test_partial_agreement_between_zero_and_one(self) -> None:
        r1 = {"1": "a", "2": "a", "3": "b", "4": "b"}
        r2 = {"1": "a", "2": "b", "3": "b", "4": "a"}
        r3 = {"1": "a", "2": "a", "3": "b", "4": "b"}
        kappa = fleiss_kappa([r1, r2, r3])
        self.assertGreater(kappa, -1.0)
        self.assertLess(kappa, 1.0)


class TestConsensus(unittest.TestCase):
    def test_majority(self) -> None:
        r1 = {"1": "a", "2": "b"}
        r2 = {"1": "a", "2": "a"}
        r3 = {"1": "b", "2": "a"}
        self.assertEqual(majority_consensus([r1, r2, r3]), {"1": "a", "2": "a"})


class TestInterpret(unittest.TestCase):
    def test_bands(self) -> None:
        self.assertEqual(interpret_kappa(-0.1), "poor (worse than chance)")
        self.assertEqual(interpret_kappa(0.5), "moderate")
        self.assertEqual(interpret_kappa(0.7), "substantial")
        self.assertEqual(interpret_kappa(0.9), "almost perfect")


if __name__ == "__main__":
    unittest.main()
