"""
Bybit'in top USDT-perp sembollerini al, freqtrade pair listesi olarak yaz.

Bybit cloud container'a kapalı (CloudFront geo-blok) → fallback olarak
CoinGecko'dan top 100 marketcap çekip BTC/USDT, ETH/USDT vb. formatına çevirir.
Bybit'te listed olmayan birkaç tanesi pair download sırasında otomatik filtrelenir.

Lokalde Bybit açıksa, USE_BYBIT=true ile direkt Bybit'ten alınır.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
import urllib.error


# Stablecoin'leri ve sarmal token'ları (perp olarak işlem görmez) atla
SKIP = {
    "USDT", "USDC", "DAI", "TUSD", "BUSD", "FDUSD", "USDE", "PYUSD", "USDS",
    "WBTC", "WETH", "STETH", "WSTETH", "WEETH", "RETH", "CBETH", "WBETH",
    "WBNB", "BSC-USD", "WMATIC", "WTRX", "WSOL", "JITOSOL", "BGB",
    # genelde Bybit'te USDT-perp'i olmayan veya likiditesi çok düşük olanlar
    "LEO", "OKB", "MNT", "GT", "KCS", "HT", "FTT",
}

# CoinGecko ID → Bybit base symbol map (CoinGecko adı farklıysa)
SYMBOL_OVERRIDE = {
    "matic-network": "MATIC",
    "polygon-ecosystem-token": "POL",
    "the-open-network": "TON",
    "bittensor": "TAO",
    "hyperliquid": "HYPE",
    "first-digital-usd": None,  # stablecoin
    "ondo-finance": "ONDO",
    "internet-computer": "ICP",
    "official-trump": "TRUMP",
    "ethena": "ENA",
    "fartcoin": "FARTCOIN",
}


def _coingecko_top(limit: int = 150) -> list[dict]:
    """CoinGecko top N by market cap. Stablecoin filtresi sonradan."""
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&order=market_cap_desc&per_page={limit}"
        "&page=1&sparkline=false"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "freqtrade-pairlist"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def _bybit_perps() -> set[str]:
    """Bybit canlı USDT-perp sembol listesi (base symbol set, örn {'BTC','ETH',...})."""
    try:
        req = urllib.request.Request(
            "https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        out = set()
        for item in data.get("result", {}).get("list", []):
            sym = item.get("symbol", "")
            quote = item.get("quoteCoin", "")
            base = item.get("baseCoin", "")
            status = item.get("status", "")
            if quote == "USDT" and status == "Trading" and base:
                out.add(base)
        return out
    except Exception as e:
        print(f"[uyari] Bybit instrument list cekilemedi: {e}", file=sys.stderr)
        return set()


def build(n: int = 100) -> list[str]:
    """Top n adet işlem yapılabilir USDT-perp pair listesi: ['BTC/USDT:USDT', ...]."""
    coins = _coingecko_top(limit=n * 2)  # filtreleme sonrası n kalmasın diye geniş çek
    bybit_set = _bybit_perps()  # cloud'da boş set döner — fallback'te kullanmıyoruz

    pairs = []
    for c in coins:
        cid = c.get("id", "")
        sym = (c.get("symbol") or "").upper()
        # override
        if cid in SYMBOL_OVERRIDE:
            mapped = SYMBOL_OVERRIDE[cid]
            if mapped is None:
                continue
            sym = mapped
        if not sym or sym in SKIP:
            continue
        # Bybit listesi varsa filtre uygula
        if bybit_set and sym not in bybit_set:
            continue
        pair = f"{sym}/USDT:USDT"  # ccxt linear perpetual format
        if pair not in pairs:
            pairs.append(pair)
        if len(pairs) >= n:
            break
    return pairs


def main():
    n = int(os.environ.get("PAIRS_N", "100"))
    pairs = build(n=n)
    out_path = os.environ.get("OUT", "user_data/pairlist_top100.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(pairs, f, indent=2)
    print(f"OK {len(pairs)} pair → {out_path}")
    for p in pairs[:20]:
        print(f"  {p}")
    if len(pairs) > 20:
        print(f"  ... ({len(pairs) - 20} more)")


if __name__ == "__main__":
    main()
