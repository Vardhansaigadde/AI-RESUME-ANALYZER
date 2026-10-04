"""Tests for the per-client rate limiter (app/rate_limit.py)."""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.rate_limit import RateLimitMiddleware


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_client(limit: int, clock: FakeClock) -> TestClient:
    app = FastAPI()

    @app.post("/api/analyze")
    def analyze():
        return {"ok": True}

    @app.get("/api/info")
    def info():
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware, limit=limit, window_seconds=60.0, clock=clock)
    return TestClient(app)


class TestRateLimit(unittest.TestCase):
    def test_blocks_after_limit_and_recovers(self):
        clock = FakeClock()
        client = make_client(limit=3, clock=clock)
        for _ in range(3):
            self.assertEqual(client.post("/api/analyze").status_code, 200)

        blocked = client.post("/api/analyze")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers["retry-after"], "60")
        self.assertIn("wait", blocked.json()["detail"])

        clock.now += 30
        self.assertEqual(client.post("/api/analyze").status_code, 429)
        self.assertEqual(client.post("/api/analyze").headers["retry-after"], "30")

        clock.now += 31  # oldest requests have left the 60 s window
        self.assertEqual(client.post("/api/analyze").status_code, 200)

    def test_get_requests_and_other_paths_not_limited(self):
        clock = FakeClock()
        client = make_client(limit=1, clock=clock)
        self.assertEqual(client.post("/api/analyze").status_code, 200)
        for _ in range(5):
            self.assertEqual(client.get("/api/info").status_code, 200)

    def test_zero_limit_disables(self):
        client = make_client(limit=0, clock=FakeClock())
        for _ in range(20):
            self.assertEqual(client.post("/api/analyze").status_code, 200)


if __name__ == "__main__":
    unittest.main()
