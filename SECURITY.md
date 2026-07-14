# Security Policy

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

- Preferred: use GitHub's private vulnerability reporting for this repository
  (Security tab → **Report a vulnerability**).
- Alternative: email **kamineniabhinaysai@gmail.com** with a description of
  the issue, steps to reproduce, and its potential impact.

We aim to acknowledge reports within 7 days and to keep you updated as we
investigate and fix confirmed issues.

## Supported Versions

featrank does not yet have tagged releases; security fixes are applied to
the `main` branch. Run the latest `main` to get fixes as soon as they land.

## API Authentication

The FastAPI service (`featrank/api/main.py`) has **no inbound
authentication** and CORS is wide open (`allow_origins=["*"]`) by default.
This is intended for local/trusted use — add your own auth layer (reverse
proxy, API gateway, etc.) before exposing it on a shared or public network.

## External API Keys

`.env.example` / `featrank/config.py` list the external services this
project can integrate with: `GROQ_API_KEY` (LLM extraction/labeling, or use
a local Ollama instance instead), `GITHUB_TOKEN`, `INTERCOM_TOKEN`, and
`ZENDESK_*` tokens for ingesting feature requests from those sources. Treat
all of these as secrets — never commit real values, and rotate any key you
suspect may have leaked.

## Data Handled

featrank processes feature-request text, optional `user_id` values, and
MRR (revenue) figures ingested from CSV, Intercom, Zendesk, or GitHub.
Request text (truncated) and small samples of requests are sent to your
configured LLM provider (Groq or local Ollama) for extraction and cluster
labeling — **no PII redaction is applied** before this step, so avoid
ingesting sources containing data you don't want sent to your LLM provider.
Embeddings are cached locally under `.cache/embeddings`.
