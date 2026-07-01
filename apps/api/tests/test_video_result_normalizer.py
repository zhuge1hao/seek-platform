import sys
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


if __name__ == "__main__":
    unittest.main()
