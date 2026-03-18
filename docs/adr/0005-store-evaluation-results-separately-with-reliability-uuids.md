# 0005. Store evaluation results separately with reliability UUID references

## Status

Accepted

## Context

The eval lab needs to persist its own evaluation runs and per-sample investigation results. It also needs enough linkage back to the reliability framework to trace what happened during execution.

Fully duplicating framework-owned records such as `llm_calls` or `workflow_runs` would create ownership confusion and increase drift risk.

## Decision

`security-ai-eval-lab` will store only its own evaluation tables and will link to framework-owned records by UUID values captured in `investigation_results`.

The evaluation layer stores:

- evaluation run metadata
- sample labels and predicted labels
- risk score, confidence, and explanation
- signal snapshots and timeline data
- reliability identifiers such as run, phase, prompt, and optional call UUIDs

These reliability identifiers are stored as plain UUID columns rather than as cross-project database foreign keys.

## Consequences

Evaluation data remains queryable on its own without copying framework tables.

Cross-project tracing is still possible through UUID references.

Integrity across project boundaries is enforced by application behavior and convention rather than by database foreign keys.
