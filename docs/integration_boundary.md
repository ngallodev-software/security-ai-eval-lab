# Integration boundary: security-ai-eval-lab ↔ ai-reliability-fw

## What each project owns

| Concern | Owner |
|---|---|
| `workflows`, `prompts`, `workflow_runs`, `llm_calls`, `escalation_records` | `ai-reliability-fw` |
| `evaluation_runs`, `investigation_results` | `security-ai-eval-lab` |
| Metrics computation | `security-ai-eval-lab` |

Eval-lab does not duplicate reliability persistence. It stores only its own evaluation tables and the UUID cross-references back to the shared reliability rows.

## Shared infrastructure

One Postgres database, configured via `DATABASE_URL` env var, is used by both projects. Each project runs its own Alembic migrations against that database and owns a separate table set.

## How the integration works

```
JSON dataset sample
        │
        ▼
evaluation.runner.run_evaluation()      ← lives in security-ai-eval-lab/evaluation/runner.py
        │
        │ 1. loads the sample
        │ 2. runs deterministic signal extraction
        │ 3. builds a structured evidence bundle
        ▼
PhaseExecutorAdapter                    ← lives in security-ai-eval-lab/agents/reliability_adapter.py
        │
        │ persists workflow / prompt / workflow_run rows via ReliabilityRepository
        │ calls PhaseExecutor.execute()
        ▼
PhaseExecutor                           ← lives in ai-reliability-fw/src/engine/phase_executor.py
        │
        │ validates input -> calls AnthropicClient -> validates output -> retries / escalates
        │ persists llm_calls and escalation_records internally
        ▼
returns {"status": "SUCCESS", "artifact": "<json>", "call_id": ..., ...}
        │
        ▼
PhaseExecutorAdapter
        │ parses artifact JSON into predicted_label / risk_score / confidence / explanation
        │ surfaces reliability metadata (call_id, model, latency_ms, token_cost_usd)
        ▼
EvalRepository
        │ stores evaluation_runs and investigation_results
        │ metrics are computed from investigation_results
        └─ prints compact summary
```

`examples/run_eval.py` is a separate local quickstart path. It uses `EmailThreatInvestigationAgent` with `FakeReliabilityExecutor` and does not require Postgres or an API key.

## Cross-project references

`investigation_results` stores four UUID columns that reference ai-reliability-fw tables:

- `reliability_run_id` → `workflow_runs.run_id`
- `reliability_phase_id` → (phase UUID used inside the run)
- `reliability_prompt_id` → `prompts.prompt_id`
- `reliability_call_id` → `llm_calls.call_id` (nullable; null if run was escalated before a call completed)

These are stored as plain UUID columns without DB-level FK constraints. This keeps the two projects decoupled at the schema level, and either project can be migrated independently.

## What is deliberately NOT here

- No duplication of `workflows`, `prompts`, `workflow_runs`, `llm_calls`, or `escalation_records` in eval-lab.
- No custom retry or escalation logic — that belongs entirely to ai-reliability-fw.
- No UI, dashboards, queues, or DAG orchestration.
- No offensive or pentesting tooling.
