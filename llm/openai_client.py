"""
OpenAI LLM client for security-ai-eval-lab.

Implements the BaseLLMClient interface from ai-reliability-fw
so PhaseExecutor can use it without modification.

The client sends the evidence bundle as a user message and
instructs the model to return a JSON object matching the
investigation result schema.
"""
from __future__ import annotations

import time

from openai import AsyncOpenAI

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


class OpenAIClient(BaseLLMClient):
    """
    Async LLM client backed by the OpenAI Chat Completions API.

    Parameters
    ----------
    model:
        OpenAI model ID, e.g. "gpt-4o-mini".
        Defaults to gpt-4o-mini for cost-effective classification.
    api_key:
        OpenAI API key. If None, reads from OPENAI_API_KEY env var.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def call(self, prompt: str, model: str | None = None) -> dict:
        effective_model = model or self._model

        t0 = time.perf_counter()
        response = await self._client.chat.completions.create(
            model=effective_model,
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        choice = response.choices[0]
        response_raw = choice.message.content

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        # gpt-4o-mini pricing: $0.15/M input, $0.60/M output (as of 2024).
        token_cost_usd = (
            round(input_tokens * 0.00000015 + output_tokens * 0.0000006, 8)
            if input_tokens is not None and output_tokens is not None
            else None
        )

        return {
            "response_raw": response_raw,
            "latency_ms": latency_ms,
            "provider": "openai",
            "model": response.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "token_cost_usd": token_cost_usd,
        }
