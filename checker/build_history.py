"""Builds history.json: daily US-dollar closing prices for Bitcoin (from 2010) and Ethereum (from 2016).

Run by GitHub once a day. Sources: Blockchain.com (Bitcoin) and Coinbase Exchange (Ethereum).
"""
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "CoinWatch/1.0", "Accept": "application/json"}


def get_json(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  fetch failed ({e}), try {i + 1}/{tries}")
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"Could not fetch {url}")


def bitcoin():
    d = get_json("https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false")
    return [[int(v["x"]) // 86400, round(float(v["y"]), 2)] for v in d["values"] if v["y"] > 0]


def ethereum():
    start = datetime(2016, 5, 18, tzinfo=timezone.utc)
    end = datetime.now(timezone.utc)
    rows = {}
    while start < end:
        stop = min(start + timedelta(days=299), end)
        url = ("https://api.exchange.coinbase.com/products/ETH-USD/candles?granularity=86400"
               f"&start={start:%Y-%m-%dT%H:%M:%SZ}&end={stop:%Y-%m-%dT%H:%M:%SZ}")
        for c in get_json(url):  # [time, low, high, open, close, volume]
            rows[int(c[0]) // 86400] = round(float(c[4]), 2)
        start = stop
        time.sleep(0.6)
    return [[d, rows[d]] for d in sorted(rows)]


def main():
    out = {
        "_about": "Daily closing prices in US dollars. Each row is [days since 1 Jan 1970, price].",
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "bitcoin": bitcoin(),
        "ethereum": ethereum(),
    }
    (ROOT / "history.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"history.json: {len(out['bitcoin'])} Bitcoin days, {len(out['ethereum'])} Ethereum days")


if __name__ == "__main__":
    main()
