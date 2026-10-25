"""Check SMTP TLS and authentication without sending any message."""

import os
import smtplib

from dotenv import load_dotenv

from .config import PROJECT_ROOT
from .email_agent import connect_smtp, smtp_password


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    missing = [
        key
        for key in ("EMAIL_SMTP_SERVER", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD")
        if not os.getenv(key, "").strip()
    ]
    if missing:
        print("Missing configuration in .env: " + ", ".join(missing))
        return 1
    stage = "TLS connection"
    try:
        with connect_smtp() as server:
            print("TLS connection verified.")
            stage = "authentication"
            server.login(os.environ["EMAIL_ADDRESS"], smtp_password())
            print("SMTP login succeeded. No email was sent.")
        return 0
    except smtplib.SMTPAuthenticationError:
        print(
            "SMTP login rejected. Check the mailbox authorization code, not the account password."
        )
    except Exception as exc:
        # SMTP/provider responses can contain personal account information.
        print(f"SMTP {stage} failed ({type(exc).__name__}). No email was sent.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
