import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import BackgroundTasks, UploadFile


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class QAKnowledgeQueueTest(unittest.TestCase):
    def test_upload_enqueues_document_ingest_in_redis_mode(self) -> None:
        from routers import qa_knowledge

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        document = {"doc_id": "doc_1", "title": "Doc", "status": "pending", "chunk_count": 0}
        upload = UploadFile(filename="doc.txt", file=BytesIO(b"hello"))
        enqueued: dict[str, object] = {}

        def fake_enqueue(func_path: str, args: tuple[object, ...] | list[object], job_id: str, **_kwargs: object) -> dict[str, object]:
            enqueued.update({"func_path": func_path, "args": tuple(args), "job_id": job_id})
            return {"backend": "redis", "job_id": job_id}

        with (
            patch.object(qa_knowledge, "queue_backend", return_value="redis"),
            patch.object(qa_knowledge.qa_document_ingest_service, "prepare_upload", return_value=document),
            patch.object(qa_knowledge, "enqueue_call", side_effect=fake_enqueue),
            patch.object(qa_knowledge.audit_log_service, "write_log"),
            patch.object(qa_knowledge.audit_log_service, "client_ip", return_value="127.0.0.1"),
        ):
            result = qa_knowledge.upload_knowledge_document(object(), BackgroundTasks(), upload, "Doc", user)

        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["job_id"], "document-ingest-doc_1")
        self.assertEqual(enqueued["func_path"], "tasks.knowledge_tasks.execute_document_ingest")
        self.assertEqual(enqueued["args"], ("doc_1", "user_a"))

    def test_reindex_enqueues_existing_document(self) -> None:
        from routers import qa_knowledge

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        detail = {"document": {"doc_id": "doc_1", "title": "Doc", "status": "completed"}}
        enqueued: dict[str, object] = {}

        def fake_enqueue(func_path: str, args: tuple[object, ...], job_id: str, **_kwargs: object) -> dict[str, object]:
            enqueued.update({"func_path": func_path, "args": args, "job_id": job_id})
            return {"backend": "redis", "job_id": job_id}

        with (
            patch.object(qa_knowledge, "queue_backend", return_value="redis"),
            patch.object(qa_knowledge.qa_knowledge_service, "get_document_detail", return_value=detail),
            patch.object(qa_knowledge, "enqueue_call", side_effect=fake_enqueue),
            patch.object(qa_knowledge.audit_log_service, "write_log"),
            patch.object(qa_knowledge.audit_log_service, "client_ip", return_value="127.0.0.1"),
            patch("services.qa_rag_store.update_document_status") as update_status,
        ):
            result = qa_knowledge.reindex_knowledge_document("doc_1", object(), BackgroundTasks(), user)

        self.assertEqual(result, {"doc_id": "doc_1", "status": "pending", "job_id": "document-reindex-doc_1"})
        update_status.assert_called_once_with("user_a", "doc_1", "pending", chunk_count=0)
        self.assertEqual(enqueued["args"], ("doc_1", "user_a"))

    def test_process_document_cancelled_does_not_write_completed(self) -> None:
        from services import qa_document_ingest_service

        document = {"doc_id": "doc_1", "title": "Doc", "status": "cancelled", "chunk_count": 0}
        with (
            patch.object(qa_document_ingest_service.qa_rag_store, "get_document", return_value=document),
            patch.object(qa_document_ingest_service.qa_rag_store, "update_document_status") as update_status,
        ):
            result = qa_document_ingest_service.process_document("user_a", "doc_1")

        self.assertEqual(result["status"], "cancelled")
        update_status.assert_not_called()

    def test_process_document_failure_cleans_chunks_and_marks_failed(self) -> None:
        from services import qa_document_ingest_service

        document = {"doc_id": "doc_1", "title": "Doc", "status": "pending", "source_path": "doc.txt", "chunk_count": 3}
        with (
            patch.object(qa_document_ingest_service.qa_rag_store, "get_document", return_value=document),
            patch.object(qa_document_ingest_service.Path, "exists", return_value=True),
            patch.object(qa_document_ingest_service.qa_document_parser, "parse_document", side_effect=RuntimeError("parse boom")),
            patch.object(qa_document_ingest_service.qa_rag_store, "delete_chunks_by_doc") as delete_chunks,
            patch.object(qa_document_ingest_service.qa_rag_store, "update_document_status") as update_status,
        ):
            with self.assertRaises(qa_document_ingest_service.QAIngestError):
                qa_document_ingest_service.process_document("user_a", "doc_1")

        delete_chunks.assert_called_once_with("user_a", "doc_1")
        update_status.assert_any_call("user_a", "doc_1", "failed", chunk_count=0, metadata={"error": "parse boom"})

    def test_document_detail_uses_request_user_for_isolation(self) -> None:
        from routers import qa_knowledge

        user = {"user_id": "user_a", "username": "user_a", "role": "operator"}
        with patch.object(qa_knowledge.qa_knowledge_service, "get_document_detail", return_value=None) as get_detail:
            with self.assertRaises(Exception):
                qa_knowledge.get_knowledge_document("doc_b", object(), user)

        get_detail.assert_called_once_with("user_a", "doc_b")


if __name__ == "__main__":
    unittest.main()
