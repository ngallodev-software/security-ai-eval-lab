Add the minimum evaluation persistence to security-ai-eval-lab.

follow impl-prompts/guardrails.md instructions

Requirements:
- One shared Postgres DB with ai-reliability-fw
- Separate eval-lab tables only
- SQLAlchemy style should match the repo
- Do not duplicate reliability-fw tables

Create table: evaluation_runs
Fields:
- id UUID PK
- name string
- dataset_name string
- model_label string nullable
- prompt_version string nullable
- status string/enum
- started_at datetime
- completed_at datetime nullable

Create table: investigation_results
Fields:
- id UUID PK
- evaluation_run_id FK -> evaluation_runs.id
- sample_id string
- actual_label string
- predicted_label string
- risk_score float
- confidence float
- explanation text nullable
- signals_json JSON/JSONB
- timeline_json JSON/JSONB
- reliability_run_id UUID
- reliability_phase_id UUID
- reliability_prompt_id UUID
- reliability_call_id UUID nullable
- created_at datetime

Add minimal repository methods to:
- create evaluation_run
- mark evaluation_run complete
- insert investigation_result
- list investigation_results by evaluation_run_id

Do not add more tables unless absolutely necessary.
Do not add a metrics table unless you prove it is needed.