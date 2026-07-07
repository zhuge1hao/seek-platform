from typing import Any

from services import app_sqlite


class SQLiteAppRepository:
    backend = "sqlite"

    def table_count(self, table: str) -> int:
        return app_sqlite.table_count(table)

    def health_check(self) -> dict[str, Any]:
        return app_sqlite.health_check()
