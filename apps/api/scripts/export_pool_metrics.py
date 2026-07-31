from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import requests


def _samples(text: str, metric: str) -> list[tuple[dict[str, str], float]]:
    rows: list[tuple[dict[str, str], float]] = []
    prefix = f"{metric}"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.startswith(prefix):
            continue
        name_labels, value_text = line.rsplit(" ", 1)
        if "{" in name_labels:
            labels_text = name_labels[name_labels.index("{") + 1:name_labels.rindex("}")]
            labels = {}
            for item in labels_text.split(","):
                if not item:
                    continue
                key, value = item.split("=", 1)
                labels[key] = value.strip('"')
        else:
            labels = {}
        rows.append((labels, float(value_text)))
    return rows


def _gauge(text: str, metric: str) -> float:
    values = [value for _labels, value in _samples(text, metric)]
    return values[-1] if values else 0.0


def _bucket_counts(text: str, metric: str = "app_db_pool_acquire_seconds", required_labels: dict[str, str] | None = None) -> list[tuple[float, float]]:
    totals: dict[float, float] = {}
    for labels, value in _samples(text, f"{metric}_bucket"):
        if required_labels and any(labels.get(key) != expected for key, expected in required_labels.items()):
            continue
        le = labels.get("le")
        if le is None:
            continue
        upper = math.inf if le == "+Inf" else float(le)
        totals[upper] = totals.get(upper, 0.0) + value
    return sorted(totals.items(), key=lambda item: item[0])


def _histogram_quantile_from_buckets(buckets: list[tuple[float, float]], quantile: float) -> float | None:
    total = 0.0
    if buckets:
        total = buckets[-1][1]
    if total <= 0:
        return None
    target = total * quantile
    previous_upper = 0.0
    previous_count = 0.0
    for upper, count in buckets:
        if count < target:
            previous_upper = upper
            previous_count = count
            continue
        if math.isinf(upper):
            return previous_upper
        bucket_count = count - previous_count
        if bucket_count <= 0:
            return upper
        ratio = (target - previous_count) / bucket_count
        return previous_upper + (upper - previous_upper) * ratio
    return None


def _histogram_quantile(text: str, quantile: float) -> float | None:
    return _histogram_quantile_from_buckets(_bucket_counts(text), quantile)


def _counter_delta(snapshots: list[str], metric: str) -> float:
    if len(snapshots) < 2:
        return _gauge(snapshots[-1], metric)
    return max(0.0, _gauge(snapshots[-1], metric) - _gauge(snapshots[0], metric))


def _max_gauge(snapshots: list[str], metric: str) -> float:
    return max((_gauge(text, metric) for text in snapshots), default=0.0)


def _window_buckets(snapshots: list[str], metric: str = "app_db_pool_acquire_seconds", required_labels: dict[str, str] | None = None) -> list[tuple[float, float]]:
    if len(snapshots) < 2:
        return _bucket_counts(snapshots[-1], metric, required_labels)
    first = dict(_bucket_counts(snapshots[0], metric, required_labels))
    last = _bucket_counts(snapshots[-1], metric, required_labels)
    return [(upper, max(0.0, count - first.get(upper, 0.0))) for upper, count in last]


def fetch_snapshots(metrics_url: str, window_seconds: int) -> list[str]:
    snapshots: list[str] = []
    deadline = time.monotonic() + max(0, window_seconds)
    while True:
        response = requests.get(metrics_url, timeout=10)
        response.raise_for_status()
        snapshots.append(response.text)
        if window_seconds <= 0 or time.monotonic() >= deadline:
            return snapshots
        time.sleep(1)


def build_report(text: str) -> dict[str, Any]:
    return build_window_report([text])


def build_window_report(snapshots: list[str]) -> dict[str, Any]:
    buckets = _window_buckets(snapshots)
    latest = snapshots[-1]
    report: dict[str, Any] = {
        "samples": len(snapshots),
        "pool_wait_p50_seconds": _histogram_quantile_from_buckets(buckets, 0.5),
        "pool_wait_p95_seconds": _histogram_quantile_from_buckets(buckets, 0.95),
        "pool_wait_p99_seconds": _histogram_quantile_from_buckets(buckets, 0.99),
        "pool_timeout_total": _counter_delta(snapshots, "app_db_pool_timeout_total"),
        "pool_discarded_total": _counter_delta(snapshots, "app_db_pool_discarded_total"),
        "pool_reconnect_total": _counter_delta(snapshots, "app_db_pool_reconnect_total"),
        "pool_in_use": _gauge(latest, "app_db_pool_in_use"),
        "pool_idle": _gauge(latest, "app_db_pool_idle"),
        "pool_overflow": _gauge(latest, "app_db_pool_overflow"),
        "pool_waiters": _gauge(latest, "app_db_pool_waiters"),
        "max_pool_in_use": _max_gauge(snapshots, "app_db_pool_in_use"),
        "max_pool_idle": _max_gauge(snapshots, "app_db_pool_idle"),
        "max_pool_overflow": _max_gauge(snapshots, "app_db_pool_overflow"),
        "max_pool_waiters": _max_gauge(snapshots, "app_db_pool_waiters"),
    }
    for name, metric in {
        "execute": "app_db_execute_seconds",
        "commit": "app_db_commit_seconds",
        "rollback": "app_db_rollback_seconds",
    }.items():
        metric_buckets = _window_buckets(snapshots, metric)
        report.update({
            f"{name}_p50_seconds": _histogram_quantile_from_buckets(metric_buckets, 0.5),
            f"{name}_p95_seconds": _histogram_quantile_from_buckets(metric_buckets, 0.95),
            f"{name}_p99_seconds": _histogram_quantile_from_buckets(metric_buckets, 0.99),
        })
    report["submit_stages"] = {
        stage: {
            f"p{int(quantile * 100)}_seconds": _histogram_quantile_from_buckets(
                _window_buckets(snapshots, "app_agent_submit_stage_seconds", {"stage": stage}), quantile
            )
            for quantile in (0.5, 0.95, 0.99)
        }
        for stage in ("blueprint_guard", "prepare_ids", "persist_run_and_conversation", "enqueue", "compensation", "response")
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Export PostgreSQL pool metrics summary from /metrics.")
    parser.add_argument("--metrics-url", default="http://127.0.0.1/metrics")
    parser.add_argument("--window-seconds", type=int, default=0)
    parser.add_argument("--json-report", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    report = build_window_report(fetch_snapshots(args.metrics_url, args.window_seconds))
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.json_report else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
