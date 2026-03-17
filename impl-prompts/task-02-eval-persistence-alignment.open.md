Goal

Align eval-lab persistence to the intended evaluation schema and repository contract, without duplicating reliability-framework tables.

Repo And Branch Ownership

- Repo: `security-ai-eval-lab`
- Branch: `task/t02-eval-persistence`
- You are not alone in the codebase. Preserve existing local changes and adapt to them. Do not revert work from other agents or the user.

Write Scope

- `db/models.py`
- `db/repository.py`
- `migrations/versions/0001_eval_lab_tables.py`
- `db/__init__.py` only if needed

Read Context

- `impl-prompts/prompt-1.claude.md`
- `impl-prompts/prompt-2.claude.md`
- `impl-prompts/guardrails.md`
- `db/models.py`
- `db/repository.py`
- `migrations/versions/0001_eval_lab_tables.py`
- `evaluation/runner.py`

Required Changes

- Reconcile the current schema with the prompt-driven contract.
- Ensure ORM models, migration columns, and repository methods all agree on the same field names.
- `evaluation_runs` must support:
  - id or evaluation run primary key
  - run name
  - dataset identifier
  - model label
  - prompt version nullable
  - status
  - started timestamp
  - completed timestamp nullable
- `investigation_results` must support:
  - evaluation run link
  - sample and label fields
  - `risk_score`, `confidence`, `explanation`
  - `signals_json`, `timeline_json`
  - `reliability_run_id`, `reliability_phase_id`, `reliability_prompt_id`
  - `reliability_call_id` nullable
  - created timestamp
- Repository methods must cover:
  - create evaluation run
  - mark evaluation run complete
  - insert investigation result
  - list investigation results by evaluation run id
- Keep reliability IDs as plain UUID columns. Do not create DB-level cross-project foreign keys into framework tables.

Guardrails

- You must follow rules in `impl-prompts/guardrails.md`.
- Do not add new tables unless clearly required.
- Do not add a metrics table.
- Do not duplicate framework-owned tables.
- Keep changes readable and explicit.

Required Validation

- Check that the migration matches the ORM.
- Check that the repository method names and field names match the runner’s needs.
- If you change method names or schema fields, note all call sites the runner task must align with.

Response Contract

- Summarize the final schema and repository method contract.
- List all changed file paths.
- End with this exact footer:

```text
TASK_ID: t02
STATUS: <completed|blocked>
TOKENS_USED: <number>
ELAPSED_SECONDS: <number>
ERRORS_ENCOUNTERED: <none or brief list>
TESTS_RUN: <command summary or none>
CHANGED_FILES: <comma-separated paths or none>
SUMMARY: <one short paragraph>
```
