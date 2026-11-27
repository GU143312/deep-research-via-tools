from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from deep_research.config import Settings
from deep_research.schemas import (
    ReportData,
    SearchFinding,
    Source,
    WebSearchItem,
    WebSearchPlan,
)
from deep_research.service import ResearchService
from deep_research.toolkit import ResearchToolkit


class StructuredStub:
    def __init__(self, schema: type[Any]) -> None:
        self.schema = schema

    async def ainvoke(self, _prompt: str) -> Any:
        if self.schema is WebSearchPlan:
            return WebSearchPlan(
                searches=[
                    WebSearchItem(query="first query", reason="first reason"),
                    WebSearchItem(query="second query", reason="second reason"),
                ]
            )
        if self.schema is ReportData:
            return ReportData(
                title="Test report",
                short_summary="Summary",
                markdown_report="# Test report\n\nEvidence with [a source](https://example.com).",
                follow_up_questions=["What next?"],
            )
        raise AssertionError(f"Unexpected schema: {self.schema}")


class ScriptedManagerModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "scripted-manager"

    def bind_tools(self, _tools: Any, **_kwargs: Any) -> "ScriptedManagerModel":
        return self

    def with_structured_output(self, schema: type[Any], **_kwargs: Any) -> StructuredStub:
        return StructuredStub(schema)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        del stop, run_manager, kwargs
        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        last_tool = tool_messages[-1].name if tool_messages else None

        if last_tool is None:
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "plan_research",
                        "args": {"question": "test question"},
                        "id": "plan-1",
                        "type": "tool_call",
                    }
                ],
            )
        elif last_tool == "plan_research":
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_web",
                        "args": {"query": "first query", "reason": "first reason"},
                        "id": "search-1",
                        "type": "tool_call",
                    },
                    {
                        "name": "search_web",
                        "args": {"query": "second query", "reason": "second reason"},
                        "id": "search-2",
                        "type": "tool_call",
                    },
                ],
            )
        elif last_tool == "search_web":
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_report",
                        "args": {"question": "test question"},
                        "id": "write-1",
                        "type": "tool_call",
                    }
                ],
            )
        else:
            message = AIMessage(content="Research complete.")

        return ChatResult(generations=[ChatGeneration(message=message)])


class SearchStub:
    def search(self, query: str, reason: str) -> SearchFinding:
        return SearchFinding(
            query=query,
            reason=reason,
            answer="Answer",
            sources=[
                Source(
                    title="Source",
                    url="https://example.com",
                    content="Evidence",
                    score=1.0,
                )
            ],
        )


@pytest.mark.asyncio
async def test_complete_tool_orchestrated_workflow() -> None:
    model = ScriptedManagerModel()
    toolkit = ResearchToolkit(
        model=model,
        search_client=SearchStub(),
        search_count=2,
    )
    service = ResearchService(
        Settings(
            deepseek_api_key="test",
            tavily_api_key="test",
            model="test",
            deepseek_base_url="https://api.deepseek.com",
            search_count=2,
            max_results=2,
            netease_email=None,
            netease_auth_code=None,
            email_to=None,
            smtp_host="smtp.163.com",
            smtp_port=465,
        )
    )

    updates = [
        update
        async for update in service.run_with(
            "test question",
            toolkit=toolkit,
            send_email=False,
        )
    ]

    assert len(toolkit.findings) == 2
    assert toolkit.report is not None
    assert updates[-1].startswith("# Test report")

