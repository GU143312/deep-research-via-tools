from email.message import EmailMessage

from deep_research.clients import NeteaseSmtpClient, TavilySearchClient


def test_tavily_normalization_discards_invalid_urls() -> None:
    finding = TavilySearchClient.normalize(
        {
            "answer": "A short answer",
            "results": [
                {
                    "title": "Official source",
                    "url": "https://example.com/report",
                    "content": "Evidence",
                    "score": 0.98,
                },
                {"title": "Bad", "url": "javascript:alert(1)", "content": "Ignore"},
            ],
        },
        query="example query",
        reason="test",
    )

    assert finding.answer == "A short answer"
    assert len(finding.sources) == 1
    assert str(finding.sources[0].url) == "https://example.com/report"


def test_netease_smtp_uses_authorization_code_and_fixed_recipient(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class FakeSmtp:
        def __init__(self, host, port, **kwargs) -> None:
            calls["connection"] = (host, port, kwargs["timeout"])

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def login(self, username, password) -> None:
            calls["login"] = (username, password)

        def send_message(self, message: EmailMessage) -> None:
            calls["message"] = message

    monkeypatch.setattr("deep_research.clients.smtplib.SMTP_SSL", FakeSmtp)
    client = NeteaseSmtpClient(
        username="sender@163.com",
        authorization_code="client-auth-code",
        recipient="fixed@example.com",
    )

    client.send(
        subject="Research\nReport",
        text_body="# Report",
        html_body="<h1>Report</h1>",
    )

    message = calls["message"]
    assert calls["connection"] == ("smtp.163.com", 465, 30)
    assert calls["login"] == ("sender@163.com", "client-auth-code")
    assert message["From"] == "sender@163.com"
    assert message["To"] == "fixed@example.com"
    assert message["Subject"] == "Research Report"

