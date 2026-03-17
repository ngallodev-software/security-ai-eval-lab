Goal

Implement the thin reliability adapter inside `security-ai-eval-lab` using the existing framework patterns and keeping the boundary narrow.

Repo And Branch Ownership

- Repo: `security-ai-eval-lab`
- Branch: `task/t03-reliability-adapter`
- You are not alone in the codebase. Preserve existing local changes and adapt to them. Do not revert work from other agents or the user.

Write Scope

- `agents/reliability_adapter.py`
- Add one tiny helper under `agents/` only if strictly needed

Read Context

- `impl-prompts/prompt-3.open.md`
- `impl-prompts/prompt-1.claude.md`
- `impl-prompts/important-impl-notes.md`
- `impl-prompts/guardrails.md`
- `agents/reliability_adapter.py`
- `/lump/apps/ai-reliability-fw/src/db/repository.py`
- `/lump/apps/ai-reliability-fw/src/db/session.py`
- `/lump/apps/ai-reliability-fw/src/engine/phase_executor.py`
- `/lump/apps/ai-reliability-fw/src/validators/input_schema_validator.py`
- `/lump/apps/ai-reliability-fw/src/validators/json_schema_validator.py`

Required Changes

- Use `DATABASE_URL` through the framework’s existing `get_db()` pattern.
- Instantiate `ReliabilityRepository`.
- Instantiate `PhaseExecutor`.
- Build the validator list.
- Accept a structured evidence bundle dict.
- Serialize the evidence bundle deterministically before `execute()`.
- Create any required workflow, prompt, and workflow run rows before `execute()`.
- Call `execute()`.
- Normalize the return payload into:
  - `predicted_label`
  - `risk_score`
  - `confidence`
  - `explanation`
  - `reliability_run_id`
  - `reliability_phase_id`
  - `reliability_prompt_id`
  - `reliability_call_id` if available
  - `provider`, `model`, `latency_ms`, `input_tokens`, `output_tokens`, `token_cost_usd` if available
- Keep one framework workflow run per evaluated dataset sample.
- Use small deterministic placeholders for workflow/prompt content if names or content are required.

Guardrails

- You must follow rules in `impl-prompts/guardrails.md`.
- Keep the adapter narrow.
- Do not duplicate retry or validation logic in eval-lab.
- Do not make eval-lab aware of unnecessary repository internals.
- Do not edit runner, models, or repository files from this task.

Required Validation

- Verify deterministic serialization is explicit in code.
- Verify failure handling does not fabricate a successful classification.
- Verify the returned dict shape is stable for the runner task.

Response Contract

- Summarize the adapter contract and any assumptions you preserved.
- List all changed file paths.
- End with this exact footer:

```text
TASK_ID: t03
STATUS: <completed|blocked>
TOKENS_USED: <number>
ELAPSED_SECONDS: <number>
ERRORS_ENCOUNTERED: <none or brief list>
TESTS_RUN: <command summary or none>
CHANGED_FILES: <comma-separated paths or none>
SUMMARY: <one short paragraph>
```
