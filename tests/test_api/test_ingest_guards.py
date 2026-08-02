"""Focused ingest guard tests (no ML pipeline imports)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from featrank.api.rate_limit import MAX_INGEST_BODY_BYTES, ingest_rate_limit, limiter
from featrank.api.routes import ingest as ingest_route


def _make_app() -> FastAPI:
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.middleware("http")
    async def ingest_body_size_guard(request, call_next):  # type: ignore[no-untyped-def]
        import os

        max_bytes = int(
            os.environ.get("FEATRANK_MAX_INGEST_BODY_BYTES", str(MAX_INGEST_BODY_BYTES))
        )
        if request.url.path.rstrip("/") == "/ingest" and request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    length = int(content_length)
                except ValueError:
                    length = -1
                if length > max_bytes:
                    from fastapi.responses import JSONResponse

                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body exceeds maximum of {max_bytes} bytes"},
                    )
        return await call_next(request)

    app.include_router(ingest_route.router, prefix="/ingest")
    return app


def test_ingest_rate_limit_env(monkeypatch):
    monkeypatch.setenv("FEATRANK_RATE_LIMIT_INGEST", "5/minute")
    assert ingest_rate_limit() == "5/minute"


def test_ingest_rejects_too_many_requests(monkeypatch):
    monkeypatch.setenv("FEATRANK_MAX_INGEST_REQUESTS", "2")
    client = TestClient(_make_app())
    payload = {
        "requests": [
            {"id": "1", "text": "one", "source": "test"},
            {"id": "2", "text": "two", "source": "test"},
            {"id": "3", "text": "three", "source": "test"},
        ]
    }
    assert client.post("/ingest", json=payload).status_code == 413


def test_ingest_rejects_oversized_body(monkeypatch):
    monkeypatch.setenv("FEATRANK_MAX_INGEST_BODY_BYTES", "50")
    client = TestClient(_make_app())
    payload = {"requests": [{"id": "1", "text": "x" * 200, "source": "test"}]}
    assert client.post("/ingest", json=payload).status_code == 413


def test_ingest_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("FEATRANK_RATE_LIMIT_INGEST", "2/minute")
    limiter.reset()
    client = TestClient(_make_app())
    payload = {"requests": [{"id": "1", "text": "rate", "source": "test"}]}
    assert client.post("/ingest", json=payload).status_code == 200
    assert client.post("/ingest", json=payload).status_code == 200
    assert client.post("/ingest", json=payload).status_code == 429
