import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}
OPERATOR = {"user_id": "op", "username": "op", "role": "operator"}


class AgentBlueprintServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        os.environ.pop("TASK_QUEUE_BACKEND", None)
        self.tmp.cleanup()

    def _payload(self, blueprint_id: str = "bp_service") -> dict:
        return {
            "blueprint_id": blueprint_id,
            "agent_id": "video_script_breakdown",
            "name": blueprint_id,
            "display_name": "Service",
            "input_schema": {"fields": [{"field_id": "prompt", "type": "text"}]},
            "methodology": {"steps": [{"step_id": "run", "order": 1, "failure_policy": "stop"}]},
            "prompt_config": {"user_prompt_template": "{{ prompt }}", "variables": [{"name": "prompt"}]},
            "execution_config": {"execution_type": "mock"},
            "output_schema": {"sections": [{"section_id": "summary", "type": "summary"}]},
            "result_ui_config": {"renderer": "generic_structured"},
        }

    def test_publish_rollback_clone_seed_and_run_test_case(self) -> None:
        from fastapi import BackgroundTasks
        from services import agent_blueprint_seed_service, agent_blueprint_service, agent_blueprint_store

        detail = agent_blueprint_service.create_draft(self._payload(), ADMIN)
        blueprint_id = detail["blueprint"]["blueprint_id"]
        case = agent_blueprint_service.save_test_case(blueprint_id, {"name": "case", "input": {"prompt": "hello"}}, OPERATOR)

        agent_blueprint_service.validate(blueprint_id, OPERATOR)
        with patch("services.orchestrator.schedule_run", lambda *_args: None):
            run = agent_blueprint_service.run_test_case(blueprint_id, case["test_case_id"], BackgroundTasks(), OPERATOR)
        agent_blueprint_service.sync_test_run_result({"run_id": run["run"]["run_id"], "status": "completed", "result": {"summary": {"ok": True}}})

        published = agent_blueprint_service.publish(blueprint_id, {}, ADMIN)
        self.assertEqual(published["blueprint"]["status"], "published")
        with self.assertRaises(Exception):
            agent_blueprint_service.update_basic(blueprint_id, {"display_name": "Nope"}, ADMIN)

        v2 = agent_blueprint_service.create_version(blueprint_id, {"change_summary": "second"}, OPERATOR)
        agent_blueprint_service.validate(blueprint_id, OPERATOR)
        with patch("services.orchestrator.schedule_run", lambda *_args: None):
            run_v2 = agent_blueprint_service.run_test_case(blueprint_id, case["test_case_id"], BackgroundTasks(), OPERATOR)
        agent_blueprint_service.sync_test_run_result({"run_id": run_v2["run"]["run_id"], "status": "completed", "result": {"summary": {"ok": True}}})
        agent_blueprint_service.publish(blueprint_id, {"version_id": v2["version_id"]}, ADMIN)
        rolled = agent_blueprint_service.rollback(blueprint_id, {"version_id": published["blueprint"]["published_version_id"]}, ADMIN)
        self.assertEqual(rolled["blueprint"]["status"], "published")
        self.assertTrue(any(item["action"] == "rollback" for item in agent_blueprint_store.list_releases(blueprint_id)))

        cloned = agent_blueprint_service.clone(blueprint_id, {}, OPERATOR)
        self.assertEqual(cloned["blueprint"]["status"], "draft")
        self.assertIsNone(cloned["blueprint"]["published_version_id"])

        self.assertTrue(run_v2["run"]["run_id"].startswith("run_"))
        stored_case = agent_blueprint_store.get_test_case(case["test_case_id"])
        self.assertIsNotNone(stored_case)
        assert stored_case is not None
        self.assertEqual(stored_case["last_result"]["status"], "PASS")

        agent_blueprint_seed_service.safe_seed_video_blueprint()
        agent_blueprint_seed_service.safe_seed_video_blueprint()
        self.assertEqual(len([item for item in agent_blueprint_store.list_blueprints() if item["blueprint_id"] == "bp_video_script_breakdown"]), 1)

    def test_redis_mode_queues_blueprint_test_run_and_worker_starts_agent_run(self) -> None:
        from fastapi import BackgroundTasks
        from services import agent_blueprint_service, agent_blueprint_store

        detail = agent_blueprint_service.create_draft(self._payload("bp_queue"), ADMIN)
        blueprint_id = detail["blueprint"]["blueprint_id"]
        case = agent_blueprint_service.save_test_case(blueprint_id, {"name": "case", "input": {"prompt": "hello"}}, OPERATOR)
        enqueued: list[tuple[str, tuple, str]] = []

        def fake_enqueue(func_path: str, args: tuple, job_id: str, *_, **__) -> dict:
            enqueued.append((func_path, args, job_id))
            return {"backend": "redis", "job_id": job_id}

        os.environ["TASK_QUEUE_BACKEND"] = "redis"
        with patch("tasks.queue.enqueue_call", side_effect=fake_enqueue), patch("services.orchestrator.start_run") as start_run:
            result = agent_blueprint_service.run_test_case(blueprint_id, case["test_case_id"], BackgroundTasks(), OPERATOR)
        self.assertEqual(result["status"], "queued")
        self.assertTrue(str(result["job_id"]).startswith("blueprint-test-"))
        self.assertEqual(enqueued[0][0], "tasks.blueprint_tasks.execute_blueprint_test")
        start_run.assert_not_called()

        test_run = agent_blueprint_store.get_test_run(result["test_run"]["test_run_id"])
        self.assertIsNotNone(test_run)
        assert test_run is not None
        self.assertEqual(test_run["status"], "pending")

        with patch("services.orchestrator.start_run", return_value={"run_id": "run_from_worker"}) as start_run:
            agent_blueprint_service.execute_queued_test_case(test_run["test_run_id"], "op")
        start_run.assert_called_once()
        updated = agent_blueprint_store.get_test_run(test_run["test_run_id"])
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "running")
        self.assertEqual(updated["agent_run_id"], "run_from_worker")


if __name__ == "__main__":
    unittest.main()
