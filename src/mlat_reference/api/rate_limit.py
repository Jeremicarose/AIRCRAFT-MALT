"""Small, process-local rate limiter for the single-node reference API."""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
import math
import threading
import time
from typing import Callable


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_after_seconds: int


class SlidingWindowRateLimiter:
    """Bound requests per client over a rolling time window.

    State is intentionally local to one process. The reference deployment uses
    one API worker; a multi-worker deployment must use a shared limiter instead.
    """

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        max_clients: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit < 1 or window_seconds < 1 or max_clients < 1:
            raise ValueError("rate-limit values must be positive integers")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._clock = clock
        self._buckets: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def consume(self, client_key: str) -> RateLimitDecision:
        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets.pop(client_key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.limit:
                self._buckets[client_key] = bucket
                reset_after = max(1, math.ceil(bucket[0] + self.window_seconds - now))
                return RateLimitDecision(False, self.limit, 0, reset_after)

            bucket.append(now)
            self._buckets[client_key] = bucket
            while len(self._buckets) > self.max_clients:
                self._buckets.popitem(last=False)

            reset_after = max(1, math.ceil(bucket[0] + self.window_seconds - now))
            return RateLimitDecision(True, self.limit, self.limit - len(bucket), reset_after)
