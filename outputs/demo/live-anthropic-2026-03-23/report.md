# Evaluation Report: live-anthropic-2026-03-23

**Model:** gpt-4o-mini  
**Generated:** 2026-03-23T00:00:00Z  
**Samples:** 10  
**Accuracy:** 80.0%

## Per-Label Metrics

| Label | Precision | Recall | F1 | TP | FP | FN |
|-------|-----------|--------|----|----|----|----|
| phishing | 0.67 | 1.00 | 0.80 | 4 | 2 | 0 |
| impersonation | 0.00 | 0.00 | 0.00 | 0 | 0 | 2 |
| benign | 1.00 | 1.00 | 1.00 | 4 | 0 | 0 |

## LLM Metadata

Providers: anthropic (10)
Models: claude-haiku-4-5-20251001 (10)
LLM calls: 10
Retries: 0
Total input tokens: 2753
Total output tokens: 1266
Total tokens: 4019
Total cost (USD): 0.007266
Total latency (ms): 15992.0
Avg latency (ms): 1599.2

## Results

| Sample | Actual | Predicted | Match | Risk | Confidence |
|--------|--------|-----------|-------|------|------------|
| benign_001 | benign | benign | + | 0.15 | 0.82 |
| benign_002 | benign | benign | + | 0.15 | 0.85 |
| benign_003 | benign | benign | + | 0.15 | 0.82 |
| benign_004 | benign | benign | + | 0.25 | 0.72 |
| imp_001 | impersonation | phishing | - | 0.82 | 0.85 |
| imp_002 | impersonation | phishing | - | 0.95 | 0.98 |
| phish_001 | phishing | phishing | + | 0.98 | 0.99 |
| phish_002 | phishing | phishing | + | 0.95 | 0.92 |
| phish_003 | phishing | phishing | + | 0.95 | 0.98 |
| phish_004 | phishing | phishing | + | 0.92 | 0.95 |
