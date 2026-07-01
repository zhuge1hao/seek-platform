from __future__ import annotations

from typing import Any


MODE_MAP = {
    "standard": "shot_text_excel",
    "standard_breakdown": "shot_text_excel",
    "shot_text_excel": "shot_text_excel",
    "mock": "mock",
}


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def _subtitle_region(options: dict[str, Any]) -> str:
    region = options.get("subtitle_region") or _first(options.get("subtitle_regions")) or "bottom"
    return "top-bottom" if region == "top_bottom" else str(region)


def build_video_agent_run_payload(run: dict[str, Any], workflow_options: dict[str, Any], output_dir: str) -> dict[str, Any]:
    mode = MODE_MAP.get(str(run.get("mode") or "standard").strip(), "shot_text_excel")
    video_file = workflow_options.get("video_file") or run.get("video_file") or run.get("video_path") or ""
    payload: dict[str, Any] = {
        "mode": mode,
        "output_dir": workflow_options.get("output_dir") or output_dir,
        "subtitle_region": _subtitle_region(workflow_options),
        "ocr_workers": int(workflow_options.get("ocr_workers") or workflow_options.get("ocr_threads") or 6),
    }
    if video_file:
        payload["video_file"] = str(video_file)
    if workflow_options.get("baseline_image_dir"):
        payload["reference_img_dir"] = workflow_options["baseline_image_dir"]
    if workflow_options.get("video_link") or run.get("video_url"):
        payload["video_link"] = workflow_options.get("video_link") or run.get("video_url")
    if workflow_options.get("report_mode"):
        payload["report_mode"] = workflow_options["report_mode"]
    if workflow_options.get("force"):
        payload["force"] = True
    if workflow_options.get("no_subtitle") or workflow_options.get("no_subtitle_audio_transcribe"):
        payload["no_subtitle"] = True
    if workflow_options.get("timed_transcript_json"):
        payload["timed_transcript_json"] = workflow_options["timed_transcript_json"]
    if workflow_options.get("sheet_title"):
        payload["sheet_title"] = workflow_options["sheet_title"]
    return payload


if __name__ == "__main__":
    demo = build_video_agent_run_payload(
        {"mode": "standard_breakdown", "video_path": r"E:\USE\codexhome\fenge\videos\test\1.mp4"},
        {"output_dir": r"E:\USE\codexhome\fenge\output\test", "subtitle_regions": ["bottom"], "ocr_threads": 6},
        "",
    )
    assert demo == {
        "mode": "shot_text_excel",
        "output_dir": r"E:\USE\codexhome\fenge\output\test",
        "subtitle_region": "bottom",
        "ocr_workers": 6,
        "video_file": r"E:\USE\codexhome\fenge\videos\test\1.mp4",
    }
