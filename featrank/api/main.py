"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from featrank import __version__
from featrank.api.rate_limit import MAX_INGEST_BODY_BYTES, limiter
from featrank.api.routes import ingest, cluster, rank, report, health

app = FastAPI(
    title="featrank API",
    description="Semantic feature request deduplication + priority ranking",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ingest_body_size_guard(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Reject oversized ingest payloads before parsing JSON."""
    if request.url.path.rstrip("/") == "/ingest" and request.method == "POST":
        import os

        max_bytes = int(os.environ.get("FEATRANK_MAX_INGEST_BODY_BYTES", str(MAX_INGEST_BODY_BYTES)))
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                length = -1
            if length > max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request body exceeds maximum of {max_bytes} bytes"
                        )
                    },
                )
    return await call_next(request)


app.include_router(health.router, tags=["health"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(cluster.router, prefix="/cluster", tags=["cluster"])
app.include_router(rank.router, prefix="/rank", tags=["rank"])
app.include_router(report.router, prefix="/report", tags=["report"])
