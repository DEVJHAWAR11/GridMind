import json
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..runs.service import start_run

router = APIRouter(prefix="/api")

Entity = Annotated[str, Field(min_length=1, max_length=200)]
Question = Annotated[str, Field(min_length=3, max_length=300)]


def clean(items: list[str], limit: int) -> list[str]:
    out = [i.strip() for i in items if i and i.strip()]
    return out[:limit]


class SheetCreate(BaseModel):
    title: str = Field(default="Untitled sheet", max_length=120)
    entities: list[Entity] = []
    questions: list[Question] = []


class TitleBody(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class QuestionsBody(BaseModel):
    questions: list[Question] = Field(min_length=1)


class EntitiesBody(BaseModel):
    entities: list[Entity] = Field(min_length=1)


class QuestionBody(BaseModel):
    question: Question


class EntityBody(BaseModel):
    entity: Entity


class RunBody(BaseModel):
    force: bool = False
    row_id: str | None = None
    column_id: str | None = None


def _repo(req: Request):
    return req.app.state.repo


async def _require_sheet(req: Request, sheet_id: str) -> dict:
    sheet = await _repo(req).get_sheet(sheet_id)
    if not sheet:
        raise HTTPException(404, "Sheet not found")
    return sheet


def _client_ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (req.client.host if req.client else "unknown")


async def _check_capacity(req: Request, sheet_id: str, new_rows: int = 0, new_cols: int = 0) -> None:
    s = req.app.state.settings
    repo = _repo(req)
    if new_rows and len(await repo.list_rows(sheet_id)) + new_rows > s.max_rows:
        raise HTTPException(422, f"A sheet can have at most {s.max_rows} rows")
    if new_cols and len(await repo.list_columns(sheet_id)) + new_cols > s.max_columns:
        raise HTTPException(422, f"A sheet can have at most {s.max_columns} columns")


# ---- sheets ----------------------------------------------------------------
@router.post("/sheets", status_code=201)
async def create_sheet(body: SheetCreate, req: Request):
    s = req.app.state.settings
    repo = _repo(req)
    if not req.app.state.create_limiter.allow(_client_ip(req)):
        raise HTTPException(429, "Too many requests")
    sheet = await repo.create_sheet(body.title.strip() or "Untitled sheet")
    await repo.add_rows(sheet["id"], clean(body.entities, s.max_rows))
    await repo.add_columns(sheet["id"], clean(body.questions, s.max_columns))
    return await repo.full_sheet(sheet["id"])


@router.get("/sheets")
async def list_sheets(req: Request, ids: str = Query("", description="comma-separated sheet ids")):
    wanted = [i for i in ids.split(",") if i][:50]
    return await _repo(req).get_sheets(wanted)


@router.get("/sheets/{sheet_id}")
async def get_sheet(sheet_id: str, req: Request):
    full = await _repo(req).full_sheet(sheet_id)
    if not full:
        raise HTTPException(404, "Sheet not found")
    return full


@router.patch("/sheets/{sheet_id}")
async def rename_sheet(sheet_id: str, body: TitleBody, req: Request):
    await _require_sheet(req, sheet_id)
    return await _repo(req).rename_sheet(sheet_id, body.title.strip())


@router.delete("/sheets/{sheet_id}", status_code=204)
async def delete_sheet(sheet_id: str, req: Request):
    await _require_sheet(req, sheet_id)
    await _repo(req).delete_sheet(sheet_id)


# ---- columns & rows ---------------------------------------------------------
@router.post("/sheets/{sheet_id}/columns", status_code=201)
async def add_columns(sheet_id: str, body: QuestionsBody, req: Request):
    await _require_sheet(req, sheet_id)
    qs = clean(body.questions, 50)
    await _check_capacity(req, sheet_id, new_cols=len(qs))
    return await _repo(req).add_columns(sheet_id, qs)


@router.patch("/columns/{column_id}")
async def update_column(column_id: str, body: QuestionBody, req: Request):
    row = await _repo(req).update_column(column_id, body.question.strip())
    if not row:
        raise HTTPException(404, "Column not found")
    return row


@router.delete("/columns/{column_id}", status_code=204)
async def delete_column(column_id: str, req: Request):
    await _repo(req).delete_column(column_id)


@router.post("/sheets/{sheet_id}/rows", status_code=201)
async def add_rows(sheet_id: str, body: EntitiesBody, req: Request):
    await _require_sheet(req, sheet_id)
    items = clean(body.entities, 500)
    await _check_capacity(req, sheet_id, new_rows=len(items))
    return await _repo(req).add_rows(sheet_id, items)


@router.patch("/rows/{row_id}")
async def update_row(row_id: str, body: EntityBody, req: Request):
    row = await _repo(req).update_row(row_id, body.entity.strip())
    if not row:
        raise HTTPException(404, "Row not found")
    return row


@router.delete("/rows/{row_id}", status_code=204)
async def delete_row(row_id: str, req: Request):
    await _repo(req).delete_row(row_id)


# ---- runs, live events, traces ----------------------------------------------
@router.post("/sheets/{sheet_id}/run")
async def run_sheet(sheet_id: str, body: RunBody, req: Request):
    await _require_sheet(req, sheet_id)
    if not req.app.state.run_limiter.allow(_client_ip(req)):
        raise HTTPException(429, "Too many runs; slow down")
    queued = await start_run(
        _repo(req), req.app.state.bus, req.app.state.worker, sheet_id, body.force, body.row_id, body.column_id
    )
    return {"queued": queued}


@router.get("/sheets/{sheet_id}/events")
async def sheet_events(sheet_id: str, req: Request):
    """SSE stream. Subscribes first, then emits `ready`; the client should fetch
    a snapshot on `ready` so no update can fall into the gap."""
    await _require_sheet(req, sheet_id)
    bus = req.app.state.bus

    async def gen():
        async with bus.subscribe(sheet_id) as q:
            yield {"event": "ready", "data": "{}"}
            while True:
                msg = await q.get()
                yield {"event": msg["event"], "data": json.dumps(msg["data"])}

    return EventSourceResponse(gen(), ping=15)


@router.get("/cells/{cell_id}/steps")
async def cell_steps(cell_id: str, req: Request):
    repo = _repo(req)
    cell = await repo.get_cell(cell_id)
    if not cell:
        raise HTTPException(404, "Cell not found")
    steps = await repo.steps(cell_id)
    return {
        "cell": cell,
        "steps": [{k: s[k] for k in ("idx", "node", "summary", "data")} for s in steps],
    }
