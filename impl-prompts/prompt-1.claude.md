You are integrating two local Python projects I own:

1. ai-reliability-fw
2. security-ai-eval-lab

Goal:
Wire security-ai-eval-lab to use ai-reliability-fw as the LLM execution control plane for email threat classification and evaluation.

Architecture intent:
- One shared Postgres database, already running in Docker.
- ai-reliability-fw owns reliability-layer persistence:
  - workflows
  - prompts
  - workflow_runs
  - llm_calls
  - escalation_records
- security-ai-eval-lab owns evaluation-layer persistence:
  - evaluation_runs
  - investigation_results
- Do not duplicate llm_calls/workflow_runs/escalation_records in security-ai-eval-lab.
- Keep the integration narrow, explicit, and easy to understand.

Important known details from ai-reliability-fw:

PhaseExecutor:
- constructor:
  PhaseExecutor(repository: ReliabilityRepository, llm_client, validators: Sequence[BaseValidator])
- async method:
  async def execute(self, run_id, phase_id, prompt_id, input_artifact, retry_policy)
- input_artifact can be dict or string; execute() passes str(input_artifact) to self.llm.call(...)
- prompt_id is a UUID foreign key to prompts; it is not a template system
- execute() persists llm_calls, escalations, and run status internally
- caller must create workflow, prompt, and workflow_run rows before execute()

Current execute() success return:
{"status": "SUCCESS", "artifact": llm_result["response_raw"]}

DB/config conventions:
- SQLAlchemy async
- env var DATABASE_URL
- get_db() async context manager
- manual DI only
- RetryPolicy passed per call
- model name currently hardcoded inside execute()

Existing reliability table shape:
- workflow_runs.run_id UUID PK, workflow_id FK, status enum, created_at
- llm_calls.call_id UUID PK deterministic uuid5; run_id FK; phase_id UUID nullable; prompt_id FK; provider; model; retry_attempt_num; failure_category; latency_ms; response_raw; created_at; input_tokens; output_tokens; token_cost_usd
- escalation_records.escalation_id UUID PK; run_id FK; phase_id UUID nullable; llm_call_id FK nullable; retry_attempt_num; failure_category; trigger_reason; escalated_at

Tasks:
1. Make security-ai-eval-lab integrate ai-reliability-fw as a local library/dependency without copying reliability code.
2. Add a thin adapter in security-ai-eval-lab that:
   - creates/uses ReliabilityRepository via get_db()
   - creates required workflow, prompt, and workflow_run rows
   - serializes the email evidence bundle deterministically before calling execute()
   - calls PhaseExecutor.execute(...)
   - parses the returned artifact into:
     - predicted_label
     - risk_score
     - confidence
     - explanation
3. Use one reliability workflow_run per evaluated dataset sample.
4. Add eval-lab persistence for:
   - evaluation_runs
   - investigation_results
5. investigation_results must store:
   - evaluation_run_id
   - sample_id
   - actual_label
   - predicted_label
   - risk_score
   - confidence
   - explanation
   - signals_json
   - timeline_json
   - reliability_run_id
   - reliability_phase_id
   - reliability_prompt_id
   - reliability_call_id nullable
6. Keep metrics computed from investigation_results for now; do not add a separate metrics table unless absolutely necessary.
7. Add a minimal evaluation runner that:
   - loads JSON dataset samples
   - runs deterministic signal extraction
   - calls the reliability adapter
   - stores investigation_results
   - prints a compact summary
8. Keep naming investigation/evaluation oriented, not pentesting oriented.

Required code change in ai-reliability-fw:
Make PhaseExecutor.execute() return richer metadata on success:
- call_id
- provider
- model
- latency_ms
- input_tokens
- output_tokens
- token_cost_usd

This change must be backward-safe and minimal.

Constraints:
- Do not add UI, dashboards, workers, queues, DAG orchestration, or offensive tooling.
- Do not redesign ai-reliability-fw broadly.
- Do not invent YAML/settings frameworks.
- Follow existing SQLAlchemy and project conventions.
- Keep the code easy for a hiring manager to understand.

Deliverables:
- integration adapter
- minimal eval-lab ORM models + migrations
- minimal end-to-end runner
- short dev note describing the boundary between the two projects