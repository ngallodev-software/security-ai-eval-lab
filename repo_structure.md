security-ai-eval-lab/
├── README.md
├── pyproject.toml              # package metadata + ai-reliability-fw dependency pin
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
│   ├── email_threat_agent.py         # current signal helpers + agent orchestration
│   └── reliability_adapter.py        # PhaseExecutor adapter (integration boundary)
├── llm/
│   ├── anthropic_client.py           # AnthropicClient implementing BaseLLMClient
│   └── openai_client.py              # OpenAIClient implementing BaseLLMClient
├── db/
│   ├── models.py                     # EvaluationRun, InvestigationResult ORM models
│   ├── repository.py                 # EvalRepository
│   └── session.py                    # async_session, get_db()
├── signals/
│   ├── auth_results.py               # placeholder module stubs for future extraction
│   ├── domain_age.py
│   ├── brand_similarity.py
│   ├── domain_extract.py
│   ├── spf_dmarc.py
│   └── passive_dns.py
├── evaluation/
│   ├── runner.py                     # async end-to-end evaluation runner
│   ├── db_report.py                  # DB-backed JSON/Markdown/HTML report generator
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
