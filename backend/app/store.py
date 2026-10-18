"""Storage layer: a small table-oriented Backend plus domain-level Repo.

Backends: Supabase (production) and in-memory (local dev without credentials,
and tests). Job claiming is a backend primitive so it can be atomic across
many API/worker instances (Postgres FOR UPDATE SKIP LOCKED).
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_in(seconds: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


class Backend(Protocol):
    async def insert(self, table: str, row: dict) -> dict: ...
    async def insert_many(self, table: str, rows: list[dict]) -> None: ...
    async def select(self, table: str, order: str | None = None, **eq: Any) -> list[dict]: ...
    async def update(self, table: str, id: str, data: dict) -> dict | None: ...
    async def delete(self, table: str, **eq: Any) -> None: ...
    async def claim_cells(self, limit: int, stale_seconds: int) -> list[dict]: ...


class MemoryBackend:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}
        self._lock = asyncio.Lock()

    async def insert(self, table, row):
        row = {"id": str(uuid.uuid4()), "created_at": now_iso(), **row}
        self.tables.setdefault(table, []).append(row)
        return dict(row)

    async def insert_many(self, table, rows):
        for r in rows:
            await self.insert(table, r)

    async def select(self, table, order=None, **eq):
        rows = [r for r in self.tables.get(table, []) if all(r.get(k) == v for k, v in eq.items())]
        if order:
            rows.sort(key=lambda r: r.get(order, 0))
        return [dict(r) for r in rows]

    async def update(self, table, id, data):
        for r in self.tables.get(table, []):
            if r["id"] == id:
                r.update(data)
                return dict(r)
        return None

    async def delete(self, table, **eq):
        self.tables[table] = [
            r for r in self.tables.get(table, []) if not all(r.get(k) == v for k, v in eq.items())
        ]

    async def claim_cells(self, limit, stale_seconds):
        async with self._lock:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=stale_seconds)).isoformat()
            now = now_iso()
            ready = [
                c
                for c in self.tables.get("cells", [])
                if (c["status"] == "queued" and (c.get("queued_at") or "") <= now)
                or (c["status"] == "running" and (c.get("locked_at") or "") < cutoff)
            ]
            ready.sort(key=lambda c: c.get("queued_at") or "")
            claimed = []
            for c in ready[:limit]:
                c.update(
                    status="running",
                    locked_at=now_iso(),
                    updated_at=now_iso(),
                    attempts=c.get("attempts", 0) + 1,
                )
                claimed.append(dict(c))
            return claimed


class SupabaseBackend:
    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client

        self.client = create_client(url, key)

    @staticmethod
    async def _run(fn):
        """Run a blocking supabase call in a thread. Supabase recycles its HTTP/2 connections
        (GOAWAY), which surfaces as a transport error on in-flight requests: retry those."""
        import httpx

        for attempt in range(3):
            try:
                return await asyncio.to_thread(fn)
            except httpx.TransportError:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.2 * (attempt + 1))

    async def insert(self, table, row):
        res = await self._run(lambda: self.client.table(table).insert(row).execute())
        return res.data[0]

    async def insert_many(self, table, rows):
        if rows:
            await self._run(lambda: self.client.table(table).insert(rows).execute())

    async def select(self, table, order=None, **eq):
        def run():
            q = self.client.table(table).select("*")
            for k, v in eq.items():
                q = q.eq(k, v)
            if order:
                q = q.order(order)
            return q.execute().data

        return await self._run(run)

    async def update(self, table, id, data):
        res = await self._run(
            lambda: self.client.table(table).update(data).eq("id", id).execute()
        )
        return res.data[0] if res.data else None

    async def delete(self, table, **eq):
        def run():
            q = self.client.table(table).delete()
            for k, v in eq.items():
                q = q.eq(k, v)
            q.execute()

        await self._run(run)

    async def claim_cells(self, limit, stale_seconds):
        res = await self._run(
            lambda: self.client.rpc(
                "claim_cells", {"p_limit": limit, "p_stale_seconds": stale_seconds}
            ).execute()
        )
        return res.data or []


class Repo:
    """Domain operations on top of a Backend."""

    def __init__(self, backend: Backend) -> None:
        self.b = backend

    # sheets
    async def create_sheet(self, title: str) -> dict:
        return await self.b.insert("sheets", {"title": title})

    async def get_sheet(self, sheet_id: str) -> dict | None:
        found = await self.b.select("sheets", id=sheet_id)
        return found[0] if found else None

    async def get_sheets(self, ids: list[str]) -> list[dict]:
        out = await asyncio.gather(*(self.get_sheet(i) for i in ids))
        return [s for s in out if s]

    async def rename_sheet(self, sheet_id: str, title: str) -> dict | None:
        return await self.b.update("sheets", sheet_id, {"title": title})

    async def delete_sheet(self, sheet_id: str) -> None:
        for t in ("cells", "rows", "columns"):
            await self.b.delete(t, sheet_id=sheet_id)
        await self.b.delete("sheets", id=sheet_id)

    async def full_sheet(self, sheet_id: str) -> dict | None:
        sheet = await self.get_sheet(sheet_id)
        if not sheet:
            return None
        cols, rows, cells = await asyncio.gather(
            self.b.select("columns", order="position", sheet_id=sheet_id),
            self.b.select("rows", order="position", sheet_id=sheet_id),
            self.b.select("cells", sheet_id=sheet_id),
        )
        return {"sheet": sheet, "columns": cols, "rows": rows, "cells": cells}

    # columns / rows
    async def list_columns(self, sheet_id: str) -> list[dict]:
        return await self.b.select("columns", order="position", sheet_id=sheet_id)

    async def list_rows(self, sheet_id: str) -> list[dict]:
        return await self.b.select("rows", order="position", sheet_id=sheet_id)

    async def get_column(self, id: str) -> dict | None:
        found = await self.b.select("columns", id=id)
        return found[0] if found else None

    async def get_row(self, id: str) -> dict | None:
        found = await self.b.select("rows", id=id)
        return found[0] if found else None

    async def add_columns(self, sheet_id: str, questions: list[str]) -> list[dict]:
        pos = max((c["position"] for c in await self.list_columns(sheet_id)), default=-1) + 1
        return [
            await self.b.insert("columns", {"sheet_id": sheet_id, "position": pos + i, "question": q})
            for i, q in enumerate(questions)
        ]

    async def add_rows(self, sheet_id: str, entities: list[str]) -> list[dict]:
        pos = max((r["position"] for r in await self.list_rows(sheet_id)), default=-1) + 1
        return [
            await self.b.insert("rows", {"sheet_id": sheet_id, "position": pos + i, "entity": e})
            for i, e in enumerate(entities)
        ]

    async def update_column(self, id: str, question: str) -> dict | None:
        await self.b.delete("cells", column_id=id)  # a new question invalidates old answers
        return await self.b.update("columns", id, {"question": question})

    async def update_row(self, id: str, entity: str) -> dict | None:
        await self.b.delete("cells", row_id=id)
        return await self.b.update("rows", id, {"entity": entity})

    async def delete_column(self, id: str) -> None:
        await self.b.delete("cells", column_id=id)
        await self.b.delete("columns", id=id)

    async def delete_row(self, id: str) -> None:
        await self.b.delete("cells", row_id=id)
        await self.b.delete("rows", id=id)

    # cells / jobs
    async def ensure_cell(self, sheet_id: str, row_id: str, column_id: str) -> dict:
        found = await self.b.select("cells", row_id=row_id, column_id=column_id)
        if found:
            return found[0]
        return await self.b.insert(
            "cells",
            {
                "sheet_id": sheet_id,
                "row_id": row_id,
                "column_id": column_id,
                "status": "idle",
                "sources": [],
                "attempts": 0,
            },
        )

    async def list_cells(self, sheet_id: str) -> list[dict]:
        return await self.b.select("cells", sheet_id=sheet_id)

    async def create_queued_cell(self, sheet_id: str, row_id: str, column_id: str) -> dict:
        return await self.b.insert(
            "cells",
            {
                "sheet_id": sheet_id,
                "row_id": row_id,
                "column_id": column_id,
                "status": "queued",
                "queued_at": now_iso(),
                "sources": [],
                "attempts": 0,
            },
        )

    async def get_cell(self, cell_id: str) -> dict | None:
        found = await self.b.select("cells", id=cell_id)
        return found[0] if found else None

    async def update_cell(self, cell_id: str, **data: Any) -> dict | None:
        return await self.b.update("cells", cell_id, {**data, "updated_at": now_iso()})

    async def enqueue_cell(self, cell_id: str) -> dict | None:
        return await self.update_cell(
            cell_id, status="queued", queued_at=now_iso(), error=None, attempts=0
        )

    async def claim_cells(self, limit: int, stale_seconds: int) -> list[dict]:
        return await self.b.claim_cells(limit, stale_seconds)

    async def save_steps(self, cell_id: str, steps: list[dict]) -> None:
        await self.b.delete("cell_steps", cell_id=cell_id)
        await self.b.insert_many(
            "cell_steps",
            [
                {
                    "cell_id": cell_id,
                    "idx": i,
                    "node": s["node"],
                    "summary": s["summary"],
                    "data": s.get("data", {}),
                }
                for i, s in enumerate(steps)
            ],
        )

    async def steps(self, cell_id: str) -> list[dict]:
        return await self.b.select("cell_steps", order="idx", cell_id=cell_id)


def make_repo() -> Repo:
    from .config import get_settings

    s = get_settings()
    if s.supabase_url and s.supabase_service_key:
        return Repo(SupabaseBackend(s.supabase_url, s.supabase_service_key))
    print("[gridmind] SUPABASE_* not set - using in-memory store (data is lost on restart)")
    return Repo(MemoryBackend())
