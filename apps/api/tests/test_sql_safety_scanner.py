from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import scan_sql_safety


class SqlSafetyScannerTest(unittest.TestCase):
    def test_scan_file_reports_function_and_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.py"
            path.write_text(
                "def list_rows(table):\n"
                "    return conn.execute(f\"SELECT * FROM {table}\")\n",
                encoding="utf-8",
            )

            findings = scan_sql_safety.scan_file(path)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].function, "list_rows")
        self.assertEqual(findings[0].risk, "high")

    def test_fail_on_new_blocks_missing_baseline_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "sample.py"
            sample.write_text("rows = conn.execute(f\"SELECT * FROM {table}\")\n", encoding="utf-8")
            baseline = Path(tmp) / "baseline.json"
            baseline.write_text(json.dumps({"findings": []}), encoding="utf-8")
            original_scan_root = scan_sql_safety.SCAN_ROOT
            try:
                scan_sql_safety.SCAN_ROOT = Path(tmp)
                result = scan_sql_safety.main(["--fail-on-new", "--baseline", str(baseline)])
            finally:
                scan_sql_safety.SCAN_ROOT = original_scan_root

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
