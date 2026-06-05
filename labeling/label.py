"""Tiny labeling helper placeholder.

Usage:
    python labeling/label.py
"""

from __future__ import annotations

from bench.run import load_scenarios


def main() -> None:
    for scenario in load_scenarios():
        print(f"{scenario.id}: {scenario.expected_label}")
        print(f"  action: {scenario.action_text}")
        print(f"  context: {scenario.context}")
        print()


if __name__ == "__main__":
    main()
