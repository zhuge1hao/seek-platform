"use client";

import { memo, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Download, Image as ImageIcon, Loader2, XCircle } from "lucide-react";
import { downloadArtifact, getAgentRunResult, getArtifactBlobUrl, type AgentRunFile, type AgentRunResult, type AgentRunStatus, type VideoWorkflowStep } from "@/lib/api";
import { markPerf } from "@/lib/perf";

type Props = { run: AgentRunStatus };
type TabKey = "overview" | "timeline" | "subtitles" | "proof_frames" | "quality_warnings" | "files";

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "overview", label: "概览" },
  { key: "timeline", label: "镜头时间轴" },
  { key: "subtitles", label: "字幕 OCR" },
  { key: "proof_frames", label: "视觉证明帧" },
  { key: "quality_warnings", label: "质量警告" },
  { key: "files", label: "输出文件" },
];

const LIMITS: Record<TabKey, number> = { overview: 0, timeline: 20, subtitles: 30, proof_frames: 20, quality_warnings: 20, files: 30 };

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  const output = typeof value === "object" ? JSON.stringify(value) : String(value);
  return output.length > 5000 ? `${output.slice(0, 5000)}...` : output;
}

function list(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null) : [];
}

function fileForPath(files: AgentRunFile[], path: unknown): AgentRunFile | undefined {
  const target = String(path || "").replace(/\\/g, "/").toLowerCase();
  return target ? files.find((file) => String(file.path || "").replace(/\\/g, "/").toLowerCase() === target) : undefined;
}

function filenameForPath(path: unknown): string {
  return String(path || "download").split(/[\\/]/).pop() || "download";
}

function Empty({ label }: { label: string }) {
  return <p className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-400">{label}</p>;
}

function FullText({ className = "text-sm font-semibold text-slate-800", value }: { className?: string; value: unknown }) {
  const content = text(value);
  return <p className={`mt-1 overflow-x-auto whitespace-nowrap ${className}`} title={content}>{content}</p>;
}

function StepIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  if (status === "failed") return <XCircle className="h-4 w-4 text-rose-600" />;
  if (status === "running") return <Loader2 className="h-4 w-4 animate-spin text-violet-600" />;
  return <span className="h-4 w-4 rounded-full border border-slate-300" />;
}

function ImagePreview({ file }: { file: AgentRunFile }) {
  const [src, setSrc] = useState("");
  useEffect(() => {
    if (!file.download_url || file.file_type !== "image") return;
    let active = true;
    getArtifactBlobUrl(file.download_url).then((url) => { if (active) setSrc(url); }).catch(() => undefined);
    return () => { active = false; if (src) URL.revokeObjectURL(src); };
  }, [file.download_url, file.file_type]);
  return src ? <img alt={file.filename || file.name} className="mt-2 max-h-36 w-full rounded-xl bg-white object-contain" loading="lazy" src={src} /> : null;
}

function LoadMore({ shown, total, onClick }: { shown: number; total: number; onClick: () => void }) {
  if (shown >= total) return null;
  return <button className="mt-3 rounded-full border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700" onClick={onClick} type="button">加载更多 {shown}/{total}</button>;
}

export const VideoBreakdownResultPanel = memo(function VideoBreakdownResultPanel({ run }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [fullResult, setFullResult] = useState<AgentRunResult | null>(null);
  const [visible, setVisible] = useState<Record<TabKey, number>>(LIMITS);

  useEffect(() => {
    setFullResult(null);
    setActiveTab("overview");
    setVisible(LIMITS);
  }, [run.run_id]);

  useEffect(() => {
    if (!run.result_has_more || fullResult) return;
    const controller = new AbortController();
    const end = markPerf("agent.videoResult.fetch", { run_id: run.run_id });
    getAgentRunResult(run.run_id, controller.signal)
      .then((detail) => setFullResult(detail.result))
      .catch((error) => {
        if ((error as Error)?.name !== "AbortError") console.warn("video result fetch failed", error);
      })
      .finally(() => {
        end();
      });
    return () => controller.abort();
  }, [fullResult, run.result_has_more, run.run_id]);

  const result = (fullResult || run.result || {}) as Partial<AgentRunResult>;
  const prepared = useMemo(() => {
    const end = markPerf("agent.videoResult.prepare", { run_id: run.run_id });
    const next = {
      summary: result.summary || {},
      steps: (result.steps || run.steps || []) as VideoWorkflowStep[],
      timeline: list(result.timeline),
      subtitles: list(result.subtitles),
      proofFrames: list(result.proof_frames),
      warnings: result.quality_warnings || [],
      files: result.files || [],
    };
    end();
    return next;
  }, [result, run.run_id, run.steps]);

  const more = (tab: TabKey) => setVisible((current) => ({ ...current, [tab]: current[tab] + LIMITS[tab] }));
  const slice = <T,>(tab: TabKey, items: T[]) => items.slice(0, visible[tab]);

  return (
    <div className="mt-5 space-y-5">
      <section className="rounded-2xl border border-violet-100 bg-violet-50/50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">视频拆解结果</p>
            <p className="mt-1 text-xs text-slate-500">任务状态：{run.status} · 更新时间：{run.updated_at || run.created_at || "-"}</p>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-violet-700">{text(prepared.summary.execution_mode || "real")}</span>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ["视频文件", prepared.summary.video_name],
            ["状态", prepared.summary.status],
            ["raw shot count", prepared.summary.raw_shot_count || prepared.summary.shot_count],
            ["model optimized shots", prepared.summary.model_optimized_shot_count],
            ["Excel columns/images", `${text(prepared.summary.excel_column_count)} / ${text(prepared.summary.excel_image_count)}`],
            ["artifact_count", prepared.summary.artifact_count || prepared.summary.file_count],
            ["Excel path", prepared.summary.excel_path],
            ["shot_report path", prepared.summary.shot_report_path],
          ].map(([label, value]) => {
            const file = label === "Excel path" || label === "shot_report path" ? fileForPath(prepared.files, value) : undefined;
            return <div key={label as string} className="rounded-xl bg-white px-3 py-2">
              <p className="text-xs text-slate-500">{label}</p>
              <FullText value={value} />
              {file?.download_url ? <button aria-label={`下载 ${label}`} className="mt-2 inline-flex items-center gap-1 rounded-lg border border-violet-200 px-2.5 py-1.5 text-xs font-semibold text-violet-700 transition hover:bg-violet-50" onClick={() => void downloadArtifact(file.download_url!, filenameForPath(value))} type="button"><Download className="h-3.5 w-3.5" />下载</button> : null}
            </div>;
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-100 p-4">
        <p className="mb-3 text-sm font-semibold text-slate-900">执行步骤</p>
        {prepared.steps.length ? <div className="grid gap-2 md:grid-cols-2">{prepared.steps.map((step) => (
          <div key={step.step_id} className="flex gap-3 rounded-xl bg-slate-50 p-3">
            <StepIcon status={step.status} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-800">{step.title || step.step_id}</p>
              <FullText className="text-xs text-slate-500" value={`${step.status} · ${step.message || "-"}`} />
            </div>
          </div>
        ))}</div> : <Empty label="暂无执行步骤。" />}
      </section>

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => <button className={`rounded-full px-3 py-2 text-sm font-semibold ${activeTab === tab.key ? "bg-violet-600 text-white" : "bg-slate-100 text-slate-600"}`} key={tab.key} onClick={() => { if (activeTab !== tab.key) setActiveTab(tab.key); }} type="button">{tab.label}</button>)}
      </div>

      {activeTab === "overview" ? <section className="rounded-2xl border border-slate-100 p-4"><p className="text-sm text-slate-500">切换上方标签查看镜头、字幕、证明帧、警告和输出文件。</p></section> : null}

      {activeTab === "timeline" ? <section className="rounded-2xl border border-slate-100 p-4">
        {prepared.timeline.length ? <div className="max-h-80 space-y-2 overflow-y-auto pr-1">{slice("timeline", prepared.timeline).map((shot, index) => <div key={text(shot.shot_id) + index} className="rounded-xl bg-slate-50 p-3 text-sm text-slate-700"><p className="font-semibold text-slate-900">{text(shot.shot_id || `shot_${index + 1}`)} · {text(shot.start_time)} - {text(shot.end_time)}</p><p className="mt-1">{text(shot.action_label || shot.scene_summary || shot.summary)}</p><p className="mt-1 text-xs text-slate-500">{text(shot.notes)}</p></div>)}</div> : <Empty label="暂无镜头时间轴。" />}<LoadMore shown={Math.min(visible.timeline, prepared.timeline.length)} total={prepared.timeline.length} onClick={() => more("timeline")} />
      </section> : null}

      {activeTab === "subtitles" ? <section className="rounded-2xl border border-slate-100 p-4">
        {prepared.subtitles.length ? <div className="max-h-72 space-y-2 overflow-y-auto pr-1">{slice("subtitles", prepared.subtitles).map((item, index) => <div key={index} className="rounded-xl bg-slate-50 p-3 text-sm"><p className="font-mono text-xs text-slate-500">{text(item.start_time)} - {text(item.end_time)}</p><p className="mt-1 text-slate-800">{text(item.text || item)}</p></div>)}</div> : <Empty label="暂无字幕 OCR。" />}<LoadMore shown={Math.min(visible.subtitles, prepared.subtitles.length)} total={prepared.subtitles.length} onClick={() => more("subtitles")} />
      </section> : null}

      {activeTab === "proof_frames" ? <section className="rounded-2xl border border-slate-100 p-4">
        {prepared.proofFrames.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{slice("proof_frames", prepared.proofFrames).map((frame, index) => <div key={index} className="rounded-xl bg-slate-50 p-3 text-sm"><p className="font-semibold text-slate-900">{text(frame.shot_id || `frame_${index + 1}`)}</p><p className="mt-1 text-xs text-slate-500">{text(frame.time)}</p><p className="mt-1 break-all text-slate-700">{text(frame.path || frame.preview_url)}</p></div>)}</div> : <Empty label="暂无视觉证明帧。" />}<LoadMore shown={Math.min(visible.proof_frames, prepared.proofFrames.length)} total={prepared.proofFrames.length} onClick={() => more("proof_frames")} />
      </section> : null}

      {activeTab === "quality_warnings" ? <section className="rounded-2xl border border-slate-100 p-4">
        {prepared.warnings.length ? <div className="space-y-2">{slice("quality_warnings", prepared.warnings).map((warning, index) => <p key={index} className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-700">{text(warning)}</p>)}</div> : <Empty label="暂无质量警告。" />}<LoadMore shown={Math.min(visible.quality_warnings, prepared.warnings.length)} total={prepared.warnings.length} onClick={() => more("quality_warnings")} />
      </section> : null}

      {activeTab === "files" ? <section className="rounded-2xl border border-slate-100 p-4">
        {prepared.files.length ? <div className="max-h-80 space-y-2 overflow-y-auto pr-1">{slice("files", prepared.files).map((file: AgentRunFile) => <div key={file.artifact_id || file.path} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-3"><div className="min-w-0 text-sm"><p className="flex items-center gap-2 font-semibold text-slate-900"><ImageIcon className="h-4 w-4" />{file.filename || file.name}</p><p className="mt-1 break-all font-mono text-xs text-slate-500">{file.path}</p><p className="mt-1 text-xs text-slate-500">{file.file_type || file.type} · {file.size_bytes ? `${file.size_bytes} bytes` : "-"} · {file.created_at || "-"}</p><ImagePreview file={file} /></div>{file.download_url ? <button className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-3 py-2 text-sm font-medium text-white" onClick={() => void downloadArtifact(file.download_url!, file.filename || file.name)} type="button"><Download className="h-4 w-4" />下载</button> : null}</div>)}</div> : <Empty label="暂无输出文件。" />}<LoadMore shown={Math.min(visible.files, prepared.files.length)} total={prepared.files.length} onClick={() => more("files")} />
      </section> : null}
    </div>
  );
});
