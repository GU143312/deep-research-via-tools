import socket

import httpx
import pytest


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch):
    """These tests must never use paid APIs, real email or real credentials."""
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-placeholder")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "offline-deepseek-placeholder")
    for name in ("EMAIL_ADDRESS", "EMAIL_TO", "EMAIL_SMTP_SERVER", "EMAIL_APP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    original_connect = socket.socket.connect

    def no_network(sock, address):
        # Windows asyncio implements its internal wakeup pipe with localhost sockets.
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect(sock, address)
        raise AssertionError("Network calls are forbidden in offline tests.")

    monkeypatch.setattr(socket.socket, "connect", no_network)

    def reject_request(request):
        raise AssertionError("Model HTTP requests must be mocked in offline tests.")

    # The installed SDK may use a native shared HTTP transport, which bypasses
    # Python socket.connect. Replace it explicitly as well.
    monkeypatch.setattr(
        "agents.models.openai_provider.shared_http_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(reject_request)),
    )
