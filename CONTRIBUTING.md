# Contributing to featrank

Thank you for your interest in contributing!

## Development setup

```bash
git clone https://github.com/askmy-stack/featrank
cd featrank
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Running tests

```bash
pytest tests/
ruff check .
```

## Pull request guidelines

- Keep changes focused and well-tested
- Run `ruff check .` and `pytest tests/` before submitting
- Update documentation for user-facing changes
- Do not commit secrets or `.env` files

## Code style

- Python 3.10+
- Ruff for linting
- Type hints encouraged

## Good First Issues

Check [GitHub Issues](https://github.com/askmy-stack/featrank/issues?q=label%3A%22good+first+issue%22) for beginner-friendly tasks.
