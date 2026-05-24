"""
Streamlit Dashboard — Zaman Döngü Otomasyonu (Mr. Abundance / J.M. Hurst yöntemi).

Çalıştırma:
    streamlit run app.py
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from src.data import fetch_ohlc
from src.pivots import significant_lows, top_n_lows
from src.cycle import Cycle
from src.dominance import score, best_subdivision
from src.chart import build_chart


st.set_page_config(page_title="Time Cycle Analizi", layout="wide")
st.title("⏱️ Zaman Döngü Analizi — Hurst / Mr. Abundance")

with st.sidebar:
    st.header("Veri")
    provider = st.selectbox(
        "Veri kaynağı",
        ["yfinance", "bybit", "binance", "kraken", "coinbase"],
        index=0,
        help="Bu cloud ortamında sadece yfinance/kraken/coinbase çalışır; "
             "Bybit/Binance lokalde kullanılır.",
    )
    default_symbol = "BTC/USDT" if provider in {"bybit", "binance"} else "BTC-USD"
    symbol = st.text_input("Sembol", value=default_symbol)
    period = st.selectbox("Periyot", ["2y", "5y", "10y", "max"], index=2)
    interval = st.selectbox("Mum aralığı", ["1d", "1wk", "1mo"], index=0)

    st.header("Pivot tespiti")
    min_sep = st.slider("Min dip aralığı (bar)", 5, 90, 25,
                        help="Daha büyük = daha az gürültü")
    prom_pct = st.slider("Belirginlik (%)", 1, 20, 5) / 100.0

    st.header("Döngü")
    auto_seed = st.checkbox("Otomatik en güçlü 2 dipten döngü kur", True)
    tol_pct = st.slider("Tolerans penceresi (%)", 5, 20, 10) / 100.0
    sub_candidates = st.multiselect(
        "Aday bölme oranları",
        options=[1, 2, 3, 4, 5, 6],
        default=[1, 2, 3, 4],
        help="En yüksek hit-rate'i veren seçilir.",
    )

    log_y = st.checkbox("Log fiyat ekseni", True)

# Veri çek
try:
    with st.spinner(f"{provider} → {symbol} çekiliyor…"):
        df = fetch_ohlc(symbol, period=period, interval=interval, provider=provider)
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

st.caption(f"📊 **{symbol}** · {df.index[0].date()} → {df.index[-1].date()} · {len(df)} bar")

# Pivot tespiti
sig = significant_lows(df["low"], min_separation_days=min_sep, prominence_pct=prom_pct)
strongest = top_n_lows(df["low"], n=10, min_separation_days=max(min_sep, 30))

if len(strongest) < 2:
    st.error("Yeterli güçlü dip bulunamadı — pivot ayarlarını gevşetin.")
    st.stop()

st.write(
    f"🔻 **{len(sig)}** anlamlı dip bulundu (en güçlü 10: "
    + ", ".join(d.strftime("%Y-%m-%d") for d in strongest[:10]) + ")"
)

# Seed seçimi
col1, col2 = st.columns(2)
options = [d.strftime("%Y-%m-%d") for d in strongest]
default_a = options[0]
default_b = options[1] if len(options) > 1 else options[0]
seed_a_str = col1.selectbox("Dip A (sol)", options, index=0)
seed_b_str = col2.selectbox("Dip B (sağ)", options, index=1 if len(options) > 1 else 0)
seed_a = pd.Timestamp(seed_a_str)
seed_b = pd.Timestamp(seed_b_str)
if seed_b <= seed_a:
    st.warning("B dipinin A'dan sonra olması gerekir — sıralamayı değiştirin.")
    st.stop()

# Skorlama
if not sub_candidates:
    sub_candidates = [1, 2, 3]
best, all_reports = best_subdivision(
    seed_a, seed_b,
    actual_lows=sig,
    start=df.index[0], end=df.index[-1],
    candidates=tuple(sub_candidates),
    tolerance_pct=tol_pct,
)

# Skor tablosu
st.subheader("📈 Bölme oranı skorları (dominant ritim seçimi)")
table = pd.DataFrame([
    {
        "Bölme": r.cycle.subdivision,
        "Alt döngü (gün)": round(r.cycle.sub_days, 1),
        "Tolerans (±gün)": round(r.cycle.tolerance_days, 1),
        "Projeksiyon": r.total_pivots,
        "Vuran": r.hits,
        "Hit-rate": f"{r.hit_rate*100:.1f}%",
    }
    for r in all_reports
])
st.dataframe(table, hide_index=True, use_container_width=True)

st.success(
    f"🏆 Dominant: **bölme = {best.cycle.subdivision}** → "
    f"alt döngü ≈ **{best.cycle.sub_days:.0f} gün** · "
    f"hit-rate **{best.hit_rate*100:.1f}%**"
    + (" ✅ (≥80% kitap eşiği)" if best.hit_rate >= 0.80 else " ⚠️ (<80%, dipleri değiştirip dene)")
)

# Grafik
layers = [(best, "#f5b400")]
# Üst-üste karşılaştırma için 2. en iyi de göster
if len(all_reports) > 1 and all_reports[1].hit_rate > 0:
    layers.append((all_reports[1], "#8c4a8c"))

fig = build_chart(
    df, actual_lows=sig, layers=layers,
    title=f"{symbol} — Dominant: bölme {best.cycle.subdivision} (≈{best.cycle.sub_days:.0f}g)",
    log_y=log_y,
)
st.plotly_chart(fig, use_container_width=True)

# Yaklaşan pivotlar
st.subheader("🔮 Yaklaşan pivotlar (gelecek 1 yıl)")
future_end = df.index[-1] + pd.Timedelta(days=365)
projected = best.cycle.project(df.index[-1], future_end)
if projected:
    rows = []
    for p in projected:
        lo, hi = best.cycle.window(p, tol_pct)
        rows.append({
            "İdeal pivot": p.strftime("%Y-%m-%d"),
            "Pencere başlangıç": lo.strftime("%Y-%m-%d"),
            "Pencere bitiş": hi.strftime("%Y-%m-%d"),
            "Bugünden gün": (p - pd.Timestamp.utcnow().tz_localize(None)).days,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
else:
    st.info("Önümüzdeki 12 ayda projekte edilen pivot yok.")
