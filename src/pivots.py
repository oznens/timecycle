"""
Pivot (dip / tepe) tespiti.

Yöntem 1: fractal/swing-low — bir bar, kendisinden önceki/sonraki `left`/`right`
bar'ların hepsinden daha düşükse swing-low'dur. Hızlı, deterministik.

Yöntem 2: scipy.signal.find_peaks — `distance` ve `prominence` ile gürültüyü filtreler.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def fractal_lows(low: pd.Series, left: int = 5, right: int = 5) -> pd.DatetimeIndex:
    """Williams fractal: bar her iki yandaki `left`/`right` bar'ın altında ise dip."""
    arr = low.values
    n = len(arr)
    out = []
    for i in range(left, n - right):
        window = arr[i - left : i + right + 1]
        if arr[i] == window.min() and (window == arr[i]).sum() == 1:
            out.append(low.index[i])
    return pd.DatetimeIndex(out)


def fractal_highs(high: pd.Series, left: int = 5, right: int = 5) -> pd.DatetimeIndex:
    arr = high.values
    n = len(arr)
    out = []
    for i in range(left, n - right):
        window = arr[i - left : i + right + 1]
        if arr[i] == window.max() and (window == arr[i]).sum() == 1:
            out.append(high.index[i])
    return pd.DatetimeIndex(out)


def significant_lows(
    low: pd.Series,
    min_separation_days: int = 20,
    prominence_pct: float = 0.05,
) -> pd.DatetimeIndex:
    """
    `find_peaks` ile dipler: en az `min_separation_days` aralık, fiyat skalasında
    en az `prominence_pct` kadar belirgin (ör. 0.05 = %5).
    """
    inv = -low.values
    prom = float(low.max() - low.min()) * prominence_pct
    idx, _ = find_peaks(inv, distance=min_separation_days, prominence=prom)
    return low.index[idx]


def top_n_lows(
    low: pd.Series,
    n: int = 6,
    min_separation_days: int = 30,
) -> pd.DatetimeIndex:
    """
    En belirgin n adet dibi döndürür (prominence ile sıralı).
    Manuel "iki büyük dibi seç" iş akışına yardımcı olur.
    """
    inv = -low.values
    rng = float(low.max() - low.min())
    idx, props = find_peaks(inv, distance=min_separation_days, prominence=rng * 0.01)
    if len(idx) == 0:
        return pd.DatetimeIndex([])
    order = np.argsort(-props["prominences"])[:n]
    picked = sorted(idx[order])
    return low.index[picked]
