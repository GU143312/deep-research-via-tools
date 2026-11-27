from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, received {raw!r}") from exc
    if value < 1 or value > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}, received {value}")
    return value


def _smtp_host_for(address: str) -> str:
    domain = address.rpartition("@")[2].lower()
    return {
        "163.com": "smtp.163.com",
        "126.com": "smtp.126.com",
        "yeah.net": "smtp.yeah.net",
    }.get(domain, "smtp.163.com")


@dataclass(frozen=True, slots=True)
class Settings:
    deepseek_api_key: str
    tavily_api_key: str
    model: str
    deepseek_base_url: str
    search_count: int
    max_results: int
    netease_email: str | None
    netease_auth_code: str | None
    email_to: str | None
    smtp_host: str
    smtp_port: int

    @classmethod
    def from_env(cls) -> Settings:
        netease_email = os.getenv("NETEASE_EMAIL", "").strip()
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
            tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip(),
            deepseek_base_url=os.getenv(
                "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
            ).strip(),
            search_count=_positive_int("RESEARCH_SEARCH_COUNT", 5, 10),
            max_results=_positive_int("RESEARCH_MAX_RESULTS", 5, 10),
            netease_email=netease_email or None,
            netease_auth_code=os.getenv("NETEASE_AUTH_CODE") or None,
            email_to=os.getenv("EMAIL_TO") or netease_email or None,
            smtp_host=(
                os.getenv("NETEASE_SMTP_HOST", "").strip()
                or _smtp_host_for(netease_email)
            ),
            smtp_port=_positive_int("NETEASE_SMTP_PORT", 465, 65535),
        )

    def validate(self, *, send_email: bool = False) -> None:
        missing: list[str] = []
        if not self.deepseek_api_key:
            missing.append("DEEPSEEK_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        if send_email:
            for name, value in (
                ("NETEASE_EMAIL", self.netease_email),
                ("NETEASE_AUTH_CODE", self.netease_auth_code),
                ("EMAIL_TO", self.email_to),
            ):
                if not value:
                    missing.append(name)
        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Missing required environment variable(s): {names}")

