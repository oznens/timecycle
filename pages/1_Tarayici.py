"""Çoklu sembol tarayıcı — pivot penceresinde olanları listele."""
from __future__ import annotations
import pandas as pd
import streamlit as st

from src.scanner import scan, DEFAULT_CRYPTO


st.set_page_config(page_title="Tarayıcı", layout="wide")
st.title("🔭 Çoklu Sembol Tarama")
st.caption("Her sembol için en güçlü dipler arasından otomatik döngü kurulur, "
           "bugünden en yakın pivot ve penceresi hesaplanır.")

with st.sidebar:
    st.header("Tarama")
    provider = st.selectbox(
        "Veri kaynağı", ["bybit", "binance", "yfinance", "kraken", "coinbase"], index=2,
        help="Cloud container'da yfinance/kraken/coinbase açık; Bybit/Binance lokal.",
    )
    interval = st.selectbox("Mum aralığı", ["1h", "4h", "1d", "1wk"], index=2)
    period = st.selectbox(
        "Periyot",
        {"1h": ["3mo", "6mo", "1y", "2y"],
         "4h": ["6mo", "1y", "2y", "5y"],
         "1d": ["1y", "2y", "5y", "10y"],
         "1wk": ["2y", "5y", "10y", "max"]}[interval],
        index=2,
    )
    tol_pct = st.slider("Tolerans (%)", 5, 20, 10) / 100.0
    min_hit = st.slider("Min hit-rate filtresi (%)", 0, 100, 60) / 100.0
    only_in_window = st.checkbox("Sadece şu an pencerede olanlar", False)
    max_workers = st.slider("Paralel iş sayısı", 1, 12, 6)

st.subheader("Sembol listesi")
default_text = "\n".join(DEFAULT_CRYPTO) if provider == "yfinance" \
    else "\n".join(s.replace("-USD", "/USDT") for s in DEFAULT_CRYPTO)
symbols_text = st.text_area(
    "Sembolleri satır satır gir",
    value=default_text, height=200,
    help="yfinance: 'BTC-USD' · ccxt: 'BTC/USDT'",
)
symbols = [s.strip() for s in symbols_text.splitlines() if s.strip()]
st.caption(f"📋 {len(symbols)} sembol")

if st.button("🚀 Taramayı başlat", type="primary"):
    progress = st.progress(0, text="Tarama başlıyor…")
    status = st.empty()
    results = []

    def cb(i, n, r):
        progress.progress(i / n, text=f"{i}/{n} · {r.symbol}")
        status.write(
            f"✓ **{r.symbol}** — "
            + (f"hit {r.hit_rate*100:.0f}% · alt {r.sub_days:.0f}g · "
               f"{'🎯 PENCEREDE' if r.in_window else f'{r.days_to_pivot:+d}g'}"
               if r.ok else f"❌ {r.error}")
        )

    results = scan(
        symbols, max_workers=max_workers, progress_cb=cb,
        provider=provider, period=period, interval=interval, tol_pct=tol_pct,
    )
    progress.empty()
    status.empty()

    # tabloya çevir
    rows = []
    for r in results:
        if not r.ok:
            continue
        if r.hit_rate < min_hit:
            continue
        if only_in_window and not r.in_window:
            continue
        rows.append({
            "Sembol": r.symbol,
            "Bar": r.bars,
            "Alt döngü (g)": round(r.sub_days, 1),
            "Bölme": r.sub,
            "Parent (g)": round(r.parent_days, 1),
            "Hit-rate": f"{r.hit_rate*100:.0f}%",
            "Sıradaki pivot": r.next_pivot.strftime("%Y-%m-%d") if r.next_pivot else "-",
            "Bugüne (g)": r.days_to_pivot,
            "Pencere başlangıç": r.window_start.strftime("%Y-%m-%d") if r.window_start else "-",
            "Pencere bitiş": r.window_end.strftime("%Y-%m-%d") if r.window_end else "-",
            "Pencerede": "🎯" if r.in_window else "",
            "Son fiyat": round(r.last_price, 4),
            "30g tepe%": f"{r.pct_from_30d_high:+.1f}%",
        })

    if not rows:
        st.warning("Filtrelere uyan sonuç yok.")
    else:
        df = pd.DataFrame(rows).sort_values(
            by=["Pencerede", "Bugüne (g)"],
            key=lambda c: c.map(abs) if c.name == "Bugüne (g)" else c,
            ascending=[False, True],
        )
        st.subheader(f"📊 Sonuçlar ({len(df)})")
        st.dataframe(df, hide_index=True, use_container_width=True)

        # Hata özet
        errors = [r for r in results if not r.ok]
        if errors:
            with st.expander(f"⚠️ {len(errors)} başarısız sembol"):
                for r in errors:
                    st.write(f"- **{r.symbol}**: {r.error}")
