"use client";

import { memo, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Clipboard,
  Download,
  FileJson,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Loader2,
  RotateCcw,
  XCircle
} from "lucide-react";
import { downloadArtifact, type AgentRunFile, type AgentRunStatus as AgentRunStatusType } from "@/lib/api";
import { VideoBreakdownResultPanel } from "@/components/VideoBreakdownResultPanel";

type AgentRunStatusProps = {
  run?: AgentRunStatusType | null;
  isActionLoading?: boolean;
  onCancel?: (runId: string) => void;
  onRetry?: (runId: string) => void;
};

const statusLabels: Record<string, string> = {
  running: "执行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消"
};

const summaryLabels: Record<string, string> = {
  mode: "模式",
  video_duration: "视频时长",
  shot_count: "镜头数",
  subtitle_count: "字幕数",
  excel_layout: "Excel 布局",
  quality_status: "质量状态",
  agent_type: "智能体类型",
  agent_name: "智能体",
  prompt_length: "提示词长度",
  selected_skill_count: "技能数量",
  file_preview_count: "文件预览数量"
};

const fileTypeLabels: Record<string, string> = {
  excel: "excel",
  contact_sheet: "联排图",
  json: "json",
  txt: "txt",
  text: "txt",
  image: "image"
};

function FileIcon({ file }: { file: AgentRunFile }) {
  if (file.type === "json") return <FileJson className="h-4 w-4" />;
  if (file.type === "txt" || file.type === "text") return <FileText className="h-4 w-4" />;
  if (file.type === "image" || file.type === "contact_sheet") return <ImageIcon className="h-4 w-4" />;
  return <FileSpreadsheet className="h-4 w-4" />;
}

function shortText(value: unknown, limit = 1000) {
  const output = typeof value === "string" ? value : JSON.stringify(value);
  return output.length > limit ? `${output.slice(0, limit)}...` : output;
}

export const AgentRunStatus = memo(function AgentRunStatus({ run, isActionLoading = false, onCancel, onRetry }: AgentRunStatusProps) {
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [liveRun, setLiveRun] = useState<AgentRunStatusType | null>(run || null);

  useEffect(() => {
    if (run) setLiveRun(run);
  }, [run]);

  if (!liveRun) {
    return <div className="mt-6 rounded-[24px] border border-violet-100 bg-white/95 p-5 text-sm text-slate-500 shadow-soft">正在读取任务状态…</div>;
  }

  const isFailed = liveRun.status === "failed";
  const isCompleted = liveRun.status === "completed";
  const isCancelled = liveRun.status === "cancelled";
  const isRunning = liveRun.status === "running";
  const summaryEntries = Object.entries(liveRun.result?.summary || {}).filter(([, value]) => value !== undefined && value !== null && value !== "");
  const qualityWarnings = (liveRun.result?.quality_warnings || []).slice(0, 20);
  const skillSuggestions = (liveRun.result?.skill_suggestions || []).slice(0, 20);
  const logs = Array.isArray(liveRun.logs) ? liveRun.logs.slice(-50) : [];
  const progress = Number.isFinite(Number(liveRun.progress)) ? Math.max(0, Math.min(Number(liveRun.progress), 100)) : 0;
  const visibleLogs = isLogExpanded ? logs : logs.slice(-3);
  const useVideoPanel = liveRun.agent_type === "video_script_breakdown" && Boolean(liveRun.result);

  const copyPath = async (path: string) => {
    await navigator.clipboard?.writeText(path);
  };

  const openDownload = async (downloadUrl: string, filename: string) => {
    await downloadArtifact(downloadUrl, filename);
  };

  return (
    <div className="mt-6 rounded-[24px] border border-violet-100 bg-white/95 p-5 text-left shadow-soft">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">Agent Run</p>
          <p className="mt-1 font-mono text-sm text-slate-700">{liveRun.run_id}</p>
        </div>
        <span
          className={[
            "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-semibold",
            isFailed || isCancelled ? "bg-rose-50 text-rose-600" : isCompleted ? "bg-emerald-50 text-emerald-600" : "bg-violet-50 text-violet-700"
          ].join(" ")}
        >
          {isFailed ? <AlertCircle className="h-4 w-4" /> : isCancelled ? <XCircle className="h-4 w-4" /> : isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <Loader2 className="h-4 w-4 animate-spin" />}
          {statusLabels[liveRun.status] || liveRun.status}
        </span>
      </div>

      {(isRunning || isFailed || isCancelled) && (onCancel || onRetry) ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {isRunning && onCancel ? (
            <button className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-600 transition hover:bg-rose-100 disabled:opacity-60" disabled={isActionLoading} onClick={() => onCancel(liveRun.run_id)} type="button">
              <XCircle className="h-4 w-4" />
              取消任务
            </button>
          ) : null}
          {(isFailed || isCancelled) && onRetry ? (
            <button className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-2 text-sm font-medium text-violet-700 transition hover:bg-violet-100 disabled:opacity-60" disabled={isActionLoading} onClick={() => onRetry(liveRun.run_id)} type="button">
              <RotateCcw className="h-4 w-4" />
              重试任务
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-slate-700">{liveRun.current_step || "等待任务状态"}</span>
          <span className="font-semibold text-violet-700">{progress}%</span>
        </div>
        <div className="h-2 rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {logs.length ? (
        <div className="mt-5">
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-800">执行日志</p>
            {logs.length > 3 ? (
              <button className="inline-flex items-center gap-1 text-xs font-medium text-violet-700" onClick={() => setIsLogExpanded((value) => !value)} type="button">
                {isLogExpanded ? "收起" : "展开全部"}
                <ChevronDown className={["h-3 w-3 transition", isLogExpanded ? "rotate-180" : ""].join(" ")} />
              </button>
            ) : null}
          </div>
          <div className="max-h-52 space-y-2 overflow-y-auto rounded-2xl bg-slate-50 p-3 text-sm text-slate-600">
            {visibleLogs.map((log, index) => (
              <p key={`${log}-${index}`}>- {log}</p>
            ))}
          </div>
        </div>
      ) : null}

      {liveRun.result_has_more ? <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">完整结果已延迟加载，展开结果区块时再读取。</div> : null}
      {liveRun.error ? <div className="mt-5 rounded-2xl bg-rose-50 p-4 text-sm font-medium leading-6 text-rose-600">{liveRun.error}</div> : null}

      {useVideoPanel ? <VideoBreakdownResultPanel run={liveRun} /> : null}

      {!useVideoPanel && summaryEntries.length ? (
        <div className="mt-5 rounded-2xl border border-violet-100 bg-violet-50/50 p-4">
          <p className="mb-3 text-sm font-semibold text-slate-900">任务摘要</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {summaryEntries.map(([key, value]) => (
              <div key={key} className="rounded-xl bg-white px-3 py-2">
                <p className="text-xs text-slate-500">{summaryLabels[key] || key}</p>
                <p className="mt-1 text-sm font-semibold text-slate-800">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {!useVideoPanel && liveRun.result?.answer ? (
        <div className="mt-5 rounded-2xl border border-slate-100 bg-white p-4 text-sm leading-7 text-slate-700">
          <p className="mb-2 font-semibold text-slate-900">返回结果</p>
          <p className="whitespace-pre-wrap">{liveRun.result.answer}</p>
        </div>
      ) : null}

      {!useVideoPanel && qualityWarnings.length ? (
        <div className="mt-5 rounded-2xl border border-amber-100 bg-amber-50 p-4">
          <p className="mb-2 text-sm font-semibold text-amber-800">质量警告</p>
          <div className="space-y-2 text-sm text-amber-700">{qualityWarnings.map((warning, index) => <p key={`${String(warning)}-${index}`}>- {shortText(warning)}</p>)}</div>
        </div>
      ) : null}

      {!useVideoPanel && skillSuggestions.length ? (
        <div className="mt-5 rounded-2xl border border-sky-100 bg-sky-50 p-4">
          <p className="mb-2 text-sm font-semibold text-sky-800">Skill 沉淀建议</p>
          <div className="space-y-2 text-sm text-sky-700">{skillSuggestions.map((suggestion, index) => <p key={`${suggestion}-${index}`}>- {suggestion}</p>)}</div>
        </div>
      ) : null}

      {!useVideoPanel && liveRun.result?.files?.length ? (
        <div className="mt-5 space-y-3">
          <p className="text-sm font-semibold text-slate-800">结果文件</p>
          {liveRun.result.files.map((file) => (
            <div key={file.path} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-violet-100 bg-violet-50/60 p-3">
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-violet-700">
                  <FileIcon file={file} />
                  {file.name}
                  <span className="rounded-full bg-white px-2 py-0.5 text-xs text-slate-500">{fileTypeLabels[file.type] || file.type || "file"}</span>
                </p>
                <p className="mt-1 break-all font-mono text-xs text-slate-600">{file.path}</p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <button className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white px-3 py-2 text-sm font-medium text-violet-700 transition hover:bg-violet-100" onClick={() => copyPath(file.path)} type="button">
                  <Clipboard className="h-4 w-4" />
                  复制路径
                </button>
                {file.download_url ? (
                  <button className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-violet-700" onClick={() => openDownload(file.download_url!, file.name)} type="button">
                    <Download className="h-4 w-4" />
                    下载
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
});
