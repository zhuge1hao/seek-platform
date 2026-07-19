from __future__ import annotations

import argparse
import json
import math
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


def _histogram_quantile(text: str, quantile: float) -> float | None:
    buckets = []
    total = 0.0
    for labels, value in _samples(text, "app_db_pool_acquire_seconds_bucket"):
        le = labels.get("le")
        if le is None:
            continue
        upper = math.inf if le == "+Inf" else float(le)
        buckets.append((upper, value))
    buckets.sort(key=lambda item: item[0])
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


def build_report(text: str) -> dict[str, Any]:
    return {
        "pool_wait_p50_seconds": _histogram_quantile(text, 0.5),
        "pool_wait_p95_seconds": _histogram_quantile(text, 0.95),
        "pool_wait_p99_seconds": _histogram_quantile(text, 0.99),
        "pool_timeout_total": _gauge(text, "app_db_pool_timeout_total"),
        "pool_discarded_total": _gauge(text, "app_db_pool_discarded_total"),
        "pool_reconnect_total": _gauge(text, "app_db_pool_reconnect_total"),
        "pool_in_use": _gauge(text, "app_db_pool_in_use"),
        "pool_idle": _gauge(text, "app_db_pool_idle"),
        "pool_overflow": _gauge(text, "app_db_pool_overflow"),
        "pool_waiters": _gauge(text, "app_db_pool_waiters"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export PostgreSQL pool metrics summary from /metrics.")
    parser.add_argument("--metrics-url", default="http://127.0.0.1/metrics")
    args = parser.parse_args()
    response = requests.get(args.metrics_url, timeout=10)
    response.raise_for_status()
    print(json.dumps(build_report(response.text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
