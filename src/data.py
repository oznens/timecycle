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
    yf_iv_map = {tf: cfg[1] for tf, cfg in _TF_MAP.items() if cfg[1] is not None}
    yf_iv = yf_iv_map.get(interval, interval)
    # yfinance küçük TF'de kısıtlı periyot
    if interval in {"15m", "30m"} and period in {"5y", "10y", "max"}:
        period = "60d"
    if interval in {"1h", "2h"} and period in {"5y", "10y", "max"}:
        period = "730d"
    df = yf.download(
        symbol, period=period, interval=yf_iv,
        progress=False, auto_adjust=False, threads=False,
    )
    if df.empty:
        raise ValueError(f"{symbol} için Yahoo Finance verisi bulunamadı.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.dropna(subset=["close"])


# interval str → (ccxt timeframe, yfinance interval, ortalama saat)
_TF_MAP = {
    "15m": ("15m", "15m", 0.25),
    "30m": ("30m", "30m", 0.5),
    "1h":  ("1h",  "1h",  1.0),
    "2h":  ("2h",  "2h",  2.0),
    "4h":  ("4h",  None,  4.0),    # yfinance 4h desteklemez
    "12h": ("12h", None,  12.0),
    "1d":  ("1d",  "1d",  24.0),
    "1wk": ("1w",  "1wk", 168.0),
    "1mo": ("1M",  "1mo", 720.0),
}


def _ccxt(symbol: str, period: str, interval: str, exchange: str) -> pd.DataFrame:
    """Bybit/Binance/Kraken için ccxt. Geo-bloklu ortamlarda hata verir."""
    import ccxt, time
    ex_cls = getattr(ccxt, exchange)
    ex = ex_cls({"enableRateLimit": True, "options": {"defaultType": "spot"}})
    period_days = {"1mo_p": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730,
                   "5y": 1825, "10y": 3650, "max": 3650 * 3}
    # 'max' düşük TF için pratik değil — TF'ye göre üst sınır
    tf_cfg = _TF_MAP.get(interval)
    if tf_cfg is None:
        raise ValueError(f"Bilinmeyen interval: {interval}")
    timeframe, _, hours = tf_cfg
    days = period_days.get(period, 1825)
    # küçük TF'lerde max periyodu mantıklı tutalım
    if hours < 1 and days > 60:
        days = 60
    elif hours < 24 and days > 730:
        days = 730

    since = ex.milliseconds() - days * 86400 * 1000
    all_rows = []
    limit = 1000
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        if not batch:
            break
        all_rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts <= since or len(batch) < 2:
            break
        # bir sonraki sayfanın başlangıcı
        since = last_ts + int(hours * 3600 * 1000)
        time.sleep(ex.rateLimit / 1000)
        if len(all_rows) > 50000:
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
