from __future__ import annotations

import asyncio
from types import SimpleNamespace
import unittest

from llm.anthropic_client import AnthropicClient
from llm.openai_client import OpenAIClient


async def _never_finishing_call(*args, **kwargs):
    await asyncio.Event().wait()


class LLMClientTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_client_times_out(self):
        client = OpenAIClient.__new__(OpenAIClient)
        client._model = "gpt-test"
        client._timeout_seconds = 0.01
        client._client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=_never_finishing_call)
            )
        )

        with self.assertRaises(TimeoutError) as ctx:
            await client.call("prompt")

        self.assertIn("OpenAI", str(ctx.exception))

    async def test_anthropic_client_times_out(self):
        client = AnthropicClient.__new__(AnthropicClient)
        client._model = "claude-test"
        client._timeout_seconds = 0.01
        client._client = SimpleNamespace(
            messages=SimpleNamespace(create=_never_finishing_call)
        )

        with self.assertRaises(TimeoutError) as ctx:
            await client.call("prompt")

        self.assertIn("Anthropic", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
