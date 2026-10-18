"""Event fan-out for live grid updates (SSE).

The API is stateless: any instance may run a cell while a different instance
holds the browser's SSE connection. MemoryEventBus covers a single instance;
RedisEventBus (REDIS_URL, e.g. Upstash free tier) bridges instances via pub/sub.
Events are best-effort: durable state lives in the DB, and clients re-fetch a
snapshot on (re)connect.
"""
import asyncio
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Protocol


class EventBus(Protocol):
    async def publish(self, sheet_id: str, event: str, data: dict[str, Any]) -> None: ...
    def subscribe(self, sheet_id: str) -> "AsyncIterator[asyncio.Queue]": ...
    async def close(self) -> None: ...


class MemoryEventBus:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, sheet_id: str):
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subs[sheet_id].add(q)
        try:
            yield q
        finally:
            self._subs[sheet_id].discard(q)
            if not self._subs[sheet_id]:
                self._subs.pop(sheet_id, None)

    async def publish(self, sheet_id, event, data):
        for q in list(self._subs.get(sheet_id, ())):
            try:
                q.put_nowait({"event": event, "data": data})
            except asyncio.QueueFull:
                pass  # slow consumer; it resyncs from a snapshot on reconnect

    async def close(self) -> None:
        self._subs.clear()


class RedisEventBus:
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(url, decode_responses=True)

    @staticmethod
    def _channel(sheet_id: str) -> str:
        return f"gridmind:sheet:{sheet_id}"

    async def publish(self, sheet_id, event, data):
        try:
            await self._redis.publish(self._channel(sheet_id), json.dumps({"event": event, "data": data}))
        except Exception:  # noqa: BLE001 - events are best-effort
            pass

    @asynccontextmanager
    async def subscribe(self, sheet_id: str):
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel(sheet_id))

        async def pump() -> None:
            async for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                try:
                    q.put_nowait(json.loads(msg["data"]))
                except asyncio.QueueFull:
                    pass

        task = asyncio.create_task(pump())
        try:
            yield q
        finally:
            task.cancel()
            await pubsub.close()

    async def close(self) -> None:
        await self._redis.aclose()


def make_bus() -> EventBus:
    from .config import get_settings

    url = get_settings().redis_url
    return RedisEventBus(url) if url else MemoryEventBus()
