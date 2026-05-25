"""
OrderFlowProxy — Order book imbalance proxy + canlıda gerçek OB confirm.

ÖNEMLİ NOT:
  Gerçek order book verisi freqtrade backtest'inde yok (sadece dry_run/live'da
  `dp.orderbook(pair, depth)` ile alınır). Bu yüzden backtest için bar bazlı
  bir 'alıcı baskısı' proxy'si kullanıyoruz: yüksek hacim + alıcı kapanış
  (close > (high+low)/2) ardışık barlarında.

  Canlıda `confirm_trade_entry` kancası ile gerçek OB imbalance kontrolü
  yapılır: top-5 bid_vol / ask_vol > 1.5 → long onaylanır.

Mantık (backtest proxy):
  LONG  : son 3 barda → 2+ bar "buying pressure" (close üst yarı, vol > 1.2x) &
          RSI 40-65 & MACD > sinyal
  SHORT : son 3 barda → 2+ bar "selling pressure" (close alt yarı, vol > 1.2x) &
          RSI 35-60 & MACD < sinyal
"""
from __future__ import annotations
import logging
from datetime import datetime

import numpy as np
import pandas as pd

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.enums import RunMode

from utils import add_macd, add_rsi, add_emas, add_atr, add_volume_avg


logger = logging.getLogger(__name__)


class OrderFlowProxy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True
    process_only_new_candles = True

    minimal_roi = {
        "0":  0.020,
        "20": 0.010,
        "60": 0.005,
        "120": 0.0,
    }
    stoploss = -0.018
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    order_types = {
        "entry": "limit", "exit": "limit", "stoploss": "limit",
        "stoploss_on_exchange": False, "emergency_exit": "market",
    }

    # Backtest proxy parametreleri — sıkı
    vol_mult       = DecimalParameter(1.2, 3.0, default=1.6, decimals=2, space="buy")
    pressure_bars  = IntParameter(2, 5, default=3, space="buy")
    pressure_window= IntParameter(3, 7, default=4, space="buy")
    atr_min_pct    = DecimalParameter(0.002, 0.008, default=0.003, decimals=4, space="buy")
    # Live OB imbalance eşiği
    ob_imbalance_ratio = 1.5
    ob_depth = 5

    startup_candle_count = 250

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe.copy()
        df = add_macd(df, fast=12, slow=26, signal=9)
        df = add_rsi(df, period=14)
        df = add_emas(df, fast=20, slow=50)
        df = add_atr(df, period=14)
        df = add_volume_avg(df, period=20)

        # Body pozisyonu: candle hacminin alıcı vs satıcıya dağılımı tahmini
        body_pos = (df["close"] - df["low"]) / (df["high"] - df["low"]).replace(0, np.nan)
        df["body_pos"] = body_pos.fillna(0.5)
        df["buying_bar"]  = (df["body_pos"] > 0.65) & (df["vol_ratio"] > float(self.vol_mult.value))
        df["selling_bar"] = (df["body_pos"] < 0.35) & (df["vol_ratio"] > float(self.vol_mult.value))

        win = int(self.pressure_window.value)
        df["buy_pressure"]  = df["buying_bar"].rolling(win).sum()
        df["sell_pressure"] = df["selling_bar"].rolling(win).sum()

        # HTF EMA200 trend filter
        df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["above_ema200"] = df["close"] > df["ema200"]
        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        pmin = int(self.pressure_bars.value)
        long_cond = (
            (df["buy_pressure"] >= pmin)
            & df["above_ema200"]                              # HTF trend onayı
            & (df["rsi"] > 40) & (df["rsi"] < 65)
            & (df["macd"] > df["macdsignal"])
            & (df["close"] > df["ema20"])
            & (df["atr_pct"] > float(self.atr_min_pct.value))
            & (df["volume"] > 0)
        )
        short_cond = (
            (df["sell_pressure"] >= pmin)
            & (~df["above_ema200"])                            # HTF trend onayı
            & (df["rsi"] > 35) & (df["rsi"] < 60)
            & (df["macd"] < df["macdsignal"])
            & (df["close"] < df["ema20"])
            & (df["atr_pct"] > float(self.atr_min_pct.value))
            & (df["volume"] > 0)
        )
        df.loc[long_cond,  ["enter_long",  "enter_tag"]] = (1, "ofproxy_buy_pressure")
        df.loc[short_cond, ["enter_short", "enter_tag"]] = (1, "ofproxy_sell_pressure")
        return df

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = dataframe
        df.loc[df["selling_bar"] & (df["macd"] < df["macdsignal"]),
                ["exit_long",  "exit_tag"]] = (1, "pressure_flip")
        df.loc[df["buying_bar"] & (df["macd"] > df["macdsignal"]),
                ["exit_short", "exit_tag"]] = (1, "pressure_flip")
        return df

    # ------------------------------------------------------------------ #
    # Canlı: gerçek OB imbalance ile entry'i onayla / iptal et            #
    # ------------------------------------------------------------------ #
    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                              rate: float, time_in_force: str,
                              current_time: datetime, entry_tag: str | None,
                              side: str, **kwargs) -> bool:
        # Backtest/hyperopt'ta canlı OB anlamsız → onayla (proxy sinyali kullanılır).
        # Sadece dry_run/live'da gerçek OB imbalance kontrolü yap.
        if self.dp.runmode in (RunMode.BACKTEST, RunMode.HYPEROPT):
            return True
        try:
            ob = self.dp.orderbook(pair, maximum=self.ob_depth)
        except Exception:
            return True
        if not ob or not ob.get("bids") or not ob.get("asks"):
            return True

        bid_vol = sum(b[1] for b in ob["bids"][:self.ob_depth])
        ask_vol = sum(a[1] for a in ob["asks"][:self.ob_depth])
        if ask_vol == 0:
            return True
        imb = bid_vol / ask_vol

        if side == "long" and imb < self.ob_imbalance_ratio:
            logger.info(f"[{pair}] LONG OB imbalance yetersiz: {imb:.2f} < {self.ob_imbalance_ratio}")
            return False
        if side == "short" and imb > (1.0 / self.ob_imbalance_ratio):
            logger.info(f"[{pair}] SHORT OB imbalance yetersiz: {imb:.2f}")
            return False
        return True

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                  max_leverage, side, **kwargs) -> float:
        return min(3.0, max_leverage)
