"""Rate limiting and request size guards for featrank ingest."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def ingest_rate_limit(*_args, **_kwargs) -> str:
    return (os.environ.get("FEATRANK_RATE_LIMIT_INGEST", "30/minute").strip() or "30/minute")


limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

# Max feature requests per ingest call and max JSON body size (bytes).
MAX_INGEST_REQUESTS = int(os.environ.get("FEATRANK_MAX_INGEST_REQUESTS", "1000"))
MAX_INGEST_BODY_BYTES = int(os.environ.get("FEATRANK_MAX_INGEST_BODY_BYTES", str(1_000_000)))
