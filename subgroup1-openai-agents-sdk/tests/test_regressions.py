import json
from email.message import EmailMessage

import httpx
import pytest
from agents import RunConfig, Runner, UserError

from deep_research.config import Settings
from deep_research.email_agent import build_email_agent, deliver_smtp
from deep_research.errors import explain_error
from deep_research.providers import build_provider
from deep_research.search_agent import build_searcher
from deep_research.state import ResearchState, ResearchUpdate

from .fake_model import message, tool_call
from .test_workflow import REPORT


@pytest.mark.parametrize("specialist", ["search", "email"])
async def test_forced_tools_send_nonthinking_to_actual_sdk(monkeypatch, tmp_path, specialist):
    settings = Settings()
    requests = []
    state = ResearchState(tmp_path)
    agent = (
        build_searcher(settings) if specialist == "search" else build_email_agent(settings, state)
    )
    # The Manager constructs specialists before the Writer produces the report.
    state.report = REPORT

    async def invoke(ctx, args):
        return "Retrieved evidence from https://example.com/source"

    if specialist == "search":
        monkeypatch.setattr(agent.tools[0], "on_invoke_tool", invoke)

    async def send(client, request, **kwargs):
        body = json.loads(request.content)
        requests.append(body)
        assert body["reasoning"]["effort"] == "none"
        if specialist == "email":
            assert REPORT.markdown_report in body["instructions"]
        if len(requests) == 1:
            assert body["tool_choice"] == "required"
            output = (
                tool_call("deepseek_web_search", query="evidence")
                if specialist == "search"
                else tool_call("send_email_tool", subject="Test", html_body="<p>Test</p>")
            )
        else:
            assert body.get("tool_choice", "auto") == "auto"
            output = message("Summary with https://example.com/source")
        return httpx.Response(
            200,
            request=request,
            json={
                "id": f"offline_{len(requests)}",
                "object": "response",
                "created_at": 0,
                "model": settings.model,
                "status": "completed",
                "tools": [],
                "tool_choice": "auto",
                "parallel_tool_calls": False,
                "output": [output.model_dump()],
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    result = await Runner.run(
        agent,
        "Test",
        run_config=RunConfig(
            model_provider=build_provider(settings),
            tracing_disabled=True,
        ),
    )
    assert result.final_output
    assert len(requests) == (2 if specialist == "search" else 1)


@pytest.mark.parametrize(
    "host, expected",
    [
        ("smtp.gmail.com", "abcdefghijklmnop"),
        ("smtp.office365.com", "abcd efgh ijkl mnop"),
    ],
)
def test_smtp_login_normalizes_only_gmail_group_spaces(monkeypatch, host, expected):
    events = []
    monkeypatch.setenv("EMAIL_SMTP_SERVER", host)
    monkeypatch.setenv("EMAIL_SMTP_PORT", "587")
    monkeypatch.setenv("EMAIL_ADDRESS", "sender@example.invalid")
    monkeypatch.setenv("EMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")

    class SMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self, **kwargs):
            events.append("TLS")

        def login(self, address, password):
            assert password == expected
            events.append("login")

        def send_message(self, message):
            events.append("send")
            return {}

    monkeypatch.setattr("deep_research.email_agent.smtplib.SMTP", SMTP)
    deliver_smtp(EmailMessage())
    assert events == ["TLS", "login", "send"]


async def test_ui_keeps_partial_outputs_on_nested_failure(monkeypatch):
    from deep_research import app

    class Manager:
        async def run(self, *args, **kwargs):
            yield ResearchUpdate("Manager called: email_report", "# Saved report", ["report.md"])
            try:
                raise TimeoutError("secret must not appear")
            except TimeoutError as exc:
                raise UserError("wrapped secret") from exc

    monkeypatch.setattr(app, "ResearchManager", Manager)
    updates = [item async for item in app.run("question", False)]
    status, report, files = updates[-1]
    assert "timed out" in status
    assert "secret" not in status
    assert report == "# Saved report"
    assert files == ["report.md"]


def test_unknown_error_does_not_disclose_contents():
    assert "secret" not in explain_error(ValueError("secret"))
