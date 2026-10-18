import asyncio

from ..events import EventBus
from ..store import Repo
from .worker import Worker, public_cell

ACTIVE = ("queued", "running")


async def start_run(
    repo: Repo,
    bus: EventBus,
    worker: Worker | None,
    sheet_id: str,
    force: bool = False,
    row_id: str | None = None,
    column_id: str | None = None,
) -> int:
    """Enqueue cells that need (re)computing; returns how many were queued.

    No in-memory state: enqueueing is just DB writes, so any API instance can
    do it and any worker instance will pick the cells up.
    """
    cols, rows, cells = await asyncio.gather(
        repo.list_columns(sheet_id), repo.list_rows(sheet_id), repo.list_cells(sheet_id)
    )
    existing = {(c["row_id"], c["column_id"]): c for c in cells}
    sem = asyncio.Semaphore(16)  # bounded write fan-out to the DB

    async def enqueue(r: dict, c: dict) -> dict | None:
        cell = existing.get((r["id"], c["id"]))
        if cell and cell["status"] in ACTIVE:
            return None
        if cell and cell["status"] == "done" and not force:
            return None
        async with sem:
            if cell:
                return await repo.enqueue_cell(cell["id"])
            return await repo.create_queued_cell(sheet_id, r["id"], c["id"])

    targets = [
        (r, c)
        for r in rows
        for c in cols
        if (row_id is None or r["id"] == row_id) and (column_id is None or c["id"] == column_id)
    ]
    queued = [x for x in await asyncio.gather(*(enqueue(r, c) for r, c in targets)) if x]
    for cell in queued:
        await bus.publish(sheet_id, "cell", public_cell(cell))
    if worker and queued:
        worker.wake()
    return len(queued)
