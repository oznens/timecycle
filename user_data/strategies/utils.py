"""
Ortak teknik analiz yardımcıları (stratejilerden import edilir).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import talib.abstract as ta


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd = ta.MACD(df, fastperiod=fast, slowperiod=slow, signalperiod=signal)
    df["macd"] = macd["macd"]
    df["macdsignal"] = macd["macdsignal"]
    df["macdhist"] = macd["macdhist"]
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df["rsi"] = ta.RSI(df, timeperiod=period)
    return df


def add_bb(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    bb = ta.BBANDS(df, timeperiod=period, nbdevup=std, nbdevdn=std, matype=0)
    df["bb_upper"]  = bb["upperband"]
    df["bb_middle"] = bb["middleband"]
    df["bb_lower"]  = bb["lowerband"]
    df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    return df


def add_emas(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.DataFrame:
    df[f"ema{fast}"] = ta.EMA(df, timeperiod=fast)
    df[f"ema{slow}"] = ta.EMA(df, timeperiod=slow)
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df["atr"] = ta.ATR(df, timeperiod=period)
    df["atr_pct"] = df["atr"] / df["close"]
    return df


def add_volume_avg(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    df["vol_avg"] = df["volume"].rolling(period).mean()
    df["vol_ratio"] = df["volume"] / df["vol_avg"]
    return df


# ---------------------------------------------------------------------------
# Basit Bull/Bear Divergence dedektörü
# ---------------------------------------------------------------------------
def add_macd_divergence(df: pd.DataFrame, lookback: int = 25) -> pd.DataFrame:
    """
    Bullish divergence: son `lookback` bar içinde son lokal min fiyat <= önceki min,
    fakat MACD histogram son lokal min > önceki min → 'macd_bull_div' = True.

    Tersi bearish. Local extrema basit `argrelextrema` ile.
    """
    from scipy.signal import argrelextrema

    close = df["close"].values
    hist  = df["macdhist"].values
    bull = np.zeros(len(df), dtype=bool)
    bear = np.zeros(len(df), dtype=bool)

    # 3-bar fractal extrema indeksleri
    order = 3
    lows_idx  = argrelextrema(close, np.less,    order=order)[0]
    highs_idx = argrelextrema(close, np.greater, order=order)[0]

    # Bullish div: son `lookback` içinde en az 2 swing low
    for i in range(lookback, len(df)):
        recent_lows = lows_idx[(lows_idx <= i) & (lows_idx > i - lookback)]
        if len(recent_lows) >= 2:
            a, b = recent_lows[-2], recent_lows[-1]
            if close[b] <= close[a] and hist[b] > hist[a]:
                bull[i] = True
        recent_highs = highs_idx[(highs_idx <= i) & (highs_idx > i - lookback)]
        if len(recent_highs) >= 2:
            a, b = recent_highs[-2], recent_highs[-1]
            if close[b] >= close[a] and hist[b] < hist[a]:
                bear[i] = True

    df["macd_bull_div"] = bull
    df["macd_bear_div"] = bear
    return df


# ---------------------------------------------------------------------------
# Bollinger band squeeze ölçer (BB / KC oranı)
# ---------------------------------------------------------------------------
def add_bb_squeeze(df: pd.DataFrame, period: int = 20, std: float = 2.0,
                    kc_mult: float = 1.5) -> pd.DataFrame:
    """
    Squeeze ON: BB tamamen Keltner Channel içinde (düşük volatilite, breakout öncesi).
    Squeeze OFF: BB Keltner dışına çıktı = breakout başladı.
    """
    # BB zaten add_bb ile eklenmiş varsayılır
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    kc_mid = typical.rolling(period).mean()
    atr = ta.ATR(df, timeperiod=period)
    kc_upper = kc_mid + kc_mult * atr
    kc_lower = kc_mid - kc_mult * atr
    df["kc_upper"] = kc_upper
    df["kc_lower"] = kc_lower

    df["squeeze_on"]  = (df["bb_upper"] < kc_upper) & (df["bb_lower"] > kc_lower)
    df["squeeze_off"] = (~df["squeeze_on"]) & df["squeeze_on"].shift(1).fillna(False)
    # momentum: linear regression slope of (close - midline) → basit proxy: roc
    df["squeeze_mom"] = (df["close"] - df["close"].rolling(period).mean()).diff()
    return df
