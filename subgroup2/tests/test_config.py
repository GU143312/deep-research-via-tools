import pytest

from deep_research.config import Settings


def test_settings_reports_missing_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    settings = Settings.from_env()

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY, TAVILY_API_KEY"):
        settings.validate()


def test_email_settings_are_only_required_when_requested() -> None:
    settings = Settings(
        deepseek_api_key="test",
        tavily_api_key="test",
        model="test-model",
        deepseek_base_url="https://api.deepseek.com",
        search_count=3,
        max_results=3,
        netease_email=None,
        netease_auth_code=None,
        email_to=None,
        smtp_host="smtp.163.com",
        smtp_port=465,
    )

    settings.validate(send_email=False)
    with pytest.raises(ValueError, match="NETEASE_EMAIL"):
        settings.validate(send_email=True)


def test_netease_host_and_recipient_default_to_mailbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETEASE_EMAIL", "researcher@126.com")
    monkeypatch.delenv("EMAIL_TO", raising=False)
    monkeypatch.delenv("NETEASE_SMTP_HOST", raising=False)

    settings = Settings.from_env()

    assert settings.email_to == "researcher@126.com"
    assert settings.smtp_host == "smtp.126.com"

