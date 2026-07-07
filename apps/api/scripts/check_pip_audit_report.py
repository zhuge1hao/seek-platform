from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path


APPROVED_EXCEPTIONS = {
    "PYSEC-2025-217": "2026-08-06",
    "GHSA-69w3-r845-3855": "2026-08-06",
    "GHSA-29pf-2h5f-8g72": "2026-08-06",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_pip_audit_report.py <pip-audit-json>", file=sys.stderr)
        return 2
    today = date.today()
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    blocking: list[str] = []
    for dep in report.get("dependencies", []):
        for vuln in dep.get("vulns") or []:
            vuln_id = str(vuln.get("id") or "")
            review_until = APPROVED_EXCEPTIONS.get(vuln_id)
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
