"""Coin Watch cloud checker.

Runs on GitHub every 10 minutes. Reads alerts.json, fetches Bitcoin and Ethereum
prices, and sends a loud push alert through ntfy when an alert level is crossed.

Settings come from environment variables:
  NTFY_TOPIC  the private ntfy topic name (kept as a GitHub secret)
  APP_URL     the app's web address, so tapping the alert opens it
  SEND_TEST   "true" to send one test alert and stop
  DRY_RUN     "true" to print what would be sent without sending
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
APP_URL = os.environ.get("APP_URL", "").strip()
DRY = os.environ.get("DRY_RUN", "").lower() == "true"
NTFY = "https://ntfy.sh"

NAMES = {"bitcoin": {"en": "Bitcoin", "ko": "비트코인"}, "ethereum": {"en": "Ethereum", "ko": "이더리움"}}
SYMBOL = {"gbp": "£", "usd": "$", "krw": "₩"}


def get_json(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CoinWatch/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  fetch failed ({e}), try {i + 1}/{tries}: {url}")
            time.sleep(4 * (i + 1))
    return None


def money(v, cur):
    if cur == "krw":
        return f"₩{v:,.0f}"
    return f"{SYMBOL[cur]}{v:,.0f}" if v >= 1000 else f"{SYMBOL[cur]}{v:,.2f}"


def fetch_prices(currencies):
    """Returns {coin: {cur: price, cur_24h_change: pct}}. Falls back to Coinbase/Upbit if CoinGecko is down."""
    vs = ",".join(sorted(currencies))
    data = get_json(f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies={vs}&include_24hr_change=true")
    if data and "bitcoin" in data:
        return data
    print("CoinGecko unavailable, using backup sources (no 24h change data).")
    out = {"bitcoin": {}, "ethereum": {}}
    for coin, tick in (("bitcoin", "BTC"), ("ethereum", "ETH")):
        for cur in currencies:
            if cur == "krw":
                u = get_json(f"https://api.upbit.com/v1/ticker?markets=KRW-{tick}")
                if u:
                    out[coin]["krw"] = float(u[0]["trade_price"])
            else:
                c = get_json(f"https://api.coinbase.com/v2/prices/{tick}-{cur.upper()}/spot")
                if c:
                    out[coin][cur] = float(c["data"]["amount"])
    return out


def recent_titles(hours):
    """Titles already sent in the last few hours, so the same alert doesn't repeat every 10 minutes."""
    if not TOPIC:
        return set()
    url = f"{NTFY}/{TOPIC}/json?poll=1&since={int(hours * 3600)}s"
    titles = set()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CoinWatch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            for line in r.read().decode("utf-8").splitlines():
                if line.strip():
                    msg = json.loads(line)
                    if msg.get("event") == "message":
                        titles.add(msg.get("title", ""))
    except Exception as e:  # noqa: BLE001
        print(f"  couldn't read recent alerts ({e}); continuing")
    return titles


def send(title, body, priority=5):
    payload = {
        "topic": TOPIC,
        "title": title,
        "message": body,
        "priority": priority,
        "tags": ["rotating_light"],
    }
    if APP_URL:
        payload["click"] = APP_URL
        payload["actions"] = [{"action": "view", "label": "Open Coin Watch / 앱 열기", "url": APP_URL}]
    if DRY or not TOPIC:
        print("WOULD SEND:", json.dumps(payload, ensure_ascii=False))
        return
    req = urllib.request.Request(NTFY, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "User-Agent": "CoinWatch/1.0"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        print(f"  sent ({r.status}): {title}")


def words(alert, price, change, lang):
    coin = NAMES[alert["coin"]][lang]
    cur = alert.get("currency", "gbp")
    v = alert["value"]
    if alert["type"] == "below":
        title = f"{coin} {money(v, cur)} 아래로 하락" if lang == "ko" else f"{coin} fell below {money(v, cur)}"
    elif alert["type"] == "above":
        title = f"{coin} {money(v, cur)} 위로 상승" if lang == "ko" else f"{coin} rose above {money(v, cur)}"
    else:
        title = f"{coin} 24시간 {v}% 하락" if lang == "ko" else f"{coin} down {v}% in 24 hours"
    now = f"현재 {money(price, cur)}" if lang == "ko" else f"Now {money(price, cur)}"
    if change is not None:
        now += f" ({change:+.1f}% 24h)"
    return title, now


def main():
    cfg = json.loads((ROOT / "alerts.json").read_text(encoding="utf-8"))
    lang = cfg.get("language", "both")
    langs = ["ko", "en"] if lang == "both" else [lang]

    if os.environ.get("SEND_TEST", "").lower() == "true":
        title = " / ".join({"ko": "코인 워치 테스트 알림", "en": "Coin Watch test alert"}[l] for l in langs)
        body = "\n".join({"ko": "알림이 잘 작동합니다.", "en": "Alerts are working."}[l] for l in langs)
        send(title, body, priority=5)
        return

    alerts = [a for a in cfg.get("alerts", []) if a.get("on", True)]
    if not alerts:
        print("No alerts switched on.")
        return
    currencies = {a.get("currency", "gbp") for a in alerts}
    prices = fetch_prices(currencies)
    already = recent_titles(cfg.get("repeatHours", 6))

    for a in alerts:
        cur = a.get("currency", "gbp")
        p = prices.get(a["coin"], {}).get(cur)
        ch = prices.get(a["coin"], {}).get(f"{cur}_24h_change")
        if p is None:
            print(f"- {a['coin']} {a['type']} {a['value']}: no price, skipped")
            continue
        if a["type"] == "below":
            hit = p <= a["value"]
        elif a["type"] == "above":
            hit = p >= a["value"]
        elif a["type"] == "drop24h":
            hit = ch is not None and ch <= -a["value"]
        else:
            print(f"- unknown alert type {a['type']!r}, skipped")
            continue
        parts = [words(a, p, ch, l) for l in langs]
        title = " / ".join(t for t, _ in parts)
        body = "\n".join(n for _, n in parts)
        status = "HIT" if hit else "ok"
        print(f"- {a['coin']} {a['type']} {a['value']} {cur}: price {p:,.2f} change {ch if ch is None else round(ch, 2)} -> {status}")
        if hit and title not in already:
            send(title, body)
        elif hit:
            print("  already alerted recently, not repeating yet")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("Checker failed:", e)
        sys.exit(1)
