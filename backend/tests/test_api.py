import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.events import MemoryEventBus
from app.main import create_app
from app.resilience import RateLimiter, TTLCache, WindowCounter, retry_async
from app.store import MemoryBackend, Repo


class FakeGraph:
    """Stands in for the compiled LangGraph; fails for entities starting with 'bad'."""

    def __init__(self):
        self.calls = 0

    async def ainvoke(self, state, config):
        self.calls += 1
        await config["configurable"]["emit"]({"node": "plan", "summary": "p", "data": {}})
        if state["entity"].startswith("bad"):
            raise RuntimeError("upstream down")
        step = {"node": "answer", "summary": "done", "data": {}}
        return {
            "result": {
                "answer": f"{state['entity']}/{state['question']}",
                "detail": "d",
                "confidence": "high",
                "sources": [{"url": "https://x.com", "title": "x"}],
                "sufficient": True,
            },
            "steps": [step],
        }


@pytest.fixture
def client():
    s = Settings(poll_interval_s=0.05, max_cell_attempts=2, retry_backoff_s=0.05, max_rows=5, max_columns=3, runs_per_minute=100)
    app = create_app(repo=Repo(MemoryBackend()), bus=MemoryEventBus(), graph=FakeGraph(), settings=s)
    with TestClient(app) as c:
        yield c


def wait_for(client, sheet_id, pred, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        data = client.get(f"/api/sheets/{sheet_id}").json()
        if pred(data):
            return data
        time.sleep(0.05)
    raise AssertionError("timeout waiting for condition")


def make_sheet(client, entities, questions):
    return client.post("/api/sheets", json={"title": "t", "entities": entities, "questions": questions}).json()


def test_full_run_fills_cells_and_stores_trace(client):
    sheet = make_sheet(client, ["Acme", "Globex"], ["Hiring?", "Stack?"])
    sid = sheet["sheet"]["id"]
    assert client.post(f"/api/sheets/{sid}/run", json={}).json() == {"queued": 4}
    data = wait_for(client, sid, lambda d: len(d["cells"]) == 4 and all(c["status"] == "done" for c in d["cells"]))
    assert {c["answer"] for c in data["cells"]} == {"Acme/Hiring?", "Acme/Stack?", "Globex/Hiring?", "Globex/Stack?"}
    trace = client.get(f"/api/cells/{data['cells'][0]['id']}/steps").json()
    assert trace["steps"][0]["node"] == "answer"


def test_rerun_skips_done_unless_forced_and_new_column_runs_only_new(client):
    sheet = make_sheet(client, ["Acme"], ["Hiring?"])
    sid = sheet["sheet"]["id"]
    client.post(f"/api/sheets/{sid}/run", json={})
    wait_for(client, sid, lambda d: d["cells"] and d["cells"][0]["status"] == "done")
    assert client.post(f"/api/sheets/{sid}/run", json={}).json() == {"queued": 0}
    client.post(f"/api/sheets/{sid}/columns", json={"questions": ["Stack?"]})
    assert client.post(f"/api/sheets/{sid}/run", json={}).json() == {"queued": 1}
    wait_for(client, sid, lambda d: len(d["cells"]) == 2 and all(c["status"] == "done" for c in d["cells"]))
    assert client.post(f"/api/sheets/{sid}/run", json={"force": True}).json() == {"queued": 2}


def test_failing_cell_retries_then_errors_without_blocking_others(client):
    sheet = make_sheet(client, ["bad corp", "Acme"], ["Hiring?"])
    sid = sheet["sheet"]["id"]
    client.post(f"/api/sheets/{sid}/run", json={})
    data = wait_for(client, sid, lambda d: len(d["cells"]) == 2 and all(c["status"] in ("done", "error") for c in d["cells"]))
    by_status = {c["status"] for c in data["cells"]}
    assert by_status == {"done", "error"}
    err = next(c for c in data["cells"] if c["status"] == "error")
    assert "upstream down" in err["error"]


def test_editing_a_question_invalidates_its_answers(client):
    sheet = make_sheet(client, ["Acme"], ["Hiring?"])
    sid, col = sheet["sheet"]["id"], sheet["columns"][0]["id"]
    client.post(f"/api/sheets/{sid}/run", json={})
    wait_for(client, sid, lambda d: d["cells"] and d["cells"][0]["status"] == "done")
    client.patch(f"/api/columns/{col}", json={"question": "Remote roles?"})
    assert client.get(f"/api/sheets/{sid}").json()["cells"] == []


def test_limits_and_validation(client):
    sheet = make_sheet(client, ["a", "b", "c", "d", "e"], ["q1?", "q2?", "q3?"])
    sid = sheet["sheet"]["id"]
    assert client.post(f"/api/sheets/{sid}/rows", json={"entities": ["f"]}).status_code == 422
    assert client.post(f"/api/sheets/{sid}/columns", json={"questions": ["q4?"]}).status_code == 422
    assert client.post(f"/api/sheets/{sid}/columns", json={"questions": ["x"]}).status_code == 422
    assert client.get("/api/sheets/does-not-exist").status_code == 404
    assert client.post("/api/sheets/does-not-exist/run", json={}).status_code == 404


def test_delete_sheet_and_list_by_ids(client):
    a = make_sheet(client, ["A"], ["Q one?"])["sheet"]["id"]
    b = make_sheet(client, ["B"], ["Q two?"])["sheet"]["id"]
    assert len(client.get(f"/api/sheets?ids={a},{b},nope").json()) == 2
    assert client.delete(f"/api/sheets/{a}").status_code == 204
    assert client.get(f"/api/sheets/{a}").status_code == 404


def test_healthz(client):
    assert client.get("/healthz").json() == {"ok": True, "worker": True, "usage": {}}


# ---- scalability primitives -------------------------------------------------
async def test_claiming_is_exclusive_across_workers():
    """Two concurrent claimers must never receive the same cell."""
    be = MemoryBackend()
    repo = Repo(be)
    for i in range(20):
        await be.insert("cells", {"status": "queued", "queued_at": f"{i:02d}", "attempts": 0})
    a, b = await asyncio.gather(repo.claim_cells(15, 180), repo.claim_cells(15, 180))
    ids_a, ids_b = {c["id"] for c in a}, {c["id"] for c in b}
    assert not ids_a & ids_b
    assert len(ids_a | ids_b) == 20


async def test_stale_running_cells_are_reclaimed():
    be = MemoryBackend()
    repo = Repo(be)
    await be.insert("cells", {"status": "running", "locked_at": "2000-01-01T00:00:00+00:00", "attempts": 1})
    await be.insert("cells", {"status": "running", "locked_at": "2999-01-01T00:00:00+00:00", "attempts": 1})
    claimed = await repo.claim_cells(10, 180)
    assert len(claimed) == 1 and claimed[0]["attempts"] == 2


async def test_cache_dedupes_inflight_requests():
    cache, calls = TTLCache(60), 0

    async def slow():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return "v"

    results = await asyncio.gather(*(cache.get_or_compute("k", slow) for _ in range(10)))
    assert results == ["v"] * 10 and calls == 1
    assert await cache.get_or_compute("k", slow) == "v" and calls == 1


async def test_retry_backs_off_on_429_only():
    class E(Exception):
        status_code = 429

    attempts = 0

    async def flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise E()
        return "ok"

    assert await retry_async(flaky, attempts=4, base=0.001) == "ok" and attempts == 3

    async def fatal():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        await retry_async(fatal, attempts=4, base=0.001)


async def test_rate_limiter_delays_excess_calls():
    lim = RateLimiter(2, per=0.2)
    t0 = time.monotonic()
    for _ in range(3):
        await lim.acquire()
    assert time.monotonic() - t0 >= 0.18


def test_window_counter():
    w = WindowCounter(2)
    assert [w.allow("ip") for _ in range(3)] == [True, True, False]
    assert w.allow("other")


async def test_backed_off_cell_is_not_claimable_until_due():
    from app.store import iso_in

    be = MemoryBackend()
    repo = Repo(be)
    await be.insert("cells", {"status": "queued", "queued_at": iso_in(60), "attempts": 1})
    assert await repo.claim_cells(5, 180) == []


def test_budget_caps_calls_and_is_not_retryable():
    from app.resilience import Budget, BudgetExceeded

    b = Budget("t", 2, "day")
    assert [b.try_spend() for _ in range(3)] == [True, True, False]
    assert BudgetExceeded.retryable is False


def test_cors_allows_vercel_preview_hosts(client):
    for origin, ok in [
        ("https://grid-mind-tan.vercel.app", True),
        ("https://grid-mind-git-main-case-compass1.vercel.app", True),
        ("https://evil-grid-mind.vercel.app", False),
    ]:
        r = client.get("/healthz", headers={"Origin": origin})
        assert (r.headers.get("access-control-allow-origin") == origin) is ok, origin
