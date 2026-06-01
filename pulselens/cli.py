from __future__ import annotations

import argparse
from pathlib import Path

from .feeds import import_rss
from .reports import weekly_report
from .storage import DEFAULT_DB, add_mention, connect, get_or_create_entity, import_csv, init_db, summary
from .web import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pulselens", description="Social listening and public-opinion early warning.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create the local database.")
    sub.add_parser("seed", help="Create sample entities and mentions.")

    add_entity = sub.add_parser("add-entity", help="Add a watched entity.")
    add_entity.add_argument("name")
    add_entity.add_argument("--aliases", default="", help="Comma-separated aliases.")
    add_entity.add_argument("--description", default="")

    add = sub.add_parser("add-mention", help="Add a single mention.")
    add.add_argument("--entity", required=True)
    add.add_argument("--text", required=True)
    add.add_argument("--source", default="manual")
    add.add_argument("--url", default="")
    add.add_argument("--author", default="")
    add.add_argument("--reach", type=int, default=1)

    csv_cmd = sub.add_parser("import-csv", help="Import mentions from CSV.")
    csv_cmd.add_argument("path")
    csv_cmd.add_argument("--entity", required=True)

    rss_cmd = sub.add_parser("import-rss", help="Import mentions from an RSS feed.")
    rss_cmd.add_argument("url")
    rss_cmd.add_argument("--entity", required=True)
    rss_cmd.add_argument("--limit", type=int, default=50)

    sub.add_parser("summary", help="Print a JSON-like summary.")

    report_cmd = sub.add_parser("weekly-report", help="Export a Markdown public-opinion weekly report.")
    report_cmd.add_argument("--output", default="exports/weekly-report.md")
    report_cmd.add_argument("--days", type=int, default=7)

    web_cmd = sub.add_parser("serve", help="Start the local dashboard.")
    web_cmd.add_argument("--host", default="127.0.0.1")
    web_cmd.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    db_path = Path(args.db)
    init_db(db_path)

    if args.command == "init":
        print(f"Initialized {db_path}")
        return 0
    if args.command == "seed":
        seed(db_path)
        print("Seeded sample data.")
        return 0
    if args.command == "add-entity":
        aliases = [args.name] + [item.strip() for item in args.aliases.split(",") if item.strip()]
        with connect(db_path) as conn:
            get_or_create_entity(conn, args.name, aliases=aliases, description=args.description)
        print(f"Watching {args.name}")
        return 0
    if args.command == "add-mention":
        with connect(db_path) as conn:
            entity_id = get_or_create_entity(conn, args.entity, aliases=[args.entity])
            mention_id = add_mention(conn, entity_id, args.text, args.source, args.url, args.author, reach=args.reach)
        print(f"Added mention #{mention_id}")
        return 0
    if args.command == "import-csv":
        with connect(db_path) as conn:
            count = import_csv(conn, args.path, args.entity)
        print(f"Imported {count} mentions.")
        return 0
    if args.command == "import-rss":
        with connect(db_path) as conn:
            count = import_rss(conn, args.url, args.entity, limit=args.limit)
        print(f"Imported {count} RSS items.")
        return 0
    if args.command == "summary":
        with connect(db_path) as conn:
            print(summary(conn))
        return 0
    if args.command == "weekly-report":
        with connect(db_path) as conn:
            path = weekly_report(conn, args.output, days=args.days)
        print(f"Exported {path}")
        return 0
    if args.command == "serve":
        serve(args.host, args.port, db_path)
        return 0
    return 1


def seed(db_path: Path) -> None:
    samples = [
        ("Acme Cloud", ["Acme Cloud", "AcmeCloud", "Acme"], "Cloud productivity platform"),
        ("北极星咖啡", ["北极星咖啡", "Polaris Coffee"], "Regional coffee brand"),
    ]
    mentions = [
        ("Acme Cloud", "x", "Acme Cloud fixed the outage quickly. Thanks for the transparent update.", 4500),
        ("Acme Cloud", "reddit", "Acme Cloud is down again and support is slow. People are angry.", 23000),
        ("Acme Cloud", "press", "Regulator opens investigation after possible data breach at Acme Cloud.", 90000),
        ("北极星咖啡", "weibo", "北极星咖啡新品很好喝，服务也有改进，推荐。", 18000),
        ("北极星咖啡", "weibo", "爆料：北极星咖啡门店卫生糟糕，很多顾客投诉。", 76000),
        ("北极星咖啡", "survey", "价格有点昂贵，但整体体验可靠。", 500),
    ]
    with connect(db_path) as conn:
        ids = {
            name: get_or_create_entity(conn, name, aliases=aliases, description=description)
            for name, aliases, description in samples
        }
        for entity_name, source, text, reach in mentions:
            add_mention(conn, ids[entity_name], text, source=source, reach=reach)


if __name__ == "__main__":
    raise SystemExit(main())
