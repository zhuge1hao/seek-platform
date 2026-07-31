# v1.8.10 SQL And Typing Review

Status: passed on 2026-07-31.

The SQL safety scan passed with 31 findings, 28 medium, 3 low, and 0 high. The baseline did not increase. The aspirational target of 28 was not pursued because the remaining findings are pre-existing dynamic SQL and changing unrelated stores would expand this cycle's risk.

Global `follow_imports = "skip"` remains unchanged. Module-level `normal` overrides for `sqlalchemy`, `sqlalchemy.*`, `psycopg`, and `psycopg.*` passed across 201 checked source files without adding ignores or reducing coverage.
