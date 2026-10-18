"""Protections for rate-limited free-tier upstreams (Groq, Tavily)."""
import asyncio
import random
import time
from collections import deque
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class RateLimiter:
    """Sliding-window limiter: at most `rate` acquisitions per `per` seconds."""

    def __init__(self, rate: int, per: float = 60.0) -> None:
        self.rate, self.per = max(1, rate), per
        self._hits: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._hits and now - self._hits[0] >= self.per:
                    self._hits.popleft()
                if len(self._hits) < self.rate:
                    self._hits.append(now)
                    return
                wait = self.per - (now - self._hits[0])
            await asyncio.sleep(wait + random.random() * 0.1)


def is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if status in (408, 429, 500, 502, 503, 504):
        return True
    return isinstance(exc, (asyncio.TimeoutError, ConnectionError, TimeoutError))


async def retry_async(
    fn: Callable[[], Awaitable[T]], attempts: int = 4, base: float = 1.0, cap: float = 20.0
) -> T:
    """Exponential backoff with full jitter on transient/429 errors."""
    for i in range(attempts):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001
            if i == attempts - 1 or not is_retryable(exc):
                raise
            retry_after = getattr(getattr(exc, "response", None), "headers", {}).get("retry-after")
            delay = float(retry_after) if retry_after and str(retry_after).replace(".", "").isdigit() else None
            await asyncio.sleep(min(cap, delay if delay is not None else random.uniform(0, base * 2**i)))
    raise RuntimeError("unreachable")


class TTLCache:
    """Async cache with TTL, bounded size, and in-flight de-duplication.

    Many cells ask near-identical queries (same entity, similar questions);
    concurrent identical requests share one upstream call.
    """

    def __init__(self, ttl: float, max_items: int = 2000) -> None:
        self.ttl, self.max_items = ttl, max_items
        self._data: dict[str, tuple[float, object]] = {}
        self._inflight: dict[str, asyncio.Future] = {}

    async def get_or_compute(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        hit = self._data.get(key)
        if hit and time.monotonic() - hit[0] < self.ttl:
            return hit[1]  # type: ignore[return-value]
        if key in self._inflight:
            return await asyncio.shield(self._inflight[key])
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._inflight[key] = fut
        try:
            value = await factory()
        except BaseException as exc:
            fut.set_exception(exc)
            fut.exception()  # mark retrieved, avoids "never retrieved" warnings
            raise
        else:
            if len(self._data) >= self.max_items:
                self._data.pop(next(iter(self._data)))
            self._data[key] = (time.monotonic(), value)
            fut.set_result(value)
            return value
        finally:
            self._inflight.pop(key, None)


class WindowCounter:
    """Per-key fixed-window counter (per-IP abuse guard). Per instance by design."""

    def __init__(self, limit: int, per: float = 60.0) -> None:
        self.limit, self.per = limit, per
        self._w: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        if len(self._w) > 10_000:
            self._w = {k: v for k, v in self._w.items() if now - v[0] < self.per}
        start, n = self._w.get(key, (now, 0))
        if now - start >= self.per:
            start, n = now, 0
        if n >= self.limit:
            return False
        self._w[key] = (start, n + 1)
        return True


class BudgetExceeded(Exception):
    """Quota guard tripped. Not retryable: retrying cannot help until the period rolls over."""

    retryable = False


class Budget:
    """Call counter with a cap per period (per instance; resets when the period key changes)."""

    def __init__(self, name: str, cap: int, period: str) -> None:
        self.name, self.cap, self.period = name, cap, period  # period: "day" | "month"
        self._key, self.used = "", 0

    def _current(self) -> str:
        from datetime import datetime, timezone

        d = datetime.now(timezone.utc)
        return d.strftime("%Y-%m-%d" if self.period == "day" else "%Y-%m")

    def try_spend(self, n: int = 1) -> bool:
        k = self._current()
        if k != self._key:
            self._key, self.used = k, 0
        if self.used + n > self.cap:
            return False
        self.used += n
        return True

    def snapshot(self) -> dict:
        return {"used": self.used, "cap": self.cap, "period": self.period}
