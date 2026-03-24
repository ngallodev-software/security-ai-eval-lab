# Evaluation Report: live-anthropic-2026-03-23

**Model:** anthropic:claude-haiku-4-5-20251001  
**Generated:** 2026-03-24 05:24 UTC  
**Samples:** 10  
**Accuracy:** 80.0%

## Classification Metrics

| Label | Support | Precision | Recall | F1 | TP | FP | FN |
|-------|---------|-----------|--------|----|----|----|----|
| benign | 4 | 1.00 | 1.00 | 1.00 | 4 | 0 | 0 |
| phishing | 4 | 0.67 | 1.00 | 0.80 | 4 | 2 | 0 |
| impersonation | 2 | 0.00 | 0.00 | 0.00 | 0 | 0 | 2 |

Macro avg: P=0.56 R=0.67 F1=0.60
Micro avg: P=0.80 R=0.80 F1=0.80
Weighted avg: P=0.67 R=0.80 F1=0.72
Total support: 10

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

## Confusion Matrix

| Actual \ Predicted | benign | phishing | impersonation |
|---|---|---|---|
| benign | 4 | 0 | 0 |
| phishing | 0 | 4 | 0 |
| impersonation | 0 | 2 | 0 |

## Explanation Support

Supported: 9
Weak: 0
Unsupported: 1
Unavailable: 0

| Sample | Actual | Predicted | Status | Notes |
|--------|--------|-----------|--------|-------|
| imp_001 | impersonation | phishing | unsupported | high-risk label with no supporting signals |

## Results

| Sample | Actual | Predicted | Match | Risk | Confidence | Support |
|--------|--------|-----------|-------|------|------------|---------|
| benign_001 | benign | benign | + | 0.15 | 0.82 | supported |
| benign_002 | benign | benign | + | 0.15 | 0.85 | supported |
| benign_003 | benign | benign | + | 0.15 | 0.82 | supported |
| benign_004 | benign | benign | + | 0.25 | 0.72 | supported |
| imp_001 | impersonation | phishing | - | 0.82 | 0.85 | unsupported |
| imp_002 | impersonation | phishing | - | 0.95 | 0.98 | supported |
| phish_001 | phishing | phishing | + | 0.98 | 0.99 | supported |
| phish_002 | phishing | phishing | + | 0.95 | 0.92 | supported |
| phish_003 | phishing | phishing | + | 0.95 | 0.98 | supported |
| phish_004 | phishing | phishing | + | 0.92 | 0.95 | supported |

## Per-Sample Execution Details

### benign_001
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1481
- Input tokens: 257
- Output tokens: 111
- Token cost (USD): 0.0006496
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: c6097648-2617-48c9-a1b4-a1f010a87cd4
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 0795d244-a602-517d-ae1d-ec4be311de04

### benign_002
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1733
- Input tokens: 252
- Output tokens: 112
- Token cost (USD): 0.0006496
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: 4258df70-379b-488a-8b18-2cbe6d1552de
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: b149f2c4-09c9-5215-970c-1d91ebd27ee0

### benign_003
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1310
- Input tokens: 256
- Output tokens: 113
- Token cost (USD): 0.0006568
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: 3870087e-a993-4fd4-a3b1-3916842b468e
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 6841684b-0d7a-5f0d-9ed8-c9d565ec24aa

### benign_004
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1217
- Input tokens: 264
- Output tokens: 100
- Token cost (USD): 0.0006112
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: ea83bcb3-49cc-4c96-ad66-aa74014e117d
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 9a29d096-1751-5ab6-bead-0568091f26f8

### imp_001
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1409
- Input tokens: 259
- Output tokens: 115
- Token cost (USD): 0.0006672
- Explanation support: unsupported
- Explanation support notes:
  - high-risk label with no supporting signals
- Reliability run id: 4640393f-2637-4d6e-8b71-303949bf4ce8
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 3ae1f5a4-1211-55ec-a872-407ea087b61c

### imp_002
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 2192
- Input tokens: 269
- Output tokens: 157
- Token cost (USD): 0.0008432
- Explanation support: supported
- Reliability run id: da9653c3-433a-41f6-96f8-ce33cf100c23
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 954584f1-8175-523b-bc8f-634c35872cea

### phish_001
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1769
- Input tokens: 315
- Output tokens: 152
- Token cost (USD): 0.00086
- Explanation support: supported
- Reliability run id: 3b3c5603-8e95-4ee4-9236-7bb3ccd262a8
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 4fd0f460-51ee-5d32-9c04-c2bd7edf01da

### phish_002
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1319
- Input tokens: 294
- Output tokens: 118
- Token cost (USD): 0.0007072
- Explanation support: supported
- Reliability run id: 7c58dc8c-3709-4fc0-87d4-ac027d7a1f20
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 3f74aec5-9895-51dd-bafa-52762f4e1a99

### phish_003
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 2017
- Input tokens: 293
- Output tokens: 154
- Token cost (USD): 0.0008504
- Explanation support: supported
- Reliability run id: 298e7478-fcff-47ad-8878-77ba29d4cbe8
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: d39288f3-c76c-5bc2-a91d-23f0a73f8864

### phish_004
- Provider: anthropic
- Model: claude-haiku-4-5-20251001
- Latency (ms): 1545
- Input tokens: 294
- Output tokens: 134
- Token cost (USD): 0.0007712
- Explanation support: supported
- Reliability run id: 3dbd3fb1-2873-48a7-bdad-898bd753ab06
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 9db416b1-cc6d-5bec-8999-b6ffa55333fa
