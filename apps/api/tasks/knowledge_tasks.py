from services import qa_document_ingest_service


def execute_document_ingest(doc_id: str, user_id: str) -> None:
    qa_document_ingest_service.process_document(user_id, doc_id)
