import tempfile
import threading
import unittest
import json
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from pulselens.cli import seed
from pulselens.storage import init_db
from pulselens.web import PulseLensHandler


class WebTest(unittest.TestCase):
    def test_dashboard_and_summary_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "pulselens.db"
            init_db(db_path)
            seed(db_path)
            PulseLensHandler.db_path = db_path
            server = ThreadingHTTPServer(("127.0.0.1", 0), PulseLensHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                index = urllib.request.urlopen(base, timeout=5).read().decode("utf-8")
                summary = urllib.request.urlopen(f"{base}/api/summary", timeout=5).read().decode("utf-8")
                topics = urllib.request.urlopen(f"{base}/api/topics", timeout=5).read().decode("utf-8")
                self.assertIn("PulseLens", index)
                self.assertIn("total_mentions", summary)
                self.assertIn("topics", topics)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_post_mention_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "pulselens.db"
            init_db(db_path)
            PulseLensHandler.db_path = db_path
            server = ThreadingHTTPServer(("127.0.0.1", 0), PulseLensHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                body = json.dumps({
                    "entity": "北极星咖啡",
                    "source": "weibo",
                    "text": "爆料：门店服务糟糕，很多顾客投诉。",
                    "reach": 76000,
                }).encode("utf-8")
                request = urllib.request.Request(
                    f"{base}/api/mentions",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                created = urllib.request.urlopen(request, timeout=5).read().decode("utf-8")
                summary = urllib.request.urlopen(f"{base}/api/summary", timeout=5).read().decode("utf-8")
                self.assertIn("id", created)
                self.assertIn('"total_mentions": 1', summary)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_mentions_endpoint_handles_invalid_and_negative_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "pulselens.db"
            init_db(db_path)
            seed(db_path)
            PulseLensHandler.db_path = db_path
            server = ThreadingHTTPServer(("127.0.0.1", 0), PulseLensHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                invalid = urllib.request.urlopen(
                    f"{base}/api/mentions?limit=invalid", timeout=5
                ).read().decode("utf-8")
                negative = urllib.request.urlopen(
                    f"{base}/api/mentions?limit=-5", timeout=5
                ).read().decode("utf-8")

                self.assertGreater(len(json.loads(invalid)["mentions"]), 1)
                self.assertEqual(len(json.loads(negative)["mentions"]), 1)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
