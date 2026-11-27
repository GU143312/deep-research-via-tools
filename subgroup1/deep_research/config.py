"""Configuration shared by the UI, CLI and agent factories."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    model: str = "deepseek-flash"
    provider: str = "deepseek"
    search_count: int = 5
    tracing: bool = False
    output_root: Path = PROJECT_ROOT / "outputs"

    def __post_init__(self):
        if self.provider not in ("deepseek", "openai"):
            raise ValueError("MODEL_PROVIDER must be deepseek or openai.")
        if not 1 <= self.search_count <= 10:
            raise ValueError("HOW_MANY_SEARCHES must be between 1 and 10.")

    @property
    def api_key_name(self) -> str:
        return "DEEPSEEK_API_KEY" if self.provider == "deepseek" else "OPENAI_API_KEY"

    @property
    def base_url(self) -> str:
        return (
            "https://api.deepseek.com"
            if self.provider == "deepseek"
            else "https://api.openai.com/v1"
        )

    @classmethod
    def from_env(cls):
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        provider = os.getenv("MODEL_PROVIDER", "deepseek").strip().lower()
        return cls(
            provider=provider,
            model=os.getenv("DEFAULT_MODEL_NAME")
            or ("deepseek-flash" if provider == "deepseek" else "gpt-5.4-mini"),
            search_count=int(os.getenv("HOW_MANY_SEARCHES", "5")),
            tracing=os.getenv("ENABLE_TRACING", "false").lower() == "true",
        )


def validate_credentials(send_email: bool = False, settings: Settings | None = None):
    settings = settings or Settings()
    required = [settings.api_key_name]
    if settings.tracing and settings.provider == "deepseek":
        raise ValueError("Set ENABLE_TRACING=false for DeepSeek. Use local workflow.json instead.")
    if send_email:
        required += ["EMAIL_SMTP_SERVER", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise ValueError("Missing configuration in .env: " + ", ".join(missing))
    if send_email:
        port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        if not 1 <= port <= 65535:
            raise ValueError("EMAIL_SMTP_PORT must be between 1 and 65535.")
