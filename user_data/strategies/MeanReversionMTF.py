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

    # Risk profili — küçük ama hızlı kazanç ("az az kazanalım")
    minimal_roi = {
        "0":  0.012,  # +1.2% giriş anında al
        "15": 0.008,  # 15dk sonra +0.8% olduysa al
        "30": 0.004,  # 30dk sonra +0.4% olduysa al
        "60": 0.0,    # 1 saat sonra break-even
    }
    stoploss = -0.018         # %1.8 hard stop
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True

    # Bybit USDT-perp gerçek fee: maker 0.01% / taker 0.06%
    # Freqtrade fee'yi ccxt'den okur; spot/futures ayrı.
    # Eklenen güvenlik için stake düşük tutulur (config'te `tradable_balance_ratio`).

    # Hyperopt için ayarlanabilir parametreler
    rsi_long_max  = IntParameter(low=20, high=35, default=30, space="buy")
    rsi_short_min = IntParameter(low=65, high=80, default=70, space="sell")
    bb_period     = IntParameter(low=15, high=30, default=20, space="buy")
    vol_ratio_min = DecimalParameter(low=0.5, high=1.5, default=0.8, decimals=2, space="buy")

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
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        long_cond = (
            (df["close"] <= df["bb_lower"])
            & (df["rsi"] < self.rsi_long_max.value)
            & (df["macd_bull_div"])
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > 0.001)   # ölü tahta filtresi
            & (df["volume"] > 0)
        )
        short_cond = (
            (df["close"] >= df["bb_upper"])
            & (df["rsi"] > self.rsi_short_min.value)
            & (df["macd_bear_div"])
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > 0.001)
            & (df["volume"] > 0)
        )
        df.loc[long_cond,  ["enter_long",  "enter_tag"]] = (1, "bb_low_rsi_div")
        df.loc[short_cond, ["enter_short", "enter_tag"]] = (1, "bb_high_rsi_div")
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
