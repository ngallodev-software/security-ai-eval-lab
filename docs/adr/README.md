# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the major design choices in `security-ai-eval-lab`.

The ADRs in this folder use the Nygard template:

- `Status`
- `Context`
- `Decision`
- `Consequences`

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](./0001-use-ai-reliability-fw-as-execution-control-plane.md) | Use `ai-reliability-fw` as the LLM execution control plane | Accepted |
| [0002](./0002-share-one-postgres-database-with-separate-table-ownership.md) | Share one Postgres database with separate table ownership | Accepted |
| [0003](./0003-run-deterministic-signal-extraction-before-llm-classification.md) | Run deterministic signal extraction before LLM classification | Accepted |
| [0004](./0004-use-a-thin-phaseexecutor-adapter-boundary.md) | Use a thin `PhaseExecutor` adapter boundary | Accepted |
| [0005](./0005-store-evaluation-results-separately-with-reliability-uuids.md) | Store evaluation results separately with reliability UUID references | Accepted |
| [0006](./0006-keep-the-runner-minimal-and-evaluation-focused.md) | Keep the runner minimal and evaluation-focused | Accepted |

## Status meanings

- `Accepted`: the decision is current and should guide ongoing work.
- `Superseded`: the decision was replaced by a newer ADR.
- `Proposed`: the decision is under consideration and not yet the default.
