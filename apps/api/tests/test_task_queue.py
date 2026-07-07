import os
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RECORDED: list[tuple[str, str]] = []


def _record_call(name: str, value: str) -> None:
    RECORDED.append((name, value))


class TaskQueueFacadeTest(unittest.TestCase):
    def tearDown(self) -> None:
        RECORDED.clear()
        for key in ("TASK_QUEUE_BACKEND", "RQ_QUEUE_NAME", "RQ_QUEUES"):
            os.environ.pop(key, None)

    def test_inline_enqueue_call_and_health_return_shape(self) -> None:
        from tasks import queue

        os.environ["TASK_QUEUE_BACKEND"] = "inline"
        result = queue.enqueue_call(f"{__name__}._record_call", ("a", "b"), "job-1")
        self.assertEqual(result, {"backend": "inline", "job_id": "job-1"})
        self.assertEqual(RECORDED, [("a", "b")])
        self.assertEqual(queue.health_check()["status"], "ok")

    def test_queue_names_and_routing_hints(self) -> None:
        from tasks import queue

        os.environ["RQ_QUEUES"] = "general,video,dataset"
        self.assertEqual(queue.queue_names(), ["general", "video", "dataset"])
        self.assertEqual(queue._queue_for_call("tasks.dataset_tasks.execute_dataset_job"), "dataset")
        self.assertEqual(queue._queue_for_call("tasks.knowledge_tasks.execute_document_ingest"), "knowledge")
        self.assertEqual(queue._queue_for_call("tasks.blueprint_tasks.execute_blueprint_test"), "blueprint")


if __name__ == "__main__":
    unittest.main()
