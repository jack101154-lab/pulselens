from __future__ import annotations

import math
import re
from dataclasses import dataclass


POSITIVE_TERMS = {
    "love", "great", "excellent", "reliable", "fast", "secure", "helpful",
    "transparent", "recommend", "improved", "trusted", "thanks", "resolved",
    "喜欢", "优秀", "可靠", "快速", "安全", "有用", "推荐", "改进", "信任", "感谢", "解决",
    "满意", "良心", "专业", "负责", "好评", "顺畅", "稳定", "放心", "支持",
}

NEGATIVE_TERMS = {
    "bad", "broken", "angry", "hate", "scam", "unsafe", "leak", "fraud",
    "boycott", "complaint", "lawsuit", "crash", "down", "slow", "expensive",
    "糟糕", "生气", "讨厌", "骗局", "不安全", "泄露", "欺诈", "抵制", "投诉", "诉讼",
    "崩溃", "宕机", "缓慢", "昂贵", "失望", "垃圾", "骗子", "退款", "维权",
    "翻车", "造假", "欺骗", "恶心", "差评", "拉黑", "曝光", "道歉",
}

URGENT_TERMS = {
    "urgent", "breaking", "viral", "trending", "investigation", "regulator",
    "media", "press", "security incident", "data breach", "class action",
    "紧急", "爆料", "热搜", "媒体", "记者", "监管", "调查", "数据泄露", "安全事故", "集体诉讼",
    "死亡", "违法", "事故", "起诉", "报警", "315", "央视", "通报", "封号",
}

RISK_TYPE_TERMS = {
    "service": {"support", "客服", "售后", "服务", "退货", "退款", "投诉", "排队", "态度"},
    "product": {"broken", "crash", "bug", "质量", "产品", "故障", "崩溃", "宕机", "缺陷", "自燃"},
    "security": {"unsafe", "leak", "data breach", "安全", "泄露", "漏洞", "事故", "风险"},
    "legal": {"lawsuit", "fraud", "regulator", "class action", "违法", "诉讼", "欺诈", "监管", "起诉", "合同"},
    "privacy": {"privacy", "doxx", "phone", "address", "隐私", "手机号", "身份证", "住址", "家人"},
    "reputation": {"boycott", "scam", "viral", "press", "抵制", "骗局", "热搜", "曝光", "媒体", "谣言"},
}


@dataclass(frozen=True)
class Analysis:
    sentiment: float
    risk_score: int
    risk_level: str
    risk_type: str
    strategy: str
    summary: str
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
    detected_type = risk_type(text)
    strategy = response_strategy(sentiment, risk_score, urgent)
    summary = summarize(text)
    rationale = build_rationale(positive, negative, urgent, reach, alias_hits, source_weight, detected_type, strategy)
    return Analysis(sentiment, risk_score, level, detected_type, strategy, summary, rationale)


def risk_level(score: int) -> str:
    if score >= 91:
        return "L5"
    if score >= 76:
        return "L4"
    if score >= 61:
        return "L3"
    if score >= 41:
        return "L2"
    if score >= 21:
        return "L1"
    return "L0"


def response_strategy(sentiment: float, risk_score: int, urgent_count: int) -> str:
    if risk_score >= 91:
        return "crisis-response"
    if risk_score >= 76:
        return "legal-or-executive-review"
    if risk_score >= 61:
        return "de-escalate"
    if sentiment >= 0.5 and urgent_count == 0:
        return "amplify"
    if urgent_count > 0 or risk_score >= 41:
        return "clarify"
    return "neutral-watch"


def risk_type(text: str) -> str:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, terms in RISK_TYPE_TERMS.items():
        scores[category] = sum(1 for term in terms if term.lower() in lowered)
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score > 0 else "general"


def summarize(text: str, limit: int = 140) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def build_rationale(
    positive: int,
    negative: int,
    urgent: int,
    reach: int,
    alias_hits: int,
    source_weight: float,
    risk_type_name: str,
    strategy: str,
) -> str:
    parts = [
        f"{positive} favorable term(s)",
        f"{negative} harmful term(s)",
        f"{urgent} urgency signal(s)",
        f"reach={reach}",
        f"entity hits={alias_hits}",
        f"source weight={source_weight:g}",
        f"risk type={risk_type_name}",
    ]
    parts.append(f"recommended action={strategy}")
    return "; ".join(parts)
