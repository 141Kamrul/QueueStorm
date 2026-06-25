"""FastAPI application for the QueueStorm Warmup mock preliminary round."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .classifier import classify
from .safety import scrub
from .schemas import HealthResponse, SortTicketRequest, SortTicketResponse

logger = logging.getLogger("queuestorm")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="QueueStorm Warmup",
    description=(
        "bKash SUST CSE Carnival 2026 mock preliminary — classifies "
        "customer support tickets into case type, severity, and department."
    ),
    version="1.0.0",
)

# -----------------------------------------------------------------------
# CORS — open by default for the mock round; tighten via env var in prod.
# -----------------------------------------------------------------------

_cors_origins_env = os.getenv("CORS_ORIGINS", "*")
_cors_origins: List[str] = (
    ["*"] if _cors_origins_env.strip() == "*" else [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="queuestorm-warmup")


@app.post("/sort-ticket", response_model=SortTicketResponse, tags=["tickets"])
async def sort_ticket(req: SortTicketRequest) -> SortTicketResponse:
    try:
        result = classify(req.message, locale=req.locale)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("classification failed")
        raise HTTPException(status_code=500, detail=f"classification failed: {exc}") from exc

    safe_summary = scrub(result.agent_summary)

    return SortTicketResponse(
        ticket_id=req.ticket_id,
        case_type=result.case_type,
        severity=result.severity,
        department=result.department,
        agent_summary=safe_summary,
        human_review_required=result.human_review_required,
        confidence=result.confidence,
    )


# -----------------------------------------------------------------------
# Static frontend (production)
# -----------------------------------------------------------------------
# After `npm run build` the compiled bundle lives at App/frontend/dist.
# We mount it at "/" so a single HTTPS URL serves both the UI and the API.
# This is overridden by the dev workflow where Vite serves the frontend
# on :5173 and proxies /api to this server.

_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    assets_dir = _FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="frontend-assets",
        )

    @app.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        index = _FRONTEND_DIST / "index.html"
        if not index.exists():
            return JSONResponse({"detail": "frontend not built"}, status_code=404)
        return FileResponse(str(index))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_catchall(full_path: str):
        # Don't shadow API routes.
        if full_path.startswith(("sort-ticket", "health", "docs", "openapi", "assets")):
            raise HTTPException(status_code=404, detail="not found")
        index = _FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(status_code=404, detail="frontend not built")
else:

    @app.get("/", include_in_schema=False)
    async def root_dev():
        return JSONResponse(
            {
                "service": "queuestorm-warmup",
                "frontend": "not built — run `cd frontend && npm run build`",
                "endpoints": ["/health", "/sort-ticket", "/docs"],
            }
        )