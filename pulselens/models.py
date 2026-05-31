from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entity:
    id: int | None
    name: str
    aliases: list[str]
    description: str = ""


@dataclass(frozen=True)
class Mention:
    id: int | None
    entity_id: int
    source: str
    text: str
    url: str = ""
    author: str = ""
    published_at: str = ""
    reach: int = 1
    sentiment: float = 0.0
    risk_score: int = 0
    risk_level: str = "low"
    strategy: str = "neutral-watch"
    rationale: str = ""
