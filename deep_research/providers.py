"""Explicit provider routing: a DeepSeek key is never sent to OpenAI."""

import os

from agents.models.openai_provider import OpenAIProvider

from .config import Settings


def build_provider(settings: Settings) -> OpenAIProvider:
    # Both selected providers expose Responses. Use explicit credentials and URL,
    # independent of ambient OPENAI_BASE_URL or global SDK provider settings.
    return OpenAIProvider(
        api_key=os.environ[settings.api_key_name],
        base_url=settings.base_url,
        use_responses=True,
        use_responses_websocket=False,
    )
