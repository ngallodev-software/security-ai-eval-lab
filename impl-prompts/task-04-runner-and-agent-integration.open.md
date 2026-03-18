Goal

Wire the evaluation runner and agent-facing contract to the persistence and adapter layers so the end-to-end flow is coherent and narrow.

Repo And Branch Ownership

- Repo: `security-ai-eval-lab`
- Branch: `task/t04-runner-integration`
- You are not alone in the codebase. Preserve existing local changes and adapt to them. Do not revert work from other agents or the user.

Write Scope

- `evaluation/runner.py`
- `agents/email_threat_agent.py`
- `examples/run_eval.py` only if needed for local coherence

Read Context

- `impl-prompts/prompt-1.claude.md`
- `impl-prompts/guardrails.md`
- `evaluation/runner.py`
- `agents/email_threat_agent.py`
- `db/repository.py`
- `agents/reliability_adapter.py`

Required Changes

- Keep deterministic signal extraction before the framework call.
- Align the runner with the final repository method names and schema field names from task `t02`.
- Align the runner with the final adapter output contract from task `t03`.
- Ensure one framework workflow run is created per sample by using one adapter execution per investigated sample.
- Persist `investigation_results` only on the non-dry-run path.
- Mark the evaluation run complete when processing is done.
- Keep the printed summary compact and useful.
- Keep naming investigation/evaluation oriented, not pentesting oriented.

Guardrails

- You must follow rules in `impl-prompts/guardrails.md`.
- Do not add new orchestration layers.
- Do not add async job systems or batching frameworks.
- Do not duplicate framework metadata tables in eval-lab.
- Keep changes limited to runner/agent wiring.

Required Validation

- Run a dry-run command if the environment allows it:
  - `python -m evaluation.runner --dataset datasets --dry-run`
- Confirm dry-run skips eval-lab writes.
- Confirm failure handling does not store fabricated results.

Response Contract

- Summarize the final runner flow in a few sentences.
- List all changed file paths.
- End with this exact footer:

```text
TASK_ID: t04
STATUS: <completed|blocked>
TOKENS_USED: <number>
ELAPSED_SECONDS: <number>
ERRORS_ENCOUNTERED: <none or brief list>
TESTS_RUN: <command summary or none>
CHANGED_FILES: <comma-separated paths or none>
SUMMARY: <one short paragraph>
```
