# Scalper MM — Top 100 Coin Cross-Margin Bot

Bybit USDT-perp üzerinde top 100 coin'i tarayıp **1m/5m** scalping yapan bot.
**freqtrade** üstüne kurulu, 4 strateji + paper trade + canlı destekli.

> **Çekirdek prensip**: Az ama sık. Market maker zihniyeti — mikro fiyat
> hareketlerinden küçük kâr al, fee'leri (maker 0.01% / taker 0.06%) hesaba kat.

## İçerik

- `user_data/config.json` — **Bybit cross-margin** prodüksiyon config (lokalde kullanırsın)
- `user_data/config.okx.json` — **OKX isolated** geliştirme config (cloud container'da backtest için)
- `user_data/strategies/` — 4 strateji + ortak `utils.py`
- `user_data/pairlist_top100.json` — CoinGecko top 100 marketcap → Bybit USDT-perp formatı
- `scripts/build_pairlist.py` — Pairlist güncelleyici
- `STRATEJI.md` — Stratejilerin mantık + parametreleri (TR)
- `KURULUM.md` — Lokal kurulum (Bybit) + cloud setup (OKX dev)

## Hızlı başlangıç

```bash
# 1) Clone + virtualenv
git clone -b claude/inspiring-goldberg-iUjyt https://github.com/oznens/timecycle.git
cd timecycle
python3 -m venv .venv && source .venv/bin/activate

# 2) Sistem bağımlılıkları (TA-Lib)
sudo apt-get install -y build-essential wget python3-dev
wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
tar xzf ta-lib-0.6.4-src.tar.gz && cd ta-lib-0.6.4
./configure --prefix=/usr/local && make && sudo make install
sudo ldconfig && cd ..

# 3) Python paketleri
pip install freqtrade scipy

# 4) Pairlist üret (top 100)
python scripts/build_pairlist.py

# 5) Veri indir (Bybit'ten)
freqtrade download-data --config user_data/config.json --timeframes 5m 1m \
    --timerange 20260101- --trading-mode futures

# 6) Backtest (her strateji)
freqtrade backtesting --config user_data/config.json \
    --strategy-list MeanReversionMTF TrendContinuation SqueezeBreakout OrderFlowProxy \
    --timeframe 5m --timerange 20260101-

# 7) Paper trade (dry_run=true)
freqtrade trade --config user_data/config.json --strategy MeanReversionMTF
```

## 4 Strateji (özet)

| Strateji | Mantık | TF | Risk |
|---|---|---|---|
| **MeanReversionMTF** | BB alt/üst + RSI extreme + MACD divergence | 5m | SL 1.8% / ROI ladder |
| **TrendContinuation** | MACD bull cross + EMA stack + RSI 40-70 | 5m | SL 2.0% / trailing |
| **SqueezeBreakout** | BB squeeze → expansion + volume burst | 5m | SL 1.5% / hızlı çık |
| **OrderFlowProxy** | Buying/selling pressure proxy + canlıda gerçek OB | 5m | SL 1.2% / sıkı |

Detay → [`STRATEJI.md`](STRATEJI.md)

## Bybit vs OKX

| | Bybit | OKX (dev) |
|---|---|---|
| **Margin mode** | cross ✅ | isolated (freqtrade kısıtlaması) |
| **Maker fee** | 0.01% | 0.02% |
| **Taker fee** | 0.06% | 0.05% |
| **Container erişimi** | ❌ (CloudFront geo-blok) | ✅ |

Geliştirmeyi OKX'te yap, prodüksiyona Bybit'te geç. Strateji aynı çalışır.
