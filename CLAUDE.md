# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Quickstart — no DB or API key needed
python3 -m examples.run_eval

# Full evaluation run — OpenAI (requires DATABASE_URL and OPENAI_API_KEY)
python3 -m evaluation.runner --dataset datasets/ --name my-run-001 --model gpt-4o-mini

# Full evaluation run — Anthropic (requires DATABASE_URL and ANTHROPIC_API_KEY)
python3 -m evaluation.runner --dataset datasets/ --name my-run-001 --provider anthropic --model claude-haiku-4-5-20251001

# Dry-run (inference only, no DB writes)
python3 -m evaluation.runner --dataset datasets/ --name test --dry-run

# Apply eval-lab migrations
alembic upgrade head

# Install (editable)
pip install -e .
```

## Environment

Both `security-ai-eval-lab` and `ai-reliability-fw` share a single Postgres instance via `DATABASE_URL`. Each project runs its own Alembic migrations against it.

Required env vars:
- `DATABASE_URL` — PostgreSQL URL (asyncpg driver, e.g. `postgresql+asyncpg://...`)
- `OPENAI_API_KEY` — required when using OpenAI provider
- `ANTHROPIC_API_KEY` — required when using Anthropic provider

Classification stage (fw PhaseExecutor) — resolved in priority order:
- `CLASSIFICATION_PROVIDER` — provider for the classification LLM (`openai` or `anthropic`)
- `CLASSIFICATION_MODEL` — model ID for the classification LLM
- Falls back to `LLM_PROVIDER` / `DEFAULT_MODEL` if unset
- Both overridden by `--provider` / `--model` CLI args

## Architecture

This is a research framework for evaluating LLM performance on security classification tasks (phishing, impersonation, benign). It is not a production system.

### Two execution paths

**Quickstart path** (`examples/run_eval.py`): Uses `EmailThreatInvestigationAgent` with `FakeReliabilityExecutor`. No Postgres, no API key. Good for wiring tests.

**Full evaluation path** (`evaluation/runner.py`): Uses `PhaseExecutorAdapter` → `ai-reliability-fw`'s `PhaseExecutor` → OpenAI API. Persists results to Postgres.

### Layered design

```
JSON dataset sample
  → evaluation/runner.py         — loads samples, drives per-sample flow
  → signals/ (deterministic)     — domain extraction, URL parsing, auth parsing, brand similarity, domain age
  → agents/reliability_adapter.py (PhaseExecutorAdapter)
      → ai-reliability-fw PhaseExecutor  — validates input, calls LLM, validates output, retries/escalates
  → db/repository.py (EvalRepository)   — writes evaluation_runs + investigation_results
  → evaluation/metrics.py        — accuracy, precision, recall, F1
```

### Key architectural constraints

**Table ownership is split across two projects.** `ai-reliability-fw` owns `workflows`, `prompts`, `workflow_runs`, `llm_calls`, and `escalation_records`. This project owns only `evaluation_runs` and `investigation_results`. The `investigation_results` table references reliability-fw rows via four UUID columns (`reliability_run_id`, `reliability_phase_id`, `reliability_prompt_id`, `reliability_call_id`) with no DB-level FK constraints — intentionally decoupled.

**`PhaseExecutorAdapter` manages its own reliability DB session.** It opens a session via the reliability-fw's `get_db()` factory directly. The evaluation runner never touches the reliability session; it only touches the eval-lab session (`db/session.py`).

**Deterministic signals run before any LLM call.** The signals in `agents/email_threat_agent.py` (domain extraction, URL parsing, auth parsing, brand similarity, domain age) are stub implementations for the MVP. The `signals/` directory contains more complete module stubs. Real WHOIS and DNS lookups are not yet implemented.

**`FakeReliabilityExecutor`** is the local testing stub. It implements the same `execute` / `execute_async` interface as `PhaseExecutorAdapter` and returns deterministic label predictions based on heuristics — no network calls.

### ai-reliability-fw dependency

Located at `/lump/apps/ai-reliability-fw`. The runner dynamically adds `ai-reliability-fw/src` to `sys.path` at runtime via `_ensure_reliability_fw_on_path()`. The `pyproject.toml` also declares it as a local path dependency.

## Dataset format

Static JSON files under `datasets/phishing/`, `datasets/impersonation/`, `datasets/benign/`. Labels: `phishing`, `impersonation`, `benign`.

```json
{
  "id": "phish_001",
  "label": "phishing",
  "email_text": "From: ...\nSubject: ...\n\nBody text.",
  "metadata": { "source_type": "synthetic", "scenario": "credential harvest" }
}
```

## Guardrails

- `InputIntegrityValidator` rejects prompt-injection patterns before any LLM call.
- `JsonSchemaValidator` enforces the output schema (`predicted_label`, `risk_score`, `confidence`, `explanation`); schema violations trigger retries via `RetryPolicy`.
- If `PhaseExecutor` returns a non-SUCCESS status, the adapter raises `RuntimeError` — the runner logs and skips the sample rather than silently recording a fabricated label that would bias metrics.
