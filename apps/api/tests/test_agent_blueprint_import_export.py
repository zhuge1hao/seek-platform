import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ADMIN = {"user_id": "admin", "username": "admin", "role": "admin"}


class AgentBlueprintImportExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        from services import app_sqlite
        app_sqlite._INIT_DONE = False

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_export_redacts_and_import_conflict_creates_new_id(self) -> None:
        from services import agent_blueprint_import_export, agent_blueprint_service, agent_blueprint_store

        agent_blueprint_service.create_draft({
            "blueprint_id": "bp_export",
            "name": "export",
            "display_name": "Export",
            "prompt_config": {"user_prompt_template": "x", "variables": []},
            "execution_config": {"execution_type": "mock"},
            "result_ui_config": {"renderer": "generic_structured"},
        }, ADMIN)
        exported = agent_blueprint_import_export.export_blueprint("bp_export", ADMIN)
        self.assertEqual(exported["platform"], "meizhaiseek")
        redacted = agent_blueprint_import_export.redact({"nested": {"api_key": "secret-value"}})
        self.assertNotIn("secret-value", str(redacted))
        self.assertIn("***REDACTED***", str(redacted))

        exported["version"]["prompt_config"] = {"user_prompt_template": "x", "variables": []}
        preview = agent_blueprint_import_export.preview_import(exported, ADMIN)
        self.assertTrue(preview["conflict"])
        self.assertEqual(preview["import_blueprint_id"], "bp_export_import")

        imported = agent_blueprint_import_export.import_blueprint(exported, ADMIN)
        self.assertEqual(imported["blueprint"]["blueprint_id"], "bp_export_import")
        stored_blueprint = agent_blueprint_store.get_blueprint("bp_export_import")
        self.assertIsNotNone(stored_blueprint)
        assert stored_blueprint is not None
        self.assertEqual(stored_blueprint["status"], "draft")


if __name__ == "__main__":
    unittest.main()
