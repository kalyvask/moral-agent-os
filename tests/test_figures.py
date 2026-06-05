"""Tests that the SVG figure helpers emit well-formed, in-bounds charts."""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET

from bench import figures


def _viewbox(svg: str) -> tuple[int, int]:
    match = re.search(r"viewBox='0 0 (\d+) (\d+)'", svg)
    assert match
    return int(match.group(1)), int(match.group(2))


def _rects_in_bounds(svg: str, width: int, height: int) -> bool:
    for rx, ry, rw, rh in re.findall(
        r"<rect x='([-\d.]+)' y='([-\d.]+)' width='([\d.]+)' height='([\d.]+)'", svg
    ):
        if float(rx) + float(rw) > width + 1 or float(ry) + float(rh) > height + 1:
            return False
        if float(rx) < -1 or float(ry) < -1:
            return False
    return True


class TestFigures(unittest.TestCase):
    def test_grouped_bar_is_valid_and_in_bounds(self) -> None:
        svg = figures.grouped_bar_chart(
            "Title",
            group_labels=["Cooperation", "Autonomous coop."],
            series_labels=["One-shot", "Interdependent"],
            values=[[0.0, 0.3], [0.9, 0.8]],
        )
        ET.fromstring(svg)  # raises on malformed XML
        self.assertTrue(_rects_in_bounds(svg, *_viewbox(svg)))

    def test_scatter_labels_stay_on_canvas(self) -> None:
        svg = figures.scatter_frontier(
            "Frontier",
            [
                figures.ScatterPoint(0.12, 0.20, "normos"),
                figures.ScatterPoint(1.0, 0.0, "always_confirm"),  # right edge
            ],
            x_label="x",
            y_label="y",
        )
        width, _ = _viewbox(svg)
        ET.fromstring(svg)
        # The right-edge label must be anchored to the end so it does not clip.
        self.assertIn("text-anchor='end'", svg)
        for tx in re.findall(r"<text x='([-\d.]+)'", svg):
            self.assertLessEqual(float(tx), width + 2)

    def test_confusion_matrix_renders_counts(self) -> None:
        svg = figures.confusion_matrix(
            "Confusion",
            row_labels=["clear_appropriate", "clear_inappropriate", "plural"],
            col_labels=["auto", "confirm", "escalate", "block"],
            counts=[[22, 1, 2, 0], [5, 3, 7, 10], [2, 0, 2, 0]],
        )
        ET.fromstring(svg)
        self.assertTrue(_rects_in_bounds(svg, *_viewbox(svg)))
        self.assertIn(">22<", svg)


if __name__ == "__main__":
    unittest.main()
