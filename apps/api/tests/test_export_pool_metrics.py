import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.export_pool_metrics import build_report, build_window_report  # noqa: E402


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
        self.assertEqual(report["max_pool_in_use"], 4)

    def test_build_window_report_uses_bucket_and_counter_deltas(self) -> None:
        first = """
app_db_pool_acquire_seconds_bucket{le="0.001"} 10
app_db_pool_acquire_seconds_bucket{le="0.01"} 10
app_db_pool_acquire_seconds_bucket{le="0.1"} 10
app_db_pool_acquire_seconds_bucket{le="+Inf"} 10
app_db_pool_timeout_total 1
app_db_pool_discarded_total 2
app_db_pool_reconnect_total 3
app_db_pool_in_use 1
app_db_pool_idle 4
app_db_pool_overflow 0
app_db_pool_waiters 0
"""
        second = """
app_db_pool_acquire_seconds_bucket{le="0.001"} 10
app_db_pool_acquire_seconds_bucket{le="0.01"} 12
app_db_pool_acquire_seconds_bucket{le="0.1"} 20
app_db_pool_acquire_seconds_bucket{le="+Inf"} 20
app_db_pool_timeout_total 3
app_db_pool_discarded_total 2
app_db_pool_reconnect_total 4
app_db_pool_in_use 0
app_db_pool_idle 5
app_db_pool_overflow 2
app_db_pool_waiters 1
"""
        report = build_window_report([first, second])
        self.assertEqual(report["samples"], 2)
        self.assertIsNotNone(report["pool_wait_p95_seconds"])
        self.assertEqual(report["pool_timeout_total"], 2)
        self.assertEqual(report["pool_reconnect_total"], 1)
        self.assertEqual(report["max_pool_overflow"], 2)
        self.assertEqual(report["max_pool_waiters"], 1)


if __name__ == "__main__":
    unittest.main()
