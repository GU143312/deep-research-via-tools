"""Safe, actionable errors without copying provider bodies or credentials into the UI."""

import smtplib

import httpx
import openai
from agents import ModelBehaviorError

from .recipients import RecipientError
from .structured_output import StructuredOutputError


def explain_error(error: Exception) -> str:
    chain = []
    current = error
    while current is not None and id(current) not in {id(e) for e in chain}:
        chain.append(current)
        current = current.__cause__ or current.__context__
    for exc in reversed(chain):
        if isinstance(exc, RecipientError):
            return str(exc)
        if isinstance(exc, StructuredOutputError):
            return (
                f"{exc.stage} returned invalid structured output after format recovery. "
                "Saved evidence is available in evidence.json. No incomplete report was accepted."
            )
        if isinstance(exc, ModelBehaviorError):
            return (
                "Invalid model output or tool arguments. Evidence is retained; check the tool log."
            )
        if isinstance(exc, smtplib.SMTPAuthenticationError):
            return "SMTP login failed. Check sender credentials. The report is retained."
        if isinstance(exc, smtplib.SMTPException):
            return (
                "SMTP delivery failed. Check the mail service and network. The report is retained."
            )
        if isinstance(exc, (TimeoutError, httpx.TimeoutException, openai.APITimeoutError)):
            return "Connection timed out. Check the service used by the last tool call."
        status = getattr(exc, "status_code", None)
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
        if status in (401, 403):
            return (
                "API authentication or permission failed. Check the selected service credentials."
            )
        if status in (402, 429):
            return "API balance or rate limit reached. Check account credits and quota."
        if status == 400:
            if "Thinking mode does not support this tool_choice" in str(exc):
                return "Thinking mode is incompatible with forced tools. Restart the updated app."
            return "The model API rejected request parameters (HTTP 400). Check tool compatibility."
        if isinstance(exc, (httpx.ConnectError, openai.APIConnectionError)):
            return "Unable to connect to the API service. Check the network connection."
    return "Research is incomplete. Check the last tool call. Generated files are retained."
