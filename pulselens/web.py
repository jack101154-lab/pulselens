from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .storage import DEFAULT_DB, connect, export_csv, init_db, list_entities, list_mentions, summary


PACKAGE_DIR = Path(__file__).parent


class PulseLensHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB

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
        if parsed.path.startswith("/static/"):
            safe_name = parsed.path.removeprefix("/static/").replace("/", "")
            path = PACKAGE_DIR / "static" / safe_name
            content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
            return self.serve_file(path, content_type)
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args) -> None:
        return

    def json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
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
