import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from services import dataset_export_service, metrics_service
from services.dataset_store import dataset_dir, record_dataset_files, update_dataset
from services.field_mapping_service import read_table, write_json


DEFAULT_RULES = {
    "dedupe_by_link": True,
    "min_total_price": 10,
    "min_unit_price": 15,
    "min_sales_amount": 1000,
    "min_cost_ratio": 5,
}

NUMERIC_FIELDS = {"price", "total_price", "unit_price", "spec_count", "sales_amount", "ad_spend", "cost_ratio", "sales_order_count", "shipping_order_count", "refund_rate", "profit", "profit_rate"}


class DataCleaningError(RuntimeError):
    pass


def parse_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[¥￥$,，\s]", "", text).replace("元", "")
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def clean_dataset(dataset: dict[str, Any], mapping: dict[str, str], rule_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = {**DEFAULT_RULES, **(rule_overrides or {})}
    _, raw_rows = read_table(dataset["source_path"])
    warnings: list[str] = []
    rule_fields = {"total_price": "总价无效", "unit_price": "单条价无效", "sales_amount": "成交金额过低", "cost_ratio": "费比无效"}
    for field in rule_fields:
        if field not in mapping:
            warnings.append(f"未映射{field}，已跳过对应清洗规则。")
    if rules.get("dedupe_by_link") and "link" not in mapping:
        warnings.append("未映射 link，已跳过重复链接去重。")

    seen_links: set[str] = set()
    valid_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    thresholds = {
        "total_price": (float(rules["min_total_price"]), "总价无效"),
        "unit_price": (float(rules["min_unit_price"]), "单条价无效"),
        "sales_amount": (float(rules["min_sales_amount"]), "成交金额过低"),
        "cost_ratio": (float(rules["min_cost_ratio"]), "费比无效"),
    }

    for raw in raw_rows:
        standard: dict[str, Any] = {}
        for field, column in mapping.items():
            value = raw.get(column)
            standard[field] = parse_number(value) if field in NUMERIC_FIELDS else value
        reasons: list[str] = []
        link = str(standard.get("link") or "").strip()
        if rules.get("dedupe_by_link") and link:
            if link in seen_links:
                reasons.append("重复链接")
            else:
                seen_links.add(link)
        for field, (minimum, reason) in thresholds.items():
            if field in mapping and (standard.get(field) is None or float(standard[field]) < minimum):
                reasons.append(reason)
        combined = {**raw, **standard}
        if reasons:
            for reason in reasons:
                reason_counts[reason] += 1
            combined["excluded_reason"] = "；".join(reasons)
            excluded_rows.append(combined)
        else:
            valid_rows.append(combined)

    valid_rows, metrics_summary = metrics_service.enrich_rows(valid_rows)
    created_at = datetime.now(timezone.utc).isoformat()
    profile = metrics_service.build_profile(dataset["dataset_id"], valid_rows, excluded_rows, dict(reason_counts), warnings, created_at)
    metrics_summary.update({"dataset_id": dataset["dataset_id"], "warnings": warnings, "created_at": created_at})
    root = dataset_dir(dataset["user_id"], dataset["dataset_id"])
    files = dataset_export_service.export_results(root / "cleaned", valid_rows, excluded_rows, profile, metrics_summary)
    write_json(root / "logs" / "cleaning_log.json", {"rules": rules, "mapping": mapping, "profile": profile, "created_at": created_at})
    updated = update_dataset(dataset["dataset_id"], dataset["user_id"], {
        "status": "cleaned",
        "cleaned_at": created_at,
        "cleaning_rules": rules,
        "profile": profile,
        "metrics": metrics_summary,
    })
    record_dataset_files(updated, files)
    return {"status": "success", "dataset_id": dataset["dataset_id"], "profile": profile, "metrics_summary": metrics_summary, "files": files, "dataset": updated}
