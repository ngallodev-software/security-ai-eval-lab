# Repository Guidelines

## Project Structure & Module Organization
`agents/` contains orchestration and the reliability adapter. `signals/` holds deterministic enrichment helpers such as domain, auth, and brand checks. `evaluation/` contains the runner, metrics, and report code. `db/` holds SQLAlchemy models, the async session, and repository logic. `llm/` wraps the Anthropic client. Labeled samples live in `datasets/`, Alembic migrations in `migrations/`, and architecture notes in `docs/` and `docs/adr/`. Use `examples/run_eval.py` for the quickstart path.

## Build, Test, and Development Commands
- `pip install -e .` installs the package in editable mode.
- `python3 -m examples.run_eval` runs the local fake-executor smoke test with no DB or API key.
- `python3 -m evaluation.runner --dataset datasets/ --name my-run-001 --model claude-haiku-4-5-20251001` runs the full evaluation flow.
- `python3 -m evaluation.runner --dataset datasets/ --name test --dry-run` exercises inference without writing results.
- `alembic upgrade head` applies database migrations.

Required environment variables for the full runner: `DATABASE_URL` and `ANTHROPIC_API_KEY`.

## Coding Style & Naming Conventions
Target Python 3.11 and follow standard PEP 8 conventions: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Keep deterministic signal extraction separate from LLM calls, and prefer explicit type hints and small, focused functions. There is no checked-in formatter or linter config, so match the existing style in nearby files.

## Testing Guidelines
This repository does not currently ship a formal automated test suite. Use `python3 -m examples.run_eval` as the fastest smoke test, and `python3 -m evaluation.runner --dry-run` to validate the main pipeline without DB writes. If you add tests, place them under `tests/` and name them `test_*.py`.

## Commit & Pull Request Guidelines
Recent commits use short, imperative, scope-prefixed messages such as `fix: ...` and `security: ...`. Keep commits focused and descriptive. Pull requests should explain the behavior change, list the commands you ran, and note any dataset or migration impact. Include sample output or screenshots when changing reporting or evaluation output.

## Security & Configuration Tips
Do not commit secrets or local credentials. This project shares a Postgres instance with `ai-reliability-fw`, but `security-ai-eval-lab` owns only its own tables and migrations. Be careful not to modify reliability-fw tables from this repository.
