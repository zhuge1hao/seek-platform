from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path


APPROVED_EXCEPTIONS = {
    ("setuptools", "PYSEC-2026-3447"): "2026-08-17",
    ("transformers", "PYSEC-2025-217"): "2026-09-17",
    ("transformers", "PYSEC-2026-2290"): "2026-09-17",
    ("transformers", "PYSEC-2026-2288"): "2026-09-17",
    ("transformers", "PYSEC-2026-2289"): "2026-09-17",
}


def _read_report(path: Path) -> dict:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"could not decode pip-audit JSON report: {path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_pip_audit_report.py <pip-audit-json>", file=sys.stderr)
        return 2
    today = date.today()
    report = _read_report(Path(sys.argv[1]))
    blocking: list[str] = []
    for dep in report.get("dependencies", []):
        for vuln in dep.get("vulns") or []:
            package_name = str(dep.get("name") or "").lower()
            vuln_id = str(vuln.get("id") or "")
            review_until = APPROVED_EXCEPTIONS.get((package_name, vuln_id))
            if not review_until:
                blocking.append(f"{dep.get('name')} {dep.get('version')} {vuln_id}: new vulnerability")
                continue
            if date.fromisoformat(review_until) < today:
                blocking.append(f"{dep.get('name')} {dep.get('version')} {vuln_id}: exception expired {review_until}")
    if blocking:
        print("\n".join(blocking))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
