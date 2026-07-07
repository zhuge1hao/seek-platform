# RAG Backends

v1.8 introduces a RAG provider facade.

Backends:

- `RAG_BACKEND=sqlite`: existing local RAG SQLite path and default.
- `RAG_BACKEND=pgvector`: production target placeholder.

Current status: SQLite remains the working implementation. pgvector is reported as not migrated and must not be described as complete until document/chunk/vector writes and reads move behind the provider.
