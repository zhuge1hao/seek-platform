"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { ArrowUp, Bot, Code2, Database, Link2, Upload, WandSparkles, X } from "lucide-react";
import { PayloadPreviewModal } from "@/components/PayloadPreviewModal";
import { AgentRunStatus } from "@/components/AgentRunStatus";
import { FilePreviewPanel } from "@/components/FilePreviewPanel";
import { SkillSelectorPanel } from "@/components/SkillSelectorPanel";
import { DatasetPanel } from "@/components/DatasetPanel";
import { ResultPanelErrorBoundary } from "@/components/ResultPanelErrorBoundary";
import { DATASET_AGENT_TYPES, DatasetSelector } from "@/components/DatasetSelector";
import {
  cancelAgentRun,
  createAgentRun,
  previewAgentRunPayload,
  retryAgentRun,
  uploadGenericFile,
  type AgentConfig,
  type AgentRunStatus as AgentRunStatusType,
  type GenericUploadResponse,
  type SkillTemplate
} from "@/lib/api";
import type { AgentDefinition } from "@/lib/agents";
import { getStoredUser } from "@/lib/auth";

type GenericAgentPanelProps = {
  agent: AgentDefinition;
  agentConfig?: AgentConfig;
  promptValue: string;
  onPromptChange: (value: string) => void;
  onOpenAgentSelector: () => void;
  onRunActiveChange?: (running: boolean) => void;
  conversationId?: string | null;
  initialRun?: AgentRunStatusType | null;
  onConversationChange?: (conversationId: string) => void | Promise<void>;
  onRunChange?: (run: AgentRunStatusType) => void;
};

export function GenericAgentPanel({ agent, agentConfig, promptValue, onPromptChange, onOpenAgentSelector, onRunActiveChange, conversationId, initialRun, onConversationChange, onRunChange }: GenericAgentPanelProps) {
  const canOperate = getStoredUser()?.role !== "viewer";
  const [link, setLink] = useState("");
  const [uploads, setUploads] = useState<GenericUploadResponse[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>(agentConfig?.default_skill_ids || []);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);
  const [datasetPanelOpen, setDatasetPanelOpen] = useState(false);
  const [datasetRefreshKey, setDatasetRefreshKey] = useState(0);
  const [isSkillPanelOpen, setIsSkillPanelOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRunActionLoading, setIsRunActionLoading] = useState(false);
  const [runStatus, setRunStatus] = useState<AgentRunStatusType | null>(null);
  const [payloadPreview, setPayloadPreview] = useState<Record<string, unknown> | null>(null);
  const [previewConnectorId, setPreviewConnectorId] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setSelectedSkillIds(agentConfig?.default_skill_ids || []);
  }, [agent.agent_type, agentConfig?.default_skill_ids]);

  const setRunning = (running: boolean) => onRunActiveChange?.(running);

  useEffect(() => {
    if (!initialRun) return;
    setRunStatus(initialRun);
    setIsSubmitting(initialRun.status === "running");
    setRunning(initialRun.status === "running");
  }, [initialRun]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !canOperate) return;
    setIsUploading(true);
    setError("");
    setNotice("");
    try {
      const uploaded = await uploadGenericFile(file);
      setUploads((current) => [...current, uploaded]);
      setNotice(uploaded.message);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "文件上传失败。");
    } finally {
      setIsUploading(false);
    }
  };

  const insertTemplate = (template: SkillTemplate) => {
    const block = `【已选技能模板：${template.name}】\n${template.prompt_template}`;
    onPromptChange(promptValue.trim() ? `${promptValue}\n\n${block}` : block);
    if (!selectedSkillIds.includes(template.id)) {
      setSelectedSkillIds([...selectedSkillIds, template.id]);
    }
  };

  const handleSubmit = async () => {
    if (!canOperate) {
      setError("当前账号为只读角色，不能创建任务。");
      return;
    }
    const trimmedPrompt = promptValue.trim();
    if (!trimmedPrompt) {
      setError("请先输入要发送给智能体的提示词。");
      setNotice("");
      return;
    }

    setIsSubmitting(true);
    setRunning(true);
    setError("");
    setNotice("");
    setRunStatus(null);

    try {
      const created = await createAgentRun({
        agent_type: agent.agent_type,
        mode: agent.default_mode || "default",
        prompt: trimmedPrompt,
        selected_skill_ids: selectedSkillIds,
        link: link.trim() || undefined,
        file_ids: uploads.map((file) => file.file_id),
        dataset_ids: selectedDatasetIds,
        image_paths: uploads.filter((file) => file.file_type === "image").map((file) => file.saved_path),
        workflow_options: agentConfig?.default_options || agent.default_options || {},
        conversation_id: conversationId || undefined
      });
      const nextRun = { run_id: created.run_id, conversation_id: created.conversation_id, agent_type: agent.agent_type, mode: agent.default_mode || "default", status: created.status, progress: 10, current_step: created.message, logs: [created.message], result: null, error: null } as AgentRunStatusType;
      setRunStatus(nextRun);
      onRunChange?.(nextRun);
      await onConversationChange?.(created.conversation_id);
      setNotice(created.message);
    } catch (submitError) {
      setIsSubmitting(false);
      setRunning(false);
      setError(submitError instanceof Error ? submitError.message : "任务创建失败。");
    }
  };

  const handlePreview = async () => {
    setPreviewOpen(true); setPreviewLoading(true); setError(""); setPayloadPreview(null);
    try {
      const result = await previewAgentRunPayload({ agent_type: agent.agent_type, mode: agent.default_mode || "default", prompt: promptValue, selected_skill_ids: selectedSkillIds, link: link.trim() || undefined, file_ids: uploads.map((file) => file.file_id), dataset_ids: selectedDatasetIds, image_paths: uploads.filter((file) => file.file_type === "image").map((file) => file.saved_path), workflow_options: agentConfig?.default_options || agent.default_options || {} });
      setPayloadPreview(result.payload); setPreviewConnectorId(result.connector_id || null);
    } catch (err) { setError(err instanceof Error ? err.message : "Payload 预览失败。"); }
    finally { setPreviewLoading(false); }
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
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : "任务取消失败。");
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
      const nextRun = { run_id: retried.run_id, conversation_id: retried.conversation_id, agent_type: agent.agent_type, mode: agent.default_mode || "default", status: retried.status, progress: 10, current_step: retried.message, logs: [retried.message], result: null, error: null } as AgentRunStatusType;
      setRunStatus(nextRun);
      onRunChange?.(nextRun);
      await onConversationChange?.(retried.conversation_id);
      setNotice(retried.message);
    } catch (retryError) {
      setIsSubmitting(false);
      setRunning(false);
      setError(retryError instanceof Error ? retryError.message : "任务重试失败。");
    } finally {
      setIsRunActionLoading(false);
    }
  };

  const clearPanel = () => {
    setRunStatus(null);
    setError("");
    setNotice("");
    setUploads([]);
    setLink("");
    setSelectedSkillIds(agentConfig?.default_skill_ids || []);
    setSelectedDatasetIds([]);
    onPromptChange("");
    setIsSubmitting(false);
    setRunning(false);
  };

  const acceptedInputs = agentConfig?.accepted_inputs?.length ? agentConfig.accepted_inputs : agent.accepted_inputs;
  const hasSession = Boolean(agentConfig?.session_id);
  const supportsDatasets = DATASET_AGENT_TYPES.has(agent.agent_type);

  return (
    <div className="mx-auto w-full max-w-[880px]">
      <div className="rounded-[24px] border border-violet-100 bg-white px-7 py-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-violet-700">当前智能体</p>
            <h3 className="mt-2 text-2xl font-bold text-slate-950">{agent.name}</h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{agent.description}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {acceptedInputs.map((item) => (
                <span key={item} className="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">{item}</span>
              ))}
              <span className={["rounded-full px-2.5 py-1 text-xs font-medium", hasSession ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-700"].join(" ")}>
                {hasSession ? "已绑定本地 agent session_id" : "未绑定专属 session_id"}
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="rounded-full border border-violet-200 bg-violet-50 px-3 py-2 text-sm font-medium text-violet-700 transition hover:bg-violet-100" onClick={onOpenAgentSelector} type="button">切换智能体</button>
            <button className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50" onClick={clearPanel} type="button">清空当前任务</button>
          </div>
        </div>

        {!hasSession ? (
          <div className="mt-4 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            当前智能体暂未绑定专属本地 agent，将使用默认 local agent 配置或 mock 模式。
          </div>
        ) : null}
        {!canOperate ? <div className="mt-4 rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-700">当前账号为只读权限，无法创建任务。</div> : null}

        <div className="mt-5">
          <label className="text-sm font-semibold text-slate-800" htmlFor="generic-agent-prompt">手动提示词</label>
          <textarea
            className="mt-2 h-40 w-full resize-none rounded-2xl border border-violet-100 bg-violet-50/70 px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-violet-200"
            id="generic-agent-prompt"
            readOnly={!canOperate}
            onChange={(event) => {
              onPromptChange(event.target.value);
              setError("");
            }}
            placeholder={`请描述你希望【${agent.name}】帮你完成的任务...`}
            value={promptValue}
          />
        </div>

        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-violet-100 bg-white px-4 py-3">
          <Link2 className="h-5 w-5 text-violet-500" />
          <input className="min-w-0 flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" onChange={(event) => setLink(event.target.value)} placeholder="可选：粘贴商品链接、竞品链接或资料链接" readOnly={!canOperate} value={link} />
        </div>

        {selectedSkillIds.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedSkillIds.map((id) => (
              <span key={id} className="rounded-full bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700">{id}</span>
            ))}
          </div>
        ) : null}

        {isSkillPanelOpen ? (
          <SkillSelectorPanel
            agentType={agent.agent_type}
            onClose={() => setIsSkillPanelOpen(false)}
            onInsertTemplate={insertTemplate}
            onSelectedSkillIdsChange={setSelectedSkillIds}
            selectedSkillIds={selectedSkillIds}
          />
        ) : null}

        <div className="mt-4">
          <input className="hidden" onChange={handleFileChange} ref={fileInputRef} type="file" />
          <button className="inline-flex items-center gap-2 rounded-2xl border border-dashed border-violet-200 bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700 transition hover:bg-violet-100 disabled:opacity-60" disabled={isUploading || !canOperate} onClick={() => fileInputRef.current?.click()} type="button">
            <Upload className="h-4 w-4" />
            {isUploading ? "正在上传文件..." : "上传文件"}
          </button>
          {uploads.length ? (
            <div className="mt-3 space-y-3">
              {uploads.map((file) => (
                <FilePreviewPanel file={file} key={file.file_id} onRemove={(fileId) => setUploads((current) => current.filter((item) => item.file_id !== fileId))} />
              ))}
            </div>
          ) : null}
        </div>

        {supportsDatasets ? <section className="mt-5 rounded-2xl border border-sky-100 bg-sky-50/40 p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><h4 className="flex items-center gap-2 text-sm font-bold text-slate-900"><Database className="h-4 w-4 text-sky-600" />数据集</h4><p className="mt-1 text-xs text-slate-500">上传并清洗 Excel，或选择已清洗数据集作为任务上下文。</p></div><button className="rounded-xl border border-sky-200 bg-white px-3 py-2 text-sm font-semibold text-sky-700" onClick={() => setDatasetPanelOpen(true)} type="button">打开数据清洗中心</button></div>
          <DatasetSelector onChange={setSelectedDatasetIds} readOnly={!canOperate} refreshKey={datasetRefreshKey} selectedIds={selectedDatasetIds} />
        </section> : null}

        {!canOperate ? <p className="mt-4 rounded-xl bg-amber-50 px-4 py-3 text-sm font-medium text-amber-700">当前账号为只读权限，无法创建任务。</p> : null}
        {error ? <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">{error}</p> : null}
        {notice ? <p className="mt-4 rounded-xl bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700">{notice}</p> : null}

        <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button className="flex h-12 items-center gap-2 rounded-2xl border border-violet-200 bg-violet-100 px-5 text-xl font-medium text-violet-700 transition hover:bg-violet-200" onClick={onOpenAgentSelector} type="button">
              <Bot className="h-6 w-6" />
              智能体
            </button>
            <button className="flex h-12 items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-xl font-medium text-slate-950 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700 disabled:opacity-50" disabled={!canOperate} onClick={() => setIsSkillPanelOpen((value) => !value)} type="button">
              <WandSparkles className="h-6 w-6" />
              技能
            </button>
          </div>

          <div className="flex items-center gap-3">
            <span className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-300 via-sky-200 to-fuchsia-300 shadow-sm" />
            <span className="text-xl font-medium text-slate-950">meizhaiseek 2.0</span>
            <span className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-xl font-semibold text-slate-950 shadow-sm">-{agent.cost}</span>
            {getStoredUser()?.role === "admin" ? <button className="inline-flex h-12 items-center gap-2 rounded-2xl border border-violet-200 px-4 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={previewLoading} onClick={() => void handlePreview()} type="button"><Code2 className="h-4 w-4" />{previewLoading ? "生成中" : "预览 Payload"}</button> : null}
            <button aria-label="提交任务" className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-300 text-white shadow-sm transition hover:bg-violet-600 disabled:cursor-not-allowed disabled:bg-slate-200" data-testid="agent-submit-run" disabled={isSubmitting || isUploading || !canOperate} onClick={handleSubmit} type="button">
              {isSubmitting ? <X className="h-5 w-5" /> : <ArrowUp className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {runStatus ? <ResultPanelErrorBoundary><AgentRunStatus isActionLoading={isRunActionLoading} onCancel={canOperate ? handleCancelRun : undefined} onRetry={canOperate ? handleRetryRun : undefined} run={runStatus} /></ResultPanelErrorBoundary> : null}
      {previewOpen ? <PayloadPreviewModal connectorId={previewConnectorId} error={!payloadPreview && !previewLoading ? error : undefined} onClose={() => setPreviewOpen(false)} onCopied={() => setNotice("Payload 已复制。")} payload={payloadPreview} /> : null}
      {supportsDatasets ? <ResultPanelErrorBoundary><DatasetPanel onChanged={() => setDatasetRefreshKey((value) => value + 1)} onClose={() => setDatasetPanelOpen(false)} open={datasetPanelOpen} readOnly={!canOperate} /></ResultPanelErrorBoundary> : null}
    </div>
  );
}
