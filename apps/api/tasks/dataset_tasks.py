import json
from pathlib import Path

from services import data_cleaning_service, dataset_store


def execute_dataset_job(job_id: str, user_id: str) -> None:
    job = dataset_store.get_dataset_job(job_id, user_id)
    if not job:
        return
    if job["status"] in {"completed", "failed", "cancelled"}:
        return
    dataset_store.update_dataset_job(job_id, {"status": "running"})
    try:
        if job["job_type"] == "dataset_clean":
            _run_clean(job)
        elif job["job_type"] == "dataset_export":
            dataset_store.update_dataset_job(job_id, {"status": "completed", "result": {"files": dataset_store.dataset_files(_dataset(job))}})
        else:
            raise RuntimeError(f"unknown dataset job type: {job['job_type']}")
    except Exception as exc:
        dataset_store.update_dataset_job(job_id, {"status": "failed", "error": str(exc)})


def _dataset(job: dict) -> dict:
    dataset = dataset_store.get_dataset(job["dataset_id"], job["user_id"])
    if not dataset:
        raise RuntimeError("dataset not found")
    return dataset


def _run_clean(job: dict) -> None:
    dataset = _dataset(job)
    mapping_path = dataset_store.dataset_dir(dataset["user_id"], dataset["dataset_id"]) / "mapping" / "field_mapping.json"
    if not mapping_path.exists():
        raise RuntimeError("field mapping is required before cleaning")
    mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8")).get("mapping", {})
    result = data_cleaning_service.clean_dataset(dataset, mapping, job.get("input", {}).get("rules") or {})
    dataset_store.update_dataset_job(job["job_id"], {"status": "completed", "result": result})
