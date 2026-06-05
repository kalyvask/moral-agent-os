"""Inter-rater agreement metrics (pure standard library).

The premise of the project is that moral competence is shared, not one author's intuition.
So the scenario labels need to be checked against independent judges. This module computes
Cohen's kappa (two raters), Fleiss' kappa (many raters), majority consensus, and plain
agreement, with a Landis-Koch reading of the kappa value. It is agnostic to where the
labels come from: independent people, or independent models (see labeling/model_raters.py).

Labels are dicts of ``{scenario_id: label}``; metrics are computed over the shared ids.
"""

from __future__ import annotations

from collections import Counter

LabelMap = dict[str, str]


def agreement_rate(a: LabelMap, b: LabelMap) -> float:
    ids = sorted(set(a) & set(b))
    if not ids:
        return 0.0
    return sum(1 for i in ids if a[i] == b[i]) / len(ids)


def cohen_kappa(a: LabelMap, b: LabelMap) -> float:
    """Cohen's kappa between two raters over their shared items."""
    ids = sorted(set(a) & set(b))
    if not ids:
        return 0.0
    n = len(ids)
    categories = {a[i] for i in ids} | {b[i] for i in ids}
    observed = sum(1 for i in ids if a[i] == b[i]) / n
    marg_a = {c: sum(1 for i in ids if a[i] == c) / n for c in categories}
    marg_b = {c: sum(1 for i in ids if b[i] == c) / n for c in categories}
    expected = sum(marg_a[c] * marg_b[c] for c in categories)
    if expected >= 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def fleiss_kappa(raters: list[LabelMap]) -> float:
    """Fleiss' kappa across N raters who each labeled the same items."""
    if len(raters) < 2:
        return 1.0
    ids = sorted(set.intersection(*[set(r) for r in raters]))
    if not ids:
        return 0.0
    categories = sorted({r[i] for r in raters for i in ids})
    n_raters = len(raters)

    counts = []  # per item: category -> count
    for i in ids:
        row = Counter(r[i] for r in raters)
        counts.append({c: row.get(c, 0) for c in categories})

    # Mean per-item agreement.
    p_item = [
        sum(v * (v - 1) for v in row.values()) / (n_raters * (n_raters - 1))
        for row in counts
    ]
    p_bar = sum(p_item) / len(ids)

    # Expected agreement from category prevalence.
    prevalence = {
        c: sum(row[c] for row in counts) / (len(ids) * n_raters) for c in categories
    }
    p_expected = sum(p * p for p in prevalence.values())
    if p_expected >= 1.0:
        return 1.0
    return (p_bar - p_expected) / (1 - p_expected)


def majority_consensus(raters: list[LabelMap]) -> LabelMap:
    """Majority label per item across raters (ties broken by sorted order)."""
    if not raters:
        return {}
    ids = sorted(set.intersection(*[set(r) for r in raters]))
    consensus: LabelMap = {}
    for i in ids:
        counts = Counter(r[i] for r in raters)
        top = max(counts.values())
        consensus[i] = sorted(c for c, n in counts.items() if n == top)[0]
    return consensus


def interpret_kappa(kappa: float) -> str:
    """Landis-Koch (1977) reading of a kappa value."""
    if kappa < 0.0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"
