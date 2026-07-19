from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .storage import add_mention, get_or_create_entity, safe_int


CONTAINER_KEYS = ("tweets", "results", "items", "data")
TEXT_KEYS = ("text", "full_text", "content", "body")
URL_KEYS = ("url", "tweet_url", "link", "permalink")
PUBLISHED_KEYS = ("published_at", "created_at", "created", "date")
AUTHOR_KEYS = ("author", "user", "username", "screen_name", "name")
REACH_KEYS = (
    "view_count",
    "viewCount",
    "views",
    "impression_count",
    "impressionCount",
    "impressions",
)


def import_tweetclaw_json(
    conn: sqlite3.Connection,
    json_path: Path | str,
    entity_name: str,
    limit: int = 200,
) -> int:
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    entity_id = get_or_create_entity(conn, entity_name, aliases=[entity_name])

    count = 0
    for record in iter_tweet_records(payload):
        if count >= limit:
            break
        text = first_text(record, TEXT_KEYS)
        if not text:
            continue
        add_mention(
            conn,
            entity_id,
            text,
            source="tweetclaw-x",
            url=first_text(record, URL_KEYS),
            author=author_name(record),
            published_at=first_text(record, PUBLISHED_KEYS),
            reach=estimated_reach(record),
        )
        count += 1
    return count


def iter_tweet_records(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            yield from iter_tweet_records(item)
        return

    if not isinstance(payload, dict):
        return

    if first_text(payload, TEXT_KEYS):
        yield payload

    for key in CONTAINER_KEYS:
        if key in payload:
            yield from iter_tweet_records(payload[key])


def first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def author_name(record: dict[str, Any]) -> str:
    for key in AUTHOR_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_handle(value)
        if isinstance(value, dict):
            nested = first_text(value, ("username", "screen_name", "name"))
            if nested:
                return normalize_handle(nested)
    return ""


def normalize_handle(value: str) -> str:
    value = value.strip()
    if value.startswith("@") or " " in value:
        return value
    return f"@{value}"


def estimated_reach(record: dict[str, Any]) -> int:
    for key in REACH_KEYS:
        value = safe_int(record.get(key), 0)
        if value > 0:
            return value

    engagement = sum(
        safe_int(record.get(key), 0)
        for key in ("like_count", "retweet_count", "reply_count", "quote_count", "bookmark_count")
    )
    return max(engagement, 1)
