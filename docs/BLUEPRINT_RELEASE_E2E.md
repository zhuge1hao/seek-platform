# Blueprint Release E2E

v1.7.2 adds an isolated APP SQLite integration test for the full Blueprint release path:

draft -> version -> schema/methodology/execution/output -> test case -> validation -> test run passed -> release gate -> publish v1 -> publish v2 -> rollback v1.

The default test uses the existing `title_writing` registry agent with `execution_type="mock"` and does not call the local 8001 video connector. It also verifies operator/viewer/admin permission boundaries, published-only viewer visibility, and disabled/deprecated Blueprint run blocking.
