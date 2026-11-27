from __future__ import annotations

import json
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .schemas import SearchFinding, Source


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Remote API returned HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach remote API: {exc.reason}") from exc


class TavilySearchClient:
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str, max_results: int = 5) -> None:
        self.api_key = api_key
        self.max_results = max_results

    def search(self, query: str, reason: str) -> SearchFinding:
        raw = _post_json(
            self.endpoint,
            {
                "api_key": self.api_key,
                "query": query,
                "topic": "general",
                "search_depth": "advanced",
                "max_results": self.max_results,
                "include_answer": True,
                "include_raw_content": False,
            },
            {},
        )
        return self.normalize(raw, query=query, reason=reason)

    @staticmethod
    def normalize(raw: dict[str, Any], *, query: str, reason: str) -> SearchFinding:
        sources: list[Source] = []
        for item in raw.get("results", []):
            url = str(item.get("url", "")).strip()
            if not url.startswith(("https://", "http://")):
                continue
            sources.append(
                Source(
                    title=str(item.get("title") or url),
                    url=url,
                    content=str(item.get("content") or "")[:6000],
                    score=item.get("score"),
                )
            )
        return SearchFinding(
            query=query,
            reason=reason,
            answer=raw.get("answer"),
            sources=sources,
        )


class NeteaseSmtpClient:
    """Send mail through a NetEase mailbox without exposing credentials to the LLM."""

    def __init__(
        self,
        *,
        username: str,
        authorization_code: str,
        recipient: str,
        host: str = "smtp.163.com",
        port: int = 465,
    ) -> None:
        self.username = username
        self.authorization_code = authorization_code
        self.recipient = recipient
        self.host = host
        self.port = port

    def send(self, *, subject: str, text_body: str, html_body: str) -> None:
        message = EmailMessage()
        message["From"] = self.username
        message["To"] = self.recipient
        message["Subject"] = " ".join(subject.splitlines()).strip()[:200] or "Deep Research Report"
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            self.host,
            self.port,
            context=context,
            timeout=30,
        ) as smtp:
            smtp.login(self.username, self.authorization_code)
            smtp.send_message(message)

