import tempfile
import threading
import unittest
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
                self.assertIn("PulseLens", index)
                self.assertIn("total_mentions", summary)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
