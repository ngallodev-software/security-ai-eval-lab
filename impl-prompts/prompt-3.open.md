Implement a thin reliability adapter inside security-ai-eval-lab.

Guardrails:
you must follow rules in impl-prompts/guardrails.md 
Responsibilities:
- use DATABASE_URL
- open async SQLAlchemy session using the existing ai-reliability-fw get_db() pattern
- instantiate ReliabilityRepository
- instantiate PhaseExecutor
- build validators list
- accept a structured evidence bundle dict
- serialize it deterministically before execute()
- create any required workflow/prompt/workflow_run records before execute()
- call execute()
- normalize the returned payload into:
  - predicted_label
  - risk_score
  - confidence
  - explanation
  - reliability_run_id
  - reliability_phase_id
  - reliability_prompt_id
  - reliability_call_id if available
  - provider/model/latency/tokens/cost if available

Important:
- One reliability workflow_run per evaluated dataset sample
- Keep the adapter narrow
- Do not duplicate retry/validation logic in eval-lab
- Do not make eval-lab aware of unnecessary internal repository details

If workflow/prompt rows require names or content, use small deterministic placeholders suitable for the email threat classification MVP.