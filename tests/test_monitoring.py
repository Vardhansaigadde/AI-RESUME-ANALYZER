"""Error monitoring: browser crash reports and the privacy scrub for Sentry."""

import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.main import app
from app.monitoring import _scrub, init_sentry

client = TestClient(app)


class ClientErrorTests(unittest.TestCase):
    def test_browser_crash_is_logged(self):
        with self.assertLogs("fitlens.client", level="ERROR") as logs:
            response = client.post(
                "/api/client-error",
                json={"kind": "render", "message": "x is undefined", "stack": "at Foo", "path": "/check?id=1"},
            )
        self.assertEqual(response.status_code, 204)
        self.assertIn("Frontend render on /check: x is undefined", logs.output[0])
        self.assertNotIn("id=1", logs.output[0])

    def test_oversized_report_is_rejected(self):
        response = client.post("/api/client-error", json={"message": "x" * 501})
        self.assertEqual(response.status_code, 422)


class SentryTests(unittest.TestCase):
    def test_off_without_dsn(self):
        with mock.patch.dict(os.environ, {"SENTRY_DSN": ""}):
            self.assertFalse(init_sentry())

    def test_scrub_keeps_no_personal_data(self):
        event = {
            "request": {
                "method": "POST",
                "url": "https://api.example/api/analyze?email=a@b.c",
                "data": "resume text",
                "headers": {"Cookie": "x"},
                "env": {"REMOTE_ADDR": "1.2.3.4"},
            },
            "user": {"ip_address": "1.2.3.4"},
        }
        scrubbed = _scrub(event, {})
        self.assertEqual(scrubbed["request"], {"method": "POST", "url": "https://api.example/api/analyze"})
        self.assertNotIn("user", scrubbed)


if __name__ == "__main__":
    unittest.main()
