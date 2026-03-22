# MVP Scope

The project should stay intentionally small.

### Must exist

A. One high-quality task
Implement only:

EmailThreatInvestigationAgent
B. A few deterministic signals
Implement only:

SPF / DKIM / DMARC result parsing
sender domain extraction
domain age lookup
brand similarity check

C. One LLM reasoning step
Use the reliability framework to classify:

phishing
impersonation
benign / low risk

D. One dataset format
A simple JSON / JSONL schema is enough:

{
  "id": "sample_001",
  "email_text": "...",
  "label": "phishing"
}

E. One evaluation runner
Given a dataset and models, produce metrics.

F. One report output
At minimum:

console summary
JSON results
markdown report

### What To Avoid
Do NOT build:

a large agent platform
many investigation domains
a full UI
a live dashboard
dozens of tools
active scanning
malware / exploit capabilities
distributed orchestration
multi-tenant infrastructure
Do NOT optimize for:

completeness
feature breadth
real-time streaming
production hardening
Optimize for:

coherence
clarity
credibility
interview value