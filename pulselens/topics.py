from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


TOPIC_RULES: dict[str, set[str]] = {
    "data-security": {"data breach", "security incident", "leak", "unsafe", "数据泄露", "安全事故", "泄露", "漏洞", "隐私"},
    "customer-service": {"support", "complaint", "slow", "客服", "售后", "投诉", "退款", "退货", "服务", "态度"},
    "product-quality": {"broken", "crash", "bug", "down", "quality", "崩溃", "宕机", "质量", "故障", "缺陷", "自燃"},
    "legal-regulatory": {"lawsuit", "regulator", "fraud", "class action", "违法", "监管", "诉讼", "欺诈", "起诉"},
    "viral-reputation": {"viral", "trending", "media", "press", "boycott", "热搜", "爆料", "媒体", "抵制", "曝光", "谣言"},
    "positive-advocacy": {"love", "great", "recommend", "thanks", "trusted", "喜欢", "推荐", "感谢", "满意", "好评", "支持"},
}

RISK_TYPE_TOPIC = {
    "security": "data-security",
    "privacy": "data-security",
    "service": "customer-service",
    "product": "product-quality",
    "legal": "legal-regulatory",
    "reputation": "viral-reputation",
}


def detect_topic(row: dict[str, Any]) -> str:
    text = f"{row.get('text') or ''} {row.get('ai_summary') or ''}".lower()
    scores = {
        topic: sum(1 for term in terms if term.lower() in text)
        for topic, terms in TOPIC_RULES.items()
    }
    topic, score = max(scores.items(), key=lambda item: item[1])
    if score > 0:
        return topic
    risk_type = str(row.get("risk_type") or "general")
    return RISK_TYPE_TOPIC.get(risk_type, "general-watch")


def cluster_mentions(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[detect_topic(row)].append(row)

    clusters = []
    for topic, items in groups.items():
        risk_scores = [int(item.get("risk_score") or 0) for item in items]
        levels = Counter(str(item.get("risk_level") or "L0") for item in items)
        risk_types = Counter(str(item.get("risk_type") or "general") for item in items)
        entities = Counter(str(item.get("entity_name") or "unknown") for item in items)
        examples = sorted(items, key=lambda item: int(item.get("risk_score") or 0), reverse=True)[:3]
        clusters.append(
            {
                "topic": topic,
                "count": len(items),
                "max_risk": max(risk_scores) if risk_scores else 0,
                "average_risk": round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0,
                "dominant_level": levels.most_common(1)[0][0] if levels else "L0",
                "dominant_risk_type": risk_types.most_common(1)[0][0] if risk_types else "general",
                "top_entity": entities.most_common(1)[0][0] if entities else "unknown",
                "examples": [
                    {
                        "id": item.get("id"),
                        "entity_name": item.get("entity_name"),
                        "risk_score": item.get("risk_score"),
                        "risk_level": item.get("risk_level"),
                        "summary": item.get("ai_summary") or item.get("text") or "",
                    }
                    for item in examples
                ],
            }
        )

    clusters.sort(key=lambda item: (item["max_risk"], item["count"]), reverse=True)
    return clusters[:limit]
