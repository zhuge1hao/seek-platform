import type { AgentDefinition } from "@/lib/agents";
import { clearAuthSession, getAuthToken, type AuthUser } from "@/lib/auth";
import { markPerf } from "@/lib/perf";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type VideoUploadResponse = {
  filename: string;
  saved_path: string;
  message: string;
};

export type GenericUploadResponse = {
  file_id: string;
  filename: string;
  file_type: string;
  saved_path: string;
  size?: number;
  created_at?: string;
  preview_status?: string;
  message: string;
};

export type SkillTemplate = {
  id: string;
  name: string;
  agent_types: string[];
  description: string;
  required_inputs: string[];
  prompt_template: string;
  output_format: string;
  enabled: boolean;
};

export type AgentConfig = {
  agent_type: string;
  name: string;
  enabled: boolean;
  workflow: string;
  local_agent_mode?: string;
  session_id?: string;
  payload_style?: string;
  accepted_inputs: string[];
  default_skill_ids: string[];
  output_types: string[];
  default_options: Record<string, unknown>;
  description?: string;
  visible?: boolean;
  connector_id?: string | null;
};

export type AgentConnector = {
  connector_id: string;
  name: string;
  agent_type: string;
  mode: "http" | "cli" | "mock";
  base_url: string;
  endpoint: string;
  cli_command?: string;
  session_id?: string;
  timeout_seconds: number;
  payload_style: "protocol" | "legacy";
  enabled: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
};

export type ConnectorTestResult = { status: string; connector_id: string; mode: string; duration_ms: number; http_status?: number | null; response_preview?: unknown; error?: string | null };
export type VideoAgentStatus = {
  status: "connected" | "disconnected" | "mock" | "disabled" | string;
  connector_id?: string | null;
  name?: string;
  base_url: string;
  reachable: boolean;
  latency_ms?: number | null;
  message: string;
  error?: string | null;
  start_hint?: string;
};
export type PayloadPreviewResult = { connector_id?: string | null; payload: Record<string, unknown> };
export type DebugPayloadSummary = { run_id: string; agent_type?: string; connector_id?: string; mode?: string; status: string; has_request: boolean; has_response: boolean; has_error: boolean; created_at: string };
export type DebugPayloadDetail = { run_id: string; request_exists: boolean; response_exists: boolean; error_exists: boolean; request?: unknown; response?: unknown; error?: string | null; metadata?: Record<string, unknown> };

export type VideoWorkflowOptions = {
  shot_cut_strategy: "smart";
  keep_single_frame_proof: boolean;
  compress_repeated_talking: boolean;
  subtitle_mode: "white_speech_only" | "all_subtitles" | "audio_transcribe";
  subtitle_regions: Array<"bottom" | "top" | "top_bottom" | "wide">;
  ignore_packaging_text: boolean;
  ignore_watermark: boolean;
  ignore_disclaimer: boolean;
  no_subtitle_audio_transcribe: boolean;
  excel_layout: "horizontal_by_shot";
  embed_shot_images: boolean;
  enable_shot_cache: boolean;
  enable_ocr_cache: boolean;
  enable_ocr?: boolean;
  enable_quality_check: boolean;
  enable_audio_transcript?: boolean;
  export_excel?: boolean;
  export_json?: boolean;
  export_keyframes?: boolean;
  keep_debug_payload?: boolean;
  generate_contact_sheet: boolean;
  target_frame_budget: number;
  ocr_threads: number;
  baseline_image_dir: string;
  previous_excel_path: string;
  output_dir?: string;
};

export type AgentRunCreatePayload = {
  agent_type: string;
  mode?: string;
  prompt: string;
  selected_skill_ids?: string[];
  link?: string;
  file_ids?: string[];
  dataset_ids?: string[];
  image_paths?: string[];
  video_path?: string;
  video_url?: string;
  session_id?: string;
  workflow_options?: VideoWorkflowOptions | Record<string, unknown>;
  conversation_id?: string;
};

export type AgentRunCreateResponse = {
  run_id: string;
  conversation_id: string;
  status: string;
  message: string;
};

export type AgentRunFile = {
  name: string;
  path: string;
  type: string;
  download_url?: string;
  artifact_id?: string;
  filename?: string;
  file_type?: string;
  size_bytes?: number;
  created_at?: string;
  preview_url?: string;
};

export type VideoWorkflowStep = {
  step_id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped" | string;
  started_at?: string | null;
  completed_at?: string | null;
  message?: string;
  detail_json?: Record<string, unknown> | null;
};

export type VideoBreakdownResult = {
  summary?: Record<string, string | number | boolean | null | undefined>;
  timeline?: Array<Record<string, unknown>>;
  subtitles?: Array<Record<string, unknown>>;
  selling_points?: Array<Record<string, unknown>>;
  proof_frames?: Array<Record<string, unknown>>;
  quality_warnings?: Array<string | Record<string, unknown>>;
  files?: AgentRunFile[];
  steps?: VideoWorkflowStep[];
  error?: string | null;
};

export type AgentRunResult = {
  answer?: string;
  summary?: Record<string, string | number | boolean | null>;
  files?: AgentRunFile[];
  quality_warnings?: Array<string | Record<string, unknown>>;
  skill_suggestions?: string[];
  raw_response?: unknown;
  timeline?: Array<Record<string, unknown>>;
  subtitles?: Array<Record<string, unknown>>;
  selling_points?: Array<Record<string, unknown>>;
  proof_frames?: Array<Record<string, unknown>>;
  steps?: VideoWorkflowStep[];
  error?: string | null;
};

export type AgentRunStatus = {
  run_id: string;
  agent_type: string;
  mode?: string;
  status: "running" | "completed" | "failed" | "cancelled" | string;
  progress: number;
  current_step: string;
  logs: string[];
  steps?: VideoWorkflowStep[];
  result: AgentRunResult | null;
  error: string | null;
  created_at?: string;
  updated_at?: string;
  conversation_id?: string;
  result_preview?: AgentRunResult | null;
  result_has_more?: boolean;
  artifact_count?: number;
  step_count?: number;
};

export type AgentRunSummaryDetail = AgentRunStatus;

export type AgentRunResultDetail = {
  run_id: string;
  conversation_id?: string;
  agent_type?: string;
  status: string;
  result: AgentRunResult | null;
  error: string | null;
  artifacts?: AgentRunFile[];
  updated_at?: string;
};

export type ConversationMessage = {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  run_id?: string | null;
  status: string;
  result?: AgentRunResult | null;
  result_has_more?: boolean;
  error?: string | null;
  progress?: number;
  current_step?: string;
  logs?: string[];
  created_at: string;
  updated_at: string;
};

export type ConversationSummary = {
  conversation_id: string;
  title: string;
  agent_type: string;
  agent_name: string;
  created_at: string;
  updated_at: string;
  latest_run_id?: string | null;
  status: string;
  summary: string;
  is_archived?: boolean;
};

export type Conversation = ConversationSummary & {
  user_id: string;
  prompt: string;
  run_ids: string[];
  messages: ConversationMessage[];
  last_opened_at: string;
};

export type ConversationDetail = {
  conversation: Conversation;
  latest_run: AgentRunStatus | null;
  runs: AgentRunStatus[];
  warnings: string[];
};

export type AgentRunSummary = {
  run_id: string;
  agent_type: string;
  mode?: string;
  status: string;
  progress: number;
  current_step: string;
  created_at?: string;
  updated_at?: string;
  error: string | null;
};

export type FilePreviewResponse = {
  file_id: string;
  file_type: string;
  filename: string;
  saved_path: string;
  download_url?: string;
  preview: Record<string, unknown>;
};

export type RuntimeHealthResponse = {
  status: string;
  version: string;
  service: string;
  configs_valid: boolean;
  agent_run_store_valid: boolean;
  warnings: string[];
};

export type RuntimeConfigsStatusResponse = {
  status: string;
  configs: Array<{ name: string; path: string; exists: boolean; valid: boolean; schema_version: string; count: number; warnings: string[] }>;
};

export type AuditLog = {
  time: string;
  user_id: string;
  username: string;
  role: string;
  action: string;
  target: string;
  status: string;
  ip: string;
  detail: Record<string, unknown>;
};

export type AdminUser = {
  user_id: string;
  username: string;
  role: "admin" | "operator" | "viewer";
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
  last_login_at?: string | null;
  password_updated_at?: string;
  remark?: string;
};

export type DatasetSummary = {
  dataset_id: string;
  user_id: string;
  name: string;
  source_file_id: string;
  source_path: string;
  file_type: string;
  status: "created" | "mapped" | "cleaned" | "failed" | "deleted" | string;
  row_count: number;
  preview_count: number;
  created_at: string;
  updated_at: string;
  cleaned_at?: string | null;
  profile?: { raw_count?: number; valid_count?: number; excluded_count?: number };
};

export type DatasetPreview = {
  dataset_id: string;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  preview_count: number;
  detected_fields: Array<{ key: string; name: string }>;
  suggested_mapping: Record<string, string>;
};

export type DatasetProfile = Record<string, unknown> & {
  dataset_id: string;
  raw_count: number;
  valid_count: number;
  excluded_count: number;
  valid_rate: number;
  excluded_reason_counts?: Record<string, number>;
  price_band_distribution?: Record<string, number>;
  top_low_cost_high_sales?: Array<Record<string, unknown>>;
  warnings?: string[];
};

export type MappingTemplate = { template_id: string; name: string; mapping: Record<string, string>; updated_at?: string };
export type DatasetCleanResult = { status: string; dataset_id: string; profile: DatasetProfile; metrics_summary: Record<string, unknown>; files: AgentRunFile[] };

export type QASource = {
  chunk_id: string;
  doc_id: string;
  title: string;
  content: string;
  content_preview?: string;
  score: number;
  metadata?: Record<string, unknown>;
};

export type QAConversationSummary = {
  conversation_id: string;
  title: string;
  status: string;
  message_count: number;
  updated_at: string;
};

export type QAConversationMessage = {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  sources?: QASource[];
  warnings?: string[];
  status?: string;
  created_at: string;
};

export type QAConversation = {
  conversation_id: string;
  user_id: string;
  type: "qa_chat";
  title: string;
  status: string;
  messages: QAConversationMessage[];
  created_at: string;
  updated_at: string;
  last_opened_at: string;
  is_archived?: boolean;
};

export type QAHealth = {
  status: string;
  rag_sqlite_exists: boolean;
  rag_chunk_count: number;
  embedding_model_path: string;
  deepseek_model: string;
  deepseek_configured: boolean;
};

export type QAChatPayload = {
  conversation_id?: string | null;
  question: string;
  use_rag?: boolean;
  top_k?: number;
};

export type QAChatResponse = {
  conversation_id: string;
  message_id: string;
  answer: string;
  sources: QASource[];
  warnings: string[];
  model: string;
};

export type QAStreamHandlers = {
  onStart?: (data: { conversation_id: string; message_id: string }) => void;
  onRetrievalStart?: (data: { message?: string }) => void;
  onSources?: (data: { sources: QASource[]; warnings: string[] }) => void;
  onDelta?: (data: { text: string }) => void;
  onDone?: (data: { answer: string; conversation_id: string; message_id: string }) => void;
  onError?: (data: { error: string; conversation_id?: string; message_id?: string }) => void;
};

export type KnowledgeStats = {
  document_count: number;
  chunk_count: number;
  ready_count: number;
  failed_count: number;
  rag_sqlite_exists: boolean;
  embedding_model_path: string;
};

export type KnowledgeDocument = {
  doc_id: string;
  title: string;
  source_type: string;
  status: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type KnowledgeChunkPreview = {
  chunk_id: string;
  chunk_index: number;
  content_preview: string;
  created_at: string;
};

export type KnowledgeUploadResponse = {
  doc_id: string;
  title: string;
  status: string;
  chunk_count: number;
  message: string;
};

export type QAModelStatus = {
  status: string;
  embedding_model: { name: string; configured_path: string; absolute_path: string; exists: boolean; loadable: boolean; dimension: number | null; loaded: boolean; error: string; setup_hint: string };
  rag: { sqlite_path: string; sqlite_exists: boolean; document_count: number; chunk_count: number; ready_document_count: number; failed_document_count: number; current_user_document_count: number; current_user_chunk_count: number };
  deepseek: { configured: boolean; model: string; base_url_configured: boolean; error: string };
  warnings: string[];
};

export type QAEmbeddingTestResult = { status: string; model?: string; dimension?: number; preview?: number[]; text_length?: number; error?: string; setup_hint?: string };
export type QARetrievalTestResult = { status: string; question: string; source_count: number; sources: Array<Pick<QASource, "doc_id" | "chunk_id" | "title" | "score" | "content_preview">>; warnings: string[]; error?: string; setup_hint?: string };
export type QADiagnoseResult = { status: "success" | "warning" | "failed" | string; summary: string; checks: Array<{ key: string; label: string; status: string; message: string; suggestion: string }> };

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  try {
    const response = await globalThis.fetch(input, { ...init, headers });
    if (response.status === 401) {
      clearAuthSession();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") window.location.replace("/login");
    }
    return response;
  } catch {
    throw new Error("后台服务未连接，请确认后端服务已启动。");
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const end = markPerf("api.json", { status: response.status, url: response.url });
  const data = await response.json().catch(() => null);
  end();
  if (!response.ok) {
    const message = response.status === 403 ? "当前账号无权限执行此操作。" : data?.detail || data?.message || `请求失败：${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data as T;
}

export async function getAgents(): Promise<{ agents: AgentDefinition[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agents`);
  return parseJsonResponse<{ agents: AgentDefinition[] }>(response);
}

export async function getVideoAgentStatus(): Promise<VideoAgentStatus> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agents/video-script/status`));
}

export async function getAgentConfigs(): Promise<{ items: AgentConfig[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-configs`);
  return parseJsonResponse<{ items: AgentConfig[] }>(response);
}

export async function updateAgentConfig(agentType: string, payload: Partial<AgentConfig>): Promise<AgentConfig> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-configs/${agentType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<AgentConfig>(response);
}

export async function getAgentConnectors(): Promise<{ items: AgentConnector[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors`));
}

export async function createAgentConnector(payload: AgentConnector): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateAgentConnector(connectorId: string, payload: Partial<AgentConnector>): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function disableAgentConnector(connectorId: string): Promise<AgentConnector> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}`, { method: "DELETE" }));
}

export async function testAgentConnector(connectorId: string, prompt = "测试连接"): Promise<ConnectorTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-connectors/${connectorId}/test`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt, extra_payload: {} }) }));
}

export async function previewAgentRunPayload(payload: AgentRunCreatePayload): Promise<PayloadPreviewResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/agent-runs/preview-payload`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function listDebugPayloads(filters: { limit?: number; agent_type?: string; status?: string } = {}): Promise<{ items: DebugPayloadSummary[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 50) });
  if (filters.agent_type) query.set("agent_type", filters.agent_type);
  if (filters.status) query.set("status", filters.status);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads?${query}`));
}

export async function getDebugPayload(runId: string): Promise<DebugPayloadDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads/${runId}`));
}

export async function replayDebugPayload(runId: string): Promise<{ run_id: string; replay_result: unknown }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/debug-payloads/${runId}/replay`, { method: "POST" }));
}

export async function getSkillTemplates(agentType?: string): Promise<{ items: SkillTemplate[] }> {
  const query = agentType ? `?agent_type=${encodeURIComponent(agentType)}` : "";
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates${query}`);
  return parseJsonResponse<{ items: SkillTemplate[] }>(response);
}

export async function getSkillTemplate(skillId: string): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates/${skillId}`);
  return parseJsonResponse<SkillTemplate>(response);
}

export async function saveSkillTemplate(payload: SkillTemplate): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<SkillTemplate>(response);
}

export async function deleteSkillTemplate(skillId: string): Promise<SkillTemplate> {
  const response = await apiFetch(`${API_BASE_URL}/api/skills/templates/${skillId}`, { method: "DELETE" });
  return parseJsonResponse<SkillTemplate>(response);
}

export async function uploadVideo(file: File): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch(`${API_BASE_URL}/api/files/video/upload`, { method: "POST", body: formData });
  return parseJsonResponse<VideoUploadResponse>(response);
}

export async function uploadGenericFile(file: File): Promise<GenericUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch(`${API_BASE_URL}/api/files/upload`, { method: "POST", body: formData });
  return parseJsonResponse<GenericUploadResponse>(response);
}

export async function getFilePreview(fileId: string): Promise<FilePreviewResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/files/${fileId}/preview`);
  return parseJsonResponse<FilePreviewResponse>(response);
}

export async function listUploadedFiles(extensions = "xlsx,xls,csv", limit = 50): Promise<{ files: GenericUploadResponse[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/files?extensions=${encodeURIComponent(extensions)}&limit=${limit}`));
}

export async function createDatasetFromFile(fileId: string, name?: string): Promise<DatasetSummary & { preview: DatasetPreview; detected_fields: DatasetPreview["detected_fields"]; suggested_mapping: Record<string, string> }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/from-file`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file_id: fileId, name: name || undefined }) }));
}

export async function listDatasets(params: { status?: string; limit?: number } = {}): Promise<{ datasets: DatasetSummary[] }> {
  const query = new URLSearchParams({ limit: String(params.limit || 50) });
  if (params.status) query.set("status", params.status);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets?${query}`));
}

export async function getDataset(datasetId: string): Promise<DatasetSummary> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}`));
}

export async function getDatasetPreview(datasetId: string): Promise<DatasetPreview> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/preview`));
}

export async function getDatasetMappingTemplates(): Promise<{ templates: MappingTemplate[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/mapping-templates`));
}

export async function saveDatasetFieldMapping(datasetId: string, payload: { mapping: Record<string, string>; template_name?: string; save_as_template?: boolean }): Promise<{ status: string; mapping: Record<string, string>; template?: MappingTemplate }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/field-mapping`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function getDatasetFieldMapping(datasetId: string): Promise<{ dataset_id: string; mapping: Record<string, string>; suggested_mapping?: Record<string, string> }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/field-mapping`));
}

export async function cleanDataset(datasetId: string, rules: Record<string, number | boolean>): Promise<DatasetCleanResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/clean`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rules }) }));
}

export async function getDatasetProfile(datasetId: string): Promise<DatasetProfile> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/profile`));
}

export async function getDatasetFiles(datasetId: string): Promise<{ files: AgentRunFile[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}/files`));
}

export async function deleteDataset(datasetId: string): Promise<{ status: string; dataset: DatasetSummary }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/datasets/${datasetId}`, { method: "DELETE" }));
}

export async function createAgentRun(payload: AgentRunCreatePayload): Promise<AgentRunCreateResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseJsonResponse<AgentRunCreateResponse>(response);
}

export async function getAgentRun(runId: string, signal?: AbortSignal): Promise<AgentRunStatus> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}`, { signal });
  return parseJsonResponse<AgentRunStatus>(response);
}

export async function getAgentRunSummary(runId: string, signal?: AbortSignal): Promise<AgentRunSummaryDetail> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/summary`, { signal });
  return parseJsonResponse<AgentRunSummaryDetail>(response);
}

export async function getAgentRunResult(runId: string, signal?: AbortSignal): Promise<AgentRunResultDetail> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/result`, { signal });
  return parseJsonResponse<AgentRunResultDetail>(response);
}

export async function cancelAgentRun(runId: string): Promise<AgentRunStatus> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/cancel`, { method: "POST" });
  return parseJsonResponse<AgentRunStatus>(response);
}

export async function retryAgentRun(runId: string): Promise<AgentRunCreateResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs/${runId}/retry`, { method: "POST" });
  return parseJsonResponse<AgentRunCreateResponse>(response);
}

export async function listAgentRuns(limit = 20): Promise<{ items: AgentRunSummary[] }> {
  const response = await apiFetch(`${API_BASE_URL}/api/agent-runs?limit=${limit}`);
  return parseJsonResponse<{ items: AgentRunSummary[] }>(response);
}

export async function listConversations(params: { limit?: number; include_archived?: boolean } = {}): Promise<{ conversations: ConversationSummary[] }> {
  const query = new URLSearchParams({ limit: String(params.limit || 50), include_archived: String(Boolean(params.include_archived)) });
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations?${query}`));
}

export async function getQAHealth(): Promise<QAHealth> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/health`));
}

export async function getQAModelStatus(params: { include_load_check?: boolean } = {}): Promise<QAModelStatus> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/model-status?include_load_check=${Boolean(params.include_load_check)}`));
}

export async function testQAEmbedding(payload: { text: string }): Promise<QAEmbeddingTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/test-embedding`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function testQARetrieval(payload: { question: string; top_k?: number }): Promise<QARetrievalTestResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/test-retrieval`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function diagnoseQAKnowledge(payload: { question?: string; run_embedding_test?: boolean; run_retrieval_test?: boolean; run_deepseek_config_check?: boolean } = {}): Promise<QADiagnoseResult> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/diagnose`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function listQAConversations(limit = 50): Promise<{ conversations: QAConversationSummary[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations?limit=${limit}`));
}

export async function getQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations/${encodeURIComponent(conversationId)}`));
}

export async function createQAConversation(payload: { title?: string } = {}): Promise<{ conversation_id: string; title: string }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: payload.title || "新对话" })
  }));
}

export async function archiveQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/conversations/${encodeURIComponent(conversationId)}/archive`, { method: "POST" }));
}

export async function deleteQAConversation(conversationId: string): Promise<{ conversation: QAConversation }> {
  return archiveQAConversation(conversationId);
}

export async function qaChat(payload: QAChatPayload): Promise<QAChatResponse> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }));
}

function dispatchQAStreamEvent(eventName: string, dataText: string, handlers: QAStreamHandlers) {
  const data = dataText ? JSON.parse(dataText) : {};
  if (eventName === "start") handlers.onStart?.(data);
  if (eventName === "retrieval_start") handlers.onRetrievalStart?.(data);
  if (eventName === "sources") handlers.onSources?.(data);
  if (eventName === "delta") handlers.onDelta?.(data);
  if (eventName === "done") handlers.onDone?.(data);
  if (eventName === "error") handlers.onError?.(data);
}

function consumeQAStreamBlock(block: string, handlers: QAStreamHandlers) {
  let eventName = "message";
  const dataLines: string[] = [];
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length) dispatchQAStreamEvent(eventName, dataLines.join("\n"), handlers);
}

export async function streamQAChat(payload: QAChatPayload, handlers: QAStreamHandlers, signal?: AbortSignal): Promise<void> {
  if (typeof ReadableStream === "undefined") throw new Error("当前浏览器不支持流式输出。");
  const response = await apiFetch(`${API_BASE_URL}/api/qa/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal
  });
  if (!response.ok) await parseJsonResponse(response);
  if (!response.body) throw new Error("当前浏览器不支持流式输出。");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      if (block.trim()) consumeQAStreamBlock(block, handlers);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) consumeQAStreamBlock(buffer, handlers);
}

export async function getKnowledgeStats(): Promise<KnowledgeStats> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/stats`));
}

export async function listKnowledgeDocuments(): Promise<{ documents: KnowledgeDocument[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents`));
}

export async function getKnowledgeDocument(docId: string): Promise<{ document: KnowledgeDocument; chunks_preview: KnowledgeChunkPreview[] }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}`));
}

export async function uploadKnowledgeDocument(file: File, title?: string): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) formData.append("title", title.trim());
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/upload`, { method: "POST", body: formData }));
}

export async function deleteKnowledgeDocument(docId: string): Promise<{ status: string; document: KnowledgeDocument }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}`, { method: "DELETE" }));
}

export async function reindexKnowledgeDocument(docId: string): Promise<KnowledgeUploadResponse> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/qa/knowledge/documents/${encodeURIComponent(docId)}/reindex`, { method: "POST" }));
}

export async function getConversation(conversationId: string, signal?: AbortSignal): Promise<ConversationDetail> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}`, { signal }));
}

export async function renameConversation(conversationId: string, title: string): Promise<{ conversation: Conversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}/rename`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title })
  }));
}

export async function archiveConversation(conversationId: string): Promise<{ conversation: Conversation }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}/archive`, { method: "POST" }));
}

export async function deleteConversation(conversationId: string): Promise<{ conversation: Conversation }> {
  return archiveConversation(conversationId);
}

export function downloadArtifactUrl(downloadUrl: string): string {
  if (downloadUrl.startsWith("http://") || downloadUrl.startsWith("https://")) {
    return downloadUrl;
  }
  return `${API_BASE_URL}${downloadUrl.startsWith("/") ? "" : "/"}${downloadUrl}`;
}

export async function downloadArtifact(downloadUrl: string, filename = "download"): Promise<void> {
  const response = await apiFetch(downloadArtifactUrl(downloadUrl));
  if (!response.ok) await parseJsonResponse(response);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export async function getArtifactBlobUrl(downloadUrl: string): Promise<string> {
  const response = await apiFetch(downloadArtifactUrl(downloadUrl));
  if (!response.ok) await parseJsonResponse(response);
  return URL.createObjectURL(await response.blob());
}

export async function getRuntimeHealth(): Promise<RuntimeHealthResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/health`);
  return parseJsonResponse<RuntimeHealthResponse>(response);
}

export async function getRuntimeConfigsStatus(): Promise<RuntimeConfigsStatusResponse> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/status`);
  return parseJsonResponse<RuntimeConfigsStatusResponse>(response);
}

export async function backupRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/backup`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function repairRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/repair`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function resetRuntimeConfigs(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/configs/reset`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function clearRuntimeCache(): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE_URL}/api/admin/runtime/cache/clear`, { method: "POST" });
  return parseJsonResponse<Record<string, unknown>>(response);
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiFetch(`${API_BASE_URL}/api/auth/me`);
  return parseJsonResponse<AuthUser>(response);
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<{ status: string; message: string }> {
  const response = await apiFetch(`${API_BASE_URL}/api/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
  });
  return parseJsonResponse<{ status: string; message: string }>(response);
}

export async function getAuditLogs(filters: { action?: string; user?: string; status?: string; start_time?: string; end_time?: string; limit?: number } = {}): Promise<{ logs: AuditLog[] }> {
  const query = new URLSearchParams();
  if (filters.action) query.set("action", filters.action);
  if (filters.status) query.set("status", filters.status);
  if (filters.user) query.set("user", filters.user);
  if (filters.start_time) query.set("start_time", filters.start_time);
  if (filters.end_time) query.set("end_time", filters.end_time);
  query.set("limit", String(filters.limit || 100));
  const response = await apiFetch(`${API_BASE_URL}/api/admin/audit-logs?${query.toString()}`);
  return parseJsonResponse<{ logs: AuditLog[] }>(response);
}

export async function exportAuditLogs(format: "csv" | "jsonl", filters: { action?: string; user?: string; status?: string } = {}): Promise<void> {
  const query = new URLSearchParams({ format, limit: "500" });
  if (filters.action) query.set("action", filters.action);
  if (filters.user) query.set("user", filters.user);
  if (filters.status) query.set("status", filters.status);
  const response = await apiFetch(`${API_BASE_URL}/api/admin/audit-logs/export?${query}`);
  if (!response.ok) await parseJsonResponse(response);
  const objectUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = objectUrl; anchor.download = `audit_logs.${format}`; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(objectUrl);
}

export async function getAdminUsers(filters: { role?: string; enabled?: string; keyword?: string; limit?: number } = {}): Promise<{ users: AdminUser[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 100) });
  if (filters.role) query.set("role", filters.role);
  if (filters.enabled) query.set("enabled", filters.enabled);
  if (filters.keyword) query.set("keyword", filters.keyword);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users?${query}`));
}

export async function createAdminUser(payload: { username: string; password: string; role: string; enabled: boolean; remark: string }): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateAdminUser(userId: string, payload: Partial<Pick<AdminUser, "role" | "enabled" | "remark">>): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function setAdminUserEnabled(userId: string, enabled: boolean): Promise<AdminUser> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/${enabled ? "enable" : "disable"}`, { method: "POST" }));
}

export async function resetAdminUserPassword(userId: string, newPassword: string): Promise<{ status: string; message: string }> {
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/reset-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_password: newPassword }) }));
}

export async function getAdminUserRuns(userId: string, filters: { status?: string; agent_type?: string; limit?: number } = {}): Promise<{ runs: AgentRunSummary[] }> {
  const query = new URLSearchParams({ limit: String(filters.limit || 50) });
  if (filters.status) query.set("status", filters.status);
  if (filters.agent_type) query.set("agent_type", filters.agent_type);
  return parseJsonResponse(await apiFetch(`${API_BASE_URL}/api/admin/users/${userId}/agent-runs?${query}`));
}
