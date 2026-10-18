import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent.deps import build_deps
from .agent.graph import build_graph
from .api.routes import router
from .config import get_settings
from .events import make_bus
from .resilience import WindowCounter
from .runs.worker import Worker
from .store import make_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # per-request INFO lines drown the worker poll


def create_app(repo=None, bus=None, graph=None, settings=None) -> FastAPI:
    """App factory; tests inject a fake repo/graph, production uses env config."""
    s = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = s
        app.state.repo = repo or make_repo()
        app.state.bus = bus or make_bus()
        app.state.run_limiter = WindowCounter(s.runs_per_minute)
        app.state.create_limiter = WindowCounter(30)
        app.state.worker = None
        app.state.usage = lambda: {}
        if s.run_worker:
            deps = None if graph else build_deps(s)
            app.state.usage = deps.usage if deps else (lambda: {})
            g = graph or build_graph(deps)
            app.state.worker = Worker(app.state.repo, app.state.bus, g, s)
            app.state.worker.start()
        yield
        if app.state.worker:
            await app.state.worker.stop()
        await app.state.bus.close()

    app = FastAPI(title="GridMind API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in s.frontend_origin.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/healthz")
    async def healthz():
        return {"ok": True, "worker": app.state.worker is not None, "usage": app.state.usage()}

    return app


app = create_app()
