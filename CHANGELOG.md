# Changelog

All notable changes to `security-ai-eval-lab` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-22

Initial release. End-to-end evaluation pipeline for LLM email threat classification.

### Added
- `EmailThreatInvestigationAgent` — deterministic signal extraction + reliability-fw LLM classification
- `FakeReliabilityExecutor` — local stub for no-infra testing
- `PhaseExecutorAdapter` — live path through ai-reliability-fw `PhaseExecutor` with retry policy and output validation
- Deterministic signals: sender domain extraction, URL parsing, SPF/DKIM/DMARC parsing, domain age stub, brand similarity stub
- Dataset: 10 synthetic samples across phishing, impersonation, and benign categories
- `evaluation/runner.py` — async evaluation loop, dry-run + live paths, per-sample error handling
- `evaluation/metrics.py` — accuracy, precision, recall, F1 per label
- `evaluation/report.py` — JSON and Markdown file output to `outputs/`
- `llm/openai_client.py` — async OpenAI client implementing BaseLLMClient interface
- DB schema: `security_eval.evaluation_runs`, `security_eval.investigation_results`
- Alembic migrations: `0001_eval_lab_tables`, `0002_move_to_security_eval_schema`
- Docker: `Dockerfile`, `docker-compose.yml` with db + migrate + eval-lab services
- `.env.sample` with all required environment variables documented

---

## Semver policy

| Change type | Version bump | Example |
|---|---|---|
| New evaluation task, new signal type, new report format (additive) | **MINOR** `0.x.0` | adding a URL reputation signal |
| Breaking change to dataset schema, runner CLI flags, or report format | **MAJOR** `x.0.0` | renaming a label class |
| Bug fix, internal refactor, doc update | **PATCH** `0.0.x` | fixing a signal regex |

## Release process

```bash
# 1. Bump version in version.py and pyproject.toml
# 2. Update CHANGELOG.md — move Unreleased items under a new [x.y.z] heading
# 3. Commit:
git add version.py pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.x.y"

# 4. Tag:
git tag v0.x.y
git push origin master --tags
```

GitHub Actions will automatically create a GitHub Release on tag push.
