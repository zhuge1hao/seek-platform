from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from db.config import load_config


_ENGINE: AsyncEngine | None = None
_SESSION: async_sessionmaker | None = None


def engine() -> AsyncEngine:
    global _ENGINE
    if _ENGINE is None:
        config = load_config()
        _ENGINE = create_async_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,
        )
    return _ENGINE


def sessionmaker() -> async_sessionmaker:
    global _SESSION
    if _SESSION is None:
        _SESSION = async_sessionmaker(engine(), expire_on_commit=False)
    return _SESSION


async def health_check() -> dict[str, Any]:
    try:
        from sqlalchemy import text
        async with sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        config = load_config()
        return {"backend": "postgres", "status": "ok", "pool_size": config.pool_size}
    except Exception as exc:
        return {"backend": "postgres", "status": "failed", "error": str(exc)}
