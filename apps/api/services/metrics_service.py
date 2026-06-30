from collections import Counter
from statistics import median
from typing import Any


def price_band(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 30:
        return "30以下"
    if value <= 50:
        return "31–50"
    if value <= 70:
        return "50–70"
    if value <= 99:
        return "71–99"
    if value <= 129:
        return "99–129"
    if value <= 159:
        return "129–159"
    return "159以上"


def _numbers(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]


def enrich_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    total_sales = sum(_numbers(rows, "sales_amount"))
    cost_values = _numbers(rows, "cost_ratio")
    sales_values = _numbers(rows, "sales_amount")
    cost_median = median(cost_values) if cost_values else None
    sales_median = median(sales_values) if sales_values else None
    distribution: Counter[str] = Counter()

    for row in rows:
        selected_price = row.get("unit_price") if isinstance(row.get("unit_price"), (int, float)) else row.get("total_price")
        band = price_band(float(selected_price)) if isinstance(selected_price, (int, float)) else None
        if band:
            distribution[band] += 1
        sales = row.get("sales_amount")
        ad_spend = row.get("ad_spend")
        row["price_band"] = band
        row["sales_share"] = round(float(sales) / total_sales * 100, 4) if isinstance(sales, (int, float)) and total_sales else None
        row["natural_sales_flag"] = not isinstance(ad_spend, (int, float)) or float(ad_spend) == 0
        row["natural_sales_note"] = "自然成交或未记录付费花费" if row["natural_sales_flag"] else None
        row["efficiency_ratio"] = round(float(sales) / float(ad_spend), 4) if isinstance(sales, (int, float)) and isinstance(ad_spend, (int, float)) and float(ad_spend) != 0 else None
        row["low_cost_high_sales_flag"] = bool(
            cost_median is not None and sales_median is not None
            and isinstance(row.get("cost_ratio"), (int, float)) and isinstance(sales, (int, float))
            and float(row["cost_ratio"]) <= cost_median and float(sales) >= sales_median
        )

    return rows, {
        "total_sales_amount": round(total_sales, 4),
        "cost_ratio_median": cost_median,
        "sales_amount_median": sales_median,
        "price_band_distribution": dict(distribution),
    }


def build_profile(dataset_id: str, valid_rows: list[dict[str, Any]], excluded_rows: list[dict[str, Any]], reason_counts: dict[str, int], warnings: list[str], created_at: str) -> dict[str, Any]:
    raw_count = len(valid_rows) + len(excluded_rows)
    cost_values = _numbers(valid_rows, "cost_ratio")
    unit_prices = _numbers(valid_rows, "unit_price")
    total_sales = sum(_numbers(valid_rows, "sales_amount"))
    distribution = Counter(row.get("price_band") for row in valid_rows if row.get("price_band"))
    top = sorted((row for row in valid_rows if row.get("low_cost_high_sales_flag")), key=lambda row: row.get("sales_amount") or 0, reverse=True)[:10]
    return {
        "dataset_id": dataset_id, "raw_count": raw_count, "valid_count": len(valid_rows),
        "excluded_count": len(excluded_rows), "valid_rate": round(len(valid_rows) / raw_count * 100, 2) if raw_count else 0,
        "total_sales_amount": round(total_sales, 4),
        "avg_cost_ratio": round(sum(cost_values) / len(cost_values), 4) if cost_values else None,
        "avg_unit_price": round(sum(unit_prices) / len(unit_prices), 4) if unit_prices else None,
        "excluded_reason_counts": reason_counts, "price_band_distribution": dict(distribution),
        "top_low_cost_high_sales": [
            {key: row.get(key) for key in ("shop_name", "title", "sales_amount", "cost_ratio", "efficiency_ratio")}
            for row in top
        ],
        "warnings": warnings, "created_at": created_at,
    }
