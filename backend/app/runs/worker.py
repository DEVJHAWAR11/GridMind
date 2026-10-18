"""Background worker: claims queued cells from the DB and runs the agent on each.

Scaling model
- The queue is the `cells` table (status = queued). Claiming is atomic
  (SKIP LOCKED), so any number of instances can run workers concurrently.
- A claimed cell carries a lock timestamp; if an instance dies mid-cell,
  the lock goes stale and another worker reclaims it (at-least-once).
- Per-instance concurrency is bounded; upstream calls are additionally
  rate-limited and cached (see agent/deps.py).
- Live progress is published on the event bus; DB is written only on
  state transitions plus one bulk write of the trace at the end.
"""
import asyncio
import logging
import random

from ..config import Settings
from ..events import EventBus
from ..store import Repo, iso_in

log = logging.getLogger("gridmind.worker")

PUBLIC_FIELDS = ("id", "row_id", "column_id", "status", "answer", "detail", "confidence", "sources", "error")


def _retryable(exc: Exception) -> bool:
    """4xx (except timeout / rate limit) and budget errors will fail the same way again."""
    if not getattr(exc, "retryable", True):
        return False
    status = getattr(exc, "status_code", None)
    return not (isinstance(status, int) and 400 <= status < 500 and status not in (408, 429))


def public_cell(cell: dict) -> dict:
    return {k: cell.get(k) for k in PUBLIC_FIELDS}


class Worker:
    def __init__(self, repo: Repo, bus: EventBus, graph, settings: Settings) -> None:
        self.repo, self.bus, self.graph, self.s = repo, bus, graph, settings
        self._wake = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._inflight: dict[str, asyncio.Task] = {}
        self._cells: dict[str, dict] = {}

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="gridmind-worker")

    def wake(self) -> None:
        self._wake.set()

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        for t in list(self._inflight.values()):
            t.cancel()
        await asyncio.gather(*self._inflight.values(), *([self._task] if self._task else []), return_exceptions=True)
        # Hand unfinished work back immediately instead of waiting for the lock to go stale.
        for cell in self._cells.values():
            try:
                await self.repo.enqueue_cell(cell["id"])
            except Exception:  # noqa: BLE001
                log.exception("failed to requeue %s on shutdown", cell["id"])

    async def _loop(self) -> None:
        while True:
            try:
                free = self.s.max_concurrency - len(self._inflight)
                if free > 0:
                    for cell in await self.repo.claim_cells(free, self.s.stale_lock_s):
                        self._cells[cell["id"]] = cell
                        t = asyncio.create_task(self._process(cell))
                        self._inflight[cell["id"]] = t
                        t.add_done_callback(lambda _t, cid=cell["id"]: self._done(cid))
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - never let the loop die (e.g. DB blip)
                log.exception("claim failed")
            try:
                # Jitter keeps many instances from polling in lockstep.
                await asyncio.wait_for(self._wake.wait(), self.s.poll_interval_s * (0.8 + random.random() * 0.4))
            except asyncio.TimeoutError:
                pass
            self._wake.clear()

    def _done(self, cell_id: str) -> None:
        self._inflight.pop(cell_id, None)
        self._cells.pop(cell_id, None)
        self.wake()  # capacity freed: pick up the next cell right away

    async def _publish_cell(self, sheet_id: str, cell: dict | None) -> None:
        if cell:
            await self.bus.publish(sheet_id, "cell", public_cell(cell))

    async def _process(self, cell: dict) -> None:
        sheet_id, cell_id = cell["sheet_id"], cell["id"]
        row = await self.repo.get_row(cell["row_id"])
        col = await self.repo.get_column(cell["column_id"])
        if not row or not col:  # deleted while queued
            await self.repo.b.delete("cells", id=cell_id)
            return
        await self._publish_cell(sheet_id, cell)

        async def emit(step: dict) -> None:
            await self.bus.publish(sheet_id, "step", {"cell_id": cell_id, **step})

        try:
            final = await asyncio.wait_for(
                self.graph.ainvoke(
                    {"entity": row["entity"], "question": col["question"], "attempt": 0},
                    config={"configurable": {"emit": emit}},
                ),
                self.s.cell_timeout_s,
            )
            res = final["result"]
            updated = await self.repo.update_cell(
                cell_id,
                status="done",
                answer=res["answer"],
                detail=res["detail"],
                confidence=res["confidence"],
                sources=res["sources"],
                error=None,
                locked_at=None,
            )
            if updated:  # None => cell was deleted/edited mid-run; discard result
                await self.repo.save_steps(cell_id, final.get("steps", []))
            await self._publish_cell(sheet_id, updated)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("cell %s failed (attempt %s): %s", cell_id, cell.get("attempts"), exc)
            retry = _retryable(exc) and cell.get("attempts", 1) < self.s.max_cell_attempts
            msg = f"{type(exc).__name__}: {str(exc)[:200]}"
            if retry:  # keep `attempts` (incremented at claim time) so retries stay bounded
                # Backoff: a future queued_at keeps the cell unclaimable until then.
                delay = min(60, self.s.retry_backoff_s * 2 ** (cell.get("attempts", 1) - 1))
                updated = await self.repo.update_cell(
                    cell_id, status="queued", queued_at=iso_in(delay), locked_at=None, error=msg
                )
            else:
                updated = await self.repo.update_cell(cell_id, status="error", error=msg, locked_at=None)
            await self._publish_cell(sheet_id, updated)
