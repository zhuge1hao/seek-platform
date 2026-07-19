"""Scan dynamic SQL sites and enforce a checked baseline."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
SCAN_ROOT = ROOT / "apps" / "api"
SQL_RE = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|PRAGMA)\b", re.IGNORECASE)
FSTRING_RE = re.compile(r"(^|[=(,\s])f[\"']")
EXCLUDED_PARTS = {"runtime", "__pycache__", ".venv", "models", "tests"}
USER_INPUT_HINTS = {
    "args",
    "body",
    "column",
    "field",
    "filter",
    "form",
    "order",
    "payload",
    "query",
    "request",
    "sort",
    "table",
    "where",
}
WHITELIST_HINTS = {
    "fixed",
    "parameterized",
    "repository-controlled",
    "schema",
    "selected",
    "trusted",
    "whitelist",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    function: str | None
    test_id: str
    has_nosec: bool
    has_whitelist: bool
    contains_user_input_hint: bool
    risk: str
    snippet_hash: str
    snippet: str
    recommendation: str


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _function_ranges(source: str) -> list[tuple[int, int, str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            ranges.append((node.lineno, int(end), node.name))
    return ranges


def _function_for_line(ranges: Iterable[tuple[int, int, str]], line_no: int) -> str | None:
    matches = [name for start, end, name in ranges if start <= line_no <= end]
    return matches[-1] if matches else None


def _is_dynamic_sql(line: str) -> bool:
    if "# nosec" in line and "B608" in line:
        return True
    if "execute(" not in line and "text(" not in line:
        return False
    return bool(SQL_RE.search(line) and (FSTRING_RE.search(line) or "execute(f" in line or "text(f" in line))


def _risk(line: str, has_nosec: bool, has_whitelist: bool, user_hint: bool) -> str:
    if not has_nosec and user_hint:
        return "high"
    if not has_nosec:
        return "medium"
    if has_whitelist and not user_hint:
        return "low"
    return "medium"


def scan_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8", errors="ignore")
    ranges = _function_ranges(source)
    findings: list[Finding] = []
    for index, line in enumerate(source.splitlines(), start=1):
        if not _is_dynamic_sql(line):
            continue
        lowered = line.lower()
        has_nosec = "# nosec" in lowered
        has_whitelist = any(hint in lowered for hint in WHITELIST_HINTS)
        user_hint = any(hint in lowered for hint in USER_INPUT_HINTS)
        test_id = "B608" if "b608" in lowered or SQL_RE.search(line) else "dynamic-sql"
        risk = _risk(line, has_nosec, has_whitelist, user_hint)
        snippet = line.strip()
        findings.append(
            Finding(
                path=_relative(path),
                line=index,
                function=_function_for_line(ranges, index),
                test_id=test_id,
                has_nosec=has_nosec,
                has_whitelist=has_whitelist,
                contains_user_input_hint=user_hint,
                risk=risk,
                snippet_hash=hashlib.sha256(snippet.encode("utf-8")).hexdigest()[:16],
                snippet=snippet,
                recommendation=(
                    "Replace structural SQL string interpolation with SQLAlchemy Core or a local identifier whitelist."
                    if risk == "high"
                    else "Keep bound values parameterized and document the fixed identifier whitelist."
                ),
            )
        )
    return findings


def iter_python_files(root: Path = SCAN_ROOT) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def scan() -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_python_files():
        findings.extend(scan_file(path))
    return findings


def _key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item["path"]), str(item.get("snippet_hash") or ""))


def _load_baseline(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("findings", data if isinstance(data, list) else []))


def build_report(findings: list[Finding]) -> dict[str, Any]:
    finding_dicts = [asdict(item) for item in findings]
    counts_by_risk: dict[str, int] = {}
    for item in findings:
        counts_by_risk[item.risk] = counts_by_risk.get(item.risk, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scanner": "scan_sql_safety.py",
        "finding_count": len(findings),
        "counts_by_risk": counts_by_risk,
        "findings": finding_dicts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan dynamic SQL sites and compare against a baseline.")
    parser.add_argument("--json-report", action="store_true", help="Print JSON report.")
    parser.add_argument("--fail-on-new", action="store_true", help="Fail when findings are not in the baseline.")
    parser.add_argument("--baseline", type=Path, help="Existing baseline JSON.")
    args = parser.parse_args(argv)

    findings = scan()
    report = build_report(findings)
    blocking: list[dict[str, object]] = []
    if args.fail_on_new:
        if not args.baseline:
            parser.error("--fail-on-new requires --baseline")
        baseline_keys = {_key(item) for item in _load_baseline(args.baseline)}
        blocking = [item for item in report["findings"] if _key(item) not in baseline_keys]
        if blocking:
            report["blocking_new_findings"] = blocking

    if args.json_report or not args.fail_on_new:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if blocking:
        print(f"SQL safety gate failed: {len(blocking)} new findings", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
