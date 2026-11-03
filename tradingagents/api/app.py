from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tradingagents.api.manager import backtest_manager
from tradingagents.api.routes.backtest import router as backtest_router
from tradingagents.api.routes.config import router as config_router
from tradingagents.api.routes.mcp import router as mcp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pass running event loop to backtest manager for threadsafe SSE pushing
    loop = asyncio.get_running_loop()
    backtest_manager.set_loop(loop)
    yield


app = FastAPI(
    title="TradingAgents Web API",
    description="REST & SSE API for TradingAgents configuration, backtest execution, and analytics.",
    version="0.7.1",
    lifespan=lifespan,
)

# Enable CORS for local dev (Vite running on localhost:5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(config_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(mcp_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "TradingAgents Web API"}


# Mount static files if web/dist exists (production mode)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
