import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class AgentBlueprintPreviewTest(unittest.TestCase):
    def test_preview_is_structural_only(self) -> None:
        from services import agent_blueprint_preview_service
        preview = agent_blueprint_preview_service.input_preview({"fields": [{"field_id": "video_file", "type": "local_path"}]})
        self.assertTrue(preview["preview_only"])
        self.assertIn("不读取本地文件", preview["fields"][0]["warning"])
        result = agent_blueprint_preview_service.result_preview({"sections": [{"section_id": "summary", "type": "summary"}]}, {"renderer": "unknown"})
        self.assertEqual(result["renderer"], "generic_structured")


if __name__ == "__main__":
    unittest.main()
