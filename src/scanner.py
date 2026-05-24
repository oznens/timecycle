"""
Çoklu sembol tarama.

Her sembol için:
  1) OHLC çek
  2) Anlamlı dipleri tespit et
  3) En güçlü N dip arasından, yeterli zaman aralığı olan tüm çiftleri dene
  4) Her çift için subdivision (1,2,3,4) skorla → en iyi hit-rate'i seç
  5) Bugünden ileri ilk projeksiyon pivotunu hesapla
  6) Bugün tolerans penceresinde mi? → işaretle

Sonuç: pivot penceresine yakın sembolleri sıralı tablo.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
import pandas as pd

from .data import fetch_ohlc
from .pivots import significant_lows, top_n_lows
from .dominance import best_subdivision, DominanceReport


@dataclass
class ScanResult:
    symbol: str
    ok: bool = False
    error: str | None = None
    bars: int = 0
    sub: int = 0
    sub_days: float = 0.0
    parent_days: float = 0.0
    hit_rate: float = 0.0
    next_pivot: pd.Timestamp | None = None
    window_start: pd.Timestamp | None = None
    window_end: pd.Timestamp | None = None
    days_to_pivot: int | None = None  # negatif = geçti, 0 = bugün
    in_window: bool = False
    last_price: float = 0.0
    pct_from_30d_high: float = 0.0
    seed_a: pd.Timestamp | None = None
    seed_b: pd.Timestamp | None = None


def _auto_seeds(
    strongest: pd.DatetimeIndex,
    span_days: int,
    min_gap_pct: float = 0.20,
    max_gap_pct: float = 0.95,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Top dipler arasından, zaman aralığı toplam span'in [min_gap, max_gap]
    yüzdesi içinde olan tüm (a, b) çiftleri."""
    min_gap = span_days * min_gap_pct
    max_gap = span_days * max_gap_pct
    pairs = []
    s = sorted(strongest)
    for i, a in enumerate(s):
        for b in s[i + 1:]:
            gap = (b - a).days
            if min_gap <= gap <= max_gap:
                pairs.append((a, b))
    return pairs


def analyze_symbol(
    symbol: str,
    period: str = "5y",
    interval: str = "1d",
    provider: str = "yfinance",
    tol_pct: float = 0.10,
    min_sep: int = 25,
    prom_pct: float = 0.05,
    top_n: int = 6,
    sub_candidates: tuple[int, ...] = (1, 2, 3, 4),
) -> ScanResult:
    res = ScanResult(symbol=symbol)
    try:
        df = fetch_ohlc(symbol, period=period, interval=interval, provider=provider)
        res.bars = len(df)
        if res.bars < 200:
            res.error = f"yetersiz bar ({res.bars})"
            return res

        sig = significant_lows(df["low"], min_separation_days=min_sep, prominence_pct=prom_pct)
        strongest = top_n_lows(df["low"], n=top_n, min_separation_days=max(min_sep, 30))
        if len(strongest) < 2:
            res.error = "yeterli güçlü dip yok"
            return res

        span_days = (df.index[-1] - df.index[0]).days
        pairs = _auto_seeds(strongest, span_days)
        if not pairs:
            res.error = "uygun seed çifti yok"
            return res

        best_overall: DominanceReport | None = None
        for a, b in pairs:
            best, _ = best_subdivision(
                a, b, actual_lows=sig,
                start=df.index[0], end=df.index[-1],
                candidates=sub_candidates, tolerance_pct=tol_pct,
            )
            if (best_overall is None) or (best.hit_rate > best_overall.hit_rate) \
                    or (best.hit_rate == best_overall.hit_rate
                        and best.total_pivots > best_overall.total_pivots):
                best_overall = best

        assert best_overall is not None
        cyc = best_overall.cycle
        res.sub = cyc.subdivision
        res.sub_days = cyc.sub_days
        res.parent_days = cyc.parent_days
        res.hit_rate = best_overall.hit_rate
        res.seed_a, res.seed_b = cyc.seed_a, cyc.seed_b

        # Bugünden ileri ilk projeksiyon
        now = pd.Timestamp.utcnow().tz_localize(None).normalize()
        horizon = now + timedelta(days=int(cyc.sub_days * 2))
        # geriye dönük da bak ki bugün zaten bir pencerede miyiz?
        backstop = now - timedelta(days=int(cyc.tolerance_days * 1.2))
        projected = cyc.project(backstop, horizon)
        if not projected:
            res.error = "projeksiyon yok"
            return res
        # bugüne en yakın pivot
        nearest = min(projected, key=lambda p: abs((p - now).days))
        res.next_pivot = nearest
        res.window_start, res.window_end = cyc.window(nearest, tol_pct)
        res.days_to_pivot = (nearest - now).days
        res.in_window = (res.window_start <= now <= res.window_end)

        res.last_price = float(df["close"].iloc[-1])
        last30 = df["high"].iloc[-30:].max() if len(df) >= 30 else df["high"].max()
        res.pct_from_30d_high = (res.last_price / float(last30) - 1.0) * 100.0

        res.ok = True
        return res
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
        return res


def scan(
    symbols: list[str],
    max_workers: int = 8,
    progress_cb=None,
    **kwargs,
) -> list[ScanResult]:
    """Tüm sembolleri tarar; results geliş sırasıyla biriktirir."""
    results: list[ScanResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(analyze_symbol, s, **kwargs): s for s in symbols}
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            if progress_cb:
                progress_cb(i, len(symbols), r)
    return results


# Hazır kripto sembol listesi (Yahoo Finance)
DEFAULT_CRYPTO = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD",
    "AVAX-USD", "DOT-USD", "LINK-USD", "MATIC-USD", "ATOM-USD", "LTC-USD", "BCH-USD",
    "UNI-USD", "NEAR-USD", "APT-USD", "FIL-USD", "OP-USD", "ARB-USD", "INJ-USD",
    "SUI-USD", "TIA-USD", "HBAR-USD", "ICP-USD", "ALGO-USD", "AAVE-USD", "MKR-USD",
    "XLM-USD", "ETC-USD", "TRX-USD", "VET-USD", "XMR-USD", "GRT-USD", "SAND-USD",
    "AXS-USD", "MANA-USD", "CHZ-USD", "FTM-USD", "RUNE-USD", "THETA-USD", "FLOW-USD",
    "EGLD-USD", "STX-USD", "QNT-USD", "IMX-USD", "SHIB-USD", "PEPE-USD",
]
