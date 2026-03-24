# Evaluation Report: live-openai-2026-03-23

**Model:** openai:gpt-4o-mini-2024-07-18  
**Generated:** 2026-03-24 05:25 UTC  
**Samples:** 10  
**Accuracy:** 100.0%

## Classification Metrics

| Label | Support | Precision | Recall | F1 | TP | FP | FN |
|-------|---------|-----------|--------|----|----|----|----|
| benign | 4 | 1.00 | 1.00 | 1.00 | 4 | 0 | 0 |
| phishing | 4 | 1.00 | 1.00 | 1.00 | 4 | 0 | 0 |
| impersonation | 2 | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 |

Macro avg: P=1.00 R=1.00 F1=1.00
Micro avg: P=1.00 R=1.00 F1=1.00
Weighted avg: P=1.00 R=1.00 F1=1.00
Total support: 10

## LLM Metadata

Providers: openai (10)
Models: gpt-4o-mini-2024-07-18 (10)
LLM calls: 10
Retries: 0
Total input tokens: 2335
Total output tokens: 855
Total tokens: 3190
Total cost (USD): 0.000863
Total latency (ms): 21222.0
Avg latency (ms): 2122.2

## Confusion Matrix

| Actual \ Predicted | benign | phishing | impersonation |
|---|---|---|---|
| benign | 4 | 0 | 0 |
| phishing | 0 | 4 | 0 |
| impersonation | 0 | 0 | 2 |

## Explanation Support

Supported: 9
Weak: 0
Unsupported: 1
Unavailable: 0

| Sample | Actual | Predicted | Status | Notes |
|--------|--------|-----------|--------|-------|
| imp_001 | impersonation | impersonation | unsupported | high-risk label with no supporting signals |

## Results

| Sample | Actual | Predicted | Match | Risk | Confidence | Support |
|--------|--------|-----------|-------|------|------------|---------|
| benign_001 | benign | benign | + | 0.10 | 0.90 | supported |
| benign_002 | benign | benign | + | 0.10 | 0.90 | supported |
| benign_003 | benign | benign | + | 0.10 | 0.90 | supported |
| benign_004 | benign | benign | + | 0.10 | 0.85 | supported |
| imp_001 | impersonation | impersonation | + | 0.85 | 0.90 | unsupported |
| imp_002 | impersonation | impersonation | + | 0.85 | 0.90 | supported |
| phish_001 | phishing | phishing | + | 0.95 | 0.90 | supported |
| phish_002 | phishing | phishing | + | 0.85 | 0.90 | supported |
| phish_003 | phishing | phishing | + | 0.90 | 0.95 | supported |
| phish_004 | phishing | phishing | + | 0.90 | 0.95 | supported |

## Per-Sample Execution Details

### benign_001
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2403
- Input tokens: 223
- Output tokens: 79
- Token cost (USD): 8.085e-05
- Explanation support: supported
- Reliability run id: b15832ef-4f5b-4850-9db1-d1bfae9fb87a
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 4d695639-e126-56d1-b80a-e11605878dec

### benign_002
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2132
- Input tokens: 217
- Output tokens: 75
- Token cost (USD): 7.755e-05
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: 68bdb12e-f4d0-4118-aac7-fc7baad99d85
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 792907ed-6315-5f12-ac01-2576e20a233c

### benign_003
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2017
- Input tokens: 218
- Output tokens: 79
- Token cost (USD): 8.01e-05
- Explanation support: supported
- Explanation support notes:
  - explanation references links but no urls were extracted
- Reliability run id: 22771b0a-88bc-4e91-ba8e-d4e9cc072a0a
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: b4f4ca52-236a-5cf5-ae48-d802d07e4d16

### benign_004
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2000
- Input tokens: 227
- Output tokens: 97
- Token cost (USD): 9.225e-05
- Explanation support: supported
- Reliability run id: cf55bff4-1c05-42fc-9c6c-26f22f5e77a6
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 4865a826-3722-52e0-a233-c952757f448e

### imp_001
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2280
- Input tokens: 225
- Output tokens: 80
- Token cost (USD): 8.175e-05
- Explanation support: unsupported
- Explanation support notes:
  - high-risk label with no supporting signals
- Reliability run id: 9d4dd443-2a64-4b29-974d-7c0a5fdf6c34
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: ccc30041-eff4-5ef7-b33e-f4a3bd2108a8

### imp_002
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 1868
- Input tokens: 226
- Output tokens: 92
- Token cost (USD): 8.91e-05
- Explanation support: supported
- Reliability run id: 9a27af5a-9e98-4679-a170-fb3c9c04ee08
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: b655cdee-179f-534c-a162-b854de02ebad

### phish_001
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2451
- Input tokens: 268
- Output tokens: 77
- Token cost (USD): 8.64e-05
- Explanation support: supported
- Reliability run id: 6c064d41-b98b-47d9-a7d7-8ed5aadaaeac
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 4518abc0-a53c-5374-b118-c2956375855d

### phish_002
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2161
- Input tokens: 242
- Output tokens: 88
- Token cost (USD): 8.91e-05
- Explanation support: supported
- Reliability run id: 67502a52-10c4-4181-ae59-8f1c8bdc6e65
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: 557ed160-4b45-5fef-88b8-01bd6895a449

### phish_003
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 2051
- Input tokens: 247
- Output tokens: 103
- Token cost (USD): 9.885e-05
- Explanation support: supported
- Reliability run id: d42bd7b3-0dc5-436c-b7c8-29c8bffd0e60
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: b5a943ee-0d6d-5ef0-b3c2-30710a78ebdf

### phish_004
- Provider: openai
- Model: gpt-4o-mini-2024-07-18
- Latency (ms): 1859
- Input tokens: 242
- Output tokens: 85
- Token cost (USD): 8.73e-05
- Explanation support: supported
- Reliability run id: 468a8aee-e699-4b35-b6ef-78d0ecc6b3d1
- Reliability phase id: b2c3d4e5-f6a7-8901-bcde-f12345678901
- Reliability prompt id: 9c3137f5-14c9-5180-8265-c90b19cd5062
- Reliability call id: f03da650-b25d-54b4-a09d-c2e845622949
