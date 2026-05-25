"""
TrendContinuation — MACD bullish/bearish cross + EMA 20/50 hizalı + RSI mid-zone.

Mantık:
  LONG  : MACD bull cross & EMA20 > EMA50 & 40 < RSI < 70 & vol_ratio > 1.0 & ATR yükseliyor
  SHORT : MACD bear cross & EMA20 < EMA50 & 30 < RSI < 60 & vol_ratio > 1.0

Mikro trend yakalama: trend yönünde kısa pozisyon, ilk düzeltmede çıkış.
"""
from __future__ import annotations
from datetime import datetime
import pandas as pd

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter

from utils import add_macd, add_rsi, add_emas, add_atr, add_volume_avg


class TrendContinuation(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True
    process_only_new_candles = True

    minimal_roi = {
        "0":  0.015,
        "20": 0.008,
        "45": 0.003,
        "90": 0.0,
    }
    stoploss = -0.020
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    rsi_long_lo  = IntParameter(35, 50, default=40, space="buy")
    rsi_long_hi  = IntParameter(60, 80, default=70, space="buy")
    rsi_short_lo = IntParameter(20, 40, default=30, space="buy")
    rsi_short_hi = IntParameter(50, 65, default=60, space="buy")
    vol_ratio_min = DecimalParameter(0.7, 2.0, default=1.0, decimals=2, space="buy")
    ema_fast      = IntParameter(10, 25, default=20, space="buy")
    ema_slow      = IntParameter(40, 100, default=50, space="buy")

    startup_candle_count = 200

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe.copy()
        df = add_macd(df, fast=12, slow=26, signal=9)
        df = add_rsi(df, period=14)
        df = add_emas(df, fast=int(self.ema_fast.value), slow=int(self.ema_slow.value))
        df = add_atr(df, period=14)
        df = add_volume_avg(df, period=20)

        ef = int(self.ema_fast.value)
        es = int(self.ema_slow.value)
        df["ema_stack_bull"] = df[f"ema{ef}"] > df[f"ema{es}"]
        df["ema_stack_bear"] = df[f"ema{ef}"] < df[f"ema{es}"]
        df["macd_bull_cross"] = (df["macd"] > df["macdsignal"]) & (df["macd"].shift(1) <= df["macdsignal"].shift(1))
        df["macd_bear_cross"] = (df["macd"] < df["macdsignal"]) & (df["macd"].shift(1) >= df["macdsignal"].shift(1))
        df["atr_rising"] = df["atr"] > df["atr"].shift(3)
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        long_cond = (
            df["macd_bull_cross"]
            & df["ema_stack_bull"]
            & (df["rsi"] > self.rsi_long_lo.value)
            & (df["rsi"] < self.rsi_long_hi.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & df["atr_rising"]
            & (df["volume"] > 0)
        )
        short_cond = (
            df["macd_bear_cross"]
            & df["ema_stack_bear"]
            & (df["rsi"] > self.rsi_short_lo.value)
            & (df["rsi"] < self.rsi_short_hi.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & df["atr_rising"]
            & (df["volume"] > 0)
        )
        df.loc[long_cond,  ["enter_long",  "enter_tag"]] = (1, "macd_x_ema_up")
        df.loc[short_cond, ["enter_short", "enter_tag"]] = (1, "macd_x_ema_down")
        return df

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        df.loc[df["macd_bear_cross"], ["exit_long",  "exit_tag"]] = (1, "macd_flip")
        df.loc[df["macd_bull_cross"], ["exit_short", "exit_tag"]] = (1, "macd_flip")
        return df

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                  max_leverage, side, **kwargs) -> float:
        return min(3.0, max_leverage)
