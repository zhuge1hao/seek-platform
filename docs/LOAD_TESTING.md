# Load Testing

Locust scenarios live in `load_tests/locustfile.py`.

Level 1:

```powershell
locust -f load_tests/locustfile.py --headless -u 20 -r 5 -t 2m --host http://127.0.0.1:8000
```

Level 2 is optional at 100 users. Level 3 is 500 users and should run only when PostgreSQL, Redis, workers, mock external services, and hardware are ready.

Record real results in `docs/CAPACITY_REPORT_V18.md`. If a level is not executed, write "not executed" with the reason.

## Authenticated User Pool

Do not run 100/500 users through a single admin username. That measures username brute-force protection instead of application capacity.

Create temporary load-test users first, then run:

```powershell
$env:LOCUST_USER_PREFIX='loadtest_'
$env:LOCUST_USER_COUNT='200'
$env:LOCUST_ADMIN_PASSWORD='<temporary-load-test-password>'
locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 5m --host http://127.0.0.1
```

The 2026-07-05 validation used this mode for 100 users. It completed with 0% HTTP errors but failed the latency target; see `docs/CAPACITY_REPORT_V18.md`.
