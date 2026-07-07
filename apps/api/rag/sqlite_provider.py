from services import qa_rag_store


class SQLiteRagProvider:
    backend = "sqlite"

    def health_check(self) -> dict:
        try:
            qa_rag_store.init_db()
            return {"backend": self.backend, "status": "ok"}
        except Exception as exc:
            return {"backend": self.backend, "status": "failed", "error": str(exc)}
