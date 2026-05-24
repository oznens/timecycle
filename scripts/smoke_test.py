"""Sistemin uçtan uca çalıştığını hızlıca doğrular."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd
from src.data import fetch_ohlc
from src.pivots import significant_lows, top_n_lows
from src.dominance import best_subdivision
from src.chart import build_chart


def main():
    print("1) BTC-USD 10y çekiliyor (yfinance)…")
    df = fetch_ohlc("BTC-USD", period="10y", interval="1d", provider="yfinance")
    print(f"   ✓ {len(df)} bar, {df.index[0].date()} → {df.index[-1].date()}")

    print("2) Anlamlı dipler tespit ediliyor…")
    sig = significant_lows(df["low"], min_separation_days=25, prominence_pct=0.05)
    strongest = top_n_lows(df["low"], n=10, min_separation_days=60)
    print(f"   ✓ {len(sig)} anlamlı dip, en güçlü 10:")
    for d in strongest:
        print(f"     - {d.date()}  low=${df.loc[d, 'low']:.0f}")

    print("3) İlk 2 güçlü dipten döngü kuruluyor + bölme oranı taranıyor…")
    seed_a, seed_b = strongest[0], strongest[1]
    best, all_r = best_subdivision(
        seed_a, seed_b, actual_lows=sig,
        start=df.index[0], end=df.index[-1],
        candidates=(1, 2, 3, 4, 5, 6),
        tolerance_pct=0.10,
    )
    print(f"   ✓ Seed A: {seed_a.date()}  Seed B: {seed_b.date()}")
    print(f"   ✓ Parent döngü: {best.cycle.parent_days:.0f} gün")
    print(f"   Bölme | Alt(gün) | Proj | Hit | Hit-rate")
    for r in all_r:
        print(f"   {r.cycle.subdivision:>5} | {r.cycle.sub_days:>8.1f} | {r.total_pivots:>4} | "
              f"{r.hits:>3} | {r.hit_rate*100:>5.1f}%")
    print(f"   🏆 Dominant: bölme={best.cycle.subdivision}  "
          f"alt={best.cycle.sub_days:.0f}g  hit={best.hit_rate*100:.1f}%")

    print("4) Plotly grafik üretiliyor…")
    fig = build_chart(
        df, actual_lows=sig,
        layers=[(best, "#f5b400")],
        title="BTC-USD — Smoke test",
        log_y=True,
    )
    out = pathlib.Path(__file__).parent.parent / "smoke_test.html"
    fig.write_html(str(out), include_plotlyjs="cdn")
    print(f"   ✓ {out}")

    print("\nTÜM ADIMLAR OK.")


if __name__ == "__main__":
    main()
