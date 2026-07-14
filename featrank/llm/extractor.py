"""Structured extraction from raw feature request text via LLM."""

from __future__ import annotations

import json
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from featrank.llm._client import get_llm_client

_EXTRACTION_SYSTEM = (
    "You are a structured data extractor. "
    "Return only valid JSON. No explanation, no markdown fences."
)

_EXTRACTION_TEMPLATE = """\
Extract structured information from this feature request.
Return JSON only. No explanation.

Request: "{text}"

Return:
{{
  "feature_name": "2-4 word feature description",
  "pain_level": "low|medium|high|critical",
  "user_type": "inferred user type",
  "implies_churn_risk": true or false,
  "workaround_exists": true or false or null
}}"""

_LABEL_TEMPLATE = """\
You are a senior product manager. Given these feature requests and keywords,
generate a concise 3-5 word feature cluster name.

Keywords: {keywords}
Sample requests:
{requests}

Return only the feature name. No explanation. No punctuation at end."""


class ExtractedFeature(BaseModel):
    feature_name: str = ""
    pain_level: str = "medium"
    user_type: str = "unknown"
    implies_churn_risk: bool = False
    workaround_exists: Optional[bool] = None


class StructureExtractor:
    """Extract structured attributes from raw request text."""

    def extract(self, text: str) -> ExtractedFeature:
        prompt = _EXTRACTION_TEMPLATE.format(text=text[:800])
        try:
            client = get_llm_client()
            response = client.chat(
                system=_EXTRACTION_SYSTEM,
                user=prompt,
            )
            data = json.loads(response)
            return ExtractedFeature(**data)
        except Exception as exc:
            logger.debug(f"[extractor] Extraction failed: {exc}")
            return ExtractedFeature()


def label_cluster(texts: list[str], keywords: list[str]) -> str | None:
    """Generate a cluster label using the LLM. Returns None on failure."""
    sample = "\n".join(f"- {t}" for t in texts[:5])
    prompt = _LABEL_TEMPLATE.format(
        keywords=", ".join(keywords),
        requests=sample,
    )
    try:
        client = get_llm_client()
        return client.chat(system="You name feature clusters concisely.", user=prompt).strip()
    except Exception as exc:
        logger.debug(f"[extractor] label_cluster failed: {exc}")
        return None
