# featrank

> Semantic feature request deduplication + priority ranking for product teams

[![PyPI](https://img.shields.io/pypi/v/featrank)](https://pypi.org/project/featrank/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## The Problem

Your users submit the same feature request 47 different ways across Intercom, Zendesk, Slack, and GitHub. Frequency-only ranking lets loud free-tier users drown out your highest-value enterprise customers. **featrank** deduplicates semantically, then ranks by actual business value.

---

## Install

```bash
pip install featrank
```

---

## Quickstart

```bash
# Copy and fill in your env vars
cp .env.example .env

# Run on built-in sample data
featrank demo

# Full pipeline on your own data
featrank ingest --source csv --file requests.csv --output data/raw/requests.json
featrank cluster --input data/raw/requests.json --output data/processed/clusters.json
featrank rank --clusters data/processed/clusters.json --roadmap roadmap.txt
featrank report --input data/processed/ranked.json --format markdown

# Or run everything in one shot
featrank run --source csv --file requests.csv --roadmap roadmap.txt
```

---

## How It Works

```
Raw requests (CSV / Intercom / Zendesk / GitHub)
  │
  ▼
TextCleaner          strip HTML, URLs, normalize whitespace
  │
  ▼
Embedder             sentence-transformers all-mpnet-base-v2
  │                  768-dim embeddings, disk-cached
  ▼
HDBSCANClusterer     no fixed K, handles noise automatically
  │
  ▼
ClusterLabeler       TF-IDF keywords + LLM 3-5 word label
  │
  ▼
CompositeRanker      4-signal weighted score → sorted list
  │
  ▼
Report               Markdown / JSON / Slack digest
```

---

## Scoring

| Signal | Default Weight | Description |
|---|---|---|
| **Frequency** | 20% | Normalized request count |
| **Segment Value** | 40% | Sum of MRR from requestors |
| **GitHub Signal** | 20% | Correlated open issues + PRs |
| **Roadmap Fit** | 20% | Cosine similarity vs your roadmap |

All weights are configurable via `.env` (must sum to 1.0).

---

## API

Start the server:

```bash
featrank serve
# or
docker-compose up
```

```bash
# Ingest (rate limited; max 1000 requests / 1 MB body by default)
curl -X POST localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"requests": [{"id":"1","text":"dark mode please","source":"intercom"}]}'
```

Ingest guards (override via env):

| Env | Default | Purpose |
|---|---|---|
| `FEATRANK_RATE_LIMIT_INGEST` | `30/minute` | Per-IP slowapi limit on `POST /ingest` |
| `FEATRANK_MAX_INGEST_REQUESTS` | `1000` | Max items in `requests` array |
| `FEATRANK_MAX_INGEST_BODY_BYTES` | `1000000` | Max JSON body size (413 if exceeded) |

```bash
# Cluster
curl -X POST localhost:8000/cluster \
  -d '{"job_id": "<job_id from above>"}'

# Rank
curl -X POST localhost:8000/rank \
  -d '{"clusters": [...], "roadmap_text": "..."}'

# Report
curl localhost:8000/report/<job_id>?format=markdown

# Health
curl localhost:8000/health
```

Full interactive docs: `http://localhost:8000/docs`

---

## CLI Commands

| Command | Description |
|---|---|
| `featrank demo` | Run full pipeline on built-in sample data |
| `featrank ingest` | Load requests from CSV / Intercom / Zendesk / GitHub |
| `featrank cluster` | Embed + cluster requests |
| `featrank rank` | Score and rank clusters |
| `featrank report` | Generate markdown / JSON / Slack report |
| `featrank run` | Full pipeline in one command |
| `featrank serve` | Start the FastAPI REST API |

---

## Benchmark

| Method | NDCG@5 | NDCG@10 |
|---|---|---|
| Random | ~0.31 | ~0.38 |
| Frequency-only | ~0.61 | ~0.67 |
| **featrank** | **~0.84** | **~0.89** |

Run your own benchmark:

```bash
python scripts/benchmark.py data/processed/ranked.json
```

---

## Environment Variables

```bash
cp .env.example .env
```

Key variables:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key (for LLM features) |
| `LLM_PROVIDER` | `groq` or `ollama` |
| `EMBEDDING_MODEL` | HuggingFace model id (default: `all-mpnet-base-v2`) |
| `GITHUB_TOKEN` | GitHub token for implementation signal |
| `GITHUB_REPO` | `owner/repo` to cross-reference |
| `WEIGHT_SEGMENT_VALUE` | MRR weight (default: 0.40) |

---

## Development

```bash
git clone https://github.com/askmy-stack/featrank
cd featrank
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Generate fixtures
python scripts/generate_fixtures.py 500

# Run tests
pytest tests/

# Start API in dev mode
uvicorn featrank.api.main:app --reload
```

---

## Research

**Title:** featrank: A Semantic Deduplication and Business-Value-Weighted Prioritization Framework for Product Feature Requests

**Target venue:** EMNLP Industry Track or ACL System Demonstrations

---

## License

MIT © askmy-stack
