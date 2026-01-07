"""
Rate limiting utilities for API calls.
Implements token bucket algorithm for rate limiting.
"""
import time
from collections import deque
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter.

    Allows a certain number of requests within a time window.
    """

    def __init__(self, rate_limit: int, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds (default 60)
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.
        Blocks until rate limit allows, or returns False if timeout.

        Args:
            timeout: Maximum time to wait in seconds (None = wait indefinitely)

        Returns:
            True if permission acquired, False if timeout
        """
        start_time = time.time()

        with self.lock:
            while True:
                now = time.time()

                # Remove old requests outside time window
                while self.requests and self.requests[0] < now - self.time_window:
                    self.requests.popleft()

                # Check if we can make a request
                if len(self.requests) < self.rate_limit:
                    self.requests.append(now)
                    return True

                # Calculate wait time
                if timeout is not None:
                    elapsed = now - start_time
                    if elapsed >= timeout:
                        return False

                # Calculate time to wait
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request) + 0.1

                # Release lock while waiting
                self.lock.release()

                # Check timeout before sleeping
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed + wait_time > timeout:
                        self.lock.acquire()
                        return False

                # Wait
                time.sleep(wait_time)

                # Re-acquire lock
                self.lock.acquire()

    def get_available_requests(self) -> int:
        """
        Get number of requests available in current time window.

        Returns:
            Number of requests that can be made immediately
        """
        with self.lock:
            now = time.time()

            # Remove old requests
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()

            return max(0, self.rate_limit - len(self.requests))
