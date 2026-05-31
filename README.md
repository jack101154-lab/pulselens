# PulseLens

PulseLens is an open-source social listening and public-opinion early-warning workbench for maintainers, researchers, small teams, and individual creators.

It helps you monitor mentions of a person, brand, project, or organization, classify sentiment, estimate reputational risk, and generate practical response suggestions before a conversation turns into a crisis.

## Why this project exists

Most social listening products are expensive SaaS tools. Many open-source attempts depend on fragile scraping or private platform APIs. PulseLens starts from a safer and more portable foundation:

- Bring your own data through CSV exports, RSS feeds, or future connectors.
- Run analysis locally with transparent scoring rules.
- Keep the risk model explainable enough for research and audit.
- Make response recommendations visible, editable, and exportable.

## Core features

- **Entity monitoring**: Track multiple watched subjects with keyword aliases.
- **CSV import**: Ingest exported posts, comments, news snippets, tickets, or survey text.
- **RSS import**: Pull public web feeds without relying on private social APIs.
- **Multilingual sentiment baseline**: Includes English and Chinese lexicons for favorable, harmful, and urgent signals.
- **Risk scoring**: Combines sentiment, reach, urgency, source weight, and keyword matches.
- **Crisis levels**: Labels items as low, guarded, elevated, high, or critical.
- **Response strategy**: Suggests amplify, clarify, neutral-watch, de-escalate, or crisis-response actions.
- **Dashboard**: Local web UI for recent mentions, trend summaries, alerts, and entity-level risk.
- **Exports**: JSON endpoint and CSV export for reporting or research workflows.
- **Privacy-first local storage**: SQLite database stored on your machine.

## Quick start

```bash
python -m pip install -e .
pulselens seed
pulselens serve
```

Open http://127.0.0.1:8765 in your browser.

## Import CSV

```bash
pulselens import-csv examples/sample_mentions.csv --entity "Acme Cloud"
```

CSV columns can include:

- `text` or `content` (required)
- `source`
- `url`
- `author`
- `published_at`
- `reach`

## Import RSS

```bash
pulselens import-rss https://example.com/feed.xml --entity "Acme Cloud"
```

## Run tests

```bash
python -m unittest discover -s tests
```

## Roadmap

- Pluggable source connectors for Mastodon, Reddit exports, GitHub issues, YouTube comments exports, and news APIs.
- Research mode with coding sheets and inter-annotator agreement helpers.
- Team workflow: assignment, status, response log, and postmortem templates.
- Better multilingual models with optional local LLM or API-backed classifiers.
- Alert destinations: email, webhook, Slack, Feishu, and DingTalk.

## Responsible use

PulseLens is designed for lawful monitoring of public or user-provided data. Do not use it for harassment, surveillance, doxxing, or private-data collection. Respect platform terms, local law, and consent requirements.

## License

MIT
