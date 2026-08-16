import os
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

    def test_output_root_named_like_video_includes_evidence_images(self) -> None:
        from services.video_breakdown_result_normalizer import normalize_video_breakdown_result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "1"
            evidence = root / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "Shot_001_000000.jpg").write_bytes(b"jpg")
            result = normalize_video_breakdown_result({"status": "completed", "data": {"output_dir": str(root), "video_file": r"E:\videos\test\1.mp4"}}, {"video_path": r"E:\videos\test\1.mp4"}, str(root), [])
            types = {item.get("file_type") or item.get("type") for item in result["files"]}
            self.assertIn("image", types)
            self.assertEqual(result["summary"]["video_name"], "1.mp4")

    def test_local_agent_output_dir_maps_container_runtime_to_host_root(self) -> None:
        from workflows.video_script_workflow import local_agent_output_dir

        os.environ["LOCAL_VIDEO_AGENT_OUTPUT_MOUNT"] = "/app/apps/api/runtime"
        os.environ["LOCAL_VIDEO_AGENT_OUTPUT_ROOT"] = r"E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\runtime"
        try:
            mapped = local_agent_output_dir(Path("/app/apps/api/runtime/users/alice/artifacts/run1"))
        finally:
            os.environ.pop("LOCAL_VIDEO_AGENT_OUTPUT_MOUNT", None)
            os.environ.pop("LOCAL_VIDEO_AGENT_OUTPUT_ROOT", None)
        self.assertEqual(mapped, r"E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\runtime\users\alice\artifacts\run1")

    def test_local_agent_video_file_maps_container_upload_to_host_root(self) -> None:
        from workflows.video_script_workflow import local_agent_video_file

        os.environ["LOCAL_VIDEO_AGENT_UPLOAD_MOUNT"] = "/app/apps/api/uploads"
        os.environ["LOCAL_VIDEO_AGENT_UPLOAD_ROOT"] = r"E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\uploads"
        try:
            mapped = local_agent_video_file("/app/apps/api/uploads/users/admin/files/demo.mp4")
        finally:
            os.environ.pop("LOCAL_VIDEO_AGENT_UPLOAD_MOUNT", None)
            os.environ.pop("LOCAL_VIDEO_AGENT_UPLOAD_ROOT", None)
        self.assertEqual(mapped, r"E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api\uploads\users\admin\files\demo.mp4")


if __name__ == "__main__":
    unittest.main()
