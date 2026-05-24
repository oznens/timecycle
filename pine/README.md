# TradingView — Time Cycles İndikatörü

Pine Script v6 ile yazılmış, doğrudan TradingView grafiğine entegre. Bybit/Binance/Coinbase ne kullandığın fark etmez — TV verisini kullanır, geo-blok yok.

## Kurulum

1. TradingView'da istediğin grafiği aç (örn. `BYBIT:BTCUSDT`, TF `1D` veya `4H`).
2. Alt panelde **Pine Editor** sekmesini aç (yoksa: alt menüdeki "+" → "Pine Editor").
3. `time_cycles.pine` dosyasının içeriğini kopyala-yapıştır.
4. Sağ üstte **Save** (Adı: ör. "Time Cycles") → **Add to chart**.
5. Grafiğin üstünde indikatörün adının yanındaki dişli (⚙) ikonuyla ayarları aç.

## Ayarlar

### 1️⃣ Seed Pivot Dipleri
- **Dip A (sol)** — büyük geçmiş dip. Grafikte sağ tıkla → bir tarih seç, kopyala.
- **Dip B (sağ)** — daha yeni büyük dip. **Parent döngü = B − A**.
- Birinci kez ekledikten sonra, ayar penceresinden ya da grafikte dikey çizgileri sürükleyerek değiştirebilirsin.

### 2️⃣ Döngü
- **Otomatik en iyi bölmeyi seç** ✓ → "Aday bölmeler" listesindeki her oran için hit-rate hesaplanır, en yüksek olan kullanılır.
- **Aday bölmeler** — varsayılan `1,2,3,4,5` (sırayla parent döngünün kendisi, 2'ye, 3'e, 4'e, 5'e bölünmüş hali).
- **Manuel bölme oranı** — otomatik kapalıyken kullanılır.
- **Tolerans penceresi (%)** — kitabın varsayılanı **%10**. Dar fakat aksiyon alınabilir.
- **İleri projeksiyon** — geleceğe kaç alt döngü çizilsin (varsayılan 8).

### 3️⃣ Pivot Tespiti
- **Pivot left / right** — Williams swing-low parametreleri. Büyütünce daha az ama daha güvenilir pivot.
- Varsayılan `10/10` günlük grafik için iyi; 1H için `20/20`, 1W için `4/4` deneyebilirsin.

### 4️⃣ Görsel
- **Ana renk** — en iyi döngü (sarı varsayılan, kitap tarzı).
- **Alt renk** — 2. en iyi döngü karşılaştırma için (mor).
- **Tolerans pencereleri** — dart-tahtası 5/10/15% katmanları (iç en koyu).
- **Yarım daire eğriler** — kitabın "just 2 clicks" görselinin Pine eşdeğeri (curved polyline).

## Grafiği okuma

- 🟨 **Sarı dikey kutular** — pivot etrafında 5/10/15% pencereler. İç (koyu) = yüksek güven bölgesi.
- ⏱ **Üst orta etiket** — `Sub=X Alt≈Yg Hit=Z% Tol±Wg` — dominant döngünün özeti.
- ▼ **Gri üçgenler** — tespit edilen tüm anlamlı dipler.
- 🅰️ / 🅱️ **A / B etiketleri** — seçtiğin seed pivotlar.
- 🌀 **Yarım daire eğriler** — her projeksiyon pivotunun döngü temsili.

**Yorum kuralı (kitaptan):**
- Hit-rate **≥ %80** → döngü geçerli ve aktif kullanılabilir.
- Hit-rate **%60-80** → eldeki seçenekler arasında en iyisi ama daha iyi seed dipleri arayabilirsin.
- Hit-rate **< %60** → yanlış seed dipleri / yanlış asset için döngü zayıf — başka pivot çiftini dene.

## Tipik iş akışı

1. **Macro plan** — `1W` veya `1D` üzerinde iki büyük dip seç (örn. BTC 2018-12 → 2022-11). Otomatik bölme genelde 1 veya 4 verecek (~halving). Bu macro pencereler aylık planlama içindir.
2. **Swing plan** — `1D` üzerinde son iki orta-büyüklük dip (örn. 2024-08-05 → 2025-04-07). Sub = 2-4 → 30-90 günlük alt döngüler.
3. **Scalp plan** — `1H` veya `4H` üzerinde son iki belirgin dip. Sub = 1 veya 2.

Aynı grafiğe **iki kez ekleyip** farklı seed çiftleri verirsen, macro + swing pencereleri **üst üste** binen yerleri görürsün — **commonality** sinyali = en güçlü giriş anı.

## Sınırlamalar

- Pine Script bir indikatör; otomatik tarama (100+ sembol) yapamaz — onun için Python tarafındaki `pages/1_Tarayici.py` var.
- TV'nin loop limitleri var — çok küçük `sub` (örn. parent=10y, sub=10 → 1y alt) ve çok sık pivot çiftleri tarama yavaşlatabilir.
- TV ücretsiz planında özel indikatör chart sayısı sınırlı (Premium için sınırsız).

## Sonraki adımlar (eklemek istersen)

- VTL (Valid Trend Line) tetik
- Momentum onayı (EMA 20/50 + ATR)
- Strategy versiyonu (backtest için)
- Alert: "bugün pivot penceresine girdik" bildirimi
