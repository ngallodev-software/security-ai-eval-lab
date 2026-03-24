# Architecture & Data Flow — security-ai-eval-lab + ai-reliability-fw

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            security-ai-eval-lab                                  │
│                                                                                  │
│  ┌─────────────────┐    ┌────────────────────────┐    ┌──────────────────────┐  │
│  │  examples/       │    │  evaluation/runner.py  │    │  evaluation/         │  │
│  │  run_eval.py     │    │  (CLI entry point)     │    │  report.py           │  │
│  │  (quickstart)    │    │                        │    │  metrics.py          │  │
│  │                 │    │                        │    │  support_check.py    │  │
│  └────────┬─────────┘    └───────────┬────────────┘    └──────────────────────┘  │
│           │                          │                                            │
│           │              ┌───────────▼────────────┐                              │
│           │              │  agents/               │                              │
│           └─────────────►│  email_threat_agent.py │                              │
│                          │  EmailThreatInvestigationAgent                        │
│                          └───────────┬────────────┘                              │
│                                      │                                            │
│              ┌───────────────────────┼───────────────────────┐                   │
│              │                       │                        │                   │
│   ┌──────────▼──────────┐ ┌──────────▼────────────────────┐  │                   │
│   │  FakeReliability    │ │  agents/reliability_adapter.py│  │                   │
│   │  Executor           │ │  PhaseExecutorAdapter         │  │                   │
│   │  (dry-run / test)   │ │                               │  │                   │
│   └─────────────────────┘ └──────────┬────────────────────┘  │                   │
│                                      │                        │                   │
│                                      │  init_reliability()    │                   │
│                                      │  called at import      │                   │
│                                      │                        │                   │
│  ┌───────────────────────────────────┼────────────────────┐  │                   │
│  │           db/                     │                    │  │                   │
│  │  session.py  repository.py  models.py                  │  │                   │
│  │  (security_eval schema)           │                    │  │                   │
│  └───────────────────────────────────┼────────────────────┘  │                   │
│                                      │                        │                   │
└──────────────────────────────────────┼────────────────────────┘                   │
                                       │
                         ┌─────────────▼──────────────────────┐
                         │         ai-reliability-fw           │
                         │  (installed as Python package)      │
                         │                                     │
                         │  src/engine/phase_executor.py       │
                         │  src/engine/decision_engine.py      │
                         │  src/validators/                    │
                         │  src/db/session.py + repository.py  │
                         │  src/core/models.py                 │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │         PostgreSQL            │
                         │                              │
                         │  schema: reliability         │
                         │  ├── workflows               │
                         │  ├── workflow_runs           │
                         │  ├── prompts                 │
                         │  ├── llm_calls               │
                         │  └── escalation_records      │
                         │                              │
                         │  schema: security_eval       │
                         │  ├── evaluation_runs         │
                         │  └── investigation_results   │
                         └──────────────────────────────┘
```

---

## 2. Execution Paths

### Path A — Quickstart (no DB, no API key)

```
examples/run_eval.py
        │
        ├─ load_samples("datasets/")
        │       └─ JSON files: phishing/ impersonation/ benign/
        │
        └─ for each sample:
               EmailThreatInvestigationAgent(executor=FakeReliabilityExecutor())
               │
               └─ agent.analyze(email_text, sample_id)
                      │
                      ├─ [1] extract_sender_domain(email_text)      → domain | None
                      ├─ [2] extract_urls(email_text)               → list[str]
                      ├─ [3] parse_auth_results(email_text)         → {spf, dkim, dmarc}
                      ├─ [4] estimate_domain_age_days(domain)       → int | None
                      ├─ [5] compute_brand_similarity(text, domain) → BrandSimilarityResult
                      │
                      └─ FakeReliabilityExecutor.execute(payload)
                             │
                             └─ heuristic rules → predicted_label, risk_score, confidence
                                (no LLM, no network, no DB)
                             │
                             └─ InvestigationResult → print to stdout
```

### Path B — Full Evaluation (live LLM + DB persistence)

```
evaluation/runner.py  --dataset datasets/ --name run-001 --model gpt-4o-mini
        │
        ├─ load_samples("datasets/")
        │
        ├─ PhaseExecutorAdapter(llm_client=OpenAIClient(model))
        │       └─ init_reliability(DATABASE_URL)  ← called at adapter import time
        │
        ├─ eval_db: EvalRepository.create_evaluation_run(name, dataset, model)
        │       └─ INSERT security_eval.evaluation_runs → evaluation_run_id (UUID)
        │
        └─ for each sample:
               investigate_sample(sample, adapter)
               │
               ├─ Signal extraction [same 5 steps as Path A]
               │
               └─ adapter.execute_async(evidence_bundle={email_text, signals})
                      │
                      └─ [described in detail in section 3]
                      │
                      └─ returns {output, call_id, model, latency_ms,
                                  reliability_run_id, reliability_phase_id,
                                  reliability_prompt_id}
               │
               └─ EvalRepository.insert_investigation_result(result + reliability refs)
                       └─ INSERT security_eval.investigation_results
        │
        ├─ EvalRepository.mark_evaluation_run_complete()
        ├─ compute_classification_metrics() → macro/micro/weighted + per-label
        ├─ compute_confusion_matrix()
        ├─ evaluate_explanation_support()
        ├─ write_json_report()  → outputs/<name>.json
        └─ write_markdown_report()  → outputs/<name>.md
```

---

## 3. PhaseExecutorAdapter → PhaseExecutor Data Flow

```
PhaseExecutorAdapter.execute_async(evidence_bundle)
│
├─ reliability_get_db()       ← async generator, yields AsyncSession
│       └─ search_path: reliability,public
│
├─ repo = ReliabilityRepository(session)
│
├─ executor = PhaseExecutor(
│       repository=repo,
│       llm_client=OpenAIClient,
│       validators=[
│           InputIntegrityValidator(required_fields=["email_text","signals"]),
│           JsonSchemaValidator(schema={predicted_label,risk_score,confidence,explanation})
│       ]
│   )
│
├─ _ensure_workflow(repo)
│       └─ UPSERT reliability.workflows (workflow_id=fixed UUID, name="email_threat_investigation")
│
├─ _ensure_prompt(repo)
│       └─ UPSERT reliability.prompts (prompt_hash=sha256, content=system_prompt)
│       └─ returns prompt_id (UUID)
│
├─ _create_run(repo)
│       └─ INSERT reliability.workflow_runs (run_id=random UUID, status=RUNNING)
│       └─ returns run_id
│
├─ input_artifact = json.dumps(evidence_bundle, sort_keys=True)
│
└─ executor.execute(run_id, phase_id, prompt_id, input_artifact, retry_policy)
        │
        └─ [see section 4]
        │
        └─ returns fw_result
│
├─ if fw_result["status"] != "SUCCESS"
│       └─ raise RuntimeError   ← skip sample, don't bias metrics
│
└─ _normalize_success_payload(artifact_json, fw_result, run_id, phase_id, prompt_id)
        └─ returns {
               "output": {predicted_label, risk_score, confidence, explanation},
               "call_id", "provider", "model", "latency_ms",
               "input_tokens", "output_tokens", "token_cost_usd",
               "reliability_run_id", "reliability_phase_id", "reliability_prompt_id"
           }
```

---

## 4. PhaseExecutor Retry / Escalation Loop

```
PhaseExecutor.execute(run_id, phase_id, prompt_id, input_artifact, retry_policy)
│
├─ [PRE-CALL] InputIntegrityValidator.validate(input_artifact)
│       ├─ required_fields present and non-empty: ["email_text", "signals"]
│       └─ injection keywords: ["ignore previous instructions", "system prompt", "developer mode"]
│       │
│       └─ FAIL → create_escalation(INPUT_VALIDATION_ERROR)
│                  update_run_status(ESCALATED)
│                  return {"status": "HALTED"}
│
└─ RETRY LOOP  (attempt_num = 0;  while attempt_num <= max_retries=2)
        │
        ├─ call_id = uuid5(NAMESPACE_URL, f"{run_id}:{phase_id}:{prompt_id}:{attempt_num}")
        │                                                        ↑ deterministic, idempotent
        │
        ├─ OpenAIClient.call(input_artifact)
        │       ├─ POST /v1/chat/completions
        │       │       system: "You are a security investigation assistant. Return JSON only."
        │       │       user:   <serialized evidence bundle>
        │       │       response_format: json_object  /  max_tokens: 512
        │       └─ returns {response_raw, latency_ms, provider, model,
        │                   input_tokens, output_tokens, token_cost_usd}
        │
        ├─ [POST-CALL] JsonSchemaValidator.validate(response_raw)
        │       ├─ JSON parse check
        │       └─ schema: {predicted_label (enum), risk_score [0-1],
        │                   confidence [0-1], explanation (string)}
        │       └─ FAIL → failures = [SCHEMA_VIOLATION]
        │
        ├─ persist_llm_call({call_id, run_id, phase_id, prompt_id,
        │                    provider, model, retry_attempt_num,
        │                    latency_ms, response_raw, failure_category,
        │                    input_tokens, output_tokens, token_cost_usd})
        │       └─ UPSERT reliability.llm_calls  ON CONFLICT (call_id) DO NOTHING
        │
        └─ decide(failures, retry_policy, attempt_num)
                │
                ├─ no failures
                │       └─ COMPLETE
                │               update_run_status(COMPLETED)
                │               return {"status":"SUCCESS", artifact, call_id, ...}
                │
                ├─ SAFETY_FLAG or INPUT_VALIDATION_ERROR
                │       └─ ESCALATE immediately (no retry)
                │
                ├─ attempt_num >= max_retries (2)
                │       └─ ESCALATE
                │               create_escalation(failure_category, attempt_num, reason)
                │               update_run_status(ESCALATED)
                │               return {"status":"ESCALATED"}
                │
                ├─ no retry rule for failure_category
                │       └─ ESCALATE
                │
                └─ retry rule exists  (SCHEMA_VIOLATION → RERUN)
                        └─ RETRY → attempt_num += 1  → loop ↑
```

---

## 5. Database Schema

```
PostgreSQL  (single shared instance)
│
├── schema: reliability          ← owned by ai-reliability-fw
│   │
│   ├── workflows
│   │       workflow_id      UUID  PK
│   │       name             VARCHAR
│   │       version          VARCHAR
│   │       definition_json  JSONB
│   │       created_at       TIMESTAMP
│   │
│   ├── prompts
│   │       prompt_id        UUID  PK
│   │       prompt_hash      VARCHAR  UNIQUE    ← dedup key
│   │       content          TEXT
│   │       version_tag      VARCHAR
│   │       created_at       TIMESTAMP
│   │
│   ├── workflow_runs
│   │       run_id           UUID  PK
│   │       workflow_id      UUID  FK→workflows
│   │       status           ENUM(RUNNING, COMPLETED, FAILED, ESCALATED, REPLAYING)
│   │       created_at       TIMESTAMP
│   │       updated_at       TIMESTAMP
│   │
│   ├── llm_calls
│   │       call_id          UUID  PK           ← deterministic uuid5
│   │       run_id           UUID  FK→workflow_runs
│   │       phase_id         UUID
│   │       prompt_id        UUID  FK→prompts
│   │       provider         VARCHAR            (openai)
│   │       model            VARCHAR            (gpt-4o-mini)
│   │       retry_attempt_num  INTEGER
│   │       latency_ms       INTEGER
│   │       response_raw     TEXT
│   │       failure_category ENUM               (nullable)
│   │       input_tokens     INTEGER
│   │       output_tokens    INTEGER
│   │       token_cost_usd   NUMERIC(10,8)
│   │       created_at       TIMESTAMP
│   │
│   └── escalation_records
│           escalation_id    UUID  PK
│           run_id           UUID  FK→workflow_runs
│           phase_id         UUID
│           llm_call_id      UUID  FK→llm_calls  (nullable)
│           failure_category ENUM
│           retry_attempt_num  INTEGER
│           trigger_reason   TEXT
│           created_at       TIMESTAMP
│
└── schema: security_eval        ← owned by security-ai-eval-lab
    │
    ├── evaluation_runs
    │       id               UUID  PK
    │       name             VARCHAR              ← --name CLI arg
    │       dataset_name     VARCHAR
    │       model_label      VARCHAR
    │       prompt_version   VARCHAR
    │       status           VARCHAR
    │       started_at       TIMESTAMP
    │       completed_at     TIMESTAMP  (nullable)
    │
    └── investigation_results
            id               UUID  PK
            evaluation_run_id  UUID  FK→evaluation_runs
            sample_id        VARCHAR
            actual_label     VARCHAR   (phishing | impersonation | benign)
            predicted_label  VARCHAR
            risk_score       FLOAT
            confidence       FLOAT
            explanation      TEXT
            signals_json     JSONB
            timeline_json    JSONB
            ─── cross-project refs (UUID cols, no DB-level FK) ───
            reliability_run_id      UUID  → reliability.workflow_runs.run_id
            reliability_phase_id    UUID  → (denormalized phase identifier)
            reliability_prompt_id   UUID  → reliability.prompts.prompt_id
            reliability_call_id     UUID  → reliability.llm_calls.call_id
            created_at       TIMESTAMP
```

---

## 6. Signal Extraction Pipeline

```
email_text  (raw string)
        │
        ├──[1]─ extract_sender_domain()
        │           regex: From: ... <user@DOMAIN>
        │           → sender_domain: "company-helpdesk-reset.com" | None
        │
        ├──[2]─ extract_urls()
        │           regex: https?://[^\s]+
        │           → urls: ["https://..."] | []
        │
        ├──[3]─ parse_auth_results()
        │           scans for: spf=pass/fail  dkim=pass/fail  dmarc=pass/fail
        │           → {spf_result, dkim_result, dmarc_result}: "pass"|"fail"|None
        │
        ├──[4]─ estimate_domain_age_days(sender_domain)         [MVP stub — no WHOIS]
        │           keywords in domain: support, review, reset, secure, login → 7 days
        │           otherwise → 365 days  |  no domain → None
        │
        └──[5]─ compute_brand_similarity(email_text, sender_domain)  [MVP stub]
                    KNOWN_BRANDS: Microsoft, DocuSign, PayPal, Zoom, GitHub, Okta, Google
                    lookalike heuristics:
                        "micr0soft"  in domain → matched_brand=Microsoft,  score=0.93
                        "paypa1"     in domain → matched_brand=PayPal,     score=0.92
                        "docusign"   (non-.net) → matched_brand=DocuSign,  score=0.88
                    substring brand match → score=0.70
                    no match → score=0.00
                    → BrandSimilarityResult(matched_brand, score)
        │
        └─ Signals assembled → serialized as dict → evidence_bundle["signals"]
```

---

## 7. Package Dependency & Initialization

```
security-ai-eval-lab process startup
        │
        ├─ db/session.py imported
        │       └─ DATABASE_URL = os.environ["DATABASE_URL"]
        │          engine created with search_path: security_eval,public
        │
        ├─ import agents.reliability_adapter
        │       │
        │       ├─ from src.db.session import init_reliability
        │       ├─ from db.session import DATABASE_URL  ← eval-lab's own module
        │       │
        │       └─ init_reliability(DATABASE_URL)        ← called at module load
        │               │
        │               └─ _engine = create_async_engine(
        │                       DATABASE_URL,
        │                       connect_args={"server_settings":
        │                           {"search_path": "reliability,public"}}
        │                   )
        │               └─ _async_session = async_sessionmaker(_engine)
        │               └─ reliability-fw DB layer is now ready
        │
        └─ PhaseExecutorAdapter.execute_async() may now safely call get_db()


FakeReliabilityExecutor path (dry-run / quickstart):
        │
        └─ reliability_adapter.py is NOT imported
               → init_reliability() is NEVER called
               → no DB connection required
               → DATABASE_URL need not be set
```

---

## 8. Output Artifacts

```
outputs/<run-name>.json
{
    "run_name": "run-001",
    "model": "gpt-4o-mini",
    "generated_at": "2026-03-23T...",
    "summary": {
        "total_samples": 10,
        "accuracy": 0.80,
        "labels": {
            "phishing":      {"precision":0.75, "recall":0.75, "f1":0.75, "tp":3, "fp":1, "fn":1},
            "impersonation": {"precision":1.00, "recall":0.50, "f1":0.67, "tp":1, "fp":0, "fn":1},
            "benign":        {"precision":0.80, "recall":1.00, "f1":0.89, "tp":4, "fp":1, "fn":0}
        }
    },
    "results": [
        {
            "sample_id": "phish_001",
            "actual_label": "phishing",
            "predicted_label": "phishing",
            "risk_score": 0.85,
            "confidence": 0.92,
            "explanation": "...",
            "signals": { ... },
            "timeline": ["parse sender domain", "extract urls", ..., "complete (250 ms)"]
        },
        ...
    ]
}

outputs/<run-name>.md
    # Evaluation Report: run-001
    **Model:** gpt-4o-mini  |  **Samples:** 10  |  **Accuracy:** 80.0%

    ## Per-Label Metrics
    | Label        | Precision | Recall | F1   | TP | FP | FN |
    |-------------|-----------|--------|------|----|----|----|
    | phishing     | 0.75      | 0.75   | 0.75 | 3  | 1  | 1  |
    | impersonation| 1.00      | 0.50   | 0.67 | 1  | 0  | 1  |
    | benign       | 0.80      | 1.00   | 0.89 | 4  | 1  | 0  |

    ## Results
    | ID        | Actual       | Predicted    | Score | Conf |
    |-----------|-------------|--------------|-------|------|
    | phish_001 | phishing     | phishing     | 0.85  | 0.92 |
    | ...
```
