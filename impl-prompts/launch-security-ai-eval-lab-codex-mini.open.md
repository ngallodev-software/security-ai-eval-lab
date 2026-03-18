Run the security-ai-eval-lab repo-local implementation pack using `gpt-5.4-mini` subagents.

This launch prompt is isolated to one repo only:
- `/lump/apps/security-ai-eval-lab`

Do not create branches, worktrees, edits, or commits in `ai-reliability-fw` from this prompt.

## Guardrails

- All tasks must follow `/lump/apps/security-ai-eval-lab/impl-prompts/guardrails.md`.
- Do not let any subagent work directly in the current live working tree.
- Do not reset, discard, or overwrite existing user changes.
- Keep all writes inside `security-ai-eval-lab`.

## Preflight

1. Inspect this repo only:
   - current branch
   - `git status --short`
   - whether the expected `impl-prompts` files exist
2. Preserve dirty state before creating worktrees:
   - create one repo-level safety branch from the current branch tip
   - create one local-only WIP preservation commit containing the current dirty state
   - do not push it
3. Create a fresh execution branch from the preserved commit SHA.
4. Create isolated worktrees under `/tmp/codex-worktrees/security-ai-eval-lab`.

## Branch names

- Repo-level execution branch: `plan/security-ai-eval-lab-reliability-integration`
- Task branches:
  - `task/t02-eval-persistence`
  - `task/t03-reliability-adapter`
  - `task/t04-runner-integration`
  - `task/t05-docs-boundary`
  - `task/t06-verification`

## Worktree roots

- `/tmp/codex-worktrees/security-ai-eval-lab/t02-eval-persistence`
- `/tmp/codex-worktrees/security-ai-eval-lab/t03-reliability-adapter`
- `/tmp/codex-worktrees/security-ai-eval-lab/t04-runner-integration`
- `/tmp/codex-worktrees/security-ai-eval-lab/t05-docs-boundary`
- `/tmp/codex-worktrees/security-ai-eval-lab/t06-verification`

## Task registry

- `t02` -> `/lump/apps/security-ai-eval-lab/impl-prompts/task-02-eval-persistence-alignment.open.md`
- `t03` -> `/lump/apps/security-ai-eval-lab/impl-prompts/task-03-reliability-adapter.open.md`
- `t04` -> `/lump/apps/security-ai-eval-lab/impl-prompts/task-04-runner-and-agent-integration.open.md`
- `t05` -> `/lump/apps/security-ai-eval-lab/impl-prompts/task-05-docs-boundary-and-usage.open.md`
- `t06` -> `/lump/apps/security-ai-eval-lab/impl-prompts/task-06-verification-and-corrective-sweep.open.md`

Launch order:
- Start `t02`, `t03`, and `t05` as soon as preflight and worktrees are ready.
- Start `t04` after `t02` and `t03` have landed or you have reviewed their diffs and can integrate them safely.
- Start `t06` only after the implementation tasks are integrated.

## Spawn settings

- Use `spawn_agent` with `agent_type=worker` for all tasks.
- Use model `gpt-5.4-mini`.
- Use `reasoning_effort=high` for `t02`, `t03`, `t04`, and `t06`.
- Use `reasoning_effort=medium` for `t05`.
- Do not delegate the main orchestration loop.

## Integration rules

- Review every agent diff before merging it back.
- Merge task results into the repo-level execution branch, not into the original working tree.
- Preserve unrelated local changes.
- If two tasks drift into the same file, stop and resolve carefully instead of blindly applying both.
- If `t06` finds a concrete defect, create one follow-up corrective task row and patch only the minimum required scope in this repo.

## Metrics ledger

Keep this table updated in this file as tasks progress.

| task_id | branch | worktree | agent_id | status | tokens_used | elapsed_seconds | errors_encountered | tests_run | changed_files |
|---|---|---|---|---|---:|---:|---|---|---|
| t02 | task/t02-eval-persistence | /tmp/codex-worktrees/security-ai-eval-lab/t02-eval-persistence | 019cfe44-769e-7bf0-909c-412c6b00d333 | completed | 8500 | 240 | python missing on PATH (used python3 instead) | python3 -m py_compile db/models.py db/repository.py migrations/versions/0001_eval_lab_tables.py; python3 contract-check script for ORM columns/repository methods | db/models.py, db/repository.py, migrations/versions/0001_eval_lab_tables.py |
| t03 | task/t03-reliability-adapter | /tmp/codex-worktrees/security-ai-eval-lab/t03-reliability-adapter | 019cfe44-76b9-7581-b114-cc56e21805b1 | completed | 6200 | 9 | python not found in PATH; rm blocked by policy; initial smoke test rerun with python3 and PYTHONPATH | python3 -m py_compile agents/reliability_adapter.py; PYTHONPATH=/lump/apps/ai-reliability-fw python3 - <<'PY' smoke test for deterministic serialization and normalized payload | agents/reliability_adapter.py |
| t04 | task/t04-runner-integration | /tmp/codex-worktrees/security-ai-eval-lab/t04-runner-integration | 019cfe47-9c02-70d0-887c-a6c7251d59fb | completed | 7200 | 900 | none | python3 -m evaluation.runner --dataset datasets --dry-run; git diff --check | agents/email_threat_agent.py, evaluation/runner.py |
| t05 | task/t05-docs-boundary | /tmp/codex-worktrees/security-ai-eval-lab/t05-docs-boundary | 019cfe44-76d1-7d23-8b28-9c758a1fc82f | completed | 8200 | 540 | initial `python3 -m evaluation.runner --help` failed until `PYTHONPATH=/lump/apps/ai-reliability-fw` was added | `PYTHONPATH=/lump/apps/ai-reliability-fw python3 -m evaluation.runner --help`; `git diff --check` | /tmp/codex-worktrees/security-ai-eval-lab/t05-docs-boundary/README.md, /tmp/codex-worktrees/security-ai-eval-lab/t05-docs-boundary/docs/integration_boundary.md |
| t06 | task/t06-verification | /tmp/codex-worktrees/security-ai-eval-lab/t06-verification | 019cfe4a-fdbe-7811-9a8e-53ee4645f1ae | completed | 5200 | 600 | none | python3 -m evaluation.runner --dataset datasets --dry-run | none |

Update rules:
- Set status to `running` when an agent starts.
- Set status to `completed` or `blocked` when it finishes.
- Copy `TOKENS_USED`, `ELAPSED_SECONDS`, and `ERRORS_ENCOUNTERED` exactly from the subagent footer.
- Record `TESTS_RUN` and `CHANGED_FILES` exactly as reported.
- If verification spawns a corrective task, append a new row instead of overwriting the original task record.

## Required final state

Before you finish:
- all task rows must be updated in the metrics ledger
- the repo-level execution branch must contain the accepted task changes
- verification must have either no findings or a minimal corrective patch set
- summarize token usage, elapsed time, and errors per task from the ledger
