# 0001. Use `ai-reliability-fw` as the LLM execution control plane

## Status

Accepted

## Context

This project evaluates LLM-assisted email threat investigations, but it should not grow its own generalized reliability framework. The repo already depends conceptually on `ai-reliability-fw` for prompt execution, validation, retry behavior, and LLM call auditing.

Duplicating that logic inside `security-ai-eval-lab` would create two reliability implementations to maintain and would blur the boundary between evaluation concerns and framework concerns.

## Decision

`security-ai-eval-lab` will use `ai-reliability-fw` as its LLM execution control plane.

The eval lab will delegate these concerns to the framework:

- workflow and prompt persistence
- workflow run lifecycle
- input and output validation
- retry and escalation behavior
- LLM call persistence and metadata capture

The eval lab will keep only the narrow integration code needed to invoke the framework for email threat classification.

## Consequences

The project keeps a cleaner separation of concerns and avoids building a second reliability stack.

The eval lab becomes dependent on the framework’s runtime availability and contract shape.

Changes to the framework’s execution contract need to be reflected at the adapter boundary rather than throughout the eval codebase.
