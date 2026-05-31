from __future__ import annotations

import math
import re
from dataclasses import dataclass


POSITIVE_TERMS = {
    "love", "great", "excellent", "reliable", "fast", "secure", "helpful",
    "transparent", "recommend", "improved", "trusted", "thanks", "resolved",
    "喜欢", "优秀", "可靠", "快速", "安全", "有用", "推荐", "改进", "信任", "感谢", "解决",
}

NEGATIVE_TERMS = {
    "bad", "broken", "angry", "hate", "scam", "unsafe", "leak", "fraud",
    "boycott", "complaint", "lawsuit", "crash", "down", "slow", "expensive",
    "糟糕", "生气", "讨厌", "骗局", "不安全", "泄露", "欺诈", "抵制", "投诉", "诉讼",
    "崩溃", "宕机", "缓慢", "昂贵", "失望",
}

URGENT_TERMS = {
    "urgent", "breaking", "viral", "trending", "investigation", "regulator",
    "media", "press", "security incident", "data breach", "class action",
    "紧急", "爆料", "热搜", "媒体", "记者", "监管", "调查", "数据泄露", "安全事故", "集体诉讼",
}


@dataclass(frozen=True)
class Analysis:
    sentiment: float
    risk_score: int
    risk_level: str
    strategy: str
    rationale: str


def tokenize(text: str) -> list[str]:
    text = text.lower()
    english = re.findall(r"[a-z][a-z0-9\-']+", text)
    chinese_hits = []
    for term in POSITIVE_TERMS | NEGATIVE_TERMS | URGENT_TERMS:
        if any("\u4e00" <= char <= "\u9fff" for char in term) and term in text:
            chinese_hits.append(term)
    return english + chinese_hits


def analyze(text: str, aliases: list[str] | None = None, reach: int = 1, source_weight: float = 1.0) -> Analysis:
    tokens = tokenize(text)
    lowered = text.lower()
    aliases = aliases or []

    positive = sum(1 for token in tokens if token in POSITIVE_TERMS)
    negative = sum(1 for token in tokens if token in NEGATIVE_TERMS)
    urgent = sum(1 for term in URGENT_TERMS if term in lowered)
    alias_hits = sum(1 for alias in aliases if alias and alias.lower() in lowered)

    total = positive + negative
    sentiment = 0.0 if total == 0 else round((positive - negative) / total, 3)

    reach_factor = min(24, int(math.log10(max(reach, 1)) * 8))
    negative_factor = max(0, int((0 - sentiment) * 40))
    urgency_factor = min(30, urgent * 10)
    entity_factor = min(10, alias_hits * 3)
    source_factor = int(max(source_weight, 0.5) * 8)

    risk_score = max(0, min(100, negative_factor + urgency_factor + reach_factor + entity_factor + source_factor))
    level = risk_level(risk_score)
    strategy = response_strategy(sentiment, risk_score, urgent)
    rationale = build_rationale(positive, negative, urgent, reach, alias_hits, source_weight, strategy)
    return Analysis(sentiment, risk_score, level, strategy, rationale)


def risk_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "guarded"
    return "low"


def response_strategy(sentiment: float, risk_score: int, urgent_count: int) -> str:
    if risk_score >= 80:
        return "crisis-response"
    if risk_score >= 60:
        return "de-escalate"
    if sentiment >= 0.5 and urgent_count == 0:
        return "amplify"
    if urgent_count > 0 or risk_score >= 40:
        return "clarify"
    return "neutral-watch"


def build_rationale(
    positive: int,
    negative: int,
    urgent: int,
    reach: int,
    alias_hits: int,
    source_weight: float,
    strategy: str,
) -> str:
    parts = [
        f"{positive} favorable term(s)",
        f"{negative} harmful term(s)",
        f"{urgent} urgency signal(s)",
        f"reach={reach}",
        f"entity hits={alias_hits}",
        f"source weight={source_weight:g}",
    ]
    parts.append(f"recommended action={strategy}")
    return "; ".join(parts)
