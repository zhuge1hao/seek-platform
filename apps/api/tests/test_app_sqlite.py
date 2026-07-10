import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeRawConnection:
    def __init__(self) -> None:
        self.closed = False
        self.commits = 0
        self.rollbacks = 0
        self.cursor = FakeRawCursor()

    def execute(self, *_args):
        return self.cursor

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


class FakeRawCursor:
    rowcount = 1

    def __init__(self) -> None:
        self.closed = False

    def fetchone(self):
        return {"ok": True}

    def fetchall(self):
        return [{"ok": True}]

    def close(self) -> None:
        self.closed = True


class AppSQLiteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["APP_DB_BACKEND"] = "sqlite"
        os.environ["APP_SQLITE_PATH"] = str(Path(self.tmp.name) / "app.sqlite3")
        os.environ["MEIZHAISEEK_ADMIN_INITIAL_PASSWORD"] = "AdminTest123!"
        os.environ["AUTH_TOKEN_SECRET"] = "sqlite-test-secret-123456789012345"
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        app_sqlite._PG_POOL = None

    def tearDown(self) -> None:
        from services import app_sqlite

        app_sqlite._INIT_DONE = False
        app_sqlite._PG_POOL = None
        for key in ("APP_DB_BACKEND", "APP_SQLITE_PATH", "APP_DB_POOL_SIZE", "APP_DB_MAX_OVERFLOW", "APP_DB_POOL_TIMEOUT", "APP_DB_POOL_RECYCLE"):
            os.environ.pop(key, None)
        self.tmp.cleanup()

    def test_sqlite_connection_and_table_count_whitelist(self) -> None:
        from services import app_sqlite, user_store

        user_store.load_users()
        with app_sqlite.connection() as conn:
            conn.execute("INSERT OR IGNORE INTO app_kv(key, value_json, updated_at) VALUES (?, ?, ?)", ("k", "{}", "now"))
        self.assertGreaterEqual(app_sqlite.table_count("users"), 1)
        self.assertRaises(ValueError, app_sqlite.table_count, "users; DROP TABLE users")
        self.assertRaises(ValueError, app_sqlite.table_count, "../users")

    def test_sqlite_multithread_connections_close_without_leak(self) -> None:
        from services import app_sqlite, user_store

        user_store.load_users()
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(5):
                    self.assertGreaterEqual(app_sqlite.table_count("users"), 1)
            except Exception as exc:  # pragma: no cover - failure path is asserted below
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])

    def test_postgres_pool_acquire_release_recycle_and_overflow(self) -> None:
        from services import app_sqlite

        os.environ["APP_DB_POOL_SIZE"] = "1"
        os.environ["APP_DB_MAX_OVERFLOW"] = "1"
        raw: list[FakeRawConnection] = []
        pool = app_sqlite._PostgresPool()

        def make_conn() -> FakeRawConnection:
            conn = FakeRawConnection()
            raw.append(conn)
            return conn

        with patch.object(pool, "_new_connection", side_effect=make_conn):
            first = pool.acquire()
            second = pool.acquire()
            self.assertEqual(pool._created, 2)
            first.close()
            second.close()
            third = pool.acquire()
            third.close()
        self.assertLessEqual(pool._pool.qsize(), 1)
        self.assertTrue(any(conn.closed for conn in raw))

    def test_postgres_pool_lifo_cursor_transactions_and_recycle(self) -> None:
        from services import app_sqlite

        os.environ["APP_DB_POOL_SIZE"] = "2"
        os.environ["APP_DB_MAX_OVERFLOW"] = "0"
        os.environ["APP_DB_POOL_RECYCLE"] = "0"
        raw: list[FakeRawConnection] = []
        pool = app_sqlite._PostgresPool()

        def make_conn() -> FakeRawConnection:
            conn = FakeRawConnection()
            raw.append(conn)
            return conn

        with patch.object(pool, "_new_connection", side_effect=make_conn):
            first = pool.acquire()
            second = pool.acquire()
            first_raw = first._conn
            second_raw = second._conn
            first.close()
            second.close()
            reused = pool.acquire()
            self.assertIs(reused._conn, second_raw)
            cursor = reused.execute("SELECT 1")
            self.assertEqual(cursor.fetchone(), {"ok": True})
            cursor.close()
            reused.commit()
            reused.rollback()
            self.assertTrue(second_raw.cursor.closed)
            self.assertEqual(second_raw.commits, 1)
            self.assertEqual(second_raw.rollbacks, 1)

            first_raw.closed = True
            recycled = pool.acquire()
            self.assertIsNot(recycled._conn, first_raw)
            reused.close()
            reused.close()
            recycled.close()

    def test_postgres_pool_timeout_and_failed_connection_accounting(self) -> None:
        from services import app_sqlite

        os.environ["APP_DB_POOL_SIZE"] = "1"
        os.environ["APP_DB_MAX_OVERFLOW"] = "0"
        pool = app_sqlite._PostgresPool()
        pool._timeout = 0.01
        with patch.object(pool, "_new_connection", return_value=FakeRawConnection()):
            first = pool.acquire()
            with self.assertRaisesRegex(RuntimeError, "pool exhausted"):
                pool.acquire()
            first.close()

        failing_pool = app_sqlite._PostgresPool()
        with patch.object(failing_pool, "_new_connection", side_effect=RuntimeError("boom")):
            self.assertRaises(RuntimeError, failing_pool.acquire)
        self.assertEqual(failing_pool._created, 0)

    def test_postgres_connection_close_returns_only_once(self) -> None:
        from services import app_sqlite

        os.environ["APP_DB_POOL_SIZE"] = "1"
        os.environ["APP_DB_MAX_OVERFLOW"] = "0"
        pool = app_sqlite._PostgresPool()
        with patch.object(pool, "_new_connection", return_value=FakeRawConnection()):
            conn = pool.acquire()
            raw = conn._conn
            conn.close()
            conn.close()
            self.assertIs(pool.acquire()._conn, raw)

    def test_postgres_pool_multithread_no_connection_leak(self) -> None:
        from services import app_sqlite

        os.environ["APP_DB_POOL_SIZE"] = "2"
        os.environ["APP_DB_MAX_OVERFLOW"] = "2"
        os.environ["APP_DB_POOL_TIMEOUT"] = "1"
        raw: list[FakeRawConnection] = []
        errors: list[Exception] = []
        pool = app_sqlite._PostgresPool()

        def make_conn() -> FakeRawConnection:
            conn = FakeRawConnection()
            raw.append(conn)
            return conn

        def worker() -> None:
            try:
                for _ in range(10):
                    conn = pool.acquire()
                    conn.execute("SELECT 1").close()
                    conn.close()
            except Exception as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        with patch.object(pool, "_new_connection", side_effect=make_conn):
            threads = [threading.Thread(target=worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(errors, [])
        self.assertLessEqual(pool._created, pool._max_total)
        self.assertLessEqual(len(raw), pool._max_total)


if __name__ == "__main__":
    unittest.main()
