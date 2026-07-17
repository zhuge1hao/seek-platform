from __future__ import annotations

from datetime import datetime, timezone
import sqlite3


SCHEMA_VERSION = "20260702_v17_agent_blueprints"
SCHEMA_VERSION_V171 = "20260703_v171_blueprint_release_loop"
SCHEMA_VERSION_V18 = "20260705_v18_capacity_foundation"
_ALLOWED_COLUMN_MIGRATIONS = {
    ("agent_runs", "row_version", "INTEGER DEFAULT 1"),
    ("artifacts", "storage_backend", "TEXT DEFAULT 'local'"),
    ("artifacts", "object_key", "TEXT"),
    ("artifacts", "original_filename", "TEXT"),
    ("artifacts", "checksum", "TEXT"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  display_name TEXT,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  is_enabled INTEGER DEFAULT 1,
  auth_version INTEGER DEFAULT 1,
  created_at TEXT,
  updated_at TEXT,
  last_login_at TEXT,
  metadata_json TEXT
  ,row_version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_logs (
  audit_id TEXT PRIMARY KEY,
  user_id TEXT,
  username TEXT,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  detail_json TEXT,
  ip TEXT,
  user_agent TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS qa_conversations (
  conversation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT,
  status TEXT,
  is_archived INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  last_opened_at TEXT,
  metadata_json TEXT
  ,storage_backend TEXT DEFAULT 'local'
  ,object_key TEXT
  ,original_filename TEXT
  ,checksum TEXT
);

CREATE TABLE IF NOT EXISTS qa_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT,
  status TEXT,
  sources_json TEXT,
  warnings_json TEXT,
  error TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS agent_conversations (
  conversation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT,
  type TEXT,
  selected_agent_id TEXT,
  agent_type TEXT,
  latest_run_id TEXT,
  status TEXT,
  is_archived INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  last_opened_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS agent_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT,
  status TEXT,
  run_id TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS agent_runs (
  run_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  conversation_id TEXT,
  agent_id TEXT,
  agent_type TEXT,
  status TEXT,
  mode TEXT,
  input_json TEXT,
  workflow_options_json TEXT,
  result_json TEXT,
  error TEXT,
  artifacts_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS local_agent_connectors (
  connector_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  connector_type TEXT,
  enabled INTEGER DEFAULT 1,
  base_url TEXT,
  command TEXT,
  timeout_seconds INTEGER,
  created_by TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS debug_payloads (
  payload_id TEXT PRIMARY KEY,
  user_id TEXT,
  connector_id TEXT,
  agent_id TEXT,
  request_json TEXT,
  response_json TEXT,
  status TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS files (
  file_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  filename TEXT,
  storage_path TEXT,
  content_type TEXT,
  size_bytes INTEGER,
  source TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  run_id TEXT,
  filename TEXT,
  storage_path TEXT,
  download_url TEXT,
  content_type TEXT,
  size_bytes INTEGER,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS datasets (
  dataset_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT,
  description TEXT,
  source_filename TEXT,
  source_path TEXT,
  status TEXT,
  row_count INTEGER,
  valid_row_count INTEGER,
  excluded_row_count INTEGER,
  columns_json TEXT,
  field_mapping_json TEXT,
  cleaning_rules_json TEXT,
  profile_json TEXT,
  metrics_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS dataset_files (
  file_id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  file_type TEXT,
  filename TEXT,
  storage_path TEXT,
  content_type TEXT,
  size_bytes INTEGER,
  created_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS dataset_jobs (
  job_id TEXT PRIMARY KEY,
  dataset_id TEXT,
  user_id TEXT,
  job_type TEXT,
  status TEXT,
  input_json TEXT,
  result_json TEXT,
  error TEXT,
  created_at TEXT,
  updated_at TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS app_kv (
  key TEXT PRIMARY KEY,
  value_json TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS agent_blueprints (
  blueprint_id TEXT PRIMARY KEY,
  agent_id TEXT,
  name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  category TEXT,
  icon TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  current_version_id TEXT,
  published_version_id TEXT,
  created_by TEXT NOT NULL,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT,
  CHECK(status IN ('draft', 'testing', 'published', 'disabled', 'deprecated'))
);

CREATE TABLE IF NOT EXISTS agent_blueprint_versions (
  version_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  version_name TEXT,
  change_summary TEXT,
  input_schema_json TEXT,
  methodology_json TEXT,
  prompt_config_json TEXT,
  execution_config_json TEXT,
  output_schema_json TEXT,
  result_ui_config_json TEXT,
  acceptance_rules_json TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  is_published INTEGER DEFAULT 0,
  parent_version_id TEXT,
  metadata_json TEXT,
  UNIQUE(blueprint_id, version_number)
);

CREATE TABLE IF NOT EXISTS agent_blueprint_test_cases (
  test_case_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  version_id TEXT,
  name TEXT NOT NULL,
  description TEXT,
  input_json TEXT NOT NULL,
  expected_status TEXT,
  expected_result_rules_json TEXT,
  expected_artifacts_json TEXT,
  max_duration_seconds INTEGER,
  requires_connector INTEGER DEFAULT 0,
  is_enabled INTEGER DEFAULT 1,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_run_id TEXT,
  last_result_json TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS agent_blueprint_releases (
  release_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  action TEXT NOT NULL,
  from_version_id TEXT,
  to_version_id TEXT,
  operator_user_id TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT,
  CHECK(action IN ('publish', 'rollback', 'disable', 'enable', 'deprecate'))
);

CREATE TABLE IF NOT EXISTS agent_blueprint_test_runs (
  test_run_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  test_case_id TEXT NOT NULL,
  agent_run_id TEXT,
  status TEXT NOT NULL,
  expected_status TEXT,
  actual_status TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  duration_ms INTEGER,
  result_summary_json TEXT,
  validation_result_json TEXT,
  missing_result_fields_json TEXT,
  missing_artifacts_json TEXT,
  error_message TEXT,
  created_by TEXT NOT NULL,
  metadata_json TEXT,
  CHECK(status IN ('pending', 'running', 'passed', 'failed', 'error', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS agent_blueprint_validation_results (
  validation_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  is_valid INTEGER NOT NULL,
  error_count INTEGER NOT NULL DEFAULT 0,
  warning_count INTEGER NOT NULL DEFAULT 0,
  errors_json TEXT,
  warnings_json TEXT,
  checked_at TEXT NOT NULL,
  checked_by TEXT NOT NULL,
  validator_version TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT,
  description TEXT
);

CREATE INDEX IF NOT EXISTS idx_qa_conversations_user_updated ON qa_conversations(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_qa_messages_conversation ON qa_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user_updated ON agent_conversations(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_user_created ON agent_runs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation ON agent_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_files_user_created ON files(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_user_created ON artifacts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_debug_payloads_user_created ON debug_payloads(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_datasets_user_updated ON datasets(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_dataset_files_dataset ON dataset_files(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_files_user_created ON dataset_files(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_dataset_jobs_user_created ON dataset_jobs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_dataset_jobs_dataset ON dataset_jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_agent_blueprints_status_updated ON agent_blueprints(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_agent_blueprints_agent_id ON agent_blueprints(agent_id);
CREATE INDEX IF NOT EXISTS idx_blueprint_versions_blueprint_number ON agent_blueprint_versions(blueprint_id, version_number);
CREATE INDEX IF NOT EXISTS idx_blueprint_test_cases_blueprint ON agent_blueprint_test_cases(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_blueprint_releases_blueprint_created ON agent_blueprint_releases(blueprint_id, created_at);
CREATE INDEX IF NOT EXISTS idx_blueprint_test_runs_blueprint_created ON agent_blueprint_test_runs(blueprint_id, started_at);
CREATE INDEX IF NOT EXISTS idx_blueprint_test_runs_test_case_created ON agent_blueprint_test_runs(test_case_id, started_at);
CREATE INDEX IF NOT EXISTS idx_blueprint_test_runs_version_status ON agent_blueprint_test_runs(version_id, status);
CREATE INDEX IF NOT EXISTS idx_blueprint_test_runs_agent_run ON agent_blueprint_test_runs(agent_run_id);
CREATE INDEX IF NOT EXISTS idx_blueprint_validations_blueprint_checked ON agent_blueprint_validation_results(blueprint_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_blueprint_validations_version_checked ON agent_blueprint_validation_results(version_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_blueprint_validations_valid ON agent_blueprint_validation_results(is_valid);
"""


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    _ensure_column(conn, "agent_runs", "row_version", "INTEGER DEFAULT 1")
    _ensure_column(conn, "artifacts", "storage_backend", "TEXT DEFAULT 'local'")
    _ensure_column(conn, "artifacts", "object_key", "TEXT")
    _ensure_column(conn, "artifacts", "original_filename", "TEXT")
    _ensure_column(conn, "artifacts", "checksum", "TEXT")
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        ("20260629_v158_storage_perf_dataset_sqlite", _now(), "v1.5.8 storage performance and dataset sqlite"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (SCHEMA_VERSION, _now(), "v1.7 agent blueprint center"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (SCHEMA_VERSION_V171, _now(), "v1.7.1 blueprint release loop"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (SCHEMA_VERSION_V18, _now(), "v1.8 capacity foundation columns"),
    )
    conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if (table, column, definition) not in _ALLOWED_COLUMN_MIGRATIONS:
        raise ValueError("unsupported sqlite migration column")
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}  # nosec B608: table is validated against _ALLOWED_COLUMN_MIGRATIONS.
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")  # nosec B608: table, column, and definition are validated against _ALLOWED_COLUMN_MIGRATIONS.
