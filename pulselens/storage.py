from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

from .analyzer import analyze


DEFAULT_DB = Path("data/pulselens.db")


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  aliases TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id INTEGER NOT NULL,
  source TEXT NOT NULL DEFAULT 'manual',
  text TEXT NOT NULL,
  url TEXT NOT NULL DEFAULT '',
  author TEXT NOT NULL DEFAULT '',
  published_at TEXT NOT NULL DEFAULT '',
  reach INTEGER NOT NULL DEFAULT 1,
  sentiment REAL NOT NULL DEFAULT 0,
  risk_score INTEGER NOT NULL DEFAULT 0,
  risk_level TEXT NOT NULL DEFAULT 'low',
  strategy TEXT NOT NULL DEFAULT 'neutral-watch',
  rationale TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE INDEX IF NOT EXISTS idx_mentions_entity ON mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_mentions_risk ON mentions(risk_score DESC);
"""


def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DEFAULT_DB) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def get_or_create_entity(conn: sqlite3.Connection, name: str, aliases: list[str] | None = None, description: str = "") -> int:
    aliases = aliases or [name]
    alias_text = ",".join(dict.fromkeys([item.strip() for item in aliases if item.strip()]))
    row = conn.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cur = conn.execute(
        "INSERT INTO entities (name, aliases, description) VALUES (?, ?, ?)",
        (name, alias_text, description),
    )
    return int(cur.lastrowid)


def entity_aliases(conn: sqlite3.Connection, entity_id: int) -> list[str]:
    row = conn.execute("SELECT name, aliases FROM entities WHERE id = ?", (entity_id,)).fetchone()
    if not row:
        return []
    aliases = [row["name"]]
    aliases.extend(part.strip() for part in row["aliases"].split(",") if part.strip())
    return list(dict.fromkeys(aliases))


def add_mention(
    conn: sqlite3.Connection,
    entity_id: int,
    text: str,
    source: str = "manual",
    url: str = "",
    author: str = "",
    published_at: str = "",
    reach: int = 1,
) -> int:
    aliases = entity_aliases(conn, entity_id)
    source_weight = source_importance(source)
    result = analyze(text, aliases=aliases, reach=reach, source_weight=source_weight)
    cur = conn.execute(
        """
        INSERT INTO mentions
        (entity_id, source, text, url, author, published_at, reach, sentiment, risk_score, risk_level, strategy, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_id,
            source,
            text,
            url,
            author,
            published_at,
            reach,
            result.sentiment,
            result.risk_score,
            result.risk_level,
            result.strategy,
            result.rationale,
        ),
    )
    return int(cur.lastrowid)


def source_importance(source: str) -> float:
    source = source.lower()
    if any(key in source for key in ["press", "news", "media", "newspaper"]):
        return 1.5
    if any(key in source for key in ["x", "twitter", "weibo", "reddit", "tiktok"]):
        return 1.25
    if any(key in source for key in ["support", "ticket", "survey"]):
        return 1.1
    return 1.0


def list_entities(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT e.*, COUNT(m.id) AS mentions,
               COALESCE(AVG(m.risk_score), 0) AS avg_risk,
               COALESCE(MAX(m.risk_score), 0) AS max_risk
        FROM entities e
        LEFT JOIN mentions m ON m.entity_id = e.id
        GROUP BY e.id
        ORDER BY max_risk DESC, e.name ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_mentions(conn: sqlite3.Connection, limit: int = 100, entity_id: int | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    where = ""
    if entity_id:
        where = "WHERE m.entity_id = ?"
        params.append(entity_id)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT m.*, e.name AS entity_name
        FROM mentions m
        JOIN entities e ON e.id = m.entity_id
        {where}
        ORDER BY m.risk_score DESC, m.created_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def summary(conn: sqlite3.Connection) -> dict[str, Any]:
    total_mentions = conn.execute("SELECT COUNT(*) AS count FROM mentions").fetchone()["count"]
    high_alerts = conn.execute("SELECT COUNT(*) AS count FROM mentions WHERE risk_score >= 60").fetchone()["count"]
    avg_risk = conn.execute("SELECT COALESCE(AVG(risk_score), 0) AS value FROM mentions").fetchone()["value"]
    top = list_mentions(conn, limit=5)
    by_level = conn.execute(
        "SELECT risk_level, COUNT(*) AS count FROM mentions GROUP BY risk_level ORDER BY count DESC"
    ).fetchall()
    by_strategy = conn.execute(
        "SELECT strategy, COUNT(*) AS count FROM mentions GROUP BY strategy ORDER BY count DESC"
    ).fetchall()
    return {
        "total_mentions": total_mentions,
        "high_alerts": high_alerts,
        "average_risk": round(float(avg_risk), 1),
        "top_alerts": top,
        "levels": [dict(row) for row in by_level],
        "strategies": [dict(row) for row in by_strategy],
    }


def import_csv(conn: sqlite3.Connection, csv_path: Path | str, entity_name: str) -> int:
    entity_id = get_or_create_entity(conn, entity_name, aliases=[entity_name])
    count = 0
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = row.get("text") or row.get("content") or row.get("body") or ""
            if not text.strip():
                continue
            add_mention(
                conn,
                entity_id,
                text.strip(),
                source=row.get("source") or "csv",
                url=row.get("url") or "",
                author=row.get("author") or "",
                published_at=row.get("published_at") or row.get("date") or "",
                reach=safe_int(row.get("reach"), 1),
            )
            count += 1
    return count


def export_csv(conn: sqlite3.Connection, output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list_mentions(conn, limit=10000)
    fields = [
        "id", "entity_name", "source", "author", "published_at", "reach", "sentiment",
        "risk_score", "risk_level", "strategy", "text", "url", "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def safe_int(value: object, default: int = 1) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default
