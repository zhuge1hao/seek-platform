from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_bandit_report.py <bandit-json>", file=sys.stderr)
        return 2
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    blocking = [item for item in report.get("results", []) if item.get("issue_severity") in {"HIGH", "MEDIUM"}]
    if blocking:
        for item in blocking:
            print(f"{item.get('issue_severity')} {item.get('test_id')} {item.get('filename')}:{item.get('line_number')} {item.get('issue_text')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
