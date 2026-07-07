import os

from rag.pgvector_provider import PgVectorRagProvider
from rag.sqlite_provider import SQLiteRagProvider


def provider():
    return PgVectorRagProvider() if os.getenv("RAG_BACKEND", "sqlite").lower() == "pgvector" else SQLiteRagProvider()
