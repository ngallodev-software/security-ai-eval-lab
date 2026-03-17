Goal

Update the docs to match the actual integration boundary, ownership split, and execution flow after the implementation tasks land.

Repo And Branch Ownership

- Repo: `security-ai-eval-lab`
- Branch: `task/t05-docs-boundary`
- You are not alone in the codebase. Preserve existing local changes and adapt to them. Do not revert work from other agents or the user.

Write Scope

- `docs/integration_boundary.md`
- `README.md`
- `repo_structure.md` only if needed

Read Context

- `impl-prompts/prompt-1.claude.md`
- `impl-prompts/guardrails.md`
- `docs/integration_boundary.md`
- `README.md`
- `repo_structure.md`
- `agents/reliability_adapter.py`
- `evaluation/runner.py`
- `db/models.py`

Required Changes

- Make the boundary document match the real final ownership split.
- Keep one shared Postgres DB with separate table ownership.
- State clearly that framework-owned persistence is not duplicated in eval-lab.
- Keep the README aligned with the final schema names, runner flow, and command examples.
- Remove or correct any doc claim that no longer matches the code.

Guardrails

- You must follow rules in `impl-prompts/guardrails.md`.
- Do not invent features not present in code.
- Do not turn the docs into product marketing copy.
- Keep the docs concise and technically accurate.

Required Validation

- Cross-check every changed doc claim against current code.
- Verify commands and file names are real.

Response Contract

- Summarize the docs you updated and the main corrections made.
- List all changed file paths.
- End with this exact footer:

```text
TASK_ID: t05
STATUS: <completed|blocked>
TOKENS_USED: <number>
ELAPSED_SECONDS: <number>
ERRORS_ENCOUNTERED: <none or brief list>
TESTS_RUN: <command summary or none>
CHANGED_FILES: <comma-separated paths or none>
SUMMARY: <one short paragraph>
```
