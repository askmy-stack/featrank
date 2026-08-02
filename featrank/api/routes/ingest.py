"""POST /ingest — accept raw feature requests."""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from loguru import logger

from featrank.api.rate_limit import ingest_rate_limit, limiter
from featrank.api.schemas import IngestRequest, IngestResponse

router = APIRouter()

_store: dict[str, list[Any]] = {}


@router.post("", response_model=IngestResponse)
@limiter.limit(ingest_rate_limit)
async def ingest(request: Request, response: Response, body: IngestRequest) -> IngestResponse:
    from featrank.api import rate_limit as rl

    max_requests = int(os.environ.get("FEATRANK_MAX_INGEST_REQUESTS", str(rl.MAX_INGEST_REQUESTS)))
    if len(body.requests) > max_requests:
        raise HTTPException(
            status_code=413,
            detail=f"At most {max_requests} requests allowed per ingest call",
        )
    job_id = str(uuid.uuid4())
    _store[job_id] = [r.model_dump() for r in body.requests]
    logger.info(f"[api/ingest] job_id={job_id}, count={len(body.requests)}")
    return IngestResponse(job_id=job_id, request_count=len(body.requests))


def get_job(job_id: str) -> list[Any] | None:
    return _store.get(job_id)
