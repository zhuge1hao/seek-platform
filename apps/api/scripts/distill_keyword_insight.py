from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from services.keyword_insight_service import analyze_rows, classification_metrics, read_ground_truth  # noqa: E402


DEFAULT_CONTEXT = {
    "industry": "女性内衣",
    "category": "女士内裤",
    "target_audience": ["30-45岁女性", "45-65岁女性", "妈妈", "中老年"],
    "materials": ["纯棉", "桑蚕丝", "羊绒"],
    "functions": ["高腰", "收腹", "无痕", "抗菌"],
}


def build_report(source_file: str | Path) -> dict:
    rows, labels, counts, overlaps = read_ground_truth(source_file)
    result = analyze_rows(rows, DEFAULT_CONTEXT)
    metrics = classification_metrics(result, labels)
    return {
        "source": {"file_name": Path(source_file).name, "sheet_counts": counts, "overlapping_strategy_keywords": overlaps},
        "benchmark_inference": result["benchmarks"],
        "ground_truth_counts": {
            "must_win": sum(value == "must_win" for value in labels.values()),
            "blue_ocean_supply_gap": sum(value == "blue_ocean_supply_gap" for value in labels.values()),
            "blue_ocean_high_intent": sum(value == "blue_ocean_high_intent" for value in labels.values()),
        },
        "prediction_counts": result["summary"],
        "metrics": metrics,
        "method": {
            "status": "INFERRED_FROM_ONE_SAMPLE",
            "runtime_model": "configurable explainable rules",
            "keyword_lookup_used": False,
            "deduplicate_intents_default": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill and evaluate the keyword insight rules against an exported workbook.")
    parser.add_argument("source_file")
    parser.add_argument("--output", default="docs/skills/keyword_insight_distillation_report.json")
    args = parser.parse_args()
    report = build_report(args.source_file)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
