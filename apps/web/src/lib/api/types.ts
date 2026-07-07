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
  health_path?: string;
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

export type AgentBlueprintStatus = "draft" | "testing" | "published" | "disabled" | "deprecated" | "unmanaged";
export type AgentBlueprint = {
  blueprint_id: string;
  agent_id?: string | null;
  name: string;
  display_name: string;
  description?: string;
  category?: string;
  icon?: string;
  status: AgentBlueprintStatus;
  current_version_id?: string | null;
  published_version_id?: string | null;
  created_by: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
};
export type AgentBlueprintVersion = {
  version_id: string;
  blueprint_id: string;
  version_number: number;
  version_name?: string;
  change_summary?: string;
  input_schema?: Record<string, unknown>;
  methodology?: Record<string, unknown>;
  prompt_config?: Record<string, unknown>;
  execution_config?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  result_ui_config?: Record<string, unknown>;
  acceptance_rules?: Record<string, unknown>;
  is_published: boolean;
  parent_version_id?: string | null;
  created_by: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};
export type AgentBlueprintTestCase = {
  test_case_id: string;
  blueprint_id: string;
  version_id?: string | null;
  name: string;
  description?: string;
  input: Record<string, unknown>;
  expected_status?: string;
  expected_result_rules?: Record<string, unknown>;
  expected_artifacts?: Record<string, unknown>;
  max_duration_seconds?: number | null;
  requires_connector?: boolean;
  is_enabled?: boolean;
  last_run_id?: string | null;
  last_result?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};
export type AgentBlueprintRelease = {
  release_id: string;
  blueprint_id: string;
  version_id: string;
  action: string;
  from_version_id?: string | null;
  to_version_id?: string | null;
  operator_user_id: string;
  note?: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};
export type AgentBlueprintValidationRecord = {
  validation_id: string;
  blueprint_id: string;
  version_id: string;
  valid: boolean;
  is_valid: boolean;
  error_count: number;
  warning_count: number;
  errors: Array<{ field: string; message: string }>;
  warnings: Array<{ field: string; message: string }>;
  checked_at: string;
  checked_by: string;
  validator_version?: string;
};
export type AgentBlueprintTestRun = {
  test_run_id: string;
  blueprint_id: string;
  version_id: string;
  test_case_id: string;
  agent_run_id?: string | null;
  status: string;
  expected_status?: string;
  actual_status?: string;
  started_at: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  result_summary?: Record<string, unknown>;
  missing_result_fields?: string[];
  missing_artifacts?: string[];
  error_message?: string;
  created_by: string;
};
export type AgentBlueprintReleaseGate = {
  allowed: boolean;
  blocking_errors: Array<{ code: string; message: string }>;
  warnings: Array<{ code: string; message: string }>;
  validation_id?: string | null;
  test_run_id?: string | null;
  version_id?: string;
};
export type AgentBlueprintDiff = {
  blueprint_id: string;
  has_changes: boolean;
  summary: Record<string, number>;
  sections: Array<{ section: string; label: string; has_changes: boolean; changes: Array<Record<string, unknown>> }>;
};
export type AgentBlueprintDetail = {
  blueprint: AgentBlueprint;
  current_version?: AgentBlueprintVersion | null;
  published_version?: AgentBlueprintVersion | null;
  versions: AgentBlueprintVersion[];
  test_cases: AgentBlueprintTestCase[];
  releases: AgentBlueprintRelease[];
};
export type AgentBlueprintValidation = {
  valid: boolean;
  errors: Array<{ field: string; message: string }>;
  warnings: Array<{ field: string; message: string }>;
  validation_id?: string;
  version_id?: string;
};
export type AgentBlueprintRegistrySyncPreview = {
  registry_only: Record<string, unknown>[];
  blueprint_only: AgentBlueprint[];
  matched: Record<string, unknown>[];
  agent_id_conflicts: Record<string, unknown>[];
  disabled_bindings: Record<string, unknown>[];
  deprecated_bindings: Record<string, unknown>[];
};
export type AgentBlueprintRegistrySyncApply = {
  created: AgentBlueprint[];
  skipped: Record<string, unknown>[];
  preview: AgentBlueprintRegistrySyncPreview;
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
  health_status?: string;
  service?: string;
  version?: string;
  model_version?: string;
  project_root?: string;
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
  ocr_workers?: number;
  subtitle_region?: "bottom" | "top" | "top-bottom" | "wide" | "middle" | "center" | "auto" | string;
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
  queue_job_id?: string | null;
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
  legacy_json_fallback_enabled?: boolean;
  configs_valid: boolean;
  agent_run_store_valid: boolean;
  warnings: string[];
};

export type StorageHealthResponse = {
  status: string;
  backend?: string;
  sqlite_path?: string;
  tables?: Record<string, number>;
  legacy_json?: Record<string, unknown>;
  warnings?: string[];
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
