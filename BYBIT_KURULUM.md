# Bybit Cross-Margin Lokal Kurulum (Prodüksiyon)

Bu cloud container'da Bybit kapalı (CloudFront geo-blok). Stratejiyi lokal makinende
Bybit cross-margin futures'ta çalıştırmak için adımlar:

## 1) Repoyu çek

```bash
git clone -b claude/inspiring-goldberg-iUjyt https://github.com/oznens/timecycle.git
cd timecycle
```

## 2) Sistem bağımlılıkları + TA-Lib

```bash
# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y build-essential wget python3-dev python3-venv git

# Mac
brew install ta-lib

# Linux: TA-Lib source build
wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
tar xzf ta-lib-0.6.4-src.tar.gz && cd ta-lib-0.6.4
./configure --prefix=/usr/local && make -j && sudo make install && sudo ldconfig && cd ..
```

## 3) Python venv

```bash
python3 -m venv .venv
source .venv/bin/activate     # Mac/Linux
# Windows: .venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 4) Bybit pairlist (top 100 ∩ Bybit listed)

```bash
EXCHANGE=bybit PAIRS_N=100 python scripts/build_pairlist.py
# user_data/pairlist_top100.json oluşur
```

Sonra `user_data/config.json` içine pair_whitelist olarak yapıştır.

## 5) Bybit API key

1. Bybit hesabı → **Account → API → Create New System-Generated Key**
2. **Permissions**:
   - ✅ Read-Write (Spot Trade)
   - ✅ Read-Write (Derivatives Trade)
   - ❌ **Withdrawal** (asla işaretleme!)
   - ❌ Subaccount Transfer (gerekmiyor)
3. **IP whitelist**: kendi IP'ni gir (zorunlu, güvenlik için)
4. `config.json` içine:
   ```json
   "exchange": {
     "name": "bybit",
     "key": "BURAYA_KEY",
     "secret": "BURAYA_SECRET",
     ...
   }
   ```
5. **Önce `dry_run: true` (paper) bırak!**

## 6) Cross-margin hesap ayarı

Bybit web → **Derivatives → Settings → Margin Mode**:
- Cross Margin ✓ (sermayenin tümü tüm pozisyonlar arasında paylaşılır)
- Leverage: 3x veya 5x öneriyorum scalping için (max 50x ama riskli)

## 7) Veri indir (Bybit)

```bash
freqtrade download-data \
    --config user_data/config.json \
    --timeframes 5m 1m \
    --timerange 20260101- \
    --trading-mode futures
```

98 sembol × 5m × 5ay = ~30dk sürer.

## 8) Hyperopt-tuned MR ile backtest

Hyperopt sonucu (`MeanReversionMTF.json`) zaten yüklü ve otomatik alınır:

```bash
freqtrade backtesting \
    --config user_data/config.json \
    --strategy MeanReversionMTF \
    --timeframe 5m \
    --timerange 20260101-
```

Cloud'da OKX'te elde edilen sonuçlar (84g, 8 pair):
- 29 trade, %82.8 win, +%1.61, DD %0.89, Sharpe 1.83

Bybit'te benzer bir sonuç beklenir (fee yapısı benzer, BTC/ETH likidite daha iyi).

## 9) Paper trade (dry_run)

```bash
freqtrade trade --config user_data/config.json --strategy MeanReversionMTF
```

İlk 7-14 gün dry_run'da bırak. Beklenen davranış:
- Günde 0-3 trade (5m, 8-20 pair üzerinden, MR sıkı koşullar)
- Win rate ~%75-85
- Bir tarihte küçük rally / küçük drawdown — backtest tutarlı mı kontrol et

## 10) Web UI (Telegram alternatif)

```json
"api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "username": "ozan",
    "password": "STRONG_PASSWORD_HERE"
}
```

`http://localhost:8080` — canlı trade listesi, profit grafiği, log.

## 11) Telegram bildirim

```json
"telegram": {
    "enabled": true,
    "token": "BOT_TOKEN_FROM_BOTFATHER",
    "chat_id": "YOUR_CHAT_ID"
}
```

@BotFather'da `/newbot`, `/start` ile chat_id al (`@userinfobot` ile öğren).

## 12) Canlı (dry_run: false)

⚠️ **Önce paper trade 2 hafta + backtest sonuçlarıyla tutarlı olmalı.**

```json
"dry_run": false
```

Komut aynı:
```bash
freqtrade trade --config user_data/config.json --strategy MeanReversionMTF
```

İlk 7 gün **çok küçük sermayeyle** (örn. $50-100) gerçek testle başla.
Tüm trade'leri logla, beklediğin gibi mi kontrol et.

## Sık sorulan

**"Cross-margin'de margin call olur mu?"** — Cross'ta tüm portfolio paylaşılır.
Tek pozisyon batırsa diğer açık pozisyonlardaki kar ile dengelenir. Maks 3x leverage
+ stoploss %2.5 ile margin call uzaktır ama imkânsız değil. **Asla %20'den fazla
sermayeyi tek anda riskte tutma.**

**"Funding rate'i strateji görür mü?"** — Evet, freqtrade futures backtest funding
rate'i hesaba katar (8 saatte bir ödeme/alım).

**"Hyperopt-tuned MR.json dosyası Bybit'te çalışır mı?"** — Stratejinin **mantığı**
exchange-agnostik. Parametreler **OKX 84g verisinde** tune edildi. Bybit'te benzer
ama farklı olabilir → ilk denemede bu params kullan, sonra Bybit verisiyle hyperopt
tekrarla.

**"`utils.py` modül bulunamadı hatası"** — `user_data/strategies/` Python yolunda
olmalı. `__init__.py` dosyaları repoda var; düşürdün mü diye kontrol et.

**"Hyperopt subprocess hatası"** — `-j 1` (single thread) ile çalıştır. Multi-process
joblib pickle sorunu nedeniyle. Yavaş ama çalışır.
