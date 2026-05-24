"""
Zaman döngüsü modeli.

Hurst yöntemi:
- iki 'seed' dipten döngü uzunluğu hesaplanır (period = ts2 - ts1)
- Bu büyük döngü, n=2 veya n=3 ile alt döngülere bölünür
- Pivotlar geriye/ileriye projekte edilir
- Tolerans penceresi = döngü uzunluğunun %X'i (varsayılan %10)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import timedelta
import pandas as pd


@dataclass
class Cycle:
    seed_a: pd.Timestamp
    seed_b: pd.Timestamp
    subdivision: int = 1  # 1 = ana döngü, 2 = ikiye böl, 3 = üçe böl
    tolerance_pct: float = 0.10  # %10 varsayılan pencere

    @property
    def parent_days(self) -> float:
        return (self.seed_b - self.seed_a).total_seconds() / 86400.0

    @property
    def sub_days(self) -> float:
        return self.parent_days / self.subdivision

    @property
    def tolerance_days(self) -> float:
        return self.sub_days * self.tolerance_pct

    def project(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> list[pd.Timestamp]:
        """Alt döngü uzunluğunda eşit aralıklı pivot listesi (seed_a esas alınır)."""
        step = timedelta(days=self.sub_days)
        pivots = []
        # geri doğru
        t = self.seed_a
        while t >= start:
            pivots.append(t)
            t -= step
        # ileri doğru
        t = self.seed_a + step
        while t <= end:
            pivots.append(t)
            t += step
        return sorted(pivots)

    def window(self, pivot: pd.Timestamp, pct: float | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
        p = self.tolerance_pct if pct is None else pct
        delta = timedelta(days=self.sub_days * p)
        return pivot - delta, pivot + delta
