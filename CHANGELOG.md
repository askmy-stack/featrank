# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-08-06

### Added
- Ingest API rate limiting and request size caps
- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, and issue templates
- GitHub Actions CI (ruff + pytest)
- MIT `LICENSE`

### Fixed
- Pin `ruff` below 0.16 and fix ingest import sorting for CI stability

## [0.1.0] - 2026-07-01

### Added
- Initial scaffold: semantic deduplication pipeline, FastAPI API, CLI, tests, and notebooks
