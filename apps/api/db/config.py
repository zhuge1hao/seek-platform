import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    backend: str
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int


def load_config() -> DatabaseConfig:
    return DatabaseConfig(
        backend=os.getenv("APP_DB_BACKEND", "sqlite").lower(),
        url=os.getenv("APP_DATABASE_URL", "postgresql+asyncpg://meizhaiseek:password@localhost:5432/meizhaiseek"),
        pool_size=max(1, int(os.getenv("APP_DB_POOL_SIZE", "20"))),
        max_overflow=max(0, int(os.getenv("APP_DB_MAX_OVERFLOW", "20"))),
        pool_timeout=max(1, int(os.getenv("APP_DB_POOL_TIMEOUT", "30"))),
        pool_recycle=max(1, int(os.getenv("APP_DB_POOL_RECYCLE", "1800"))),
    )
