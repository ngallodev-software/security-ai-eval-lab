"""
Anthropic LLM client for security-ai-eval-lab.

Implements the BaseLLMClient interface from ai-reliability-fw
so PhaseExecutor can use it without modification.
"""
from __future__ import annotations

import time

import anthropic

from src.llm.client import BaseLLMClient

SYSTEM_PROMPT = """\
You are a security investigation assistant. You will be given a structured
evidence bundle extracted from an email. Your job is to classify the email
and explain your reasoning.

Return ONLY a valid JSON object with exactly these fields:
{
  "predicted_label": "<phishing | impersonation | benign>",
  "risk_score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "explanation": "<1-3 sentence summary>"
}

Do not include any text outside the JSON object.
"""


class AnthropicClient(BaseLLMClient):
    """
    Async LLM client backed by the Anthropic Messages API.

    Parameters
    ----------
    model:
        Anthropic model ID, e.g. "claude-haiku-4-5-20251001".
        Defaults to claude-haiku-4-5-20251001 for cost-effective classification.
    api_key:
        Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
    """

    def __init__(self, model: str = "claude-haiku-4-5-20251001", api_key: str | None = None) -> None:
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def call(self, prompt: str, model: str | None = None) -> dict:
        effective_model = model or self._model

        t0 = time.perf_counter()
        response = await self._client.messages.create(
            model=effective_model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text_block = next(b for b in response.content if b.type == "text")
        response_raw = text_block.text

        usage = response.usage
        input_tokens = usage.input_tokens if usage else None
        output_tokens = usage.output_tokens if usage else None
        # claude-haiku-4-5 pricing: $0.80/M input, $4.00/M output (as of 2025).
        token_cost_usd = (
            round(input_tokens * 0.0000008 + output_tokens * 0.000004, 8)
            if input_tokens is not None and output_tokens is not None
            else None
        )

        return {
            "response_raw": response_raw,
            "latency_ms": latency_ms,
            "provider": "anthropic",
            "model": response.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "token_cost_usd": token_cost_usd,
        }
