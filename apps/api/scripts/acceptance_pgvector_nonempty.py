from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _run(cmd: list[str], env: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, timeout=600, check=False)  # noqa: S603
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "seconds": round(time.time() - started, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="v1.8.6 pgvector non-empty migration acceptance")
    parser.add_argument("--sqlite-path", default="")
    parser.add_argument("--batch-size", default="500")
    parser.add_argument("--json-report", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"acceptance": "pgvector_nonempty", "status": "not_run", "checks": {}, "started_at_epoch": time.time()}
    if not args.sqlite_path:
        report["reason"] = "sqlite_path_required"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        report["reason"] = "sqlite_path_not_found"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    env = os.environ.copy()
    env["RAG_SQLITE_PATH"] = str(sqlite_path)
    script = str(Path("scripts") / "migrate_rag_sqlite_to_pgvector.py")
    commands = {
        "dry_run": [sys.executable, script, "--dry-run", "--json-report"],
        "execute": [sys.executable, script, "--execute", "--batch-size", args.batch_size, "--json-report"],
        "verify": [sys.executable, script, "--verify", "--json-report"],
        "verify_repeat": [sys.executable, script, "--verify", "--json-report"],
    }
    ok = True
    for name, cmd in commands.items():
        result = _run(cmd, env)
        report["checks"][name] = result
        ok = ok and result["returncode"] == 0
        if not ok:
            break
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
