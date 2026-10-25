import json
from email import policy
from email.parser import BytesParser

import pytest
from agents import RunConfig
from agents.run_config import ToolExecutionConfig
from agents.tool_context import ToolContext

from deep_research.config import Settings, validate_credentials
from deep_research.email_agent import build_email_agent
from deep_research.manager_agent import build_manager
from deep_research.research_manager import ResearchManager
from deep_research.state import ResearchState
from deep_research.writer_agent import ReportData

from .fake_model import ScriptedModel, message, tool_call

REPORT = ReportData(
    short_summary="Offline fixture, not real research.",
    markdown_report="# Research fixture\n\nEvidence [source](https://example.com/source).",
    follow_up_questions=["What further evidence is needed?"],
)


def script(extra_search=False, finish_email=True):
    steps = [
        ("Research Manager", [tool_call("plan_research", input="Original research question")]),
        (
            "research planner",
            [message(json.dumps({"searches": [{"query": "query A", "reason": "context"}]}))],
        ),
        ("Research Manager", [tool_call("search_web", input="query A; reason: context")]),
        ("research assistant", [message("Evidence A: https://example.com/source")]),
    ]
    if extra_search:
        steps += [
            (
                "Research Manager",
                [tool_call("search_web", input="Extra query: conflicting evidence")],
            ),
            ("research assistant", [message("Additional evidence: https://example.com/extra")]),
        ]
    steps += [
        (
            "Research Manager",
            [
                tool_call(
                    "write_report", input="Original question and all evidence with source URLs"
                )
            ],
        ),
        ("senior researcher", [message(REPORT.model_dump_json())]),
    ]
    if finish_email:
        steps += [
            ("Research Manager", [tool_call("email_report", input="Prepare the saved report.")]),
            (
                "You receive a finished research report",
                [
                    tool_call(
                        "send_email_tool", subject="Research fixture", html_body="<p>Fixture</p>"
                    )
                ],
            ),
        ]
    steps += [("Research Manager", [message("Finished; email preview only.")])]
    return steps


def use_model(monkeypatch, steps):
    model = ScriptedModel(steps)
    config = RunConfig(
        model=model,
        tracing_disabled=True,
        tool_execution=ToolExecutionConfig(max_function_tool_concurrency=1),
    )
    monkeypatch.setattr("deep_research.research_manager.RunConfig", lambda **kwargs: config)
    return model


@pytest.mark.parametrize("extra_search", [False, True])
async def test_real_sdk_nested_tools_and_streaming(tmp_path, monkeypatch, extra_search):
    model = use_model(monkeypatch, script(extra_search))
    updates = [
        update
        async for update in ResearchManager(Settings(search_count=1, output_root=tmp_path)).run(
            "Original research question"
        )
    ]
    assert not model.steps
    final = updates[-1]
    assert (
        final.report == REPORT.markdown_report
    )  # Manager's short reply cannot replace the report.
    assert "preview_only_not_sent" in final.status
    assert final.status.count("Manager called: search_web") == 1 + extra_search
    for tool in ("plan_research", "write_report", "email_report"):
        assert f"Manager called: {tool}" in final.status
    directory = next(tmp_path.iterdir())
    assert (directory / "report.md").read_text(encoding="utf-8") == REPORT.markdown_report
    assert json.loads((directory / "email_status.json").read_text())["status"] == (
        "preview_only_not_sent"
    )
    saved_email = BytesParser(policy=policy.default).parsebytes(
        (directory / "email.eml").read_bytes()
    )
    assert saved_email.get_body(preferencelist=("plain",)).get_content().strip() == (
        REPORT.markdown_report
    )
    assert "workflow.json" in " ".join(final.files)
    # Check actual tool results reached the manager's later model input.
    final_manager_input = json.dumps(model.calls[-1][1], default=str)
    assert "Evidence A" in final_manager_input
    assert "markdown_report" in final_manager_input
    assert "preview_only_not_sent" in final_manager_input
    search_call = next(call for call in model.calls if call[0] == "research assistant")
    assert search_call[2]["tools"][0].name == "deepseek_web_search"


async def test_incomplete_manager_is_not_reported_as_success(tmp_path, monkeypatch):
    use_model(monkeypatch, [("Research Manager", [message("I am done without using tools.")])])
    updates = []
    with pytest.raises(RuntimeError, match="planned searches"):
        async for update in ResearchManager(Settings(output_root=tmp_path)).run("Question"):
            updates.append(update)
    assert "Research failed" in updates[-1].status
    assert "Complete." not in updates[-1].status


async def test_missing_email_keeps_report_but_fails_completion(tmp_path, monkeypatch):
    use_model(monkeypatch, script(finish_email=False))
    with pytest.raises(RuntimeError, match="email receipt"):
        async for _ in ResearchManager(Settings(search_count=1, output_root=tmp_path)).run("Q"):
            pass
    assert next(tmp_path.glob("*/report.md")).read_text(encoding="utf-8") == REPORT.markdown_report


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        validate_credentials()


def test_preview_needs_no_mail_credentials():
    validate_credentials(send_email=False)
    with pytest.raises(ValueError, match="EMAIL_SMTP_SERVER"):
        validate_credentials(send_email=True)


async def test_blank_query_fails_before_model_call(tmp_path):
    with pytest.raises(ValueError, match="research question"):
        async for _ in ResearchManager(Settings(output_root=tmp_path)).run("   "):
            pass
    assert not list(tmp_path.iterdir())


def test_four_tools_and_no_handoffs(tmp_path):
    manager = build_manager(Settings(), ResearchState(tmp_path), RunConfig(tracing_disabled=True))
    assert {tool.name for tool in manager.tools} == {
        "plan_research",
        "search_web",
        "write_report",
        "email_report",
    }
    assert manager.handoffs == []


async def invoke_email(state):
    agent = build_email_agent(Settings(), state)
    arguments = json.dumps({"subject": "Test", "html_body": "<p>Test</p>"})
    return await agent.tools[0].on_invoke_tool(
        ToolContext(
            context=None,
            tool_name="send_email_tool",
            tool_call_id="test-call",
            tool_arguments=arguments,
            run_config=RunConfig(tracing_disabled=True),
        ),
        arguments,
    )


async def test_email_before_report_is_rejected(tmp_path):
    state = ResearchState(tmp_path)
    with pytest.raises(ValueError, match="No report exists"):
        await invoke_email(state)
    assert state.email_receipt is None
    assert not list(tmp_path.iterdir())


async def test_repeated_email_call_does_not_send_twice(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("deep_research.email_agent.deliver_smtp", lambda msg: calls.append(msg))
    state = ResearchState(
        tmp_path, send_email=True, recipient="recipient@example.com", report=REPORT
    )
    first = await invoke_email(state)
    second = await invoke_email(state)
    assert first == second
    assert len(calls) == 1
    assert state.email_receipt["status"] == "accepted_by_smtp"


async def test_smtp_failure_is_not_success_or_retried(tmp_path, monkeypatch):
    calls = []

    def fail(message):
        calls.append(message)
        raise TimeoutError("Fake SMTP timeout")

    monkeypatch.setattr("deep_research.email_agent.deliver_smtp", fail)
    state = ResearchState(
        tmp_path, send_email=True, recipient="recipient@example.com", report=REPORT
    )
    with pytest.raises(TimeoutError):
        await invoke_email(state)
    with pytest.raises(RuntimeError, match="already attempted"):
        await invoke_email(state)
    assert len(calls) == 1
    assert state.email_receipt is None
    assert (tmp_path / "email.eml").exists()


@pytest.mark.parametrize("count", [0, 11])
def test_invalid_search_budget(count):
    with pytest.raises(ValueError, match="between 1 and 10"):
        Settings(search_count=count)
