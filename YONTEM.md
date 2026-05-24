# Zaman Döngü (Time Cycles) Yöntemi — Mr. Abundance / J.M. Hurst

Bu doküman, `kaynak/` klasöründeki "Beginner's Guide to Time Cycles" PDF'inden (136 sayfa, 7 parça) çıkarılan yöntemin özetidir. Otomasyon sistemi bu modele dayanacak.

---

## 1. Temel Fikir

Piyasalar rastgele hareket etmez — **iç içe geçmiş zaman ritimlerinde** hareket eder.
- Her döngünün bir **uzunluğu** vardır (20 gün, 80 gün, 20 hafta vb.)
- Küçük döngüler büyük döngülerin içine **yuvalanır** (Russian doll mantığı)
- Döngüler aynı anda dip yaptığında (**senkronizasyon**) büyük dönüş noktaları oluşur

Slogan: **Fiyat "nerede"yi söyler, zaman "ne zaman"ı söyler.**

---

## 2. Hurst'ün 8 İlkesi

| # | İlke | Anlamı |
|---|------|--------|
| 1 | Commonality (Ortaklık) | Benzer enstrümanlar benzer hareket eder |
| 2 | Cyclicality (Döngüsellik) | Hareket rastgele değil, döngüseldir |
| 3 | Summation (Toplama) | Döngüler basit toplamayla birleşir |
| 4 | Harmonicity (Harmonik) | Döngü uzunlukları basit oranlarla (2x, 3x) bağlıdır |
| 5 | Synchronicity (Senkronizasyon) | Mümkün olduğunda dipler aynı anda oluşur |
| 6 | Proportionality (Orantılılık) | Genlik ↔ dalga boyu orantılıdır |
| 7 | Nominality (Nominallik) | Ortak nominal döngü uzunlukları vardır |
| 8 | Variation (Sapma) | Her şey ± tolerans bandı içinde; ideal tarih yerine **zaman penceresi** |

---

## 3. Nominal Döngü Uzunlukları (Hurst Tablosu)

| Nominal Döngü | Ort. Uzunluk (Takvim Günü) | Tolerans (± gün) |
|---|---|---|
| 18-Yıl | 6.570 | ± 328 |
| 9-Yıl | 3.285 | ± 164 |
| 54-Ay | 1.095 | ± 55 |
| 27-Ay | 822 | ± 41 |
| 18-Ay | 540 | ± 27 |
| 9-Ay | 270 | ± 13 |
| **20-Hafta** | **140** | **± 14** |
| **80-Gün** | **80** | **± 8** |
| 40-Gün | 40 | ± 4 |
| 20-Gün | 20 | ± 2 |
| 10-Gün | 10 | ± 1 |
| 5-Gün | 5 | ± 0.5 |

**Tolerans Formülü:** Pencere ≈ döngü uzunluğunun **%10**'u (varsayılan). Uzun döngülerde %5'e daraltılabilir, kritik durumlarda %15'e açılabilir.

---

## 4. Zaman Penceresi (Bullseye / Dart Tahtası)

Her ideal pivot tarihi etrafında 3 katmanlı bir hedef oluşur:
- **%5 (sarı çekirdek)** — en yüksek güven
- **%10 (turuncu)** — standart geçerli pencere
- **%15 (kırmızı dış halka)** — son izin verilen sapma

Bir pivot %15'in dışında oluşursa veya pencere içinde anlamlı bir dip/breakout yoksa **döngü geçersizdir (invalid)**. Üst üste 2 invalid pivot → döngüleri yeniden çiz.

---

## 5. Döngü Haritalama (Mapping by Symmetry)

**"Just 2 clicks"** yaklaşımı:
1. **Log mod**a geç (yüksek volatilitede şart).
2. **İki büyük dip** seç (HTF — aylık/yıllık).
3. Time Cycle aracıyla bağla → yarım daireler oluşur.
4. **2'ye böl** (harmonik 2) → alt döngüleri kontrol et.
5. Uymuyorsa **3'e böl** (harmonik 3) dene.
6. Hangi oran (2 vs 3 vs nadiren 5) en çok dibi yakalıyorsa **dominant ritim** odur.
7. Tekrar 2'ye veya 3'e bölerek aşağı timeframe'lere in.
8. **20 gün altına inme** — düşük TF'de döngüler dağılır.

### Görsel İpucu
- **M-şekli** yapı = döngüler birleşirken oluşan tipik fiyat formu
- **W-şekli** dipler = senkronize trough'lar
- Wick'leri **görmezden gelmek** OK — ana ritim önemli, "pico-dip" değil

---

## 6. Dominant Ritim ≠ En Büyük Dip

**Anahtar prensip:** Asıl döngüyü en büyük wick'e değil, **en çok dibi yakalayan ritime** göre çiz. Buna "stealth time cycles" denebilir; breakout öncesi son dipler de referans noktası olabilir.

**Volkan analojisi:** Büyük döngüler "uyuyan volkan" gibidir — büyüklerine saygı duy ama günlük hayat yan koniler (dominant alt döngü) etrafında döner.

**Tren analojisi:** Bir pivot erken veya geç olabilir; bir sonraki birkaç pivot da kayar ama eninde sonunda "tarifeye" döner. (Mean reversion of rhythm.)

---

## 7. İşlem Sinyalleri

### Long (Alış)
- Fiyat zaman penceresine düşerken, **VTL** (Valid Trend Line — son iki aynı-derece dipten geçen trend) yukarı yönlü kırıldığında tetik
- Minimum hedef = **1:1 risk/ödül** (zayıflık işareti < 1:1)
- Genişletme hedefleri: **Fib 1.0, 1.382, 1.618, 2.272**

### Short (Satış)
- Pivot penceresinin sonuna yaklaşırken, dipleri birleştiren VTL **aşağı kırılınca** tetik
- Stop = son tepe; hedef = 1:1 minimum

### Confluence (Birleşim) Kontrol Listesi
1. **Zaman**: pivot penceresinde miyiz?
2. **Yapı**: Wyckoff M1/M2, 3-drive, range low?
3. **Momentum**: 20/50 EMA çaprazı + yükselen ATR + hacim?
4. **Oran (Ratio)**: ilgili çapraz oranlar talep bölgesinde mi?
5. **Commonality**: Korelasyondaki diğer varlıklarda pivot var mı?

---

## 8. Momentum Checklist (Long onay)

- ✅ Pivot 3+ aylık range oluşturmuş
- ✅ Range'den breakout yapısı
- ✅ **20 EMA > 50 EMA** çapraz + sapma
- ✅ **ATR** yukarı kıvrılıyor
- ✅ Spot/perp talep + hacim artıyor
- ✅ Alt/ETH oranı talepte

→ 5 üzerinden skorla; 3+ ideal long.

---

## 9. Oran Analizi (Ratio Analysis) — Market Maker Gözüyle

Tek bir varlık (USD bazında) bakmak yerine **oran sor**:
- "Para nereye dönüyor?"
- "Bu hareket gerçek mi yoksa USD zayıflığı mı?"

### 4 Oran Yasası
1. **Aynı büyüklük sınıfı** (Top 3 metal vs Top 3 madenci)
2. **Aynı statü** (Silver = #2 metal, ETH = #2 crypto)
3. **Berraklık** — net trend, range, 3-drive yoksa AT
4. **Yedek hazırla** — bir oran tıkanırsa, benzerine geç

### Kritik Oranlar (özet)
- **TIP/BTC** — likidite rotasyonu, BTC zirve sinyali
- **HYG/LQD** — risk iştahı (junk vs investment-grade bond)
- **IPO/BND** — spekülasyon barometresi
- **ARKK/VIX** — innovation vs fear
- **USDT.D − USDC.D** — kripto offshore retail vs kurumsal
- **XAU/XL[K,F,E,V,Y,P,I,RE,U,C,B]** — 11 S&P sektörü altın bazında
- **HUI/VT** — küresel likidite sıkıntısı
- **BTC/SPX**, **BTC/QQQ**, **BTC/GOLD** — BTC için "gerçek güç"

---

## 10. Backtest ile İstatistik Çıkarma

Bir döngü tanımlandıktan sonra geriye dönük olarak:
- **A.** Pivot'tan ortalama % yükseliş
- **B.** Pivot → lokal tepe arası ortalama gün sayısı
- **C.** Düzeltme fib seviyesi (genellikle **0.382**)

Bu istatistikler **TP1/TP2/TP3** planını otomatikleştirir (örnek DOGE: +8% min 1/10, +20% standart 9/10 ~6 gün).

---

## 11. Geçersizleştirme Kuralları

- Pivot %15 penceresinin **dışında** ve hiçbir higher-low/breakout %15 içinde yoksa → **invalid**
- Üst üste **2 invalid** → döngüleri yeniden çiz
- Yine de "ghost" pivot ekleyerek alternatif ritmi izle

---

## 12. Otomasyon İçin Çıkarılan Bileşenler

Aşağıdaki tüm adımlar kodla otomatikleştirilebilir:

| Modül | Girdi | Çıktı |
|---|---|---|
| **PivotDetector** | OHLC verisi | Tarihsel anlamlı dipler (zigzag/fractal) |
| **CycleFitter** | İki seed dip + bölme oranı | Projected pivot listesi |
| **WindowCalculator** | Pivot tarihleri + döngü uzunluğu | %5/%10/%15 pencereleri |
| **DominanceScorer** | Aday döngüler + gerçek dipler | Hit-rate (en çok dibi yakalayan kazanır) |
| **VTLBuilder** | Aynı derece ardışık 2 dip | Trend çizgisi + kırılma sinyali |
| **MomentumScorer** | EMA20, EMA50, ATR, Volume | 0-5 momentum skoru |
| **RatioEngine** | Çapraz fiyat serileri | Oran serisi + Wyckoff yapı tespit |
| **ConfluenceScanner** | Yukarıdakilerin hepsi | Tarih × Varlık matrisi: long/short fırsatları |
| **Backtester** | Geçmiş pivotlar + entry kuralları | TP istatistikleri (avg %, avg gün, fib retrace) |
| **Alerts** | Aktif pencereler + tetik koşulları | Bildirim |

---

## 13. Mantra'lar

> "Don't look for perfect time cycles, look for **dominant** time cycles."

> "If you can see the rhythm, you can ride the wave."

> "Cycles give **when**, price gives **where**. Edge = structure + high probability zones, not prediction."

> "Price is the sea. Time is the tide."
