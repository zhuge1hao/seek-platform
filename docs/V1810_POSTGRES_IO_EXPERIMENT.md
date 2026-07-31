# v1.8.10 PostgreSQL IO Experiment

Status: not_run.

Compare synchronous_commit on/off using test-only session or override settings, then restore on. Compare API workers 1/2/4 while keeping total possible pool connections below PostgreSQL max_connections with operating reserve.

