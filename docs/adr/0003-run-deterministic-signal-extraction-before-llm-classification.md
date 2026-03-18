# 0003. Run deterministic signal extraction before LLM classification

## Status

Accepted

## Context

Email threat evaluation benefits from both deterministic evidence and model judgment. Pure LLM classification would make runs less auditable and harder to reason about, while a purely rule-based approach would miss context-sensitive patterns.

The repo already contains deterministic helpers for extracting sender domain, URLs, authentication results, domain age heuristics, and brand similarity.

## Decision

The evaluation flow will extract deterministic signals before calling the LLM-driven reliability path.

The LLM receives a structured evidence bundle that includes:

- the source email text
- extracted deterministic signals

The deterministic step remains explicit in the runner and agent-facing code rather than being hidden inside the framework integration.

## Consequences

The project keeps a clearer audit trail for why a classification was produced.

Signal extraction can be tested and evolved independently of LLM behavior.

The system still depends on the quality of the deterministic heuristics, so poor signal extraction can degrade downstream model performance.
