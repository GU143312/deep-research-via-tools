from email import policy
from email.parser import BytesParser

import pytest

from deep_research.config import Settings
from deep_research.recipients import RecipientError, validate_recipient
from deep_research.research_manager import ResearchManager
from deep_research.state import ResearchState

from .test_workflow import REPORT, invoke_email, script, use_model


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-an-email",
        "@example.com",
        "person@",
        "one@example.com,two@example.com",
        "person@example.com\r\nBcc: other@example.com",
    ],
)
async def test_invalid_send_recipient_fails_before_api_or_smtp(tmp_path, value):
    with pytest.raises(RecipientError):
        async for _ in ResearchManager(Settings(output_root=tmp_path)).run(
            "Research question", send_email=True, recipient=value
        ):
            pass
    assert not list(tmp_path.iterdir())


def test_preview_can_have_no_recipient_and_addresses_are_trimmed():
    assert validate_recipient("") == ""
    assert validate_recipient(" person@example.com ", required=True) == "person@example.com"


async def test_each_run_uses_its_ui_recipient_not_environment(tmp_path, monkeypatch):
    for key in ("EMAIL_SMTP_SERVER", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD"):
        monkeypatch.setenv(key, "offline-test-value")
    monkeypatch.setenv("EMAIL_TO", "old-environment@example.com")
    received = []
    monkeypatch.setattr(
        "deep_research.email_agent.deliver_smtp", lambda message: received.append(message["To"])
    )
    model = use_model(monkeypatch, script() + script())
    for recipient in ("first@example.com", "second@example.com"):
        async for _ in ResearchManager(Settings(search_count=1, output_root=tmp_path)).run(
            "Research question", send_email=True, recipient=recipient
        ):
            pass
    assert not model.steps
    assert received == ["first@example.com", "second@example.com"]


async def test_preview_never_sends_even_with_recipient(tmp_path, monkeypatch):
    def send(message):
        pytest.fail("Preview must not send email")

    monkeypatch.setattr("deep_research.email_agent.deliver_smtp", send)
    monkeypatch.setenv("EMAIL_TO", "old-environment@example.com")
    state = ResearchState(tmp_path, recipient="ui@example.com", report=REPORT)
    await invoke_email(state)
    message = BytesParser(policy=policy.default).parsebytes((tmp_path / "email.eml").read_bytes())
    assert message["To"] == "ui@example.com"
    assert state.email_receipt["status"] == "preview_only_not_sent"
