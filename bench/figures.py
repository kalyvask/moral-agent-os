"""Pure-Python SVG chart helpers.

The repo is deliberately dependency-free, so figures are emitted as hand-built SVG rather
than via matplotlib. SVG renders inline on GitHub and stays diff-friendly. These helpers
cover the three shapes the benchmark needs: grouped bars, a scatter frontier, and a
confusion matrix.
"""

from __future__ import annotations

from dataclasses import dataclass

# Calm, distinct palette (no purple-on-white gradient).
PALETTE = ["#2f6f8f", "#c1666b", "#6a8f4f", "#d9a441", "#7d6f9c", "#4f4f4f"]
FONT = "font-family='Segoe UI, Helvetica, Arial, sans-serif'"
AXIS = "#444"
GRID = "#dddddd"


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&#39;")
    )


def _text(x: float, y: float, s: str, size: int = 13, anchor: str = "start",
          color: str = "#222", weight: str = "normal", rotate: float | None = None) -> str:
    transform = f" transform='rotate({rotate} {x} {y})'" if rotate is not None else ""
    return (
        f"<text x='{x:.1f}' y='{y:.1f}' {FONT} font-size='{size}' "
        f"fill='{color}' font-weight='{weight}' text-anchor='{anchor}'{transform}>"
        f"{_esc(s)}</text>"
    )


def _pct(value: float) -> str:
    return f"{value:.0%}"


def grouped_bar_chart(
    title: str,
    group_labels: list[str],
    series_labels: list[str],
    values: list[list[float]],
    *,
    y_max: float = 1.0,
    subtitle: str = "",
) -> str:
    """Grouped bars. ``values[series][group]`` in [0, y_max]."""
    width, height = 820, 470
    left, right, top, bottom = 56, 200, 64, 118
    plot_w = width - left - right
    plot_h = height - top - bottom
    n_groups = len(group_labels)
    n_series = len(series_labels)
    group_w = plot_w / max(n_groups, 1)
    bar_w = group_w / (n_series + 0.6)

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' "
        f"width='{width}' height='{height}' role='img'>",
        f"<rect width='{width}' height='{height}' fill='white'/>",
        _text(left, 28, title, size=18, weight="bold"),
    ]
    if subtitle:
        parts.append(_text(left, 48, subtitle, size=12, color="#666"))

    # Gridlines + y-axis labels.
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = top + plot_h * (1 - frac)
        parts.append(
            f"<line x1='{left}' y1='{y:.1f}' x2='{left + plot_w}' y2='{y:.1f}' "
            f"stroke='{GRID}' stroke-width='1'/>"
        )
        parts.append(_text(left - 8, y + 4, _pct(frac * y_max), size=11,
                           anchor="end", color="#666"))

    # Bars.
    for g, group in enumerate(group_labels):
        gx = left + g * group_w
        for s in range(n_series):
            value = max(0.0, min(y_max, values[s][g]))
            bh = plot_h * (value / y_max) if y_max else 0
            bx = gx + 0.3 * bar_w + s * bar_w
            by = top + plot_h - bh
            parts.append(
                f"<rect x='{bx:.1f}' y='{by:.1f}' width='{bar_w:.1f}' height='{bh:.1f}' "
                f"fill='{PALETTE[s % len(PALETTE)]}'/>"
            )
        # Group label (wrapped onto two lines if long).
        cx = gx + group_w / 2
        parts.extend(_wrapped_label(cx, top + plot_h + 16, group))

    # Axis line.
    parts.append(
        f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' "
        f"y2='{top + plot_h}' stroke='{AXIS}' stroke-width='1.5'/>"
    )

    # Legend.
    lx = left + plot_w + 24
    ly = top + 6
    for s, label in enumerate(series_labels):
        parts.append(
            f"<rect x='{lx}' y='{ly - 11}' width='13' height='13' "
            f"fill='{PALETTE[s % len(PALETTE)]}'/>"
        )
        parts.append(_text(lx + 19, ly, label, size=12))
        ly += 24

    parts.append("</svg>")
    return "\n".join(parts)


def _wrapped_label(cx: float, y: float, label: str, max_chars: int = 16) -> list[str]:
    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return [
        _text(cx, y + i * 13, line, size=11, anchor="middle", color="#444")
        for i, line in enumerate(lines[:3])
    ]


@dataclass(frozen=True)
class ScatterPoint:
    x: float
    y: float
    label: str


def scatter_frontier(
    title: str,
    points: list[ScatterPoint],
    x_label: str,
    y_label: str,
    *,
    x_max: float = 1.0,
    y_max: float = 1.0,
    subtitle: str = "",
    better_corner: str = "lower-left",
) -> str:
    """Scatter frontier; draws a 'better' arrow toward the better corner.

    ``better_corner`` is "lower-left" (minimize both axes) or "upper-right" (maximize both).
    """
    width, height = 620, 520
    left, right, top, bottom = 70, 40, 70, 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    def px(x: float) -> float:
        return left + plot_w * (x / x_max if x_max else 0)

    def py(y: float) -> float:
        return top + plot_h * (1 - (y / y_max if y_max else 0))

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' "
        f"width='{width}' height='{height}' role='img'>",
        f"<rect width='{width}' height='{height}' fill='white'/>",
        _text(left, 28, title, size=18, weight="bold"),
    ]
    if subtitle:
        parts.append(_text(left, 48, subtitle, size=12, color="#666"))

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gx = left + plot_w * frac
        gy = top + plot_h * (1 - frac)
        parts.append(f"<line x1='{gx:.1f}' y1='{top}' x2='{gx:.1f}' "
                     f"y2='{top + plot_h}' stroke='{GRID}'/>")
        parts.append(f"<line x1='{left}' y1='{gy:.1f}' x2='{left + plot_w}' "
                     f"y2='{gy:.1f}' stroke='{GRID}'/>")
        parts.append(_text(left + plot_w * frac, top + plot_h + 18,
                           _pct(frac * x_max), size=11, anchor="middle", color="#666"))
        parts.append(_text(left - 8, top + plot_h * (1 - frac) + 4,
                           _pct(frac * y_max), size=11, anchor="end", color="#666"))

    # Axes.
    parts.append(f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' "
                 f"y2='{top + plot_h}' stroke='{AXIS}' stroke-width='1.5'/>")
    parts.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_h}' "
                 f"stroke='{AXIS}' stroke-width='1.5'/>")
    parts.append(_text(left + plot_w / 2, height - 30, x_label, size=13,
                       anchor="middle", color="#333"))
    parts.append(_text(18, top + plot_h / 2, y_label, size=13, anchor="middle",
                       color="#333", rotate=-90))

    # "Better" arrow toward the better corner.
    parts.append(
        "<defs><marker id='arrow' markerWidth='9' markerHeight='9' refX='6' refY='3' "
        "orient='auto'><path d='M0,0 L6,3 L0,6 Z' fill='#6a8f4f'/></marker></defs>"
    )
    if better_corner == "upper-right":
        ax = left + plot_w
        parts.append(
            f"<line x1='{ax - 70}' y1='{top + 70}' x2='{ax - 14}' y2='{top + 14}' "
            f"stroke='#6a8f4f' stroke-width='2' marker-end='url(#arrow)'/>"
        )
        parts.append(_text(ax - 78, top + 60, "better", size=11, anchor="end",
                           color="#6a8f4f"))
    else:
        parts.append(
            f"<line x1='{left + 70}' y1='{top + 70}' x2='{left + 14}' y2='{top + 14}' "
            f"stroke='#6a8f4f' stroke-width='2' marker-end='url(#arrow)'/>"
        )
        parts.append(_text(left + 78, top + 64, "better", size=11, color="#6a8f4f"))

    for i, point in enumerate(points):
        color = PALETTE[i % len(PALETTE)]
        cx, cy = px(point.x), py(point.y)
        parts.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='8' fill='{color}'/>")
        # Place the label inward when the point is near the right edge so it never clips.
        if point.x > 0.7 * x_max:
            parts.append(_text(cx - 12, cy + 4, point.label, size=13, weight="bold",
                               anchor="end", color=color))
        else:
            parts.append(_text(cx + 12, cy + 4, point.label, size=13, weight="bold",
                               color=color))

    parts.append("</svg>")
    return "\n".join(parts)


def line_chart(
    title: str,
    x_values: list[float],
    series: list[tuple[str, list[float]]],
    *,
    x_label: str = "",
    y_label: str = "",
    y_max: float = 1.0,
    subtitle: str = "",
) -> str:
    """Line chart for learning curves. ``series`` is [(label, y-values)]."""
    width, height = 760, 460
    left, right, top, bottom = 64, 180, 64, 76
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_max = max(x_values) if x_values else 1

    def px(x: float) -> float:
        return left + plot_w * (x / x_max if x_max else 0)

    def py(y: float) -> float:
        return top + plot_h * (1 - (y / y_max if y_max else 0))

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' "
        f"width='{width}' height='{height}' role='img'>",
        f"<rect width='{width}' height='{height}' fill='white'/>",
        _text(left, 28, title, size=18, weight="bold"),
    ]
    if subtitle:
        parts.append(_text(left, 48, subtitle, size=12, color="#666"))

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = top + plot_h * (1 - frac)
        parts.append(f"<line x1='{left}' y1='{y:.1f}' x2='{left + plot_w}' "
                     f"y2='{y:.1f}' stroke='{GRID}'/>")
        parts.append(_text(left - 8, y + 4, _pct(frac * y_max), size=11,
                           anchor="end", color="#666"))

    parts.append(f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' "
                 f"y2='{top + plot_h}' stroke='{AXIS}' stroke-width='1.5'/>")
    parts.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_h}' "
                 f"stroke='{AXIS}' stroke-width='1.5'/>")
    # X tick labels (integer counts); thin out if there are many points.
    step = max(1, len(x_values) // 12)
    for i, x in enumerate(x_values):
        if i % step == 0 or i == len(x_values) - 1:
            parts.append(_text(px(x), top + plot_h + 18, f"{int(x)}", size=11,
                               anchor="middle", color="#666"))
    if x_label:
        parts.append(_text(left + plot_w / 2, height - 24, x_label, size=12,
                           anchor="middle", color="#333"))
    if y_label:
        parts.append(_text(20, top + plot_h / 2, y_label, size=12, anchor="middle",
                           color="#333", rotate=-90))

    for s, (label, ys) in enumerate(series):
        color = PALETTE[s % len(PALETTE)]
        pts = " ".join(
            f"{px(x):.1f},{py(y):.1f}" for x, y in zip(x_values, ys, strict=False)
        )
        parts.append(f"<polyline points='{pts}' fill='none' stroke='{color}' "
                     f"stroke-width='2.5'/>")
        for x, y in zip(x_values, ys, strict=False):
            parts.append(f"<circle cx='{px(x):.1f}' cy='{py(y):.1f}' r='3' "
                         f"fill='{color}'/>")
        ly = top + 6 + s * 24
        parts.append(f"<rect x='{left + plot_w + 24}' y='{ly - 11}' width='13' "
                     f"height='13' fill='{color}'/>")
        parts.append(_text(left + plot_w + 43, ly, label, size=12))

    parts.append("</svg>")
    return "\n".join(parts)


def pareto_frontier(
    title: str,
    curve: list[tuple[float, float]],
    references: list[ScatterPoint],
    *,
    x_label: str = "",
    y_label: str = "",
    x_max: float = 1.0,
    y_max: float = 1.0,
    subtitle: str = "",
) -> str:
    """A swept Pareto curve (line + dots) with labeled reference points overlaid."""
    width, height = 640, 520
    left, right, top, bottom = 70, 40, 70, 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    def px(x: float) -> float:
        return left + plot_w * (x / x_max if x_max else 0)

    def py(y: float) -> float:
        return top + plot_h * (1 - (y / y_max if y_max else 0))

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' "
        f"width='{width}' height='{height}' role='img'>",
        f"<rect width='{width}' height='{height}' fill='white'/>",
        _text(left, 28, title, size=18, weight="bold"),
    ]
    if subtitle:
        parts.append(_text(left, 48, subtitle, size=12, color="#666"))

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gx = left + plot_w * frac
        gy = top + plot_h * (1 - frac)
        parts.append(f"<line x1='{gx:.1f}' y1='{top}' x2='{gx:.1f}' "
                     f"y2='{top + plot_h}' stroke='{GRID}'/>")
        parts.append(f"<line x1='{left}' y1='{gy:.1f}' x2='{left + plot_w}' "
                     f"y2='{gy:.1f}' stroke='{GRID}'/>")
        parts.append(_text(left + plot_w * frac, top + plot_h + 18, _pct(frac * x_max),
                           size=11, anchor="middle", color="#666"))
        parts.append(_text(left - 8, top + plot_h * (1 - frac) + 4, _pct(frac * y_max),
                           size=11, anchor="end", color="#666"))

    parts.append(f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' "
                 f"y2='{top + plot_h}' stroke='{AXIS}' stroke-width='1.5'/>")
    parts.append(f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_h}' "
                 f"stroke='{AXIS}' stroke-width='1.5'/>")
    if x_label:
        parts.append(_text(left + plot_w / 2, height - 30, x_label, size=13,
                           anchor="middle", color="#333"))
    if y_label:
        parts.append(_text(18, top + plot_h / 2, y_label, size=13, anchor="middle",
                           color="#333", rotate=-90))

    # Swept curve.
    ordered = sorted(curve)
    pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in ordered)
    parts.append(f"<polyline points='{pts}' fill='none' stroke='{PALETTE[2]}' "
                 f"stroke-width='2.5'/>")
    for x, y in ordered:
        parts.append(f"<circle cx='{px(x):.1f}' cy='{py(y):.1f}' r='3.5' "
                     f"fill='{PALETTE[2]}'/>")
    parts.append(_text(px(ordered[len(ordered) // 2][0]) + 8,
                       py(ordered[len(ordered) // 2][1]) - 8, "normos sweep", size=12,
                       weight="bold", color=PALETTE[2]))

    # Reference points (baselines).
    for i, point in enumerate(references):
        color = PALETTE[(i % 2)]  # alternate teal/terracotta, distinct from the green curve
        cx, cy = px(point.x), py(point.y)
        parts.append(f"<rect x='{cx - 5:.1f}' y='{cy - 5:.1f}' width='10' height='10' "
                     f"fill='{color}'/>")
        if point.x > 0.7 * x_max:
            parts.append(_text(cx - 10, cy + 4, point.label, size=12, weight="bold",
                               anchor="end", color=color))
        else:
            parts.append(_text(cx + 10, cy + 4, point.label, size=12, weight="bold",
                               color=color))

    parts.append("</svg>")
    return "\n".join(parts)


def confusion_matrix(
    title: str,
    row_labels: list[str],
    col_labels: list[str],
    counts: list[list[int]],
    *,
    subtitle: str = "",
) -> str:
    """Heat grid of expected label (rows) x routed disposition (cols)."""
    cell = 92
    label_w, label_h = 150, 70
    width = label_w + cell * len(col_labels) + 24
    height = label_h + cell * len(row_labels) + 90
    max_count = max((max(row) for row in counts if row), default=1) or 1

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' "
        f"width='{width}' height='{height}' role='img'>",
        f"<rect width='{width}' height='{height}' fill='white'/>",
        _text(20, 28, title, size=18, weight="bold"),
    ]
    if subtitle:
        parts.append(_text(20, 48, subtitle, size=12, color="#666"))

    x0, y0 = label_w, label_h
    for c, col in enumerate(col_labels):
        cx = x0 + c * cell + cell / 2
        parts.append(_text(cx, y0 - 10, col, size=12, anchor="middle", color="#333"))
    for r, row in enumerate(row_labels):
        ry = y0 + r * cell + cell / 2
        parts.append(_text(x0 - 12, ry + 4, row, size=12, anchor="end", color="#333"))

    for r in range(len(row_labels)):
        for c in range(len(col_labels)):
            count = counts[r][c]
            intensity = count / max_count
            fill = _heat(intensity)
            x = x0 + c * cell
            y = y0 + r * cell
            parts.append(
                f"<rect x='{x}' y='{y}' width='{cell}' height='{cell}' fill='{fill}' "
                f"stroke='white' stroke-width='2'/>"
            )
            text_color = "#fff" if intensity > 0.55 else "#222"
            parts.append(_text(x + cell / 2, y + cell / 2 + 5, str(count), size=18,
                               anchor="middle", color=text_color, weight="bold"))

    parts.append(_text(20, height - 30, "rows: expected label   columns: routed disposition",
                       size=11, color="#666"))
    parts.append("</svg>")
    return "\n".join(parts)


def _heat(intensity: float) -> str:
    # White -> teal ramp.
    intensity = max(0.0, min(1.0, intensity))
    r = int(255 - intensity * (255 - 47))
    g = int(255 - intensity * (255 - 111))
    b = int(255 - intensity * (255 - 143))
    return f"rgb({r},{g},{b})"
