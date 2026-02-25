import feedparser

feeds = [
    ("AP News",           "https://feeds.apnews.com/rss/apf-topnews"),
    ("BBC World",         "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera",        "https://www.aljazeera.com/xml/rss/all.xml"),
    ("VOA News",          "https://feeds.voanews.com/rss/english/world"),
    ("DW English",        "https://rss.dw.com/rdf/rss-en-world"),
    ("France24",          "https://www.france24.com/en/rss"),
    ("NHK World",         "https://www3.nhk.or.jp/rss/news/cat6.xml"),
    ("The Guardian",      "https://www.theguardian.com/world/rss"),
    ("NYTimes World",     "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("UN News",           "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("GNews World",       "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"),
    ("GNews Geopolitics", "https://news.google.com/rss/search?q=war+diplomacy+sanctions+military&hl=en-US&gl=US&ceid=US:en"),
]

print(f"{'状态':<5} {'来源':<22} {'HTTP':>5} {'条目':>5}  示例标题")
print("-" * 90)
for name, url in feeds:
    d = feedparser.parse(url)
    n = len(d.entries)
    s = d.get("status", 0)
    ok = "✅ OK" if n > 0 else "❌ --"
    sample = d.entries[0].title[:42] if n else "(none)"
    print(f"{ok:<5} {name:<22} {str(s):>5} {n:>5}  {sample}")
