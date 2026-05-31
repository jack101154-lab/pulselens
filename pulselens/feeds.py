from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

from .storage import add_mention, get_or_create_entity


def import_rss(conn, feed_url: str, entity_name: str, limit: int = 50) -> int:
    request = urllib.request.Request(feed_url, headers={"User-Agent": "PulseLens/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
    root = ET.fromstring(body)
    entity_id = get_or_create_entity(conn, entity_name, aliases=[entity_name])

    count = 0
    for item in root.findall(".//item")[:limit]:
        title = text_of(item, "title")
        description = strip_html(text_of(item, "description"))
        link = text_of(item, "link")
        published_at = text_of(item, "pubDate")
        text = " ".join(part for part in [title, description] if part)
        if text:
            add_mention(conn, entity_id, text, source="rss-news", url=link, published_at=published_at, reach=50)
            count += 1
    return count


def text_of(item: ET.Element, tag: str) -> str:
    found = item.find(tag)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def strip_html(value: str) -> str:
    result = []
    in_tag = False
    for char in unescape(value):
        if char == "<":
            in_tag = True
            continue
        if char == ">":
            in_tag = False
            result.append(" ")
            continue
        if not in_tag:
            result.append(char)
    return " ".join("".join(result).split())
