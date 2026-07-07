from services import task_store


def execute_agent_run(run_id: str, user_id: str) -> None:
    run = task_store.get_run(run_id, user_id, include_legacy=False)
    if run and run.get("status") == "cancelled":
        return
    from services.orchestrator import execute_run
    execute_run(run_id, user_id)
