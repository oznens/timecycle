"""
Plotly grafik: fiyat (mum) + altta yarım daire döngüler + zaman pencereleri.

Yarım daireleri SVG path olarak çizmek yerine,
sayısal hesap edilmiş eğri noktalarını secondary axis'te scatter trace olarak
çiziyoruz — bu sayede log-mod fiyat ekseni etkilenmiyor.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

from .cycle import Cycle
from .dominance import DominanceReport


def _semicircle(
    center: pd.Timestamp, radius_days: float, n: int = 60
) -> tuple[list[str], list[float]]:
    """y >= 0 olan üst yarım daire. Plotly image-export uyumu için ISO string."""
    theta = np.linspace(np.pi, 0, n)
    xs = [
        (pd.Timestamp(center) + timedelta(days=float(radius_days * np.cos(t)))).isoformat()
        for t in theta
    ]
    ys = (radius_days * np.sin(theta)).tolist()
    return xs, ys


def build_chart(
    df: pd.DataFrame,
    actual_lows: pd.DatetimeIndex,
    layers: list[tuple[DominanceReport, str]],
    title: str,
    log_y: bool = True,
) -> go.Figure:
    """
    layers: [(DominanceReport, hex_renk), ...] — birden fazla döngü üst üste
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.02,
        subplot_titles=(title, "Zaman Döngüleri (yarım daire = bir alt döngü)"),
    )

    # 1) Fiyat (mum + close çizgi gizlenmiş)
    x_str = [ts.isoformat() for ts in df.index]
    fig.add_trace(
        go.Candlestick(
            x=x_str,
            open=df["open"].tolist(), high=df["high"].tolist(),
            low=df["low"].tolist(), close=df["close"].tolist(),
            name="Fiyat", increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # 2) Tespit edilen tüm anlamlı dipler (küçük X)
    if len(actual_lows):
        low_vals = df.loc[actual_lows, "low"]
        fig.add_trace(
            go.Scatter(
                x=[ts.isoformat() for ts in actual_lows], y=low_vals.tolist(),
                mode="markers", name="Anlamlı dipler",
                marker=dict(symbol="x", size=8, color="#888"),
            ),
            row=1, col=1,
        )

    # 3) Her katman için: pivot çizgileri + pencere alanları + yarım daireler
    def _iso(ts):
        return pd.Timestamp(ts).isoformat()

    for report, color in layers:
        cyc = report.cycle
        sub_d = cyc.sub_days
        radius = sub_d / 2.0

        # Tüm projeksiyon pivotları (vurgu: vurulan/kaçırılan)
        all_pivots = cyc.project(df.index[0], df.index[-1])
        hit_set = set(report.hit_dates)
        for piv in all_pivots:
            is_hit = piv in hit_set
            line_color = color if is_hit else "rgba(150,150,150,0.4)"
            fig.add_vline(
                x=_iso(piv), line_width=1, line_dash="dot",
                line_color=line_color, row=1, col=1,
            )
            # 5/10/15% pencere kutuları
            for pct, alpha in [(0.15, 0.05), (0.10, 0.08), (0.05, 0.18)]:
                lo, hi = cyc.window(piv, pct)
                fig.add_vrect(
                    x0=_iso(lo), x1=_iso(hi),
                    fillcolor=color, opacity=alpha, line_width=0,
                    row=1, col=1,
                )
            # Yarım daire (alt panel)
            xs, ys = _semicircle(piv, radius)
            fig.add_trace(
                go.Scatter(
                    x=xs, y=ys, mode="lines",
                    line=dict(color=color, width=1.5),
                    showlegend=False, hoverinfo="skip",
                ),
                row=2, col=1,
            )
        # Seed işaretleri
        for s, label in [(cyc.seed_a, "A"), (cyc.seed_b, "B")]:
            try:
                y_anchor = float(df.loc[:s, "low"].iloc[-1])
            except (KeyError, IndexError):
                y_anchor = float(df["low"].min())
            fig.add_annotation(
                x=_iso(s), y=y_anchor,
                text=label, showarrow=True, arrowhead=2,
                ax=0, ay=30, font=dict(color=color, size=12),
                row=1, col=1,
            )
        # Eşleştirilen gerçek dipleri yıldız
        if report.matched_actuals:
            fig.add_trace(
                go.Scatter(
                    x=[ts.isoformat() for ts in report.matched_actuals],
                    y=df.loc[report.matched_actuals, "low"].tolist(),
                    mode="markers", name=f"Eşleşen dip ({int(sub_d)}g)",
                    marker=dict(symbol="star", size=11, color=color),
                ),
                row=1, col=1,
            )

    fig.update_layout(
        height=820, hovermode="x unified",
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(type="log" if log_y else "linear", row=1, col=1)
    fig.update_yaxes(visible=False, row=2, col=1)
    fig.update_xaxes(showspikes=True, spikemode="across", spikecolor="#aaa")
    return fig
