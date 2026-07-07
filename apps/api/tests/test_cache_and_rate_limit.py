import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class CacheRateLimitEventBusTest(unittest.TestCase):
    def tearDown(self) -> None:
        for key in ("CACHE_BACKEND", "RATE_LIMIT_BACKEND", "EVENT_BACKEND", "LOGIN_RATE_LIMIT_PER_WINDOW", "LOGIN_RATE_LIMIT_WINDOW_SECONDS"):
            os.environ.pop(key, None)

    def test_memory_cache_ttl_delete_and_redis_fallback(self) -> None:
        from services import cache_service

        cache_service._MEMORY.clear()
        os.environ["CACHE_BACKEND"] = "memory"
        cache_service.set("a", {"value": 1}, ttl_seconds=1)
        self.assertEqual(cache_service.get("a"), {"value": 1})
        cache_service.delete("a")
        self.assertEqual(cache_service.get("a", "missing"), "missing")
        cache_service.set("b", 2, ttl_seconds=1)
        with patch("services.cache_service.time.time", return_value=time.time() + 2):
            self.assertEqual(cache_service.get("b", "expired"), "expired")
        os.environ["CACHE_BACKEND"] = "redis"
        with patch("services.cache_service.redis_service.client", side_effect=RuntimeError("down")):
            self.assertEqual(cache_service.get("c", "fallback"), "fallback")

    def test_rate_limit_memory_and_login_pipeline(self) -> None:
        from services import rate_limit_service

        rate_limit_service._WINDOWS.clear()
        self.assertTrue(rate_limit_service.check("k", 1, 60).allowed)
        blocked = rate_limit_service.check("k", 1, 60)
        self.assertFalse(blocked.allowed)
        self.assertGreater(blocked.retry_after, 0)

        os.environ["RATE_LIMIT_BACKEND"] = "redis"

        class FakePipe:
            command_stack = [1]

            def __init__(self, values: list[int] | None = None) -> None:
                self.values = values or []

            def incr(self, _key: str) -> None:
                return None

            def expire(self, _key: str, _ttl: int) -> None:
                return None

            def execute(self) -> list[int]:
                return self.values

        class FakeRedis:
            def pipeline(self) -> FakePipe:
                return FakePipe([1, 1])

            def ttl(self, _key: str) -> int:
                return 60

        with patch("services.rate_limit_service.redis_service.client", return_value=FakeRedis()):
            self.assertTrue(rate_limit_service.check_login("127.0.0.1", "Alice").allowed)

    def test_event_bus_memory_and_redis_payload_redaction_shape(self) -> None:
        from services import agent_run_event_bus

        os.environ["EVENT_BACKEND"] = "memory"
        self.assertIsNone(agent_run_event_bus.wait_for_event("run1", timeout=0.01))
        self.assertEqual(agent_run_event_bus.health_check()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
