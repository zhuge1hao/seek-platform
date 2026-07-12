import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class CacheRateLimitEventBusTest(unittest.TestCase):
    def tearDown(self) -> None:
        from services import redis_service

        redis_service.reset_clients_for_test()
        os.environ.pop("REDIS_URL", None)
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

    def test_cache_redis_paths_and_sensitive_entry_refusal(self) -> None:
        from services import cache_service

        class FakeRedis:
            def __init__(self) -> None:
                self.values: dict[str, str] = {}

            def get(self, key: str) -> str | None:
                return self.values.get(key)

            def setex(self, key: str, _ttl: int, value: str) -> None:
                self.values[key] = value

            def delete(self, key: str) -> None:
                self.values.pop(key, None)

        redis = FakeRedis()
        os.environ["CACHE_BACKEND"] = "redis"
        with patch("services.cache_service.redis_service.client", return_value=redis):
            cache_service.set("agents:list", {"items": [1]}, ttl_seconds=10)
            self.assertEqual(cache_service.get("agents:list"), {"items": [1]})
            cache_service.delete("agents:list")
            self.assertEqual(cache_service.get("agents:list", "missing"), "missing")
            cache_service.set("token", {"value": "secret"}, ttl_seconds=10)
            self.assertEqual(cache_service.get("token", "blocked"), "blocked")
            cache_service.set("normal", {"api_key": "secret"}, ttl_seconds=10)
            self.assertEqual(cache_service.get("normal", "blocked"), "blocked")

    def test_redis_service_namespace_health_reuse_and_redaction(self) -> None:
        from services import redis_service

        class FakeRedis:
            def __init__(self, ok: bool = True) -> None:
                self.ok = ok

            def ping(self) -> bool:
                return self.ok

        created: list[FakeRedis] = []

        def make_client(_decode: bool) -> FakeRedis:
            redis = FakeRedis()
            created.append(redis)
            return redis

        os.environ["REDIS_URL"] = "redis://:top-secret@localhost:6379/0"
        redis_service.reset_clients_for_test()
        self.assertEqual(redis_service.key("cache", ":agents:"), "meizhaiseek:cache:agents")
        with patch("services.redis_service._make_client", side_effect=make_client):
            self.assertIs(redis_service.client(), redis_service.client())
            self.assertEqual(len(created), 1)
            self.assertEqual(redis_service.health_check()["status"], "ok")

        redis_service.reset_clients_for_test()
        with patch("services.redis_service._make_client", side_effect=RuntimeError("redis://:top-secret@localhost:6379/0 failed")):
            failed = redis_service.health_check()
        self.assertEqual(failed["status"], "failed")
        self.assertNotIn("top-secret", failed["error"])

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

    def test_event_bus_redis_publish_wait_and_payload_redaction(self) -> None:
        from services import agent_run_event_bus

        class FakePubSub:
            def __init__(self, redis: "FakeRedis") -> None:
                self.redis = redis

            def subscribe(self, channel: str) -> None:
                self.redis.subscribed = channel

            def get_message(self, timeout: float = 0.2) -> dict | None:
                return self.redis.messages.pop(0) if self.redis.messages else None

            def close(self) -> None:
                self.redis.closed = True

        class FakeRedis:
            def __init__(self) -> None:
                self.messages: list[dict] = []
                self.subscribed = ""
                self.closed = False

            def publish(self, channel: str, payload: str) -> None:
                self.messages.append({"type": "message", "channel": channel, "data": payload})

            def pubsub(self) -> FakePubSub:
                return FakePubSub(self)

        redis = FakeRedis()
        os.environ["EVENT_BACKEND"] = "redis"
        with patch("services.agent_run_event_bus.redis_service.client", return_value=redis):
            agent_run_event_bus.publish_run_event(
                {
                    "run_id": "run1",
                    "status": "completed",
                    "prompt": "hidden",
                    "workflow_options": {"token": "secret"},
                    "result": {"answer": "ok", "raw_response": "hidden"},
                }
            )
            event = agent_run_event_bus.wait_for_event("run1", timeout=0.01)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["status"], "completed")
        self.assertNotIn("raw_response", str(event))
        self.assertNotIn("workflow_options", str(event))
        self.assertNotIn("token", str(event).lower())
        self.assertTrue(redis.closed)

    def test_runtime_health_validation_and_secret_safety(self) -> None:
        from services import runtime_health_service

        with (
            patch("services.runtime_health_service.component_health", return_value={
                "database": {"backend": "postgres", "status": "ok"},
                "redis": {"status": "ok"},
                "queue": {"backend": "redis", "status": "ok"},
                "events": {"backend": "redis", "status": "ok"},
                "artifact_storage": {"backend": "s3", "status": "ok"},
                "rag": {"backend": "pgvector", "status": "ok"},
                "security": {"token_secret_status": "configured", "default_admin_password_detected": False},
                "capacity_profile": "500-users",
            }),
            patch.dict(os.environ, {"MULTI_INSTANCE_SSE_VERIFIED": "passed", "PGVECTOR_MIGRATION_VERIFIED": "failed", "CAPACITY_LAST_VERIFIED_USERS": "100"}),
        ):
            health = runtime_health_service.runtime_health()
        self.assertEqual(health["version"], "v1.8.3")
        self.assertEqual(health["model"], "meizhaiseek 2.0")
        self.assertEqual(health["validation"]["multi_instance_sse_verified"], "passed")
        self.assertEqual(health["validation"]["pgvector_migration_verified"], "failed")
        self.assertEqual(health["validation"]["capacity_last_verified_users"], 100)
        self.assertNotIn("top-secret", str(health).lower())


if __name__ == "__main__":
    unittest.main()
