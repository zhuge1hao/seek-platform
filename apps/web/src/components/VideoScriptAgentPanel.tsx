"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { ArrowUp, Bot, CheckCircle2, ChevronDown, Clipboard, Code2, PlugZap, RotateCcw, Settings2, Upload, XCircle } from "lucide-react";
import { AgentRunStatus } from "@/components/AgentRunStatus";
import { PayloadPreviewModal } from "@/components/PayloadPreviewModal";
import {
  cancelAgentRun,
  createAgentRun,
  getVideoAgentStatus,
  previewAgentRunPayload,
  retryAgentRun,
  uploadVideo,
  type AgentRunStatus as AgentRunStatusType,
  type VideoAgentStatus,
  type VideoWorkflowOptions
} from "@/lib/api";
import { getStoredUser } from "@/lib/auth";

type VideoScriptAgentPanelProps = {
  selectedAgentId?: string | null;
  onOpenAgentSelector: () => void;
  onRunActiveChange?: (running: boolean) => void;
  conversationId?: string | null;
  initialRun?: AgentRunStatusType | null;
  onConversationChange?: (conversationId: string) => void;
  onRunChange?: (run: AgentRunStatusType) => void;
  initialPrompt?: string;
};

type BreakdownMode = "standard_breakdown" | "no_subtitle_breakdown" | "fast_breakdown" | "quality_check";

const VIDEO_SCRIPT_SESSION_ID = "019dd824-f4bb-7273-8ac3-6e19b195ff82";
const allowedExtensions = [".mp4", ".mov", ".webm", ".mkv"];
let cachedStatus: { value: VideoAgentStatus; checkedAt: number } | null = null;
let pendingStatus: Promise<VideoAgentStatus> | null = null;

const modeOptions: Array<{ label: string; value: BreakdownMode; description: string }> = [
  { label: "标准视频拆解", value: "standard_breakdown", description: "镜头、字幕、卖点和证明帧完整拆解" },
  { label: "无字幕视频拆解", value: "no_subtitle_breakdown", description: "优先启用音频转写，适合无字幕素材" },
  { label: "快速拆解", value: "fast_breakdown", description: "降低帧预算，快速获得初版结果" },
  { label: "质检拆解", value: "quality_check", description: "强化质量警告和输出校验" }
];

const defaultWorkflowOptions: VideoWorkflowOptions = {
  shot_cut_strategy: "smart",
  keep_single_frame_proof: true,
  compress_repeated_talking: true,
  subtitle_mode: "white_speech_only",
  subtitle_regions: ["bottom"],
  ignore_packaging_text: true,
  ignore_watermark: true,
  ignore_disclaimer: true,
  no_subtitle_audio_transcribe: false,
  excel_layout: "horizontal_by_shot",
  embed_shot_images: true,
  enable_shot_cache: true,
  enable_ocr_cache: true,
  enable_ocr: true,
  enable_audio_transcript: false,
  enable_quality_check: true,
  export_excel: true,
  export_json: true,
  export_keyframes: true,
  keep_debug_payload: true,
  generate_contact_sheet: true,
  target_frame_budget: 80,
  ocr_threads: 4,
  baseline_image_dir: "",
  previous_excel_path: "",
  output_dir: ""
};

function optionsForMode(mode: BreakdownMode, current: VideoWorkflowOptions): VideoWorkflowOptions {
  const next = { ...current };
  if (mode === "no_subtitle_breakdown") {
    next.subtitle_mode = "audio_transcribe";
    next.no_subtitle_audio_transcribe = true;
    next.enable_audio_transcript = true;
  }
  if (mode === "fast_breakdown") next.target_frame_budget = 40;
  if (mode === "quality_check") next.enable_quality_check = true;
  return next;
}

function statusTone(status?: string) {
  if (status === "connected") return "border-emerald-100 bg-emerald-50 text-emerald-700";
  if (status === "mock") return "border-amber-100 bg-amber-50 text-amber-700";
  return "border-rose-100 bg-rose-50 text-rose-700";
}

function loadVideoAgentStatus(force = false) {
  if (!force && cachedStatus && Date.now() - cachedStatus.checkedAt < 10000) return Promise.resolve(cachedStatus.value);
  if (!force && pendingStatus) return pendingStatus;
  pendingStatus = getVideoAgentStatus()
    .then((result) => {
      cachedStatus = { value: result, checkedAt: Date.now() };
      return result;
    })
    .finally(() => {
      pendingStatus = null;
    });
  return pendingStatus;
}

export function VideoScriptAgentPanel({ selectedAgentId, onOpenAgentSelector, onRunActiveChange, conversationId, initialRun, onConversationChange, onRunChange, initialPrompt }: VideoScriptAgentPanelProps) {
  const canOperate = getStoredUser()?.role !== "viewer";
  const [videoUrl, setVideoUrl] = useState("");
  const [localVideoPath, setLocalVideoPath] = useState("");
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [savedPath, setSavedPath] = useState("");
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<BreakdownMode>("standard_breakdown");
  const [workflowOptions, setWorkflowOptions] = useState<VideoWorkflowOptions>(defaultWorkflowOptions);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [status, setStatus] = useState<VideoAgentStatus | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState("");
  const [showPreflight, setShowPreflight] = useState(false);
  const [payloadPreview, setPayloadPreview] = useState<Record<string, unknown> | null>(null);
  const [previewConnectorId, setPreviewConnectorId] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRunActionLoading, setIsRunActionLoading] = useState(false);
  const [runStatus, setRunStatus] = useState<AgentRunStatusType | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialPrompt !== undefined) setPrompt(initialPrompt);
  }, [initialPrompt]);

  useEffect(() => {
    void testConnection(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!initialRun) return;
    setRunStatus(initialRun);
    setIsSubmitting(initialRun.status === "running");
    setRunning(initialRun.status === "running");
  }, [initialRun?.run_id, initialRun?.status]);

  const setRunning = (running: boolean) => onRunActiveChange?.(running);

  const testConnection = async (showNotice = true) => {
    try {
      const result = await loadVideoAgentStatus(showNotice);
      setStatus(result);
      setLastCheckedAt(new Date().toLocaleTimeString());
      if (showNotice) setNotice(result.message);
      return result;
    } catch (err) {
      const fallback: VideoAgentStatus = { status: "disconnected", base_url: "http://127.0.0.1:8001", reachable: false, message: err instanceof Error ? err.message : "连接状态检测失败", start_hint: "请确认平台后端已启动。" };
      setStatus(fallback);
      return fallback;
    }
  };

  const updateOption = <K extends keyof VideoWorkflowOptions>(key: K, value: VideoWorkflowOptions[K]) => {
    setWorkflowOptions((current) => ({ ...current, [key]: value }));
    setError("");
  };

  const handleModeChange = (nextMode: BreakdownMode) => {
    setMode(nextMode);
    setWorkflowOptions((current) => optionsForMode(nextMode, current));
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !canOperate) return;
    if (!allowedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension))) {
      setError("请上传 mp4、mov、webm 或 mkv 格式的视频文件。");
      return;
    }
    setIsUploading(true);
    setError("");
    setNotice("");
    try {
      const result = await uploadVideo(file);
      setUploadedFileName(result.filename);
      setSavedPath(result.saved_path);
      setNotice(result.message || "视频已上传。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "视频上传失败。");
      setUploadedFileName("");
      setSavedPath("");
    } finally {
      setIsUploading(false);
    }
  };

  const buildPrompt = () => {
    const source = savedPath || localVideoPath.trim() || videoUrl.trim();
    return prompt.trim() || (source ? `请拆解这个视频：${source}` : "");
  };

  const submitRun = async (skipPreflight = false) => {
    if (!canOperate) {
      setError("当前账号为只读角色，不能创建任务。");
      return;
    }
    const sourcePath = savedPath || localVideoPath.trim();
    const sourceUrl = videoUrl.trim();
    const finalPrompt = buildPrompt();
    if (!sourcePath && !sourceUrl && !finalPrompt) {
      setError("请先上传视频、输入本地视频路径或粘贴视频链接。");
      return;
    }
    if (!skipPreflight) {
      const nextStatus = await testConnection(false);
      if (["disconnected", "disabled"].includes(nextStatus.status)) {
        setShowPreflight(true);
        return;
      }
    }
    setShowPreflight(false);
    setIsSubmitting(true);
    setRunning(true);
    setError("");
    setRunStatus(null);
    try {
      const created = await createAgentRun({
        agent_type: "video_script_breakdown",
        mode,
        prompt: finalPrompt,
        video_path: sourcePath || undefined,
        video_url: sourceUrl || undefined,
        session_id: VIDEO_SCRIPT_SESSION_ID,
        workflow_options: { ...workflowOptions, fixed_session_id: VIDEO_SCRIPT_SESSION_ID },
        conversation_id: conversationId || undefined
      });
      onConversationChange?.(created.conversation_id);
      const nextRun = { run_id: created.run_id, conversation_id: created.conversation_id, agent_type: "video_script_breakdown", mode, status: created.status, progress: 10, current_step: created.message, logs: [created.message], result: null, error: null } as AgentRunStatusType;
      setRunStatus(nextRun);
      onRunChange?.(nextRun);
      setNotice(created.message);
    } catch (err) {
      setIsSubmitting(false);
      setRunning(false);
      setError(err instanceof Error ? err.message : "任务创建失败。");
    }
  };

  const handlePreview = async () => {
    setPreviewOpen(true);
    setPreviewLoading(true);
    setPayloadPreview(null);
    setError("");
    try {
      const result = await previewAgentRunPayload({
        agent_type: "video_script_breakdown",
        mode,
        prompt: buildPrompt() || "测试视频拆解 payload",
        video_path: savedPath || localVideoPath.trim() || undefined,
        video_url: videoUrl.trim() || undefined,
        session_id: VIDEO_SCRIPT_SESSION_ID,
        workflow_options: { ...workflowOptions, fixed_session_id: VIDEO_SCRIPT_SESSION_ID }
      });
      setPayloadPreview(result.payload);
      setPreviewConnectorId(result.connector_id || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payload 预览失败。");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleCancelRun = async (runId: string) => {
    setIsRunActionLoading(true);
    setError("");
    try {
      const cancelledRun = await cancelAgentRun(runId);
      setRunStatus(cancelledRun);
      onRunChange?.(cancelledRun);
      setIsSubmitting(false);
      setRunning(false);
      setNotice("任务已取消。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务取消失败。");
    } finally {
      setIsRunActionLoading(false);
    }
  };

  const handleRetryRun = async (runId: string) => {
    setIsRunActionLoading(true);
    setIsSubmitting(true);
    setRunning(true);
    setError("");
    try {
      const retried = await retryAgentRun(runId);
      onConversationChange?.(retried.conversation_id);
      const nextRun = { run_id: retried.run_id, conversation_id: retried.conversation_id, agent_type: "video_script_breakdown", mode, status: retried.status, progress: 10, current_step: retried.message, logs: [retried.message], result: null, error: null } as AgentRunStatusType;
      setRunStatus(nextRun);
      onRunChange?.(nextRun);
      setNotice(retried.message);
    } catch (err) {
      setIsSubmitting(false);
      setRunning(false);
      setError(err instanceof Error ? err.message : "任务重试失败。");
    } finally {
      setIsRunActionLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[960px]">
      <div className="rounded-[24px] border border-violet-100 bg-white px-6 py-6 shadow-soft">
        {!canOperate ? <div className="mb-4 rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-700">当前账号为只读权限，可以查看历史结果，不能创建新任务。</div> : null}

        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold text-violet-700">视频拆解智能体</h3>
            <p className="mt-1 text-sm text-slate-500">上传视频或填写本地路径，调用本地 8001 视频 Agent 生成镜头、字幕、卖点、证明帧和文件结果。</p>
          </div>
          <button className="inline-flex items-center gap-2 rounded-xl border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700" onClick={() => void testConnection()} type="button">
            <PlugZap className="h-4 w-4" />
            测试连接
          </button>
        </div>

        <div className={`rounded-2xl border px-4 py-3 text-sm ${statusTone(status?.status)}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-semibold">{status?.message || "正在检测本地视频拆解 Agent..."}</p>
            <span>{status?.base_url || "http://127.0.0.1:8001"}</span>
          </div>
          <p className="mt-1 text-xs">最近测试：{lastCheckedAt || "-"}{status?.latency_ms !== undefined && status?.latency_ms !== null ? ` · ${status.latency_ms}ms` : ""}</p>
          {status?.error ? <p className="mt-2 text-xs">{status.error}</p> : null}
          {status?.start_hint ? <p className="mt-2 text-xs">{status.start_hint}</p> : null}
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_220px]">
          <label className="block text-sm font-semibold text-slate-800">
            视频链接
            <input className="mt-2 w-full rounded-xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-violet-200" onChange={(event) => setVideoUrl(event.target.value)} placeholder="粘贴视频链接，可选" readOnly={!canOperate} value={videoUrl} />
          </label>
          <button className="mt-7 inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-dashed border-violet-300 bg-violet-50 px-4 text-sm font-semibold text-violet-700 disabled:opacity-60" disabled={isUploading || !canOperate} onClick={() => fileInputRef.current?.click()} type="button">
            <Upload className="h-4 w-4" />
            {isUploading ? "上传中..." : uploadedFileName || "上传视频"}
          </button>
          <input accept="video/mp4,video/quicktime,video/webm,video/x-matroska,.mp4,.mov,.webm,.mkv" className="hidden" onChange={handleFileChange} ref={fileInputRef} type="file" />
        </div>

        {savedPath ? (
          <div className="mt-3 rounded-xl bg-violet-50 px-4 py-3 text-sm text-slate-700">
            <p className="font-semibold text-violet-700">{uploadedFileName}</p>
            <p className="mt-1 break-all font-mono text-xs">{savedPath}</p>
            <button className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-violet-700" onClick={() => void navigator.clipboard?.writeText(savedPath)} type="button"><Clipboard className="h-3 w-3" />复制路径</button>
          </div>
        ) : null}

        <label className="mt-5 block text-sm font-semibold text-slate-800">
          本地视频路径
          <input className="mt-2 w-full rounded-xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-violet-200" onChange={(event) => setLocalVideoPath(event.target.value)} placeholder="例如 E:/videos/demo.mp4，可选" readOnly={!canOperate} value={localVideoPath} />
        </label>

        <label className="mt-5 block text-sm font-semibold text-slate-800">
          任务说明
          <textarea className="mt-2 h-28 w-full resize-none rounded-2xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm leading-6 outline-none focus:bg-white focus:ring-2 focus:ring-violet-200" onChange={(event) => setPrompt(event.target.value)} placeholder="可选。不填时平台会按视频来源自动生成拆解提示。" readOnly={!canOperate} value={prompt} />
        </label>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {modeOptions.map((option) => (
            <button key={option.value} className={`rounded-2xl border p-4 text-left ${mode === option.value ? "border-violet-300 bg-violet-50" : "border-slate-100 bg-white hover:border-violet-200"}`} disabled={!canOperate} onClick={() => handleModeChange(option.value)} type="button">
              <p className="font-semibold text-slate-900">{option.label}</p>
              <p className="mt-1 text-xs text-slate-500">{option.description}</p>
            </button>
          ))}
        </div>

        <div className="mt-5 rounded-2xl border border-violet-100 bg-slate-50/70">
          <button className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-slate-800" onClick={() => setIsAdvancedOpen((current) => !current)} type="button">
            <span className="inline-flex items-center gap-2"><Settings2 className="h-4 w-4 text-violet-600" />高级参数</span>
            <ChevronDown className={["h-4 w-4 transition", isAdvancedOpen ? "rotate-180" : ""].join(" ")} />
          </button>
          {isAdvancedOpen ? (
            <div className="grid gap-3 border-t border-violet-100 p-4 md:grid-cols-2">
              {[
                ["enable_ocr", "启用字幕 OCR"],
                ["enable_audio_transcript", "启用音频转写"],
                ["export_excel", "输出 Excel"],
                ["export_json", "输出 JSON"],
                ["export_keyframes", "输出关键帧"],
                ["enable_quality_check", "启用质量检查"],
                ["keep_debug_payload", "保留 Debug Payload"]
              ].map(([key, label]) => (
                <label key={key} className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm text-slate-700">
                  <input checked={Boolean(workflowOptions[key as keyof VideoWorkflowOptions])} disabled={!canOperate} onChange={(event) => updateOption(key as keyof VideoWorkflowOptions, event.target.checked as never)} type="checkbox" />
                  {label}
                </label>
              ))}
              <label className="text-sm text-slate-700">
                目标帧预算
                <input className="mt-1 w-full rounded-xl border border-violet-100 px-3 py-2" min={1} onChange={(event) => updateOption("target_frame_budget", Number(event.target.value))} type="number" value={workflowOptions.target_frame_budget} />
              </label>
              <label className="text-sm text-slate-700">
                OCR 并发数
                <input className="mt-1 w-full rounded-xl border border-violet-100 px-3 py-2" min={1} onChange={(event) => updateOption("ocr_threads", Number(event.target.value))} type="number" value={workflowOptions.ocr_threads} />
              </label>
              <label className="text-sm text-slate-700 md:col-span-2">
                输出目录（可选）
                <input className="mt-1 w-full rounded-xl border border-violet-100 px-3 py-2" onChange={(event) => updateOption("output_dir", event.target.value)} placeholder="默认写入当前用户 artifact 目录" value={workflowOptions.output_dir || ""} />
              </label>
            </div>
          ) : null}
        </div>

        {error ? <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">{error}</p> : null}
        {notice ? <p className="mt-4 rounded-xl bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700">{notice}</p> : null}

        <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
          <button className={["flex h-12 items-center gap-2 rounded-2xl border px-5 text-lg font-medium transition", selectedAgentId ? "border-violet-200 bg-violet-100 text-violet-700" : "border-slate-200 bg-white text-slate-950"].join(" ")} onClick={onOpenAgentSelector} type="button">
            <Bot className="h-5 w-5" />
            智能体
          </button>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-lg font-medium text-slate-950">meizhaiseek 2.0</span>
            {getStoredUser()?.role === "admin" ? <button className="inline-flex h-11 items-center gap-2 rounded-2xl border border-violet-200 px-4 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={previewLoading} onClick={() => void handlePreview()} type="button"><Code2 className="h-4 w-4" />{previewLoading ? "生成中" : "预览 Payload"}</button> : null}
            <button className="inline-flex h-11 items-center gap-2 rounded-2xl border border-violet-200 px-4 text-sm font-semibold text-violet-700" onClick={() => void testConnection()} type="button"><RotateCcw className="h-4 w-4" />测试连接</button>
            <button aria-label="提交视频拆解任务" className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-600 text-white shadow-sm transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-slate-200" disabled={isSubmitting || isUploading || !canOperate} onClick={() => void submitRun(false)} type="button">
              <ArrowUp className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {showPreflight ? (
        <div className="mt-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">
          <div className="flex items-start gap-3">
            <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">本地视频拆解 Agent 未启动</p>
              <p className="mt-1">当前平台无法连接 {status?.base_url || "http://127.0.0.1:8001"}。请先启动本地视频拆解服务，再重新测试连接或提交任务。</p>
              <p className="mt-1">如果仍要提交，任务会真实失败并记录到任务中心。</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="rounded-full border border-rose-200 bg-white px-3 py-2 font-semibold" onClick={() => void testConnection()} type="button">测试连接</button>
                <button className="rounded-full border border-rose-200 bg-white px-3 py-2 font-semibold" onClick={() => setShowPreflight(false)} type="button">取消</button>
                <button className="rounded-full bg-rose-600 px-3 py-2 font-semibold text-white" onClick={() => void submitRun(true)} type="button">仍然提交</button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {runStatus ? <AgentRunStatus isActionLoading={isRunActionLoading} onCancel={canOperate ? handleCancelRun : undefined} onRetry={canOperate ? handleRetryRun : undefined} run={runStatus} /> : null}
      {previewOpen ? <PayloadPreviewModal connectorId={previewConnectorId} error={!payloadPreview && !previewLoading ? error : undefined} onClose={() => setPreviewOpen(false)} onCopied={() => setNotice("Payload 已复制。")} payload={payloadPreview} /> : null}
    </div>
  );
}
