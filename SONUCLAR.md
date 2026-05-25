# Backtest Sonuçları & İterasyonlar

Hedef: top 100 USDT-perp · 5m · cross-margin · market-maker tarzı küçük kârlar.

## 1. İlk backtest — default params (84g, 8 pair)

| Strateji | Trades | Win% | Avg P | Toplam | DD |
|---|---|---|---|---|---|
| MeanReversionMTF | 682 | 60.6% | -0.31% | -21.98% | 22.44% |
| TrendContinuation | 2005 | 37.5% | -0.31% | -52.47% | 53.22% |
| SqueezeBreakout | 2310 | 45.5% | -0.31% | -56.69% | 58.34% |
| OrderFlowProxy | 3315 | 48.2% | -0.40% | -78.91% | 78.91% |

Asıl sorun: çok fazla trade × fee = sermaye yiyor.

## 2. MR v3 — sıkı filtreler + maker-only (84g, 8 pair)

Değişiklikler:
- HTF EMA200 trend filtresi
- RSI threshold sıkıldı (long 26, short 74)
- vol_ratio min 1.1, atr min 0.002
- Limit-only emir (fee 0.05% → 0.01%)
- ROI ladder yükseltildi
- MACD divergence şartı çıkarıldı (sinyal kıtlığı yarattı)

| Trades | Win% | Avg P | Toplam | DD |
|---|---|---|---|---|
| 23 | 56.5% | -0.53% | **-1.44%** | **1.73%** |

15x daha az kayıp, 13x daha az drawdown.

## 3. MR hyperopt (8 pair, 40 epoch, Sharpe loss)

Optimum params (`MeanReversionMTF.json`):
- `rsi_long_max: 19` (derin oversold)
- `bb_period: 26`
- `vol_ratio_min: 1.22`
- `atr_min_pct: 0.003`
- ROI: 0:9.6 → 33:3.4 → 73:1.0 → 97:BE
- SL: -30.9% (trailing aktif olduğu için soft)

Doğrulama (aynı 8 pair, in-sample):
| Trades | Win% | Avg P | Toplam | DD | Sharpe |
|---|---|---|---|---|---|
| 29 | **82.8%** | **+0.47%** | **+1.61%** | **0.89%** | **1.83** |

## 4. Out-of-sample test — 15 pair (overfitting bulgusu!)

Aynı hyperopt params, eklenen 7 pair (HYPE, ZEC, CC, XLM, TON, TRX, BCH):

| Trades | Win% | Avg P | Toplam | DD | Sharpe |
|---|---|---|---|---|---|
| 81 | 72.8% | -0.14% | **-1.13%** | 5.80% | -0.63 |

**Bulgu**: hyperopt 8 pair'e aşırı uyumlanmış. Yeni pair'lerde win rate hâlâ %72.8 (iyi) ama avg profit fee'yi yetersiz aşıyor.

**Sonraki adım**: hyperopt'u 15+ pair üzerinde tekrar et → daha sağlam genelleştirilmiş params.

## 5. Devam ediyor: 98 pair download + hyperopt 15 pair

Şu an arka planda:
- 98 pair tam veri indirmesi (OKX rate-limit, ~50dk total)
- 15 pair üzerinde yeniden hyperopt (60 epoch, ~10-15dk)

## 6. Yapılacaklar

- [ ] 15 pair hyperopt sonuçları → daha sağlam params
- [ ] 98 pair download bitti → full universe backtest
- [ ] Walk-forward test: 1. yarısında hyperopt, 2. yarısında doğrula
- [ ] Diğer 3 stratejiyi de aynı yöntemle (HTF filter + sıkı + maker + hyperopt)
- [ ] Top 3 stratejiyi ensemble (her birinde 5-8 pair, çakışan sinyallere ağırlık)
- [ ] Paper trade 2 hafta
- [ ] Bybit canlı küçük sermayeyle ($50-100)

## 7. Önemli dersler

1. **Default params asla pozitif olmaz** — hyperopt şart
2. **Fee = scalping'in en büyük düşmanı** — maker-only + sıkı filtre şart
3. **In-sample backtest yanıltıcı** — out-of-sample test mutlaka yap
4. **Trade sayısı küçük (29) → istatistik az** — 200+ trade hedefle
5. **80%+ win rate küçük portföyde fragile** — geniş portföyde doğrula
6. **Cross-margin ≠ "agresif risk"** — sermaye verimliliği, leverage düşük tut (3x)
