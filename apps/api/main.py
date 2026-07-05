import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        if key and not os.environ.get(key):
            os.environ[key] = value.strip().strip('"').strip("'")


_load_env_file()

from routers import admin_runtime, admin_users, agent_blueprints, agent_configs, agent_connectors, agent_runs, agents, artifacts, auth, chat, conversations, datasets, files, qa_chat, qa_knowledge, skills
from services import agent_blueprint_seed_service, agent_blueprint_service, app_sqlite, conversation_store, json_to_sqlite_migrator, security_config_service, service_events

app = FastAPI(title="meizhaiseek-api", version="1.7.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(agent_blueprints.router, prefix="/api", tags=["agent-blueprints"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(agent_configs.router, prefix="/api", tags=["agent-configs"])
app.include_router(agent_connectors.router, prefix="/api", tags=["agent-connectors"])
app.include_router(skills.router, prefix="/api", tags=["skills"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(agent_runs.router, prefix="/api", tags=["agent-runs"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(qa_chat.router, prefix="/api", tags=["qa-chat"])
app.include_router(qa_knowledge.router, prefix="/api", tags=["qa-knowledge"])
app.include_router(artifacts.router, prefix="/api", tags=["artifacts"])
app.include_router(admin_runtime.router, prefix="/api", tags=["admin-runtime"])
app.include_router(admin_users.router, prefix="/api", tags=["admin-users"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meizhaiseek-api"}


@app.on_event("startup")
def startup_storage() -> None:
    app_sqlite.init_app_db()
    app_sqlite.run_migrations()
    if not os.getenv("AUTH_TOKEN_SECRET", "").strip():
        security_config_service.ensure_generated_secret()
    service_events.register_run_updated_handler(conversation_store.sync_run_to_conversation)
    service_events.register_run_updated_handler(agent_blueprint_service.sync_test_run_result)
    agent_blueprint_seed_service.safe_seed_video_blueprint()
    if os.getenv("APP_SQLITE_AUTO_MIGRATE", "true").lower() in {"1", "true", "yes", "on"}:
        try:
            json_to_sqlite_migrator.migrate_json_to_sqlite(force=False)
        except Exception as exc:
            app_sqlite.set_kv("json_migration_last_error", str(exc))


