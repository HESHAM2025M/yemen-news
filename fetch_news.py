#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يجلب أخبار اليمن كل ساعة من RSS ويحفظها في data/news.json
يعمل على GitHub Actions مجاناً - لا يحتاج خادم مدفوع
المصادر: المشهد اليمني، يمن مونيتور، أخبار اليمن الآن، الصحوة نت، عدن 24، سما نيوز، نيوزيمن + الجزيرة والعربية وBBC عبر Google News
"""
import json, os, re, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError
import xml.etree.ElementTree as ET

SOURCES = [
    ("المشهد اليمني", "https://www.almashhad-alyemeni.com/rss.xml"),
    ("يمن مونيتور", "https://www.yemenmonitor.com/feed/"),
    ("أخبار اليمن الآن", "https://yemen-now.com/feed/"),
    ("الصحوة نت", "https://www.alsahwa-yemen.net/rss"),
    ("عدن 24", "https://aden24.net/feed/"),
    ("سما نيوز", "https://samanews.com/feed/"),
    ("نيوزيمن", "https://www.newsyemen.net/rss"),
    # تغطية عربية عبر Google News - موثوقة ولا تحجب RSS
    ("الجزيرة نت", "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%8A%D9%85%D9%86%20%D9%85%D9%88%D9%82%D8%B9:aljazeera.net&hl=ar&gl=EG&ceid=EG:ar"),
    ("العربية", "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%8A%D9%85%D9%86%20%D9%85%D9%88%D9%82%D8%B9:alarabiya.net&hl=ar&gl=EG&ceid=EG:ar"),
    ("أخبار اليمن - Google", "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=EG&ceid=EG:ar"),
]

def clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

def fetch_rss(name, url):
    print(f"Fetching {name}: {url}")
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 YemenNewsBot/1.0"})
        with urlopen(req, timeout=20) as r:
            data = r.read()
    except Exception as e:
        print(f"  failed: {e}")
        return []
    try:
        root = ET.fromstring(data)
    except Exception as e:
        print(f"  parse failed: {e}")
        return []
    items = []
    for it in root.iter("item"):
        title = clean(it.findtext("title"))
        link = (it.findtext("link") or "").strip()
        desc = clean(it.findtext("description"))
        pub = (it.findtext("pubDate") or "").strip()
        if title and link:
            items.append({
                "title": title,
                "link": link,
                "summary": desc[:300],
                "source": name,
                "published": pub,
            })
        if len(items) >= 20:
            break
    print(f"  got {len(items)}")
    return items

def main():
    all_items = []
    seen = set()
    for name, url in SOURCES:
        for it in fetch_rss(name, url):
            if it["link"] in seen:
                continue
            seen.add(it["link"])
            # تصنيف بسيط
            t = it["title"]
            if any(k in t for k in ["عاجل", "غارات", "قصف", "اشتباك", "هجوم"]):
                it["category"] = "عاجل"
            elif any(k in t for k in ["دولار", "صرف", "اقتصاد", "أسعار", "ريال"]):
                it["category"] = "اقتصاد"
            elif any(k in t for k in ["رياضة", "مباراة", "منتخب"]):
                it["category"] = "رياضة"
            else:
                it["category"] = "سياسة"
            all_items.append(it)
    os.makedirs("data", exist_ok=True)
    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_at_text": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(all_items),
        "sources": [s[0] for s in SOURCES],
        "articles": all_items[:150],
    }
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_items)} articles to data/news.json")

if __name__ == "__main__":
    main()
