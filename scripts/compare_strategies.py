"""
backtest_results/ klasöründeki en son sonuçları tarayıp karşılaştırma tablosu üret.
Usage: python scripts/compare_strategies.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import zipfile


def find_latest_results(base: Path = Path("user_data/backtest_results")) -> list[Path]:
    if not base.exists():
        return []
    # .zip ve _bt-results.json dosyalarını birleştir
    files = sorted(base.glob(".last_result.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return []
    last = json.loads(files[0].read_text())
    return [base / last["latest_backtest"]]


def load_result(path: Path) -> dict:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith(".json"):
                    return json.loads(z.read(name))
        return {}
    return json.loads(path.read_text())


def main():
    results = find_latest_results()
    if not results:
        print("Sonuç bulunamadı.")
        sys.exit(1)
    data = load_result(results[0])
    strats = data.get("strategy", {})
    if not strats:
        print(f"'strategy' bulunamadı: {results[0]}")
        sys.exit(1)

    rows = []
    for name, s in strats.items():
        rows.append({
            "Strateji": name,
            "Trades": s.get("total_trades", 0),
            "Win%": round(s.get("wins", 0) / max(s.get("total_trades", 1), 1) * 100, 1),
            "AvgP%": round(s.get("profit_mean", 0) * 100, 3),
            "TotP%": round(s.get("profit_total", 0) * 100, 2),
            "DD%": round(s.get("max_drawdown_account", 0) * 100, 2),
            "Sharpe": round(s.get("sharpe", 0), 2) if s.get("sharpe") else "-",
            "Sortino": round(s.get("sortino", 0), 2) if s.get("sortino") else "-",
            "AvgDur": s.get("holding_avg", "-"),
        })

    # Tablo yazdır
    headers = list(rows[0].keys())
    widths = [max(len(h), max(len(str(r[h])) for r in rows)) for h in headers]
    print(" | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    # Sort by total profit
    for r in sorted(rows, key=lambda x: -x["TotP%"]):
        print(" | ".join(f"{str(r[h]):<{w}}" for h, w in zip(headers, widths)))


if __name__ == "__main__":
    main()
