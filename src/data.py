"""
Çoklu veri kaynağı (pluggable) OHLC çekme.

Bu Anthropic cloud container'ında Bybit/Binance CloudFront geo-blok döndürüyor
(HTTP 403/451). Lokalde çalıştırırken `provider='bybit'` veya `'binance'` sorunsuz
çalışır. Container içinde varsayılan `'yfinance'` (Yahoo) — 11+ yıl BTC-USD verisi.
"""
from __future__ import annotations
import pandas as pd


def _yf(symbol: str, period: str, interval: str) -> pd.DataFrame:
    import yfinance as yf
    # ETH için 'ETH-USD' gibi
    df = yf.download(
        symbol, period=period, interval=interval,
        progress=False, auto_adjust=False, threads=False,
    )
    if df.empty:
        raise ValueError(f"{symbol} için Yahoo Finance verisi bulunamadı.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.dropna(subset=["close"])


def _ccxt(symbol: str, period: str, interval: str, exchange: str) -> pd.DataFrame:
    """Bybit/Binance için ccxt. Geo-bloklu ortamlarda hata verir."""
    import ccxt, time
    ex_cls = getattr(ccxt, exchange)
    ex = ex_cls({"enableRateLimit": True})
    # period -> ms
    period_days = {"1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 3650 * 3}
    days = period_days.get(period, 1825)
    timeframe = {"1d": "1d", "1wk": "1w", "1mo": "1M"}.get(interval, "1d")
    since = ex.milliseconds() - days * 86400 * 1000
    all_rows = []
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not batch:
            break
        all_rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts <= since or len(batch) < 2:
            break
        since = last_ts + 1
        time.sleep(ex.rateLimit / 1000)
        if len(all_rows) > 20000:
            break
    if not all_rows:
        raise ValueError(f"{exchange}:{symbol} için veri yok.")
    df = pd.DataFrame(all_rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    df = df.set_index("ts").drop_duplicates()
    return df.sort_index()


def fetch_ohlc(
    symbol: str,
    period: str = "max",
    interval: str = "1d",
    provider: str = "yfinance",
) -> pd.DataFrame:
    """
    Args:
        symbol: yfinance için 'BTC-USD', ccxt için 'BTC/USDT'
        period: '1y','2y','5y','10y','max'
        interval: '1d','1wk','1mo'
        provider: 'yfinance' | 'bybit' | 'binance' | 'kraken'
    """
    if provider == "yfinance":
        return _yf(symbol, period, interval)
    if provider in {"bybit", "binance", "kraken", "coinbase"}:
        return _ccxt(symbol, period, interval, provider)
    raise ValueError(f"Bilinmeyen provider: {provider}")
