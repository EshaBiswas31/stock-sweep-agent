"""
agent.py
--------
The "trading agent". It takes the list of crossing points found by the
sweep-line algorithm and turns each relevant one into a BUY or SELL
decision, using simple, well-known trading rules:

  - Price crosses ABOVE its SMA50   -> BUY  (momentum turning up)
  - Price crosses BELOW its SMA50   -> SELL (momentum turning down)
  - SMA50 crosses ABOVE SMA200      -> BUY  ("Golden Cross", strong signal)
  - SMA50 crosses BELOW SMA200      -> SELL ("Death Cross", strong signal)

Any other crossing the algorithm finds (there can be more than these,
since the algorithm is general-purpose) is simply ignored by the agent.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.sweep_line import Point, Segment


@dataclass
class Signal:
    day_index: float
    price_at_signal: float
    action: str   # "BUY" or "SELL"
    reason: str


def _segments_by_label(segments: List[Segment]):
    by_label = {}
    for s in segments:
        x0, x1 = min(s.p1.x, s.p2.x), max(s.p1.x, s.p2.x)
        y0 = s.p1.y if s.p1.x < s.p2.x else s.p2.y
        y1 = s.p2.y if s.p1.x < s.p2.x else s.p1.y
        by_label.setdefault(s.label, []).append((x0, x1, y0, y1))
    for k in by_label:
        by_label[k].sort()
    return by_label


def _y_at(segs, x):
    for (x0, x1, y0, y1) in segs:
        if x0 - 1e-6 <= x <= x1 + 1e-6:
            if abs(x1 - x0) < 1e-9:
                return y0
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return None


def _which_was_above(by_label, label_a, label_b, x):
    """Was line A above line B just before x? Used to tell an upward
    crossing from a downward one."""
    just_before = x - 0.5
    ya = _y_at(by_label.get(label_a, []), just_before)
    yb = _y_at(by_label.get(label_b, []), just_before)
    if ya is None or yb is None:
        return "unknown"
    return "a_above" if ya > yb else "b_above"


def generate_signals(intersections: List[Tuple[Point, List[Segment]]],
                      all_segments: List[Segment]) -> List[Signal]:
    by_label = _segments_by_label(all_segments)
    signals: List[Signal] = []

    for point, segs in intersections:
        labels = set(s.label for s in segs)
        x, y = point.x, point.y

        if {"SMA50", "SMA200"}.issubset(labels):
            prev = _which_was_above(by_label, "SMA50", "SMA200", x)
            if prev == "b_above":   # SMA50 was below SMA200, now crossing above it
                signals.append(Signal(x, y, "BUY", "Golden Cross: SMA50 crossed above SMA200"))
            elif prev == "a_above":
                signals.append(Signal(x, y, "SELL", "Death Cross: SMA50 crossed below SMA200"))

        elif {"Close", "SMA50"}.issubset(labels):
            prev = _which_was_above(by_label, "Close", "SMA50", x)
            if prev == "b_above":
                signals.append(Signal(x, y, "BUY", "Price crossed above its 50-day average"))
            elif prev == "a_above":
                signals.append(Signal(x, y, "SELL", "Price crossed below its 50-day average"))

    signals.sort(key=lambda s: s.day_index)

    # Keep only signals that actually change the decision (BUY, SELL, BUY, SELL, ...).
    # Two crossings can land on the same day when the price briefly wiggles across
    # its average -- the second one wouldn't change what the agent does, so drop it.
    deduped: List[Signal] = []
    for s in signals:
        if deduped and deduped[-1].action == s.action:
            continue
        deduped.append(s)

    return deduped
