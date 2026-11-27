import ssl
from contextlib import contextmanager
from email.message import EmailMessage

import pytest

from deep_research import check_email, email_agent


@pytest.mark.parametrize("port", [465, 587])
def test_tls_mode_and_certificate_validation(monkeypatch, port):
    events = []
    monkeypatch.setenv("EMAIL_SMTP_SERVER", "smtp.qq.com")
    monkeypatch.setenv("EMAIL_SMTP_PORT", str(port))
    monkeypatch.setenv("EMAIL_ADDRESS", "sender@example.invalid")
    monkeypatch.setenv("EMAIL_APP_PASSWORD", "test-authorization-code")

    def verify(context):
        assert context.check_hostname
        assert context.verify_mode == ssl.CERT_REQUIRED

    class SMTP:
        def __init__(self, host, selected_port, *, timeout, context=None):
            assert host == "smtp.qq.com"
            assert selected_port == port
            if port == 465:
                verify(context)
                events.append("implicit_tls")
            else:
                assert context is None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self, *, context):
            assert port == 587
            verify(context)
            events.append("starttls")

        def login(self, address, password):
            assert events
            events.append("login")

        def send_message(self, message):
            events.append("send")
            return {}

    selected = "SMTP_SSL" if port == 465 else "SMTP"
    monkeypatch.setattr(email_agent.smtplib, selected, SMTP)
    email_agent.deliver_smtp(EmailMessage())
    assert events == ["implicit_tls" if port == 465 else "starttls", "login", "send"]


def test_tls_failure_never_authenticates_or_sends(monkeypatch):
    monkeypatch.setenv("EMAIL_SMTP_SERVER", "smtp.qq.com")
    monkeypatch.setenv("EMAIL_SMTP_PORT", "465")

    def fail(*args, **kwargs):
        raise ssl.SSLCertVerificationError("untrusted certificate")

    monkeypatch.setattr(email_agent.smtplib, "SMTP_SSL", fail)
    with pytest.raises(ssl.SSLCertVerificationError):
        email_agent.deliver_smtp(EmailMessage())


def test_diagnostic_authenticates_without_sending(monkeypatch, capsys):
    monkeypatch.setattr(check_email, "load_dotenv", lambda *args, **kwargs: None)
    for key in ("EMAIL_SMTP_SERVER", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD"):
        monkeypatch.setenv(key, "offline-private-value")
    events = []

    class SMTP:
        def login(self, address, password):
            events.append("login")

        def send_message(self, *args, **kwargs):
            pytest.fail("Diagnostic must never send email")

    @contextmanager
    def connect():
        yield SMTP()

    monkeypatch.setattr(check_email, "connect_smtp", connect)
    assert check_email.main() == 0
    assert events == ["login"]
    output = capsys.readouterr().out
    assert "No email was sent" in output
    assert "offline-private-value" not in output
