Review the current integration between security-ai-eval-lab and ai-reliability-fw and verify all of the following:

1. security-ai-eval-lab uses ai-reliability-fw as the LLM execution control plane.
2. deterministic signal extraction happens before the reliability framework call.
3. eval-lab persists its own evaluation_runs and investigation_results tables.
4. llm_calls, workflow_runs, escalation_records, workflows, and prompts are not duplicated in eval-lab.
5. one reliability workflow_run is created per evaluated sample.
6. investigation_results correctly link back to reliability IDs.
7. PhaseExecutor.execute() returns richer success metadata with minimal code change.
8. the evaluation runner works end-to-end on the starter dataset.
9. no unnecessary abstractions or scope creep were introduced.

If any item fails, propose the smallest corrective patch set.