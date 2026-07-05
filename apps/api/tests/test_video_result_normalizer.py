import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class VideoResultNormalizerTest(unittest.TestCase):
    def test_aliases_and_text_response(self) -> None:
        from services.video_breakdown_result_normalizer import normalize_video_breakdown_result

        result = normalize_video_breakdown_result(
            {
                "status": "completed",
                "rawShotCount": 161,
                "optimized_shots": 45,
                "excel_path": r"E:\out\1.xlsx",
                "report_path": r"E:\out\model_optimized_shot_report.json",
            },
            {"video_path": "1.mp4"},
            "",
            [],
        )
        self.assertEqual(result["summary"]["raw_shot_count"], 161)
        self.assertEqual(result["summary"]["model_optimized_shot_count"], 45)
        self.assertTrue(result["summary"]["excel_path"].endswith(".xlsx"))

        text_result = normalize_video_breakdown_result("raw shot count: 12\nmodel optimized shots: 5", {"video_path": "1.mp4"}, "", [])
        self.assertEqual(text_result["summary"]["raw_shot_count"], 12)
        self.assertEqual(text_result["summary"]["model_optimized_shot_count"], 5)
        self.assertIn("normalization_warnings", text_result)

    def test_json_path_missing_report_preview_and_artifacts(self) -> None:
        from services.video_breakdown_result_normalizer import normalize_video_breakdown_result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xlsx = root / "demo_result.xlsx"
            xlsx.write_text("x", encoding="utf-8")
            data_path = root / "response.json"
            data_path.write_text(
                '{"status":"completed","data":{"excel_file":"' + str(xlsx).replace("\\", "\\\\") + '","shot_report":"missing.json"},"raw":"'
                + ("x" * 6000)
                + '"}',
                encoding="utf-8",
            )
            result = normalize_video_breakdown_result(str(data_path), {"video_path": "demo.mp4"}, str(root), [])
            self.assertEqual(result["summary"]["status"], "completed")
            self.assertTrue(result["summary"]["excel_path"].endswith(".xlsx"))
            self.assertIn("shot_report not found", " ".join(result["normalization_warnings"]))
            self.assertTrue(result["raw_preview"].endswith("..."))
            types = {item.get("file_type") or item.get("type") for item in result["files"]}
            self.assertIn("excel", types)
            self.assertIn("json", types)


if __name__ == "__main__":
    unittest.main()
