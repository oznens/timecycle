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
        "0":  0.030,
        "30": 0.015,
        "90": 0.005,
        "180": 0.0,
    }
    stoploss = -0.025
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.020
    trailing_only_offset_is_reached = True

    order_types = {
        "entry": "limit", "exit": "limit", "stoploss": "limit",
        "stoploss_on_exchange": False, "emergency_exit": "market",
    }

    rsi_long_lo  = IntParameter(35, 55, default=45, space="buy")
    rsi_long_hi  = IntParameter(60, 75, default=68, space="buy")
    rsi_short_lo = IntParameter(25, 40, default=32, space="buy")
    rsi_short_hi = IntParameter(45, 65, default=55, space="buy")
    vol_ratio_min = DecimalParameter(1.0, 2.5, default=1.3, decimals=2, space="buy")
    atr_min_pct   = DecimalParameter(0.002, 0.008, default=0.003, decimals=4, space="buy")
    ema_fast      = IntParameter(10, 25, default=20, space="buy")
    ema_slow      = IntParameter(40, 100, default=50, space="buy")

    startup_candle_count = 250

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

        # HTF EMA200 trend filter
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["above_ema200"] = df["close"] > df["ema200"]
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        long_cond = (
            df["macd_bull_cross"]
            & df["ema_stack_bull"]
            & df["above_ema200"]                              # HTF trend onayı
            & (df["rsi"] > self.rsi_long_lo.value)
            & (df["rsi"] < self.rsi_long_hi.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > float(self.atr_min_pct.value))
            & df["atr_rising"]
            & (df["volume"] > 0)
        )
        short_cond = (
            df["macd_bear_cross"]
            & df["ema_stack_bear"]
            & (~df["above_ema200"])                            # HTF trend onayı
            & (df["rsi"] > self.rsi_short_lo.value)
            & (df["rsi"] < self.rsi_short_hi.value)
            & (df["vol_ratio"] > float(self.vol_ratio_min.value))
            & (df["atr_pct"] > float(self.atr_min_pct.value))
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
