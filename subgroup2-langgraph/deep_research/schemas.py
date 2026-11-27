from __future__ import annotations

import re
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, HttpUrl, model_validator


class WebSearchItem(BaseModel):
    query: str = Field(min_length=3, description="A focused web search query")
    reason: str = Field(
        min_length=3,
        description="Why this search helps answer the question",
        validation_alias=AliasChoices("reason", "purpose", "rationale"),
    )


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="Non-overlapping searches to execute")


class Source(BaseModel):
    title: str
    url: HttpUrl
    content: str
    score: float | None = None


class SearchFinding(BaseModel):
    query: str
    reason: str
    answer: str | None = None
    sources: list[Source]


class ReportData(BaseModel):
    title: str = Field(description="A concise report title")
    short_summary: str = Field(description="A two or three sentence executive summary")
    markdown_report: str = Field(description="The full, source-cited Markdown report")
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Useful next research questions",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_provider_output(cls, value: Any) -> Any:
        """Accept compact JSON returned by OpenAI-compatible providers such as DeepSeek."""
        if not isinstance(value, dict):
            return value

        data = dict(value)
        report = data.get("markdown_report") or data.get("report") or data.get("content")
        if not isinstance(report, str) or not report.strip():
            return data

        data.setdefault("markdown_report", report)
        data.setdefault("title", cls._title_from_markdown(report))
        data.setdefault("short_summary", cls._summary_from_markdown(report))
        data.setdefault(
            "follow_up_questions",
            data.get("questions") or data.get("next_questions") or [],
        )
        return data

    @staticmethod
    def _title_from_markdown(report: str) -> str:
        match = re.search(r"^#\s+(.+?)\s*$", report, flags=re.MULTILINE)
        return match.group(1).strip() if match else "Deep Research Report"

    @staticmethod
    def _summary_from_markdown(report: str) -> str:
        for block in re.split(r"\n\s*\n", report):
            paragraph = " ".join(block.split()).strip()
            if paragraph and not paragraph.startswith("#") and paragraph != "---":
                return paragraph[:1000]
        return "See the full research report for findings and sources."


class PlanResearchInput(BaseModel):
    question: str = Field(description="The user's original research question")


class SearchWebInput(BaseModel):
    query: str = Field(description="One query from the approved search plan")
    reason: str = Field(description="Why this search is relevant")


class WriteReportInput(BaseModel):
    question: str = Field(description="The user's original research question")


class SendEmailInput(BaseModel):
    subject: str = Field(description="A short subject line for the research report")

