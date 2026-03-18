# 0004. Use a thin `PhaseExecutor` adapter boundary

## Status

Accepted

## Context

The eval lab needs to call into `ai-reliability-fw`, but it should not leak framework internals throughout the codebase. Without a dedicated adapter, framework-specific setup and response normalization would spread into the runner and agent code.

The integration also needs a stable place to handle deterministic evidence serialization, setup of workflow-related rows, and normalization of the framework response.

## Decision

The project will isolate framework integration inside `agents/reliability_adapter.py`.

This adapter is responsible for:

- opening the framework DB session through the framework’s existing pattern
- creating or ensuring workflow, prompt, and run records
- deterministically serializing the evidence bundle before execution
- invoking `PhaseExecutor.execute(...)`
- normalizing the framework result into the shape expected by eval-lab callers

The adapter will remain narrow and will not reimplement framework-owned validation, retry, or persistence logic.

## Consequences

The rest of the eval lab can operate against a simpler contract.

Framework changes are more localized.

The adapter becomes the primary integration choke point, so its contract should remain small and explicit.
