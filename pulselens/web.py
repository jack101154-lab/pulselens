from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analyzer import analyze
from .reports import weekly_report
from .storage import DEFAULT_DB, add_mention, connect, export_csv, get_or_create_entity, init_db, list_entities, list_mentions, summary


PACKAGE_DIR = Path(__file__).parent


class PulseLensHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.serve_file(PACKAGE_DIR / "templates" / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/api/summary":
            with connect(self.db_path) as conn:
                return self.json(summary(conn))
        if parsed.path == "/api/entities":
            with connect(self.db_path) as conn:
                return self.json({"entities": list_entities(conn)})
        if parsed.path == "/api/mentions":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["100"])[0])
            entity = query.get("entity_id", [None])[0]
            with connect(self.db_path) as conn:
                return self.json({"mentions": list_mentions(conn, limit=limit, entity_id=int(entity) if entity else None)})
        if parsed.path == "/export/mentions.csv":
            with connect(self.db_path) as conn:
                path = export_csv(conn, Path("exports/mentions.csv"))
            return self.serve_file(path, "text/csv; charset=utf-8")
        if parsed.path == "/export/weekly-report.md":
            with connect(self.db_path) as conn:
                path = weekly_report(conn, Path("exports/weekly-report.md"))
            return self.serve_file(path, "text/markdown; charset=utf-8")
        if parsed.path.startswith("/static/"):
            safe_name = parsed.path.removeprefix("/static/").replace("/", "")
            path = PACKAGE_DIR / "static" / safe_name
            content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
            return self.serve_file(path, content_type)
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            return self.error_json(str(exc), HTTPStatus.BAD_REQUEST)

        if parsed.path == "/api/entities":
            name = str(payload.get("name") or "").strip()
            if not name:
                return self.error_json("name is required", HTTPStatus.BAD_REQUEST)
            aliases_value = payload.get("aliases") or []
            aliases = aliases_value if isinstance(aliases_value, list) else str(aliases_value).split(",")
            description = str(payload.get("description") or "")
            with connect(self.db_path) as conn:
                entity_id = get_or_create_entity(conn, name, aliases=[name, *aliases], description=description)
            return self.json({"id": entity_id})

        if parsed.path == "/api/mentions":
            entity_name = str(payload.get("entity") or payload.get("entity_name") or "").strip()
            text = str(payload.get("text") or "").strip()
            if not entity_name or not text:
                return self.error_json("entity and text are required", HTTPStatus.BAD_REQUEST)
            with connect(self.db_path) as conn:
                entity_id = get_or_create_entity(conn, entity_name, aliases=[entity_name])
                mention_id = add_mention(
                    conn,
                    entity_id,
                    text,
                    source=str(payload.get("source") or "manual"),
                    url=str(payload.get("url") or ""),
                    author=str(payload.get("author") or ""),
                    published_at=str(payload.get("published_at") or ""),
                    reach=self.safe_int(payload.get("reach"), 1),
                )
            return self.json({"id": mention_id})

        if parsed.path == "/api/analyze-preview":
            text = str(payload.get("text") or "").strip()
            if not text:
                return self.error_json("text is required", HTTPStatus.BAD_REQUEST)
            aliases_value = payload.get("aliases") or []
            aliases = aliases_value if isinstance(aliases_value, list) else str(aliases_value).split(",")
            result = analyze(
                text,
                aliases=[str(item) for item in aliases],
                reach=self.safe_int(payload.get("reach"), 1),
            )
            return self.json(result.__dict__)

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args) -> None:
        return

    def json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, message: str, status: HTTPStatus) -> None:
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def read_json_body(self) -> dict:
        length = self.safe_int(self.headers.get("Content-Length"), 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    @staticmethod
    def safe_int(value: object, default: int = 0) -> int:
        try:
            return int(value or default)
        except (TypeError, ValueError):
            return default

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = "127.0.0.1", port: int = 8765, db_path: Path | str = DEFAULT_DB) -> None:
    init_db(db_path)
    PulseLensHandler.db_path = Path(db_path)
    server = ThreadingHTTPServer((host, port), PulseLensHandler)
    print(f"PulseLens running at http://{host}:{port}")
    server.serve_forever()
