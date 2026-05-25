"""
MeanReversionMTF — BB + RSI + MACD divergence bazlı mean-reversion scalper.

Mantık:
  LONG  : close <= BB_lower  & RSI < 30  & MACD bullish divergence  & vol_ratio > 0.8
  SHORT : close >= BB_upper  & RSI > 70  & MACD bearish divergence  & vol_ratio > 0.8

Çıkış: BB orta bandı, ROI laddiri, veya hard stop.

Cross-margin futures, can_short=True. Top 100 coin'den hangileri kuralları sağlarsa.
"""
from __future__ import annotations
from datetime import datetime
import pandas as pd

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter

from utils import (
    add_macd, add_rsi, add_bb, add_emas, add_atr, add_volume_avg,
    add_macd_divergence,
)


class MeanReversionMTF(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True
    process_only_new_candles = True

    # Risk profili: %60+ win rate gerektiriyor. Avg trade %1.0+ olmalı (fee'den 5-10x).
    minimal_roi = {
        "0":  0.025,  # %2.5 hedef — fee'den çok büyük
        "30": 0.015,  # 30dk sonra %1.5
        "90": 0.008,  # 90dk sonra %0.8
        "180": 0.0,   # 3 saat sonra BE
    }
    stoploss = -0.025          # %2.5 hard stop (1:1 RR)
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.020
    trailing_only_offset_is_reached = True

    # Yalnızca limit emir (maker, post-only) → fee 0.01% × 2 = 0.02% (10x daha az)
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "limit",
        "stoploss_on_exchange": False,
        "emergency_exit": "market",
    }

    # Daha sıkı parametreler — daha az ama daha güvenilir trade
    rsi_long_max  = IntParameter(low=18, high=32, default=26, space="buy")
    rsi_short_min = IntParameter(low=68, high=82, default=74, space="sell")
    bb_period     = IntParameter(low=15, high=30, default=20, space="buy")
    vol_ratio_min = DecimalParameter(low=0.8, high=2.0, default=1.1, decimals=2, space="buy")
    atr_min_pct   = DecimalParameter(low=0.001, high=0.008, default=0.002,
                                       decimals=4, space="buy")

    startup_candle_count = 200

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe.copy()
        df = add_bb(df, period=int(self.bb_period.value), std=2.0)
        df = add_rsi(df, period=14)
        df = add_macd(df, fast=12, slow=26, signal=9)
        df = add_emas(df, fast=20, slow=50)
        df = add_atr(df, period=14)
        df = add_volume_avg(df, period=20)
        df = add_macd_divergence(df, lookback=25)

        # HTF trend filtresi (1h ema50) — trend yönüne ters MR'i azalt
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["above_ema200"] = df["close"] > df["ema200"]
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        # LONG: HTF uptrend + (ekstreme satım VEYA güçlü divergence) + güçlü hacim
        long_cond = (
            (df["close"] <= df["bb_lower"])
            & (df["rsi"] < self.rsi_long_max.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > float(self.atr_min_pct.value))
            & (df["above_ema200"])
            & (df["volume"] > 0)
        )
        short_cond = (
            (df["close"] >= df["bb_upper"])
            & (df["rsi"] > self.rsi_short_min.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > float(self.atr_min_pct.value))
            & (~df["above_ema200"])
            & (df["volume"] > 0)
        )
        df.loc[long_cond,  ["enter_long",  "enter_tag"]] = (1, "bb_low_rsi_div_htf")
        df.loc[short_cond, ["enter_short", "enter_tag"]] = (1, "bb_high_rsi_div_htf")
        return df

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        df.loc[(df["close"] >= df["bb_middle"]) & (df["rsi"] > 50),
                ["exit_long",  "exit_tag"]] = (1, "bb_middle")
        df.loc[(df["close"] <= df["bb_middle"]) & (df["rsi"] < 50),
                ["exit_short", "exit_tag"]] = (1, "bb_middle")
        return df

    # Leverage: cross margin için sabit tut (hyperopt edilebilir)
    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                  max_leverage, side, **kwargs) -> float:
        return min(3.0, max_leverage)
