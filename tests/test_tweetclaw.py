import json
import tempfile
import unittest
from pathlib import Path

from pulselens.storage import connect, init_db, list_mentions
from pulselens.tweetclaw import import_tweetclaw_json


class TweetClawImportTest(unittest.TestCase):
    def test_imports_tweetclaw_tweets(self):
        payload = {
            "tweets": [
                {
                    "id": "123",
                    "text": "Acme Cloud outage is unsafe and customers are angry.",
                    "author": {"username": "analyst"},
                    "created": "2026-06-06T18:00:00Z",
                    "url": "https://x.com/analyst/status/123",
                    "view_count": 1200,
                },
                {"text": ""},
            ]
        }
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "pulselens.db"
            json_path = Path(tmp) / "tweetclaw.json"
            json_path.write_text(json.dumps(payload), encoding="utf-8")
            init_db(db_path)

            with connect(db_path) as conn:
                count = import_tweetclaw_json(conn, json_path, "Acme Cloud")
                mentions = list_mentions(conn)

        self.assertEqual(count, 1)
        self.assertEqual(mentions[0]["source"], "tweetclaw-x")
        self.assertEqual(mentions[0]["author"], "@analyst")
        self.assertEqual(mentions[0]["reach"], 1200)
        self.assertIn("Acme Cloud outage", mentions[0]["text"])

    def test_imports_nested_result_items_with_engagement_reach(self):
        payload = {
            "data": {
                "items": [
                    {
                        "full_text": "Acme Cloud support delay caused many complaints.",
                        "user": {"screen_name": "customer"},
                        "tweet_url": "https://x.com/customer/status/456",
                        "like_count": 5,
                        "retweet_count": 2,
                        "reply_count": 3,
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "pulselens.db"
            json_path = Path(tmp) / "tweetclaw.json"
            json_path.write_text(json.dumps(payload), encoding="utf-8")
            init_db(db_path)

            with connect(db_path) as conn:
                count = import_tweetclaw_json(conn, json_path, "Acme Cloud")
                mentions = list_mentions(conn)

        self.assertEqual(count, 1)
        self.assertEqual(mentions[0]["author"], "@customer")
        self.assertEqual(mentions[0]["reach"], 10)
        self.assertEqual(mentions[0]["url"], "https://x.com/customer/status/456")

    def test_imports_camel_case_view_count(self):
        payload = {
            "results": [
                {
                    "text": "Acme Cloud launch reached the developer crowd.",
                    "author": "launchdesk",
                    "viewCount": 4321,
                }
            ]
        }
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "pulselens.db"
            json_path = Path(tmp) / "tweetclaw.json"
            json_path.write_text(json.dumps(payload), encoding="utf-8")
            init_db(db_path)

            with connect(db_path) as conn:
                count = import_tweetclaw_json(conn, json_path, "Acme Cloud")
                mentions = list_mentions(conn)

        self.assertEqual(count, 1)
        self.assertEqual(mentions[0]["author"], "@launchdesk")
        self.assertEqual(mentions[0]["reach"], 4321)


if __name__ == "__main__":
    unittest.main()
