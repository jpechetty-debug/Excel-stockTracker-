"""
Rate Limiter
Throttles outgoing requests to prevent API bans.
"""

import time
import threading
from infrastructure.logging.logger import logger


class RateLimiter:
    """A thread-safe rate limiter enforcing a maximum number of requests per second."""
    
    def __init__(self, requests_per_second: float = 2.0):
        self.delay = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_call = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Blocks the thread until it is safe to make the next request."""
        if self.delay <= 0:
            return

        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_call
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                time.sleep(sleep_time)
            self.last_call = time.monotonic()
