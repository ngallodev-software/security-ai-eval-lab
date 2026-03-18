# 0006. Keep the runner minimal and evaluation-focused

## Status

Accepted

## Context

This repo is intended to be easy to demo and easy to understand. A larger orchestration layer, job system, dashboard, or multi-stage pipeline would increase complexity without helping the current goal of evaluating email threat investigation quality.

The existing runner already follows a simple path: load samples, investigate each sample, persist evaluation results, and print compact metrics.

## Decision

The project will keep a minimal evaluation runner in `evaluation/runner.py`.

The runner is responsible for:

- loading dataset samples from JSON files
- executing deterministic signal extraction
- calling the reliability adapter once per sample
- persisting eval-lab-owned results
- printing compact evaluation metrics

The runner will not introduce broader orchestration concerns such as queues, DAGs, distributed workers, dashboards, or generalized multi-investigation workflows.

## Consequences

The project stays easy to explain and demo.

Local runs remain straightforward.

If the project later needs larger-scale execution patterns, those needs should be documented as new decisions rather than added implicitly.
