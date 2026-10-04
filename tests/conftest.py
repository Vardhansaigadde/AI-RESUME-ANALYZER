"""Shared pytest setup."""

import os

# The API rate limit would throttle the test client (every test request comes
# from the same address). Disable it for the suite; tests/test_rate_limit.py
# exercises the limiter directly.
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
