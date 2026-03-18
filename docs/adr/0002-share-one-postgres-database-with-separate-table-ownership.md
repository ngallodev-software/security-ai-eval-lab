# 0002. Share one Postgres database with separate table ownership

## Status

Accepted

## Context

The evaluation flow needs to connect evaluation results with reliability-run metadata such as run IDs, prompt IDs, and call IDs. Using separate databases would add operational complexity and make cross-project investigation harder.

At the same time, these two projects should remain independently understandable and migratable.

## Decision

Both projects will use the same Postgres database through `DATABASE_URL`, but each project will own its own tables and migrations.

`ai-reliability-fw` owns reliability-layer tables such as:

- `workflows`
- `prompts`
- `workflow_runs`
- `llm_calls`
- `escalation_records`

`security-ai-eval-lab` owns evaluation-layer tables such as:

- `evaluation_runs`
- `investigation_results`

## Consequences

Operators only need one database for local demos and development.

Cross-project debugging is simpler because evaluation rows and reliability rows live in the same database.

Schema discipline matters more, because the projects share infrastructure but must not take ownership of each other’s tables.
