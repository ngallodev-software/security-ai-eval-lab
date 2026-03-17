Goal

Verify the `security-ai-eval-lab` prompt-pack results inside this repo and apply only the smallest local corrective patch set if a concrete defect remains.

Repo And Branch Ownership

- Repo: `security-ai-eval-lab`
- Branch: `task/t06-verification`
- You are not alone in the codebase. Preserve existing local changes and adapt to them. Do not revert work from other agents or the user.

Write Scope

- Read all relevant files in this repo
- Do not edit by default
- If and only if you find a concrete defect, apply the smallest fix necessary in this repo

Read Context

- `impl-prompts/prompt-5-verification.open.md`
- `impl-prompts/guardrails.md`
- `agents/reliability_adapter.py`
- `evaluation/runner.py`
- `db/models.py`
- `db/repository.py`
- `migrations/versions/0001_eval_lab_tables.py`
- `docs/integration_boundary.md`

Required Changes

- Verify the eval-lab-owned items in `prompt-5-verification.open.md`.
- Confirm deterministic signal extraction happens before the framework call.
- Confirm eval-lab persists only its own tables.
- Confirm framework tables are not duplicated in eval-lab.
- Confirm one framework workflow run is created per evaluated sample from the eval-lab call path.
- Confirm investigation results store reliability IDs correctly.
- If any eval-lab-owned item fails, apply the smallest local corrective patch set and explain why.

Guardrails

- Follow `impl-prompts/guardrails.md`.
- Do not expand scope after finding one issue.
- Prefer verification-only completion if the integrated state is already correct.
- Do not edit files outside `security-ai-eval-lab`.

Required Validation

- Run the narrowest set of checks that proves the integration.
- If the environment allows it, run:
  - `python -m evaluation.runner --dataset datasets --dry-run`
- If you patch anything, rerun only the checks needed to prove the fix.

Response Contract

- Report findings first, ordered by severity.
- If no findings exist, state that explicitly.
- List all changed file paths, or `none`.
- End with this exact footer:

```text
TASK_ID: t06
STATUS: <completed|blocked>
TOKENS_USED: <number>
ELAPSED_SECONDS: <number>
ERRORS_ENCOUNTERED: <none or brief list>
TESTS_RUN: <command summary or none>
CHANGED_FILES: <comma-separated paths or none>
SUMMARY: <one short paragraph>
```
