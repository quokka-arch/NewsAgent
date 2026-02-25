from __future__ import annotations

RSS_FEEDS = {
    # ── Tier 1: 通讯社 / 最稳定权威 ────────────────────────────
    "AP News":          "https://feeds.apnews.com/rss/apf-topnews",
    "BBC World":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    # ── Tier 2: 国际公共广播 ────────────────────────────────────
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "VOA News":         "https://feeds.voanews.com/rss/english/world",
    "DW English":       "https://rss.dw.com/rdf/rss-en-world",
    "France24":         "https://www.france24.com/en/rss",
    "NHK World":        "https://www3.nhk.or.jp/rss/news/cat6.xml",
    # ── Tier 3: 商业媒体 / 分析深度强 ──────────────────────────
    "The Guardian":     "https://www.theguardian.com/world/rss",
    "NYTimes World":    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    # ── Tier 4: 官方机构 / 外交/人道主义视角 ───────────────────
    "UN News":          "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    # ── Tier 5: Google News 关键词聚合（覆盖中小媒体长尾内容）────
    # 话题订阅：Google News 世界新闻板块（来源多元，含 AP/Reuters 等）
    "GNews World":      "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
    # 关键词订阅：精准命中地缘政治核心事件（可按需修改 q= 参数）
    "GNews Geopolitics": "https://news.google.com/rss/search?q=war+diplomacy+sanctions+military&hl=en-US&gl=US&ceid=US:en",
    # ── 已停用（保留注释供参考）──────────────────────────────────
    # "Reuters World":  "https://feeds.reuters.com/Reuters/worldNews",  # 免费RSS已关闭
    # "Yahoo News":     "https://news.yahoo.com/rss/world",             # 仅5条且内容为娱乐聚合，不适用
}

POLITICAL_KEYWORDS = {
    "election",
    "government",
    "parliament",
    "president",
    "prime minister",
    "diplomacy",
    "sanction",
    "ceasefire",
    "conflict",
    "war",
    "military",
    "nato",
    "un",
    "china",
    "us",
    "usa",
    "russia",
    "ukraine",
    "middle east",
    "gaza",
    "israel",
    "iran",
    "taiwan",
    "south china sea",
    "tariff",
    "summit",
    "security",
    "coup",
    "protest",
    "policy",
    "外交",
    "制裁",
    "冲突",
    "战争",
    "总统",
    "总理",
    "议会",
}

RISK_KEYWORDS = {
    "high": {
        "war",
        "missile",
        "invasion",
        "nuclear",
        "airstrike",
        "sanction",
        "military",
        "attack",
        "conflict",
        "blockade",
        "escalation",
        "coup",
        "hostage",
    },
    "medium": {
        "protest",
        "tension",
        "tariff",
        "diplomatic",
        "negotiation",
        "ceasefire",
        "summit",
        "election",
        "policy",
    },
}

COUNTRY_ALIASES = {
    "United States": {"us", "u.s.", "usa", "united states", "america"},
    "China": {"china", "beijing", "chinese"},
    "Russia": {"russia", "moscow", "russian"},
    "Ukraine": {"ukraine", "kyiv", "kiev"},
    "Israel": {"israel", "israeli"},
    "Palestine": {"palestine", "gaza", "west bank"},
    "Iran": {"iran", "tehran", "iranian"},
    "United Kingdom": {"uk", "britain", "united kingdom", "london"},
    "France": {"france", "paris", "french"},
    "Germany": {"germany", "berlin", "german"},
    "Japan": {"japan", "tokyo", "japanese"},
    "South Korea": {"south korea", "seoul", "korean"},
    "India": {"india", "new delhi", "indian"},
    "Taiwan": {"taiwan", "taipei"},
}

COUNTRY_ZH: dict[str, str] = {
    "United States": "美国",
    "China": "中国",
    "Russia": "俄罗斯",
    "Ukraine": "乌克兰",
    "Israel": "以色列",
    "Palestine": "巴勒斯坦",
    "Iran": "伊朗",
    "United Kingdom": "英国",
    "France": "法国",
    "Germany": "德国",
    "Japan": "日本",
    "South Korea": "韩国",
    "India": "印度",
    "Taiwan": "台湾",
}

TOPIC_ZH: dict[str, str] = {
    "Military Conflict": "军事冲突",
    "Diplomacy": "外交",
    "Sanctions & Trade": "制裁与贸易",
    "Domestic Politics": "国内政治",
    "Civil Unrest": "社会动荡",
}

RISK_ZH: dict[str, str] = {
    "HIGH": "高风险",
    "MEDIUM": "中风险",
    "LOW": "低风险",
}

TOPIC_KEYWORDS = {
    "Military Conflict": {"war", "military", "missile", "airstrike", "attack", "invasion"},
    "Diplomacy": {"summit", "diplomatic", "talks", "negotiation", "ceasefire", "un"},
    "Sanctions & Trade": {"sanction", "tariff", "trade", "export", "embargo"},
    "Domestic Politics": {"election", "parliament", "government", "president", "prime minister"},
    "Civil Unrest": {"protest", "riot", "strike", "demonstration", "coup"},
}
