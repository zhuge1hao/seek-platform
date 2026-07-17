from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _run(cmd: list[str], env: dict[str, str], expect: set[int] | None = None) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(cmd, cwd=API_ROOT, env=env, capture_output=True, text=True, timeout=600, check=False)  # noqa: S603
    ok_codes = expect or {0}
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "expected_returncode": sorted(ok_codes),
        "passed": proc.returncode in ok_codes,
        "seconds": round(time.time() - started, 3),
        "json": parsed,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def _embedding(seed: int, dims: int = 512) -> list[float]:
    values = []
    for index in range(dims):
        digest = hashlib.sha256(f"v187:{seed}:{index}".encode("utf-8")).digest()
        values.append(int.from_bytes(digest[:4], "big") / 0xFFFFFFFF)
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / norm, 8) for value in values]


def _create_fixture(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    suffix = uuid.uuid4().hex[:10]
    users = [f"pgv_u_a_{suffix}", f"pgv_u_b_{suffix}"]
    knowledge_bases = [f"kb_a_{suffix}", f"kb_b_{suffix}"]
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE documents (
              doc_id TEXT PRIMARY KEY,
              user_id TEXT,
              title TEXT,
              source_path TEXT,
              source_type TEXT,
              status TEXT,
              chunk_count INTEGER,
              created_at TEXT,
              updated_at TEXT,
              metadata_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks (
              chunk_id TEXT PRIMARY KEY,
              doc_id TEXT,
              user_id TEXT,
              chunk_index INTEGER,
              content TEXT,
              embedding_json TEXT,
              metadata_json TEXT,
              created_at TEXT
            )
            """
        )
        chunk_total = 0
        query_chunk_id = ""
        for doc_index in range(5):
            user_id = users[doc_index % len(users)]
            kb_id = knowledge_bases[doc_index % len(knowledge_bases)]
            doc_id = f"doc_v187_{suffix}_{doc_index}"
            chunk_count = 12
            conn.execute(
                """
                INSERT INTO documents(doc_id, user_id, title, source_path, source_type, status, chunk_count, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    user_id,
                    f"v1.8.7 pgvector fixture {doc_index}",
                    f"fixture://{doc_id}.md",
                    "markdown",
                    "completed",
                    chunk_count,
                    "2026-07-17T00:00:00Z",
                    "2026-07-17T00:00:00Z",
                    json.dumps({"knowledge_base_id": kb_id}, ensure_ascii=False),
                ),
            )
            for chunk_index in range(chunk_count):
                chunk_seed = doc_index * 100 + chunk_index
                chunk_id = f"chunk_v187_{suffix}_{doc_index}_{chunk_index}"
                if doc_index == 0 and chunk_index == 0:
                    query_chunk_id = chunk_id
                conn.execute(
                    """
                    INSERT INTO chunks(chunk_id, doc_id, user_id, chunk_index, content, embedding_json, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        doc_id,
                        user_id,
                        chunk_index,
                        f"fixture content user={user_id} kb={kb_id} doc={doc_index} chunk={chunk_index}",
                        json.dumps(_embedding(chunk_seed)),
                        json.dumps({"knowledge_base_id": kb_id}, ensure_ascii=False),
                        "2026-07-17T00:00:00Z",
                    ),
                )
                chunk_total += 1
    return {
        "sqlite_path": str(path),
        "document_count": 5,
        "chunk_count": chunk_total,
        "embedding_dimensions": 512,
        "users": users,
        "knowledge_base_ids": knowledge_bases,
        "query_user_id": users[0],
        "query_chunk_id": query_chunk_id,
        "query_embedding": _embedding(0),
    }


def _sqlite_chunks(sqlite_path: Path, user_id: str) -> list[dict[str, Any]]:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM chunks WHERE user_id=? ORDER BY chunk_id", (user_id,)).fetchall()
    return [dict(row) for row in rows]


def _cosine(a: list[float], b: list[float]) -> float:
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=False)) / denom


def _sqlite_topk(sqlite_path: Path, user_id: str, query: list[float], limit: int = 5) -> list[dict[str, Any]]:
    scored = []
    for row in _sqlite_chunks(sqlite_path, user_id):
        embedding = [float(item) for item in json.loads(row["embedding_json"])]
        scored.append({"chunk_id": row["chunk_id"], "doc_id": row["doc_id"], "score": _cosine(query, embedding)})
    return sorted(scored, key=lambda item: (-float(item["score"]), str(item["chunk_id"])))[:limit]


def _pgvector_topk(user_id: str, query: list[float], limit: int = 5) -> tuple[list[dict[str, Any]], float]:
    from rag.pgvector_provider import PgVectorRagProvider

    provider = PgVectorRagProvider()
    started = time.time()
    rows = provider.search(user_id, query, limit=limit)
    return rows, round((time.time() - started) * 1000, 3)


def _orphan_check(user_id: str) -> dict[str, Any]:
    from rag.pgvector_provider import PgVectorRagProvider

    provider = PgVectorRagProvider()
    chunks_before = provider.count_chunks(user_id)
    docs = provider.list_documents(user_id)
    deleted_doc = docs[0]["doc_id"] if docs else ""
    deleted_chunks = provider.delete_chunks_by_doc(user_id, deleted_doc) if deleted_doc else 0
    chunks_after = provider.count_chunks(user_id)
    return {
        "deleted_doc_id": deleted_doc,
        "deleted_chunks": deleted_chunks,
        "chunks_before": chunks_before,
        "chunks_after": chunks_after,
        "passed": bool(deleted_doc) and chunks_after == chunks_before - deleted_chunks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.7 pgvector non-empty migration acceptance")
    parser.add_argument("--sqlite-path", default="")
    parser.add_argument("--batch-size", default="500")
    parser.add_argument("--include-resume", action="store_true")
    parser.add_argument("--include-topk", action="store_true")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"acceptance": "pgvector_nonempty", "status": "not_run", "checks": {}, "started_at_epoch": time.time()}
    fixture: dict[str, Any] | None = None
    if args.sqlite_path:
        sqlite_path = Path(args.sqlite_path)
        if not sqlite_path.exists():
            report["reason"] = "sqlite_path_not_found"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
    else:
        sqlite_path = API_ROOT / "runtime" / "acceptance" / "v187_pgvector" / f"fixture_{uuid.uuid4().hex[:10]}.sqlite3"
        fixture = _create_fixture(sqlite_path)
        report["fixture"] = {key: value for key, value in fixture.items() if key != "query_embedding"}

    env = os.environ.copy()
    env["RAG_SQLITE_PATH"] = str(sqlite_path)
    script = str(Path("scripts") / "migrate_rag_sqlite_to_pgvector.py")
    commands: dict[str, tuple[list[str], set[int] | None]] = {
        "dry_run": ([sys.executable, script, "--dry-run", "--json-report"], None),
        "execute": ([sys.executable, script, "--execute", "--batch-size", args.batch_size, "--json-report"], None),
        "verify": ([sys.executable, script, "--verify", "--json-report"], None),
        "execute_repeat": ([sys.executable, script, "--execute", "--batch-size", args.batch_size, "--json-report"], None),
        "verify_repeat": ([sys.executable, script, "--verify", "--json-report"], None),
    }
    ok = True
    for name, (cmd, expect) in commands.items():
        result = _run(cmd, env, expect)
        report["checks"][name] = result
        ok = ok and result["passed"]
        if not ok:
            break

    if ok and args.include_resume:
        checkpoint = API_ROOT / "runtime" / "acceptance" / "v187_pgvector" / f"checkpoint_{uuid.uuid4().hex[:10]}.json"
        partial = _run(
            [sys.executable, script, "--execute", "--resume", "--checkpoint", str(checkpoint), "--stop-after-items", "10", "--json-report"],
            env,
            {3},
        )
        resume = _run(
            [sys.executable, script, "--execute", "--resume", "--checkpoint", str(checkpoint), "--batch-size", args.batch_size, "--json-report"],
            env,
            None,
        )
        verify_after_resume = _run([sys.executable, script, "--verify", "--json-report"], env, None)
        report["checks"]["resume"] = {"partial": partial, "resume": resume, "verify_after_resume": verify_after_resume}
        ok = partial["passed"] and resume["passed"] and verify_after_resume["passed"]

    if ok and args.include_topk and fixture:
        sqlite_results = _sqlite_topk(sqlite_path, str(fixture["query_user_id"]), list(fixture["query_embedding"]))
        pg_results, query_ms = _pgvector_topk(str(fixture["query_user_id"]), list(fixture["query_embedding"]))
        sqlite_ids = [item["chunk_id"] for item in sqlite_results]
        pg_ids = [item["chunk_id"] for item in pg_results]
        topk_passed = sqlite_ids[:5] == pg_ids[:5]
        orphan = _orphan_check(str(fixture["query_user_id"]))
        report["checks"]["topk"] = {
            "sqlite_chunk_ids": sqlite_ids,
            "pgvector_chunk_ids": pg_ids,
            "exact_match": topk_passed,
            "pgvector_query_ms": query_ms,
            "passed": topk_passed,
        }
        report["checks"]["orphan_after_delete"] = orphan
        ok = topk_passed and bool(orphan.get("passed"))

    report["status"] = "passed" if ok else "failed"
    report["completed_at_epoch"] = time.time()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
