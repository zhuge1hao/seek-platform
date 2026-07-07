from db.config import load_config
from db.repositories.postgres import PostgresAppRepository
from db.repositories.sqlite import SQLiteAppRepository


_REPOSITORY = None


def repository():
    global _REPOSITORY
    if _REPOSITORY is None:
        _REPOSITORY = PostgresAppRepository() if load_config().backend == "postgres" else SQLiteAppRepository()
    return _REPOSITORY
