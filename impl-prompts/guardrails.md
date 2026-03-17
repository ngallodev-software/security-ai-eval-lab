Guardrails for this task:

Do not:
- build a generalized agent framework
- add DAG orchestration
- add multiple investigation types
- add a UI/dashboard
- add distributed workers/queues
- add active scanning or offensive-security capabilities
- copy ai-reliability-fw code into security-ai-eval-lab
- duplicate llm_calls, workflow_runs, or escalation_records in eval-lab
- redesign the reliability framework broadly

Do:
- keep the integration narrow
- focus on email threat investigation only
- preserve clean project boundaries
- keep one shared Postgres DB and separate table ownership
- make the code readable and easy to demo