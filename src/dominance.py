"""
Dominant ritim skorlama.

Her projeksiyon pivotu için, ±%10 (varsayılan) tolerans penceresinde gerçek bir
significant low var mı? Hit-rate hesaplanır.

Kitabın kuralı: 80%+ hit-rate = geçerli/dominant döngü.
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from datetime import timedelta

from .cycle import Cycle


@dataclass
class DominanceReport:
    cycle: Cycle
    total_pivots: int
    hits: int
    hit_dates: list[pd.Timestamp]
    miss_dates: list[pd.Timestamp]
    matched_actuals: list[pd.Timestamp]

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total_pivots if self.total_pivots else 0.0


def score(
    cycle: Cycle,
    actual_lows: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> DominanceReport:
    projected = cycle.project(start, end)
    hits, misses, matched = [], [], []
    used: set[pd.Timestamp] = set()
    tol = timedelta(days=cycle.tolerance_days)
    for p in projected:
        # tolerans penceresine düşen ve daha önce eşleştirilmemiş en yakın gerçek dipi bul
        candidates = [
            a for a in actual_lows
            if (a >= p - tol) and (a <= p + tol) and (a not in used)
        ]
        if candidates:
            closest = min(candidates, key=lambda a: abs((a - p).total_seconds()))
            hits.append(p)
            matched.append(closest)
            used.add(closest)
        else:
            misses.append(p)
    return DominanceReport(
        cycle=cycle,
        total_pivots=len(projected),
        hits=len(hits),
        hit_dates=hits,
        miss_dates=misses,
        matched_actuals=matched,
    )


def best_subdivision(
    seed_a: pd.Timestamp,
    seed_b: pd.Timestamp,
    actual_lows: pd.DatetimeIndex,
    start: pd.Timestamp,
    end: pd.Timestamp,
    candidates: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    tolerance_pct: float = 0.10,
) -> tuple[DominanceReport, list[DominanceReport]]:
    """
    Aday bölme oranlarını dener, en yüksek hit-rate'i seçer.
    Eşitlikte daha az parametreli (küçük subdivision) tercih edilir.
    """
    reports = []
    for n in candidates:
        c = Cycle(seed_a, seed_b, subdivision=n, tolerance_pct=tolerance_pct)
        reports.append(score(c, actual_lows, start, end))
    reports.sort(key=lambda r: (-r.hit_rate, r.cycle.subdivision))
    return reports[0], reports
