import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from fastapi import BackgroundTasks


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class DatasetQueueTest(unittest.TestCase):
    def test_clean_dataset_enqueues_dataset_job_in_redis_mode(self) -> None:
        from routers import datasets

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        dataset = {"dataset_id": "dataset_1", "user_id": "user_a", "status": "mapped"}
        job = {"job_id": "dataset_job_1", "dataset_id": "dataset_1", "user_id": "user_a", "status": "pending"}
        enqueued: dict[str, object] = {}

        def fake_enqueue(func_path: str, args: tuple[object, ...], job_id: str, *_args: object, **_kwargs: object) -> dict[str, object]:
            enqueued.update({"func_path": func_path, "args": args, "job_id": job_id})
            return {"backend": "redis", "job_id": job_id}

        with tempfile.TemporaryDirectory() as tmp:
            mapping_dir = Path(tmp) / "mapping"
            mapping_dir.mkdir(parents=True)
            (mapping_dir / "field_mapping.json").write_text(json.dumps({"mapping": {"name": "name"}}), encoding="utf-8")

            with (
                patch.object(datasets, "_dataset_or_404", return_value=dataset),
                patch.object(datasets.dataset_store, "dataset_dir", return_value=Path(tmp)),
                patch.object(datasets.dataset_store, "create_dataset_job", return_value=job) as create_job,
                patch("tasks.queue.backend", return_value="redis"),
                patch("tasks.queue.enqueue_call", side_effect=fake_enqueue),
                patch.object(datasets.audit_log_service, "write_log"),
                patch.object(datasets.audit_log_service, "client_ip", return_value="127.0.0.1"),
            ):
                result = datasets.clean_dataset("dataset_1", datasets.CleaningRequest(rules={"drop_empty": True}), object(), BackgroundTasks(), user)

        create_job.assert_called_once_with("dataset_1", "user_a", "dataset_clean", {"rules": {"drop_empty": True}})
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["job_id"], "dataset_job_1")
        self.assertEqual(enqueued["func_path"], "tasks.dataset_tasks.execute_dataset_job")
        self.assertEqual(enqueued["args"], ("dataset_job_1", "user_a"))

    def test_export_dataset_enqueues_dataset_job_in_redis_mode(self) -> None:
        from routers import datasets

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        dataset = {"dataset_id": "dataset_1", "user_id": "user_a", "status": "cleaned"}
        job = {"job_id": "dataset_job_2", "dataset_id": "dataset_1", "user_id": "user_a", "status": "pending"}

        with (
            patch.object(datasets, "_dataset_or_404", return_value=dataset),
            patch.object(datasets.dataset_store, "create_dataset_job", return_value=job) as create_job,
            patch("tasks.queue.backend", return_value="redis"),
            patch.object(datasets, "_enqueue_dataset_job") as enqueue,
            patch.object(datasets.audit_log_service, "write_log"),
            patch.object(datasets.audit_log_service, "client_ip", return_value="127.0.0.1"),
        ):
            result = datasets.export_dataset("dataset_1", datasets.ExportRequest(format="xlsx"), object(), BackgroundTasks(), user)

        create_job.assert_called_once_with("dataset_1", "user_a", "dataset_export", {"format": "xlsx"})
        enqueue.assert_called_once_with(job, ANY)
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["job_id"], "dataset_job_2")

    def test_dataset_job_cancel_and_retry(self) -> None:
        from routers import datasets

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        job = {"job_id": "dataset_job_1", "dataset_id": "dataset_1", "user_id": "user_a", "job_type": "dataset_export", "status": "failed", "input": {"format": "xlsx"}}
        retry = {"job_id": "dataset_job_2", "dataset_id": "dataset_1", "user_id": "user_a", "job_type": "dataset_export", "status": "pending", "input": {"format": "xlsx"}}

        with (
            patch.object(datasets.dataset_store, "cancel_dataset_job", return_value={**job, "status": "cancelled"}) as cancel,
            patch.object(datasets.audit_log_service, "write_log"),
            patch.object(datasets.audit_log_service, "client_ip", return_value="127.0.0.1"),
        ):
            cancelled = datasets.cancel_dataset_job("dataset_job_1", object(), user)

        cancel.assert_called_once_with("dataset_job_1", "user_a")
        self.assertEqual(cancelled["status"], "cancelled")

        with (
            patch.object(datasets.dataset_store, "get_dataset_job", return_value=job),
            patch.object(datasets.dataset_store, "retry_dataset_job", return_value=retry) as retry_job,
            patch.object(datasets, "_enqueue_dataset_job") as enqueue,
            patch.object(datasets.audit_log_service, "write_log"),
            patch.object(datasets.audit_log_service, "client_ip", return_value="127.0.0.1"),
        ):
            retried = datasets.retry_dataset_job("dataset_job_1", object(), BackgroundTasks(), user)

        retry_job.assert_called_once_with("dataset_job_1", "user_a")
        enqueue.assert_called_once_with(retry, ANY)
        self.assertEqual(retried["status"], "queued")
        self.assertEqual(retried["job_id"], "dataset_job_2")


if __name__ == "__main__":
    unittest.main()
