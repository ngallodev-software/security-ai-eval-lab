security-ai-eval-lab/
├── README.md
├── pyproject.toml              # declares ai-reliability-fw as a path dependency
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 0001_eval_lab_tables.py   # evaluation_runs + investigation_results
├── datasets/
│   ├── phishing/
│   ├── impersonation/
│   └── benign/
├── agents/
│   ├── email_threat_agent.py         # signal extraction + agent orchestration
│   └── reliability_adapter.py        # PhaseExecutor adapter (integration boundary)
├── llm/
│   └── anthropic_client.py           # AnthropicClient implementing BaseLLMClient
├── db/
│   ├── models.py                     # EvaluationRun, InvestigationResult ORM models
│   ├── repository.py                 # EvalRepository
│   └── session.py                    # async_session, get_db()
├── signals/
│   ├── auth_results.py
│   ├── domain_age.py
│   ├── brand_similarity.py
│   ├── domain_extract.py
│   ├── spf_dmarc.py
│   └── passive_dns.py
├── evaluation/
│   ├── runner.py                     # async end-to-end evaluation runner
│   ├── metrics.py                    # accuracy / precision / recall / F1
│   └── report.py
├── schemas/
│   ├── sample_schema.json
│   └── result_schema.json
├── examples/
│   └── run_eval.py                   # quickstart with FakeReliabilityExecutor
└── docs/
    ├── architecture.md
    ├── integration_boundary.md       # boundary doc: eval-lab ↔ ai-reliability-fw
    ├── dataset_notes.md
    ├── threat-task.md
    ├── mvp-boundaries.md
    └── reuse-plan.md
