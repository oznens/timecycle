# Kurulum & Çalıştırma Kılavuzu

## Lokal kurulum (Bybit prodüksiyon)

### 1) Sistem bağımlılıkları (Linux/Mac)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential wget python3-dev python3-venv git

# Mac
brew install ta-lib
# (TA-Lib zaten geldi → 4. adımı atla)
```

### 2) TA-Lib (Linux için)

```bash
wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
tar xzf ta-lib-0.6.4-src.tar.gz
cd ta-lib-0.6.4
./configure --prefix=/usr/local
make -j
sudo make install
sudo ldconfig
cd ..
```

### 3) Repoyu çek

```bash
git clone -b claude/inspiring-goldberg-iUjyt https://github.com/oznens/timecycle.git
cd timecycle
```

### 4) Python venv + paketler

```bash
python3 -m venv .venv
source .venv/bin/activate           # Mac/Linux
# Windows: .venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install freqtrade scipy
```

### 5) Pairlist (top 100 USDT-perp)

```bash
python scripts/build_pairlist.py
# user_data/pairlist_top100.json oluştu
```

`config.json`'da `pair_whitelist` listesini bu dosyadan al — ya manuel kopyala, ya da
`VolumePairList` kullanarak Bybit'in canlı hacmine göre otomatik filtrele.

### 6) Bybit API key (paper/canlı için)

1. Bybit hesabında: **Account → API → Create New Key**
2. **Read + Trade + Withdrawal**: sadece **Read + Trade** seç (withdrawal asla!)
3. IP whitelist yap
4. `user_data/config.json` içine `key` ve `secret`'i yaz
5. **`dry_run: true`** kalsın (paper modda başla!)

### 7) Veri indir

```bash
freqtrade download-data \
    --config user_data/config.json \
    --timeframes 5m 1m \
    --timerange 20260101- \
    --trading-mode futures
```

İlk indirme ~10-30dk sürer (100 sembol × birden fazla TF).

### 8) Backtest

```bash
freqtrade backtesting \
    --config user_data/config.json \
    --strategy-list MeanReversionMTF TrendContinuation SqueezeBreakout OrderFlowProxy \
    --timeframe 5m \
    --timerange 20260101-
```

### 9) Hyperopt (parametre tarama)

```bash
freqtrade hyperopt \
    --config user_data/config.json \
    --strategy MeanReversionMTF \
    --hyperopt-loss SharpeHyperOptLoss \
    --spaces buy sell roi stoploss \
    --epochs 300 --timeframe 5m \
    --timerange 20260101-
```

Sonuçları görüntüle:
```bash
freqtrade hyperopt-show --best --no-details
```

### 10) Paper trade (dry_run)

```bash
freqtrade trade \
    --config user_data/config.json \
    --strategy MeanReversionMTF
```

Web UI: `http://localhost:8080` (config'te `api_server.enabled: true` yap)

### 11) Canlı (`dry_run: false`)

⚠️ **Önce minimum 2 hafta paper trade yap, sonuçlar pozitifse:**

```bash
# config.json'da:
"dry_run": false,
"dry_run_wallet": 1000  # bunun yerine gerçek bakiye kullanılır
```

Komut aynı:
```bash
freqtrade trade --config user_data/config.json --strategy MeanReversionMTF
```

---

## Cloud container kurulumu (Anthropic web)

Bu container'da Bybit/Binance geo-bloklu (CloudFront → HTTP 403/451).
Geliştirme + backtest için **OKX** kullanırız (linear USDT-perp, fees benzer).

### Önceden hazırlanmış venv

```bash
/opt/ftvenv/bin/freqtrade --version

# Strateji listele
/opt/ftvenv/bin/freqtrade list-strategies --config user_data/config.okx.json

# Veri indir (OKX)
/opt/ftvenv/bin/freqtrade download-data \
    --config user_data/config.okx.json \
    --timeframes 5m --timerange 20260301- --trading-mode futures

# Backtest 4 strateji
/opt/ftvenv/bin/freqtrade backtesting \
    --config user_data/config.okx.json \
    --strategy-list MeanReversionMTF TrendContinuation SqueezeBreakout OrderFlowProxy \
    --timeframe 5m --timerange 20260301-
```

### Cert sorunu (container içinde)

ccxt `certifi` bundle'ı kullanır; container'ın MITM cert'i sistem cert'inde
ama certifi'da yok. Tek seferlik düzeltme:

```bash
CERTIFI=$(/opt/ftvenv/bin/python -c "import certifi; print(certifi.where())")
cat /etc/ssl/certs/ca-certificates.crt >> "$CERTIFI"
```

---

## Komut özetleri

```bash
# Strateji listesi
freqtrade list-strategies --config user_data/config.json

# Pair listesi tıklat
freqtrade list-pairs --config user_data/config.json --print-list

# Backtest sonucu plot
freqtrade plot-dataframe --config user_data/config.json \
    --strategy MeanReversionMTF --pairs BTC/USDT:USDT

# Backtest sonuç raporları
freqtrade backtesting-show
```
