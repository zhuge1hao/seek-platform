from typing import Any


class PostgresAppRepository:
    backend = "postgres"

    async def health_check(self) -> dict[str, Any]:
        from db.session import health_check
        return await health_check()

    async def table_count(self, table: str) -> int:
        from sqlalchemy import text
        from db.session import sessionmaker
        async with sessionmaker()() as session:
            row = (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).first()  # nosec B608: table names are repository-controlled schema identifiers, not request input.
            return int(row[0]) if row else 0
