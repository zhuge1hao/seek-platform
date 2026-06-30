from workflows.focused_agent_workflow import run_focused_workflow


def run(run_id: str, user_id: str) -> None:
    run_focused_workflow(run_id, user_id, "通用智能体")
