"""Per-run results; never shared between users or research requests."""

from dataclasses import dataclass, field
from pathlib import Path

from .planner_agent import WebSearchPlan
from .writer_agent import ReportData


@dataclass
class ResearchState:
    output_dir: Path
    send_email: bool = False
    recipient: str = ""
    plan: WebSearchPlan | None = None
    searches: list[str] = field(default_factory=list)
    report: ReportData | None = None
    email_receipt: dict | None = None
    email_attempted: bool = False
    query: str = ""
    diagnostics: list[str] = field(default_factory=list)
    format_failures: dict[str, int] = field(default_factory=dict)

    def save_evidence(self):
        import json

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "evidence.json").write_text(
            json.dumps(
                {
                    "query": self.query,
                    "plan": self.plan.model_dump() if self.plan else None,
                    "search_summaries": self.searches,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


@dataclass
class ResearchUpdate:
    status: str
    report: str = ""
    files: list[str] = field(default_factory=list)
