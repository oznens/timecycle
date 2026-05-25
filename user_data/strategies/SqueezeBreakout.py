"""
SqueezeBreakout — Bollinger Band squeeze sonrası volatilite genişlemesinde breakout.

Mantık:
  - Squeeze ON: BB tamamen Keltner Channel içinde (düşük volatilite, biriken enerji)
  - Squeeze OFF: BB Keltner dışına çıktı → volatilite expansion başladı

  LONG  : squeeze_off (yeni) & squeeze_mom > 0 & close > BB_middle & vol_ratio > 1.5
  SHORT : squeeze_off (yeni) & squeeze_mom < 0 & close < BB_middle & vol_ratio > 1.5

Volatile burst'ün ilk birkaç barını yakala, hızlı çık.
"""
from __future__ import annotations
import pandas as pd

from freqtrade.strategy import IStrategy, DecimalParameter

from utils import (
    add_macd, add_rsi, add_bb, add_atr, add_volume_avg, add_bb_squeeze,
)


class SqueezeBreakout(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True
    process_only_new_candles = True

    # Squeeze breakout volatile → daha geniş ROI, tighter stop
    minimal_roi = {
        "0":  0.020,
        "10": 0.010,
        "30": 0.005,
        "60": 0.0,
    }
    stoploss = -0.015        # squeeze yanlış yönlü gelirse hızlı çık
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    vol_ratio_min = DecimalParameter(1.0, 3.0, default=1.5, decimals=2, space="buy")
    kc_mult       = DecimalParameter(1.0, 2.0, default=1.5, decimals=2, space="buy")

    startup_candle_count = 200

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe.copy()
        df = add_bb(df, period=20, std=2.0)
        df = add_bb_squeeze(df, period=20, std=2.0, kc_mult=float(self.kc_mult.value))
        df = add_rsi(df, period=14)
        df = add_macd(df, fast=12, slow=26, signal=9)
        df = add_atr(df, period=14)
        df = add_volume_avg(df, period=20)
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        # squeeze son birkaç barda ON'dan OFF'a yeni geçti
        recently_squeezed = df["squeeze_on"].shift(1).fillna(False) | df["squeeze_on"].shift(2).fillna(False)
        breakout = (~df["squeeze_on"]) & recently_squeezed

        long_cond = (
            breakout
            & (df["squeeze_mom"] > 0)
            & (df["close"] > df["bb_middle"])
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["macd"] > df["macdsignal"])
            & (df["volume"] > 0)
        )
        short_cond = (
            breakout
            & (df["squeeze_mom"] < 0)
            & (df["close"] < df["bb_middle"])
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["macd"] < df["macdsignal"])
            & (df["volume"] > 0)
        )
        df.loc[long_cond,  ["enter_long",  "enter_tag"]] = (1, "sqz_break_up")
        df.loc[short_cond, ["enter_short", "enter_tag"]] = (1, "sqz_break_down")
        return df

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        # momentum tükendi (BB band'ına dönüş)
        df.loc[(df["close"] < df["bb_middle"]) & (df["squeeze_mom"] < 0),
                ["exit_long",  "exit_tag"]] = (1, "sqz_mom_fade")
        df.loc[(df["close"] > df["bb_middle"]) & (df["squeeze_mom"] > 0),
                ["exit_short", "exit_tag"]] = (1, "sqz_mom_fade")
        return df

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                  max_leverage, side, **kwargs) -> float:
        return min(3.0, max_leverage)
