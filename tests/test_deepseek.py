import json

import httpx
import pytest
from agents import RunConfig, Runner

from deep_research.config import Settings, validate_credentials
from deep_research.deepseek_search import SEARCH_URL, search_deepseek
from deep_research.planner_agent import WebSearchPlan, build_planner
from deep_research.providers import build_provider
from deep_research.search_agent import build_searcher

from .fake_model import ScriptedModel, message, tool_call


def mock_search(monkeypatch, payload, status=200):
    calls = []
    original_client = httpx.AsyncClient

    def handler(request):
        calls.append(request)
        assert str(request.url) == SEARCH_URL
        assert request.headers["Authorization"] == "Bearer offline-deepseek-placeholder"
        return httpx.Response(status, json=payload)

    monkeypatch.setattr(
        "deep_research.deepseek_search.httpx.AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    return calls


async def test_search_agent_calls_real_function_tool(monkeypatch):
    calls = mock_search(
        monkeypatch,
        {
            "results": [
                {
                    "title": "Source",
                    "url": "https://example.com/evidence",
                    "summary": "Evidence from search",
                    "content": "content",
                    "date": None,
                }
            ]
        },
    )
    model = ScriptedModel(
        [
            ("research assistant", [tool_call("deepseek_web_search", query="research evidence")]),
            ("research assistant", [message("Summary: https://example.com/evidence")]),
        ]
    )
    result = await Runner.run(
        build_searcher(Settings()),
        "Research this topic",
        run_config=RunConfig(model=model, tracing_disabled=True),
    )
    assert result.final_output == "Summary: https://example.com/evidence"
    assert len(calls) == 1
    assert json.loads(calls[0].content) == {
        "query": "research evidence",
        "count": 5,
        "need_content": True,
    }
    assert "Evidence from search" in json.dumps(model.calls[-1][1])


@pytest.mark.parametrize("status", [401, 402, 429, 500])
async def test_search_errors_are_not_fabricated_as_evidence(monkeypatch, status):
    mock_search(monkeypatch, {"error": {"message": "Test failure"}}, status)
    with pytest.raises(httpx.HTTPStatusError):
        await search_deepseek("research")


async def test_empty_search_is_returned_honestly(monkeypatch):
    mock_search(monkeypatch, {"results": []})
    assert json.loads(await search_deepseek("research"))["results"] == []


@pytest.mark.parametrize("query", ["   ", "x" * 129])
async def test_invalid_search_term_never_makes_request(query):
    with pytest.raises(ValueError, match="1-128"):
        await search_deepseek(query)


async def test_invalid_search_response(monkeypatch):
    mock_search(monkeypatch, {"unexpected": []})
    with pytest.raises(ValueError, match="invalid response"):
        await search_deepseek("research")


async def test_real_sdk_responses_serialization_routes_to_deepseek(monkeypatch):
    requests = []

    async def send(client, request, **kwargs):
        requests.append(request)
        assert str(request.url) == "https://api.deepseek.com/responses"
        assert request.headers["Authorization"] == "Bearer offline-deepseek-placeholder"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-flash"
        assert body["text"]["format"]["type"] == "json_schema"
        assert "previous_response_id" not in body
        assert "conversation" not in body
        return httpx.Response(
            200,
            request=request,
            json={
                "id": "offline_response",
                "object": "response",
                "created_at": 0,
                "model": "deepseek-flash",
                "status": "completed",
                "tools": [],
                "tool_choice": "auto",
                "parallel_tool_calls": True,
                "output": [
                    message(
                        json.dumps({"searches": [{"query": "test", "reason": "test evidence"}]})
                    ).model_dump()
                ],
            },
        )

    # Intercept at HTTP boundary: exercise the actual SDK provider, serialization
    # and structured response parsing without transmitting a key or paying for API.
    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://wrong-provider.invalid")
    settings = Settings()
    result = await Runner.run(
        build_planner(settings),
        "Question",
        run_config=RunConfig(model_provider=build_provider(settings), tracing_disabled=True),
    )
    assert len(requests) == 1
    assert isinstance(result.final_output, WebSearchPlan)
    assert result.final_output.searches[0].query == "test"


def test_openai_fallback_uses_its_own_credentials(monkeypatch):
    settings = Settings(provider="openai", model="gpt-5.4-mini")
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        validate_credentials(settings=settings)
    assert settings.base_url == "https://api.openai.com/v1"
    assert build_searcher(settings).tools[0].__class__.__name__ == "WebSearchTool"


def test_deepseek_does_not_enable_openai_cloud_tracing():
    with pytest.raises(ValueError, match="ENABLE_TRACING=false"):
        validate_credentials(settings=Settings(tracing=True))
