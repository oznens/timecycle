# 4 Strateji — Detaylar

Tüm stratejiler:
- **TF**: 5m (1m da kullanılabilir, parametre revize gerekir)
- **Trading mode**: futures, isolated (OKX dev) / cross (Bybit prod)
- **can_short**: True
- **Leverage**: maks 3x (config'ten ayarlanır)
- **Pair universe**: top 100 USDT-perp

Tüm risk parametreleri kısa vadeli scalp için ayarlandı — "az ama sık" (kullanıcının
isteği). Stop loss tight, ROI ladder erken kâr alır.

---

## 1. MeanReversionMTF — Klasik MM tarzı

**Mantık**: Fiyat extreme uçlara gittiğinde, RSI doygunluğa ulaştığında ve MACD
histogram divergence sinyali verdiğinde tersine pozisyon. Klasik "satıcılar tükendi,
alıcılar gelecek" varsayımı.

**Sinyal seti (LONG)**:
- `close ≤ BB_lower` (Bollinger alt band)
- `RSI < 30` (aşırı satım)
- `macd_bull_div = True` (fiyat lower-low yaparken MACD histogram higher-low)
- `vol_ratio > 0.8` (volüm ölmediği sürece)
- `atr_pct > 0.001` (yeterli volatilite)

**Çıkış**: BB middle band'a dönüş + RSI > 50 (LONG için)

**Risk profili**:
- SL: -1.8% hard
- ROI: 1.2% → 0.8% (15dk) → 0.4% (30dk) → BE (60dk)
- Trailing: %0.5 (1.2% kar olduktan sonra)

**Hyperopt edilebilir**: rsi_long_max, rsi_short_min, bb_period, vol_ratio_min

**Beklenen davranış**: Range-bound piyasalarda iyi (BTC sideways dönemler).
Trend günlerinde "knife catching" tehlikesi var → SL hassasiyeti önemli.

---

## 2. TrendContinuation — Mikro trend yakalama

**Mantık**: Trend yönünde MACD bull/bear cross + EMA stack onayı + RSI henüz
extreme'de değilse → küçük continuation pozisyonu. İlk düzeltmede çık.

**Sinyal seti (LONG)**:
- `MACD bull cross` (macd > signal, önceki bar tersi)
- `EMA20 > EMA50`
- `40 < RSI < 70` (overbought değil ama momentum var)
- `vol_ratio > 1.0`
- `ATR yükseliyor` (volatilite artıyor)

**Çıkış**: MACD bear cross (pozisyon flip sinyali)

**Risk profili**:
- SL: -2.0%
- ROI: 1.5% → 0.8% (20dk) → 0.3% (45dk) → BE (90dk)
- Trailing: %0.6 (1.5% sonra)

**Beklenen davranış**: Trend günlerinde iyi (BTC ATH testleri, breakout sonrası).
Sideways'de fakeout'larda kaybeder.

---

## 3. SqueezeBreakout — Volatilite patlaması

**Mantık**: BB Keltner Channel içine sıkıştığında (squeeze ON), düşük volatilite
biriken enerji. KC dışına çıkış (squeeze OFF) → patlama başladı. Momentum
yönünde gir, ilk hızlanmayı yakala.

**Sinyal seti (LONG)**:
- `squeeze_on (önceki 1-2 bar)` → `squeeze_off (mevcut)` (yeni breakout)
- `squeeze_mom > 0` (momentum pozitif)
- `close > BB_middle`
- `vol_ratio > 1.5` (hacim onayı)
- `MACD > signal`

**Çıkış**: Momentum tükendi (BB middle'a geri dön)

**Risk profili**:
- SL: -1.5% (yanlış yön = hızlı çık)
- ROI: 2.0% → 1.0% (10dk) → 0.5% (30dk) → BE (60dk)
- Trailing: %0.8 (1.5% sonra)

**Beklenen davranış**: Haber/event sonrası (Powell konuşması, CPI, halving anı)
mükemmel. Sakin günlerde sinyal azalır = sorun değil, az ama keskin.

---

## 4. OrderFlowProxy — OB imbalance proxy + canlı OB confirm

**Önemli**: Gerçek order book verisi backtest'te yok (freqtrade kısıtlaması).
Backtest için **bar bazlı proxy** kullanıyoruz: yüksek hacim + alıcı/satıcı
ağırlıklı close (body position) ardışık barları.

**Backtest sinyali (LONG)**:
- Son 3 barda → 2+ bar **buying bar**
  - `body_pos > 0.6` (close, candle üst yarısında)
  - `vol_ratio > 1.2`
- `RSI 40-65`
- `MACD > signal`
- `close > EMA20`

**Canlı onay (LONG)** — `confirm_trade_entry`:
- `dp.orderbook(pair, depth=5)` ile gerçek bid/ask hacmi
- `bid_vol / ask_vol > 1.5` → onayla, değilse iptal

**Risk profili**:
- SL: -1.2% (en sıkı)
- ROI: 1.0% → 0.6% (10dk) → 0.3% (25dk) → BE (60dk)

**Beklenen davranış**: Canlıda gerçek MM benzeri davranış. Backtest'te proxy
yaklaşık sonuç verir, %100 doğru olmayabilir → live forward-test şart.

---

## Fee + slippage hesabı

Bybit USDT-perp (VIP-0):
- Maker: 0.01% (limit, post-only) → 1k pos açıp kapama = 0.02% toplam
- Taker: 0.06% (market) → 1k pos açıp kapama = 0.12% toplam
- Funding rate: 8 saatte bir, ±0.01% ortalama

Freqtrade `entry_pricing.use_order_book` → limit-as-maker, taker'a kaçınmaya
çalışır. Ama partial fill durumunda kalanı taker olur.

**Realistik trade başına maliyet**: ~0.05-0.10%. Bu yüzden ROI'nin minimum 0.3%
olması gerekiyor (3-10x maliyet).

---

## Strateji seçim akışı

1. **Backtest'te** 4'ünü aynı dönemde çalıştır → en yüksek **Sharpe + Calmar**
2. **Hyperopt** ile parametre tara (her strateji için ayrı):
   ```bash
   freqtrade hyperopt --config user_data/config.json \
       --strategy MeanReversionMTF --hyperopt-loss SharpeHyperOptLoss \
       --spaces buy sell --epochs 200
   ```
3. **Walk-forward test** (out-of-sample doğrulama)
4. **Paper trade** (dry_run=true) — minimum 2 hafta canlı verisi
5. Gerçek küçük sermayeyle başla, ölçekle

## Önemli notlar

- ❌ **Backtest ≠ canlı**: 5m scalping'te slippage backtest'te tam yansımaz
- ❌ **Cherry-picking**: Aşırı parametre tuning curve-fitting yaratır
- ✅ **Out-of-sample**: Hyperopt 6 aylık veri / live'a koymadan önce farklı 1 ayla doğrula
- ✅ **Risk management**: Asla cüzdanın >10%'unu tek trade'e açma; max_open_trades
  ile dağıt
