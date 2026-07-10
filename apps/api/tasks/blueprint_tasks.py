from services import agent_blueprint_service


def execute_blueprint_test(test_run_id: str, user_id: str) -> None:
    agent_blueprint_service.execute_queued_test_case(test_run_id, user_id)
