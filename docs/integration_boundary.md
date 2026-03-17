# Integration boundary: security-ai-eval-lab ↔ ai-reliability-fw

## What each project owns

| Concern | Owner |
|---|---|
| Workflow / prompt / workflow_run rows | ai-reliability-fw |
| LLM calls, retry logic, escalations | ai-reliability-fw |
| Evaluation runs | security-ai-eval-lab |
| Investigation results | security-ai-eval-lab |
| Metrics computation | security-ai-eval-lab |

## Shared infrastructure

One Postgres database, configured via `DATABASE_URL` env var, is used by both projects. Each project runs its own Alembic migrations against that database.

## How the integration works

```
EmailThreatInvestigationAgent
        │
        │ calls execute_async()
        ▼
PhaseExecutorAdapter           ← lives in security-ai-eval-lab/agents/reliability_adapter.py
        │
        │ 1. persists workflow, prompt, workflow_run rows via ReliabilityRepository
        │ 2. calls PhaseExecutor.execute()
        ▼
PhaseExecutor                  ← lives in ai-reliability-fw/src/engine/phase_executor.py
        │
        │ validates input → calls AnthropicClient → validates output → retries/escalates
        │ persists llm_calls and escalation_records internally
        ▼
 returns {"status": "SUCCESS", "artifact": "<json>", "call_id": ..., ...}
        │
        ▼
PhaseExecutorAdapter
        │ parses artifact JSON into predicted_label / risk_score / confidence / explanation
        │ surfaces reliability metadata (call_id, model, latency_ms, token_cost_usd)
        ▼
EvaluationRunner               ← lives in security-ai-eval-lab/evaluation/runner.py
        │ stores investigation_results (with reliability_run_id / call_id cross-references)
        │ computes accuracy / precision / recall / F1
        └─ prints compact summary
```

## Cross-project references

`investigation_results` stores four UUID columns that reference ai-reliability-fw tables:

- `reliability_run_id` → `workflow_runs.run_id`
- `reliability_phase_id` → (phase UUID used inside the run)
- `reliability_prompt_id` → `prompts.prompt_id`
- `reliability_call_id` → `llm_calls.call_id` (nullable; null if run was escalated before a call completed)

These are stored as plain UUID columns without DB-level FK constraints. This keeps the two projects decoupled at the schema level — either project can be migrated independently.

## What is deliberately NOT here

- No duplication of `llm_calls`, `workflow_runs`, or `escalation_records` in eval-lab.
- No custom retry or escalation logic — that belongs entirely to ai-reliability-fw.
- No UI, dashboards, queues, or DAG orchestration.
- No offensive or pentesting tooling.
