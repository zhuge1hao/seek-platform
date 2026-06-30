import logging
from typing import Any, Callable


RunUpdatedHandler = Callable[[dict[str, Any]], None]

_RUN_UPDATED_HANDLERS: list[RunUpdatedHandler] = []
_LOG = logging.getLogger(__name__)


def register_run_updated_handler(handler: RunUpdatedHandler) -> None:
    if handler not in _RUN_UPDATED_HANDLERS:
        _RUN_UPDATED_HANDLERS.append(handler)


def emit_run_updated(run: dict[str, Any]) -> None:
    for handler in list(_RUN_UPDATED_HANDLERS):
        try:
            handler(run)
        except Exception:
            _LOG.warning("run updated handler failed", exc_info=True)


def clear_handlers_for_test() -> None:
    _RUN_UPDATED_HANDLERS.clear()
