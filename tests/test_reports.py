import tempfile
import unittest
from pathlib import Path

from pulselens.cli import seed
from pulselens.reports import weekly_report
from pulselens.storage import connect, init_db


class ReportsTest(unittest.TestCase):
    def test_weekly_report_exports_markdown(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db_path = Path(tmp) / "pulselens.db"
            output_path = Path(tmp) / "weekly.md"
            init_db(db_path)
            seed(db_path)
            with connect(db_path) as conn:
                result = weekly_report(conn, output_path)

            content = result.read_text(encoding="utf-8")
            self.assertIn("PulseLens Weekly Public Opinion Report", content)
            self.assertIn("Topic Clusters", content)
            self.assertIn("Priority Alerts", content)
            self.assertIn("Suggested Next Actions", content)


if __name__ == "__main__":
    unittest.main()
