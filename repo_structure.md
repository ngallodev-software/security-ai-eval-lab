security-ai-eval-lab/
├── README.md
├── datasets/
│   ├── phishing/
│   └── benign/
├── agents/
│   └── email_threat_agent.py
├── signals/
│   ├── auth_results.py
│   ├── domain_age.py
│   ├── brand_similarity.py
│   └── domain_extract.py
├── evaluation/
│   ├── runner.py
│   ├── metrics.py
│   └── report.py
├── schemas/
│   ├── sample_schema.json
│   └── result_schema.json
├── examples/
│   └── run_eval.py
└── docs/
    ├── architecture.md
    └── threat-task.md