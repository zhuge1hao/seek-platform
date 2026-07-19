import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.export_pool_metrics import build_report  # noqa: E402


class ExportPoolMetricsTest(unittest.TestCase):
    def test_build_report_from_prometheus_text(self) -> None:
        text = """
app_db_pool_acquire_seconds_bucket{le="0.001"} 1
app_db_pool_acquire_seconds_bucket{le="0.01"} 2
app_db_pool_acquire_seconds_bucket{le="0.1"} 10
app_db_pool_acquire_seconds_bucket{le="+Inf"} 10
app_db_pool_timeout_total 0
app_db_pool_discarded_total 2
app_db_pool_reconnect_total 3
app_db_pool_in_use 4
app_db_pool_idle 5
app_db_pool_overflow 1
app_db_pool_waiters 0
"""
        report = build_report(text)
        self.assertIsNotNone(report["pool_wait_p95_seconds"])
        self.assertEqual(report["pool_timeout_total"], 0)
        self.assertEqual(report["pool_in_use"], 4)
        self.assertEqual(report["pool_overflow"], 1)


if __name__ == "__main__":
    unittest.main()
