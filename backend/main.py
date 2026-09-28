"""FastAPI application: JSON API + the dashboard frontend.

Run locally:
    uvicorn backend.main:app --reload --port 8000
Then open http://localhost:8000  (API docs at http://localhost:8000/docs)
"""
import hmac
import os
import threading
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .services import AppState, NotFound

state: Optional[AppState] = None
_rebuild_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global state
    state = AppState()
    yield


app = FastAPI(
    title="Nassau Candy — Factory Reallocation API",
    version=config.APP_VERSION,
    description="Where should each product ship from? Lead-time predictions, factory "
                "comparisons, ranked recommendations and risk checks.",
    lifespan=lifespan,
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["*"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


# --------------------------------------------------------------------- schemas
class PredictRequest(BaseModel):
    product: str = Field(..., examples=["Wonka Bar - Milk Chocolate"])
    region: str = Field(..., examples=["Pacific"])
    factory: str = Field(..., examples=["Lot's O' Nuts"])
    ship_mode: str = Field("Standard Class", examples=["Standard Class"])
    units: Optional[float] = Field(None, gt=0, le=10_000, description="Units per order (defaults to the historical average)")
    sales: Optional[float] = Field(None, ge=0, le=1_000_000, description="Order value in $ (defaults to the product average)")


# ------------------------------------------------------------------------ API
@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "version": config.APP_VERSION, "model_loaded": state.model is not None,
            "options": len(state.sim), "recommendations": len(state.recs),
            "data_generated_at": state.bundle.get("meta", {}).get("generated_at")}


@app.get("/api/meta", tags=["reference"])
def meta():
    """Products (with current factory), regions, factories, ship modes."""
    return state.meta()


@app.get("/api/summary", tags=["reference"])
def summary():
    """Headline numbers: orders analysed, win-win routes, estimated profit uplift."""
    return state.summary()


@app.get("/api/bundle", tags=["reference"])
def bundle():
    """Everything the dashboard renders from, in one document."""
    return JSONResponse(state.bundle, headers={"Cache-Control": "public, max-age=300"})


@app.get("/api/simulate", tags=["decisions"])
def simulate(product: str, region: str, ship_mode: str = "Standard Class"):
    """Where should this product ship from? Ranks every factory by predicted lead time."""
    return state.simulate(product, region, ship_mode)


@app.post("/api/predict", tags=["decisions"])
def predict(req: PredictRequest):
    """Live lead-time prediction from the trained model for any factory choice."""
    return state.predict(req.product, req.region, req.factory, req.ship_mode, req.units, req.sales)


@app.get("/api/compare", tags=["decisions"])
def compare(product: str, candidate: str):
    """Current factory vs a candidate factory for one product (Standard Class, all regions)."""
    return state.compare(product, candidate)


@app.get("/api/recommendations", tags=["decisions"])
def recommendations(
    region: Optional[List[str]] = Query(None, description="Repeat to filter several regions"),
    min_orders: int = Query(0, ge=0),
    priority: float = Query(0.5, ge=0, le=1, description="0 = profit first, 1 = speed first"),
    limit: int = Query(30, ge=1, le=500),
):
    """Ranked reassignment recommendations, same ranking as the dashboard table."""
    return state.recommendations(region, min_orders, priority, limit)


@app.get("/api/recommendations/top", tags=["decisions"])
def top_opportunities(n: int = Query(3, ge=1, le=20)):
    """The biggest opportunities right now."""
    return state.top_opportunities(n)


@app.get("/api/risk", tags=["decisions"])
def risk(limit: int = Query(15, ge=1, le=500)):
    """Recommendations that trade profit for speed, and ones with limited history."""
    return state.risk(limit)


@app.post("/api/admin/rebuild", tags=["system"])
def rebuild(full: bool = False, x_admin_token: Optional[str] = Header(None)):
    """Re-run the pipeline and reload data. Needs the ADMIN_TOKEN environment variable
    to be set on the server and sent as the X-Admin-Token header."""
    if not config.ADMIN_TOKEN:
        raise HTTPException(403, "Rebuild is disabled (ADMIN_TOKEN is not set on the server).")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, config.ADMIN_TOKEN):
        raise HTTPException(401, "Invalid admin token.")
    if not _rebuild_lock.acquire(blocking=False):
        raise HTTPException(409, "A rebuild is already running.")
    try:
        from .pipeline import rebuild_bundle_only, run_pipeline
        result = run_pipeline(include_eda=False) if full else rebuild_bundle_only()
        state.reload()
        return {"status": "rebuilt", **result}
    finally:
        _rebuild_lock.release()


@app.get("/api/{path:path}", include_in_schema=False)
def api_not_found(path: str):
    raise HTTPException(404, f"No API endpoint /api/{path}. See /docs.")


# ------------------------------------------------------------------- frontend
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(config.WEB_DIR, "index.html"), headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=config.WEB_DIR, html=True), name="web")
