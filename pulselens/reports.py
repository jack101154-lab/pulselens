from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .storage import list_mentions
from .topics import cluster_mentions


def weekly_report(conn, output_path: Path | str = "exports/weekly-report.md", days: int = 7) -> Path:
    rows = list_mentions(conn, limit=10000)
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
    recent = [row for row in rows if is_recent(row, since)]
    if not recent:
        recent = rows

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_weekly_report(recent, days), encoding="utf-8")
    return path


def is_recent(row: dict[str, Any], since: datetime) -> bool:
    value = row.get("published_at") or row.get("created_at") or ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[: len(fmt)], fmt) >= since
        except ValueError:
            continue
    return True


def render_weekly_report(rows: list[dict[str, Any]], days: int = 7) -> str:
    total = len(rows)
    high_risk = [row for row in rows if int(row.get("risk_score") or 0) >= 61]
    positive = [row for row in rows if float(row.get("sentiment") or 0) > 0]
    negative = [row for row in rows if float(row.get("sentiment") or 0) < 0]
    neutral = total - len(positive) - len(negative)

    levels = Counter(row.get("risk_level") or "L0" for row in rows)
    strategies = Counter(row.get("strategy") or "neutral-watch" for row in rows)
    risk_types = Counter(row.get("risk_type") or "general" for row in rows)
    platforms = Counter(row.get("source") or "unknown" for row in rows)
    entities = Counter(row.get("entity_name") or "unknown" for row in rows)
    topics = cluster_mentions(rows, limit=8)

    lines = [
        "# PulseLens Weekly Public Opinion Report",
        "",
        f"Period: last {days} day(s)",
        f"Generated at: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Executive Summary",
        "",
        f"- Total mentions analyzed: {total}",
        f"- High-risk mentions (L3-L5): {len(high_risk)}",
        f"- Sentiment split: {len(positive)} favorable, {neutral} neutral, {len(negative)} harmful",
        f"- Most common risk type: {top_label(risk_types)}",
        f"- Recommended dominant action: {top_label(strategies)}",
        "",
        "## Risk Level Distribution",
        "",
    ]
    lines.extend(counter_lines(levels))
    lines.extend(["", "## Platform Distribution", ""])
    lines.extend(counter_lines(platforms))
    lines.extend(["", "## Watched Entity Distribution", ""])
    lines.extend(counter_lines(entities))
    lines.extend(["", "## Risk Type Distribution", ""])
    lines.extend(counter_lines(risk_types))
    lines.extend(["", "## Topic Clusters", ""])
    if topics:
        for topic in topics:
            lines.append(
                f"- {topic['topic']}: {topic['count']} mention(s), "
                f"max risk {topic['max_risk']}, dominant type {topic['dominant_risk_type']}"
            )
    else:
        lines.append("- No topic clusters detected")
    lines.extend(["", "## Priority Alerts", ""])

    for row in sorted(rows, key=lambda item: int(item.get("risk_score") or 0), reverse=True)[:8]:
        lines.append(f"### {row.get('risk_level')} - {row.get('entity_name')} - score {row.get('risk_score')}")
        lines.append("")
        lines.append(f"- Source: {row.get('source') or 'unknown'}")
        lines.append(f"- Risk type: {row.get('risk_type') or 'general'}")
        lines.append(f"- Strategy: {row.get('strategy') or 'neutral-watch'}")
        lines.append(f"- Summary: {row.get('ai_summary') or row.get('text') or ''}")
        if row.get("url"):
            lines.append(f"- URL: {row['url']}")
        lines.append("")

    lines.extend([
        "## Suggested Next Actions",
        "",
        "- Review L3-L5 mentions first and decide whether to create response tasks.",
        "- Amplify favorable mentions with high reach when there is no active controversy.",
        "- Keep a human reviewer in the loop before publishing public responses.",
        "- Treat risk scores as decision-support signals, not verified facts.",
        "",
    ])
    return "\n".join(lines)


def counter_lines(counter: Counter) -> list[str]:
    if not counter:
        return ["- No data"]
    return [f"- {label}: {count}" for label, count in counter.most_common()]


def top_label(counter: Counter) -> str:
    if not counter:
        return "none"
    label, count = counter.most_common(1)[0]
    return f"{label} ({count})"
