"""
sweep_line.py
-------------
The core algorithm for this project: Line Segment Intersection using the
plane-sweep (Bentley-Ottmann style) method taught in class.

THE IDEA (explain this part to your professor):
  - Every line on a stock chart (the price line, SMA50, SMA200) is really
    just a chain of small straight line segments -- one segment connecting
    each day's value to the next day's value.
  - A "crossover" between two lines (e.g. price crossing above its average)
    is exactly the same thing as two line segments intersecting each other.
  - So instead of writing a special "check if price crossed its average"
    loop, we solve the general problem: given a bunch of line segments,
    find every point where any two of them intersect.

HOW THE ALGORITHM WORKS (simple version):
  - Imagine a horizontal line sweeping from the top of the chart (highest
    price) down to the bottom (lowest price).
  - We only need to pause the sweep at "interesting" moments: when a
    segment starts, when a segment ends, or when two segments swap
    left-right order (which can only happen if they just crossed).
  - These pause points are called "event points" and are processed in
    order using a priority queue (we use Python's heapq module for this --
    a heap is a simple way to always get the next event quickly).
  - We keep track of which segments the sweep line currently touches, and
    their left-to-right order, in a simple sorted list (the "status
    structure").
  - Whenever two neighbouring segments in that order swap places, that
    swap IS a crossing point -- we record it.

WHY THIS IS BETTER THAN THE OBVIOUS WAY:
  The obvious way is to compare every segment against every other segment
  -- with n segments that's about n*n comparisons. This algorithm only
  compares segments that are near each other at any given moment, so it
  runs in about (n + k) * log(n) time, where k is the number of crossings
  actually found. This is called "output-sensitive" -- it only works
  harder when there's actually more to find.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import heapq
import itertools

EPS = 1e-9


@dataclass
class Point:
    x: float
    y: float

    def event_key(self):
        # Sweep order: higher y (price) first; on a tie, smaller x first.
        return (-self.y, self.x)


@dataclass
class Segment:
    """One small straight piece of a line (e.g. one day's price move)."""
    p1: Point
    p2: Point
    label: str = ""  # which line this belongs to, e.g. "Close" or "SMA50"

    def __post_init__(self):
        # Always store p1 as the upper endpoint (bigger y / price first).
        if (self.p1.y, -self.p1.x) < (self.p2.y, -self.p2.x):
            self.p1, self.p2 = self.p2, self.p1

    def x_at_y(self, y: float) -> float:
        """Where is this segment, left-to-right, at height y?"""
        if abs(self.p1.y - self.p2.y) < EPS:
            return min(self.p1.x, self.p2.x)
        t = (self.p1.y - y) / (self.p1.y - self.p2.y)
        return self.p1.x + t * (self.p2.x - self.p1.x)

    def contains_point(self, p: Point) -> bool:
        if not (min(self.p1.x, self.p2.x) - EPS <= p.x <= max(self.p1.x, self.p2.x) + EPS):
            return False
        if not (min(self.p1.y, self.p2.y) - EPS <= p.y <= max(self.p1.y, self.p2.y) + EPS):
            return False
        cross = (self.p2.x - self.p1.x) * (p.y - self.p1.y) - (self.p2.y - self.p1.y) * (p.x - self.p1.x)
        return abs(cross) < 1e-6


def segment_intersection(s1: Segment, s2: Segment) -> Optional[Point]:
    """Classic line-segment intersection formula (from coordinate geometry):
    treat each segment as a parametric line and solve for where they meet."""
    x1, y1, x2, y2 = s1.p1.x, s1.p1.y, s1.p2.x, s1.p2.y
    x3, y3, x4, y4 = s2.p1.x, s2.p1.y, s2.p2.x, s2.p2.y

    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < EPS:
        return None  # parallel lines, no single crossing point

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / d

    if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
        return Point(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


class _EventQueue:
    """A simple priority queue (min-heap) of event points, ordered by the
    sweep direction. Using Python's built-in heapq keeps this easy to
    explain: 'always process the next point in sweep order first'."""

    def __init__(self):
        self._heap = []
        self._counter = itertools.count()   # tie-breaker so heap never compares Points directly
        self._seen = set()

    def _rk(self, p: Point):
        return (round(p.x, 6), round(p.y, 6))

    def push(self, p: Point):
        key = self._rk(p)
        if key in self._seen:
            return
        self._seen.add(key)
        heapq.heappush(self._heap, (p.event_key(), next(self._counter), p))

    def pop(self) -> Point:
        _, _, p = heapq.heappop(self._heap)
        self._seen.discard(self._rk(p))
        return p

    def empty(self) -> bool:
        return len(self._heap) == 0


def find_intersections(segments: List[Segment]) -> List[Tuple[Point, List[Segment]]]:
    """
    Runs the sweep and returns every intersection point found, along with
    which segments crossed there. This is the FindIntersections algorithm
    from the slides, written with simple Python data structures instead of
    a full balanced-BST implementation, which keeps the code readable
    while keeping the same core idea and the same output-sensitive
    behaviour in practice.
    """
    segments = [s for s in segments if not (abs(s.p1.x - s.p2.x) < EPS and abs(s.p1.y - s.p2.y) < EPS)]

    Q = _EventQueue()
    upper_at = {}
    for s in segments:
        Q.push(s.p1)
        Q.push(s.p2)
        key = (round(s.p1.x, 6), round(s.p1.y, 6))
        upper_at.setdefault(key, []).append(s)

    status: List[Segment] = []
    results: List[Tuple[Point, List[Segment]]] = []

    def find_new_event(sl, sr, p):
        if sl is None or sr is None:
            return
        ip = segment_intersection(sl, sr)
        if ip is None:
            return
        if ip.y < p.y + EPS or (abs(ip.y - p.y) < EPS and ip.x > p.x + EPS):
            Q.push(ip)

    while not Q.empty():
        p = Q.pop()
        key = (round(p.x, 6), round(p.y, 6))
        U = upper_at.get(key, [])

        L, C = [], []
        for s in status:
            if s in U:
                continue
            if s.contains_point(p):
                lower = s.p2 if (s.p1.y, -s.p1.x) >= (s.p2.y, -s.p2.x) else s.p1
                if abs(lower.x - p.x) < EPS and abs(lower.y - p.y) < EPS:
                    L.append(s)
                else:
                    C.append(s)

        found_here = L + U + C
        if len(found_here) > 1:
            results.append((p, found_here))

        remove_ids = set(id(s) for s in (L + C))
        status = [s for s in status if id(s) not in remove_ids]

        sweep_y = p.y - 1e-7
        status.extend(U + C)
        status.sort(key=lambda s: s.x_at_y(sweep_y))

        if len(U) + len(C) == 0:
            left, right = None, None
            for s in status:
                sx = s.x_at_y(sweep_y)
                if sx < p.x - EPS:
                    left = s
                elif sx > p.x + EPS and right is None:
                    right = s
            find_new_event(left, right, p)
        else:
            uc_ids = set(id(s) for s in (U + C))
            idxs = [i for i, s in enumerate(status) if id(s) in uc_ids]
            if idxs:
                i_left, i_right = idxs[0], idxs[-1]
                sl = status[i_left - 1] if i_left - 1 >= 0 else None
                sr = status[i_right + 1] if i_right + 1 < len(status) else None
                find_new_event(sl, status[i_left], p)
                find_new_event(status[i_right], sr, p)

    return results
