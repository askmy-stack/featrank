"""GET /report/{job_id} — retrieve formatted priority report."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse


router = APIRouter()

_report_store: dict[str, list] = {}


def save_report(job_id: str, ranked: list) -> None:
    _report_store[job_id] = ranked


@router.get("/{job_id}")
async def report(
    job_id: str,
    format: str = Query(default="markdown", regex="^(markdown|json|slack)$"),
) -> PlainTextResponse:
    data = _report_store.get(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No report found for job_id '{job_id}'")

    if format == "json":
        import json

        content = json.dumps([c if isinstance(c, dict) else c.model_dump() for c in data], indent=2)
        return PlainTextResponse(content=content, media_type="application/json")

    if format == "slack":
        from featrank.report.slack import SlackFormatter

        content = SlackFormatter().format(data)
        return PlainTextResponse(content=content, media_type="text/plain")

    from featrank.report.markdown import MarkdownFormatter

    content = MarkdownFormatter().format(data)
    return PlainTextResponse(content=content, media_type="text/markdown")
