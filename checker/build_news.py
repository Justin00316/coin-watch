"""Builds news.json: the latest Bitcoin and Ethereum headlines in English and Korean.

Run by GitHub every hour. Source: Google News search feeds (headline, publisher, link, time).
Only headlines and links are kept; the full articles stay on the publishers' sites.
"""
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEEDS = {
    "en": ("bitcoin OR ethereum OR crypto when:2d", "en-GB", "GB", "GB:en"),
    "ko": ("비트코인 OR 이더리움 OR 가상자산 when:2d", "ko", "KR", "KR:ko"),
}
PER_LANG = 15
# Established outlets only. Crypto news is full of paid adverts for risky tokens dressed up as articles,
# so headlines from other sites only fill in if the trusted list runs short, and never if they look promotional.
TRUSTED = {
    "en": ["reuters", "bloomberg", "cnbc", "financial times", "bbc", "the guardian", "wall street journal", "wsj",
           "associated press", "ap news", "forbes", "fortune", "yahoo finance", "barron", "marketwatch", "the economist",
           "coindesk", "cointelegraph", "the block", "decrypt", "bitcoin magazine", "dl news", "blockworks", "axios",
           "business insider", "the times", "the telegraph", "sky news", "investopedia", "kiplinger", "the motley fool"],
    "ko": ["연합뉴스", "연합인포맥스", "한국경제", "매일경제", "조선일보", "조선비즈", "중앙일보", "동아일보", "한겨레",
           "경향신문", "서울경제", "머니투데이", "이데일리", "뉴스1", "뉴시스", "아시아경제", "파이낸셜뉴스", "헤럴드경제",
           "디지털데일리", "전자신문", "zdnet", "지디넷", "kbs", "mbc", "sbs", "ytn", "jtbc", "블록미디어", "디센터",
           "토큰포스트", "블루밍비트", "코인데스크", "디지털애셋", "investing.com", "비즈니스포스트", "한국일보", "국민일보"],
}
PROMO = re.compile(r"presale|pre-sale|price prediction|prediction market|100x|1000x|meme ?coin|airdrop|next big|"
                   r"to buy now|best crypto|top crypto|explodes?|skyrocket|millionaire|프리세일|급등 예상|100배", re.I)


def fetch(lang):
    q, hl, gl, ceid = FEEDS[lang]
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": hl, "gl": gl, "ceid": ceid})
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CoinWatch/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return ET.fromstring(r.read())
        except Exception as e:  # noqa: BLE001
            print(f"  {lang} feed failed ({e}), try {i + 1}/3")
            time.sleep(5 * (i + 1))
    return None


def items(lang):
    root = fetch(lang)
    if root is None:
        return None
    out, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)].strip()
        key = re.sub(r"\W+", "", title.lower())[:60]
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            when = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:  # noqa: BLE001
            when = None
        out.append({"title": title, "source": source, "link": (it.findtext("link") or "").strip(), "time": when})
    out = [x for x in out if not PROMO.search(x["title"])]
    trusted = lambda x: any(n in x["source"].lower() for n in TRUSTED[lang])  # noqa: E731
    good = [x for x in out if trusted(x)]
    if len(good) < 8:
        good += [x for x in out if not trusted(x)][: 8 - len(good)]
    good.sort(key=lambda x: x["time"] or "", reverse=True)
    return good[:PER_LANG]


def main():
    path = ROOT / "news.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for lang in FEEDS:
        got = items(lang)
        data[lang] = got if got else old.get(lang, [])  # keep yesterday's list rather than show nothing
        print(f"{lang}: {len(data[lang])} headlines")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
