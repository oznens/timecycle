# Kullanım Kılavuzu — Time Cycle Analizi

İki kullanım yolu var:

| Yol | Ne için iyi | Setup |
|---|---|---|
| **TradingView İndikatörü** (`pine/`) | Bybit/Binance verisini doğrudan TV'de canlı görmek, anında parametre denemek, geo-blok yok | Tek tık — Pine Editor'a yapıştır |
| **Python + Streamlit** (bu proje) | Çoklu sembol tarama, backtest, otomasyon, alarm | Lokalde `pip install` + `streamlit run` |

## TradingView (önerilen — en hızlı yol)

Detaylı: [`pine/README.md`](pine/README.md)

Kısa özet:
1. TradingView'da `BYBIT:BTCUSDT` (veya istediğin sembol) aç, TF seç (`1D`, `4H` vb.)
2. Alt panel → **Pine Editor**
3. `pine/time_cycles.pine` içeriğini kopyala-yapıştır → **Save** → **Add to chart**
4. ⚙ Settings → iki dip tarihini gir (örn. son macro dip ve önceki büyük dip)
5. Otomatik en iyi bölme + 5/10/15% dart-board pencereleri + yarım daire döngüler çizilir

## Hızlı başlangıç (lokal makinen — Python tarafı)

```bash
# 1) Repoyu çek (designated branch)
git clone -b claude/inspiring-goldberg-iUjyt https://github.com/oznens/timecycle.git
cd timecycle

# 2) Sanal ortam (zorunlu değil ama önerilir)
python3 -m venv .venv
source .venv/bin/activate          # Mac/Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows cmd:        .venv\Scripts\activate.bat

# 3) Bağımlılıklar
pip install -r requirements.txt

# 4) Uygulamayı başlat
streamlit run app.py
```

Tarayıcı otomatik açılır: `http://localhost:8501`

> **Python 3.10+** gerekli. Windows'ta `python3` yerine `python` kullan.

---

## Bybit ile kullanım (senin senaryon)

Sidebar'dan:

| Ayar | Değer |
|---|---|
| **Veri kaynağı** | `bybit` |
| **Sembol** | `BTC/USDT` (ccxt formatı: `COIN/USDT`) |
| **Mum aralığı (TF)** | `15m` / `30m` / `1h` / `2h` / `4h` / `12h` / `1d` / `1wk` / `1mo` |
| **Geçmiş periyot** | TF'ye göre otomatik liste gelir |
| **Tolerans %** | 10 (varsayılan — kitabın önerisi) |

Örnek:
- ETH 4 saatlik → Sembol `ETH/USDT`, TF `4h`, Periyot `1y`
- BTC günlük macro → Sembol `BTC/USDT`, TF `1d`, Periyot `5y` veya `10y`
- SOL 1-saatlik kısa vadeli → Sembol `SOL/USDT`, TF `1h`, Periyot `6mo`

### "İki dip"i seçme
- "Otomatik en güçlü 2 dipten döngü kur" işaretliyse → sistem en güçlü dipleri kendi seçer
- Manuel seçim için bu kutuyu kapat, **Dip A** ve **Dip B**'yi açılır menülerden seç
- Skor tablosunda hangi **bölme (1/2/3/4)** en yüksek hit-rate veriyorsa o dominant ritim olarak işaretlenir

### Grafiği okuma
- 🟨 Sarı dikey kutular = **dart tahtası zaman pencereleri** (en koyu içte = ±%5, dış = ±%15)
- ⭐ Sarı yıldız = pencerede vurulan gerçek dip
- ✖ Gri X = tüm anlamlı dipler
- **Alt panel** = yarım daire döngüler (kitabın "just 2 clicks" aracının analogu)
- Üstte fiyat **log skala** (toggle ile linear)

---

## Tarayıcı sayfası

Sol menüden **Tarayıcı**'yı aç. 47 popüler kripto için aynı anda:
- Otomatik döngü kurulur
- Hit-rate ≥ %60 olanlar listelenir
- "Sadece şu an pencerede olanlar" filtresi → bugün **giriş fırsatı** olanları gösterir
- Sıralama bugüne yakınlığa göre

İstediğin sembolleri text-area'ya ekleyebilirsin.

---

## Anthropic web ortamında

Cloud container'da **Bybit/Binance CloudFront geo-blok** verir (`HTTP 403/451`).
- Bu ortamda: `yfinance` (sembol formatı `BTC-USD`), `kraken`, `coinbase` kullan
- Lokalde: `bybit`, `binance` sorunsuz

---

## Sık karşılaşılan hatalar

| Hata | Çözüm |
|---|---|
| `streamlit: command not found` | `pip install -r requirements.txt` çalıştığını kontrol et, virtualenv aktif mi? |
| `ccxt: NetworkError` | İnternet/proxy/VPN; Bybit erişimi açık mı kontrol et |
| `yfinance: Possibly delisted` | Sembol formatı yanlış — Yahoo için `BTC-USD`, ccxt için `BTC/USDT` |
| Grafik boş | TF için periyot çok kısa, daha uzun periyot seç |
| `yeterli güçlü dip yok` | Sidebar'da **Belirginlik**'i düşür veya **Min dip aralığı**'nı düşür |
| Hit-rate düşük (<%60) | Farklı seed dipleri dene, veya daha uzun periyotla bak |

---

## Mimari — neresi neyi yapar

```
src/
  data.py        # OHLC çekme (yfinance + ccxt: bybit/binance/kraken/coinbase)
  pivots.py      # Anlamlı dip tespiti (scipy find_peaks + Williams fractal)
  cycle.py       # Cycle modeli: 2 seed + subdivision → projeksiyon + pencere
  dominance.py   # Hit-rate skorlama + best_subdivision (1,2,3,4 oranlar)
  chart.py       # Plotly mum + dart-board pencereleri + yarım daireler
  scanner.py     # Çoklu sembol paralel tarama + auto-seed seçimi
app.py           # Tek sembol analizi (ana sayfa)
pages/
  1_Tarayici.py  # Çoklu sembol tarayıcı
kaynak/          # Kaynak PDF (Mr. Abundance kitabı, 7 parça)
YONTEM.md        # Yöntem özeti (Türkçe)
```
